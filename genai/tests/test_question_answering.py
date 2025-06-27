"""Tests for Question Answering service functionality."""

import pytest
import pytest_asyncio

from src.meilisearch import MeilisearchService
from src.models import QuestionContext, QuestionRequest, QuestionResponse
from src.services import ContributionsIngestionService, QuestionAnsweringService


@pytest.mark.asyncio
class TestQuestionAnsweringService:
    """Test Question Answering service functionality."""

    @pytest_asyncio.fixture
    async def qa_service(self) -> QuestionAnsweringService:
        """Create a QA service for testing."""
        meilisearch_service = MeilisearchService()
        await meilisearch_service.initialize()

        ingestion_service = ContributionsIngestionService(meilisearch_service)
        return QuestionAnsweringService(ingestion_service)


    async def test_question_context_validation(self) -> None:
        """Test QuestionContext model validation."""
        # Test valid context
        context = QuestionContext(
            focus_areas=["features", "bugs", "performance"],
            include_evidence=True,
            reasoning_depth="detailed",
            max_evidence_items=5,
        )

        assert context.focus_areas == ["features", "bugs", "performance"]
        assert context.include_evidence is True
        assert context.reasoning_depth == "detailed"
        assert context.max_evidence_items == 5

    async def test_question_request_validation(self) -> None:
        """Test QuestionRequest model validation."""
        request = QuestionRequest(
            question="What commits were programmed?",
            context=QuestionContext(
                focus_areas=["features", "bugs", "performance"],
                include_evidence=True,
                reasoning_depth="detailed",
                max_evidence_items=5,
            ),
        )

        assert request.question == "What commits were programmed?"
        assert request.context.focus_areas == ["features", "bugs", "performance"]
        assert request.context.max_evidence_items == 5

    async def test_question_request_serialization(self) -> None:
        """Test QuestionRequest JSON serialization."""
        request = QuestionRequest(
            question="What commits were programmed?",
            context=QuestionContext(
                focus_areas=["features", "bugs", "performance"],
                include_evidence=True,
                reasoning_depth="detailed",
            ),
        )

        # Test JSON serialization
        json_data = request.model_dump()
        assert "question" in json_data
        assert "context" in json_data
        assert json_data["question"] == "What commits were programmed?"
        assert json_data["context"]["focus_areas"] == [
            "features",
            "bugs",
            "performance",
        ]

    async def test_retrieve_relevant_contributions_empty(self, qa_service) -> None:
        """Test retrieving contributions when none exist."""
        request = QuestionRequest(question="What was done?", context=QuestionContext(max_evidence_items=5))

        contributions = await qa_service._retrieve_relevant_contributions(
            user="nonexistent_user", week="2024-W99", request=request
        )

        assert isinstance(contributions, list)
        assert len(contributions) == 0

    async def test_answer_question_no_contributions(self, qa_service) -> None:
        """Test answering question when no contributions are found."""
        request = QuestionRequest(question="What was done?", context=QuestionContext())

        # Test with a user/week that has no contributions
        response = await qa_service.answer_question(user="nonexistent_user", week="2024-W99", request=request)

        assert isinstance(response, QuestionResponse)
        assert response.user == "nonexistent_user"
        assert response.week == "2024-W99"
        assert response.question == "What was done?"
        assert isinstance(response.answer, str)
        assert isinstance(response.confidence, float)
        assert isinstance(response.evidence, list)
        assert isinstance(response.reasoning_steps, list)
        assert isinstance(response.suggested_actions, list)

        # Should have no evidence when no contributions
        assert len(response.evidence) == 0
        # AI can be confident about stating there are no contributions
        assert 0.0 <= response.confidence <= 1.0

    async def test_full_question_answering_flow(self, qa_service) -> None:
        """Test the complete question answering flow."""
        request = QuestionRequest(
            question="What commits were programmed?",
            context=QuestionContext(
                focus_areas=["features", "bugs", "performance"],
                include_evidence=True,
                reasoning_depth="detailed",
                max_evidence_items=5,
            ),
        )

        # This should not raise "Incorrect label names" error anymore
        response = await qa_service.answer_question(user="testuser", week="2024-W21", request=request)

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

    async def test_question_storage_and_retrieval(self, qa_service) -> None:
        """Test that questions are stored and can be retrieved."""
        request = QuestionRequest(question="Test question", context=QuestionContext())

        # Ask a question
        response = await qa_service.answer_question(user="testuser", week="2024-W21", request=request)

        question_id = response.question_id

        # Retrieve the question
        retrieved = qa_service.get_question(question_id)

        assert retrieved is not None
        assert retrieved.question_id == question_id
        assert retrieved.question == "Test question"
        assert retrieved.user == "testuser"
        assert retrieved.week == "2024-W21"

    async def test_question_not_found(self, qa_service) -> None:
        """Test retrieving a non-existent question."""
        fake_id = "non-existent-id"
        result = qa_service.get_question(fake_id)
        assert result is None

    @pytest.mark.skip(reason="Conversation history persistence is being refactored")
    async def test_conversation_context_functionality(self, qa_service) -> None:
        """Test LangChain conversation context features."""
        user = "testuser"
        week = "2024-W21"

        # First question
        request1 = QuestionRequest(question="What commits were made?", context=QuestionContext())

        response1 = await qa_service.answer_question(user, week, request1)
        conversation_id = response1.conversation_id

        # Verify conversation ID format (should be user:week)
        assert conversation_id == f"{user}:{week}"

        # Second question in same conversation
        request2 = QuestionRequest(question="Tell me more about those commits", context=QuestionContext())

        response2 = await qa_service.answer_question(user, week, request2)

        # Should have same conversation ID
        assert response2.conversation_id == conversation_id

        # Verify conversation history exists
        history = qa_service.get_conversation_history(user, week)
        assert len(history) >= 2  # At least 2 messages (human + AI from first question)

    @pytest.mark.skip(reason="Conversation history persistence is being refactored")
    async def test_conversation_history_management(self, qa_service) -> None:
        """Test conversation history retrieval and clearing."""
        user = "testuser2"
        week = "2024-W22"

        # Initially no history
        history = qa_service.get_conversation_history(user, week)
        assert len(history) == 0

        # Ask a question to create history
        request = QuestionRequest(question="What was done?", context=QuestionContext())

        await qa_service.answer_question(user, week, request)

        # Should now have history
        history = qa_service.get_conversation_history(user, week)
        assert len(history) > 0

        # Clear history
        qa_service.clear_conversation_history(user, week)

        # Should be empty again
        history = qa_service.get_conversation_history(user, week)
        assert len(history) == 0

    @pytest.mark.skip(reason="Conversation history persistence is being refactored")
    async def test_separate_conversation_sessions(self, qa_service) -> None:
        """Test that different user/week combinations have separate conversations."""
        # Ask questions for different user/week combinations
        request = QuestionRequest(question="What was done?", context=QuestionContext())

        response1 = await qa_service.answer_question("user1", "2024-W21", request)
        response2 = await qa_service.answer_question("user2", "2024-W21", request)
        response3 = await qa_service.answer_question("user1", "2024-W22", request)

        # Should have different conversation IDs
        assert response1.conversation_id == "user1:2024-W21"
        assert response2.conversation_id == "user2:2024-W21"
        assert response3.conversation_id == "user1:2024-W22"

        # Each should have separate history
        history1 = qa_service.get_conversation_history("user1", "2024-W21")
        history2 = qa_service.get_conversation_history("user2", "2024-W21")
        history3 = qa_service.get_conversation_history("user1", "2024-W22")

        assert len(history1) > 0
        assert len(history2) > 0
        assert len(history3) > 0

        # Clearing one shouldn't affect others
        qa_service.clear_conversation_history("user1", "2024-W21")

        history1_after = qa_service.get_conversation_history("user1", "2024-W21")
        history2_after = qa_service.get_conversation_history("user2", "2024-W21")
        history3_after = qa_service.get_conversation_history("user1", "2024-W22")

        assert len(history1_after) == 0
        assert len(history2_after) > 0  # Unchanged
        assert len(history3_after) > 0  # Unchanged
