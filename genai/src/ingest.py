import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog

from .contributions import GitHubContentService
from .meilisearch import MeilisearchService
from .metrics import (
    meilisearch_duration,
    meilisearch_requests,
    record_error_metrics,
    record_request_metrics,
    time_operation,
)
from .models import (
    ContributionsIngestRequest,
    ContributionsIngestResponse,
    ContributionsStatusResponse,
    ContributionType,
    GitHubContribution,
    IngestTaskResponse,
    IngestTaskStatus,
    TaskStatus,
    generate_uuidv7,
)
from .summary import SummaryService

logger = structlog.get_logger()


class ContributionsIngestionService:
    """Service for ingesting GitHub contributions using metadata and fetching content as needed."""

    def __init__(
        self,
        meilisearch_service: MeilisearchService | None = None,
        summary_service: SummaryService | None = None,
    ) -> None:
        # Store contributions by [user, week] key
        self.contributions_store: dict[str, dict[str, GitHubContribution]] = {}
        self.embedding_jobs: dict[str, dict[str, Any]] = {}
        self.ingest_tasks: dict[str, IngestTaskStatus] = {}  # Track ingestion tasks
        self.meilisearch_service = meilisearch_service
        self.summary_service = summary_service  # Will be injected to avoid circular imports

    def _get_user_week_key(self, user: str, week: str) -> str:
        """Generate key for user-week tuple."""
        return f"{user}:{week}"

    async def start_ingestion_task(self, request: ContributionsIngestRequest) -> IngestTaskResponse:
        """Start an asynchronous ingestion task using metadata and fetching selected content."""
        task_id = generate_uuidv7()

        # Generate summary_id upfront for unified workflow
        summary_id = generate_uuidv7() if self.summary_service else None

        # Create initial task status
        task_status = IngestTaskStatus(
            task_id=task_id,
            user=request.user,
            week=request.week,
            repository=request.repository,
            status=TaskStatus.QUEUED,
            total_contributions=len(request.contributions),
            ingested_count=0,
            failed_count=0,
            created_at=datetime.now(UTC),
        )

        self.ingest_tasks[task_id] = task_status

        # Start the ingestion task asynchronously
        asyncio.create_task(self._process_ingestion_task(task_id, request, summary_id))

        # Return immediate response
        return IngestTaskResponse(
            task_id=task_id,
            user=request.user,
            week=request.week,
            repository=request.repository,
            status=TaskStatus.QUEUED,
            total_contributions=len(request.contributions),
            summary_id=summary_id,
            created_at=datetime.now(UTC),
        )

    async def _process_ingestion_task(
        self,
        task_id: str,
        request: ContributionsIngestRequest,
        summary_id: str | None = None,
    ) -> None:
        """Process the full ingestion and summarization task asynchronously."""
        try:
            # Phase 1: Start ingesting
            if task_id in self.ingest_tasks:
                self.ingest_tasks[task_id].status = TaskStatus.INGESTING
                self.ingest_tasks[task_id].started_at = datetime.now(UTC)

            logger.info(
                "Starting ingestion phase",
                task_id=task_id,
                user=request.user,
                week=request.week,
            )

            # Fetch content for selected contributions using GitHub service
            pat_info = "provided" if request.github_pat else "not provided"
            logger.info(
                "Creating GitHubContentService",
                user=request.user,
                week=request.week,
                repository=request.repository,
                github_pat=pat_info,
            )
            github_content_service = GitHubContentService(request.github_pat)
            contributions = await github_content_service.fetch_contributions(
                repository=request.repository,
                user=request.user,
                week=request.week,
                metadata_list=request.contributions,
            )

            # Process the fetched contributions
            await self._ingest_contributions_content(request.user, request.week, contributions)

            # Update ingestion counts
            if task_id in self.ingest_tasks:
                self.ingest_tasks[task_id].ingested_count = len(contributions)
                self.ingest_tasks[task_id].failed_count = len([m for m in request.contributions if m.selected]) - len(
                    contributions
                )

            logger.info(
                "Ingestion phase completed",
                task_id=task_id,
                user=request.user,
                week=request.week,
                ingested_count=len(contributions),
            )

            # Phase 2: Start summarizing (only if we have a summary service and contributions)
            if self.summary_service and len(contributions) > 0:
                if task_id in self.ingest_tasks:
                    self.ingest_tasks[task_id].status = TaskStatus.SUMMARIZING

                logger.info(
                    "Starting summarization phase",
                    task_id=task_id,
                    user=request.user,
                    week=request.week,
                )

                # Generate summary
                summary = await self.summary_service.generate_summary(request.user, request.week, summary_id)

                # Store summary in task
                if task_id in self.ingest_tasks:
                    self.ingest_tasks[task_id].summary = summary

                logger.info(
                    "Summarization phase completed",
                    task_id=task_id,
                    user=request.user,
                    week=request.week,
                )

            # Phase 3: Mark as done
            if task_id in self.ingest_tasks:
                self.ingest_tasks[task_id].status = TaskStatus.DONE
                self.ingest_tasks[task_id].completed_at = datetime.now(UTC)

                started_at = self.ingest_tasks[task_id].started_at
                completed_at = self.ingest_tasks[task_id].completed_at
                if started_at and completed_at:
                    processing_time = completed_at - started_at
                    self.ingest_tasks[task_id].processing_time_ms = int(processing_time.total_seconds() * 1000)

            logger.info(
                "Full task completed successfully",
                task_id=task_id,
                user=request.user,
                week=request.week,
                status="done",
            )

        except Exception as e:
            # Update task status to failed
            if task_id in self.ingest_tasks:
                self.ingest_tasks[task_id].status = TaskStatus.FAILED
                self.ingest_tasks[task_id].error_message = str(e)
                self.ingest_tasks[task_id].completed_at = datetime.now(UTC)

            logger.exception(
                "Ingestion task failed",
                task_id=task_id,
                user=request.user,
                week=request.week,
                error=str(e),
            )

    def get_ingestion_task_status(self, task_id: str) -> IngestTaskStatus | None:
        """Get the status of an ingestion task."""
        return self.ingest_tasks.get(task_id)

    @time_operation(meilisearch_duration, {"operation": "ingest"})
    async def ingest_contributions(self, request: ContributionsIngestRequest) -> ContributionsIngestResponse:
        """Legacy method - now delegates to task-based approach."""
        try:
            record_request_metrics(meilisearch_requests, {"operation": "ingest"}, "started")

            # Fetch content for selected contributions using GitHub service
            github_content_service = GitHubContentService(request.github_pat)
            contributions = await github_content_service.fetch_contributions(
                repository=request.repository,
                user=request.user,
                week=request.week,
                metadata_list=request.contributions,
            )

            # Process the fetched contributions
            (
                ingested_count,
                failed_count,
                embedding_job_id,
            ) = await self._ingest_contributions_content(request.user, request.week, contributions)

            record_request_metrics(meilisearch_requests, {"operation": "ingest"}, "success")

            logger.info(
                "Contributions ingestion completed",
                user=request.user,
                week=request.week,
                ingested_count=ingested_count,
                failed_count=failed_count,
                embedding_job_id=embedding_job_id,
            )

            return ContributionsIngestResponse(
                user=request.user,
                week=request.week,
                ingested_count=ingested_count,
                failed_count=failed_count,
                embedding_job_id=embedding_job_id,
                status="processing",
            )

        except Exception as e:
            record_request_metrics(meilisearch_requests, {"operation": "ingest"}, "error")
            record_error_metrics(meilisearch_requests, {"operation": "ingest"}, type(e).__name__)
            logger.exception(
                "Contributions ingestion failed",
                user=request.user,
                week=request.week,
                error=str(e),
            )
            raise

    async def _ingest_contributions_content(
        self, user: str, week: str, contributions: list[GitHubContribution]
    ) -> tuple[int, int, str]:
        """Ingest the actual contribution content."""
        user_week_key = self._get_user_week_key(user, week)

        ingested_count = 0
        failed_count = 0
        embedding_job_id = generate_uuidv7()

        # Initialize storage for this user-week if not exists
        if user_week_key not in self.contributions_store:
            self.contributions_store[user_week_key] = {}

        # Process each contribution
        for contribution in contributions:
            try:
                # Store contribution with user-week context
                self.contributions_store[user_week_key][contribution.id] = contribution

                # Prepare for embedding (placeholder)
                await self._prepare_for_embedding(contribution, user, week)

                ingested_count += 1

            except Exception as e:
                logger.exception(
                    "Failed to ingest contribution",
                    contribution_id=contribution.id,
                    user=user,
                    week=week,
                    error=str(e),
                )
                failed_count += 1

        # Create embedding job
        self.embedding_jobs[embedding_job_id] = {
            "user": user,
            "week": week,
            "status": "processing",
            "total": len(contributions),
            "processed": ingested_count,
            "failed": failed_count,
            "created_at": datetime.now(UTC),
        }

        # Start embedding process (placeholder)
        asyncio.create_task(self._process_embeddings(embedding_job_id, contributions, user, week))

        return ingested_count, failed_count, embedding_job_id

    async def _prepare_for_embedding(self, contribution: GitHubContribution, user: str, week: str) -> None:
        """Prepare contribution for embedding by extracting text content with user-week context."""
        # This is now handled by the Meilisearch service during indexing
        logger.debug(
            "Prepared contribution for embedding",
            contribution_id=contribution.id,
            user=user,
            week=week,
        )

    def _extract_text_content(self, contribution: GitHubContribution) -> str:
        """Extract searchable text content from contribution."""
        content_parts = []

        # Common fields
        content_parts.append(f"Repository: {contribution.repository}")
        content_parts.append(f"Author: {contribution.author}")

        if contribution.type == ContributionType.COMMIT:
            # Handle commit-specific attributes
            if hasattr(contribution, "message"):
                content_parts.append(f"Commit: {contribution.message}")
            if hasattr(contribution, "files"):
                for file in contribution.files:
                    content_parts.append(f"File: {file.filename}")
                    if file.patch:
                        content_parts.append(f"Changes: {file.patch[:500]}")  # Truncate patch

        elif contribution.type == ContributionType.PULL_REQUEST:
            # Handle pull request-specific attributes
            if hasattr(contribution, "title"):
                content_parts.append(f"Pull Request: {contribution.title}")
            if hasattr(contribution, "body") and contribution.body:
                content_parts.append(f"Description: {contribution.body}")

            # Include comments
            if hasattr(contribution, "comments_data"):
                for comment in contribution.comments_data:
                    content_parts.append(f"Comment by {comment.user.login}: {comment.body}")

            # Include review comments
            if hasattr(contribution, "reviews_data"):
                for review in contribution.reviews_data:
                    if review.body:
                        content_parts.append(f"Review by {review.user.login}: {review.body}")
                    for comment in review.comments:
                        content_parts.append(f"Review comment: {comment.body}")

        elif contribution.type == ContributionType.ISSUE:
            # Handle issue-specific attributes
            if hasattr(contribution, "title"):
                content_parts.append(f"Issue: {contribution.title}")
            if hasattr(contribution, "body") and contribution.body:
                content_parts.append(f"Description: {contribution.body}")

            # Include comments
            if hasattr(contribution, "comments_data"):
                for comment in contribution.comments_data:
                    content_parts.append(f"Comment by {comment.user.login}: {comment.body}")

        elif contribution.type == ContributionType.RELEASE:
            # Handle release-specific attributes
            if hasattr(contribution, "name"):
                content_parts.append(f"Release: {contribution.name}")
            if hasattr(contribution, "body") and contribution.body:
                content_parts.append(f"Release Notes: {contribution.body}")

        return "\n".join(content_parts)

    async def _process_embeddings(
        self, job_id: str, contributions: list[GitHubContribution], user: str, week: str
    ) -> None:
        """Process embeddings for contributions using Meilisearch."""
        try:
            if self.meilisearch_service:
                # Index contributions in Meilisearch
                result = await self.meilisearch_service.index_contributions(user, week, contributions)

                # Update job status
                if job_id in self.embedding_jobs:
                    self.embedding_jobs[job_id]["status"] = "completed"
                    self.embedding_jobs[job_id]["completed_at"] = datetime.now(UTC)
                    self.embedding_jobs[job_id]["meilisearch_task_uid"] = result.get("task_uid")
                    self.embedding_jobs[job_id]["indexed_count"] = result.get("indexed", 0)
                    self.embedding_jobs[job_id]["failed_count"] = result.get("failed", 0)

                logger.info(
                    "Meilisearch indexing completed",
                    job_id=job_id,
                    user=user,
                    week=week,
                    indexed_count=result.get("indexed", 0),
                    failed_count=result.get("failed", 0),
                )
            else:
                # Fallback: simulate processing without Meilisearch
                await asyncio.sleep(1.0)

                if job_id in self.embedding_jobs:
                    self.embedding_jobs[job_id]["status"] = "completed"
                    self.embedding_jobs[job_id]["completed_at"] = datetime.now(UTC)

                logger.info(
                    "Embedding processing completed (no Meilisearch)",
                    job_id=job_id,
                    user=user,
                    week=week,
                )

        except Exception as e:
            if job_id in self.embedding_jobs:
                self.embedding_jobs[job_id]["status"] = "failed"
                self.embedding_jobs[job_id]["error"] = str(e)

            logger.exception(
                "Embedding processing failed",
                job_id=job_id,
                user=user,
                week=week,
                error=str(e),
            )

    async def get_contributions_status(self, user: str, week: str) -> ContributionsStatusResponse:
        """Get status of contributions and embeddings for a specific user's week."""
        user_week_key = self._get_user_week_key(user, week)

        total_contributions = len(self.contributions_store.get(user_week_key, {}))

        # Get embedded contributions count from Meilisearch
        embedded_contributions = 0
        meilisearch_status = "unknown"

        if self.meilisearch_service:
            try:
                embedded_contributions = await self.meilisearch_service.get_contributions_count(user, week)
                health = await self.meilisearch_service.health_check()
                meilisearch_status = health["status"]
            except Exception as e:
                logger.exception("Failed to get Meilisearch status", error=str(e))
                meilisearch_status = "unhealthy"
        else:
            # Fallback when no Meilisearch service
            embedded_contributions = total_contributions
            meilisearch_status = "not_configured"

        pending_embeddings = max(0, total_contributions - embedded_contributions)

        # Get last update time
        last_updated = datetime.now(UTC)
        if self.contributions_store.get(user_week_key):
            last_updated = max(contrib.created_at for contrib in self.contributions_store[user_week_key].values())

        return ContributionsStatusResponse(
            user=user,
            week=week,
            total_contributions=total_contributions,
            embedded_contributions=embedded_contributions,
            pending_embeddings=pending_embeddings,
            last_updated=last_updated,
            meilisearch_status=meilisearch_status,
        )

    def get_user_week_contributions(self, user: str, week: str) -> list[GitHubContribution]:
        """Get all contributions for a specific user's week."""
        user_week_key = self._get_user_week_key(user, week)
        return list(self.contributions_store.get(user_week_key, {}).values())
