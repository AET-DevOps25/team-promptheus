#!/usr/bin/env python3
"""
Prompteus Demo Script

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
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
import structlog
import questionary
from requests.adapters import HTTPAdapter
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class GitHubTokenManager:
    """Manages GitHub Personal Access Token retrieval from various sources"""
    
    @staticmethod
    def get_token(args) -> str:
        """Get GitHub Personal Access Token from args, environment, or prompt user"""
        # Priority 1: Command line argument
        if args.github_token:
            logger.info("Using GitHub token from command line argument")
            return args.github_token
        
        # Priority 2: Environment variable
        env_token = os.getenv(GITHUB_TOKEN_ENV_VAR)
        if env_token:
            logger.info("Using GitHub token from environment variable",
                       env_var=GITHUB_TOKEN_ENV_VAR)
            return env_token
        
        # Priority 3: Interactive prompt (fallback)
        return GitHubTokenManager._prompt_for_token()
    
    @staticmethod
    def _prompt_for_token() -> str:
        """Prompt user for GitHub token with helpful instructions"""
        print("🔑 GitHub Personal Access Token Required")
        print("=" * 50)
        print("To fetch your GitHub contributions, we need a Personal Access Token (PAT).")
        print("You can create one at: https://github.com/settings/tokens")
        print("Required scopes: 'repo' (for private repos) or 'public_repo' (for public repos only)")
        print()
        print("💡 Tip: You can avoid this prompt by:")
        print("  - Using --github-token TOKEN argument")
        print(f"  - Setting {GITHUB_TOKEN_ENV_VAR} environment variable")
        print()
        
        token = getpass.getpass("Enter your GitHub PAT: ").strip()
        
        if not token:
            print("❌ No token provided. Exiting.")
            sys.exit(1)
        
        return token


class DateTimeHelper:
    """Helper class for date and time operations"""
    
    @staticmethod
    def parse_iso_week(week: str) -> tuple[datetime, datetime]:
        """Parse ISO week format (YYYY-WXX) and return start/end dates"""
        year, week_num = week.split('-W')
        year = int(year)
        week_num = int(week_num)
        
        # Calculate week start and end dates (timezone-aware)
        jan_1 = datetime(year, 1, 1, tzinfo=timezone.utc)
        week_start = jan_1 + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=7)
        
        return week_start, week_end
    
    @staticmethod
    def get_current_iso_week() -> str:
        """Get the current ISO week in YYYY-WXX format"""
        current_date = datetime.now()
        year = current_date.year
        week_num = current_date.isocalendar()[1]
        return f"{year}-W{week_num:02d}"


class HTTPClientMixin:
    """Mixin providing configured HTTP session with retry logic"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
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
    """GitHub API client for fetching contribution metadata"""
    
    def __init__(self, token: str):
        super().__init__(GITHUB_API_BASE_URL)
        self.token = token
        self._configure_authentication()
    
    def _configure_authentication(self) -> None:
        """Configure GitHub API authentication headers"""
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": USER_AGENT
        })
    
    def test_authentication(self) -> bool:
        """Test if the GitHub token is valid"""
        try:
            response = self.session.get(f"{self.base_url}/user")
            if response.status_code == 200:
                user_data = response.json()
                logger.info("GitHub authentication successful", 
                           user=user_data.get("login"))
                return True
            else:
                logger.error("GitHub authentication failed", 
                           status_code=response.status_code)
                return False
        except Exception as e:
            logger.error("GitHub authentication error", error=str(e))
            return False
    
    def get_contribution_metadata(self, username: str, repo: str, week: str) -> List[Dict[str, Any]]:
        """Fetch metadata for all contributions in the specified week"""
        week_start, week_end = DateTimeHelper.parse_iso_week(week)
        
        logger.info("Fetching contribution metadata", 
                   username=username, 
                   repo=repo, 
                   week=week,
                   start_date=week_start.isoformat(),
                   end_date=week_end.isoformat())
        
        metadata = []
        
        # Fetch all contribution types metadata
        metadata.extend(self._fetch_commits_metadata(username, repo, week_start, week_end))
        metadata.extend(self._fetch_pull_requests_metadata(username, repo, week_start, week_end))
        metadata.extend(self._fetch_issues_metadata(username, repo, week_start, week_end))
        metadata.extend(self._fetch_releases_metadata(username, repo, week_start, week_end))
        
        logger.info("Contribution metadata fetched successfully", 
                   username=username, 
                   repo=repo, 
                   total_contributions=len(metadata))
        
        return metadata
    
    def _fetch_commits_metadata(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch commit metadata"""
        metadata = []
        try:
            url = f"{self.base_url}/repos/{repo}/commits"
            params = {
                "author": username,
                "since": start_date.isoformat(),
                "until": end_date.isoformat(),
                "per_page": 100
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                commits = response.json()
                for commit in commits:
                    metadata.append({
                        "type": "commit",
                        "id": commit["sha"],
                        "title": commit["commit"]["message"].split('\n')[0][:60] + "...",
                        "created_at": commit["commit"]["author"]["date"],
                        "selected": False  # Default to not selected
                    })
        except Exception as e:
            logger.error("Error fetching commits metadata", error=str(e), repo=repo, username=username)
        
        return metadata
    
    def _fetch_pull_requests_metadata(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch pull request metadata"""
        metadata = []
        try:
            url = f"{self.base_url}/repos/{repo}/pulls"
            params = {"state": "all", "sort": "created", "direction": "desc", "per_page": 100}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                pulls = response.json()
                for pr in pulls:
                    pr_created = datetime.fromisoformat(pr["created_at"].replace('Z', '+00:00'))
                    if (start_date <= pr_created <= end_date and 
                        pr["user"]["login"] == username):
                        metadata.append({
                            "type": "pull_request",
                            "id": str(pr["number"]),
                            "title": f"PR #{pr['number']}: {pr['title'][:50]}...",
                            "created_at": pr["created_at"],
                            "selected": False
                        })
        except Exception as e:
            logger.error("Error fetching pull requests metadata", error=str(e), repo=repo, username=username)
        
        return metadata
    
    def _fetch_issues_metadata(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch issue metadata"""
        metadata = []
        try:
            url = f"{self.base_url}/repos/{repo}/issues"
            params = {"creator": username, "state": "all", "sort": "created", "direction": "desc", "per_page": 100}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    # Skip pull requests (they appear in issues API)
                    if "pull_request" in issue:
                        continue
                    
                    issue_created = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
                    if start_date <= issue_created <= end_date:
                        metadata.append({
                            "type": "issue",
                            "id": str(issue["number"]),
                            "title": f"Issue #{issue['number']}: {issue['title'][:50]}...",
                            "created_at": issue["created_at"],
                            "selected": False
                        })
        except Exception as e:
            logger.error("Error fetching issues metadata", error=str(e), repo=repo, username=username)
        
        return metadata
    
    def _fetch_releases_metadata(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch release metadata"""
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
                    
                    release_created = datetime.fromisoformat(release["published_at"].replace('Z', '+00:00'))
                    if (start_date <= release_created <= end_date and 
                        release["author"]["login"] == username):
                        metadata.append({
                            "type": "release",
                            "id": str(release["id"]),
                            "title": f"Release: {release['name']} ({release['tag_name']})",
                            "created_at": release["published_at"],
                            # Ignore these for now, not sure what to actually do with them.
                            "selected": False
                        })
        except Exception as e:
            logger.error("Error fetching releases metadata", error=str(e), repo=repo, username=username)
        
        return metadata


class InteractiveSelector:
    """Handle interactive selection of contributions using questionary"""
    
    @staticmethod
    def select_contributions(contributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Display contributions and allow user to select which ones to process"""
        if not contributions:
            print("📭 No contributions found for the specified period.")
            return []
        
        print("\n📋 Select Contributions to Process")
        print("=" * 50)
        
        # Create choices for questionary with better formatting
        choices = []
        for contrib in contributions:
            # Format the choice text with type, title, and date
            choice_text = InteractiveSelector._format_contribution_choice(contrib)
            choices.append({
                'name': choice_text,
                'value': contrib,
                'checked': False  # Default to unchecked
            })
        
        # Group choices by type for better organization
        grouped_choices = InteractiveSelector._group_choices_by_type(choices)
        
        # Use questionary checkbox for multi-selection
        try:
            selected_contributions = questionary.checkbox(
                "Select contributions to process (use Space to select, Enter to confirm):",
                choices=grouped_choices,
                style=InteractiveSelector._get_questionary_style()
            ).ask()
            
            if selected_contributions is None:  # User cancelled with Ctrl+C
                print("\n❌ Selection cancelled.")
                sys.exit(0)
            
            # Mark selected contributions
            for contrib in contributions:
                contrib['selected'] = contrib in selected_contributions
            
            selected_count = len(selected_contributions)
            total_count = len(contributions)
            
            print(f"\n✅ Selected {selected_count} out of {total_count} contributions")
            
            if selected_count == 0:
                print("💡 No contributions selected. You can re-run the script to select different contributions.")
            
            return contributions
            
        except KeyboardInterrupt:
            print("\n👋 Selection cancelled by user.")
            sys.exit(0)
    
    @staticmethod
    def _format_contribution_choice(contrib: Dict[str, Any]) -> str:
        """Format a contribution for display in the selection list"""
        contrib_type = contrib["type"].replace('_', ' ').title()
        title = contrib["title"]
        date = contrib["created_at"][:10]  # Just the date part
        
        # Truncate title if too long
        if len(title) > 60:
            title = title[:57] + "..."
        
        return f"[{contrib_type}] {title} ({date})"
    
    @staticmethod
    def _group_choices_by_type(choices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group choices by contribution type for better organization"""
        grouped = {}
        
        # Group by type
        for choice in choices:
            contrib_type = choice['value']['type']
            if contrib_type not in grouped:
                grouped[contrib_type] = []
            grouped[contrib_type].append(choice)
        
        # Create final list with separators
        final_choices = []
        
        type_order = ['commit', 'pull_request', 'issue', 'release']
        type_names = {
            'commit': 'Commits',
            'pull_request': 'Pull Requests', 
            'issue': 'Issues',
            'release': 'Releases'
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
    def _get_questionary_style():
        """Get custom styling for questionary prompts"""
        from questionary import Style
        
        return Style([
            ('question', 'bold'),
            ('answer', 'fg:#00aa00 bold'),
            ('pointer', 'fg:#00aa00 bold'),
            ('highlighted', 'fg:#00aa00 bold'),
            ('selected', 'fg:#00aa00'),
            ('separator', 'fg:#666666'),
            ('instruction', 'fg:#999999'),
            ('text', ''),
            ('disabled', 'fg:#666666 italic')
        ])


class UserInputManager:
    """Manages user input collection for demo parameters using questionary"""
    
    @staticmethod
    def get_user_parameters(args) -> tuple[str, str, str]:
        """Get user, repository, and week from args or user input"""
        user = args.user or UserInputManager._get_username()
        repo = args.repo or UserInputManager._get_repository()
        week = args.week or UserInputManager._get_week()
        
        return user, repo, week
    
    @staticmethod
    def _get_username() -> str:
        """Get GitHub username from user input"""
        try:
            username = questionary.text(
                "GitHub username:",
                style=InteractiveSelector._get_questionary_style()
            ).ask()
            
            if not username or not username.strip():
                print("❌ Username is required.")
                sys.exit(1)
            return username.strip()
        except KeyboardInterrupt:
            print("\n👋 Cancelled by user.")
            sys.exit(0)
    
    @staticmethod
    def _get_repository() -> str:
        """Get repository from user input"""
        try:
            repo = questionary.text(
                "Repository (format: owner/repo):",
                style=InteractiveSelector._get_questionary_style()
            ).ask()
            
            if not repo or not repo.strip() or '/' not in repo:
                print("❌ Repository must be in format: owner/repo")
                sys.exit(1)
            return repo.strip()
        except KeyboardInterrupt:
            print("\n👋 Cancelled by user.")
            sys.exit(0)
    
    @staticmethod
    def _get_week() -> str:
        """Get week from user input or default to current week"""
        try:
            current_week = DateTimeHelper.get_current_iso_week()
            week = questionary.text(
                f"Week (YYYY-WXX, press Enter for current week {current_week}):",
                default="",
                style=InteractiveSelector._get_questionary_style()
            ).ask()
            
            if not week or not week.strip():
                week = current_week
                print(f"✅ Using current week: {week}")
            return week.strip()
        except KeyboardInterrupt:
            print("\n👋 Cancelled by user.")
            sys.exit(0)


class ContributionSummaryPrinter:
    """Utility class for printing contribution summaries"""
    
    @staticmethod
    def print_summary(contributions: List[Dict[str, Any]]) -> None:
        """Print a formatted summary of fetched contributions"""
        if not contributions:
            print("📭 No contributions found for the specified period.")
            return
        
        print(f"\n📊 Contributions Summary")
        print("=" * 30)
        
        # Count by type
        type_counts = ContributionSummaryPrinter._count_by_type(contributions)
        
        for contrib_type, count in type_counts.items():
            formatted_type = contrib_type.replace('_', ' ').title()
            print(f"  {formatted_type}: {count}")
        
        print(f"  Total: {len(contributions)}")
        print()
    
    @staticmethod
    def _count_by_type(contributions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count contributions by type"""
        type_counts = {}
        for contrib in contributions:
            contrib_type = contrib["type"]
            type_counts[contrib_type] = type_counts.get(contrib_type, 0) + 1
        return type_counts


class PrompteusAPIClient(HTTPClientMixin):
    """Client for interacting with the Prompteus GenAI service"""
    
    def __init__(self, base_url: str = DEFAULT_GENAI_URL):
        super().__init__(base_url)
    
    def health_check(self) -> bool:
        """Check if the GenAI service is running and healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def ingest_contributions(self, user: str, week: str, repo: str, contributions_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest contributions using the simplified API - returns summary when complete"""
        payload = {
            "user": user,
            "week": week,
            "repository": repo,
            "contributions": [
                {
                    "type": contrib["type"],
                    "id": contrib["id"],
                    "selected": contrib["selected"]
                }
                for contrib in contributions_metadata
            ]
        }
        
        # Start the ingestion task
        task_response = self._start_ingestion_task(payload)
        task_id = task_response["task_id"]
        
        logger.info("Ingestion and summarization task started", 
                   task_id=task_id, 
                   user=user, 
                   week=week,
                   repository=repo,
                   total_contributions=task_response["total_contributions"])
        
        # Poll for completion
        return self._poll_task_completion(task_id)
    
    def _start_ingestion_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Start the ingestion task and return task response"""
        response = self.session.post(f"{self.base_url}/contributions", json=payload)
        if response.status_code != 200:
            logger.error("Ingestion failed", 
                        status_code=response.status_code,
                        response_text=response.text,
                        payload_sample=str(payload)[:500])
        response.raise_for_status()
        return response.json()
    
    def _poll_task_completion(self, task_id: str) -> Dict[str, Any]:
        """Poll for task completion with timeout"""
        max_retries = 120  # 2 minutes with 1-second intervals (ingestion + summarization takes longer)
        
        for attempt in range(max_retries):
            try:
                status_response = self.session.get(f"{self.base_url}/ingest/{task_id}")
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data["status"]
                
                if status == "done":
                    logger.info("Task completed successfully", 
                               task_id=task_id,
                               ingested_count=status_data.get("ingested_count", 0),
                               failed_count=status_data.get("failed_count", 0))
                    
                    return status_data  # Return the complete status with summary
                
                elif status == "failed":
                    error_msg = status_data.get("error_message", "Unknown error")
                    logger.error("Task failed", 
                                task_id=task_id, 
                                error_message=error_msg)
                    raise Exception(f"Task failed: {error_msg}")
                
                elif status in ["queued", "ingesting", "summarizing"]:
                    logger.debug("Task in progress", 
                                task_id=task_id, 
                                status=status,
                                attempt=attempt + 1)
                    
                    # Show progress to user
                    status_emoji = {
                        "queued": "⏳",
                        "ingesting": "📥", 
                        "summarizing": "🤖"
                    }
                    print(f"\r{status_emoji.get(status, '⏳')} {status.title()}...", end='', flush=True)
                    time.sleep(1)  # Wait 1 second before next check
                
                else:
                    logger.warning("Unknown task status", 
                                  task_id=task_id, 
                                  status=status)
                    time.sleep(1)
                    
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise
                logger.warning("Error checking task status, retrying", 
                              task_id=task_id, 
                              attempt=attempt + 1, 
                              error=str(e))
                time.sleep(1)
        
        # If we reach here, the task didn't complete in time
        raise Exception(f"Task {task_id} did not complete within {max_retries} seconds")
    
    def ask_question(self, user: str, week: str, question: str) -> Dict[str, Any]:
        """Ask a question about the user's contributions"""
        payload = {
            "question": question,
            "context": {
                "focus_areas": ["features", "bugs", "performance"],
                "include_evidence": True,
                "reasoning_depth": "detailed"
            }
        }
        
        response = self.session.post(f"{self.base_url}/users/{user}/weeks/{week}/questions", json=payload)
        response.raise_for_status()
        return response.json()
    
    def generate_summary(self, user: str, week: str) -> Dict[str, Any]:
        """Generate a comprehensive summary of the user's weekly contributions"""
        payload = {
            "user": user,
            "week": week,
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "comprehensive"
        }
        
        response = self.session.post(f"{self.base_url}/users/{user}/weeks/{week}/summary", json=payload)
        response.raise_for_status()
        return response.json()
    
    def generate_summary_stream(self, user: str, week: str) -> None:
        """Generate and display a streaming summary of the user's weekly contributions"""
        payload = {
            "user": user,
            "week": week,
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "comprehensive"
        }
        
        response = self.session.post(f"{self.base_url}/users/{user}/weeks/{week}/summary/stream", 
                                   json=payload, stream=True)
        response.raise_for_status()
        
        StreamingSummaryDisplayer.display_streaming_response(response)


class StreamingSummaryDisplayer:
    """Handles the display of streaming summary responses"""
    
    @staticmethod
    def display_streaming_response(response) -> None:
        """Display streaming summary with real-time updates"""
        print("\n📄 Weekly Contribution Summary")
        print("=" * 50)
        
        current_section = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        chunk_data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                        StreamingSummaryDisplayer._process_chunk(chunk_data, current_section)
                        
                        # Update current section if changed
                        if chunk_data.get("chunk_type") == "section" and chunk_data.get("section"):
                            current_section = chunk_data["section"]
                            
                    except json.JSONDecodeError as e:
                        logger.warning("Failed to parse streaming chunk", 
                                     error=str(e), 
                                     line=line_str)
                        continue
    
    @staticmethod
    def _process_chunk(chunk_data: Dict[str, Any], current_section: Optional[str]) -> None:
        """Process individual chunks of the streaming response"""
        chunk_type = chunk_data.get("chunk_type")
        content = chunk_data.get("content", "")
        section = chunk_data.get("section")
        
        if chunk_type == "section" and section:
            # New section starting
            if section != current_section:
                section_title = section.replace('_', ' ').title()
                print(f"\n\n**{section_title}:**")
        
        elif chunk_type == "content":
            # Stream content without newline
            print(content, end='', flush=True)
        
        elif chunk_type == "metadata":
            # Summary metadata
            metadata = chunk_data["metadata"]
            StreamingSummaryDisplayer._print_metadata(metadata)
        
        elif chunk_type == "complete":
            # Summary complete
            metadata = chunk_data.get("metadata", {})
            if not metadata.get('printed'):  # Avoid duplicate metadata
                StreamingSummaryDisplayer._print_metadata(metadata)
            print(f"\n✅ Summary generation completed!")
        
        elif chunk_type == "error":
            print(f"\n❌ Error during summary generation: {content}")
    
    @staticmethod
    def _print_metadata(metadata: Dict[str, Any]) -> None:
        """Print summary metadata statistics"""
        print(f"\n\n**Summary Statistics:**")
        print(f"- Total contributions: {metadata.get('total_contributions', 0)}")
        print(f"- Processing time: {metadata.get('processing_time_ms', 0)}ms")


class InteractiveQASession:
    """Manages interactive Q&A sessions"""
    
    def __init__(self, prompteus_client: PrompteusAPIClient):
        self.client = prompteus_client
    
    async def run_session(self, user: str, week: str) -> None:
        """Run an interactive Q&A session with the user"""
        self._print_session_header()
        
        try:
            while True:
                question = input("❓ Your question: ").strip()
                
                if self._should_exit(question):
                    break
                
                if not question:
                    continue
                
                await self._process_question(user, week, question)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
    
    def _print_session_header(self) -> None:
        """Print the Q&A session header with instructions"""
        print("\n🤖 Interactive Q&A Session")
        print("=" * 40)
        print("Ask questions about the contributions. Type 'quit' or press Ctrl+C to exit.")
        print("Example questions:")
        print("  - What features were implemented?")
        print("  - What bugs were fixed?")
        print("  - What files were changed the most?")
        print("  - Summarize the week's work")
        print()
    
    def _should_exit(self, question: str) -> bool:
        """Check if the user wants to exit the session"""
        return question.lower() in ['quit', 'exit', 'q']
    
    async def _process_question(self, user: str, week: str, question: str) -> None:
        """Process a single question and display the response"""
        try:
            print("🤔 Thinking...")
            response = self.client.ask_question(user, week, question)
            
            self._display_answer(response)
            
        except Exception as e:
            print(f"❌ Error processing question: {e}")
            print()
    
    def _display_answer(self, response: Dict[str, Any]) -> None:
        """Display the answer and supporting evidence"""
        print(f"\n💡 Answer:")
        print(f"   {response['answer']}")
        print(f"   Confidence: {response['confidence']:.2f}")
        
        if response.get('evidence'):
            self._display_evidence(response['evidence'])
        
        print()
    
    def _display_evidence(self, evidence: List[Dict[str, Any]]) -> None:
        """Display supporting evidence for the answer"""
        print(f"\n📚 Evidence ({len(evidence)} items):")
        for i, item in enumerate(evidence[:3], 1):
            title = item.get('title', 'No title available')
            excerpt = item.get('excerpt', 'No excerpt available')
            print(f"   {i}. {title}: {excerpt[:80]}...")


class ArgumentParser:
    """Handles command line argument parsing for the demo script"""
    
    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """Parse and return command line arguments"""
        parser = argparse.ArgumentParser(description="Prompteus Demo Script")
        
        # User input arguments
        parser.add_argument("--user", help="GitHub username")
        parser.add_argument("--repo", help="Repository (format: owner/repo)")
        parser.add_argument("--week", help="Week (format: YYYY-WXX)")
        
        # Service configuration
        parser.add_argument("--genai-url", default=DEFAULT_GENAI_URL, 
                           help=f"GenAI service URL (default: {DEFAULT_GENAI_URL})")
        
        # Authentication
        parser.add_argument("--github-token", 
                           help=f"GitHub Personal Access Token (can also use {GITHUB_TOKEN_ENV_VAR} env var)")
        
        return parser.parse_args()


class ServiceHealthChecker:
    """Utility class for checking service health"""
    
    @staticmethod
    def check_genai_service(genai_url: str) -> None:
        """Check if GenAI service is running and exit if not"""
        prompteus_client = PrompteusAPIClient(genai_url)
        
        if not prompteus_client.health_check():
            print(f"❌ GenAI service is not running at {genai_url}")
            print("Please start the service with: docker compose up")
            sys.exit(1)
        
        print(f"✅ GenAI service is running at {genai_url}")


class DemoRunner:
    """Main class that orchestrates the demo workflow"""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.github_client: Optional[GitHubAPIClient] = None
        self.prompteus_client: Optional[PrompteusAPIClient] = None
    
    def run(self) -> None:
        """Execute the complete demo workflow"""
        self._print_welcome_banner()
        self._initialize_services()
        self._authenticate_github()
        
        user, repo, week = UserInputManager.get_user_parameters(self.args)
        
        # Process contributions (ingestion + summarization combined)
        result = self._fetch_and_process_contributions(user, repo, week)
        
        # Display the generated summary
        self._display_summary(result)
        
        # Start interactive Q&A session
        asyncio.run(self._run_qa_session(user, week))
    
    def _print_welcome_banner(self) -> None:
        """Print the welcome banner"""
        print("🚀 Welcome to Prompteus Demo!")
        print("=" * 40)
    
    def _initialize_services(self) -> None:
        """Initialize and health check all required services"""
        ServiceHealthChecker.check_genai_service(self.args.genai_url)
        self.prompteus_client = PrompteusAPIClient(self.args.genai_url)
    
    def _authenticate_github(self) -> None:
        """Get GitHub token and initialize authenticated client"""
        github_token = GitHubTokenManager.get_token(self.args)
        
        self.github_client = GitHubAPIClient(github_token)
        if not self.github_client.test_authentication():
            print("❌ GitHub authentication failed. Please check your token.")
            sys.exit(1)
        
        print("✅ GitHub authentication successful")
    
    def _fetch_and_process_contributions(self, user: str, repo: str, week: str) -> Dict[str, Any]:
        """Fetch contribution metadata and process them with the GenAI service"""
        try:
            print(f"\n📥 Fetching contribution metadata for {user} in {repo} for week {week}...")
            
            contributions_metadata = self.github_client.get_contribution_metadata(user, repo, week)
            ContributionSummaryPrinter.print_summary(contributions_metadata)
            
            if not contributions_metadata:
                print("No contributions to analyze. Exiting.")
                sys.exit(0)
            
            # Interactive selection of contributions
            selected_contributions = InteractiveSelector.select_contributions(contributions_metadata)
            
            selected_count = sum(1 for c in selected_contributions if c['selected'])
            if selected_count == 0:
                print("No contributions selected. Exiting.")
                sys.exit(0)
            
            # Process selected contributions (ingestion + summarization)
            print(f"\n🚀 Processing {selected_count} selected contributions...")
            print("This will ingest the contributions and generate a summary.")
            
            result = self.prompteus_client.ingest_contributions(user, week, repo, selected_contributions)
            print(f"\n✅ Task completed successfully!")
            print(f"   Ingested: {result.get('ingested_count', 0)} contributions")
            print(f"   Failed: {result.get('failed_count', 0)} contributions")
            
            return result
            
        except Exception as e:
            logger.error("Failed to fetch and process contributions", error=str(e))
            print(f"❌ Failed to fetch and process contributions: {e}")
            sys.exit(1)
    
    def _display_summary(self, result: Dict[str, Any]) -> None:
        """Display the generated summary from the task result"""
        summary = result.get('summary')
        if not summary:
            print("⚠️  No summary available from the task.")
            return
            
        print("\n📄 Weekly Contribution Summary")
        print("=" * 50)
        
        # Display overview
        if summary.get('overview'):
            print(f"\n**Overview:**")
            print(summary['overview'])
        
        # Display detailed sections
        sections = [
            ('commits_summary', 'Commits'),
            ('pull_requests_summary', 'Pull Requests'),
            ('issues_summary', 'Issues'), 
            ('releases_summary', 'Releases')
        ]
        
        for section_key, section_title in sections:
            content = summary.get(section_key)
            if content and content.strip():
                print(f"\n**{section_title}:**")
                print(content)
        
        # Display analysis
        if summary.get('analysis'):
            print(f"\n**Analysis:**")
            print(summary['analysis'])
        
        # Display achievements
        achievements = summary.get('key_achievements', [])
        if achievements:
            print(f"\n**Key Achievements:**")
            for achievement in achievements:
                print(f"  • {achievement}")
        
        # Display areas for improvement
        improvements = summary.get('areas_for_improvement', [])
        if improvements:
            print(f"\n**Areas for Improvement:**")
            for improvement in improvements:
                print(f"  • {improvement}")
        
        # Display metadata
        metadata = summary.get('metadata', {})
        if metadata:
            print(f"\n**Summary Statistics:**")
            print(f"  • Total contributions: {metadata.get('total_contributions', 0)}")
            print(f"  • Processing time: {metadata.get('processing_time_ms', 0)}ms")
    
    async def _run_qa_session(self, user: str, week: str) -> None:
        """Run the interactive Q&A session"""
        qa_session = InteractiveQASession(self.prompteus_client)
        await qa_session.run_session(user, week)


def main():
    """Main entry point for the demo script"""
    try:
        args = ArgumentParser.parse_arguments()
        demo_runner = DemoRunner(args)
        demo_runner.run()
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error("Demo failed with unexpected error", error=str(e))
        print(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 