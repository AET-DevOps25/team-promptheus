import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.services import SummaryService, ContributionsIngestionService
from src.models import (
    SummaryRequest, SummaryResponse, SummaryMetadata, generate_uuidv7
)
from tests.test_data import (
    get_test_commit_contribution, get_test_pull_request_contribution,
    get_test_issue_contribution, get_test_release_contribution
)

# TODO: Evaluate this idea: embed both the release summary and an expected string, and check if they are meaningfully similar

class TestSummaryService:
    """Test the SummaryService class"""
    
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
        """Create sample contributions for testing"""
        return [
            get_test_commit_contribution(),
            get_test_pull_request_contribution(),
            get_test_issue_contribution()
        ]
    
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
        """Test generating a summary with contributions"""
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
        assert len(result.commits_summary) > 0
        assert len(result.pull_requests_summary) > 0
        assert len(result.issues_summary) > 0
        assert result.releases_summary == "No releases published this week."
        assert len(result.analysis) > 0
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
        assert len(result.areas_for_improvement) > 0  # Should have suggestions
        
        # Verify metadata
        assert result.metadata.total_contributions == 0
        assert result.metadata.commits_count == 0
        assert result.metadata.pull_requests_count == 0
        assert result.metadata.issues_count == 0
        assert result.metadata.releases_count == 0
    
    @pytest.mark.asyncio
    async def test_generate_summary_stream_with_contributions(self, summary_service, mock_ingestion_service, 
                                                             sample_contributions, summary_request):
        """Test streaming summary generation with contributions"""
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
        
        # Verify section chunks exist
        section_chunks = [chunk for chunk in chunks if chunk.chunk_type == "section"]
        assert len(section_chunks) > 0
        
        # Verify content chunks exist
        content_chunks = [chunk for chunk in chunks if chunk.chunk_type == "content"]
        assert len(content_chunks) > 0
    
    @pytest.mark.asyncio
    async def test_generate_summary_stream_no_contributions(self, summary_service, mock_ingestion_service, summary_request):
        """Test streaming summary generation when no contributions exist"""
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
        """Test metadata generation"""
        start_time = datetime.now(timezone.utc)
        metadata = summary_service._generate_metadata(sample_contributions, "2024-W21", start_time)
        
        assert isinstance(metadata, SummaryMetadata)
        assert metadata.total_contributions == 3
        assert metadata.commits_count == 1
        assert metadata.pull_requests_count == 1
        assert metadata.issues_count == 1
        assert metadata.releases_count == 0
        assert metadata.time_period == "2024-W21"
        assert len(metadata.repositories) > 0
        assert metadata.processing_time_ms == 0  # Not set yet
    
    @pytest.mark.asyncio
    async def test_generate_overview(self, summary_service, sample_contributions, summary_request):
        """Test overview generation"""
        overview = await summary_service._generate_overview(sample_contributions, summary_request)
        
        assert isinstance(overview, str)
        assert len(overview) > 0
        # Check for content that indicates meaningful contribution activity
        # The AI should mention some combination of contributions/activity/development work
        overview_lower = overview.lower()
        
        # Should mention contributions or development activity
        assert any(word in overview_lower for word in ["contribution", "development", "work", "activity", "project"])
        
        # Should mention repository/repo context
        assert any(word in overview_lower for word in ["repositor", "repo", "project"])
        
        # Should mention types of contributions made (at least one of these)
        contribution_types = ["commit", "pull request", "pr", "issue", "bug", "feature", "fix"]
        assert any(word in overview_lower for word in contribution_types)
    
    @pytest.mark.asyncio
    async def test_generate_commits_summary(self, summary_service, sample_contributions, summary_request):
        """Test commits summary generation"""
        summary = await summary_service._generate_commits_summary(sample_contributions, summary_request)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        # Check for content that indicates commit activity rather than exact phrase
        assert ("1" in summary and "commit" in summary.lower()) or "commit" in summary.lower() or "bug" in summary.lower() or "fix" in summary.lower()
    
    @pytest.mark.asyncio
    async def test_generate_commits_summary_no_commits(self, summary_service, summary_request):
        """Test commits summary when no commits exist"""
        # Create contributions without commits
        contributions = [get_test_issue_contribution()]
        
        summary = await summary_service._generate_commits_summary(contributions, summary_request)
        
        assert summary == "No commits made this week."
    
    @pytest.mark.asyncio
    async def test_generate_analysis(self, summary_service, sample_contributions, summary_request):
        """Test analysis generation"""
        analysis = await summary_service._generate_analysis(sample_contributions, summary_request)
        
        assert isinstance(analysis, str)
        assert len(analysis) > 0
        # Check for content that indicates analysis rather than exact phrase
        assert ("insight" in analysis.lower() or "analysis" in analysis.lower() or "development" in analysis.lower() or "contribution" in analysis.lower())
        assert "activity" in analysis.lower()
    
    @pytest.mark.asyncio
    async def test_generate_key_achievements(self, summary_service, sample_contributions):
        """Test key achievements generation"""
        achievements = await summary_service._generate_key_achievements(sample_contributions)
        
        assert isinstance(achievements, list)
        assert len(achievements) > 0
        
        # Should mention commits and other contributions
        achievements_text = " ".join(achievements)
        assert ("commit" in achievements_text.lower() or "bug" in achievements_text.lower() or "fix" in achievements_text.lower() or "contribution" in achievements_text.lower())
    
    @pytest.mark.asyncio
    async def test_generate_improvement_areas(self, summary_service, sample_contributions):
        """Test improvement areas generation"""
        improvements = await summary_service._generate_improvement_areas(sample_contributions)
        
        assert isinstance(improvements, list)
        # May or may not have suggestions depending on the contribution patterns
    
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
            analysis="Test analysis",
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
        """Test summary generation with releases"""
        # Create contributions including a release
        contributions = [
            get_test_commit_contribution(),
            get_test_release_contribution()
        ]
        
        mock_ingestion_service.get_user_week_contributions.return_value = contributions
        
        result = await summary_service.generate_summary("testuser", "2024-W21", summary_request)
        
        # Verify releases are included
        assert result.metadata.releases_count == 1
        # Check for content that indicates 1 release rather than exact phrase
        assert ("1" in result.releases_summary and "release" in result.releases_summary.lower()) or "version" in result.releases_summary.lower() or "released" in result.releases_summary.lower()
        assert "No releases published" not in result.releases_summary
    
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