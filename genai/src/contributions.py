import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import structlog

from .models import (
    GitHubContribution, ContributionType, ContributionsIngestRequest, 
    ContributionsIngestResponse, IngestTaskResponse, IngestTaskStatus,
    ContributionsStatusResponse, generate_uuidv7
)
from .metrics import (
    time_operation, record_request_metrics, record_error_metrics,
    meilisearch_requests, meilisearch_duration
)
from .meilisearch import MeilisearchService

logger = structlog.get_logger()


class ContributionsIngestionService:
    """Service for ingesting GitHub contributions and storing them with embeddings for [user, week] tuples"""
    
    def __init__(self, meilisearch_service: Optional[MeilisearchService] = None):
        # Store contributions by [user, week] key
        self.contributions_store: Dict[str, Dict[str, GitHubContribution]] = {}
        self.embedding_jobs: Dict[str, Dict[str, Any]] = {}
        self.ingest_tasks: Dict[str, IngestTaskStatus] = {}  # Track ingestion tasks
        self.meilisearch_service = meilisearch_service
    
    def _get_user_week_key(self, user: str, week: str) -> str:
        """Generate key for user-week tuple"""
        return f"{user}:{week}"
    
    @time_operation(meilisearch_duration, {"operation": "ingest"})
    async def ingest_contributions(self, request: ContributionsIngestRequest) -> ContributionsIngestResponse:
        """Ingest contributions for a specific user's week and prepare them for embedding"""
        try:
            user_week_key = self._get_user_week_key(request.user, request.week)
            
            record_request_metrics(
                meilisearch_requests,
                {"operation": "ingest"},
                "started"
            )
            
            ingested_count = 0
            failed_count = 0
            embedding_job_id = generate_uuidv7()
            
            # Initialize storage for this user-week if not exists
            if user_week_key not in self.contributions_store:
                self.contributions_store[user_week_key] = {}
            
            # Process each contribution
            for contribution in request.contributions:
                try:
                    # Store contribution with user-week context
                    self.contributions_store[user_week_key][contribution.id] = contribution
                    
                    # Prepare for embedding (placeholder)
                    await self._prepare_for_embedding(contribution, request.user, request.week)
                    
                    ingested_count += 1
                    
                except Exception as e:
                    logger.error("Failed to ingest contribution",
                               contribution_id=contribution.id,
                               user=request.user,
                               week=request.week,
                               error=str(e))
                    failed_count += 1
            
            # Create embedding job
            self.embedding_jobs[embedding_job_id] = {
                "user": request.user,
                "week": request.week,
                "status": "processing",
                "total": len(request.contributions),
                "processed": ingested_count,
                "failed": failed_count,
                "created_at": datetime.now(timezone.utc)
            }
            
            # Start embedding process (placeholder)
            asyncio.create_task(self._process_embeddings(embedding_job_id, request.contributions, request.user, request.week))
            
            record_request_metrics(
                meilisearch_requests,
                {"operation": "ingest"},
                "success"
            )
            
            logger.info("Contributions ingestion completed",
                       user=request.user,
                       week=request.week,
                       ingested_count=ingested_count,
                       failed_count=failed_count,
                       embedding_job_id=embedding_job_id)
            
            return ContributionsIngestResponse(
                user=request.user,
                week=request.week,
                ingested_count=ingested_count,
                failed_count=failed_count,
                embedding_job_id=embedding_job_id,
                status="processing"
            )
            
        except Exception as e:
            record_request_metrics(
                meilisearch_requests,
                {"operation": "ingest"},
                "error"
            )
            record_error_metrics(
                meilisearch_requests,
                {"operation": "ingest"},
                type(e).__name__
            )
            logger.error("Contributions ingestion failed", 
                        user=request.user, 
                        week=request.week, 
                        error=str(e))
            raise
    
    async def _prepare_for_embedding(self, contribution: GitHubContribution, user: str, week: str) -> None:
        """Prepare contribution for embedding by extracting text content with user-week context"""
        # This is now handled by the Meilisearch service during indexing
        logger.debug("Prepared contribution for embedding",
                    contribution_id=contribution.id,
                    user=user,
                    week=week)
    
    def _extract_text_content(self, contribution: GitHubContribution) -> str:
        """Extract searchable text content from contribution"""
        content_parts = []
        
        # Common fields
        content_parts.append(f"Repository: {contribution.repository}")
        content_parts.append(f"Author: {contribution.author}")
        
        if contribution.type == ContributionType.COMMIT:
            content_parts.append(f"Commit: {contribution.message}")
            for file in contribution.files:
                content_parts.append(f"File: {file.filename}")
                if file.patch:
                    content_parts.append(f"Changes: {file.patch[:500]}")  # Truncate patch
                    
        elif contribution.type == ContributionType.PULL_REQUEST:
            content_parts.append(f"Pull Request: {contribution.title}")
            if contribution.body:
                content_parts.append(f"Description: {contribution.body}")
            
            # Include comments
            for comment in contribution.comments_data:
                content_parts.append(f"Comment by {comment.user.login}: {comment.body}")
            
            # Include review comments
            for review in contribution.reviews_data:
                if review.body:
                    content_parts.append(f"Review by {review.user.login}: {review.body}")
                for comment in review.comments:
                    content_parts.append(f"Review comment: {comment.body}")
                    
        elif contribution.type == ContributionType.ISSUE:
            content_parts.append(f"Issue: {contribution.title}")
            if contribution.body:
                content_parts.append(f"Description: {contribution.body}")
            
            # Include comments
            for comment in contribution.comments_data:
                content_parts.append(f"Comment by {comment.user.login}: {comment.body}")
                
        elif contribution.type == ContributionType.RELEASE:
            content_parts.append(f"Release: {contribution.name}")
            if contribution.body:
                content_parts.append(f"Release Notes: {contribution.body}")
        
        return "\n".join(content_parts)
    
    async def _process_embeddings(self, job_id: str, contributions: List[GitHubContribution], user: str, week: str) -> None:
        """Process embeddings for contributions using Meilisearch"""
        try:
            if self.meilisearch_service:
                # Index contributions in Meilisearch
                result = await self.meilisearch_service.index_contributions(user, week, contributions)
                
                # Update job status
                if job_id in self.embedding_jobs:
                    self.embedding_jobs[job_id]["status"] = "completed"
                    self.embedding_jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
                    self.embedding_jobs[job_id]["meilisearch_task_uid"] = result.get("task_uid")
                    self.embedding_jobs[job_id]["indexed_count"] = result.get("indexed", 0)
                    self.embedding_jobs[job_id]["failed_count"] = result.get("failed", 0)
                
                logger.info("Meilisearch indexing completed", 
                           job_id=job_id, 
                           user=user, 
                           week=week,
                           indexed_count=result.get("indexed", 0),
                           failed_count=result.get("failed", 0))
            else:
                # Fallback: simulate processing without Meilisearch
                await asyncio.sleep(1.0)
                
                if job_id in self.embedding_jobs:
                    self.embedding_jobs[job_id]["status"] = "completed"
                    self.embedding_jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
                
                logger.info("Embedding processing completed (no Meilisearch)", 
                           job_id=job_id, 
                           user=user, 
                           week=week)
            
        except Exception as e:
            if job_id in self.embedding_jobs:
                self.embedding_jobs[job_id]["status"] = "failed"
                self.embedding_jobs[job_id]["error"] = str(e)
            
            logger.error("Embedding processing failed", 
                        job_id=job_id, 
                        user=user, 
                        week=week, 
                        error=str(e))
    
    async def get_contributions_status(self, user: str, week: str) -> ContributionsStatusResponse:
        """Get status of contributions and embeddings for a specific user's week"""
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
                logger.error("Failed to get Meilisearch status", error=str(e))
                meilisearch_status = "unhealthy"
        else:
            # Fallback when no Meilisearch service
            embedded_contributions = total_contributions
            meilisearch_status = "not_configured"
        
        pending_embeddings = max(0, total_contributions - embedded_contributions)
        
        # Get last update time
        last_updated = datetime.now(timezone.utc)
        if user_week_key in self.contributions_store and self.contributions_store[user_week_key]:
            last_updated = max(contrib.created_at for contrib in self.contributions_store[user_week_key].values())
        
        return ContributionsStatusResponse(
            user=user,
            week=week,
            total_contributions=total_contributions,
            embedded_contributions=embedded_contributions,
            pending_embeddings=pending_embeddings,
            last_updated=last_updated,
            meilisearch_status=meilisearch_status
        )
    
    def get_user_week_contributions(self, user: str, week: str) -> List[GitHubContribution]:
        """Get all contributions for a specific user's week"""
        user_week_key = self._get_user_week_key(user, week)
        return list(self.contributions_store.get(user_week_key, {}).values())
    
    async def start_ingestion_task(self, request: ContributionsIngestRequest) -> IngestTaskResponse:
        """Start an asynchronous ingestion task for contributions"""
        try:
            task_id = generate_uuidv7()
            created_at = datetime.now(timezone.utc)
            
            # Create initial task status
            task_status = IngestTaskStatus(
                task_id=task_id,
                user=request.user,
                week=request.week,
                status="queued",
                total_contributions=len(request.contributions),
                ingested_count=0,
                failed_count=0,
                created_at=created_at
            )
            
            # Store the task
            self.ingest_tasks[task_id] = task_status
            
            # Start the actual ingestion process asynchronously
            asyncio.create_task(self._process_ingestion_task(task_id, request))
            
            logger.info("Ingestion task started",
                       task_id=task_id,
                       user=request.user,
                       week=request.week,
                       total_contributions=len(request.contributions))
            
            return IngestTaskResponse(
                task_id=task_id,
                user=request.user,
                week=request.week,
                status="queued",
                total_contributions=len(request.contributions),
                created_at=created_at
            )
            
        except Exception as e:
            logger.error("Failed to start ingestion task",
                        user=request.user,
                        week=request.week,
                        error=str(e))
            raise
    
    async def _process_ingestion_task(self, task_id: str, request: ContributionsIngestRequest) -> None:
        """Process the actual ingestion task"""
        try:
            # Update task status to processing
            if task_id in self.ingest_tasks:
                self.ingest_tasks[task_id].status = "processing"
                self.ingest_tasks[task_id].started_at = datetime.now(timezone.utc)
            
            # Perform the actual ingestion
            result = await self.ingest_contributions(request)
            
            # Update task status to completed
            if task_id in self.ingest_tasks:
                completed_at = datetime.now(timezone.utc)
                self.ingest_tasks[task_id].status = "completed"
                self.ingest_tasks[task_id].ingested_count = result.ingested_count
                self.ingest_tasks[task_id].failed_count = result.failed_count
                self.ingest_tasks[task_id].embedding_job_id = result.embedding_job_id
                self.ingest_tasks[task_id].completed_at = completed_at
                
                # Calculate processing time
                if self.ingest_tasks[task_id].started_at:
                    processing_time = (completed_at - self.ingest_tasks[task_id].started_at).total_seconds() * 1000
                    self.ingest_tasks[task_id].processing_time_ms = int(processing_time)
            
            logger.info("Ingestion task completed",
                       task_id=task_id,
                       user=request.user,
                       week=request.week,
                       ingested_count=result.ingested_count,
                       failed_count=result.failed_count)
            
        except Exception as e:
            # Update task status to failed
            if task_id in self.ingest_tasks:
                self.ingest_tasks[task_id].status = "failed"
                self.ingest_tasks[task_id].error_message = str(e)
                self.ingest_tasks[task_id].completed_at = datetime.now(timezone.utc)
            
            logger.error("Ingestion task failed",
                        task_id=task_id,
                        user=request.user,
                        week=request.week,
                        error=str(e))
    
    def get_ingestion_task_status(self, task_id: str) -> Optional[IngestTaskStatus]:
        """Get the status of an ingestion task"""
        return self.ingest_tasks.get(task_id) 