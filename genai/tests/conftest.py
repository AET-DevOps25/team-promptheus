"""Pytest configuration and fixtures for GenAI service tests."""

import asyncio
from datetime import UTC, datetime
from typing import Never
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from src.meilisearch import MeilisearchService
from src.models import (
    CommitAuthor,
    CommitContribution,
    CommitStats,
    CommitTree,
    GitHubUser,
    IssueContribution,
    PullRequestContribution,
    PullRequestRef,
    SummaryMetadata,
    SummaryResponse,
    generate_uuidv7,
)

# Import our application and services
from src.services import (
    ContributionsIngestionService,
    GitHubContentService,
    QuestionAnsweringService,
    SummaryService,
)

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def meilisearch_service():
    """Create and initialize a real Meilisearch service for testing."""
    service = MeilisearchService()

    try:
        initialized = await service.initialize()
        if not initialized:
            pytest.skip("Meilisearch not available for testing")
    except Exception as e:
        pytest.skip(f"Meilisearch initialization failed: {e}")

    yield service

    # Cleanup: delete test data
    try:
        # Delete all test documents
        await service.contributions_index.delete_all_documents()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="session")
def test_services(meilisearch_service):
    """Initialize test services with real Meilisearch."""
    ingestion_service = ContributionsIngestionService(meilisearch_service)
    github_content_service = GitHubContentService()  # Use test PAT if needed
    qa_service = QuestionAnsweringService(github_content_service, meilisearch_service)
    summary_service = SummaryService(ingestion_service)

    return {
        "meilisearch": meilisearch_service,
        "ingestion": ingestion_service,
        "github_content": github_content_service,
        "qa": qa_service,
        "summary": summary_service,
    }


@pytest.fixture(scope="session")
def test_client(test_services):
    """Create a test client with properly initialized services."""
    # Import app inside the fixture to avoid circular imports
    import app as app_module

    # Monkey patch the app's global service instances
    app_module.meilisearch_service = test_services["meilisearch"]
    app_module.ingestion_service = test_services["ingestion"]
    app_module.qa_service = test_services["qa"]
    app_module.summary_service = test_services["summary"]

    # Create the test client with the FastAPI app instance
    test_client_instance = TestClient(app_module.app)

    yield test_client_instance

    # Cleanup
    app_module.meilisearch_service = None
    app_module.ingestion_service = None
    app_module.qa_service = None
    app_module.summary_service = None


@pytest.fixture(autouse=True)
def ensure_services(test_services) -> None:
    """Ensure services are available for each test."""
    import app as app_module

    # Always set the services for tests
    app_module.meilisearch_service = test_services["meilisearch"]
    app_module.ingestion_service = test_services["ingestion"]
    app_module.qa_service = test_services["qa"]
    app_module.summary_service = test_services["summary"]


@pytest_asyncio.fixture(loop_scope="function")
async def clean_services(test_services):
    """Clean service state between tests."""
    # Clear any stored data
    test_services["ingestion"].contributions_store.clear()
    test_services["ingestion"].embedding_jobs.clear()

    # Clear Meilisearch test data
    try:
        await test_services["meilisearch"].contributions_index.delete_all_documents()
        # Wait a bit for deletion to complete
        await asyncio.sleep(0.1)
    except Exception:
        pass  # Ignore cleanup errors

    yield test_services


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_github_service():
    """Mock GitHubContentService to return test data instead of hitting real GitHub API."""

    def create_mock_commit(sha="abc123def456", repository="test/repo"):
        return CommitContribution(
            id=f"commit-{sha}",
            type="commit",
            repository=repository,
            author="testuser",
            created_at=datetime.now(UTC),
            url=f"https://api.github.com/repos/{repository}/commits/{sha}",
            sha=sha,
            message="Fix authentication bug",
            tree=CommitTree(
                sha="tree123",
                url=f"https://api.github.com/repos/{repository}/git/trees/tree123",
            ),
            parents=[],
            author_info=CommitAuthor(
                name="Test User",
                email="testuser@example.com",
                date=datetime.now(UTC),
            ),
            committer=CommitAuthor(
                name="Test User",
                email="testuser@example.com",
                date=datetime.now(UTC),
            ),
            stats=CommitStats(total=15, additions=10, deletions=5),
            files=[],
        )

    def create_mock_pr(pr_id="42", repository="test/repo"):
        return PullRequestContribution(
            id=f"pr-{pr_id}",
            type="pull_request",
            repository=repository,
            author="testuser",
            created_at=datetime.now(UTC),
            url=f"https://api.github.com/repos/{repository}/pulls/{pr_id}",
            number=int(pr_id),
            title="Add user management feature",
            body="This PR adds comprehensive user management functionality",
            state="open",
            locked=False,
            user=GitHubUser(login="testuser", id=12345, type="User"),
            head=PullRequestRef(
                label="testuser:feature-branch",
                ref="feature-branch",
                sha="def456ghi789",
                repo={"name": "repo", "full_name": repository},
            ),
            base=PullRequestRef(
                label="test:main",
                ref="main",
                sha="ghi789jkl012",
                repo={"name": "repo", "full_name": repository},
            ),
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=50,
            deletions=10,
            changed_files=3,
            comments_data=[],
            reviews_data=[],
            commits_data=[],
            files_data=[],
        )

    def create_mock_issue(issue_id="15", repository="test/repo"):
        return IssueContribution(
            id=f"issue-{issue_id}",
            type="issue",
            repository=repository,
            author="testuser",
            created_at=datetime.now(UTC),
            url=f"https://api.github.com/repos/{repository}/issues/{issue_id}",
            number=int(issue_id),
            title="Performance optimization needed",
            body="The application is running slowly with large datasets",
            state="open",
            locked=False,
            user=GitHubUser(login="testuser", id=12345, type="User"),
            comments=0,
            comments_data=[],
            events_data=[],
        )

    async def mock_fetch_contributions(self, repository, user, week, metadata_list):
        """Mock fetch_contributions to return test data or simulate failures."""
        # Check if we should simulate a failure
        if hasattr(self, "_should_fail") and self._should_fail:
            msg = "Simulated GitHub API failure"
            raise Exception(msg)

        # Check for invalid repository to simulate 404
        if repository == "invalid/repo":
            msg = "Repository not found (404)"
            raise Exception(msg)

        results = []
        for metadata in metadata_list:
            # Handle both dict and object metadata
            if hasattr(metadata, "selected"):
                selected = metadata.selected
                contribution_type = metadata.type
                contribution_id = metadata.id
            else:
                selected = metadata.get("selected", True)
                contribution_type = metadata.get("type")
                contribution_id = metadata.get("id")

            if not selected:
                continue

            # Simulate individual contribution fetch failures
            if contribution_id == "fail123":
                continue  # Skip this one to simulate partial failure

            if contribution_type == "commit":
                results.append(create_mock_commit(contribution_id, repository))
            elif contribution_type == "pull_request":
                results.append(create_mock_pr(contribution_id, repository))
            elif contribution_type == "issue":
                results.append(create_mock_issue(contribution_id, repository))

        return results

    # Patch the GitHubContentService.fetch_contributions method
    with patch(
        "src.contributions.GitHubContentService.fetch_contributions",
        mock_fetch_contributions,
    ):
        # Patch new async methods for agent_tools
        async def mock_get_file_content(self, repository, file_path) -> str | None:
            if file_path == "notfound.py":
                return None
            return f"# Mock content of {file_path} in {repository}"

        async def mock_search_code(self, repository, query):
            return [
                {
                    "path": "src/example.py",
                    "html_url": f"https://github.com/{repository}/blob/main/src/example.py",
                }
            ]

        async def mock_search_issues_and_prs(self, repository, query, is_pr=False, is_open=None):
            if is_pr:
                return [
                    {
                        "number": 1,
                        "title": "Mock PR",
                        "state": "open",
                        "html_url": f"https://github.com/{repository}/pull/1",
                    }
                ]
            return [
                {
                    "number": 2,
                    "title": "Mock Issue",
                    "state": "open",
                    "html_url": f"https://github.com/{repository}/issues/2",
                }
            ]

        async def mock_search_commits(self, repository, query):
            return [
                {
                    "sha": "abc123",
                    "commit": {"message": "Mock commit"},
                    "html_url": f"https://github.com/{repository}/commit/abc123",
                }
            ]

        async def mock_get_commit_details(self, repository, sha) -> None:
            return None

        async def mock_get_issue_details(self, repository, issue_number) -> None:
            return None

        async def mock_get_pull_request_details(self, repository, pr_number) -> None:
            return None

        patchers = [
            patch(
                "src.contributions.GitHubContentService.get_file_content",
                mock_get_file_content,
            ),
            patch("src.contributions.GitHubContentService.search_code", mock_search_code),
            patch(
                "src.contributions.GitHubContentService.search_issues_and_prs",
                mock_search_issues_and_prs,
            ),
            patch(
                "src.contributions.GitHubContentService.search_commits",
                mock_search_commits,
            ),
            patch(
                "src.contributions.GitHubContentService.get_commit_details",
                mock_get_commit_details,
            ),
            patch(
                "src.contributions.GitHubContentService.get_issue_details",
                mock_get_issue_details,
            ),
            patch(
                "src.contributions.GitHubContentService.get_pull_request_details",
                mock_get_pull_request_details,
            ),
        ]
        for p in patchers:
            p.start()
        yield
        for p in patchers:
            p.stop()


@pytest.fixture
def failing_github_service():
    """Mock GitHubContentService to simulate failures for error handling tests."""

    async def mock_fetch_contributions_fail(self, repository, user, week, metadata_list) -> Never:
        """Mock that always fails."""
        msg = "GitHub API connection failed"
        raise Exception(msg)

    with patch(
        "src.contributions.GitHubContentService.fetch_contributions",
        mock_fetch_contributions_fail,
    ):
        yield


@pytest.fixture(autouse=True)
def auto_mock_github():
    """Automatically apply GitHub mocking to all tests."""

    def create_mock_commit(sha="abc123def456", repository="test/repo"):
        return CommitContribution(
            id=f"commit-{sha}",
            type="commit",
            repository=repository,
            author="testuser",
            created_at=datetime.now(UTC),
            url=f"https://api.github.com/repos/{repository}/commits/{sha}",
            sha=sha,
            message="Fix authentication bug",
            tree=CommitTree(
                sha="tree123",
                url=f"https://api.github.com/repos/{repository}/git/trees/tree123",
            ),
            parents=[],
            author_info=CommitAuthor(
                name="Test User",
                email="testuser@example.com",
                date=datetime.now(UTC),
            ),
            committer=CommitAuthor(
                name="Test User",
                email="testuser@example.com",
                date=datetime.now(UTC),
            ),
            stats=CommitStats(total=15, additions=10, deletions=5),
            files=[],
        )

    def create_mock_pr(pr_id="42", repository="test/repo"):
        return PullRequestContribution(
            id=f"pr-{pr_id}",
            type="pull_request",
            repository=repository,
            author="testuser",
            created_at=datetime.now(UTC),
            url=f"https://api.github.com/repos/{repository}/pulls/{pr_id}",
            number=int(pr_id),
            title="Add user management feature",
            body="This PR adds comprehensive user management functionality",
            state="open",
            locked=False,
            user=GitHubUser(login="testuser", id=12345, type="User"),
            head=PullRequestRef(
                label="testuser:feature-branch",
                ref="feature-branch",
                sha="def456ghi789",
                repo={"name": "repo", "full_name": repository},
            ),
            base=PullRequestRef(
                label="test:main",
                ref="main",
                sha="ghi789jkl012",
                repo={"name": "repo", "full_name": repository},
            ),
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=50,
            deletions=10,
            changed_files=3,
            comments_data=[],
            reviews_data=[],
            commits_data=[],
            files_data=[],
        )

    def create_mock_issue(issue_id="15", repository="test/repo"):
        return IssueContribution(
            id=f"issue-{issue_id}",
            type="issue",
            repository=repository,
            author="testuser",
            created_at=datetime.now(UTC),
            url=f"https://api.github.com/repos/{repository}/issues/{issue_id}",
            number=int(issue_id),
            title="Performance optimization needed",
            body="The application is running slowly with large datasets",
            state="open",
            locked=False,
            user=GitHubUser(login="testuser", id=12345, type="User"),
            comments=0,
            comments_data=[],
            events_data=[],
        )

    async def mock_fetch_contributions(self, repository, user, week, metadata_list):
        """Mock fetch_contributions to return test data or simulate failures."""
        # Check if we should simulate a failure
        if hasattr(self, "_should_fail") and self._should_fail:
            msg = "Simulated GitHub API failure"
            raise Exception(msg)

        # Check for invalid repository to simulate 404
        if repository == "invalid/repo":
            msg = "Repository not found (404)"
            raise Exception(msg)

        results = []
        for metadata in metadata_list:
            # Handle both dict and object metadata
            if hasattr(metadata, "selected"):
                selected = metadata.selected
                contribution_type = metadata.type
                contribution_id = metadata.id
            else:
                selected = metadata.get("selected", True)
                contribution_type = metadata.get("type")
                contribution_id = metadata.get("id")

            if not selected:
                continue

            # Simulate individual contribution fetch failures
            if contribution_id == "fail123":
                continue  # Skip this one to simulate partial failure

            if contribution_type == "commit":
                results.append(create_mock_commit(contribution_id, repository))
            elif contribution_type == "pull_request":
                results.append(create_mock_pr(contribution_id, repository))
            elif contribution_type == "issue":
                results.append(create_mock_issue(contribution_id, repository))

        return results

    # Patch the GitHubContentService.fetch_contributions method
    with patch(
        "src.contributions.GitHubContentService.fetch_contributions",
        mock_fetch_contributions,
    ):
        yield


@pytest.fixture
def mock_summary_for_api():
    """Automatically mock summary service to prevent OpenAI API calls during tests."""

    async def mock_generate_summary(self, user, week, summary_id=None):
        """Mock summary generation to return test data quickly."""
        if summary_id is None:
            summary_id = generate_uuidv7()

        # Get actual contributions count from the ingestion service
        contributions = self.ingestion_service.get_user_week_contributions(user, week)
        total_contributions = len(contributions)

        # Count by type
        commits_count = sum(1 for c in contributions if getattr(c, "type", None) == "commit")
        prs_count = sum(1 for c in contributions if getattr(c, "type", None) == "pull_request")
        issues_count = sum(1 for c in contributions if getattr(c, "type", None) == "issue")
        releases_count = sum(1 for c in contributions if getattr(c, "type", None) == "release")

        # Extract repositories
        repositories = list({getattr(c, "repository", "test/repo") for c in contributions})
        if not repositories:
            repositories = ["test/repo"]

        # Create mock metadata with actual data
        metadata = SummaryMetadata(
            total_contributions=total_contributions,
            commits_count=commits_count,
            pull_requests_count=prs_count,
            issues_count=issues_count,
            releases_count=releases_count,
            repositories=repositories,
            time_period=week,
            generated_at=datetime.now(UTC),
            processing_time_ms=100,
        )

        # Create mock summary response
        return SummaryResponse(
            summary_id=summary_id,
            user=user,
            week=week,
            overview=f"Test summary for {user} in week {week}",
            commits_summary="Made 1 commit this week",
            pull_requests_summary="No pull requests created this week",
            issues_summary="No issues created this week",
            releases_summary="No releases published this week",
            analysis="Test analysis of contributions",
            key_achievements=["Completed development tasks"],
            areas_for_improvement=["Continue consistent contribution patterns"],
            metadata=metadata,
            generated_at=datetime.now(UTC),
        )

    # Patch the SummaryService.generate_summary method
    with patch("src.summary.SummaryService.generate_summary", mock_generate_summary):
        yield
