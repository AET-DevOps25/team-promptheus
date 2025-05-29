"""
Tests for Question Answering service functionality
"""
import pytest
import pytest_asyncio
from src.services import QuestionAnsweringService, ContributionsIngestionService
from src.models import QuestionRequest, QuestionContext, QuestionResponse
from src.meilisearch import MeilisearchService


@pytest.mark.asyncio
class TestQuestionAnsweringService:
    """Test Question Answering service functionality"""
    
    @pytest_asyncio.fixture
    async def qa_service(self):
        """Create a QA service for testing"""
        meilisearch_service = MeilisearchService()
        await meilisearch_service.initialize()
        
        ingestion_service = ContributionsIngestionService(meilisearch_service)
        qa_service = QuestionAnsweringService(ingestion_service)
        
        return qa_service
    
    async def test_question_context_validation(self):
        """Test QuestionContext model validation"""
        # Test valid context
        context = QuestionContext(
            focus_areas=["features", "bugs", "performance"],
            include_evidence=True,
            reasoning_depth="detailed",
            max_evidence_items=5
        )
        
        assert context.focus_areas == ["features", "bugs", "performance"]
        assert context.include_evidence is True
        assert context.reasoning_depth == "detailed"
        assert context.max_evidence_items == 5
        
    async def test_question_request_validation(self):
        """Test QuestionRequest model validation"""
        request = QuestionRequest(
            question="What commits were programmed?",
            context=QuestionContext(
                focus_areas=["features", "bugs", "performance"],
                include_evidence=True,
                reasoning_depth="detailed",
                max_evidence_items=5
            )
        )
        
        assert request.question == "What commits were programmed?"
        assert request.context.focus_areas == ["features", "bugs", "performance"]
        assert request.context.max_evidence_items == 5
        
    async def test_question_request_serialization(self):
        """Test QuestionRequest JSON serialization"""
        request = QuestionRequest(
            question="What commits were programmed?",
            context=QuestionContext(
                focus_areas=["features", "bugs", "performance"],
                include_evidence=True,
                reasoning_depth="detailed"
            )
        )
        
        # Test JSON serialization
        json_data = request.model_dump()
        assert "question" in json_data
        assert "context" in json_data
        assert json_data["question"] == "What commits were programmed?"
        assert json_data["context"]["focus_areas"] == ["features", "bugs", "performance"]
        
    async def test_retrieve_relevant_contributions_empty(self, qa_service):
        """Test retrieving contributions when none exist"""
        request = QuestionRequest(
            question="What was done?",
            context=QuestionContext(max_evidence_items=5)
        )
        
        contributions = await qa_service._retrieve_relevant_contributions(
            user="nonexistent_user",
            week="2024-W99",
            request=request
        )
        
        assert isinstance(contributions, list)
        assert len(contributions) == 0
        
    async def test_generate_agentic_answer_no_contributions(self, qa_service):
        """Test generating answer when no contributions are found"""
        request = QuestionRequest(
            question="What was done?",
            context=QuestionContext()
        )
        
        answer_data = await qa_service._generate_agentic_answer(
            user="testuser",
            week="2024-W21",
            request=request,
            contributions=[]
        )
        
        assert isinstance(answer_data, dict)
        assert "answer" in answer_data
        assert "confidence" in answer_data
        assert "evidence" in answer_data
        assert "reasoning_steps" in answer_data
        assert "suggested_actions" in answer_data
        
        # Should have low confidence when no contributions
        assert answer_data["confidence"] <= 0.2
        assert len(answer_data["evidence"]) == 0
        
    async def test_full_question_answering_flow(self, qa_service):
        """Test the complete question answering flow"""
        request = QuestionRequest(
            question="What commits were programmed?",
            context=QuestionContext(
                focus_areas=["features", "bugs", "performance"],
                include_evidence=True,
                reasoning_depth="detailed",
                max_evidence_items=5
            )
        )
        
        # This should not raise "Incorrect label names" error anymore
        response = await qa_service.answer_question(
            user="testuser",
            week="2024-W21",
            request=request
        )
        
        assert isinstance(response, QuestionResponse)
        assert response.user == "testuser"
        assert response.week == "2024-W21"
        assert response.question == "What commits were programmed?"
        assert isinstance(response.answer, str)
        assert 0.0 <= response.confidence <= 1.0
        assert isinstance(response.evidence, list)
        assert isinstance(response.reasoning_steps, list)
        assert isinstance(response.suggested_actions, list)
        assert isinstance(response.response_time_ms, int)
        assert response.response_time_ms > 0
        
    async def test_question_storage_and_retrieval(self, qa_service):
        """Test that questions are stored and can be retrieved"""
        request = QuestionRequest(
            question="Test question",
            context=QuestionContext()
        )
        
        # Ask a question
        response = await qa_service.answer_question(
            user="testuser",
            week="2024-W21",
            request=request
        )
        
        question_id = response.question_id
        
        # Retrieve the question
        retrieved = qa_service.get_question(question_id)
        
        assert retrieved is not None
        assert retrieved.question_id == question_id
        assert retrieved.question == "Test question"
        assert retrieved.user == "testuser"
        assert retrieved.week == "2024-W21"
        
    async def test_question_not_found(self, qa_service):
        """Test retrieving a non-existent question"""
        fake_id = "non-existent-id"
        result = qa_service.get_question(fake_id)
        assert result is None 