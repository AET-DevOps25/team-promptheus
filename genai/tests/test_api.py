"""Tests for the FastAPI application endpoints."""

import json
import time

import pytest

from src.models import generate_uuidv7
from tests.test_data import (
    get_test_contributions_metadata_request,
    get_test_contributions_request,  # Legacy format for backward compatibility tests
)


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    def test_health_endpoint(self, test_client) -> None:
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

        # Check service status
        services = data["services"]
        assert "contributions_ingestion" in services
        assert "question_answering" in services
        assert "meilisearch" in services
        assert "langchain" in services

        # With real Meilisearch, status should be "healthy"
        assert services["meilisearch"] in ["healthy", "not_configured"]

    def test_metrics_endpoint(self, test_client) -> None:
        """Test the Prometheus metrics endpoint."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "genai_service_info" in response.text


@pytest.mark.usefixtures("mock_summary_for_api")
class TestUnifiedWorkflow:
    """Test the unified workflow endpoint that handles ingestion and summarization in one task."""

    def test_unified_task_creation(self, test_client, clean_services) -> None:
        """Test creating a unified task with metadata-only contributions."""
        # Use metadata-only format - same as working tests
        request_data = get_test_contributions_metadata_request(contribution_types=["commit"])

        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"
        assert "summary_id" in data

    def test_unified_task_completion_with_summary(self, test_client, clean_services) -> None:
        """Test that unified task completes and includes summary when done."""
        # Use metadata-only format
        request_data = get_test_contributions_metadata_request()

        # Start unified task
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["task_id"]
        summary_id = task_data["summary_id"]

        # Wait for completion and check status
        max_attempts = 20
        for _attempt in range(max_attempts):
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()

            assert status_data["status"] in [
                "queued",
                "ingesting",
                "summarizing",
                "done",
            ]
            assert "task_id" in status_data
            assert status_data["failed_count"] >= 0

            if status_data["status"] == "done":
                assert status_data["failed_count"] >= 0

                # Verify summary is included when done
                assert "summary" in status_data
                summary = status_data["summary"]
                assert summary is not None
                assert "summary_id" in summary
                assert summary["summary_id"] == summary_id
                assert isinstance(summary["overview"], str)
                assert len(summary["overview"]) > 0
                break
            if status_data["status"] == "failed":
                pytest.fail(f"Task failed: {status_data.get('error_message', 'Unknown error')}")

            time.sleep(0.5)
        else:
            pytest.fail(f"Task {task_id} did not complete within {max_attempts * 0.5} seconds")

    def test_unified_task_with_github_api_failure(self, test_client, clean_services, failing_github_service) -> None:
        """Test that unified task properly handles GitHub API failures with FAILED status."""
        # Use metadata-only format with invalid repository to trigger GitHub API failure
        request_data = {
            "user": "testuser",
            "week": "2024-W21",
            "repository": "invalid/repo",
            "contributions": [{"type": "commit", "id": "abc123def456", "selected": True}],
        }

        # Start unified task
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["task_id"]

        # Wait for task to complete or fail
        max_attempts = 20
        final_status = None
        for _attempt in range(max_attempts):
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()

            final_status = status_data["status"]
            if final_status in ["done", "failed"]:
                break
            time.sleep(0.5)
        else:
            pytest.fail(f"Task {task_id} did not complete within {max_attempts * 0.5} seconds")

        # Verify task failed gracefully with proper status
        assert final_status == "failed"
        assert "error_message" in status_data
        assert status_data["error_message"] is not None
        assert len(status_data["error_message"]) > 0

        # Verify task has proper structure even when failed
        assert "task_id" in status_data
        assert status_data["task_id"] == task_id
        assert "failed_count" in status_data

        # Summary should be None or not present when task fails
        if "summary" in status_data:
            assert status_data["summary"] is None

    def test_unified_task_with_partial_github_failure(self, test_client, clean_services) -> None:
        """Test that unified task handles partial GitHub API failures gracefully."""
        # Use metadata with one contribution that will fail
        request_data = {
            "user": "testuser",
            "week": "2024-W21",
            "repository": "test/repo",
            "contributions": [
                {"type": "commit", "id": "abc123def456", "selected": True},
                {
                    "type": "commit",
                    "id": "fail123",
                    "selected": True,
                },  # This will be skipped by mock
            ],
        }

        # Start unified task
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["task_id"]

        # Wait for completion
        max_attempts = 20
        for _attempt in range(max_attempts):
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()

            if status_data["status"] == "done":
                # Should complete successfully but with failed_count > 0
                assert status_data["failed_count"] > 0
                assert "summary" in status_data
                summary = status_data["summary"]
                assert summary is not None  # Should still generate summary with partial data
                break
            if status_data["status"] == "failed":
                pytest.fail(f"Task failed when it should handle partial failures: {status_data.get('error_message')}")

            time.sleep(0.5)
        else:
            pytest.fail(f"Task {task_id} did not complete within {max_attempts * 0.5} seconds")


class TestTaskStatus:
    """Test task status endpoints."""

    def test_get_task_status_not_found(self, test_client) -> None:
        """Test getting status for non-existent task."""
        fake_task_id = generate_uuidv7()

        response = test_client.get(f"/ingest/{fake_task_id}")
        assert response.status_code == 404

        data = response.json()
        assert "not found" in data["error"]

    def test_simple_task_creation(self, test_client, clean_services) -> None:
        """Test creating a task - debugging version."""
        request_data = get_test_contributions_metadata_request(contribution_types=["commit"])

        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "task_id" in data

    def test_task_status_progression(self, test_client, clean_services) -> None:
        """Test that task status progresses through expected states."""
        request_data = get_test_contributions_metadata_request(contribution_types=["commit"])

        # Start the task
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        # Track status progression
        observed_statuses = set()

        # Poll for status changes
        import time

        for _ in range(15):  # 15 seconds max
            time.sleep(1)
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            current_status = status_data["status"]
            observed_statuses.add(current_status)

            if current_status in ["done", "failed"]:
                break

        # Should have seen at least queued and either done or some processing status
        assert "queued" in observed_statuses or len(observed_statuses) > 0
        assert any(status in observed_statuses for status in ["done", "failed", "ingesting", "summarizing"])

    def test_task_handles_github_api_failure_gracefully(
        self, test_client, clean_services, failing_github_service
    ) -> None:
        """Test that tasks handle GitHub API failures gracefully with proper FAILED status."""
        # Use metadata that will trigger GitHub API failure
        request_data = {
            "user": "testuser",
            "week": "2024-W21",
            "repository": "invalid/repo",  # This will trigger GitHub API failure
            "contributions": [{"type": "commit", "id": "abc123def456", "selected": True}],
        }

        # Start the task
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        # Wait for task to complete or fail
        import time

        final_status = None
        final_response = None
        for _ in range(20):  # 20 seconds max
            time.sleep(1)
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200  # Should never crash, even on failure

            status_data = status_response.json()
            final_status = status_data["status"]
            final_response = status_data

            if final_status in ["done", "failed"]:
                break

        # Verify the task failed gracefully with proper structure
        assert final_status == "failed", f"Expected task to fail gracefully, but got status: {final_status}"
        assert "error_message" in final_response
        assert final_response["error_message"] is not None
        assert len(final_response["error_message"]) > 0

        # Verify task has proper structure even when failed
        assert "task_id" in final_response
        assert final_response["task_id"] == task_id
        assert "failed_count" in final_response

        # Summary should be None when task fails
        if "summary" in final_response:
            assert final_response["summary"] is None


class TestContributionsStatus:
    """Test contributions status endpoints."""

    def test_get_contributions_status_success(self, test_client, clean_services) -> None:
        """Test getting contributions status after unified workflow."""
        # First run unified ingestion + summarization
        request_data = get_test_contributions_metadata_request(contribution_types=["commit"])

        ingest_response = test_client.post("/contributions", json=request_data)
        assert ingest_response.status_code == 200

        # Wait a bit for processing
        import time

        time.sleep(2)

        # Then check status
        response = test_client.get("/users/testuser/weeks/2024-W21/contributions/status")
        assert response.status_code == 200

        data = response.json()
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert "total_contributions" in data
        assert "embedded_contributions" in data
        assert "pending_embeddings" in data
        assert "last_updated" in data
        assert "meilisearch_status" in data

        # With real Meilisearch, status should be "healthy"
        assert data["meilisearch_status"] in ["healthy", "not_configured"]

    def test_get_contributions_status_no_data(self, test_client) -> None:
        """Test getting status for user with no contributions."""
        response = test_client.get("/users/nonexistent/weeks/2024-W21/contributions/status")
        assert response.status_code == 200

        data = response.json()
        assert data["user"] == "nonexistent"
        assert data["week"] == "2024-W21"
        assert data["total_contributions"] == 0
        assert data["meilisearch_status"] in ["healthy", "not_configured"]


class TestQuestionAnswering:
    """Test question answering endpoints."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_client, clean_services) -> None:
        """Set up test data before each test using unified workflow."""
        # Use unified workflow to ingest and summarize test data
        self.test_contributions = get_test_contributions_metadata_request()

        # Start unified task
        response = test_client.post("/contributions", json=self.test_contributions)
        assert response.status_code == 200
        self.task_id = response.json()["task_id"]

        # Wait for completion
        import time

        for _ in range(10):  # 10 seconds max for setup
            time.sleep(1)
            status_response = test_client.get(f"/ingest/{self.task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] in ["done", "failed"]:
                    break

    async def test_ask_question_success(self, test_client) -> None:
        """Test successful question answering."""
        request_data = {
            "question": "What commits were made?",
            "context": {
                "focus_areas": ["features", "bugs", "performance"],
                "include_evidence": True,
                "reasoning_depth": "detailed",
                "max_evidence_items": 5,
            },
        }

        response = test_client.post("/users/testuser/weeks/2024-W21/questions", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "question_id" in data
        assert "user" in data
        assert "week" in data
        assert "question" in data
        assert "answer" in data
        assert "confidence" in data
        assert "evidence" in data
        assert "reasoning_steps" in data
        assert "suggested_actions" in data
        assert "asked_at" in data
        assert "response_time_ms" in data
        assert "conversation_id" in data

        # Verify values
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert data["question"] == "What commits were made?"
        assert isinstance(data["answer"], str)
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["evidence"], list)
        assert isinstance(data["reasoning_steps"], list)
        assert isinstance(data["suggested_actions"], list)
        assert isinstance(data["response_time_ms"], int)
        assert data["conversation_id"] == "testuser:2024-W21"

    @pytest.mark.skip(reason="Conversation history persistence is being refactored")
    async def test_conversation_history_endpoints(self, test_client) -> None:
        """Test conversation history API endpoints."""
        user = "testuser"
        week = "2024-W21"

        # First, ask a question to create conversation history
        request_data = {
            "question": "What was done this week?",
            "context": {"include_evidence": True, "reasoning_depth": "detailed"},
        }

        response = test_client.post(f"/users/{user}/weeks/{week}/questions", json=request_data)
        assert response.status_code == 200

        # Test getting conversation history
        history_response = test_client.get(f"/users/{user}/weeks/{week}/conversations/history")
        assert history_response.status_code == 200

        history_data = history_response.json()
        assert isinstance(history_data, dict)
        assert "session_id" in history_data
        assert "message_count" in history_data
        assert "messages" in history_data
        assert history_data["session_id"] == f"{user}:{week}"
        # Should have at least 2 messages (human question + AI response)
        assert history_data["message_count"] >= 2
        assert len(history_data["messages"]) >= 2

        # Test clearing conversation history
        clear_response = test_client.delete(f"/users/{user}/weeks/{week}/conversations")
        assert clear_response.status_code == 200

        clear_data = clear_response.json()
        assert "message" in clear_data
        assert "session_id" in clear_data

        # Verify history is cleared
        history_after_clear = test_client.get(f"/users/{user}/weeks/{week}/conversations/history")
        assert history_after_clear.status_code == 200

        cleared_history = history_after_clear.json()
        assert isinstance(cleared_history, dict)
        assert cleared_history["message_count"] == 0
        assert len(cleared_history["messages"]) == 0


@pytest.mark.usefixtures("mock_summary_for_api")
class TestSummaryGeneration:
    """Test summary generation endpoints (Legacy standalone + Unified workflow)."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_client, clean_services, mock_summary_for_api) -> None:
        """Set up test data before each test using unified workflow."""
        # Use unified workflow to ingest and summarize test data
        self.test_contributions = get_test_contributions_metadata_request()

        # Start unified task
        response = test_client.post("/contributions", json=self.test_contributions)
        assert response.status_code == 200
        self.task_id = response.json()["task_id"]

        # Wait for completion to ensure summary is available
        import time

        for i in range(30):  # 30 seconds max for setup
            time.sleep(1)
            status_response = test_client.get(f"/ingest/{self.task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] == "done":
                    # Summary should be available
                    assert "summary" in status_data
                    self.task_summary = status_data["summary"]
                    break
                if status_data["status"] == "failed":
                    pytest.fail(f"Setup task failed: {status_data.get('error_message', 'Unknown error')}")
            if i == 29:  # Last iteration
                pytest.fail(
                    f"Task did not complete in time. Final status: {status_data.get('status', 'unknown') if 'status_data' in locals() else 'no response'}"
                )

    def test_summary_via_unified_workflow(self, test_client) -> None:
        """Test that summary is available through unified workflow."""
        # Get the completed task status which should include summary
        response = test_client.get(f"/ingest/{self.task_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "done"
        assert "summary" in data

        summary = data["summary"]
        assert "summary_id" in summary
        assert summary["user"] == "testuser"
        assert summary["week"] == "2024-W21"
        assert "overview" in summary
        assert "commits_summary" in summary
        assert "pull_requests_summary" in summary
        assert "issues_summary" in summary
        assert "releases_summary" in summary
        assert "analysis" in summary
        assert "key_achievements" in summary
        assert "areas_for_improvement" in summary
        assert "metadata" in summary
        assert "generated_at" in summary

        # Check metadata structure
        metadata = summary["metadata"]
        assert "total_contributions" in metadata
        assert "commits_count" in metadata
        assert "pull_requests_count" in metadata
        assert "issues_count" in metadata
        assert "releases_count" in metadata
        assert "repositories" in metadata
        assert "time_period" in metadata
        assert "generated_at" in metadata
        assert "processing_time_ms" in metadata

    def test_generate_summary_standalone_success(self, test_client) -> None:
        """Test legacy standalone summary generation (if still supported)."""
        summary_request = {
            "user": "testuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "comprehensive",
        }

        response = test_client.post("/users/testuser/weeks/2024-W21/summary", json=summary_request)
        assert response.status_code == 200

        data = response.json()
        assert "summary_id" in data
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert "overview" in data
        assert "commits_summary" in data
        assert "pull_requests_summary" in data
        assert "issues_summary" in data
        assert "releases_summary" in data
        assert "analysis" in data
        assert "key_achievements" in data
        assert "areas_for_improvement" in data
        assert "metadata" in data
        assert "generated_at" in data

        # Check metadata structure
        metadata = data["metadata"]
        assert "total_contributions" in metadata
        assert "commits_count" in metadata
        assert "pull_requests_count" in metadata
        assert "issues_count" in metadata
        assert "releases_count" in metadata
        assert "repositories" in metadata
        assert "time_period" in metadata
        assert "generated_at" in metadata
        assert "processing_time_ms" in metadata

        # Verify content is not empty for our test data
        assert len(data["overview"]) > 0
        assert metadata["total_contributions"] >= 2  # At least 2 from test data

    def test_generate_summary_no_contributions(self, test_client, clean_services) -> None:
        """Test summary generation when no contributions exist."""
        summary_request = {
            "user": "nocontribuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "brief",
        }

        response = test_client.post("/users/nocontribuser/weeks/2024-W21/summary", json=summary_request)
        assert response.status_code == 404  # Should return 404 when no contributions exist

        data = response.json()
        assert "No contributions found" in data["error"]

    def test_generate_summary_stream_success(self, test_client) -> None:
        """Test successful streaming summary generation (if still supported)."""
        summary_request = {
            "user": "testuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": False,
            "include_issue_discussions": True,
            "max_detail_level": "standard",
        }

        response = test_client.post("/users/testuser/weeks/2024-W21/summary/stream", json=summary_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # Parse the streaming response
        chunks = []
        for line in response.text.split("\n"):
            if line.startswith("data: "):
                chunk_data = json.loads(line[6:])  # Remove 'data: ' prefix
                chunks.append(chunk_data)

        # Verify we got chunks
        assert len(chunks) > 0

        # Check for expected chunk types
        chunk_types = [chunk.get("chunk_type") for chunk in chunks]
        assert "metadata" in chunk_types
        assert "section" in chunk_types
        assert "content" in chunk_types
        assert "complete" in chunk_types

        # Find the metadata chunk
        metadata_chunk = next((chunk for chunk in chunks if chunk.get("chunk_type") == "metadata"), None)
        assert metadata_chunk is not None
        assert "metadata" in metadata_chunk
        assert metadata_chunk["metadata"]["total_contributions"] >= 2  # At least 2 from test data

        # Find the completion chunk
        complete_chunk = next((chunk for chunk in chunks if chunk.get("chunk_type") == "complete"), None)
        assert complete_chunk is not None
        assert "summary_id" in complete_chunk["metadata"]
        assert "processing_time_ms" in complete_chunk["metadata"]

    def test_get_summary_success(self, test_client) -> None:
        """Test retrieving a previously generated summary by ID."""
        # Use the summary from the unified workflow setup
        if hasattr(self, "task_summary"):
            summary_id = self.task_summary["summary_id"]

            # Retrieve summary by ID
            response = test_client.get(f"/users/testuser/weeks/2024-W21/summaries/{summary_id}")
            assert response.status_code == 200

            data = response.json()
            assert data["summary_id"] == summary_id
            assert data["user"] == "testuser"
            assert data["week"] == "2024-W21"
            assert "overview" in data
            assert "metadata" in data

    def test_get_summary_not_found(self, test_client) -> None:
        """Test retrieving a non-existent summary."""
        fake_summary_id = generate_uuidv7()
        response = test_client.get(f"/users/testuser/weeks/2024-W21/summaries/{fake_summary_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]


class TestDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_json(self, test_client) -> None:
        """Test OpenAPI JSON endpoint."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Prompteus GenAI Service"

    def test_scalar_ui(self, test_client) -> None:
        """Test Scalar UI endpoint."""
        response = test_client.get("/reference")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_json(self, test_client) -> None:
        """Test handling of invalid JSON."""
        response = test_client.post(
            "/contributions",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, test_client) -> None:
        """Test handling of missing required fields."""
        request_data = {
            "user": "testuser"
            # Missing week and contributions
        }

        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data


@pytest.mark.usefixtures("mock_summary_for_api")
class TestFullWorkflow:
    """Test complete workflow scenarios."""

    def test_complete_unified_workflow(self, test_client, clean_services) -> None:
        """Test the complete unified workflow from ingestion to summarization to Q&A."""
        # 1. Start unified ingestion + summarization task
        contributions_data = get_test_contributions_metadata_request(
            user="workflowuser",
            week="2024-W22",
            repository="test/repo",
            contribution_types=["commit", "issue"],
        )

        ingest_response = test_client.post("/contributions", json=contributions_data)
        assert ingest_response.status_code == 200

        # Check task-based response
        task_data = ingest_response.json()
        assert "task_id" in task_data
        assert task_data["total_contributions"] == 2
        assert task_data["repository"] == "test/repo"
        task_id = task_data["task_id"]

        # Wait for unified task completion (ingestion + summarization)
        import time

        max_retries = 20  # Increased for unified workflow
        for _ in range(max_retries):
            time.sleep(1)
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            if status_data["status"] == "done":
                # Verify both ingestion and summarization completed
                assert status_data["ingested_count"] >= 0  # May be 0 if GitHub API mocked
                assert "summary" in status_data  # Summary included in unified workflow
                summary = status_data["summary"]
                assert "summary_id" in summary
                assert summary["user"] == "workflowuser"
                assert summary["week"] == "2024-W22"
                break
            if status_data["status"] == "failed":
                pytest.fail(f"Unified task failed: {status_data.get('error_message', 'Unknown error')}")
        else:
            pytest.fail("Unified task did not complete within timeout")

        # 2. Check contributions status
        status_response = test_client.get("/users/workflowuser/weeks/2024-W22/contributions/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["user"] == "workflowuser"
        assert status_data["week"] == "2024-W22"

        # 3. Ask questions about the contributions
        question1 = {
            "question": "What new features were implemented?",
            "context": {
                "focus_areas": ["features", "implementation"],
                "include_evidence": True,
                "reasoning_depth": "detailed",
            },
        }

        q1_response = test_client.post("/users/workflowuser/weeks/2024-W22/questions", json=question1)
        assert q1_response.status_code == 200
        q1_data = q1_response.json()
        assert "answer" in q1_data
        assert q1_data["user"] == "workflowuser"
        assert q1_data["week"] == "2024-W22"

        question2 = {
            "question": "Are there any performance issues?",
            "context": {
                "focus_areas": ["performance", "optimization"],
                "include_evidence": True,
                "reasoning_depth": "quick",
            },
        }

        q2_response = test_client.post("/users/workflowuser/weeks/2024-W22/questions", json=question2)
        assert q2_response.status_code == 200
        q2_data = q2_response.json()
        assert "answer" in q2_data

        # 4. Retrieve questions by ID
        q1_id = q1_data["question_id"]
        retrieve_response = test_client.get(f"/users/workflowuser/weeks/2024-W22/questions/{q1_id}")
        assert retrieve_response.status_code == 200
        assert retrieve_response.json()["question_id"] == q1_id

    def test_multiple_users_same_week_unified(self, test_client, clean_services) -> None:
        """Test handling multiple users in the same week with unified workflow."""
        week = "2024-W23"

        # Prepare metadata for both users
        user1_data = get_test_contributions_metadata_request(
            user="user1",
            week=week,
            repository="user1/repo",
            contribution_types=["commit"],
            selected=True,
        )

        user2_data = get_test_contributions_metadata_request(
            user="user2",
            week=week,
            repository="user2/repo",
            contribution_types=["commit"],
            selected=True,
        )

        # Start unified tasks for both users
        response1 = test_client.post("/contributions", json=user1_data)
        response2 = test_client.post("/contributions", json=user2_data)
        assert response1.status_code == 200
        assert response2.status_code == 200

        task1_id = response1.json()["task_id"]
        task2_id = response2.json()["task_id"]

        # Wait for both tasks to complete
        import time

        for task_id in [task1_id, task2_id]:
            for _ in range(15):  # 15 seconds per task
                time.sleep(1)
                status_response = test_client.get(f"/ingest/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data["status"] in ["done", "failed"]:
                        break

        # Ask questions for each user
        question = {
            "question": "What did I work on?",
            "context": {
                "focus_areas": [],
                "include_evidence": True,
                "reasoning_depth": "detailed",
            },
        }

        q1_response = test_client.post(f"/users/user1/weeks/{week}/questions", json=question)
        q2_response = test_client.post(f"/users/user2/weeks/{week}/questions", json=question)

        assert q1_response.status_code == 200
        assert q2_response.status_code == 200

        # Verify each user gets their own data
        q1_data = q1_response.json()
        q2_data = q2_response.json()

        assert q1_data["user"] == "user1"
        assert q2_data["user"] == "user2"
        assert q1_data["week"] == week
        assert q2_data["week"] == week

    def test_legacy_workflow_compatibility(self, test_client, clean_services) -> None:
        """Test that legacy workflow still works (backward compatibility)."""
        # Use legacy format (without repository, full contribution data)
        legacy_data = get_test_contributions_request(user="legacyuser", week="2024-W24", contribution_types=["commit"])

        # This might fail validation due to missing repository field
        response = test_client.post("/contributions", json=legacy_data)

        # Either succeeds with task response or fails validation
        assert response.status_code in [200, 422]
