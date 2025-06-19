import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import structlog

# LangChain imports for conversation history
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers import PydanticOutputParser
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel as PydanticBaseModel, Field

from .models import (
    GitHubContribution, ContributionType, QuestionRequest, QuestionResponse, 
    QuestionEvidence, generate_uuidv7
)
from .metrics import (
    time_operation, record_request_metrics, record_error_metrics,
    question_answering_duration, question_answering_requests, question_confidence_score, 
    question_answering_errors, langchain_model_requests, langchain_model_duration, langchain_model_errors
)
from .ingest import ContributionsIngestionService

logger = structlog.get_logger()


class QuestionAnswerOutput(PydanticBaseModel):
    """Structured output for question answering"""
    answer: str = Field(description="Direct answer to the user's question based on the evidence")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    reasoning_steps: List[str] = Field(description="Step-by-step reasoning process used to arrive at the answer")
    suggested_actions: List[str] = Field(description="Actionable suggestions based on the analysis")


class ConversationState(PydanticBaseModel):
    """State for conversation context including evidence and metadata"""
    user: str
    week: str
    question: str
    evidence: List[QuestionEvidence]
    focus_areas: List[str] = Field(default_factory=list)


class QuestionAnsweringService:
    """Service for answering questions with LangChain's conversation history management"""
    
    def __init__(self, ingestion_service: ContributionsIngestionService):
        self.ingestion_service = ingestion_service
        self.questions_store: Dict[str, QuestionResponse] = {}
        
        # Simple in-memory conversation storage per user:week
        self.conversation_stores: Dict[str, InMemoryChatMessageHistory] = {}
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model=os.getenv("LANGCHAIN_MODEL_NAME", "gpt-4-turbo"),
            temperature=0.0,
            max_tokens=20000
        )
        
        # Create the conversation-aware chain
        self.qa_chain = self._create_qa_chain()
        self.qa_with_history = self._create_qa_with_history()
    
    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create in-memory chat message history for a session (user:week)"""
        if session_id not in self.conversation_stores:
            self.conversation_stores[session_id] = InMemoryChatMessageHistory()
            logger.info("Created new conversation session", session_id=session_id)
        return self.conversation_stores[session_id]
    
    def _create_qa_chain(self):
        """Create the core Q&A chain without history"""
        
        # Create system prompt template with conversation history placeholder
        system_prompt = """You are an AI assistant that analyzes developer contributions and answers questions about their work.

You are analyzing contributions for developer "{user}" during week "{week}".

Your task is to:
1. Carefully analyze the provided evidence from their contributions
2. Use conversation history to provide contextual answers and maintain conversational flow
3. Answer the user's question directly and accurately based on the evidence
4. Provide reasoning steps showing your analysis process
5. Suggest actionable next steps when appropriate
6. Assign a confidence score based on the quality and relevance of evidence

Guidelines:
- Be specific and reference actual contributions when possible
- Reference previous questions/answers from the conversation when relevant
- If the evidence doesn't fully support an answer, be honest about limitations
- Focus on factual information from the contributions
- Provide actionable insights when possible
- Maintain a conversational tone that builds on previous interactions

{focus_context}

Evidence from {user}'s contributions in week {week}:

{evidence_context}

Return a JSON response with this exact structure:
{{
    "answer": "Direct answer to the user's question based on the evidence",
    "confidence": 0.85,
    "reasoning_steps": ["Step 1", "Step 2", "Step 3"],
    "suggested_actions": ["Action 1", "Action 2"]
}}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),  # LangChain manages this
            ("human", "{question}")
        ])
        
        # Create parser
        parser = PydanticOutputParser(pydantic_object=QuestionAnswerOutput)
        
        # Create the chain that returns structured output
        structured_chain = prompt | self.llm | parser
        
        # Create a wrapper that returns just the answer for conversation history
        def extract_answer(structured_output):
            if hasattr(structured_output, 'answer'):
                return structured_output.answer
            return str(structured_output)
        
        # Chain that returns just the answer string for conversation history
        conversation_chain = structured_chain | extract_answer
        
        # Store both chains - we'll use structured_chain directly in our implementation
        self.structured_chain = structured_chain
        
        return conversation_chain
    
    def _create_qa_with_history(self):
        """Create the Q&A chain with conversation history"""
        return RunnableWithMessageHistory(
            self.qa_chain,
            self._get_session_history,
            input_messages_key="question",
            history_messages_key="history",
        )
    
    @time_operation(question_answering_duration, {"user": "unknown", "week": "unknown"})
    async def answer_question(self, user: str, week: str, request: QuestionRequest) -> QuestionResponse:
        """Answer a question about a specific user's week using RAG with LangChain conversation history"""
        start_time = datetime.now(timezone.utc)
        question_id = generate_uuidv7()
        
        # Create session ID for this user/week combination
        session_id = f"{user}:{week}"
        
        try:
            record_request_metrics(
                question_answering_requests,
                {"user": user, "week": week},
                "started"
            )
            
            # 1. Retrieve relevant contributions for this user's week
            relevant_contributions = await self._retrieve_relevant_contributions(user, week, request)
            
            # 2. Prepare evidence context for the LLM
            evidence, evidence_context = self._prepare_evidence_context(relevant_contributions)
            
            # 3. Prepare focus areas context
            focus_context = ""
            if request.context.focus_areas:
                focus_context = f"\nPay special attention to these focus areas: {', '.join(request.context.focus_areas)}"
            
            # 4. Invoke the conversation-aware chain
            config = {"configurable": {"session_id": session_id}}
            
            chain_input = {
                "user": user,
                "week": week,
                "question": request.question,
                "evidence_context": evidence_context,
                "focus_context": focus_context
            }
            
            logger.info("Calling LangChain conversation-aware Q&A",
                       user=user,
                       week=week,
                       session_id=session_id,
                       question=request.question[:100],
                       evidence_count=len(evidence))
            
            # Use the conversation-aware chain to maintain history (returns just answer string)
            conversation_answer = await self.qa_with_history.ainvoke(chain_input, config=config)
            
            # Also get the full structured response for our application
            # Add empty history for the structured chain call
            structured_input = chain_input.copy()
            structured_input["history"] = []
            llm_result = await self.structured_chain.ainvoke(structured_input)
            
            # Calculate response time
            response_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            response = QuestionResponse(
                question_id=question_id,
                user=user,
                week=week,
                question=request.question,
                answer=llm_result.answer,
                confidence=llm_result.confidence,
                evidence=evidence,
                reasoning_steps=llm_result.reasoning_steps,
                suggested_actions=llm_result.suggested_actions,
                asked_at=datetime.now(timezone.utc),
                response_time_ms=response_time_ms,
                conversation_id=session_id  # Use session_id as conversation_id
            )
            
            # Store the question for retrieval
            self.questions_store[question_id] = response
            
            # Record metrics
            question_confidence_score.labels(
                user=user,
                week=week
            ).observe(llm_result.confidence)
            
            record_request_metrics(
                question_answering_requests,
                {"user": user, "week": week},
                "success"
            )
            
            logger.info("Question answered successfully with conversation context",
                       question_id=question_id,
                       user=user,
                       week=week,
                       session_id=session_id,
                       question_length=len(request.question),
                       evidence_count=len(evidence),
                       confidence=llm_result.confidence,
                       response_time_ms=response_time_ms)
            
            return response
            
        except Exception as e:
            record_request_metrics(
                question_answering_requests,
                {"user": user, "week": week},
                "error"
            )
            record_error_metrics(
                question_answering_errors,
                {"user": user, "week": week},
                type(e).__name__
            )
            logger.error("Question answering failed",
                        user=user,
                        week=week,
                        question=request.question,
                        error=str(e))
            raise
    
    async def _retrieve_relevant_contributions(self, user: str, week: str, request: QuestionRequest) -> List[GitHubContribution]:
        """Retrieve relevant contributions using semantic search with Meilisearch"""
        try:
            if self.ingestion_service.meilisearch_service:
                # Use Meilisearch for semantic search
                search_results = await self.ingestion_service.meilisearch_service.search_contributions(
                    user, week, request.question, limit=request.context.max_evidence_items
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
                
                logger.info("Retrieved contributions using Meilisearch",
                           user=user,
                           week=week,
                           query=request.question,
                           results_count=len(relevant_contributions))
                
                return relevant_contributions
            else:
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
                        if relevance_score > 0.1:  # Minimum relevance threshold
                            relevant_contributions.append(contribution)
                
                logger.info("Retrieved contributions using fallback search",
                           user=user,
                           week=week,
                           query=request.question,
                           results_count=len(relevant_contributions))
                
                return relevant_contributions[:request.context.max_evidence_items]
                
        except Exception as e:
            logger.error("Failed to retrieve relevant contributions",
                        user=user,
                        week=week,
                        query=request.question,
                        error=str(e))
            # Return empty list on error
            return []
    
    def _prepare_evidence_context(self, contributions: List[GitHubContribution]) -> tuple[List[QuestionEvidence], str]:
        """Prepare evidence objects and formatted context for LLM"""
        evidence = []
        evidence_context = []
        
        for i, contrib in enumerate(contributions):
            title = self._extract_contribution_title(contrib)
            text_content = self.ingestion_service._extract_text_content(contrib)
            
            evidence.append(QuestionEvidence(
                contribution_id=contrib.id,
                contribution_type=contrib.type,
                title=title,
                excerpt=text_content,
                relevance_score=max(0.9 - (i * 0.1), 0.1),  # Decreasing relevance
                timestamp=contrib.created_at
            ))
            
            # Format for LLM context
            evidence_context.append(
                f"Evidence {i+1} ({contrib.type.value}):\n"
                f"Title: {title}\n"
                f"Repository: {getattr(contrib, 'repository', 'unknown')}\n"
                f"Content: {text_content}\n"
                f"Timestamp: {contrib.created_at}\n"
            )
        
        return evidence, "\n".join(evidence_context)

    def _extract_contribution_title(self, contrib: GitHubContribution) -> str:
        """Extract a meaningful title from a contribution"""
        if contrib.type == ContributionType.COMMIT:
            return contrib.message[:100] if contrib.message else "Untitled commit"
        elif contrib.type == ContributionType.PULL_REQUEST:
            return contrib.title or "Untitled pull request"
        elif contrib.type == ContributionType.ISSUE:
            return contrib.title or "Untitled issue"
        elif contrib.type == ContributionType.RELEASE:
            return contrib.name or f"Release {contrib.tag_name}" if hasattr(contrib, 'tag_name') else "Untitled release"
        else:
            return f"{contrib.type.value} contribution"
    

    
    def get_question(self, question_id: str) -> Optional[QuestionResponse]:
        """Retrieve a previously asked question"""
        return self.questions_store.get(question_id)
    
    def get_conversation_history(self, user: str, week: str) -> List[BaseMessage]:
        """Get conversation history for a user/week"""
        session_id = f"{user}:{week}"
        if session_id in self.conversation_stores:
            return self.conversation_stores[session_id].messages
        return []
    
    def clear_conversation_history(self, user: str, week: str) -> None:
        """Clear conversation history for a user/week"""
        session_id = f"{user}:{week}"
        if session_id in self.conversation_stores:
            self.conversation_stores[session_id].clear()
            logger.info("Cleared conversation history", user=user, week=week, session_id=session_id) 