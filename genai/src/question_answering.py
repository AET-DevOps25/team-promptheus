"""Question answering service using LangGraph agents with automatic tool usage."""

from datetime import UTC, datetime
from typing import Any

import structlog

# LangChain and LangGraph imports
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from .agent_tools import create_agent_tools, get_tool_descriptions
from .contributions import GitHubContentService
from .llm_service import LLMService
from .meilisearch import MeilisearchService
from .metrics import (
    question_answering_duration,
    question_answering_errors,
    question_answering_requests,
    question_confidence_score,
    record_error_metrics,
    record_request_metrics,
    time_operation,
)
from .models import (
    QuestionEvidence,
    QuestionRequest,
    QuestionResponse,
    generate_uuidv7,
)

logger = structlog.get_logger()

# Minimum relevance threshold for contribution filtering
MIN_RELEVANCE_THRESHOLD = 0.1


class QuestionAnswerOutput(PydanticBaseModel):
    """Structured output for question answering."""

    answer: str = Field(description="Direct answer to the user's question based on the evidence")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    reasoning_steps: list[str] = Field(description="Step-by-step reasoning process used to arrive at the answer")
    suggested_actions: list[str] = Field(description="Actionable suggestions based on the analysis")


class ConversationState(PydanticBaseModel):
    """State for conversation context including evidence and metadata."""

    user: str
    week: str
    question: str
    evidence: list[QuestionEvidence]
    focus_areas: list[str] = Field(default_factory=list)


class QuestionAnsweringService:
    """Service for answering questions using LangGraph agents with automatic tool usage."""

    def __init__(self, content_service: GitHubContentService, meilisearch_service: MeilisearchService) -> None:
        """Initialize the question answering service.

        Args:
            content_service: Service for fetching contributions.
            meilisearch_service: Service for semantic search.
        """
        self.content_service = content_service
        self.meilisearch_service = meilisearch_service

        # Initialize LLM using centralized service
        self.llm = LLMService.create_llm(
            temperature=0.2,
            timeout=60.0,
        )

        # Create checkpointer for agent sessions
        self.checkpointer = MemorySaver()

    def _create_context_message(
        self, user: str, week: str, repository: str, evidence: list[QuestionEvidence], tools: list[Any] | None = None
    ) -> str:
        """Create a context message for the agent."""
        tool_descriptions = get_tool_descriptions(tools) if tools else ""
        return f"""You are analyzing contributions for developer \"{user}\" during week \"{week}\" in repository \"{repository}\".

You have access to the following tools:

{tool_descriptions}

IMPORTANT: When using GitHub API tools, always use the repository "{repository}" as the repository parameter.

Your task is to answer questions about their work by:
1. Analyzing the provided evidence from their contributions
2. Using available tools to gather additional real-time information when needed
3. Providing direct, accurate answers based on both static evidence and tool-enhanced data
4. Suggesting actionable next steps when appropriate

Evidence from {user}'s contributions in week {week}:
{self._format_evidence_as_xml(evidence) if evidence else "<evidence>No evidence available</evidence>"}

Use the available GitHub API tools whenever they can provide better or more current
information than the static evidence alone. Remember to use "{repository}" as the repository parameter in all tool calls."""

    @time_operation(question_answering_duration, {"user": "unknown", "week": "unknown"})
    async def answer_question(self, user: str, week: str, request: QuestionRequest) -> QuestionResponse:
        """Answer a question using LangGraph agent with automatic tool usage."""
        start_time = datetime.now(UTC)
        question_id = generate_uuidv7()

        # Create session ID for this user/week combination
        session_id = f"{user}:{week}"

        try:
            record_request_metrics(question_answering_requests, {"user": user, "week": week}, "started")

            relevant_contributions = await self._retrieve_relevant_contributions(user, week, request)

            evidence = []
            for contrib in relevant_contributions:
                # Ensure relevance_score is a float, default to 0.0 if None
                relevance_score_raw = contrib.get("relevance_score", 0.0)
                relevance_score_value: float = float(relevance_score_raw) if relevance_score_raw is not None else 0.0

                evidence.append(
                    QuestionEvidence(
                        title=contrib.get("title", ""),
                        contribution_id=contrib.get("contribution_id", ""),
                        contribution_type=contrib.get("contribution_type", "commit"),
                        excerpt=contrib.get("content", ""),  # Limit excerpt length
                        relevance_score=relevance_score_value,
                        timestamp=datetime.fromisoformat(contrib.get("created_at", datetime.now(UTC).isoformat())),
                    )
                )

            # Set the GitHub PAT for the content service
            if request.github_pat:
                self.content_service.set_github_pat(request.github_pat)

            tools = create_agent_tools(request.github_pat)

            context_message = self._create_context_message(user, week, request.repository, evidence, tools)

            agent = create_react_agent(model=self.llm, tools=tools, checkpointer=self.checkpointer)

            messages = [
                SystemMessage(content=context_message),
                HumanMessage(content=request.question),
            ]

            config = RunnableConfig(configurable={"thread_id": session_id})

            logger.info(
                "Calling LangGraph agent with automatic tool usage",
                user=user,
                week=week,
                session_id=session_id,
                question=request.question[:100],
                evidence_count=len(evidence),
            )

            # 9. Invoke the agent (it will automatically use tools as needed)
            agent_response = await agent.ainvoke({"messages": messages}, config=config)

            # 8. Extract the final answer from agent response
            final_message = agent_response["messages"][-1]
            answer = final_message.content

            # 9. Calculate response time
            response_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # 10. Determine confidence based on tool usage
            # Check if tools were used by looking at the message history
            tool_usage_detected = any(
                hasattr(msg, "tool_calls") and msg.tool_calls for msg in agent_response["messages"]
            )
            confidence = 0.9 if tool_usage_detected else 0.7

            # 11. Extract reasoning from agent's work
            reasoning_steps: list[str] = []
            for msg in agent_response["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    reasoning_steps.extend(
                        f"Used {tool_call['name']} to gather additional information" for tool_call in msg.tool_calls
                    )

            if not reasoning_steps:
                reasoning_steps = ["Analyzed provided evidence to answer the question"]

            response = QuestionResponse(
                question_id=question_id,
                user=user,
                week=week,
                question=request.question,
                answer=answer,
                confidence=confidence,
                evidence=evidence,
                reasoning_steps=reasoning_steps,
                suggested_actions=["Continue exploring related questions to get more insights"],
                asked_at=datetime.now(UTC),
                response_time_ms=response_time_ms,
                conversation_id=session_id,
            )

            # Record metrics
            question_confidence_score.labels(user=user, week=week).observe(confidence)

            record_request_metrics(question_answering_requests, {"user": user, "week": week}, "success")

            logger.info(
                "Question answered successfully using LangGraph agent",
                question_id=question_id,
                user=user,
                week=week,
                session_id=session_id,
                question_length=len(request.question),
                evidence_count=len(evidence),
                confidence=confidence,
                tool_usage_detected=tool_usage_detected,
                response_time_ms=response_time_ms,
            )

            return response

        except Exception as e:
            record_request_metrics(question_answering_requests, {"user": user, "week": week}, "error")
            record_error_metrics(
                question_answering_errors,
                {"user": user, "week": week},
                type(e).__name__,
            )
            logger.exception(
                "LangGraph agent question answering failed",
                user=user,
                week=week,
                question=request.question,
                error=str(e),
            )
            raise

    async def _retrieve_relevant_contributions(
        self, user: str, week: str, request: QuestionRequest
    ) -> list[dict[str, Any]]:
        """Retrieve relevant contributions using semantic search with Meilisearch."""
        try:
            search_results = await self.meilisearch_service.search_contributions(
                user,
                week,
                request.question,
                limit=request.context.max_evidence_items,
            )

            return search_results[: request.context.max_evidence_items]

        except Exception as e:
            logger.exception(
                "Failed to retrieve relevant contributions",
                user=user,
                week=week,
                query=request.question,
                error=str(e),
            )
            # Return empty list on error
            return []

    def get_conversation_history(self, user: str, week: str) -> list[BaseMessage]:
        """Get conversation history for a user/week from LangGraph checkpointer."""
        thread_id = f"{user}:{week}"
        try:
            # Get the latest checkpoint from the LangGraph agent
            checkpoint = self.checkpointer.get({"configurable": {"thread_id": thread_id}})
            # Try different checkpoint formats depending on LangGraph version
            if checkpoint:
                # Try different possible attribute names - use getattr for safety
                data = getattr(checkpoint, "data", None)
                if data and isinstance(data, dict) and "messages" in data:
                    return data["messages"]

                channel_values = getattr(checkpoint, "channel_values", None)
                if channel_values and isinstance(channel_values, dict) and "messages" in channel_values:
                    return channel_values["messages"]

                if isinstance(checkpoint, dict) and "messages" in checkpoint:
                    return checkpoint["messages"]  # type: ignore[typeddict-item]
        except Exception as e:
            logger.warning(
                "Could not retrieve conversation history",
                thread_id=thread_id,
                error=str(e),
            )
        return []

    def clear_conversation_history(self, user: str, week: str) -> None:
        """Clear conversation history for a user/week."""
        thread_id = f"{user}:{week}"
        try:
            # Clear the checkpoint for this thread
            # Clear the checkpoint by putting None (simpler approach)
            # Note: This may vary depending on LangGraph version
            try:
                # Try to delete using the correct method for the LangGraph version
                if hasattr(self.checkpointer, "delete"):
                    self.checkpointer.delete({"configurable": {"thread_id": thread_id}})
                else:
                    # Fallback: create empty checkpoint manually
                    pass
                    # Clear by not putting anything - just skip
            except Exception:
                # If all else fails, silently ignore
                pass
            logger.info(
                "Cleared conversation history",
                user=user,
                week=week,
                thread_id=thread_id,
            )
        except Exception as e:
            logger.warning(
                "Could not clear conversation history",
                thread_id=thread_id,
                error=str(e),
            )

    async def cleanup(self) -> None:
        """Clean up async resources properly."""
        try:
            # If the LLM has an async client, close it properly
            if hasattr(self.llm, "_client") and hasattr(self.llm._client, "aclose"):
                await self.llm._client.aclose()
        except Exception as e:
            logger.warning("Error during LLM cleanup", error=str(e))

    def _format_evidence_as_xml(self, evidence: list[QuestionEvidence]) -> str:
        """Format evidence as XML."""
        if not evidence:
            return "<evidence>No evidence available</evidence>"

        xml_parts = ["<evidence>"]

        for item in evidence:
            xml_parts.append("  <item>")
            xml_parts.append(f"    <title>{self._escape_xml(item.title)}</title>")
            xml_parts.append(f"    <contribution_id>{self._escape_xml(item.contribution_id)}</contribution_id>")
            xml_parts.append(f"    <contribution_type>{item.contribution_type.value}</contribution_type>")
            xml_parts.append(f"    <excerpt>{self._escape_xml(item.excerpt)}</excerpt>")
            xml_parts.append(f"    <relevance_score>{item.relevance_score:.3f}</relevance_score>")
            xml_parts.append(f"    <timestamp>{item.timestamp.isoformat()}</timestamp>")
            xml_parts.append("  </item>")

        xml_parts.append("</evidence>")
        return "\n".join(xml_parts)

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
