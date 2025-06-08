import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.services import SummaryService, ContributionsIngestionService
from src.models import (
    SummaryRequest, SummaryResponse, SummaryMetadata, generate_uuidv7,
    CommitContribution, PullRequestContribution, IssueContribution, ReleaseContribution,
    ContributionType, CommitAuthor, CommitTree, CommitStats, GitHubUser, PullRequestRef
)


class TestSummaryService:
    """Test the SummaryService class with strongly-typed contributions"""
    
    @pytest.fixture
    def mock_ingestion_service(self):
        """Create a mock ingestion service"""
        service = MagicMock(spec=ContributionsIngestionService)
        service.get_user_week_contributions = MagicMock()
        return service
    
    @pytest.fixture
    def summary_service(self, mock_ingestion_service):
        """Create a SummaryService instance with mocked dependencies"""
        return SummaryService(mock_ingestion_service)
    
    @pytest.fixture
    def sample_contributions(self):
        """Create sample strongly-typed contributions for testing"""
        commit = CommitContribution(
            id="commit-123",
            repository="test/repo",
            author="testuser",
            created_at=datetime.now(timezone.utc),
            url="https://api.github.com/repos/test/repo/commits/commit-123",
            sha="commit-123",
            message="Fix authentication bug",
            tree=CommitTree(
                sha="tree123",
                url="https://api.github.com/repos/test/repo/git/trees/tree123"
            ),
            parents=[],
            author_info=CommitAuthor(
                name="Test User",
                email="testuser@example.com",
                date=datetime.now(timezone.utc)
            ),
            committer=CommitAuthor(
                name="Test User",
                email="testuser@example.com",
                date=datetime.now(timezone.utc)
            ),
            stats=CommitStats(
                total=15,
                additions=10,
                deletions=5
            ),
            files=[]
        )
        
        pr = PullRequestContribution(
            id="pr-42",
            repository="test/repo",
            author="testuser",
            created_at=datetime.now(timezone.utc),
            url="https://api.github.com/repos/test/repo/pulls/42",
            number=42,
            title="Add user management feature",
            body="This PR adds comprehensive user management functionality",
            state="open",
            locked=False,
            user=GitHubUser(login="testuser", id=12345, type="User"),
            head=PullRequestRef(
                label="testuser:feature-branch",
                ref="feature-branch",
                sha="def456ghi789",
                repo={"name": "repo", "full_name": "test/repo"}
            ),
            base=PullRequestRef(
                label="test:main",
                ref="main",
                sha="ghi789jkl012",
                repo={"name": "repo", "full_name": "test/repo"}
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
            files_data=[]
        )
        
        issue = IssueContribution(
            id="issue-15",
            repository="test/repo",
            author="testuser",
            created_at=datetime.now(timezone.utc),
            url="https://api.github.com/repos/test/repo/issues/15",
            number=15,
            title="Performance optimization needed",
            body="The application is running slowly with large datasets",
            state="open",
            locked=False,
            user=GitHubUser(login="testuser", id=12345, type="User"),
            comments=0,
            comments_data=[],
            events_data=[]
        )
        
        return [commit, pr, issue]
    
    @pytest.fixture
    def summary_request(self):
        """Create a sample summary request"""
        return SummaryRequest(
            user="testuser",
            week="2024-W21",
            include_code_changes=True,
            include_pr_reviews=True,
            include_issue_discussions=True,
            max_detail_level="comprehensive"
        )
    
    @pytest.mark.asyncio
    async def test_generate_summary_with_contributions(self, summary_service, mock_ingestion_service, 
                                                      sample_contributions, summary_request):
        """Test generating a weekly progress report with contributions"""
        # Setup mock
        mock_ingestion_service.get_user_week_contributions.return_value = sample_contributions
        
        # Generate summary
        result = await summary_service.generate_summary("testuser", "2024-W21", summary_request)
        
        # Verify result structure
        assert isinstance(result, SummaryResponse)
        assert result.user == "testuser"
        assert result.week == "2024-W21"
        assert result.summary_id is not None
        assert len(result.overview) > 0
        assert result.commits_summary == "Completed 1 commits"
        assert result.pull_requests_summary == "Worked on 1 pull requests"
        assert result.issues_summary == "Addressed 1 issues"
        assert result.releases_summary == "No releases this week"
        assert result.analysis == "Weekly progress report generated"
        assert len(result.key_achievements) > 0
        assert len(result.areas_for_improvement) >= 0
        
        # Verify metadata
        assert result.metadata.total_contributions == 3
        assert result.metadata.commits_count == 1
        assert result.metadata.pull_requests_count == 1
        assert result.metadata.issues_count == 1
        assert result.metadata.releases_count == 0
        assert result.metadata.time_period == "2024-W21"
        assert result.metadata.processing_time_ms > 0
        
        # Verify the summary is stored
        assert summary_service.get_summary(result.summary_id) == result
    
    @pytest.mark.asyncio
    async def test_generate_summary_no_contributions(self, summary_service, mock_ingestion_service, summary_request):
        """Test generating a summary when no contributions exist"""
        # Setup mock to return empty list
        mock_ingestion_service.get_user_week_contributions.return_value = []
        
        # Generate summary
        result = await summary_service.generate_summary("testuser", "2024-W21", summary_request)
        
        # Verify empty summary structure
        assert isinstance(result, SummaryResponse)
        assert result.user == "testuser"
        assert result.week == "2024-W21"
        assert "No contributions found" in result.overview
        assert result.commits_summary == "No commits made this week."
        assert result.pull_requests_summary == "No pull requests created this week."
        assert result.issues_summary == "No issues created this week."
        assert result.releases_summary == "No releases published this week."
        assert result.analysis == "No activity to analyze for this week."
        assert len(result.key_achievements) == 0
        assert "No remaining tasks assigned" in result.areas_for_improvement
        
        # Verify metadata
        assert result.metadata.total_contributions == 0
        assert result.metadata.commits_count == 0
        assert result.metadata.pull_requests_count == 0
        assert result.metadata.issues_count == 0
        assert result.metadata.releases_count == 0
    
    @pytest.mark.asyncio
    async def test_generate_summary_stream_with_contributions(self, summary_service, mock_ingestion_service, 
                                                             sample_contributions, summary_request):
        """Test streaming weekly progress report generation"""
        # Setup mock
        mock_ingestion_service.get_user_week_contributions.return_value = sample_contributions
        
        # Generate streaming summary
        chunks = []
        async for chunk in summary_service.generate_summary_stream("testuser", "2024-W21", summary_request):
            chunks.append(chunk)
        
        # Verify we got chunks
        assert len(chunks) > 0
        
        # Check chunk types
        chunk_types = [chunk.chunk_type for chunk in chunks]
        assert "metadata" in chunk_types
        assert "section" in chunk_types
        assert "content" in chunk_types
        assert "complete" in chunk_types
        
        # Find and verify metadata chunk
        metadata_chunk = next((chunk for chunk in chunks if chunk.chunk_type == "metadata"), None)
        assert metadata_chunk is not None
        assert metadata_chunk.metadata is not None
        assert metadata_chunk.metadata["total_contributions"] == 3
        
        # Find and verify completion chunk
        complete_chunk = next((chunk for chunk in chunks if chunk.chunk_type == "complete"), None)
        assert complete_chunk is not None
        assert "summary_id" in complete_chunk.metadata
        assert "processing_time_ms" in complete_chunk.metadata
        assert complete_chunk.metadata["total_contributions"] == 3
        assert complete_chunk.metadata["status"] == "success"
        
        # Verify progress report sections exist
        section_chunks = [chunk for chunk in chunks if chunk.chunk_type == "section"]
        assert len(section_chunks) > 0
        
        # Verify content chunks exist  
        content_chunks = [chunk for chunk in chunks if chunk.chunk_type == "content"]
        assert len(content_chunks) > 0
        
        # Look for specific progress report sections
        content_text = " ".join([chunk.content for chunk in content_chunks])
        assert "Summary" in content_text or "Accomplishments" in content_text
    
    @pytest.mark.asyncio
    async def test_generate_summary_stream_no_contributions(self, summary_service, mock_ingestion_service, summary_request):
        """Test streaming progress report when no contributions exist"""
        # Setup mock to return empty list
        mock_ingestion_service.get_user_week_contributions.return_value = []
        
        # Generate streaming summary
        chunks = []
        async for chunk in summary_service.generate_summary_stream("testuser", "2024-W21", summary_request):
            chunks.append(chunk)
        
        # Verify we got chunks
        assert len(chunks) >= 2  # At least content and complete
        
        # Find content chunk
        content_chunk = next((chunk for chunk in chunks if chunk.chunk_type == "content"), None)
        assert content_chunk is not None
        assert "No contributions found" in content_chunk.content
        
        # Find completion chunk
        complete_chunk = next((chunk for chunk in chunks if chunk.chunk_type == "complete"), None)
        assert complete_chunk is not None
        assert complete_chunk.metadata["total_contributions"] == 0
    
    def test_generate_metadata(self, summary_service, sample_contributions):
        """Test metadata generation with strongly-typed contributions"""
        start_time = datetime.now(timezone.utc)
        metadata = summary_service._generate_metadata(sample_contributions, "2024-W21", start_time, 100)
        
        assert isinstance(metadata, SummaryMetadata)
        assert metadata.total_contributions == 3
        assert metadata.commits_count == 1
        assert metadata.pull_requests_count == 1
        assert metadata.issues_count == 1
        assert metadata.releases_count == 0
        assert metadata.time_period == "2024-W21"
        assert len(metadata.repositories) == 1
        assert "test/repo" in metadata.repositories
        assert metadata.processing_time_ms == 100
    
    def test_format_contributions_for_prompt(self, summary_service, sample_contributions):
        """Test formatting strongly-typed contributions for AI prompt"""
        formatted = summary_service._format_contributions_for_prompt(sample_contributions)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "COMMIT in test/repo: Fix authentication bug" in formatted
        assert "PULL REQUEST in test/repo: Add user management feature (open)" in formatted
        assert "ISSUE in test/repo: Performance optimization needed (open)" in formatted
    
    @pytest.mark.asyncio
    async def test_progress_report_structure(self, summary_service, mock_ingestion_service, sample_contributions, summary_request):
        """Test that the progress report has the expected structure"""
        # Setup mock
        mock_ingestion_service.get_user_week_contributions.return_value = sample_contributions
        
        # Generate progress report
        progress_report = await summary_service._generate_progress_report("testuser", "2024-W21", sample_contributions, summary_request)
        
        # Verify structure
        assert hasattr(progress_report, 'summary')
        assert hasattr(progress_report, 'key_accomplishments')
        assert hasattr(progress_report, 'impediments')
        assert hasattr(progress_report, 'next_steps')
        
        assert isinstance(progress_report.summary, str)
        assert isinstance(progress_report.key_accomplishments, list)
        assert isinstance(progress_report.impediments, list)
        assert isinstance(progress_report.next_steps, list)
        
        assert len(progress_report.summary) > 0
    
    def test_get_summary_exists(self, summary_service):
        """Test retrieving an existing summary"""
        # Create a mock summary
        summary_id = generate_uuidv7()
        mock_summary = SummaryResponse(
            summary_id=summary_id,
            user="testuser",
            week="2024-W21",
            overview="Test overview",
            commits_summary="Test commits",
            pull_requests_summary="Test PRs",
            issues_summary="Test issues",
            releases_summary="Test releases",
            analysis="Weekly progress report generated",
            key_achievements=["Achievement 1"],
            areas_for_improvement=["Improvement 1"],
            metadata=SummaryMetadata(
                total_contributions=1,
                commits_count=1,
                pull_requests_count=0,
                issues_count=0,
                releases_count=0,
                repositories=["test/repo"],
                time_period="2024-W21",
                generated_at=datetime.now(timezone.utc),
                processing_time_ms=100
            ),
            generated_at=datetime.now(timezone.utc)
        )
        
        # Store the summary
        summary_service.summaries_store[summary_id] = mock_summary
        
        # Retrieve it
        result = summary_service.get_summary(summary_id)
        assert result == mock_summary
    
    def test_get_summary_not_exists(self, summary_service):
        """Test retrieving a non-existent summary"""
        fake_id = generate_uuidv7()
        result = summary_service.get_summary(fake_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_summary_with_releases(self, summary_service, mock_ingestion_service, summary_request):
        """Test progress report generation with releases"""
        # Create contributions including a release
        release = ReleaseContribution(
            id="release-101",
            repository="test/repo",
            author="testuser",
            created_at=datetime.now(timezone.utc),
            url="https://api.github.com/repos/test/repo/releases/101",
            tag_name="v1.2.0",
            target_commitish="main",
            name="Version 1.2.0",
            body="## What's New\n- Added user management\n- Fixed authentication bugs",
            draft=False,
            prerelease=False,
            published_at=datetime.now(timezone.utc),
            author_info=GitHubUser(login="testuser", id=12345, type="User"),
            assets=[]
        )
        
        contributions = [release]
        mock_ingestion_service.get_user_week_contributions.return_value = contributions
        
        result = await summary_service.generate_summary("testuser", "2024-W21", summary_request)
        
        # Verify releases are included
        assert result.metadata.releases_count == 1
        assert result.releases_summary == "Published 1 releases"
    
    @pytest.mark.asyncio
    async def test_summary_error_handling(self, summary_service, mock_ingestion_service, summary_request):
        """Test error handling in summary generation"""
        # Setup mock to raise an exception
        mock_ingestion_service.get_user_week_contributions.side_effect = Exception("Test error")
        
        # Should propagate the exception
        with pytest.raises(Exception, match="Test error"):
            await summary_service.generate_summary("testuser", "2024-W21", summary_request)
    
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, summary_service, mock_ingestion_service, summary_request):
        """Test error handling in streaming summary generation"""
        # Setup mock to raise an exception
        mock_ingestion_service.get_user_week_contributions.side_effect = Exception("Test error")
        
        # Should yield an error chunk
        chunks = []
        async for chunk in summary_service.generate_summary_stream("testuser", "2024-W21", summary_request):
            chunks.append(chunk)
        
        # Should have at least one error chunk
        error_chunks = [chunk for chunk in chunks if chunk.chunk_type == "error"]
        assert len(error_chunks) > 0
        assert "Test error" in error_chunks[0].content
        assert error_chunks[0].metadata["status"] == "error" 