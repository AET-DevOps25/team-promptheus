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
from asyncio import gather

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


class ContributionSummary(PydanticBaseModel):
    """Detailed summary of all contribution data"""
    detailed_summary: str = Field(description="Comprehensive summary of all contributions with full context and details")


class AnalysisExpertOutput(PydanticBaseModel):
    """What was accomplished analysis"""
    accomplishments: List[str] = Field(description="Detailed list of what was accomplished")
    technical_work: str = Field(description="Technical work completed")
    impact: str = Field(description="Impact of the work done")


class ImpedimentsExpertOutput(PydanticBaseModel):
    """Impediments and blockers analysis"""
    current_impediments: List[str] = Field(description="Current blockers or impediments")
    potential_risks: List[str] = Field(description="Potential risks identified from the work pattern")


class TodosExpertOutput(PydanticBaseModel):
    """Areas for improvement and next steps"""
    improvement_areas: List[str] = Field(description="Areas that could be improved")
    next_steps: List[str] = Field(description="Recommended next steps")
    follow_ups: List[str] = Field(description="Required follow-up actions")


class TipsExpertOutput(PydanticBaseModel):
    """Tips and recommendations"""
    productivity_tips: List[str] = Field(description="Tips to improve productivity")
    best_practices: List[str] = Field(description="Best practice recommendations")
    tools_suggestions: List[str] = Field(description="Tool or process suggestions")


class FinalSummaryOutput(PydanticBaseModel):
    """Final combined expert analysis"""
    executive_summary: str = Field(description="Executive summary of the week's work")
    key_accomplishments: List[str] = Field(description="Most important accomplishments")
    critical_impediments: List[str] = Field(description="Most critical impediments to address")
    priority_improvements: List[str] = Field(description="Highest priority improvement areas")
    actionable_tips: List[str] = Field(description="Most actionable tips and recommendations")


class SummaryService:
    """Simplified Mixture of Experts Summary Service"""
    model_name = os.getenv("LANGCHAIN_MODEL_NAME", "gpt-4-turbo")
    temperature = 0.2
    max_tokens = 2000
    
    def __init__(self, ingestion_service: "ContributionsIngestionService"):
        self.ingestion_service = ingestion_service
        self.summaries_store: Dict[str, SummaryResponse] = {}

        logger.info("SummaryService initialized", model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens)
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    @time_operation(summary_generation_duration, {"repository": "unknown", "username": "unknown"})
    async def generate_summary(self, user: str, week: str, request: SummaryRequest, summary_id: Optional[str] = None) -> SummaryResponse:
        """Generate a weekly progress report using Mixture of Experts approach"""
        start_time = datetime.now(timezone.utc)
        if summary_id is None:
            summary_id = generate_uuidv7()
        
        try:
            logger.info("Starting summary generation", user=user, week=week, summary_id=summary_id)
            
            # Step 1: Get contributions
            contributions = self.ingestion_service.get_user_week_contributions(user, week)
            
            if not contributions:
                logger.warning("No contributions found", user=user, week=week)
                return self._create_empty_summary(summary_id, user, week, start_time)
            
            # Step 2: Create detailed summary of all contribution data
            detailed_summary = await self._summarize_all_contributions(contributions)
            
            # Step 3: Run expert analysis in parallel
            analysis_expert, impediments_expert, todos_expert, tips_expert = await gather(
                self._analysis_expert(detailed_summary, contributions),
                self._impediments_expert(detailed_summary, contributions),
                self._todos_expert(detailed_summary, contributions),
                self._tips_expert(detailed_summary, contributions)
            )
            
            # Step 4: Combine expert outputs
            final_summary = await self._combining_expert(
                detailed_summary, analysis_expert, impediments_expert, todos_expert, tips_expert
            )
            
            # Step 5: Create response
            processing_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            metadata = self._generate_metadata(contributions, week, start_time, processing_time_ms)
            
            summary_response = SummaryResponse(
                summary_id=summary_id,
                user=user,
                week=week,
                overview=final_summary.executive_summary,
                commits_summary=analysis_expert.technical_work,
                pull_requests_summary=analysis_expert.accomplishments,
                issues_summary=analysis_expert.accomplishments,
                releases_summary=analysis_expert.accomplishments,
                analysis=analysis_expert.impact,
                key_achievements=final_summary.key_accomplishments,
                areas_for_improvement=final_summary.priority_improvements + final_summary.actionable_tips,
                metadata=metadata,
                generated_at=datetime.now(timezone.utc)
            )
            
            self.summaries_store[summary_id] = summary_response
            
            logger.info("MoE summary completed", user=user, week=week, summary_id=summary_id)
            return summary_response
            
        except Exception as e:
            logger.error("MoE summary generation failed", user=user, week=week, error=str(e))
            raise
    
    async def _summarize_all_contributions(self, contributions: List[GitHubContribution]) -> ContributionSummary:
        """Expert 0: Comprehensive summarization of all contribution data"""
        contributions_data = self._format_all_contribution_data(contributions)
        
        parser = PydanticOutputParser(pydantic_object=ContributionSummary)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are the Contribution Summarization Expert in Auto-Pulse.
Your role is to create a comprehensive, detailed summary of ALL contribution data provided.

Do not filter or highlight - include ALL details from commits, PRs, issues, releases.
Include technical details, code changes, discussions, review comments, everything.

{parser.get_format_instructions()}"""),
            HumanMessage(content=f"Summarize ALL of this contribution data comprehensively:\n\n{contributions_data}")
        ])
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({})
    
    async def _analysis_expert(self, summary: ContributionSummary, contributions: List[GitHubContribution]) -> AnalysisExpertOutput:
        """Expert 1: Analysis of what was accomplished"""
        parser = PydanticOutputParser(pydantic_object=AnalysisExpertOutput)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are the Analysis Expert in Auto-Pulse's Mixture of Experts system.
Your specialty is analyzing what was accomplished and its impact.

Focus on:
- What specific work was completed
- Technical achievements and deliverables  
- Business/project impact of the work
- Quality and scope of contributions

{parser.get_format_instructions()}"""),
            HumanMessage(content=f"Analyze what was accomplished based on this summary:\n\n{summary.detailed_summary}")
        ])
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({})
    
    async def _impediments_expert(self, summary: ContributionSummary, contributions: List[GitHubContribution]) -> ImpedimentsExpertOutput:
        """Expert 2: Impediments and blockers analysis"""
        parser = PydanticOutputParser(pydantic_object=ImpedimentsExpertOutput)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are the Impediments Expert in Auto-Pulse's Mixture of Experts system.
Your specialty is identifying blockers, risks, and impediments.

Look for signs of:
- Blocked or stalled work
- Technical debt or complexity issues
- Process bottlenecks
- Resource constraints
- Dependencies causing delays

{parser.get_format_instructions()}"""),
            HumanMessage(content=f"Identify impediments and risks from this summary:\n\n{summary.detailed_summary}")
        ])
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({})
    
    async def _todos_expert(self, summary: ContributionSummary, contributions: List[GitHubContribution]) -> TodosExpertOutput:
        """Expert 3: Areas for improvement and next steps"""
        parser = PydanticOutputParser(pydantic_object=TodosExpertOutput)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are the Todos & Improvement Expert in Auto-Pulse's Mixture of Experts system.
Your specialty is identifying improvement areas and next steps.

Focus on:
- Areas that could be improved in the work
- Logical next steps based on current progress
- Follow-up actions needed
- Process improvements

{parser.get_format_instructions()}"""),
            HumanMessage(content=f"Identify improvement areas and next steps from this summary:\n\n{summary.detailed_summary}")
        ])
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({})
    
    async def _tips_expert(self, summary: ContributionSummary, contributions: List[GitHubContribution]) -> TipsExpertOutput:
        """Expert 4: Tips and recommendations"""
        parser = PydanticOutputParser(pydantic_object=TipsExpertOutput)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are the Tips & Recommendations Expert in Auto-Pulse's Mixture of Experts system.
Your specialty is providing actionable tips and best practice recommendations.

Focus on:
- Productivity improvement tips
- Best practices for the type of work being done
- Tool and process recommendations
- Code quality and development tips

{parser.get_format_instructions()}"""),
            HumanMessage(content=f"Provide tips and recommendations based on this summary:\n\n{summary.detailed_summary}")
        ])
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({})
    
    async def _combining_expert(self, summary: ContributionSummary, analysis: AnalysisExpertOutput, 
                               impediments: ImpedimentsExpertOutput, todos: TodosExpertOutput, 
                               tips: TipsExpertOutput) -> FinalSummaryOutput:
        """Final Expert: Combines all expert inputs based on relevance"""
        parser = PydanticOutputParser(pydantic_object=FinalSummaryOutput)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are the Combining Expert in Auto-Pulse's Mixture of Experts system.
Your role is to synthesize inputs from all specialist experts and create a final, coherent summary.

The Combining Expert never starts its summary by saying a question or idea or observation was good, great, fascinating, profound, excellent, significant, or any other positive adjective. It skips the flattery and responds directly.

Prioritize based on:
- Relevance to the user's work
- Criticality and impact
- Actionability
- Strategic importance

Combine these expert analyses into a final summary:

ANALYSIS EXPERT:
{analysis.model_dump_json(indent=2)}

IMPEDIMENTS EXPERT:  
{impediments.model_dump_json(indent=2)}

TODOS EXPERT:
{todos.model_dump_json(indent=2)}

TIPS EXPERT:
{tips.model_dump_json(indent=2)}""")
        ])
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({})
    
    def _format_all_contribution_data(self, contributions: List[GitHubContribution]) -> str:
        """Format ALL contribution data for comprehensive analysis"""
        formatted = []
        for contrib in contributions:
            if isinstance(contrib, CommitContribution):
                formatted.append(f"""COMMIT in {contrib.repository}:
- Message: {contrib.message}
- SHA: {contrib.sha}
- Date: {contrib.created_at}
- Author: {contrib.author_info.name} ({contrib.author_info.email})
- Files: {len(contrib.files)} files changed
- Stats: +{contrib.stats.additions}/-{contrib.stats.deletions} ({contrib.stats.total} total changes)
- Files modified: {', '.join([f.filename for f in contrib.files[:5]])}{'...' if len(contrib.files) > 5 else ''}""")
            elif isinstance(contrib, PullRequestContribution):
                formatted.append(f"""PULL REQUEST in {contrib.repository}:
- Title: {contrib.title}
- State: {contrib.state}
- Number: #{contrib.number}
- Date: {contrib.created_at}
- Body: {contrib.body or 'No description'}
- Comments: {contrib.comments}
- Review comments: {contrib.review_comments}
- Commits: {contrib.commits}
- Changes: +{contrib.additions}/-{contrib.deletions} in {contrib.changed_files} files""")
            elif isinstance(contrib, IssueContribution):
                formatted.append(f"""ISSUE in {contrib.repository}:
- Title: {contrib.title}
- State: {contrib.state}
- Number: #{contrib.number}
- Date: {contrib.created_at}
- Body: {contrib.body or 'No description'}
- Comments: {contrib.comments}
- Labels: {', '.join([label.name for label in contrib.labels]) if contrib.labels else 'None'}
- Assignees: {', '.join([assignee.login for assignee in contrib.assignees]) if contrib.assignees else 'None'}""")
            elif isinstance(contrib, ReleaseContribution):
                formatted.append(f"""RELEASE in {contrib.repository}:
- Name: {contrib.name}
- Tag: {contrib.tag_name}
- Date: {contrib.created_at}
- Published: {contrib.published_at or 'Not published'}
- Body: {contrib.body or 'No release notes'}
- Draft: {contrib.draft}
- Prerelease: {contrib.prerelease}
- Assets: {len(contrib.assets)} assets""")
        
        return "\n\n".join(formatted) if formatted else "No contribution data available."
   
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

    # Simplified streaming - just calls regular generate_summary for now
    async def generate_summary_stream(self, user: str, week: str, request: SummaryRequest) -> AsyncGenerator[SummaryChunk, None]:
        """Generate a streaming weekly progress report (simplified)"""
        try:
            summary = await self.generate_summary(user, week, request)
            
            # Convert to streaming format
            yield SummaryChunk(
                chunk_type="content",
                section="overview",
                content=summary.overview
            )
            
            yield SummaryChunk(
                chunk_type="complete",
                content="",
                metadata={
                    "summary_id": summary.summary_id,
                    "total_contributions": summary.metadata.total_contributions,
                    "status": "success"
                }
            )
            
        except Exception as e:
            yield SummaryChunk(
                chunk_type="error",
                content=f"Error generating summary: {str(e)}",
                metadata={"status": "error", "error_type": type(e).__name__}
            )
    
 