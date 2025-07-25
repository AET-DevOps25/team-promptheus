"""Summary service for generating weekly progress reports."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

import structlog
from langchain.prompts import ChatPromptTemplate

# LangChain imports
from langchain.schema import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from .agent_tools import all_tools, get_tool_descriptions
from .llm_service import LLMService
from .metrics import (
    record_request_metrics,
    summary_generation_duration,
    summary_generation_requests,
    time_operation,
)
from .models import (
    CommitContribution,
    GitHubContribution,
    IssueContribution,
    PullRequestContribution,
    ReleaseContribution,
    SummaryMetadata,
    SummaryResponse,
    generate_uuidv7,
)

# Type-only import to avoid circular dependency
if TYPE_CHECKING:
    from .ingest import ContributionsIngestionService

logger = structlog.get_logger()


class WeeklyProgressOutput(PydanticBaseModel):
    """Structured output for weekly progress report."""

    summary: str = Field(description="Brief summary of work completed this week (2-3 sentences)")
    key_accomplishments: list[str] = Field(description="List of key accomplishments this week")
    impediments: list[str] = Field(description="Current blockers or impediments (empty list if none)")
    next_steps: list[str] = Field(description="Planned work for next week based on assignments and context")
    analysis: str = Field(description="Analysis of the week's contributions")


class SummaryService:
    """Service for generating weekly progress reports."""

    def __init__(self, ingestion_service: "ContributionsIngestionService") -> None:
        """Initialize the summary service.

        Args:
            ingestion_service: Service for ingesting and retrieving contributions.
        """
        self.ingestion_service = ingestion_service

        # Initialize LLM using centralized service
        self.llm = LLMService.create_llm(
            temperature=0.2,
            max_tokens=2500,
            timeout=120.0,  # Increased timeout
        )

        # Create LangGraph agent for tool-enhanced summary generation
        self.agent = create_react_agent(model=self.llm, tools=all_tools, checkpointer=MemorySaver())

    @time_operation(summary_generation_duration, {"repository": "unknown", "username": "unknown"})
    async def generate_summary(
        self,
        user: str,
        week: str,
        summary_id: str | None = None,
    ) -> SummaryResponse:
        """Generate a weekly progress report."""
        datetime.now(UTC)
        if summary_id is None:
            summary_id = generate_uuidv7()

        try:
            record_request_metrics(
                summary_generation_requests,
                {"repository": "unknown", "username": user, "status": "started"},
                "started",
            )

            logger.info(
                "Starting weekly progress report generation",
                user=user,
                week=week,
                summary_id=summary_id,
            )

            # Get all contributions for the user's week
            contributions = self.ingestion_service.get_user_week_contributions(user, week)

            if not contributions:
                logger.warning("No contributions found for summary", user=user, week=week)
                return self._create_empty_summary(summary_id, user, week)

            # Generate the progress report using AI
            progress_report = await self._generate_progress_report(user, week, contributions)

            # Generate metadata
            metadata = self._generate_metadata(contributions, week)

            # Create final summary response
            summary = SummaryResponse(
                summary_id=summary_id,
                user=user,
                week=week,
                overview=progress_report.summary,
                commits_summary=f"Completed {metadata.commits_count} commits"
                if metadata.commits_count > 0
                else "No commits this week",
                pull_requests_summary=f"Worked on {metadata.pull_requests_count} pull requests"
                if metadata.pull_requests_count > 0
                else "No pull requests this week",
                issues_summary=f"Addressed {metadata.issues_count} issues"
                if metadata.issues_count > 0
                else "No issues this week",
                releases_summary=f"Published {metadata.releases_count} releases"
                if metadata.releases_count > 0
                else "No releases this week",
                analysis=progress_report.analysis,  # Use the critical analysis from the AI
                key_achievements=progress_report.key_accomplishments,
                areas_for_improvement=progress_report.impediments + progress_report.next_steps,
                metadata=metadata,
                generated_at=datetime.now(UTC),
            )

            record_request_metrics(
                summary_generation_requests,
                {"repository": "unknown", "username": user},
                "success",
            )

            logger.info(
                "Weekly progress report generation completed",
                user=user,
                week=week,
                summary_id=summary_id,
                contributions_count=len(contributions),
            )

            return summary

        except Exception as e:
            record_request_metrics(
                summary_generation_requests,
                {"repository": "unknown", "username": user},
                "error",
            )

            logger.exception(
                "Weekly progress report generation failed",
                user=user,
                week=week,
                error=str(e),
            )
            raise

    async def _generate_progress_report(
        self,
        user: str,
        week: str,
        contributions: list[GitHubContribution],
    ) -> WeeklyProgressOutput:
        """Generate structured progress report using AI."""
        contributions_summary = self._format_contributions_for_prompt(contributions)
        tool_descriptions = get_tool_descriptions(all_tools)

        # Bind the Pydantic model to the LLM for structured output
        structured_llm = self.llm.with_structured_output(WeeklyProgressOutput)

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=f"""You are Auto-Pulse, a senior engineering manager assistant that generates weekly progress
reports with critical analysis for developer performance reviews and career development.

Auto-Pulse provides direct, evidence-based feedback without unnecessary pleasantries or flattery.

You have access to the following tools:
{tool_descriptions}

Your role is to analyze developer \"{user}\"\'s work and provide:
1. Factual summary of accomplishments
2. Critical analysis of software engineering practices
3. Actionable feedback for improvement

CRITICAL ANALYSIS GUIDELINES:
- Be direct and honest - managers need truthful assessments for effective 1:1s
- Base ALL observations on concrete evidence from contributions
- Identify both strengths and areas needing improvement
- Focus on patterns that impact code quality, collaboration, and productivity
- Suggest specific improvements tied to career progression

ANALYZE THESE SE BEST PRACTICES:
1. Code Quality & Standards
   - Commit message quality (descriptive, atomic, follows conventions)
   - PR size and scope (small, focused changes vs large, unfocused ones)
   - Testing evidence (are tests mentioned in commits/PRs?)

2. Collaboration & Communication
   - PR descriptions quality
   - Issue tracking discipline
   - Response to feedback (PR review cycles)

3. Development Practices
   - Frequency and consistency of contributions
   - Balance between feature work, bug fixes, and maintenance
   - Documentation habits

4. Technical Leadership
   - Mentoring indicators (reviewing others' PRs, helping with issues)
   - Architectural decisions and design discussions
   - Initiative in addressing technical debt

Use the available tools to gather additional context when needed for accurate analysis.

IMPORTANT: The 'analysis' field must contain a critical, evidence-based assessment of the developer's
software engineering practices this week. Include specific examples and actionable feedback."""
                ),
                HumanMessage(
                    content=f"""Analyze {user}'s contributions for week {week}:

{contributions_summary}

Generate a comprehensive progress report with critical analysis.
Focus on factual observations and specific examples from the contributions.
Use tools when needed to verify facts or gather additional context."""
                ),
            ]
        )

        # Create the chain with structured output
        chain = prompt | structured_llm

        try:
            # Invoke the chain and get the structured response
            return cast("WeeklyProgressOutput", await chain.ainvoke({}))
        except Exception as e:
            logger.warning(
                "Failed to generate structured progress report, using fallback",
                error=str(e),
            )
            # Fallback with basic analysis
            return WeeklyProgressOutput(
                summary=f"{user} completed {len(contributions)} contributions this week across various repositories.",
                key_accomplishments=[f"Completed {len(contributions)} development tasks"],
                impediments=[],
                next_steps=["Continue with assigned development tasks"],
                analysis="Unable to generate a critical analysis of the developer's work this week.",
            )

    def _format_contributions_for_prompt(self, contributions: list[GitHubContribution]) -> str:
        """Format contributions for AI prompt."""
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

    def _generate_metadata(
        self,
        contributions: list[GitHubContribution],
        week: str,
    ) -> SummaryMetadata:
        """Generate metadata about the contributions."""
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
            generated_at=datetime.now(UTC),
        )

    def _create_empty_summary(self, summary_id: str, user: str, week: str) -> SummaryResponse:
        """Create summary when no contributions are found."""
        metadata = SummaryMetadata(
            total_contributions=0,
            commits_count=0,
            pull_requests_count=0,
            issues_count=0,
            releases_count=0,
            repositories=[],
            time_period=week,
            generated_at=datetime.now(UTC),
        )

        # Provide critical analysis even for zero contributions
        analysis = (
            f"No contributions detected for {user} during week {week}. "
            "This absence of activity requires immediate attention:\n\n"
            "CRITICAL OBSERVATIONS:\n"
            "• Zero commits, PRs, or issues indicates complete disengagement from development work\n"
            "• This could signal: blocked work, unclear assignments, personal issues, or role misalignment\n"
            "• Extended periods without contributions impact team velocity and project timelines\n\n"
            "RECOMMENDED MANAGER ACTIONS:\n"
            "1. Schedule immediate 1:1 to understand blockers or challenges\n"
            "2. Review current task assignments and priorities\n"
            "3. Assess if developer has necessary resources and support\n"
            "4. Consider pairing opportunities to re-engage with codebase\n\n"
            "Note: Verify if work is happening outside tracked repositories before drawing conclusions."
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
            analysis=analysis,
            key_achievements=[],
            areas_for_improvement=["Immediate re-engagement with development work required"],
            metadata=metadata,
            generated_at=datetime.now(UTC),
        )
