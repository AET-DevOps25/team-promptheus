#!/usr/bin/env python3
"""
Prompteus Demo Script

This script demonstrates the full Prompteus workflow:
1. Prompts for GitHub Personal Access Token (PAT) or uses provided token
2. Fetches GitHub contributions for a specified user/repository
3. Generates AI-powered summaries using the GenAI service
4. Provides an interactive Q&A session about the contributions

Features:
- Live streaming summary generation with real-time updates
- Evidence-based Q&A with confidence scoring  
- Flexible GitHub token authentication (CLI, env var, or prompt)
- Task-based ingestion with progress tracking

Planned Improvements:
- Conversational Q&A sessions with context retention between messages
- Direct insights beyond evidence for broader analytical answers

GitHub Token Options:
    --github-token TOKEN    Provide GitHub PAT via command line
    GH_PAT environment var  Set GitHub PAT via environment variable
    Interactive prompt      Enter token when prompted (fallback)

Usage:
    python demo.py [--user USERNAME] [--repo REPOSITORY] [--week WEEK] [--github-token TOKEN]

Examples:
    python demo.py --user octocat --repo Hello-World --week 2024-W01 --github-token ghp_xxxxx
    GH_PAT=ghp_xxxxx python demo.py --user octocat --repo Hello-World --week 2024-W01
    python demo.py --user octocat --repo Hello-World --week 2024-W01  # will prompt for token
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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration constants
GITHUB_API_BASE_URL = "https://api.github.com"
DEFAULT_GENAI_URL = "http://localhost:3003"
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
    """GitHub API client for fetching contributions"""
    
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
    
    def get_user_contributions(self, username: str, repo: str, week: str) -> List[Dict[str, Any]]:
        """Fetch all contributions for a user in a specific repository and week"""
        week_start, week_end = DateTimeHelper.parse_iso_week(week)
        
        logger.info("Fetching contributions", 
                   username=username, 
                   repo=repo, 
                   week=week,
                   start_date=week_start.isoformat(),
                   end_date=week_end.isoformat())
        
        contributions = []
        
        # Fetch all contribution types
        contribution_fetchers = [
            self._fetch_commits,
            self._fetch_pull_requests,
            self._fetch_issues,
            self._fetch_releases
        ]
        
        for fetcher in contribution_fetchers:
            contributions.extend(fetcher(username, repo, week_start, week_end))
        
        logger.info("Contributions fetched successfully", 
                   username=username, 
                   repo=repo, 
                   total_contributions=len(contributions))
        
        return contributions
    
    def _fetch_commits(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch commits for the user in the specified time range"""
        commits = []
        
        try:
            # Get commits from the repository
            url = f"{self.base_url}/repos/{repo}/commits"
            params = {
                "author": username,
                "since": start_date.isoformat(),
                "until": end_date.isoformat(),
                "per_page": 100
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                commit_data = response.json()
                
                for commit in commit_data:
                    # Get detailed commit information
                    commit_detail = self._get_commit_details(repo, commit["sha"])
                    if commit_detail:
                        commits.append(commit_detail)
            else:
                logger.warning("Failed to fetch commits", 
                             status_code=response.status_code,
                             repo=repo,
                             username=username)
        
        except Exception as e:
            logger.error("Error fetching commits", error=str(e), repo=repo, username=username)
        
        return commits
    
    def _get_commit_details(self, repo: str, sha: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific commit"""
        try:
            url = f"{self.base_url}/repos/{repo}/commits/{sha}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                commit_data = response.json()
                
                # Transform to our format
                return {
                    "id": f"commit-{sha}",
                    "type": "commit",
                    "repository": repo,
                    "author": commit_data["author"]["login"] if commit_data.get("author") else "unknown",
                    "created_at": commit_data["commit"]["author"]["date"],
                    "url": commit_data["url"],
                    "sha": sha,
                    "message": commit_data["commit"]["message"],
                    "tree": {
                        "sha": commit_data["commit"]["tree"]["sha"],
                        "url": commit_data["commit"]["tree"]["url"]
                    },
                    "parents": [
                        {"sha": parent["sha"], "url": parent["url"]} 
                        for parent in commit_data.get("parents", [])
                    ],
                    "author_info": commit_data["commit"]["author"],
                    "committer": commit_data["commit"]["committer"],
                    "stats": commit_data.get("stats", {"total": 0, "additions": 0, "deletions": 0}),
                    "files": [
                        {
                            "filename": file["filename"],
                            "status": file["status"],
                            "additions": file.get("additions", 0),
                            "deletions": file.get("deletions", 0),
                            "changes": file.get("changes", 0),
                            "blob_url": file.get("blob_url", ""),
                            "raw_url": file.get("raw_url", ""),
                            "contents_url": file.get("contents_url", ""),
                            "patch": file.get("patch", "")
                        }
                        for file in commit_data.get("files", [])
                    ]
                }
        except Exception as e:
            logger.error("Error fetching commit details", error=str(e), sha=sha)
        
        return None
    
    def _fetch_pull_requests(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch pull requests for the user in the specified time range"""
        pull_requests = []
        
        try:
            url = f"{self.base_url}/repos/{repo}/pulls"
            params = {
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": 100
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                pr_data = response.json()
                
                for pr in pr_data:
                    pr_created = datetime.fromisoformat(pr["created_at"].replace('Z', '+00:00'))
                    
                    # Filter by date range and author
                    if (start_date <= pr_created <= end_date and 
                        pr["user"]["login"] == username):
                        
                        # Transform to our format
                        pull_requests.append({
                            "id": f"pr-{pr['id']}",
                            "type": "pull_request",
                            "repository": repo,
                            "author": username,
                            "created_at": pr["created_at"],
                            "url": pr["url"],
                            "number": pr["number"],
                            "title": pr["title"],
                            "body": pr.get("body", ""),
                            "state": pr["state"],
                            "locked": pr.get("locked", False),
                            "user": {
                                "login": pr["user"]["login"],
                                "id": pr["user"]["id"],
                                "type": pr["user"]["type"]
                            },
                            "head": {
                                "label": pr["head"]["label"],
                                "ref": pr["head"]["ref"],
                                "sha": pr["head"]["sha"],
                                "repo": {
                                    "name": pr["head"]["repo"]["name"] if pr["head"]["repo"] else "",
                                    "full_name": pr["head"]["repo"]["full_name"] if pr["head"]["repo"] else ""
                                }
                            },
                            "base": {
                                "label": pr["base"]["label"],
                                "ref": pr["base"]["ref"],
                                "sha": pr["base"]["sha"],
                                "repo": {
                                    "name": pr["base"]["repo"]["name"],
                                    "full_name": pr["base"]["repo"]["full_name"]
                                }
                            },
                            "merged": pr.get("merged", False),
                            "comments": pr.get("comments", 0),
                            "review_comments": pr.get("review_comments", 0),
                            "commits": pr.get("commits", 0),
                            "additions": pr.get("additions", 0),
                            "deletions": pr.get("deletions", 0),
                            "changed_files": pr.get("changed_files", 0),
                            "comments_data": [],
                            "reviews_data": [],
                            "commits_data": [],
                            "files_data": []
                        })
        
        except Exception as e:
            logger.error("Error fetching pull requests", error=str(e), repo=repo, username=username)
        
        return pull_requests
    
    def _fetch_issues(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch issues for the user in the specified time range"""
        issues = []
        
        try:
            url = f"{self.base_url}/repos/{repo}/issues"
            params = {
                "creator": username,
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": 100
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                issue_data = response.json()
                
                for issue in issue_data:
                    # Skip pull requests (they appear in issues API)
                    if "pull_request" in issue:
                        continue
                    
                    issue_created = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
                    
                    # Filter by date range
                    if start_date <= issue_created <= end_date:
                        issues.append({
                            "id": f"issue-{issue['id']}",
                            "type": "issue",
                            "repository": repo,
                            "author": username,
                            "created_at": issue["created_at"],
                            "url": issue["url"],
                            "number": issue["number"],
                            "title": issue["title"],
                            "body": issue.get("body", ""),
                            "state": issue["state"],
                            "locked": issue.get("locked", False),
                            "user": {
                                "login": issue["user"]["login"],
                                "id": issue["user"]["id"],
                                "type": issue["user"]["type"]
                            },
                            "comments": issue.get("comments", 0),
                            "comments_data": [],
                            "events_data": []
                        })
        
        except Exception as e:
            logger.error("Error fetching issues", error=str(e), repo=repo, username=username)
        
        return issues
    
    def _fetch_releases(self, username: str, repo: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch releases for the user in the specified time range"""
        releases = []
        
        try:
            url = f"{self.base_url}/repos/{repo}/releases"
            params = {"per_page": 100}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                release_data = response.json()
                
                for release in release_data:
                    if not release.get("published_at"):
                        continue
                    
                    release_created = datetime.fromisoformat(release["published_at"].replace('Z', '+00:00'))
                    
                    # Filter by date range and author
                    if (start_date <= release_created <= end_date and 
                        release["author"]["login"] == username):
                        
                        releases.append({
                            "id": f"release-{release['id']}",
                            "type": "release",
                            "repository": repo,
                            "author": username,
                            "created_at": release["published_at"],
                            "url": release["url"],
                            "tag_name": release["tag_name"],
                            "target_commitish": release["target_commitish"],
                            "name": release["name"],
                            "body": release.get("body", ""),
                            "draft": release.get("draft", False),
                            "prerelease": release.get("prerelease", False),
                            "published_at": release.get("published_at"),
                            "author_info": {
                                "login": release["author"]["login"],
                                "id": release["author"]["id"],
                                "type": release["author"]["type"]
                            },
                            "assets": []
                        })
        
        except Exception as e:
            logger.error("Error fetching releases", error=str(e), repo=repo, username=username)
        
        return releases


class UserInputManager:
    """Manages user input collection with defaults and validation"""
    
    @staticmethod
    def get_user_parameters(args) -> tuple[str, str, str]:
        """Get user, repository, and week from args or prompt with defaults"""
        user = UserInputManager._get_username(args.user)
        repo = UserInputManager._get_repository(args.repo)
        week = UserInputManager._get_week(args.week)
        
        return user, repo, week
    
    @staticmethod
    def _get_username(provided_user: Optional[str]) -> str:
        """Get username from argument or prompt"""
        if provided_user:
            return provided_user
        
        user = input("Enter GitHub username: ").strip()
        if not user:
            print("❌ Username is required. Exiting.")
            sys.exit(1)
        return user
    
    @staticmethod
    def _get_repository(provided_repo: Optional[str]) -> str:
        """Get repository from argument or prompt"""
        if provided_repo:
            return provided_repo
        
        repo = input("Enter repository (format: owner/repo): ").strip()
        if not repo:
            print("❌ Repository is required. Exiting.")
            sys.exit(1)
        return repo
    
    @staticmethod
    def _get_week(provided_week: Optional[str]) -> str:
        """Get week from argument or prompt with current week default"""
        if provided_week:
            return provided_week
        
        current_week = DateTimeHelper.get_current_iso_week()
        week_input = input(f"Enter week (format: YYYY-WXX, default: {current_week}): ").strip()
        
        return week_input if week_input else current_week


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
    
    def ingest_contributions(self, user: str, week: str, contributions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest contributions using task-based approach with status polling"""
        payload = {
            "user": user,
            "week": week,
            "contributions": contributions
        }
        
        # Start the ingestion task
        task_response = self._start_ingestion_task(payload)
        task_id = task_response["task_id"]
        
        logger.info("Ingestion task started", 
                   task_id=task_id, 
                   user=user, 
                   week=week,
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
        max_retries = DEFAULT_TIMEOUT  # 60 seconds with 1-second intervals
        
        for attempt in range(max_retries):
            try:
                status_response = self.session.get(f"{self.base_url}/ingest/{task_id}")
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data["status"]
                
                if status == "completed":
                    logger.info("Ingestion task completed", 
                               task_id=task_id,
                               ingested_count=status_data["ingested_count"],
                               failed_count=status_data["failed_count"])
                    
                    # Return in the old format for backward compatibility
                    return self._format_completion_response(task_id, status_data)
                
                elif status == "failed":
                    error_msg = status_data.get("error_message", "Unknown error")
                    logger.error("Ingestion task failed", 
                                task_id=task_id, 
                                error_message=error_msg)
                    raise Exception(f"Ingestion failed: {error_msg}")
                
                elif status in ["queued", "processing"]:
                    logger.debug("Ingestion task in progress", 
                                task_id=task_id, 
                                status=status,
                                attempt=attempt + 1)
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
        raise Exception(f"Ingestion task {task_id} did not complete within {max_retries} seconds")
    
    def _format_completion_response(self, task_id: str, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the completion response for backward compatibility"""
        return {
            "task_id": task_id,
            "user": status_data["user"],
            "week": status_data["week"],
            "ingested_count": status_data["ingested_count"],
            "failed_count": status_data["failed_count"],
            "embedding_job_id": status_data.get("embedding_job_id"),
            "status": "completed",
            "processing_time_ms": status_data.get("processing_time_ms")
        }
    
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
                print(f"\n## {section_title}")
        
        elif chunk_type == "content":
            # Stream content as it comes
            print(content, end='', flush=True)
        
        elif chunk_type == "metadata" and chunk_data.get("metadata"):
            # Display metadata at the end
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
        
        self._fetch_and_process_contributions(user, repo, week)
        self._generate_summary(user, week)
        
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
    
    def _fetch_and_process_contributions(self, user: str, repo: str, week: str) -> None:
        """Fetch contributions from GitHub and ingest them into the GenAI service"""
        try:
            print(f"\n📥 Fetching contributions for {user} in {repo} for week {week}...")
            
            contributions = self.github_client.get_user_contributions(user, repo, week)
            ContributionSummaryPrinter.print_summary(contributions)
            
            if not contributions:
                print("No contributions to analyze. Exiting.")
                sys.exit(0)
            
            # Ingest contributions
            print("📤 Ingesting contributions into GenAI service...")
            ingest_result = self.prompteus_client.ingest_contributions(user, week, contributions)
            print(f"✅ Ingested {ingest_result['ingested_count']} contributions")
            
            # Wait for processing
            print("⏳ Processing contributions...")
            time.sleep(2)
            
        except Exception as e:
            logger.error("Failed to fetch and process contributions", error=str(e))
            print(f"❌ Failed to fetch and process contributions: {e}")
            sys.exit(1)
    
    def _generate_summary(self, user: str, week: str) -> None:
        """Generate and display the weekly summary"""
        print("\n📋 Generating comprehensive summary...")
        
        try:
            # Use streaming summary generation for live updates
            self.prompteus_client.generate_summary_stream(user, week)
            
        except Exception as e:
            logger.error("Failed to generate summary", error=str(e))
            print(f"⚠️  Could not generate summary: {e}")
            
            # Fallback to Q&A approach
            self._fallback_to_qa_summary(user, week)
        
        print("\n" + "=" * 50)
    
    def _fallback_to_qa_summary(self, user: str, week: str) -> None:
        """Fallback to Q&A approach when streaming summary fails"""
        print("🔄 Falling back to Q&A approach...")
        
        try:
            summary_question = (
                f"Please provide a comprehensive summary of {user}'s contributions this week, "
                f"including features implemented, bugs fixed, code changes, and overall impact."
            )
            
            summary_response = self.prompteus_client.ask_question(user, week, summary_question)
            
            print("\n📄 Weekly Contribution Summary (Q&A)")
            print("=" * 50)
            print(summary_response['answer'])
            print(f"\nConfidence: {summary_response['confidence']:.2f}")
            
            if summary_response.get('evidence'):
                print(f"\nBased on {len(summary_response['evidence'])} contribution(s)")
            
        except Exception as fallback_e:
            logger.error("Fallback Q&A also failed", error=str(fallback_e))
            print(f"❌ Both summary and Q&A approaches failed: {fallback_e}")
    
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