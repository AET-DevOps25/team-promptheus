import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import structlog

from .models import (
    GitHubContribution, ContributionType, QuestionRequest, QuestionResponse, 
    QuestionEvidence, generate_uuidv7
)
from .metrics import (
    time_operation, record_request_metrics, record_error_metrics,
    question_answering_duration, question_answering_requests, question_confidence_score, 
    question_answering_errors
)
from .contributions import ContributionsIngestionService

logger = structlog.get_logger()


class QuestionAnsweringService:
    """Service for answering questions about a user's weekly contributions using RAG"""
    
    def __init__(self, ingestion_service: ContributionsIngestionService):
        self.ingestion_service = ingestion_service
        self.questions_store: Dict[str, QuestionResponse] = {}
    
    @time_operation(question_answering_duration, {"user": "unknown", "week": "unknown"})
    async def answer_question(self, user: str, week: str, request: QuestionRequest) -> QuestionResponse:
        """Answer a question about a specific user's week using RAG with embedded contributions"""
        start_time = datetime.now(timezone.utc)
        question_id = generate_uuidv7()
        
        try:
            record_request_metrics(
                question_answering_requests,
                {"user": user, "week": week},
                "started"
            )
            
            # 1. Retrieve relevant contributions for this user's week
            relevant_contributions = await self._retrieve_relevant_contributions(user, week, request)
            
            # 2. Generate answer using agentic RAG (placeholder)
            answer_data = await self._generate_agentic_answer(user, week, request, relevant_contributions)
            
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
                response_time_ms=response_time_ms
            )
            
            # Store the question for retrieval
            self.questions_store[question_id] = response
            
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
                                     contributions: List[GitHubContribution]) -> Dict[str, Any]:
        """Generate answer using agentic RAG with LangChain (placeholder)"""
        await asyncio.sleep(0.5)  # Simulate LLM processing
        
        # This is where the agentic LangChain implementation would go
        # For now, return a structured placeholder response
        
        if not contributions:
            return {
                "answer": f"I couldn't find any relevant contributions for {user} in week {week} to answer your question.",
                "confidence": 0.1,
                "evidence": [],
                "reasoning_steps": [
                    f"Searched through {user}'s contributions for week {week}",
                    "No relevant contributions found matching the question"
                ],
                "suggested_actions": [
                    f"Verify that {user} has contributions for week {week}",
                    "Try rephrasing the question with different keywords"
                ]
            }
        
        # Create evidence from contributions
        evidence = []
        for i, contrib in enumerate(contributions[:5]):  # Limit to top 5 evidence items
            title = ""
            if contrib.type == ContributionType.COMMIT:
                title = contrib.message[:100]
            elif contrib.type == ContributionType.PULL_REQUEST:
                title = contrib.title
            elif contrib.type == ContributionType.ISSUE:
                title = contrib.title
            elif contrib.type == ContributionType.RELEASE:
                title = contrib.name
            
            # Extract relevant excerpt
            text_content = self.ingestion_service._extract_text_content(contrib)
            excerpt = text_content[:200] + "..." if len(text_content) > 200 else text_content
            
            evidence.append(QuestionEvidence(
                contribution_id=contrib.id,
                contribution_type=contrib.type,
                title=title,
                excerpt=excerpt,
                relevance_score=0.9 - (i * 0.1),  # Decreasing relevance
                timestamp=contrib.created_at
            ))
        
        # Generate contextual answer based on focus areas
        focus_areas = request.context.focus_areas
        reasoning_steps = [
            f"Analyzed {len(contributions)} relevant contributions for {user} in week {week}",
            f"Applied focus areas: {', '.join(focus_areas) if focus_areas else 'general analysis'}",
            f"Found {len(evidence)} pieces of supporting evidence"
        ]
        
        # Generate answer based on question type and focus areas
        if any(keyword in request.question.lower() for keyword in ["blocker", "blocked", "impediment"]):
            answer_parts = [
                f"Based on {user}'s contributions in week {week}, I found {len(contributions)} relevant items.",
                "Analyzing for blockers and impediments..."
            ]
            suggested_actions = [
                "Review identified blockers with the team",
                "Prioritize resolution of blocking issues"
            ]
        elif any(keyword in request.question.lower() for keyword in ["progress", "done", "completed"]):
            answer_parts = [
                f"{user} made {len(contributions)} contributions in week {week}.",
                "Progress analysis shows active development across multiple areas."
            ]
            suggested_actions = [
                "Continue current development pace",
                "Consider documenting completed work"
            ]
        else:
            answer_parts = [
                f"Based on {user}'s {len(contributions)} contributions in week {week},",
                "I found relevant information to answer your question."
            ]
            suggested_actions = [
                "Review the evidence for more details",
                "Ask follow-up questions for specific areas"
            ]
        
        return {
            "answer": " ".join(answer_parts),
            "confidence": 0.8 if len(contributions) > 2 else 0.6,
            "evidence": evidence,
            "reasoning_steps": reasoning_steps,
            "suggested_actions": suggested_actions
        }
    
    def get_question(self, question_id: str) -> Optional[QuestionResponse]:
        """Retrieve a previously asked question"""
        return self.questions_store.get(question_id) 