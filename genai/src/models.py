"""
Prompteus GenAI Service - Data Models

Pydantic models for API requests, responses, and internal data structures.
Models are organized by functional domain and follow GitHub API conventions.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Constants
DEFAULT_EVIDENCE_LIMIT = 10
DEFAULT_REASONING_DEPTH = "detailed"


class ContributionType(str, Enum):
    """Types of GitHub contributions supported by the system"""
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    RELEASE = "release"


class TaskStatus(str, Enum):
    """Status values for asynchronous tasks"""
    QUEUED = "queued"
    INGESTING = "ingesting"
    SUMMARIZING = "summarizing"
    DONE = "done"
    FAILED = "failed"


class DetailLevel(str, Enum):
    """Detail levels for summary generation"""
    BRIEF = "brief"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class ReasoningDepth(str, Enum):
    """Depth levels for question answering reasoning"""
    QUICK = "quick"
    DETAILED = "detailed"
    DEEP = "deep"


# === Core GitHub API Models ===

class GitHubUser(BaseModel):
    """GitHub user representation"""
    login: str
    id: int
    type: str = "User"


class GitHubLabel(BaseModel):
    """GitHub label representation"""
    id: int
    name: str
    color: str
    description: Optional[str] = None


class GitHubMilestone(BaseModel):
    """GitHub milestone representation"""
    id: int
    number: int
    title: str
    description: Optional[str] = None
    state: str = "open"
    due_on: Optional[datetime] = None


class GitHubReactions(BaseModel):
    """GitHub reactions representation"""
    total_count: int = 0
    plus_one: int = Field(default=0, alias="+1")
    minus_one: int = Field(default=0, alias="-1")
    laugh: int = 0
    hooray: int = 0
    confused: int = 0
    heart: int = 0
    rocket: int = 0
    eyes: int = 0

    model_config = ConfigDict(populate_by_name=True)


# === Commit-Specific Models ===

class CommitAuthor(BaseModel):
    """Commit author/committer information"""
    name: str
    email: str
    date: datetime


class CommitTree(BaseModel):
    """Commit tree reference"""
    sha: str
    url: str


class CommitParent(BaseModel):
    """Commit parent reference"""
    sha: str
    url: str


class CommitStats(BaseModel):
    """Commit statistics for additions/deletions"""
    total: int
    additions: int
    deletions: int


class CommitFile(BaseModel):
    """File changed in a commit"""
    sha: Optional[str] = None
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    contents_url: str
    patch: Optional[str] = None


class CommitContribution(BaseModel):
    """Commit contribution from GitHub API"""
    type: ContributionType = ContributionType.COMMIT
    id: str
    repository: str
    author: str
    created_at: datetime
    url: str

    # GitHub Commits API fields
    sha: str
    message: str
    tree: CommitTree
    parents: List[CommitParent]
    author_info: CommitAuthor
    committer: CommitAuthor
    stats: CommitStats
    files: List[CommitFile]

    model_config = ConfigDict(populate_by_name=True)


# === Pull Request Models ===

class PullRequestRef(BaseModel):
    """Pull request head/base reference"""
    label: str
    ref: str
    sha: str
    repo: Dict[str, str]


class PullRequestComment(BaseModel):
    """Pull request comment"""
    id: int
    user: GitHubUser
    created_at: datetime
    updated_at: datetime
    body: str
    reactions: GitHubReactions


class ReviewComment(BaseModel):
    """Pull request review comment"""
    id: int
    user: GitHubUser
    created_at: datetime
    body: str
    path: str
    position: Optional[int] = None
    original_position: Optional[int] = None
    commit_id: str
    original_commit_id: str
    diff_hunk: str
    reactions: GitHubReactions


class PullRequestReview(BaseModel):
    """Pull request review"""
    id: int
    user: GitHubUser
    body: Optional[str] = None
    state: str
    submitted_at: datetime
    commit_id: str
    comments: List[ReviewComment] = Field(default_factory=list)


class PullRequestCommit(BaseModel):
    """Commit within a pull request"""
    sha: str
    commit: Dict[str, Any]
    author: Optional[GitHubUser] = None


class PullRequestFile(BaseModel):
    """File changed in a pull request"""
    sha: Optional[str] = None
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    contents_url: str
    patch: Optional[str] = None


class PullRequestContribution(BaseModel):
    """Pull request contribution from GitHub API"""
    type: ContributionType = ContributionType.PULL_REQUEST
    id: str
    repository: str
    author: str
    created_at: datetime
    url: str

    # GitHub Pull Requests API fields
    number: int
    title: str
    body: Optional[str] = None
    state: str
    locked: bool = False
    user: GitHubUser
    assignee: Optional[GitHubUser] = None
    assignees: List[GitHubUser] = Field(default_factory=list)
    requested_reviewers: List[GitHubUser] = Field(default_factory=list)
    labels: List[GitHubLabel] = Field(default_factory=list)
    milestone: Optional[GitHubMilestone] = None
    head: PullRequestRef
    base: PullRequestRef
    merged: bool = False
    mergeable: Optional[bool] = None
    mergeable_state: Optional[str] = None
    merged_by: Optional[GitHubUser] = None
    comments: int = 0
    review_comments: int = 0
    commits: int = 0
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0

    # Extended data
    comments_data: List[PullRequestComment] = Field(default_factory=list)
    reviews_data: List[PullRequestReview] = Field(default_factory=list)
    commits_data: List[PullRequestCommit] = Field(default_factory=list)
    files_data: List[PullRequestFile] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


# === Issue Models ===

class IssueComment(BaseModel):
    """Issue comment"""
    id: int
    user: GitHubUser
    created_at: datetime
    updated_at: datetime
    body: str
    reactions: GitHubReactions


class IssueEvent(BaseModel):
    """Issue timeline event"""
    id: int
    event: str
    created_at: datetime
    actor: GitHubUser
    label: Optional[GitHubLabel] = None
    assignee: Optional[GitHubUser] = None
    commit_id: Optional[str] = None


class IssueContribution(BaseModel):
    """Issue contribution from GitHub API"""
    type: ContributionType = ContributionType.ISSUE
    id: str
    repository: str
    author: str
    created_at: datetime
    url: str

    # GitHub Issues API fields
    number: int
    title: str
    body: Optional[str] = None
    state: str
    locked: bool = False
    user: GitHubUser
    assignee: Optional[GitHubUser] = None
    assignees: List[GitHubUser] = Field(default_factory=list)
    labels: List[GitHubLabel] = Field(default_factory=list)
    milestone: Optional[GitHubMilestone] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[GitHubUser] = None
    comments: int = 0

    # Extended data
    comments_data: List[IssueComment] = Field(default_factory=list)
    events_data: List[IssueEvent] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


# === Release Models ===

class ReleaseAsset(BaseModel):
    """Release asset file"""
    id: int
    name: str
    label: Optional[str] = None
    uploader: GitHubUser
    content_type: str
    state: str
    size: int
    download_count: int
    created_at: datetime
    updated_at: datetime
    browser_download_url: str


class ReleaseContribution(BaseModel):
    """Release contribution from GitHub API"""
    type: ContributionType = ContributionType.RELEASE
    id: str
    repository: str
    author: str
    created_at: datetime
    url: str

    # GitHub Releases API fields
    tag_name: str
    target_commitish: str
    name: str
    body: Optional[str] = None
    draft: bool = False
    prerelease: bool = False
    published_at: Optional[datetime] = None
    author_info: GitHubUser

    # Extended data
    assets: List[ReleaseAsset] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


# === Union Type for All Contributions ===

GitHubContribution = Union[
    CommitContribution,
    PullRequestContribution,
    IssueContribution,
    ReleaseContribution
]


# === API Request/Response Models ===

class ContributionMetadata(BaseModel):
    """Metadata about a contribution to be fetched"""
    type: ContributionType
    id: str
    selected: bool  # Only fetch actual data if true

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        """Validate that ID is non-empty"""
        if not v or not v.strip():
            raise ValueError('ID cannot be empty')
        return v.strip()


class ContributionsIngestRequest(BaseModel):
    """Request to ingest contributions for a user's week (metadata only)"""
    user: str
    week: str  # ISO week format: 2024-W21
    repository: str  # Repository to fetch contributions from
    contributions: List[ContributionMetadata]

    @field_validator('week')
    @classmethod
    def validate_week_format(cls, v):
        """Validate ISO week format (YYYY-WXX)"""
        import re
        if not re.match(r'^\d{4}-W\d{2}$', v):
            raise ValueError('Week must be in ISO format: YYYY-WXX (e.g., 2024-W21)')
        return v

    @field_validator('repository')
    @classmethod
    def validate_repository_format(cls, v):
        """Validate repository format (owner/repo)"""
        if not v or '/' not in v:
            raise ValueError('Repository must be in format: owner/repo')
        return v


class IngestTaskResponse(BaseModel):
    """Response from starting a contributions ingestion task"""
    task_id: str  # UUIDv7 task identifier
    user: str
    week: str
    repository: str  # Repository being processed
    status: TaskStatus = TaskStatus.QUEUED
    total_contributions: int
    summary_id: Optional[str] = None  # UUIDv7 summary identifier for unified workflow
    created_at: datetime


class IngestTaskStatus(BaseModel):
    """Status of a contributions ingestion task"""
    task_id: str
    user: str
    week: str
    repository: str  # Repository being processed
    status: TaskStatus
    total_contributions: int
    ingested_count: int
    failed_count: int
    embedding_job_id: Optional[str] = None
    summary: Optional['SummaryResponse'] = None  # Only populated when status is DONE
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None


class ContributionsIngestResponse(BaseModel):
    """Legacy response from contributions ingestion (deprecated - use IngestTaskResponse)"""
    user: str
    week: str
    ingested_count: int
    failed_count: int
    embedding_job_id: str
    status: str = "processing"


class ContributionsStatusResponse(BaseModel):
    """Response for contributions status inquiry"""
    user: str
    week: str
    total_contributions: int
    embedded_contributions: int
    pending_embeddings: int
    last_updated: datetime
    meilisearch_status: str


# === Question Answering Models ===

class QuestionContext(BaseModel):
    """Context configuration for question answering"""
    focus_areas: List[str] = Field(default_factory=list)  # ["blockers", "progress", "achievements"]
    include_evidence: bool = True
    reasoning_depth: ReasoningDepth = ReasoningDepth.DETAILED
    max_evidence_items: int = DEFAULT_EVIDENCE_LIMIT


class QuestionRequest(BaseModel):
    """Request to ask a question about a user's week"""
    question: str
    context: QuestionContext = Field(default_factory=QuestionContext)


class QuestionEvidence(BaseModel):
    """Evidence supporting a question answer"""
    title: str
    contribution_id: str
    contribution_type: ContributionType
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    timestamp: datetime


class QuestionResponse(BaseModel):
    """Response to a question about a user's week"""
    question_id: str  # UUIDv7
    user: str
    week: str
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[QuestionEvidence] = Field(default_factory=list)
    reasoning_steps: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    asked_at: datetime
    response_time_ms: int
    # LangChain conversation session ID (user:week)
    conversation_id: Optional[str] = None


class SummaryRequest(BaseModel):
    """Request to generate a summary for a user's week"""
    user: str
    week: str  # ISO week format: 2024-W21
    include_code_changes: bool = True
    include_pr_reviews: bool = True
    include_issue_discussions: bool = True
    max_detail_level: DetailLevel = DetailLevel.COMPREHENSIVE


class SummaryChunk(BaseModel):
    """A chunk of the streaming summary response"""
    chunk_type: str  # "section" | "content" | "metadata" | "complete" | "error"
    section: Optional[str] = None  # "overview" | "commits" | "pull_requests" | "issues" | "releases" | "analysis"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class SummaryMetadata(BaseModel):
    """Metadata about a generated summary"""
    total_contributions: int
    commits_count: int
    pull_requests_count: int
    issues_count: int
    releases_count: int
    repositories: List[str]
    time_period: str
    generated_at: datetime
    processing_time_ms: int


class SummaryResponse(BaseModel):
    """Complete summary response (non-streaming)"""
    summary_id: str  # UUIDv7
    user: str
    week: str
    overview: str
    commits_summary: str
    pull_requests_summary: str
    issues_summary: str
    releases_summary: str
    analysis: str
    key_achievements: List[str]
    areas_for_improvement: List[str]
    metadata: SummaryMetadata
    generated_at: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime


def generate_uuidv7() -> str:
    """Generate a UUIDv7-like (time-ordered UUID) for consistent sorting"""
    # uuid7 is only available in Python 3.12+, use uuid4 as fallback
    try:
        return str(uuid.uuid7())  # type: ignore[attr-defined]
    except AttributeError:
        # Fallback to uuid4 for older Python versions
        return str(uuid.uuid4())


