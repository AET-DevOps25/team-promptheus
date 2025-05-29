"""
Pytest configuration and fixtures for GenAI service tests
"""

import pytest
import pytest_asyncio
import asyncio
import os
from fastapi.testclient import TestClient

# Import our application and services
from src.services import ContributionsIngestionService, QuestionAnsweringService, SummaryService
from src.meilisearch import MeilisearchService

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def meilisearch_service():
    """Create and initialize a real Meilisearch service for testing"""
    # Set test environment variables
    os.environ["MEILISEARCH_URL"] = "http://meilisearch:7700"
    os.environ["MEILI_MASTER_KEY"] = "CHANGE_ME_CHANGE_ME"
    
    service = MeilisearchService()
    
    try:
        initialized = await service.initialize()
        if not initialized:
            pytest.skip("Meilisearch not available for testing")
    except Exception as e:
        pytest.skip(f"Meilisearch initialization failed: {e}")
    
    yield service
    
    # Cleanup: delete test data
    try:
        # Delete all test documents
        await service.contributions_index.delete_all_documents()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="session")
def test_services(meilisearch_service):
    """Initialize test services with real Meilisearch"""
    ingestion_service = ContributionsIngestionService(meilisearch_service)
    qa_service = QuestionAnsweringService(ingestion_service)
    summary_service = SummaryService(ingestion_service)
    
    return {
        "meilisearch": meilisearch_service,
        "ingestion": ingestion_service,
        "qa": qa_service,
        "summary": summary_service
    }


@pytest.fixture(scope="session")
def test_client(test_services):
    """Create a test client with properly initialized services"""
    # Import app inside the fixture to avoid circular imports
    import app as app_module
    
    # Monkey patch the app's global service instances
    app_module.meilisearch_service = test_services["meilisearch"]
    app_module.ingestion_service = test_services["ingestion"]
    app_module.qa_service = test_services["qa"]
    app_module.summary_service = test_services["summary"]
    
    # Create the test client with the FastAPI app instance
    test_client_instance = TestClient(app_module.app)
    
    yield test_client_instance
    
    # Cleanup
    app_module.meilisearch_service = None
    app_module.ingestion_service = None
    app_module.qa_service = None
    app_module.summary_service = None


@pytest.fixture(autouse=True)
def ensure_services(test_services):
    """Ensure services are available for each test"""
    import app as app_module
    # Always set the services for tests
    app_module.meilisearch_service = test_services["meilisearch"]
    app_module.ingestion_service = test_services["ingestion"]
    app_module.qa_service = test_services["qa"]
    app_module.summary_service = test_services["summary"]


@pytest_asyncio.fixture(loop_scope="function")
async def clean_services(test_services):
    """Clean service state between tests"""
    # Clear any stored data
    test_services["ingestion"].contributions_store.clear()
    test_services["ingestion"].embedding_jobs.clear()
    test_services["qa"].questions_store.clear()
    test_services["summary"].summaries_store.clear()
    
    # Clear Meilisearch test data
    try:
        await test_services["meilisearch"].contributions_index.delete_all_documents()
        # Wait a bit for deletion to complete
        await asyncio.sleep(0.1)
    except Exception:
        pass  # Ignore cleanup errors
    
    yield test_services 