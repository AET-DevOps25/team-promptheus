import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, AsyncGenerator, TYPE_CHECKING
import structlog

# LangChain imports
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel as PydanticBaseModel, Field

from .models import (
    ContributionType, SummaryRequest, SummaryResponse, 
    SummaryChunk, SummaryMetadata, generate_uuidv7,
    GitHubContribution, CommitContribution, PullRequestContribution,
    IssueContribution, ReleaseContribution
)
from .metrics import (
    time_operation, record_request_metrics, record_error_metrics,
    summary_generation_duration, summary_generation_requests
)

# Type-only import to avoid circular dependency
if TYPE_CHECKING:
    from .ingest import ContributionsIngestionService

logger = structlog.get_logger()


class WeeklyProgressOutput(PydanticBaseModel):
    """Structured output for weekly progress report"""
    summary: str = Field(description="Brief summary of work completed this week (2-3 sentences)")
    key_accomplishments: List[str] = Field(description="List of key accomplishments this week")
    impediments: List[str] = Field(description="Current blockers or impediments (empty list if none)")
    next_steps: List[str] = Field(description="Planned work for next week based on assignments and context")


class SummaryService:
    """Service for generating weekly progress reports"""
    
    def __init__(self, ingestion_service: "ContributionsIngestionService"):
        self.ingestion_service = ingestion_service
        self.summaries_store: Dict[str, SummaryResponse] = {}
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model=os.getenv("LANGCHAIN_MODEL_NAME", "gpt-4-turbo"),
            temperature=0.2,
            max_tokens=1500
        )
    
    @time_operation(summary_generation_duration, {"repository": "unknown", "username": "unknown"})
    async def generate_summary(self, user: str, week: str, request: SummaryRequest, summary_id: Optional[str] = None) -> SummaryResponse:
        """Generate a weekly progress report"""
        start_time = datetime.now(timezone.utc)
        if summary_id is None:
            summary_id = generate_uuidv7()
        
        try:
            record_request_metrics(
                summary_generation_requests,
                {"repository": "unknown", "username": user, "status": "started"},
                "started"
            )
            
            logger.info("Starting weekly progress report generation",
                       user=user,
                       week=week,
                       summary_id=summary_id)
            
            # Get all contributions for the user's week
            contributions = self.ingestion_service.get_user_week_contributions(user, week)
            
            if not contributions:
                logger.warning("No contributions found for summary",
                              user=user,
                              week=week)
                return self._create_empty_summary(summary_id, user, week, start_time)
            
            # Generate the progress report using AI
            progress_report = await self._generate_progress_report(user, week, contributions, request)
            
            # Calculate timing metrics
            processing_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            # Generate metadata
            metadata = self._generate_metadata(contributions, week, start_time, processing_time_ms)
            
            # Create final summary response
            summary = SummaryResponse(
                summary_id=summary_id,
                user=user,
                week=week,
                overview=progress_report.summary,
                commits_summary=f"Completed {metadata.commits_count} commits" if metadata.commits_count > 0 else "No commits this week",
                pull_requests_summary=f"Worked on {metadata.pull_requests_count} pull requests" if metadata.pull_requests_count > 0 else "No pull requests this week",
                issues_summary=f"Addressed {metadata.issues_count} issues" if metadata.issues_count > 0 else "No issues this week",
                releases_summary=f"Published {metadata.releases_count} releases" if metadata.releases_count > 0 else "No releases this week",
                analysis="Weekly progress report generated",
                key_achievements=progress_report.key_accomplishments,
                areas_for_improvement=progress_report.impediments + progress_report.next_steps,
                metadata=metadata,
                generated_at=datetime.now(timezone.utc)
            )
            
            # Store the summary
            self.summaries_store[summary_id] = summary
            
            record_request_metrics(
                summary_generation_requests,
                {"repository": "unknown", "username": user},
                "success"
            )
            
            logger.info("Weekly progress report generation completed",
                       user=user,
                       week=week,
                       summary_id=summary_id,
                       contributions_count=len(contributions),
                       processing_time_ms=processing_time_ms)
            
            return summary
            
        except Exception as e:
            record_request_metrics(
                summary_generation_requests,
                {"repository": "unknown", "username": user},
                "error"
            )
            
            logger.error("Weekly progress report generation failed",
                        user=user,
                        week=week,
                        error=str(e))
            raise
    
    async def generate_summary_stream(self, user: str, week: str, request: SummaryRequest) -> AsyncGenerator[SummaryChunk, None]:
        """Generate a streaming weekly progress report"""
        start_time = datetime.now(timezone.utc)
        summary_id = generate_uuidv7()
        
        try:
            logger.info("Starting streaming weekly progress report",
                       user=user,
                       week=week,
                       summary_id=summary_id)
            
            # Get all contributions for the user's week
            contributions = self.ingestion_service.get_user_week_contributions(user, week)
            
            if not contributions:
                yield SummaryChunk(
                    chunk_type="content",
                    section="overview",
                    content=f"No contributions found for {user} in week {week}."
                )
                yield SummaryChunk(
                    chunk_type="complete",
                    content="",
                    metadata={"total_contributions": 0, "summary_id": summary_id}
                )
                return
            
            # Generate metadata first
            metadata = self._generate_metadata(contributions, week, start_time, 0)
            yield SummaryChunk(
                chunk_type="metadata",
                content="",
                metadata=metadata.model_dump()
            )
            
            # Generate progress report
            yield SummaryChunk(chunk_type="section", section="progress", content="# Weekly Progress Report\n\n")
            
            progress_report = await self._generate_progress_report(user, week, contributions, request)
            
            # Stream the summary
            yield SummaryChunk(chunk_type="content", section="summary", content=f"## Summary\n{progress_report.summary}\n\n")
            
            # Stream accomplishments
            if progress_report.key_accomplishments:
                accomplishments_text = "\n".join([f"- {item}" for item in progress_report.key_accomplishments])
                yield SummaryChunk(chunk_type="content", section="accomplishments", content=f"## Key Accomplishments\n{accomplishments_text}\n\n")
            
            # Stream impediments
            if progress_report.impediments:
                impediments_text = "\n".join([f"- {item}" for item in progress_report.impediments])
                yield SummaryChunk(chunk_type="content", section="impediments", content=f"## Impediments\n{impediments_text}\n\n")
            else:
                yield SummaryChunk(chunk_type="content", section="impediments", content="## Impediments\n*No impediments reported*\n\n")
            
            # Stream next steps
            if progress_report.next_steps:
                next_steps_text = "\n".join([f"- {item}" for item in progress_report.next_steps])
                yield SummaryChunk(chunk_type="content", section="next_steps", content=f"## Next Steps\n{next_steps_text}\n\n")
            else:
                yield SummaryChunk(chunk_type="content", section="next_steps", content="## Next Steps\n*No remaining tasks assigned*\n\n")
            
            # Final completion with timing metrics
            processing_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            yield SummaryChunk(
                chunk_type="complete",
                content="",
                metadata={
                    "summary_id": summary_id,
                    "processing_time_ms": processing_time_ms,
                    "total_contributions": len(contributions),
                    "status": "success"
                }
            )
            
        except Exception as e:
            logger.error("Streaming weekly progress report failed",
                        user=user,
                        week=week,
                        error=str(e))
            yield SummaryChunk(
                chunk_type="error",
                content=f"Error generating progress report: {str(e)}",
                metadata={"status": "error", "error_type": type(e).__name__}
            )
    
    async def _generate_progress_report(self, user: str, week: str, contributions: List[GitHubContribution], request: SummaryRequest) -> WeeklyProgressOutput:
        """Generate structured progress report using AI"""
        contributions_summary = self._format_contributions_for_prompt(contributions)
        
        parser = PydanticOutputParser(pydantic_object=WeeklyProgressOutput)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are Auto-Pulse, a helpful assistant that generates weekly progress reports for developers.
Auto-Pulse never starts its response by saying a question or idea or observation was good, great, fascinating, profound, excellent, or any other positive adjective. It skips the flattery and responds directly.
                          
You are generating a weekly progress report for developer "{user}". 

Create a brief, professional report similar to a weekly scrum update.

Focus on:
- What was accomplished this week (brief, factual)
- Key achievements and deliverables
- Any blockers or impediments encountered
- Planned next steps (infer from open issues and work patterns)

If no impediments are apparent from the contributions, use an empty list.
If no clear next steps can be inferred, indicate "No remaining tasks assigned".

{parser.get_format_instructions()}"""),
            HumanMessage(content=f"""Analyze {user}'s contributions for week {week}:

{contributions_summary}

Generate a weekly progress report for {user}. Be concise and professional.""")
        ])
        
        chain = prompt | self.llm | parser
        
        try:
            result = await chain.ainvoke({})
            return result
        except Exception as e:
            logger.warning("Failed to parse structured progress report, using fallback", error=str(e))
            # Fallback to basic report
            return WeeklyProgressOutput(
                summary=f"{user} completed {len(contributions)} contributions this week across various repositories.",
                key_accomplishments=[f"Completed {len(contributions)} development tasks"],
                impediments=[],
                next_steps=["Continue with assigned development tasks"]
            )
    
    def _format_contributions_for_prompt(self, contributions: List[GitHubContribution]) -> str:
        """Format contributions for AI prompt"""
        formatted = []
        for contrib in contributions:
            if isinstance(contrib, CommitContribution):
                formatted.append(f"COMMIT in {contrib.repository}: {contrib.message}")
            elif isinstance(contrib, PullRequestContribution):
                formatted.append(f"PULL REQUEST in {contrib.repository}: {contrib.title} ({contrib.state})")
            elif isinstance(contrib, IssueContribution):
                formatted.append(f"ISSUE in {contrib.repository}: {contrib.title} ({contrib.state})")
            elif isinstance(contrib, ReleaseContribution):
                formatted.append(f"RELEASE in {contrib.repository}: {contrib.name} ({contrib.tag_name})")
        
        return "\n".join(formatted) if formatted else "No detailed contribution data available."
    
    def _generate_metadata(self, contributions: List[GitHubContribution], week: str, start_time: datetime, processing_time_ms: int) -> SummaryMetadata:
        """Generate metadata about the contributions"""
        commits_count = 0
        pull_requests_count = 0
        issues_count = 0
        releases_count = 0
        repositories = set()
        
        for contrib in contributions:
            repositories.add(contrib.repository)
            
            if isinstance(contrib, CommitContribution):
                commits_count += 1
            elif isinstance(contrib, PullRequestContribution):
                pull_requests_count += 1
            elif isinstance(contrib, IssueContribution):
                issues_count += 1
            elif isinstance(contrib, ReleaseContribution):
                releases_count += 1
        
        return SummaryMetadata(
            total_contributions=len(contributions),
            commits_count=commits_count,
            pull_requests_count=pull_requests_count,
            issues_count=issues_count,
            releases_count=releases_count,
            repositories=list(repositories),
            time_period=week,
            generated_at=datetime.now(timezone.utc),
            processing_time_ms=processing_time_ms
        )
    
    def _create_empty_summary(self, summary_id: str, user: str, week: str, start_time: datetime) -> SummaryResponse:
        """Create summary when no contributions are found"""
        processing_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        metadata = SummaryMetadata(
            total_contributions=0,
            commits_count=0,
            pull_requests_count=0,
            issues_count=0,
            releases_count=0,
            repositories=[],
            time_period=week,
            generated_at=datetime.now(timezone.utc),
            processing_time_ms=processing_time_ms
        )
        
        return SummaryResponse(
            summary_id=summary_id,
            user=user,
            week=week,
            overview=f"No contributions found for {user} in week {week}.",
            commits_summary="No commits made this week.",
            pull_requests_summary="No pull requests created this week.",
            issues_summary="No issues created this week.",
            releases_summary="No releases published this week.",
            analysis="No activity to analyze for this week.",
            key_achievements=[],
            areas_for_improvement=["No remaining tasks assigned"],
            metadata=metadata,
            generated_at=datetime.now(timezone.utc)
        )
    
    def get_summary(self, summary_id: str) -> Optional[SummaryResponse]:
        """Retrieve a previously generated summary"""
        return self.summaries_store.get(summary_id)
    
 