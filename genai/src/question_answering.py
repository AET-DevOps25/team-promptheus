import asyncio
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import structlog

# LangChain imports
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel as PydanticBaseModel, Field

from .models import (
    GitHubContribution, ContributionType, QuestionRequest, QuestionResponse, 
    QuestionEvidence, generate_uuidv7, ConversationThread, ConversationTurn
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


class QuestionAnsweringService:
    """Service for answering questions about a user's weekly contributions using RAG"""
    
    def __init__(self, ingestion_service: ContributionsIngestionService):
        self.ingestion_service = ingestion_service
        self.questions_store: Dict[str, QuestionResponse] = {}
        # New conversation management
        self.conversations_store: Dict[str, ConversationThread] = {}  # conversation_id -> thread
        self.user_conversations: Dict[str, str] = {}  # user:week -> conversation_id
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model=os.getenv("LANGCHAIN_MODEL_NAME", "gpt-4-turbo"),
            temperature=0.0,
            max_tokens=20000
        )
    
    @time_operation(question_answering_duration, {"user": "unknown", "week": "unknown"})
    async def answer_question(self, user: str, week: str, request: QuestionRequest) -> QuestionResponse:
        """Answer a question about a specific user's week using RAG with embedded contributions"""
        start_time = datetime.now(timezone.utc)
        question_id = generate_uuidv7()
        
        # Handle conversation context
        conversation_thread = self._get_or_create_conversation(user, week, request.context.conversation_id)
        
        try:
            record_request_metrics(
                question_answering_requests,
                {"user": user, "week": week},
                "started"
            )
            
            # 1. Retrieve relevant contributions for this user's week
            relevant_contributions = await self._retrieve_relevant_contributions(user, week, request)
            
            # 2. Generate answer using agentic RAG with LLM (now with conversation context)
            answer_data = await self._generate_agentic_answer(user, week, request, relevant_contributions, conversation_thread)
            
            # Calculate response time
            response_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            response = QuestionResponse(
                question_id=question_id,
                user=user,
                week=week,
                question=request.question,
                answer=answer_data["answer"],
                confidence=answer_data["confidence"],
                evidence=answer_data["evidence"],
                reasoning_steps=answer_data["reasoning_steps"],
                suggested_actions=answer_data["suggested_actions"],
                asked_at=datetime.now(timezone.utc),
                response_time_ms=response_time_ms,
                conversation_id=conversation_thread.conversation_id  # Link to conversation
            )
            
            # Store the question for retrieval
            self.questions_store[question_id] = response
            
            # Add this Q&A to the conversation thread
            conversation_thread.add_turn(
                question=request.question,
                answer=answer_data["answer"],
                confidence=answer_data["confidence"],
                response_time_ms=response_time_ms
            )
            
            # Record metrics
            question_confidence_score.labels(
                user=user,
                week=week
            ).observe(answer_data["confidence"])
            
            record_request_metrics(
                question_answering_requests,
                {"user": user, "week": week},
                "success"
            )
            
            logger.info("Question answered successfully",
                       question_id=question_id,
                       user=user,
                       week=week,
                       conversation_id=conversation_thread.conversation_id,
                       question_length=len(request.question),
                       evidence_count=len(answer_data["evidence"]),
                       confidence=answer_data["confidence"],
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
    
    async def _generate_agentic_answer(self, user: str, week: str, request: QuestionRequest, 
                                     contributions: List[GitHubContribution], conversation_thread: ConversationThread) -> Dict[str, Any]:
        """Generate answer using agentic RAG with LangChain"""
        
        # Record LangChain metrics
        model_name = self.llm.model_name
        start_time = datetime.now(timezone.utc)
        
        try:
            langchain_model_requests.labels(
                model=model_name,
                operation="question_answering",
                status="started"
            ).inc()
            
            if not contributions:
                # No contributions found - return simple response without LLM call
                return {
                    "answer": f"I couldn't find any relevant contributions for {user} in week {week} to answer your question about '{request.question}'. This could mean no contributions exist for this period or none match your query.",
                    "confidence": 0.0,
                    "evidence": [],
                    "reasoning_steps": [
                        f"Searched through {user}'s contributions for week {week}",
                        "No relevant contributions found matching the question",
                        "No data available for analysis"
                    ],
                    "suggested_actions": [
                        f"Verify that {user} has contributions for week {week}",
                        "Try rephrasing the question with different keywords",
                        "Check if the contributions have been properly ingested"
                    ]
                }
            
            # Create evidence from contributions
            evidence = []
            evidence_context = []
            
            for i, contrib in enumerate(contributions):
                title = self._extract_contribution_title(contrib)
                text_content = self.ingestion_service._extract_text_content(contrib)
                # Use full text content - no truncation for LLM analysis
                excerpt = text_content  
                
                evidence.append(QuestionEvidence(
                    contribution_id=contrib.id,
                    contribution_type=contrib.type,
                    title=title,
                    excerpt=excerpt,
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
            
            # Build context about focus areas
            focus_context = ""
            if request.context.focus_areas:
                focus_context = f"\nPay special attention to these focus areas: {', '.join(request.context.focus_areas)}"
            
            # Build conversation history context
            conversation_context = ""
            recent_turns = conversation_thread.get_recent_turns(request.context.max_conversation_history)
            if recent_turns:
                conversation_context = "\n\nPrevious conversation in this session:"
                for i, turn in enumerate(recent_turns, 1):
                    conversation_context += f"\n\nQ{i}: {turn.question}"
                    conversation_context += f"\nA{i}: {turn.answer[:200]}{'...' if len(turn.answer) > 200 else ''}"
                
                conversation_context += "\n\nNote: Use this conversation history to provide contextual answers. Reference previous questions/answers when relevant, and maintain conversational flow."
            
            # Create system prompt
            system_prompt = f"""You are an AI assistant that analyzes developer contributions and answers questions about their work.
You are analyzing contributions for developer "{user}" during week {week}.

Your task is to:
1. Carefully analyze the provided evidence from their contributions
2. Answer the user's question directly and accurately based on this evidence
3. Use conversation history to provide contextual answers and maintain conversational flow
4. Provide reasoning steps showing your analysis process
5. Suggest actionable next steps when appropriate
6. Assign a confidence score based on the quality and relevance of evidence

Guidelines:
- Be specific and reference actual contributions when possible
- Reference previous questions/answers from the conversation when relevant
- If the evidence doesn't fully support an answer, be honest about limitations
- Focus on factual information from the contributions
- Provide actionable insights when possible
- Maintain a conversational tone that builds on previous interactions{focus_context}{conversation_context}

Return a JSON response with this exact structure:
{{
    "answer": "Direct answer to the user's question based on the evidence",
    "confidence": 0.85,
    "reasoning_steps": ["Step 1", "Step 2", "Step 3"],
    "suggested_actions": ["Action 1", "Action 2"]
}}"""

            # Create human prompt
            human_prompt = f"""Question: {request.question}

Evidence from {user}'s contributions in week {week}:

{chr(10).join(evidence_context)}

Based on this evidence, please answer the question with appropriate confidence and reasoning."""

            logger.info("Calling LLM for question answering",
                       user=user,
                       week=week,
                       question=request.question[:100],
                       evidence_count=len(evidence_context))
            
            # ALWAYS try to use LLM - no fallbacks during LLM processing
            return await self._call_llm_with_evidence(system_prompt, human_prompt, evidence, model_name)
            
        except Exception as e:
            langchain_model_requests.labels(
                model=model_name,
                operation="question_answering",
                status="error"
            ).inc()
            
            langchain_model_errors.labels(
                model=model_name,
                operation="question_answering",
                error_type=type(e).__name__
            ).inc()
            
            logger.error("LLM-based answer generation failed completely", 
                        user=user,
                        week=week,
                        question=request.question,
                        error=str(e))
            
            # Decline to answer if LLM is completely unavailable
            return {
                "answer": "I'm unable to answer your question at the moment due to AI processing issues. Please try again later or contact support if the problem persists.",
                "confidence": 0.0,
                "evidence": evidence if 'evidence' in locals() else [],
                "reasoning_steps": ["LLM processing failed", "Unable to analyze contributions", "Declining to provide potentially inaccurate answer"],
                "suggested_actions": ["Try again in a few minutes", "Contact support if issue persists", "Check system status"]
            }
    


    async def _call_llm_with_evidence(self, system_prompt: str, human_prompt: str, evidence: List[QuestionEvidence], model_name: str) -> Dict[str, Any]:
        """Robust LLM calling with multiple fallback strategies"""
        
        # Strategy 1: Try structured output with Pydantic parser
        try:
            parser = PydanticOutputParser(pydantic_object=QuestionAnswerOutput)
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt + f"\n\n{parser.get_format_instructions()}"),
                HumanMessage(content=human_prompt)
            ])
            
            chain = prompt | self.llm | parser
            llm_result = await chain.ainvoke({})
            
            print(llm_result)
            logger.info("LLM structured response successful", confidence=llm_result.confidence)
            
            langchain_model_requests.labels(
                model=model_name,
                operation="question_answering", 
                status="success"
            ).inc()
            
            return {
                "answer": llm_result.answer,
                "confidence": llm_result.confidence,  # Use LLM's confidence
                "evidence": evidence,
                "reasoning_steps": llm_result.reasoning_steps,
                "suggested_actions": llm_result.suggested_actions
            }
            
        except Exception as parse_error:
            logger.warning("Structured parsing failed, trying raw LLM response", error=str(parse_error))
            
            # Strategy 2: Raw LLM call with JSON parsing
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=human_prompt)
                ]
                
                response = await self.llm.ainvoke(messages)
                
                raw_answer = response.content.strip()
                logger.info("Raw LLM response successful", answer_length=len(raw_answer))
                
                # Try to parse JSON from raw response
                import json
                if raw_answer.startswith('{') and raw_answer.endswith('}'):
                    try:
                        parsed = json.loads(raw_answer)
                        langchain_model_requests.labels(model=model_name, operation="question_answering", status="success").inc()
                        return {
                            "answer": parsed.get("answer", raw_answer),
                            "confidence": float(parsed.get("confidence", 0.0)),  # Use LLM's confidence or reasonable default
                            "evidence": evidence,
                            "reasoning_steps": parsed.get("reasoning_steps", ["Analyzed contributions and generated response"]),
                            "suggested_actions": parsed.get("suggested_actions", ["Review evidence for more details"])
                        }
                    except json.JSONDecodeError:
                        pass
                
                # Strategy 3: Use raw answer if JSON parsing fails
                langchain_model_requests.labels(model=model_name, operation="question_answering", status="success").inc()
                return {
                    "answer": raw_answer,
                    "confidence": 0.6,  # Lower confidence for unstructured response
                    "evidence": evidence,
                    "reasoning_steps": ["Generated response using LLM reasoning"],
                    "suggested_actions": ["Review the evidence for more detailed information"]
                }
                
            except Exception as raw_error:
                logger.error("Raw LLM response also failed", error=str(raw_error))
                # This should rarely happen - only if LLM is completely unavailable
                raise raw_error

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
    
    def _get_or_create_conversation(self, user: str, week: str, conversation_id: Optional[str] = None) -> ConversationThread:
        """Get existing conversation or create a new one for the user/week"""
        user_week_key = f"{user}:{week}"
        
        if conversation_id:
            # Client provided a specific conversation ID
            if conversation_id in self.conversations_store:
                thread = self.conversations_store[conversation_id]
                # Verify it matches the user/week
                if thread.user == user and thread.week == week:
                    return thread
                else:
                    logger.warning("Conversation ID mismatch",
                                 conversation_id=conversation_id,
                                 expected_user=user,
                                 expected_week=week,
                                 actual_user=thread.user,
                                 actual_week=thread.week)
        
        # Check if we have an existing conversation for this user/week
        if user_week_key in self.user_conversations:
            existing_conversation_id = self.user_conversations[user_week_key]
            if existing_conversation_id in self.conversations_store:
                return self.conversations_store[existing_conversation_id]
        
        # Create new conversation
        new_conversation_id = generate_uuidv7()
        conversation_thread = ConversationThread(
            conversation_id=new_conversation_id,
            user=user,
            week=week,
            created_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc)
        )
        
        # Store the conversation
        self.conversations_store[new_conversation_id] = conversation_thread
        self.user_conversations[user_week_key] = new_conversation_id
        
        logger.info("Created new conversation thread",
                   conversation_id=new_conversation_id,
                   user=user,
                   week=week)
        
        return conversation_thread
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationThread]:
        """Get a conversation thread by ID"""
        return self.conversations_store.get(conversation_id)
    
    def get_user_conversations(self, user: str, week: str) -> Optional[ConversationThread]:
        """Get the active conversation for a user/week"""
        user_week_key = f"{user}:{week}"
        conversation_id = self.user_conversations.get(user_week_key)
        if conversation_id:
            return self.conversations_store.get(conversation_id)
        return None 