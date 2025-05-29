#!/usr/bin/env python3
"""
Meilisearch Setup Script for Prompteus GenAI Service

This script sets up Meilisearch indices and configures them properly.
It can be run standalone or as part of the deployment process.

The script configures:
- Index creation and settings (searchable, filterable, sortable attributes)
- OpenAI embedder for AI-powered semantic search (requires OPENAI_API_KEY)
- Search ranking rules and synonyms
- Stop words and other search optimizations

Usage:
    python scripts/setup_meilisearch.py [OPTIONS]

Options:
    --reset         Delete existing indices and recreate them
    --test          Run functionality tests after setup
    --test-only     Only run functionality tests (skip setup)
    --host HOST     Meilisearch host URL (default: http://localhost:7700)
    --key KEY       Meilisearch master key (default: from environment)
    --openai-key KEY OpenAI API key for embeddings (default: from environment)
    --help          Show this help message

Examples:
    # Basic setup
    python scripts/setup_meilisearch.py

    # Reset indices and run tests
    python scripts/setup_meilisearch.py --reset --test

    # Only run tests
    python scripts/setup_meilisearch.py --test-only

    # Setup with custom host and OpenAI key
    python scripts/setup_meilisearch.py --host http://localhost:7700 --openai-key sk-...

Environment Variables:
    MEILISEARCH_URL     - Meilisearch server URL
    MEILI_MASTER_KEY   - Meilisearch master key for authentication
    OPENAI_API_KEY     - OpenAI API key for embeddings (enables semantic search)
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
except NameError:
    # If __file__ is not available, we're probably running from the correct directory
    sys.path.insert(0, os.getcwd())

from src.meilisearch import MeilisearchService
import structlog

# Configure logging for the script
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def setup_meilisearch(host: str, master_key: str, openai_key: str = None, reset: bool = False):
    """Set up Meilisearch indices and configuration"""
    
    logger.info("Starting Meilisearch setup", host=host, reset=reset)
    
    # Override environment variables if provided
    if host:
        os.environ["MEILISEARCH_URL"] = host
    if master_key:
        os.environ["MEILI_MASTER_KEY"] = master_key
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    
    try:
        # Initialize Meilisearch service
        service = MeilisearchService()
        
        # Test connection first
        logger.info("Testing Meilisearch connection...")
        health = await service.health_check()
        
        if health["status"] != "healthy":
            logger.error("Meilisearch is not healthy", health=health)
            return False
        
        logger.info("Meilisearch connection successful", health=health["health"])
        
        # Reset indices if requested
        if reset:
            logger.info("Resetting Meilisearch indices...")
            try:
                # Delete the contributions index if it exists
                await asyncio.to_thread(
                    service.client.delete_index,
                    service.contributions_index_name
                )
                logger.info("Deleted existing contributions index")
            except Exception as e:
                logger.info("No existing index to delete", error=str(e))
        
        # Initialize the service (this will create indices and configure settings)
        logger.info("Initializing Meilisearch service...")
        success = await service.initialize()
        
        if not success:
            logger.error("Failed to initialize Meilisearch service")
            return False
        
        # Verify the setup
        logger.info("Verifying Meilisearch setup...")
        
        # Check index exists and get stats
        stats = await asyncio.to_thread(service.contributions_index.get_stats)
        logger.info("Contributions index stats", stats=stats)
        
        # Check settings
        settings = await asyncio.to_thread(service.contributions_index.get_settings)
        logger.info("Index settings configured", 
                   searchable_attributes=len(settings.get("searchableAttributes", [])),
                   filterable_attributes=len(settings.get("filterableAttributes", [])),
                   sortable_attributes=len(settings.get("sortableAttributes", [])))
        
        # Check if embedders are configured
        embedders = settings.get("embedders", {})
        if embedders:
            logger.info("Embedders configured for AI-powered search", 
                       embedder_count=len(embedders),
                       embedders=list(embedders.keys()))
        else:
            logger.warning("No embedders configured - only full-text search will be available")
        
        logger.info("Meilisearch setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error("Meilisearch setup failed", error=str(e))
        return False


async def test_meilisearch_functionality(host: str, master_key: str, openai_key: str = None):
    """Test basic Meilisearch functionality with sample data"""
    
    logger.info("Testing Meilisearch functionality...")
    
    # Override environment variables if provided
    if host:
        os.environ["MEILISEARCH_URL"] = host
    if master_key:
        os.environ["MEILI_MASTER_KEY"] = master_key
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    
    try:
        service = MeilisearchService()
        await service.initialize()
        
        # Create test documents
        test_documents = [
            {
                "id": "test-user-2024-W01-commit-1",
                "user": "testuser",
                "week": "2024-W01",
                "contribution_id": "commit-1",
                "contribution_type": "commit",
                "repository": "test/repo",
                "author": "testuser",
                "created_at": "2024-01-01T10:00:00Z",
                "created_at_timestamp": 1704110400,
                "title": "Fix authentication bug",
                "message": "Fix authentication bug",
                "body": "",
                "filename": "auth.py",
                "patch": "Fixed validation logic",
                "content": "Repository: test/repo\nAuthor: testuser\nCommit: Fix authentication bug\nFile: auth.py\nChanges: Fixed validation logic",
                "relevance_score": 1.0
            },
            {
                "id": "test-user-2024-W01-pr-1",
                "user": "testuser",
                "week": "2024-W01",
                "contribution_id": "pr-1",
                "contribution_type": "pull_request",
                "repository": "test/repo",
                "author": "testuser",
                "created_at": "2024-01-02T14:00:00Z",
                "created_at_timestamp": 1704204000,
                "title": "Add user management feature",
                "message": "",
                "body": "This PR adds comprehensive user management functionality",
                "filename": "",
                "patch": "",
                "content": "Repository: test/repo\nAuthor: testuser\nPull Request: Add user management feature\nDescription: This PR adds comprehensive user management functionality",
                "relevance_score": 1.0
            }
        ]
        
        # Index test documents
        logger.info("Indexing test documents...")
        task = await asyncio.to_thread(
            service.contributions_index.add_documents,
            test_documents
        )
        await asyncio.to_thread(service.client.wait_for_task, task.task_uid)
        logger.info("Test documents indexed successfully")
        
        # Test search functionality
        logger.info("Testing search functionality...")
        
        # Test 1: Search for "authentication"
        results = await service.search_contributions("testuser", "2024-W01", "authentication", limit=5)
        logger.info("Search test 1 - 'authentication'", results_count=len(results))
        
        # Test 2: Search for "user management"
        results = await service.search_contributions("testuser", "2024-W01", "user management", limit=5)
        logger.info("Search test 2 - 'user management'", results_count=len(results))
        
        # Test 3: Test semantic search if OpenAI key is available
        if openai_key:
            results = await service.search_contributions("testuser", "2024-W01", "fixing bugs and errors", limit=5)
            logger.info("Search test 3 - semantic search for 'fixing bugs and errors'", results_count=len(results))
        else:
            logger.info("Skipping semantic search test - no OpenAI key available")
        
        # Test 4: Get contributions count
        count = await service.get_contributions_count("testuser", "2024-W01")
        logger.info("Contributions count test", count=count)
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        await service.delete_user_week_contributions("testuser", "2024-W01")
        
        logger.info("Meilisearch functionality test completed successfully!")
        return True
        
    except Exception as e:
        logger.error("Meilisearch functionality test failed", error=str(e))
        return False


async def main():
    """Main function"""
    try:
        print("🚀 Starting Meilisearch setup script...")
        
        parser = argparse.ArgumentParser(
            description="Set up Meilisearch indices for Prompteus GenAI service",
            epilog=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add arguments
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing indices and recreate them"
        )
        
        parser.add_argument(
            "--host",
            default=os.getenv("MEILISEARCH_URL", "http://localhost:7700"),
            help="Meilisearch host URL (default: http://localhost:7700)"
        )
        
        parser.add_argument(
            "--key",
            default=os.getenv("MEILI_MASTER_KEY", "CHANGE_ME_CHANGE_ME"),
            help="Meilisearch master key (default: from MEILI_MASTER_KEY env var)"
        )
        
        parser.add_argument(
            "--openai-key",
            default=os.getenv("OPENAI_API_KEY"),
            help="OpenAI API key for embeddings (default: from OPENAI_API_KEY env var)"
        )
        
        parser.add_argument(
            "--test",
            action="store_true",
            help="Run functionality tests after setup"
        )
        
        parser.add_argument(
            "--test-only",
            action="store_true",
            help="Only run functionality tests (skip setup)"
        )
        
        # Parse arguments
        args = parser.parse_args()
        
        print(f"📊 Configuration:")
        print(f"   Host: {args.host}")
        print(f"   Master Key: {args.key[:10]}...")
        print(f"   OpenAI Key: {'✓ Available' if args.openai_key else '✗ Not available'}")
        print(f"   Reset: {args.reset}")
        print(f"   Test: {args.test}")
        print(f"   Test Only: {args.test_only}")
        print()
        
        # Setup logger
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        async def run_setup():
            success = True
            
            if not args.test_only:
                # Run setup
                success = await setup_meilisearch(args.host, args.key, args.openai_key, args.reset)
            
            if success and (args.test or args.test_only):
                # Run tests
                success = await test_meilisearch_functionality(args.host, args.key, args.openai_key)
            
            return success
        
        # Run the setup
        success = await run_setup()
        
        if success:
            print("✅ Meilisearch setup completed successfully!")
        else:
            print("❌ Meilisearch setup failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Fatal error in main: {e}")
        from traceback import TracebackException
        TracebackException.from_exception(e, limit=-10, capture_locals=True).print()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 