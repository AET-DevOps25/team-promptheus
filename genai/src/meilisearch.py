import asyncio
import os
from typing import List, Dict, Any
from datetime import datetime  # noqa: F401
import structlog
import meilisearch
from meilisearch.errors import MeilisearchApiError

from .models import GitHubContribution, ContributionType

logger = structlog.get_logger()


class MeilisearchService:
    """Service for managing Meilisearch operations for GitHub contributions"""

    def __init__(self):
        self.host = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        self.master_key = os.getenv("MEILI_MASTER_KEY", "CHANGE_ME_CHANGE_ME")
        self.client = meilisearch.Client(self.host, self.master_key)

        # Index names
        self.contributions_index_name = "contributions"
        self.contributions_index = None

    async def initialize(self) -> bool:
        """Initialize Meilisearch indices and settings"""
        try:
            # Create or get the contributions index
            try:
                self.contributions_index = self.client.index(
                    self.contributions_index_name
                )
                # Test if index exists by getting stats
                await asyncio.to_thread(self.contributions_index.get_stats)
                logger.info("Meilisearch contributions index already exists")
            except MeilisearchApiError as e:
                if e.code == "index_not_found":
                    # Create the index
                    task = await asyncio.to_thread(
                        self.client.create_index,
                        self.contributions_index_name,
                        {"primaryKey": "id"},
                    )
                    # Wait for index creation
                    await asyncio.to_thread(self.client.wait_for_task, task.task_uid)
                    self.contributions_index = self.client.index(
                        self.contributions_index_name
                    )
                    logger.info("Created Meilisearch contributions index")
                else:
                    raise

            logger.info("Meilisearch service initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize Meilisearch service", error=str(e))
            return False

    async def index_contributions(
        self, user: str, week: str, contributions: List[GitHubContribution]
    ) -> Dict[str, Any]:
        """Index contributions for a specific user's week"""
        try:
            documents = []

            for contribution in contributions:
                # Create document for Meilisearch
                document = self._create_document(user, week, contribution)
                documents.append(document)

            if not documents:
                return {"indexed": 0, "failed": 0, "task_uid": None}

            # Index documents
            task = await asyncio.to_thread(
                self.contributions_index.add_documents, documents
            )

            # Wait for indexing to complete
            await asyncio.to_thread(self.client.wait_for_task, task.task_uid)

            # Get task details
            task_info = await asyncio.to_thread(self.client.get_task, task.task_uid)

            indexed_count = len(documents)
            failed_count = 0

            if task_info.status == "failed":
                failed_count = len(documents)
                indexed_count = 0
                logger.error(
                    "Meilisearch indexing failed",
                    task_uid=task.task_uid,
                    error=task_info.error,
                )

            logger.info(
                "Contributions indexed in Meilisearch",
                user=user,
                week=week,
                indexed_count=indexed_count,
                failed_count=failed_count,
                task_uid=task.task_uid,
            )

            return {
                "indexed": indexed_count,
                "failed": failed_count,
                "task_uid": task.task_uid,
            }

        except Exception as e:
            logger.error(
                "Failed to index contributions in Meilisearch",
                user=user,
                week=week,
                error=str(e),
            )
            raise

    def _create_document(
        self, user: str, week: str, contribution: GitHubContribution
    ) -> Dict[str, Any]:
        """Create a Meilisearch document from a contribution"""
        # Extract text content for search
        content_parts = []

        # Common fields
        content_parts.append(f"Repository: {contribution.repository}")
        content_parts.append(f"Author: {contribution.author}")

        # Type-specific content
        title = ""
        body = ""
        filename = ""
        patch = ""

        if contribution.type == ContributionType.COMMIT:
            title = contribution.message
            content_parts.append(f"Commit: {contribution.message}")

            # Include file information
            for file in contribution.files:
                content_parts.append(f"File: {file.filename}")
                filename += f"{file.filename} "
                if file.patch:
                    content_parts.append(f"Changes: {file.patch[:500]}")
                    patch += f"{file.patch[:500]} "

        elif contribution.type == ContributionType.PULL_REQUEST:
            title = contribution.title
            body = contribution.body or ""
            content_parts.append(f"Pull Request: {contribution.title}")
            if contribution.body:
                content_parts.append(f"Description: {contribution.body}")

            # Include comments
            for comment in contribution.comments_data:
                content_parts.append(f"Comment by {comment.user.login}: {comment.body}")

            # Include review comments
            for review in contribution.reviews_data:
                if review.body:
                    content_parts.append(
                        f"Review by {review.user.login}: {review.body}"
                    )
                for comment in review.comments:
                    content_parts.append(f"Review comment: {comment.body}")

        elif contribution.type == ContributionType.ISSUE:
            title = contribution.title
            body = contribution.body or ""
            content_parts.append(f"Issue: {contribution.title}")
            if contribution.body:
                content_parts.append(f"Description: {contribution.body}")

            # Include comments
            for comment in contribution.comments_data:
                content_parts.append(f"Comment by {comment.user.login}: {comment.body}")

        elif contribution.type == ContributionType.RELEASE:
            title = contribution.name
            body = contribution.body or ""
            content_parts.append(f"Release: {contribution.name}")
            if contribution.body:
                content_parts.append(f"Release Notes: {contribution.body}")

        # Create the document
        document = {
            "id": f"{user}-{week}-{contribution.id}",
            "user": user,
            "week": week,
            "contribution_id": contribution.id,
            "contribution_type": contribution.type.value,
            "repository": contribution.repository,
            "author": contribution.author,
            "created_at": contribution.created_at.isoformat(),
            "created_at_timestamp": int(contribution.created_at.timestamp()),
            "title": title,
            "message": getattr(contribution, "message", ""),
            "body": body,
            "filename": filename.strip(),
            "patch": patch.strip(),
            "content": "\n".join(content_parts),
            "relevance_score": 1.0,  # Default relevance score
            "is_selected": getattr(contribution, "is_selected", True),  # Default to True if not present
        }

        return document

    async def search_contributions(
        self, user: str, week: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search contributions for a specific user's week"""
        try:
            # Build search filters
            filters = f'user = "{user}" AND week = "{week}"'

            # Check if embedders are configured by checking for Ollama key
            ollama_api_key = os.getenv("OLLAMA_API_KEY")
            search_params = {
                "filter": filters,
                "limit": limit,
                "attributesToHighlight": ["content", "title", "message", "body"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "sort": ["created_at_timestamp:desc"],
            }

            # Use hybrid search if Ollama embedder is available
            if ollama_api_key:
                search_params["hybrid"] = {
                    "embedder": "default",
                    "semanticRatio": 0.5,  # 50% semantic, 50% full-text
                }
                logger.debug("Using hybrid search with TinyLlama embeddings")
            else:
                logger.debug("Using full-text search only (no Ollama embedder)")

            # Perform search
            search_results = await asyncio.to_thread(
                self.contributions_index.search, query, search_params
            )

            logger.info(
                "Meilisearch search completed",
                user=user,
                week=week,
                query=query,
                results_count=len(search_results["hits"]),
                search_type="hybrid" if ollama_api_key else "full-text",
            )

            return search_results["hits"]

        except Exception as e:
            logger.error(
                "Failed to search contributions in Meilisearch",
                user=user,
                week=week,
                query=query,
                error=str(e),
            )
            raise

    async def get_contributions_count(self, user: str, week: str) -> int:
        """Get the count of contributions for a specific user's week"""
        try:
            filters = f'user = "{user}" AND week = "{week}"'

            search_results = await asyncio.to_thread(
                self.contributions_index.search,
                "",
                {
                    "filter": filters,
                    "limit": 0,  # We only want the count
                },
            )

            return search_results["estimatedTotalHits"]

        except Exception as e:
            logger.error(
                "Failed to get contributions count from Meilisearch",
                user=user,
                week=week,
                error=str(e),
            )
            return 0

    async def delete_user_week_contributions(self, user: str, week: str) -> bool:
        """Delete all contributions for a specific user's week"""
        try:
            # First, search for documents to get their IDs
            filters = f'user = "{user}" AND week = "{week}"'

            search_results = await asyncio.to_thread(
                self.contributions_index.search,
                "",
                {
                    "filter": filters,
                    "limit": 1000,  # Get all matching documents
                    "attributesToRetrieve": ["id"],
                },
            )

            if not search_results["hits"]:
                logger.info("No contributions found to delete", user=user, week=week)
                return True

            # Extract document IDs
            document_ids = [hit["id"] for hit in search_results["hits"]]

            # Delete documents by IDs
            task = await asyncio.to_thread(
                self.contributions_index.delete_documents, document_ids
            )

            # Wait for deletion to complete
            await asyncio.to_thread(self.client.wait_for_task, task.task_uid)

            logger.info(
                "Deleted contributions from Meilisearch",
                user=user,
                week=week,
                count=len(document_ids),
                task_uid=task.task_uid,
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to delete contributions from Meilisearch",
                user=user,
                week=week,
                error=str(e),
            )
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check Meilisearch health and return status"""
        try:
            # Check if we can connect and get health
            health = await asyncio.to_thread(self.client.health)

            # Get index stats
            stats = (
                await asyncio.to_thread(self.contributions_index.get_stats)
                if self.contributions_index
                else {}
            )

            return {
                "status": "healthy",
                "health": health,
                "contributions_index_stats": stats,
            }

        except Exception as e:
            logger.error("Meilisearch health check failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}
