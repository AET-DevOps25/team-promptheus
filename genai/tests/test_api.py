import pytest
import json

from src.models import generate_uuidv7
from tests.test_data import get_test_contributions_request, get_minimal_commit_contribution


class TestHealthEndpoints:
    """Test health and monitoring endpoints"""
    
    def test_health_endpoint(self, test_client):
        """Test the health check endpoint"""
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
    
    def test_metrics_endpoint(self, test_client):
        """Test the Prometheus metrics endpoint"""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "genai_service_info" in response.text


class TestContributionsIngest:
    """Test contributions ingestion endpoints (legacy format - will be deprecated)"""
    
    def test_ingest_contributions_success(self, test_client, clean_services):
        """Test successful contribution ingestion returns task response"""
        request_data = get_test_contributions_request()
        
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Updated to match new task-based response
        assert "task_id" in data
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert data["status"] == "queued"
        assert data["total_contributions"] == 2
        assert "created_at" in data
    
    def test_ingest_contributions_invalid_data(self, test_client):
        """Test contribution ingestion with invalid data"""
        request_data = {
            "user": "testuser",
            # Missing required week
            "contributions": []
        }
        
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_ingest_contributions_empty_list(self, test_client, clean_services):
        """Test ingesting empty contributions list"""
        request_data = {
            "user": "testuser",
            "week": "2024-W21",
            "contributions": []
        }
        
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Updated to match new task-based response
        assert "task_id" in data
        assert data["total_contributions"] == 0
        assert data["status"] == "queued"


class TestTaskBasedIngestion:
    """Test new task-based ingestion endpoints"""
    
    def test_start_ingestion_task_success(self, test_client, clean_services):
        """Test starting an ingestion task"""
        request_data = get_test_contributions_request()
        
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert data["status"] == "queued"
        assert data["total_contributions"] == 2
        assert "created_at" in data
        
        # Store task_id for status check
        task_id = data["task_id"]
        
        # Check task status immediately
        status_response = test_client.get(f"/ingest/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["task_id"] == task_id
        assert status_data["user"] == "testuser"
        assert status_data["week"] == "2024-W21"
        assert status_data["status"] in ["queued", "processing", "completed"]
        assert status_data["total_contributions"] == 2
        assert status_data["ingested_count"] >= 0
        assert status_data["failed_count"] >= 0
        assert "created_at" in status_data
    
    def test_get_task_status_not_found(self, test_client):
        """Test getting status for non-existent task"""
        fake_task_id = generate_uuidv7()
        
        response = test_client.get(f"/ingest/{fake_task_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert "not found" in data["error"]
    
    def test_task_completion_status(self, test_client, clean_services):
        """Test that task eventually completes"""
        request_data = {
            "user": "testuser",
            "week": "2024-W21",
            "contributions": [get_minimal_commit_contribution()]
        }
        
        # Start the task
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # Wait for completion (up to 5 seconds)
        import time
        for _ in range(10):  # 10 * 0.5 = 5 seconds max
            time.sleep(0.5)
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            if status_data["status"] == "completed":
                # Verify completion data
                assert status_data["ingested_count"] == 1
                assert status_data["failed_count"] == 0
                assert "embedding_job_id" in status_data
                assert "completed_at" in status_data
                assert "processing_time_ms" in status_data
                break
        else:
            # If we reach here, task didn't complete in time
            pytest.fail("Task did not complete within 5 seconds")
    
    def test_task_with_empty_contributions(self, test_client, clean_services):
        """Test task with empty contributions list"""
        request_data = {
            "user": "testuser",
            "week": "2024-W21",
            "contributions": []
        }
        
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_contributions"] == 0
        task_id = data["task_id"]
        
        # Wait a moment for processing
        import time
        time.sleep(1)
        
        # Check final status
        status_response = test_client.get(f"/ingest/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["status"] == "completed"
        assert status_data["ingested_count"] == 0
        assert status_data["failed_count"] == 0


class TestContributionsStatus:
    """Test contributions status endpoints"""
    
    def test_get_contributions_status_success(self, test_client, clean_services):
        """Test getting contributions status"""
        # First ingest some contributions
        request_data = {
            "user": "testuser",
            "week": "2024-W21",
            "contributions": [get_minimal_commit_contribution()]
        }
        
        ingest_response = test_client.post("/contributions", json=request_data)
        assert ingest_response.status_code == 200
        
        # Wait a bit for processing
        import time
        time.sleep(0.5)
        
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
    
    def test_get_contributions_status_no_data(self, test_client):
        """Test getting status for user with no contributions"""
        response = test_client.get("/users/nonexistent/weeks/2024-W21/contributions/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["user"] == "nonexistent"
        assert data["week"] == "2024-W21"
        assert data["total_contributions"] == 0
        assert data["meilisearch_status"] in ["healthy", "not_configured"]


class TestQuestionAnswering:
    """Test question answering endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_client, clean_services):
        """Set up test data before each test"""
        # Ingest some test contributions
        self.test_contributions = get_test_contributions_request()
        
        # Ingest the test data
        response = test_client.post("/contributions", json=self.test_contributions)
        assert response.status_code == 200
        
        # Wait a bit for processing
        import time
        time.sleep(0.5)
    
    def test_ask_question_success(self, test_client):
        """Test successful question answering"""
        question_request = {
            "question": "What bugs were fixed this week?",
            "context": {
                "focus_areas": ["bug fixes", "authentication"],
                "include_code_changes": True,
                "max_evidence_items": 5
            }
        }
        
        response = test_client.post("/users/testuser/weeks/2024-W21/questions", json=question_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "question_id" in data
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert data["question"] == "What bugs were fixed this week?"
        assert "answer" in data
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0
        assert "evidence" in data
        assert "reasoning_steps" in data
        assert "suggested_actions" in data
        assert "asked_at" in data
        assert "response_time_ms" in data
        
        # Check evidence structure
        if data["evidence"]:
            evidence = data["evidence"][0]
            assert "contribution_id" in evidence
            assert "contribution_type" in evidence
            assert "excerpt" in evidence
            assert "relevance_score" in evidence
            assert "timestamp" in evidence
    
    def test_ask_question_no_relevant_contributions(self, test_client):
        """Test asking question when no relevant contributions exist"""
        question_request = {
            "question": "What database optimizations were made?",
            "context": {
                "focus_areas": ["database", "performance"],
                "include_code_changes": False,
                "max_evidence_items": 3
            }
        }
        
        response = test_client.post("/users/testuser/weeks/2024-W21/questions", json=question_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        # Note: With real Meilisearch, we might get some results, so confidence could be higher
        assert 0.0 <= data["confidence"] <= 1.0
    
    def test_ask_question_invalid_user_week(self, test_client):
        """Test asking question about non-existent user/week"""
        question_request = {
            "question": "What was done?",
            "context": {
                "focus_areas": [],
                "include_code_changes": True,
                "max_evidence_items": 5
            }
        }
        
        response = test_client.post("/users/nonexistent/weeks/2024-W99/questions", json=question_request)
        assert response.status_code == 404  # Should return 404 when no contributions exist
        
        data = response.json()
        assert "No contributions found" in data["error"]
    
    def test_get_question_success(self, test_client):
        """Test retrieving a previously asked question"""
        # First ask a question
        question_request = {
            "question": "What features were added?",
            "context": {
                "focus_areas": ["features"],
                "include_code_changes": True,
                "max_evidence_items": 5
            }
        }
        
        ask_response = test_client.post("/users/testuser/weeks/2024-W21/questions", json=question_request)
        assert ask_response.status_code == 200
        question_id = ask_response.json()["question_id"]
        
        # Then retrieve it
        response = test_client.get(f"/users/testuser/weeks/2024-W21/questions/{question_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["question_id"] == question_id
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert data["question"] == "What features were added?"
    
    def test_get_question_not_found(self, test_client):
        """Test retrieving a non-existent question"""
        fake_question_id = generate_uuidv7()
        response = test_client.get(f"/users/testuser/weeks/2024-W21/questions/{fake_question_id}")
        assert response.status_code == 404
    
    def test_ask_question_validation_error(self, test_client):
        """Test question request with invalid data"""
        question_request = {
            # Missing required question field
            "context": {
                "focus_areas": ["test"],
                "include_code_changes": True,
                "max_evidence_items": 5
            }
        }
        
        response = test_client.post("/users/testuser/weeks/2024-W21/questions", json=question_request)
        assert response.status_code == 422  # Validation error


class TestSummaryGeneration:
    """Test summary generation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_client, clean_services):
        """Set up test data before each test"""
        # Ingest some test contributions
        self.test_contributions = get_test_contributions_request()
        
        # Ingest the test data
        response = test_client.post("/contributions", json=self.test_contributions)
        assert response.status_code == 200
        
        # Wait a bit for processing
        import time
        time.sleep(0.5)
    
    def test_generate_summary_success(self, test_client):
        """Test successful summary generation"""
        summary_request = {
            "user": "testuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "comprehensive"
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
    
    def test_generate_summary_no_contributions(self, test_client, clean_services):
        """Test summary generation when no contributions exist"""
        summary_request = {
            "user": "nocontribuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "brief"
        }
        
        response = test_client.post("/users/nocontribuser/weeks/2024-W21/summary", json=summary_request)
        assert response.status_code == 404  # Should return 404 when no contributions exist
        
        data = response.json()
        assert "No contributions found" in data["error"]
    
    def test_generate_summary_stream_success(self, test_client):
        """Test successful streaming summary generation"""
        summary_request = {
            "user": "testuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": False,
            "include_issue_discussions": True,
            "max_detail_level": "standard"
        }
        
        response = test_client.post("/users/testuser/weeks/2024-W21/summary/stream", json=summary_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Parse the streaming response
        chunks = []
        for line in response.text.split('\n'):
            if line.startswith('data: '):
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
    
    def test_generate_summary_stream_no_contributions(self, test_client, clean_services):
        """Test streaming summary generation when no contributions exist"""
        summary_request = {
            "user": "nocontribuser",
            "week": "2024-W21",
            "include_code_changes": False,
            "include_pr_reviews": False,
            "include_issue_discussions": False,
            "max_detail_level": "brief"
        }
        
        response = test_client.post("/users/nocontribuser/weeks/2024-W21/summary/stream", json=summary_request)
        assert response.status_code == 404  # Should return 404 when no contributions exist
        
        data = response.json()
        assert "No contributions found" in data["error"]
    
    def test_get_summary_success(self, test_client):
        """Test retrieving a previously generated summary"""
        # First generate a summary
        summary_request = {
            "user": "testuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "comprehensive"
        }
        
        generate_response = test_client.post("/users/testuser/weeks/2024-W21/summary", json=summary_request)
        assert generate_response.status_code == 200
        
        summary_data = generate_response.json()
        summary_id = summary_data["summary_id"]
        
        # Then retrieve it
        response = test_client.get(f"/users/testuser/weeks/2024-W21/summaries/{summary_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["summary_id"] == summary_id
        assert data["user"] == "testuser"
        assert data["week"] == "2024-W21"
        assert data["overview"] == summary_data["overview"]
        assert data["metadata"]["total_contributions"] == summary_data["metadata"]["total_contributions"]
    
    def test_get_summary_not_found(self, test_client):
        """Test retrieving a non-existent summary"""
        fake_summary_id = generate_uuidv7()
        response = test_client.get(f"/users/testuser/weeks/2024-W21/summaries/{fake_summary_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]
    
    def test_get_summary_wrong_user_week(self, test_client):
        """Test retrieving a summary with wrong user/week combination"""
        # First generate a summary for testuser
        summary_request = {
            "user": "testuser",
            "week": "2024-W21",
            "include_code_changes": True,
            "include_pr_reviews": True,
            "include_issue_discussions": True,
            "max_detail_level": "brief"
        }
        
        generate_response = test_client.post("/users/testuser/weeks/2024-W21/summary", json=summary_request)
        assert generate_response.status_code == 200
        
        summary_data = generate_response.json()
        summary_id = summary_data["summary_id"]
        
        # Try to retrieve it with wrong user
        response = test_client.get(f"/users/wronguser/weeks/2024-W21/summaries/{summary_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]
        
        # Try to retrieve it with wrong week
        response = test_client.get(f"/users/testuser/weeks/2024-W22/summaries/{summary_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]
    
    def test_summary_validation_error(self, test_client):
        """Test summary generation with invalid request data"""
        invalid_request = {
            "user": "testuser",
            # Missing required week
            "include_code_changes": True,
            "max_detail_level": "invalid_level"
        }
        
        response = test_client.post("/users/testuser/weeks/2024-W21/summary", json=invalid_request)
        assert response.status_code == 422


class TestDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_json(self, test_client):
        """Test OpenAPI JSON endpoint"""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Prompteus GenAI Service"
    
    def test_scalar_ui(self, test_client):
        """Test Scalar UI endpoint"""
        response = test_client.get("/reference")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_json(self, test_client):
        """Test handling of invalid JSON"""
        response = test_client.post(
            "/contributions",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, test_client):
        """Test handling of missing required fields"""
        request_data = {
            "user": "testuser"
            # Missing week and contributions
        }
        
        response = test_client.post("/contributions", json=request_data)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data


class TestFullWorkflow:
    """Test complete workflow scenarios"""
    
    def test_complete_workflow(self, test_client, clean_services):
        """Test the complete workflow from ingestion to Q&A"""
        # 1. Ingest contributions
        contributions_data = get_test_contributions_request(
            user="workflowuser", 
            week="2024-W22", 
            contribution_types=["commit", "issue"]
        )
        
        ingest_response = test_client.post("/contributions", json=contributions_data)
        assert ingest_response.status_code == 200
        
        # Updated to check task-based response
        task_data = ingest_response.json()
        assert "task_id" in task_data
        assert task_data["total_contributions"] == 2
        task_id = task_data["task_id"]
        
        # Wait for task completion
        import time
        max_retries = 10
        for _ in range(max_retries):
            time.sleep(0.5)
            status_response = test_client.get(f"/ingest/{task_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            if status_data["status"] == "completed":
                assert status_data["ingested_count"] == 2
                break
        else:
            pytest.fail("Task did not complete within timeout")
        
        # 2. Check status
        status_response = test_client.get("/users/workflowuser/weeks/2024-W22/contributions/status")
        assert status_response.status_code == 200
        assert status_response.json()["total_contributions"] == 2
        
        # 3. Ask questions about the contributions
        question1 = {
            "question": "What new features were implemented?",
            "context": {
                "focus_areas": ["features", "implementation"],
                "include_code_changes": True,
                "max_evidence_items": 5
            }
        }
        
        q1_response = test_client.post("/users/workflowuser/weeks/2024-W22/questions", json=question1)
        assert q1_response.status_code == 200
        q1_data = q1_response.json()
        assert "answer" in q1_data
        
        question2 = {
            "question": "Are there any performance issues?",
            "context": {
                "focus_areas": ["performance", "optimization"],
                "include_code_changes": False,
                "max_evidence_items": 3
            }
        }
        
        q2_response = test_client.post("/users/workflowuser/weeks/2024-W22/questions", json=question2)
        assert q2_response.status_code == 200
        q2_data = q2_response.json()
        assert "answer" in q2_data
        
        # 4. Retrieve questions
        q1_id = q1_data["question_id"]
        retrieve_response = test_client.get(f"/users/workflowuser/weeks/2024-W22/questions/{q1_id}")
        assert retrieve_response.status_code == 200
        assert retrieve_response.json()["question_id"] == q1_id
    
    def test_multiple_users_same_week(self, test_client, clean_services):
        """Test handling multiple users in the same week"""
        week = "2024-W23"
        
        # Ingest for user1
        user1_data = {
            "user": "user1",
            "week": week,
            "contributions": [get_minimal_commit_contribution()]
        }
        
        # Ingest for user2
        user2_data = {
            "user": "user2",
            "week": week,
            "contributions": [get_minimal_commit_contribution()]
        }
        
        # Ingest both
        response1 = test_client.post("/contributions", json=user1_data)
        response2 = test_client.post("/contributions", json=user2_data)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Wait for processing
        import time
        time.sleep(1.0)
        
        # Ask questions for each user
        question = {
            "question": "What did I work on?",
            "context": {
                "focus_areas": [],
                "include_code_changes": True,
                "max_evidence_items": 5
            }
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