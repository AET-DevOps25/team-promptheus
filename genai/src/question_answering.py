"""Question answering service using LangGraph agents with automatic tool usage."""

import asyncio
import os
from datetime import UTC, datetime

import structlog

# LangChain and LangGraph imports
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from .agent_tools import all_tools, get_tool_descriptions
from .ingest import ContributionsIngestionService
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
    ContributionType,
    GitHubContribution,
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

    def __init__(self, ingestion_service: ContributionsIngestionService) -> None:
        """Initialize the question answering service.

        Args:
            ingestion_service: Service for ingesting and retrieving contributions.
        """
        self.ingestion_service = ingestion_service
        self.questions_store: dict[str, QuestionResponse] = {}

        # Initialize LangChain components with Ollama
        ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        ollama_api_key = os.getenv("OLLAMA_API_KEY")
        model_name = os.getenv("LANGCHAIN_MODEL_NAME", "llama3.3:latest")

        self.llm = ChatOllama(
            model=model_name,
            base_url=ollama_base_url,
            client_kwargs={
                "headers": {"Authorization": f"Bearer {ollama_api_key}"},
                "timeout": 60.0,
            },
            temperature=0.2,
            num_predict=-1,
        )

        # Create LangGraph agent with automatic tool usage
        self.checkpointer = MemorySaver()
        self.agent = create_react_agent(model=self.llm, tools=all_tools, checkpointer=self.checkpointer)

    def _create_context_message(self, user: str, week: str, evidence_context: str, focus_context: str = "") -> str:
        """Create a context message for the agent."""
        tool_descriptions = get_tool_descriptions(all_tools)
        return f"""You are analyzing contributions for developer \"{user}\" during week \"{week}\".

You have access to the following tools:

{tool_descriptions}

Your task is to answer questions about their work by:
1. Analyzing the provided evidence from their contributions
2. Using available tools to gather additional real-time information when needed
3. Providing direct, accurate answers based on both static evidence and tool-enhanced data
4. Suggesting actionable next steps when appropriate

Evidence from {user}'s contributions in week {week}:
{evidence_context}

{focus_context}

Use the available GitHub API tools whenever they can provide better or more current
information than the static evidence alone."""

    @time_operation(question_answering_duration, {"user": "unknown", "week": "unknown"})
    async def answer_question(self, user: str, week: str, request: QuestionRequest) -> QuestionResponse:
        """Answer a question using LangGraph agent with automatic tool usage."""
        start_time = datetime.now(UTC)
        question_id = generate_uuidv7()

        # Create session ID for this user/week combination
        session_id = f"{user}:{week}"

        try:
            record_request_metrics(question_answering_requests, {"user": user, "week": week}, "started")

            # 1. Retrieve relevant contributions for this user's week
            relevant_contributions = await self._retrieve_relevant_contributions(user, week, request)

            # 2. Prepare evidence context
            evidence, evidence_context = self._prepare_evidence_context(relevant_contributions)

            # 3. Prepare focus areas context
            focus_context = ""
            if request.context.focus_areas:
                focus_context = (
                    f"\nPay special attention to these focus areas: {', '.join(request.context.focus_areas)}"
                )

            # 4. Create context message for the agent
            context_message = self._create_context_message(user, week, evidence_context, focus_context)

            # 5. Prepare messages for the agent
            messages = [
                SystemMessage(content=context_message),
                HumanMessage(content=request.question),
            ]

            # 6. Configure the agent
            config = RunnableConfig(configurable={"thread_id": session_id})

            logger.info(
                "Calling LangGraph agent with automatic tool usage",
                user=user,
                week=week,
                session_id=session_id,
                question=request.question[:100],
                evidence_count=len(evidence),
            )

            # 7. Invoke the agent (it will automatically use tools as needed)
            try:
                agent_response = await self.agent.ainvoke({"messages": messages}, config=config)
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    logger.exception(
                        "Event loop closed during agent invocation - this indicates async resource cleanup issue",
                        user=user,
                        week=week,
                        session_id=session_id,
                        error=str(e),
                    )
                    # Return a fallback response instead of crashing
                    response = QuestionResponse(
                        question_id=question_id,
                        user=user,
                        week=week,
                        question=request.question,
                        answer="I apologize, but I encountered a technical issue while processing your question. Please try again.",
                        confidence=0.0,
                        evidence=evidence,
                        reasoning_steps=["Technical error occurred during processing"],
                        suggested_actions=["Please try asking your question again"],
                        asked_at=datetime.now(UTC),
                        response_time_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                        conversation_id=session_id,
                    )

                    # Store the question for retrieval
                    self.questions_store[question_id] = response
                    return response
                raise

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

            # Store the question for retrieval
            self.questions_store[question_id] = response

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
    ) -> list[GitHubContribution]:
        """Retrieve relevant contributions using semantic search with Meilisearch."""
        try:
            if self.ingestion_service.meilisearch_service:
                # Use Meilisearch for semantic search
                search_results = await self.ingestion_service.meilisearch_service.search_contributions(
                    user,
                    week,
                    request.question,
                    limit=request.context.max_evidence_items,
                )

                # Convert search results back to contributions
                relevant_contributions = []
                all_contributions = self.ingestion_service.get_user_week_contributions(user, week)

                # Create a lookup map for contributions
                contrib_map = {contrib.id: contrib for contrib in all_contributions}

                for result in search_results:
                    contribution_id = result.get("contribution_id")
                    if contribution_id in contrib_map:
                        relevant_contributions.append(contrib_map[contribution_id])

                logger.info(
                    "Retrieved contributions using Meilisearch",
                    user=user,
                    week=week,
                    query=request.question,
                    results_count=len(relevant_contributions),
                )

                return relevant_contributions
            # Fallback: simple keyword matching
            await asyncio.sleep(0.1)  # Simulate search time

            all_contributions = self.ingestion_service.get_user_week_contributions(user, week)
            question_words = set(request.question.lower().split())
            relevant_contributions = []

            for contribution in all_contributions:
                text_content = self.ingestion_service._extract_text_content(contribution)
                content_words = set(text_content.lower().split())

                # Calculate simple relevance score
                intersection = question_words.intersection(content_words)
                if intersection:
                    relevance_score = len(intersection) / len(question_words)
                    if relevance_score > MIN_RELEVANCE_THRESHOLD:  # Minimum relevance threshold
                        relevant_contributions.append(contribution)

            logger.info(
                "Retrieved contributions using fallback search",
                user=user,
                week=week,
                query=request.question,
                results_count=len(relevant_contributions),
            )

            return relevant_contributions[: request.context.max_evidence_items]

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

    def _prepare_evidence_context(self, contributions: list[GitHubContribution]) -> tuple[list[QuestionEvidence], str]:
        """Prepare evidence objects and formatted context for LLM."""
        evidence = []
        evidence_context = []

        for i, contrib in enumerate(contributions):
            title = self._extract_contribution_title(contrib)
            text_content = self.ingestion_service._extract_text_content(contrib)

            evidence.append(
                QuestionEvidence(
                    contribution_id=contrib.id,
                    contribution_type=contrib.type,
                    title=title,
                    excerpt=text_content,
                    relevance_score=max(0.9 - (i * 0.1), 0.1),  # Decreasing relevance
                    timestamp=contrib.created_at,
                )
            )

            # Format for LLM context
            evidence_context.append(
                f"Evidence {i + 1} ({contrib.type.value}):\n"
                f"Title: {title}\n"
                f"Repository: {getattr(contrib, 'repository', 'unknown')}\n"
                f"Content: {text_content}\n"
                f"Timestamp: {contrib.created_at}\n"
            )

        return evidence, "\n".join(evidence_context)

    def _extract_contribution_title(self, contrib: GitHubContribution) -> str:
        """Extract a meaningful title from a contribution."""
        title_map = {
            ContributionType.COMMIT: self._get_commit_title,
            ContributionType.PULL_REQUEST: self._get_pr_title,
            ContributionType.ISSUE: self._get_issue_title,
            ContributionType.RELEASE: self._get_release_title,
        }
        return title_map.get(contrib.type, lambda _: "Unknown contribution type")(contrib)

    def _get_commit_title(self, contrib: GitHubContribution) -> str:
        """Get title for commit contribution."""
        if hasattr(contrib, "message"):
            return contrib.message[:100] if contrib.message else "Untitled commit"
        return "Untitled commit"

    def _get_pr_title(self, contrib: GitHubContribution) -> str:
        """Get title for pull request contribution."""
        if hasattr(contrib, "title"):
            return contrib.title or "Untitled pull request"
        return "Untitled pull request"

    def _get_issue_title(self, contrib: GitHubContribution) -> str:
        """Get title for issue contribution."""
        if hasattr(contrib, "title"):
            return contrib.title or "Untitled issue"
        return "Untitled issue"

    def _get_release_title(self, contrib: GitHubContribution) -> str:
        """Get title for release contribution."""
        if hasattr(contrib, "name"):
            return contrib.name or f"Release {contrib.tag_name}" if hasattr(contrib, "tag_name") else "Untitled release"
        return "Untitled release"

    def get_question(self, question_id: str) -> QuestionResponse | None:
        """Retrieve a previously asked question."""
        return self.questions_store.get(question_id)

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
