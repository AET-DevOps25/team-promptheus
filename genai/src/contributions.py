"""GitHub Content Service.

Service for fetching actual GitHub contribution content based on metadata.
This service handles authentication and fetching of commits, pull requests, issues, and releases.
"""

import base64
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import requests
import structlog
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    CommitAuthor,
    CommitContribution,
    CommitFile,
    CommitParent,
    CommitStats,
    CommitTree,
    ContributionMetadata,
    ContributionType,
    GitHubContribution,
    GitHubUser,
    IssueContribution,
    PullRequestContribution,
    PullRequestRef,
    ReleaseContribution,
)

logger = structlog.get_logger()

# Configuration constants
GITHUB_API_BASE_URL = "https://api.github.com"
DEFAULT_TIMEOUT = 60
REQUEST_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 1
ITEMS_PER_PAGE = 100
USER_AGENT = "Prompteus-GenAI/1.0"

# HTTP status codes that warrant retry
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]


class GitHubContentService:
    """Service for fetching GitHub contribution content from GitHub API."""

    def __init__(self, github_pat: str | None = None) -> None:
        """Initialize the GitHub content service.

        Args:
            github_pat: Personal Access Token for GitHub API authentication.
        """
        self.github_token = github_pat or os.getenv("GITHUB_TOKEN") or os.getenv("GH_PAT")

        if not self.github_token:
            logger.warning("No GitHub token provided - API requests will be rate limited")

        self.session = self._create_session()
        self._configure_authentication()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=REQUEST_RETRY_ATTEMPTS,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS_CODES,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _configure_authentication(self) -> None:
        """Configure GitHub API authentication headers."""
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": USER_AGENT}

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        self.session.headers.update(headers)

    async def fetch_contributions(
        self,
        repository: str,
        user: str,
        week: str,
        metadata_list: list[ContributionMetadata],
    ) -> list[GitHubContribution]:
        """Fetch actual contribution content based on metadata for selected contributions only."""
        # Only fetch contributions marked as selected
        selected_metadata = [m for m in metadata_list if self._get_selected(m)]

        if not selected_metadata:
            logger.info("No contributions selected for fetching", user=user, week=week)
            return []

        logger.info(
            "Fetching selected contributions",
            user=user,
            week=week,
            repository=repository,
            total_metadata=len(metadata_list),
            selected_count=len(selected_metadata),
        )

        contributions = []
        week_start, week_end = self._parse_iso_week(week)

        # Group metadata by type for efficient fetching
        metadata_by_type: dict[ContributionType, list[ContributionMetadata]] = {}
        for metadata in selected_metadata:
            contrib_type = self._get_type(metadata)
            if contrib_type not in metadata_by_type:
                metadata_by_type[contrib_type] = []
            metadata_by_type[contrib_type].append(metadata)

        # Fetch each type of contribution
        for contrib_type, type_metadata in metadata_by_type.items():
            try:
                if contrib_type == ContributionType.COMMIT:
                    contributions.extend(await self._fetch_commits_by_metadata(repository, type_metadata))
                elif contrib_type == ContributionType.PULL_REQUEST:
                    contributions.extend(await self._fetch_pull_requests_by_metadata(repository, type_metadata))
                elif contrib_type == ContributionType.ISSUE:
                    contributions.extend(await self._fetch_issues_by_metadata(repository, type_metadata))
                elif contrib_type == ContributionType.RELEASE:
                    contributions.extend(await self._fetch_releases_by_metadata(repository, type_metadata))
            except Exception as e:
                logger.exception(
                    "Error fetching contributions by type",
                    type=contrib_type,
                    error=str(e),
                    repository=repository,
                )

        logger.info(
            "Contributions fetched successfully",
            user=user,
            week=week,
            repository=repository,
            fetched_count=len(contributions),
        )

        return contributions

    def _get_id(self, metadata: ContributionMetadata | dict[str, Any]) -> str:
        """Safely get ID from metadata (supports both dict and ContributionMetadata objects)."""
        if hasattr(metadata, "id"):
            return metadata.id
        # isinstance check is exhaustive for the union type
        return metadata["id"]

    def _get_type(self, metadata: ContributionMetadata | dict[str, Any]) -> ContributionType:
        """Safely get type from metadata (supports both dict and ContributionMetadata objects)."""
        if hasattr(metadata, "type"):
            return metadata.type
        # isinstance check is exhaustive for the union type
        contrib_type = metadata["type"]
        # Handle string type conversion to enum
        if isinstance(contrib_type, str):
            return ContributionType(contrib_type.lower())
        return contrib_type

    def _get_selected(self, metadata: ContributionMetadata | dict[str, Any]) -> bool:
        """Safely get selected from metadata (supports both dict and ContributionMetadata objects)."""
        if hasattr(metadata, "selected"):
            return metadata.selected
        # isinstance check is exhaustive for the union type
        return metadata["selected"]

    def _parse_iso_week(self, week: str) -> tuple[datetime, datetime]:
        """Parse ISO week format (YYYY-WXX) and return start/end dates."""
        year_str, week_str = week.split("-W")
        year = int(year_str)
        week_num = int(week_str)

        # Calculate week start and end dates (timezone-aware)
        jan_1 = datetime(year, 1, 1, tzinfo=UTC)
        week_start = jan_1 + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=7)

        return week_start, week_end

    async def _fetch_commits_by_metadata(
        self, repository: str, metadata_list: list[ContributionMetadata]
    ) -> list[GitHubContribution]:
        """Fetch commits based on metadata list."""
        commits = []

        for metadata in metadata_list:
            try:
                # Extract SHA from ID (format: "commit-{sha}" or just "{sha}")
                sha = self._get_id(metadata).replace("commit-", "")
                commit_detail = await self.get_commit_details(repository, sha)
                if commit_detail:
                    commits.append(commit_detail)
            except Exception as e:
                logger.exception(
                    "Error fetching commit by metadata",
                    metadata_id=self._get_id(metadata),
                    error=str(e),
                    repository=repository,
                )

        return commits

    async def get_commit_details(self, repository: str, sha: str) -> GitHubContribution | None:
        """Get detailed information for a specific commit."""
        try:
            url = f"{GITHUB_API_BASE_URL}/repos/{repository}/commits/{sha}"
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                commit_data = response.json()

                # Transform to our format
                stats_data = commit_data.get("stats", {"total": 0, "additions": 0, "deletions": 0})
                created_at = self._parse_datetime(commit_data["commit"]["author"]["date"])
                if created_at is None:
                    logger.warning("Invalid created_at datetime for commit", sha=sha)
                    return None

                return CommitContribution(
                    id=f"commit-{sha}",
                    type=ContributionType.COMMIT,
                    repository=repository,
                    author=commit_data["author"]["login"] if commit_data.get("author") else "unknown",
                    created_at=created_at,
                    url=commit_data["url"],
                    sha=sha,
                    message=commit_data["commit"]["message"],
                    tree=CommitTree(
                        sha=commit_data["commit"]["tree"]["sha"],
                        url=commit_data["commit"]["tree"]["url"],
                    ),
                    parents=[
                        CommitParent(sha=parent["sha"], url=parent["url"]) for parent in commit_data.get("parents", [])
                    ],
                    author_info=CommitAuthor(
                        name=commit_data["commit"]["author"]["name"],
                        email=commit_data["commit"]["author"]["email"],
                        date=self._parse_datetime(commit_data["commit"]["author"]["date"]) or created_at,
                    ),
                    committer=CommitAuthor(
                        name=commit_data["commit"]["committer"]["name"],
                        email=commit_data["commit"]["committer"]["email"],
                        date=self._parse_datetime(commit_data["commit"]["committer"]["date"]) or created_at,
                    ),
                    stats=CommitStats(
                        total=stats_data["total"],
                        additions=stats_data["additions"],
                        deletions=stats_data["deletions"],
                    ),
                    files=[
                        CommitFile(
                            filename=file["filename"],
                            status=file["status"],
                            additions=file.get("additions", 0),
                            deletions=file.get("deletions", 0),
                            changes=file.get("changes", 0),
                            blob_url=file.get("blob_url", ""),
                            raw_url=file.get("raw_url", ""),
                            contents_url=file.get("contents_url", ""),
                            patch=file.get("patch", ""),
                        )
                        for file in commit_data.get("files", [])
                    ],
                )
            logger.warning(
                "Failed to fetch commit details",
                status_code=response.status_code,
                repository=repository,
                sha=sha,
            )
        except Exception as e:
            logger.exception(
                "Error fetching commit details",
                error=str(e),
                sha=sha,
                repository=repository,
            )

        return None

    async def _fetch_pull_requests_by_metadata(
        self, repository: str, metadata_list: list[ContributionMetadata]
    ) -> list[GitHubContribution]:
        """Fetch pull requests based on metadata list."""
        pull_requests = []

        for metadata in metadata_list:
            try:
                # Extract PR number from ID (format: "pr-{number}" or just "{number}")
                pr_number = self._get_id(metadata).replace("pr-", "")
                pr_detail = await self.get_pull_request_details(repository, pr_number)
                if pr_detail:
                    pull_requests.append(pr_detail)
            except Exception as e:
                logger.exception(
                    "Error fetching pull request by metadata",
                    metadata_id=self._get_id(metadata),
                    error=str(e),
                    repository=repository,
                )

        return pull_requests

    async def get_pull_request_details(self, repository: str, pr_number: str) -> GitHubContribution | None:
        """Get detailed information for a specific pull request."""
        try:
            url = f"{GITHUB_API_BASE_URL}/repos/{repository}/pulls/{pr_number}"
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                pr = response.json()

                # Transform to our format
                created_at = self._parse_datetime(pr["created_at"])
                if created_at is None:
                    logger.warning("Invalid created_at datetime for PR", pr_number=pr_number)
                    return None

                return PullRequestContribution(
                    id=f"pr-{pr['id']}",
                    type=ContributionType.PULL_REQUEST,
                    repository=repository,
                    author=pr["user"]["login"],
                    created_at=created_at,
                    url=pr["url"],
                    number=pr["number"],
                    title=pr["title"],
                    body=pr.get("body", ""),
                    state=pr["state"],
                    locked=pr.get("locked", False),
                    user=GitHubUser(
                        login=pr["user"]["login"],
                        id=pr["user"]["id"],
                        type=pr["user"]["type"],
                    ),
                    head=PullRequestRef(
                        label=pr["head"]["label"],
                        ref=pr["head"]["ref"],
                        sha=pr["head"]["sha"],
                        repo={
                            "name": pr["head"]["repo"]["name"] if pr["head"]["repo"] else "",
                            "full_name": pr["head"]["repo"]["full_name"] if pr["head"]["repo"] else "",
                        },
                    ),
                    base=PullRequestRef(
                        label=pr["base"]["label"],
                        ref=pr["base"]["ref"],
                        sha=pr["base"]["sha"],
                        repo={
                            "name": pr["base"]["repo"]["name"],
                            "full_name": pr["base"]["repo"]["full_name"],
                        },
                    ),
                    merged=pr.get("merged", False),
                    comments=pr.get("comments", 0),
                    review_comments=pr.get("review_comments", 0),
                    commits=pr.get("commits", 0),
                    additions=pr.get("additions", 0),
                    deletions=pr.get("deletions", 0),
                    changed_files=pr.get("changed_files", 0),
                    comments_data=[],
                    reviews_data=[],
                    commits_data=[],
                    files_data=[],
                )
            logger.warning(
                "Failed to fetch pull request details",
                status_code=response.status_code,
                repository=repository,
                pr_number=pr_number,
            )
        except Exception as e:
            logger.exception(
                "Error fetching pull request details",
                error=str(e),
                pr_number=pr_number,
                repository=repository,
            )

        return None

    async def _fetch_issues_by_metadata(
        self, repository: str, metadata_list: list[ContributionMetadata]
    ) -> list[GitHubContribution]:
        """Fetch issues based on metadata list."""
        issues = []

        for metadata in metadata_list:
            try:
                # Extract issue number from ID (format: "issue-{number}" or just "{number}")
                issue_number = self._get_id(metadata).replace("issue-", "")
                issue_detail = await self.get_issue_details(repository, issue_number)
                if issue_detail:
                    issues.append(issue_detail)
            except Exception as e:
                logger.exception(
                    "Error fetching issue by metadata",
                    metadata_id=self._get_id(metadata),
                    error=str(e),
                    repository=repository,
                )

        return issues

    async def get_issue_details(self, repository: str, issue_number: str) -> GitHubContribution | None:
        """Get detailed information for a specific issue."""
        try:
            url = f"{GITHUB_API_BASE_URL}/repos/{repository}/issues/{issue_number}"
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                issue = response.json()

                # Skip pull requests (they appear in issues API)
                if "pull_request" in issue:
                    return None

                created_at = self._parse_datetime(issue["created_at"])
                if created_at is None:
                    logger.warning("Invalid created_at datetime for issue", issue_id=issue["id"])
                    return None

                return IssueContribution(
                    id=f"issue-{issue['id']}",
                    type=ContributionType.ISSUE,
                    repository=repository,
                    author=issue["user"]["login"],
                    created_at=created_at,
                    url=issue["url"],
                    number=issue["number"],
                    title=issue["title"],
                    body=issue.get("body", ""),
                    state=issue["state"],
                    locked=issue.get("locked", False),
                    user=GitHubUser(
                        login=issue["user"]["login"],
                        id=issue["user"]["id"],
                        type=issue["user"]["type"],
                    ),
                    comments=issue.get("comments", 0),
                    comments_data=[],
                    events_data=[],
                )
            logger.warning(
                "Failed to fetch issue details",
                status_code=response.status_code,
                repository=repository,
                issue_number=issue_number,
            )
        except Exception as e:
            logger.exception(
                "Error fetching issue details",
                error=str(e),
                issue_number=issue_number,
                repository=repository,
            )

        return None

    async def _fetch_releases_by_metadata(
        self, repository: str, metadata_list: list[ContributionMetadata]
    ) -> list[GitHubContribution]:
        """Fetch releases based on metadata list."""
        releases = []

        for metadata in metadata_list:
            try:
                # Extract release ID from ID (format: "release-{id}" or just "{id}")
                release_id = self._get_id(metadata).replace("release-", "")
                release_detail = await self._get_release_details(repository, release_id)
                if release_detail:
                    releases.append(release_detail)
            except Exception as e:
                logger.exception(
                    "Error fetching release by metadata",
                    metadata_id=self._get_id(metadata),
                    error=str(e),
                    repository=repository,
                )

        return releases

    async def _get_release_details(self, repository: str, release_id: str) -> GitHubContribution | None:
        """Get detailed information for a specific release."""
        try:
            url = f"{GITHUB_API_BASE_URL}/repos/{repository}/releases/{release_id}"
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                release = response.json()

                created_at = self._parse_datetime(release.get("published_at", release.get("created_at")))
                if created_at is None:
                    logger.warning("Invalid created_at datetime for release", release_id=release["id"])
                    return None

                return ReleaseContribution(
                    id=f"release-{release['id']}",
                    type=ContributionType.RELEASE,
                    repository=repository,
                    author=release["author"]["login"],
                    created_at=created_at,
                    url=release["url"],
                    tag_name=release["tag_name"],
                    target_commitish=release["target_commitish"],
                    name=release["name"],
                    body=release.get("body", ""),
                    draft=release.get("draft", False),
                    prerelease=release.get("prerelease", False),
                    published_at=self._parse_datetime(release.get("published_at"))
                    if release.get("published_at")
                    else None,
                    author_info=GitHubUser(
                        login=release["author"]["login"],
                        id=release["author"]["id"],
                        type=release["author"]["type"],
                    ),
                    assets=[],  # Could be extended to include asset details
                )
            logger.warning(
                "Failed to fetch release details",
                status_code=response.status_code,
                repository=repository,
                release_id=release_id,
            )
        except Exception as e:
            logger.exception(
                "Error fetching release details",
                error=str(e),
                release_id=release_id,
                repository=repository,
            )

        return None

    async def get_file_content(self, repository: str, file_path: str) -> str | None:
        """Get content of a file in a repository."""
        try:
            url = f"{GITHUB_API_BASE_URL}/repos/{repository}/contents/{file_path}"
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                if data.get("type") == "file" and "content" in data:
                    content_b64 = data["content"]
                    return base64.b64decode(content_b64).decode("utf-8")
                logger.warning(
                    "Path is not a file or has no content",
                    repository=repository,
                    file_path=file_path,
                )
                return f"Path '{file_path}' is not a file or has no content."
            if response.status_code == 404:
                logger.warning(
                    "File not found",
                    status_code=response.status_code,
                    repository=repository,
                    file_path=file_path,
                )
                return f"File '{file_path}' not found in repository '{repository}'."
            logger.warning(
                "Failed to get file content",
                status_code=response.status_code,
                repository=repository,
                file_path=file_path,
            )
            return f"Failed to get file content for '{file_path}'. Status: {response.status_code}"
        except Exception as e:
            logger.exception(
                "Error getting file content",
                error=str(e),
                file_path=file_path,
                repository=repository,
            )

        return None

    async def search_code(self, repository: str, query: str) -> list[dict]:
        """Search for code in a repository."""
        try:
            url = f"{GITHUB_API_BASE_URL}/search/code"
            params = {"q": f"{query} repo:{repository}"}
            response = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                return response.json().get("items", [])
            logger.warning(
                "Failed to search code",
                status_code=response.status_code,
                repository=repository,
                query=query,
                response_text=response.text,
            )
            return []
        except Exception as e:
            logger.exception("Error searching code", error=str(e), query=query, repository=repository)
            return []

    async def search_issues_and_prs(
        self,
        repository: str,
        query: str,
        is_pr: bool = False,
        is_open: bool | None = None,
    ) -> list[dict]:
        """Search for issues and PRs in a repository."""
        try:
            url = f"{GITHUB_API_BASE_URL}/search/issues"

            pr_filter = "is:pr" if is_pr else "is:issue"
            state_filter = ""
            if is_open is True:
                state_filter = "is:open"
            elif is_open is False:
                state_filter = "is:closed"

            params = {"q": f"repo:{repository} {pr_filter} {state_filter} {query}".strip()}
            response = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                return response.json().get("items", [])
            logger.warning(
                "Failed to search issues/prs",
                status_code=response.status_code,
                repository=repository,
                query=query,
                response_text=response.text,
            )
            return []
        except Exception as e:
            logger.exception(
                "Error searching issues/prs",
                error=str(e),
                query=query,
                repository=repository,
            )
            return []

    async def search_commits(self, repository: str, query: str) -> list[dict]:
        """Search for commits in a repository."""
        try:
            url = f"{GITHUB_API_BASE_URL}/search/commits"
            params = {"q": f"repo:{repository} {query}"}
            # Special header for commit search API preview
            headers = dict(self.session.headers)
            headers["Accept"] = "application/vnd.github.cloak-preview+json"

            response = self.session.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                return response.json().get("items", [])
            logger.warning(
                "Failed to search commits",
                status_code=response.status_code,
                repository=repository,
                query=query,
                response_text=response.text,
            )
            return []
        except Exception as e:
            logger.exception(
                "Error searching commits",
                error=str(e),
                query=query,
                repository=repository,
            )
            return []

    def _parse_datetime(self, datetime_str: str | None) -> datetime | None:
        """Parse GitHub API datetime string to datetime object."""
        if not datetime_str:
            return None
        if datetime_str.endswith("Z"):
            datetime_str = datetime_str[:-1] + "+00:00"
        return datetime.fromisoformat(datetime_str)
