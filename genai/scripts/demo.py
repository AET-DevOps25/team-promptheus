#!/usr/bin/env python3
"""Prompteus Demo Script.

This script demonstrates the new metadata-only Prompteus workflow:
1. Prompts for GitHub Personal Access Token (PAT) or uses provided token
2. Fetches GitHub contribution metadata for a specified user/repository
3. Interactive selection of contributions to process
4. Calls the new GenAI service ingest endpoint with metadata only
5. Generates AI-powered summaries using the GenAI service
6. Provides an interactive Q&A session about the contributions

Features:
- Interactive contribution selection with check/uncheck functionality
- Metadata-only approach for efficiency (only fetches data for selected contributions)
- Live streaming summary generation with real-time updates
- Evidence-based Q&A with confidence scoring
- Flexible GitHub token authentication (CLI, env var, or prompt)
- Task-based ingestion with progress tracking

GitHub Token Options:
    --github-token TOKEN    Provide GitHub PAT via command line
    GH_PAT environment var  Set GitHub PAT via environment variable
    Interactive prompt      Enter token when prompted (fallback)

Usage:
    python demo.py [--user USERNAME] [--repo REPOSITORY] [--week WEEK] [--github-token TOKEN]

Examples:
    python demo.py --user octocat --repo octocat/Hello-World --week 2024-W01 --github-token ghp_xxxxx
    GH_PAT=ghp_xxxxx python demo.py --user octocat --repo octocat/Hello-World --week 2024-W01
    python demo.py --user octocat --repo octocat/Hello-World --week 2024-W01  # will prompt for token
"""

import argparse
import asyncio
import getpass
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import questionary
import requests
import structlog
from requests.adapters import HTTPAdapter
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from urllib3.util.retry import Retry

# Configuration constants
GITHUB_API_BASE_URL = "https://api.github.com"
DEFAULT_GENAI_URL = "http://0.0.0.0:3003"
GITHUB_TOKEN_ENV_VAR = "GH_PAT"
DEFAULT_TIMEOUT = 60
REQUEST_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 1
ITEMS_PER_PAGE = 100

# HTTP status codes that warrant retry
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# User agent for GitHub API requests
USER_AGENT = "Prompteus-Demo/1.0"

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize rich console for beautiful output
console = Console()


class GitHubTokenManager:
    """Manages GitHub Personal Access Token retrieval from various sources."""

    @staticmethod
    def get_token(args: argparse.Namespace) -> str:
        """Get GitHub Personal Access Token from args, environment, or prompt user."""
        # Priority 1: Command line argument
        if args.github_token:
            logger.info("Using GitHub token from command line argument")
            return args.github_token

        # Priority 2: Environment variable
        env_token = os.getenv(GITHUB_TOKEN_ENV_VAR)
        if env_token:
            logger.info(
                "Using GitHub token from environment variable",
                env_var=GITHUB_TOKEN_ENV_VAR,
            )
            return env_token

        # Priority 3: Interactive prompt (fallback)
        return GitHubTokenManager._prompt_for_token()

    @staticmethod
    def _prompt_for_token() -> str:
        """Prompt user for GitHub token with helpful instructions."""
        token = getpass.getpass("Enter your GitHub PAT: ").strip()

        if not token:
            sys.exit(1)

        return token


class DateTimeHelper:
    """Helper class for date and time operations."""

    @staticmethod
    def parse_iso_week(week: str) -> tuple[datetime, datetime]:
        """Parse ISO week format (YYYY-WXX) and return start/end dates."""
        year_str, week_str = week.split("-W")
        year = int(year_str)
        week_num = int(week_str)

        # Calculate week start and end dates (timezone-aware)
        jan_1 = datetime(year, 1, 1, tzinfo=UTC)
        week_start = jan_1 + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=7)

        return week_start, week_end

    @staticmethod
    def get_current_iso_week() -> str:
        """Get the current ISO week in YYYY-WXX format."""
        current_date = datetime.now()
        year = current_date.year
        week_num = current_date.isocalendar()[1]
        return f"{year}-W{week_num:02d}"


class HTTPClientMixin:
    """Mixin providing configured HTTP session with retry logic."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.session = self._create_session()

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


class GitHubAPIClient(HTTPClientMixin):
    """GitHub API client for fetching contribution metadata."""

    def __init__(self, token: str) -> None:
        super().__init__(GITHUB_API_BASE_URL)
        self.token = token
        self._configure_authentication()

    def _configure_authentication(self) -> None:
        """Configure GitHub API authentication headers."""
        self.session.headers.update(
            {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": USER_AGENT,
            }
        )

    def test_authentication(self) -> bool:
        """Test if the GitHub token is valid."""
        try:
            response = self.session.get(f"{self.base_url}/user")
            if response.status_code == 200:
                user_data = response.json()
                logger.info("GitHub authentication successful", user=user_data.get("login"))
                return True
            logger.error("GitHub authentication failed", status_code=response.status_code)
            return False
        except Exception as e:
            logger.exception("GitHub authentication error", error=str(e))
            return False

    def get_contribution_metadata(self, username: str, repo: str, week: str) -> list[dict[str, Any]]:
        """Fetch metadata for all contributions in the specified week."""
        week_start, week_end = DateTimeHelper.parse_iso_week(week)

        logger.info(
            "Fetching contribution metadata",
            username=username,
            repo=repo,
            week=week,
            start_date=week_start.isoformat(),
            end_date=week_end.isoformat(),
        )

        metadata = []

        # Fetch all contribution types metadata
        metadata.extend(self._fetch_commits_metadata(username, repo, week_start, week_end))
        metadata.extend(self._fetch_pull_requests_metadata(username, repo, week_start, week_end))
        metadata.extend(self._fetch_issues_metadata(username, repo, week_start, week_end))
        metadata.extend(self._fetch_releases_metadata(username, repo, week_start, week_end))

        logger.info(
            "Contribution metadata fetched successfully",
            username=username,
            repo=repo,
            total_contributions=len(metadata),
        )

        return metadata

    def _fetch_commits_metadata(
        self, username: str, repo: str, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Fetch commit metadata."""
        metadata = []
        try:
            url = f"{self.base_url}/repos/{repo}/commits"
            params: dict[str, str] = {
                "author": username,
                "since": start_date.isoformat(),
                "until": end_date.isoformat(),
                "per_page": "100",
            }

            response = self.session.get(url, params=params)
            if response.status_code == 200:
                commits = response.json()
                for commit in commits:
                    metadata.append(
                        {
                            "type": "commit",
                            "id": commit["sha"],
                            "title": commit["commit"]["message"].split("\n")[0][:60] + "...",
                            "created_at": commit["commit"]["author"]["date"],
                            "selected": False,  # Default to not selected
                        }
                    )
        except Exception as e:
            logger.exception(
                "Error fetching commits metadata",
                error=str(e),
                repo=repo,
                username=username,
            )

        return metadata

    def _fetch_pull_requests_metadata(
        self, username: str, repo: str, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Fetch pull request metadata."""
        metadata = []
        try:
            url = f"{self.base_url}/repos/{repo}/pulls"
            params: dict[str, str] = {
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": "100",
            }

            response = self.session.get(url, params=params)
            if response.status_code == 200:
                pulls = response.json()
                for pr in pulls:
                    pr_created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    if start_date <= pr_created <= end_date and pr["user"]["login"] == username:
                        metadata.append(
                            {
                                "type": "pull_request",
                                "id": str(pr["number"]),
                                "title": f"PR #{pr['number']}: {pr['title'][:50]}...",
                                "created_at": pr["created_at"],
                                "selected": False,
                            }
                        )
        except Exception as e:
            logger.exception(
                "Error fetching pull requests metadata",
                error=str(e),
                repo=repo,
                username=username,
            )

        return metadata

    def _fetch_issues_metadata(
        self, username: str, repo: str, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Fetch issue metadata."""
        metadata = []
        try:
            url = f"{self.base_url}/repos/{repo}/issues"
            params: dict[str, str] = {
                "creator": username,
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": "100",
            }

            response = self.session.get(url, params=params)
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    # Skip pull requests (they appear in issues API)
                    if "pull_request" in issue:
                        continue

                    issue_created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                    if start_date <= issue_created <= end_date:
                        metadata.append(
                            {
                                "type": "issue",
                                "id": str(issue["number"]),
                                "title": f"Issue #{issue['number']}: {issue['title'][:50]}...",
                                "created_at": issue["created_at"],
                                "selected": False,
                            }
                        )
        except Exception as e:
            logger.exception(
                "Error fetching issues metadata",
                error=str(e),
                repo=repo,
                username=username,
            )

        return metadata

    def _fetch_releases_metadata(
        self, username: str, repo: str, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Fetch release metadata."""
        metadata = []
        try:
            url = f"{self.base_url}/repos/{repo}/releases"
            params = {"per_page": 100}

            response = self.session.get(url, params=params)
            if response.status_code == 200:
                releases = response.json()
                for release in releases:
                    if not release.get("published_at"):
                        continue

                    release_created = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
                    if start_date <= release_created <= end_date and release["author"]["login"] == username:
                        metadata.append(
                            {
                                "type": "release",
                                "id": str(release["id"]),
                                "title": f"Release: {release['name']} ({release['tag_name']})",
                                "created_at": release["published_at"],
                                # Ignore these for now, not sure what to actually do with them.
                                "selected": False,
                            }
                        )
        except Exception as e:
            logger.exception(
                "Error fetching releases metadata",
                error=str(e),
                repo=repo,
                username=username,
            )

        return metadata


class InteractiveSelector:
    """Handle interactive selection of contributions using questionary."""

    @staticmethod
    def select_contributions(
        contributions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Display contributions and allow user to select which ones to process."""
        if not contributions:
            return []

        # Create choices for questionary with better formatting
        choices = []
        for contrib in contributions:
            # Format the choice text with type, title, and date
            choice_text = InteractiveSelector._format_contribution_choice(contrib)
            choices.append(
                {
                    "name": choice_text,
                    "value": contrib,
                    "checked": False,  # Default to unchecked
                }
            )

        # Group choices by type for better organization
        grouped_choices = InteractiveSelector._group_choices_by_type(choices)

        # Use questionary checkbox for multi-selection
        try:
            selected_contributions = questionary.checkbox(
                "Select contributions to process (use Space to select, Enter to confirm):",
                choices=grouped_choices,
                style=InteractiveSelector._get_questionary_style(),
            ).ask()

            if selected_contributions is None:  # User cancelled with Ctrl+C
                sys.exit(0)

            # Mark selected contributions
            for contrib in contributions:
                contrib["selected"] = contrib in selected_contributions

            selected_count = len(selected_contributions)
            len(contributions)

            if selected_count == 0:
                pass

            return contributions

        except KeyboardInterrupt:
            sys.exit(0)

    @staticmethod
    def _format_contribution_choice(contrib: dict[str, Any]) -> str:
        """Format a contribution for display in the selection list."""
        contrib_type = contrib["type"].replace("_", " ").title()
        title = contrib["title"]
        date = contrib["created_at"][:10]  # Just the date part

        # Truncate title if too long
        if len(title) > 60:
            title = title[:57] + "..."

        return f"[{contrib_type}] {title} ({date})"

    @staticmethod
    def _group_choices_by_type(choices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Group choices by contribution type for better organization."""
        grouped: dict[str, list[dict[str, Any]]] = {}

        # Group by type
        for choice in choices:
            contrib_type = choice["value"]["type"]
            if contrib_type not in grouped:
                grouped[contrib_type] = []
            grouped[contrib_type].append(choice)

        # Create final list with separators
        final_choices: list[Any] = []

        type_order = ["commit", "pull_request", "issue", "release"]
        type_names = {
            "commit": "Commits",
            "pull_request": "Pull Requests",
            "issue": "Issues",
            "release": "Releases",
        }

        for contrib_type in type_order:
            if contrib_type in grouped:
                # Add separator (disabled choice that shows the category)
                if final_choices:  # Add spacing between groups
                    final_choices.append(questionary.Separator())

                final_choices.append(questionary.Separator(f"── {type_names[contrib_type]} ──"))

                # Add choices for this type
                final_choices.extend(grouped[contrib_type])

        return final_choices

    @staticmethod
    def _get_questionary_style() -> Any:
        """Get custom styling for questionary prompts."""
        from questionary import Style

        return Style(
            [
                ("question", "bold"),
                ("answer", "fg:#00aa00 bold"),
                ("pointer", "fg:#00aa00 bold"),
                ("highlighted", "fg:#00aa00 bold"),
                ("selected", "fg:#00aa00"),
                ("separator", "fg:#666666"),
                ("instruction", "fg:#999999"),
                ("text", ""),
                ("disabled", "fg:#666666 italic"),
            ]
        )


class UserInputManager:
    """Manages user input collection for demo parameters using questionary."""

    @staticmethod
    def get_user_parameters(args: argparse.Namespace) -> tuple[str, str, str]:
        """Get user, repository, and week from args or user input."""
        user = args.user or UserInputManager._get_username()
        repo = args.repo or UserInputManager._get_repository()
        week = args.week or UserInputManager._get_week()

        return user, repo, week

    @staticmethod
    def _get_username() -> str:
        """Get GitHub username from user input."""
        try:
            username = questionary.text("GitHub username:", style=InteractiveSelector._get_questionary_style()).ask()

            if not username or not username.strip():
                sys.exit(1)
            return username.strip()
        except KeyboardInterrupt:
            sys.exit(0)

    @staticmethod
    def _get_repository() -> str:
        """Get repository from user input."""
        try:
            repo = questionary.text(
                "Repository (format: owner/repo):",
                style=InteractiveSelector._get_questionary_style(),
            ).ask()

            if not repo or not repo.strip() or "/" not in repo:
                sys.exit(1)
            return repo.strip()
        except KeyboardInterrupt:
            sys.exit(0)

    @staticmethod
    def _get_week() -> str:
        """Get week from user input or default to current week."""
        try:
            current_week = DateTimeHelper.get_current_iso_week()
            week = questionary.text(
                f"Week (YYYY-WXX, press Enter for current week {current_week}):",
                default="",
                style=InteractiveSelector._get_questionary_style(),
            ).ask()

            if not week or not week.strip():
                week = current_week
            return week.strip()
        except KeyboardInterrupt:
            sys.exit(0)


class ContributionSummaryPrinter:
    """Utility class for printing contribution summaries."""

    @staticmethod
    def print_summary(contributions: list[dict[str, Any]]) -> None:
        """Print a formatted summary of fetched contributions."""
        if not contributions:
            return

        # Count by type
        type_counts = ContributionSummaryPrinter._count_by_type(contributions)

        for contrib_type in type_counts:
            contrib_type.replace("_", " ").title()

    @staticmethod
    def _count_by_type(contributions: list[dict[str, Any]]) -> dict[str, int]:
        """Count contributions by type."""
        type_counts: dict[str, int] = {}
        for contrib in contributions:
            contrib_type = contrib["type"]
            type_counts[contrib_type] = type_counts.get(contrib_type, 0) + 1
        return type_counts


class PrompteusAPIClient(HTTPClientMixin):
    """Client for interacting with the Prompteus GenAI service."""

    def __init__(self, base_url: str = DEFAULT_GENAI_URL, github_token: str | None = None) -> None:
        super().__init__(base_url)
        self.github_token = github_token

    def health_check(self) -> bool:
        """Check if the GenAI service is running and healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def ingest_contributions(
        self,
        user: str,
        week: str,
        repo: str,
        contributions_metadata: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Ingest contributions using the simplified API - returns summary when complete."""
        if not self.github_token:
            msg = "GitHub token is required for API calls"
            raise ValueError(msg)

        payload = {
            "user": user,
            "week": week,
            "repository": repo,
            "contributions": [
                {
                    "type": contrib["type"],
                    "id": contrib["id"],
                    "selected": contrib["selected"],
                }
                for contrib in contributions_metadata
            ],
            "github_pat": self.github_token,
        }

        # Start the ingestion task
        task_response = self._start_ingestion_task(payload)
        task_id = task_response["task_id"]

        logger.info(
            "Ingestion and summarization task started",
            task_id=task_id,
            user=user,
            week=week,
            repository=repo,
            total_contributions=task_response["total_contributions"],
        )

        # Poll for completion
        return self._poll_task_completion(task_id)

    def _start_ingestion_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Start the ingestion task and return task response."""
        response = self.session.post(f"{self.base_url}/contributions", json=payload)
        if response.status_code != 200:
            logger.error(
                "Ingestion failed",
                status_code=response.status_code,
                response_text=response.text,
                payload_sample=str(payload)[:500],
            )
        response.raise_for_status()
        return response.json()

    def _poll_task_completion(self, task_id: str) -> dict[str, Any]:
        """Poll for task completion with timeout."""
        max_retries = 120  # 2 minutes with 1-second intervals (ingestion + summarization takes longer)

        for attempt in range(max_retries):
            try:
                status_response = self.session.get(f"{self.base_url}/ingest/{task_id}")
                status_response.raise_for_status()

                status_data = status_response.json()
                status = status_data["status"]

                if status == "done":
                    logger.info(
                        "Task completed successfully",
                        task_id=task_id,
                        ingested_count=status_data.get("ingested_count", 0),
                        failed_count=status_data.get("failed_count", 0),
                    )

                    return status_data  # Return the complete status with summary

                if status == "failed":
                    error_msg = status_data.get("error_message", "Unknown error")
                    logger.error("Task failed", task_id=task_id, error_message=error_msg)
                    msg = f"Task failed: {error_msg}"
                    raise Exception(msg)

                if status in ["queued", "ingesting", "summarizing"]:
                    logger.debug(
                        "Task in progress",
                        task_id=task_id,
                        status=status,
                        attempt=attempt + 1,
                    )

                    # Show progress to user
                    time.sleep(1)  # Wait 1 second before next check

                else:
                    logger.warning("Unknown task status", task_id=task_id, status=status)
                    time.sleep(1)

            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise
                logger.warning(
                    "Error checking task status, retrying",
                    task_id=task_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                time.sleep(1)

        # If we reach here, the task didn't complete in time
        msg = f"Task {task_id} did not complete within {max_retries} seconds"
        raise Exception(msg)

    def ask_question(self, user: str, week: str, question: str) -> dict[str, Any]:
        """Ask a question about the user's contributions."""
        if not self.github_token:
            msg = "GitHub token is required for API calls"
            raise ValueError(msg)

        payload = {
            "question": question,
            "github_pat": self.github_token,
        }

        response = self.session.post(f"{self.base_url}/users/{user}/weeks/{week}/questions", json=payload)
        response.raise_for_status()
        return response.json()

    def generate_summary(self, user: str, week: str) -> dict[str, Any]:
        """Generate a comprehensive summary of the user's weekly contributions."""
        payload = {
            "user": user,
            "week": week,
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "comprehensive",
        }

        response = self.session.post(f"{self.base_url}/users/{user}/weeks/{week}/summary", json=payload)
        response.raise_for_status()
        return response.json()


class InteractiveQASession:
    """Manages interactive Q&A sessions with conversation context visualization."""

    def __init__(self, prompteus_client: PrompteusAPIClient) -> None:
        self.client = prompteus_client
        self.conversation_id = None
        self.question_count = 0

    async def run_session(self, user: str, week: str) -> None:
        """Run an interactive Q&A session with conversation context."""
        self._print_session_header()

        try:
            while True:
                question = input("❓ Your question: ").strip()

                if self._should_exit(question):
                    break

                if not question:
                    continue

                # Check for special commands
                if await self._handle_special_commands(user, week, question):
                    continue

                await self._process_question(user, week, question)

        except KeyboardInterrupt:
            pass

    def _print_session_header(self) -> None:
        """Print the Q&A session header with instructions."""
        qa_panel = Panel(
            "[bold cyan]🤖 Interactive Q&A Session with Conversation Context[/]\n\n"
            "Ask questions about the contributions. The AI will remember our conversation!\n\n"
            "[bold]Example questions:[/]\n"
            "  • What features were implemented?\n"
            "  • What bugs were fixed?\n"
            "  • Tell me more about that bug fix\n"
            "  • What was the most challenging part?\n"
            "  • How can I improve based on this?\n\n"
            "[bold]Special commands:[/]\n"
            "  • 'history' - Show conversation history\n"
            "  • 'clear' - Clear conversation history\n"
            "  • 'quit' or Ctrl+C - Exit session",
            title="[bold magenta]Q&A Session[/]",
            expand=False,
            padding=(1, 2),
        )
        console.print(qa_panel)

    def _should_exit(self, question: str) -> bool:
        """Check if the user wants to exit the session."""
        return question.lower() in ["quit", "exit", "q"]

    async def _handle_special_commands(self, user: str, week: str, question: str) -> bool:
        """Handle special commands like 'history' and 'clear'. Returns True if command was handled."""
        command = question.lower().strip()

        if command == "history":
            await self._show_conversation_history(user, week)
            return True
        if command == "clear":
            await self._clear_conversation_history(user, week)
            return True

        return False

    async def _show_conversation_history(self, user: str, week: str) -> None:
        """Show the current conversation history."""
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/users/{user}/weeks/{week}/conversations/history"
            )
            if response.status_code == 200:
                history_data = response.json()

                # Handle structured response from API
                messages = history_data.get("messages", [])
                history_data.get("session_id", "unknown")

                if not messages:
                    return

                # Process LangChain message format
                question_count = 0
                for i, message in enumerate(messages):
                    # Handle different message formats
                    if isinstance(message, dict):
                        message_type = message.get("type", "unknown")
                        content = message.get("content", str(message))
                    else:
                        # Assume alternating human/AI pattern
                        message_type = "human" if i % 2 == 0 else "ai"
                        content = str(message)

                    if message_type == "human":
                        question_count += 1
                    elif message_type == "ai":
                        # Truncate long AI responses for readability
                        content[:200] + "..." if len(content) > 200 else content

            else:
                pass
        except Exception:
            pass

    async def _clear_conversation_history(self, user: str, week: str) -> None:
        """Clear the conversation history."""
        try:
            response = self.client.session.delete(f"{self.client.base_url}/users/{user}/weeks/{week}/conversations")
            if response.status_code == 200:
                self.conversation_id = None
                self.question_count = 0
            else:
                pass
        except Exception:
            pass

    async def _process_question(self, user: str, week: str, question: str) -> None:
        """Process a single question and display the response with context indicators."""
        try:
            self.question_count += 1
            response = self.client.ask_question(user, week, question)

            # Track conversation ID from first response
            if not self.conversation_id and response.get("conversation_id"):
                self.conversation_id = response["conversation_id"]
                console.print(f"💬 Started conversation session: [cyan]{self.conversation_id}[/]")

            self._display_answer_with_context(response)

        except Exception:
            pass

    def _display_answer_with_context(self, response: dict[str, Any]) -> None:
        """Display the answer with conversation context indicators."""
        answer = response["answer"]
        confidence = response["confidence"]

        # Look for conversation context indicators in the answer
        context_keywords = [
            "previous",
            "earlier",
            "mentioned",
            "discussed",
            "that",
            "those",
            "this",
            "as I said",
            "building on",
            "following up",
            "in addition to",
        ]

        has_context = any(keyword in answer.lower() for keyword in context_keywords)

        # Display answer with context indicator
        if has_context and self.question_count > 1:
            context_icon = "🔗"
            context_note = " [dim](references previous conversation)[/]"
        else:
            context_icon = "💡"
            context_note = ""

        console.print(f"\n{context_icon} [bold]Answer:[/]{context_note}")
        console.print(f"   {answer}")
        console.print(f"   [dim]Confidence: {confidence:.2f}[/]")

        console.print(response)

        # Show evidence if available
        if response.get("evidence"):
            self._display_evidence(response["evidence"])

        # Show reasoning if available and high confidence
        if response.get("reasoning_steps") and confidence > 0.7:
            self._display_reasoning(response["reasoning_steps"])

    def _display_evidence(self, evidence: list[dict[str, Any]]) -> None:
        """Display supporting evidence for the answer."""
        console.print("   [bold]Evidence:[/]")
        for item in evidence:
            console.print(f"   {item.get('title', 'No title available')}")
            console.print(f"   {item.get('contribution_id', 'No contribution ID available')}")
            console.print(f"   {item.get('contribution_type', 'No contribution type available')}")

    def _display_reasoning(self, reasoning_steps: list[str]) -> None:
        """Display reasoning steps for transparent AI decision making."""
        console.print("   [bold]Reasoning:[/]")
        for _i, _step in enumerate(reasoning_steps):
            console.print(f"   {_step}")


class ArgumentParser:
    """Handles command line argument parsing for the demo script."""

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """Parse and return command line arguments."""
        parser = argparse.ArgumentParser(description="Prompteus Demo Script")

        # User input arguments
        parser.add_argument("--user", help="GitHub username")
        parser.add_argument("--repo", help="Repository (format: owner/repo)")
        parser.add_argument("--week", help="Week (format: YYYY-WXX)")

        # Service configuration
        parser.add_argument(
            "--genai-url",
            default=DEFAULT_GENAI_URL,
            help=f"GenAI service URL (default: {DEFAULT_GENAI_URL})",
        )

        # Authentication
        parser.add_argument(
            "--github-token",
            help=f"GitHub Personal Access Token (can also use {GITHUB_TOKEN_ENV_VAR} env var)",
        )

        return parser.parse_args()


class ServiceHealthChecker:
    """Utility class for checking service health."""

    @staticmethod
    def check_genai_service(genai_url: str) -> None:
        """Check if GenAI service is running and exit if not."""
        prompteus_client = PrompteusAPIClient(genai_url)

        if not prompteus_client.health_check():
            sys.exit(1)

        console.print(f"✅ GenAI service is running at {genai_url}", style="green")


class DemoRunner:
    """Main class that orchestrates the demo workflow."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.github_client: GitHubAPIClient | None = None
        self.prompteus_client: PrompteusAPIClient | None = None

    def run(self) -> None:
        """Execute the complete demo workflow."""
        self._print_welcome_banner()

        # Get GitHub token first
        github_token = GitHubTokenManager.get_token(self.args)

        self._initialize_services(github_token)
        self._authenticate_github(github_token)

        user, repo, week = UserInputManager.get_user_parameters(self.args)

        # Process contributions (ingestion + summarization combined)
        result = self._fetch_and_process_contributions(user, repo, week)

        # Display the generated summary
        self._display_summary(result)

        # Start interactive Q&A session
        asyncio.run(self._run_qa_session(user, week))

    def _print_welcome_banner(self) -> None:
        """Print the welcome banner."""
        welcome_panel = Panel(
            "[bold blue]🚀 Welcome to Prompteus Demo![/]",
            title="[bold green]Prompteus[/]",
            expand=False,
            padding=(1, 2),
        )
        console.print(welcome_panel)

    def _initialize_services(self, github_token: str) -> None:
        """Initialize and health check all required services."""
        ServiceHealthChecker.check_genai_service(self.args.genai_url)
        self.prompteus_client = PrompteusAPIClient(self.args.genai_url, github_token)

    def _authenticate_github(self, github_token: str) -> None:
        """Initialize authenticated GitHub client with the provided token."""
        self.github_client = GitHubAPIClient(github_token)
        if not self.github_client.test_authentication():
            sys.exit(1)

        console.print("✅ GitHub authentication successful", style="green")

    def _fetch_and_process_contributions(self, user: str, repo: str, week: str) -> dict[str, Any]:
        """Fetch contribution metadata and process them with the GenAI service."""
        try:
            if not self.github_client:
                msg = "GitHub client not initialized"
                raise RuntimeError(msg)
            contributions_metadata = self.github_client.get_contribution_metadata(user, repo, week)
            ContributionSummaryPrinter.print_summary(contributions_metadata)

            if not contributions_metadata:
                sys.exit(0)

            # Interactive selection of contributions
            selected_contributions = InteractiveSelector.select_contributions(contributions_metadata)

            selected_count = sum(1 for c in selected_contributions if c["selected"])
            if selected_count == 0:
                sys.exit(0)

            # Process selected contributions (ingestion + summarization)

            if not self.prompteus_client:
                msg = "Prompteus client not initialized"
                raise RuntimeError(msg)
            result = self.prompteus_client.ingest_contributions(
                user=user, week=week, repo=repo, contributions_metadata=selected_contributions
            )
            console.print("\n✅ Task completed successfully!", style="green bold")
            console.print(f"   [green]Ingested:[/] {result.get('ingested_count', 0)} contributions")
            console.print(f"   [red]Failed:[/] {result.get('failed_count', 0)} contributions")

            return result

        except Exception as e:
            logger.exception("Failed to fetch and process contributions", error=str(e))
            sys.exit(1)

    def _display_summary(self, result: dict[str, Any]) -> None:
        """Display the generated summary from the task result using rich markdown formatting."""
        summary = result.get("summary")
        if not summary:
            console.print("⚠️  No summary available from the task.", style="yellow")
            return

        # Build markdown content for the summary
        markdown_content = []

        # Add title
        markdown_content.append("# 📄 Weekly Contribution Summary\n")

        # Display overview
        if summary.get("overview"):
            markdown_content.append("## Overview\n")
            markdown_content.append(f"{summary['overview']}\n")

        # Display detailed sections
        sections = [
            ("commits_summary", "Commits"),
            ("pull_requests_summary", "Pull Requests"),
            ("issues_summary", "Issues"),
            ("releases_summary", "Releases"),
        ]

        for section_key, section_title in sections:
            content = summary.get(section_key)
            if content and content.strip():
                markdown_content.append(f"## {section_title}\n")
                markdown_content.append(f"{content}\n")

        # Display analysis
        if summary.get("analysis"):
            markdown_content.append("## Analysis\n")
            markdown_content.append(f"{summary['analysis']}\n")

        # Display achievements
        achievements = summary.get("key_achievements", [])
        if achievements:
            markdown_content.append("## Key Achievements\n")
            for achievement in achievements:
                markdown_content.append(f"• {achievement}\n")
            markdown_content.append("")

        # Display areas for improvement
        improvements = summary.get("areas_for_improvement", [])
        if improvements:
            markdown_content.append("## Areas for Improvement\n")
            for improvement in improvements:
                markdown_content.append(f"• {improvement}\n")
            markdown_content.append("")

        # Display metadata
        metadata = summary.get("metadata", {})
        if metadata:
            markdown_content.append("## Summary Statistics\n")
            markdown_content.append(f"• **Total contributions:** {metadata.get('total_contributions', 0)}\n")
            markdown_content.append(f"• **Processing time:** {metadata.get('processing_time_ms', 0)}ms\n")

        # Render the markdown content using rich
        full_markdown = "\n".join(markdown_content)
        console.print(Markdown(full_markdown))

    async def _run_qa_session(self, user: str, week: str) -> None:
        """Run the interactive Q&A session."""
        if not self.prompteus_client:
            msg = "Prompteus client not initialized"
            raise RuntimeError(msg)
        qa_session = InteractiveQASession(self.prompteus_client)
        await qa_session.run_session(user, week)


def main() -> None:
    """Main entry point for the demo script."""
    try:
        args = ArgumentParser.parse_arguments()
        demo_runner = DemoRunner(args)
        demo_runner.run()

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception("Demo failed with unexpected error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
