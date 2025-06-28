"""Summary service for generating weekly progress reports."""

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate

# LangChain imports
from langchain.schema import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from .agent_tools import all_tools, get_tool_descriptions
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


class SummaryService:
    """Service for generating weekly progress reports."""

    def __init__(self, ingestion_service: "ContributionsIngestionService") -> None:
        """Initialize the summary service.

        Args:
            ingestion_service: Service for ingesting and retrieving contributions.
        """
        self.ingestion_service = ingestion_service

        # Initialize LangChain components with Ollama
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "https://gpu.aet.cit.tum.de/ollama")
        ollama_api_key = os.getenv("OLLAMA_API_KEY")
        model_name = os.getenv("LANGCHAIN_MODEL_NAME", "llama3.3:latest")

        self.llm = ChatOllama(
            model=model_name,
            base_url=ollama_base_url,
            client_kwargs={"headers": {"Authorization": f"Bearer {ollama_api_key}"}},
            temperature=0.2,
            num_predict=2500,  # Use num_predict instead of max_tokens for Ollama
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
        start_time = datetime.now(UTC)
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
                return self._create_empty_summary(summary_id, user, week, start_time)

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
                analysis="Weekly progress report generated",
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
        parser = PydanticOutputParser(pydantic_object=WeeklyProgressOutput)
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=f"""You are Auto-Pulse, a helpful assistant that generates weekly progress
reports for developers.
Auto-Pulse never starts its response by saying a question or idea or observation was good, great,
fascinating, profound, excellent, or any other positive adjective. It skips the flattery and responds directly.

You have access to the following tools:

{tool_descriptions}

You are generating a weekly progress report for developer \"{user}\".

Create a brief, professional, up-to one page report similar to a weekly scrum update.

Focus on:
- What was accomplished this week (brief, factual) - enhance with tool data when helpful
- Key achievements and deliverables - use tools to understand impact
- Any blockers or impediments encountered - check related issues if needed
- Planned next steps (infer from open issues and work patterns) - use tools to identify upcoming work

If no impediments are apparent from the contributions, use an empty list.
If no clear next steps can be inferred, indicate \"No remaining tasks assigned\".

{parser.get_format_instructions()}"""
                ),
                HumanMessage(
                    content=f"""Analyze {user}'s contributions for week {week}:

{contributions_summary}

Generate a weekly progress report for {user}. Be concise and professional.
Consider using available tools to provide richer context where appropriate."""
                ),
            ]
        )

        # Use the agent for enhanced summary generation
        # First try with the structured chain, but the agent can use tools if needed
        chain = prompt | self.llm | parser

        try:
            return await chain.ainvoke({})
        except Exception as e:
            logger.warning(
                "Failed to parse structured progress report, using fallback",
                error=str(e),
            )
            # Fallback to basic report
            return WeeklyProgressOutput(
                summary=f"{user} completed {len(contributions)} contributions this week across various repositories.",
                key_accomplishments=[f"Completed {len(contributions)} development tasks"],
                impediments=[],
                next_steps=["Continue with assigned development tasks"],
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
            generated_at=datetime.now(UTC),
        )
