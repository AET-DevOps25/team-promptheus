"""Tests for Meilisearch service functionality."""

import asyncio
from datetime import UTC, datetime

import pytest

from src.meilisearch import MeilisearchService
from src.models import CommitAuthor, CommitContribution, CommitStats, CommitTree


@pytest.mark.asyncio
class TestMeilisearchService:
    """Test Meilisearch service functionality."""

    async def test_meilisearch_initialization(self) -> None:
        """Test Meilisearch service initialization."""
        service = MeilisearchService()

        # Test initialization
        result = await service.initialize()
        assert result is True
        assert service.contributions_index is not None

    async def test_meilisearch_configuration(self) -> None:
        """Test Meilisearch index configuration."""
        service = MeilisearchService()
        await service.initialize()

        # Check index settings
        settings = await asyncio.to_thread(service.contributions_index.get_settings)

        # Verify required attributes are configured
        assert "content" in settings.get("searchableAttributes", [])
        assert "title" in settings.get("searchableAttributes", [])
        assert "user" in settings.get("filterableAttributes", [])
        assert "week" in settings.get("filterableAttributes", [])
        assert "created_at_timestamp" in settings.get("sortableAttributes", [])

    async def test_search_contributions_empty_results(self) -> None:
        """Test searching for contributions with no results."""
        service = MeilisearchService()
        await service.initialize()

        # Test search with no results
        results = await service.search_contributions(
            user="nonexistent_user", week="2024-W99", query="test query", limit=5
        )

        assert isinstance(results, list)
        assert len(results) == 0

    async def test_search_with_sort_parameter(self) -> None:
        """Test that search with sort parameter works without errors."""
        service = MeilisearchService()
        await service.initialize()

        # Test search with sort - should not raise "Incorrect label names" error
        try:
            search_results = await asyncio.to_thread(
                service.contributions_index.search,
                "test",
                {
                    "filter": 'user = "test_user" AND week = "2024-W21"',
                    "limit": 1,
                    "sort": ["created_at_timestamp:desc"],
                },
            )
            assert "hits" in search_results
            assert isinstance(search_results["hits"], list)
        except Exception as e:
            pytest.fail(f"Search with sort failed: {e}")

    async def test_contributions_count(self) -> None:
        """Test getting contributions count."""
        service = MeilisearchService()
        await service.initialize()

        count = await service.get_contributions_count("test_user", "2024-W21")
        assert isinstance(count, int)
        assert count >= 0

    async def test_health_check(self) -> None:
        """Test Meilisearch health check."""
        service = MeilisearchService()
        await service.initialize()

        health = await service.health_check()
        assert isinstance(health, dict)
        assert "status" in health

    async def test_document_creation(self) -> None:
        """Test creating a document from a contribution."""
        service = MeilisearchService()

        # Create a test commit contribution
        commit = CommitContribution(
            id="test-commit-123",
            repository="test/repo",
            author="testuser",
            created_at=datetime.now(UTC),
            url="https://api.github.com/test",
            sha="abc123",
            message="Test commit message",
            tree=CommitTree(sha="tree123", url="https://api.github.com/test"),
            parents=[],
            author_info=CommitAuthor(
                name="Test User",
                email="test@example.com",
                date=datetime.now(UTC),
            ),
            committer=CommitAuthor(
                name="Test User",
                email="test@example.com",
                date=datetime.now(UTC),
            ),
            stats=CommitStats(total=10, additions=5, deletions=5),
            files=[],
        )

        # Test document creation
        document = service._create_document("testuser", "2024-W21", commit)

        assert document["id"] == "testuser-2024-W21-test-commit-123"
        assert document["user"] == "testuser"
        assert document["week"] == "2024-W21"
        assert document["contribution_id"] == "test-commit-123"
        assert document["contribution_type"] == "commit"
        assert document["repository"] == "test/repo"
        assert document["author"] == "testuser"
        assert "content" in document
        assert "Test commit message" in document["content"]
