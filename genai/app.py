"""Prompteus GenAI Service - FastAPI Application.

A comprehensive AI-powered service for analyzing GitHub contributions,
generating intelligent summaries, and providing interactive Q&A capabilities.
"""

import json
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import structlog
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from src.meilisearch import MeilisearchService
from src.metrics import initialize_service_info
from src.models import (
    ContributionsIngestRequest,
    ContributionsStatusResponse,
    ErrorResponse,
    HealthResponse,
    IngestTaskResponse,
    IngestTaskStatus,
    QuestionRequest,
    QuestionResponse,
    SummaryChunk,
    SummaryRequest,
    SummaryResponse,
)
from src.services import (
    ContributionsIngestionService,
    QuestionAnsweringService,
    SummaryService,
)

# Configuration constants
APP_TITLE = "Prompteus GenAI Service"
APP_DESCRIPTION = "AI-powered service for ingesting GitHub contributions and providing Q&A for user weekly summaries"
APP_VERSION = "1.0.0"
DEFAULT_MODEL_NAME = "llama3.3:latest"

# Service error messages
SERVICE_NOT_INITIALIZED = "Service not initialized"
INGESTION_TASK_FAILED = "Failed to start ingestion task"
SUMMARY_GENERATION_FAILED = "Streaming summary generation failed"

load_dotenv()


class ServiceContainer:
    """Container for managing service instances following dependency injection pattern."""

    def __init__(self) -> None:
        self.meilisearch_service: MeilisearchService | None = None
        self.ingestion_service: ContributionsIngestionService | None = None
        self.qa_service: QuestionAnsweringService | None = None
        self.summary_service: SummaryService | None = None
        # Telemetry components
        self.span_processor: BatchSpanProcessor | None = None
        self.otlp_exporter: OTLPSpanExporter | None = None
        self.tracer_provider: TracerProvider | None = None

    async def initialize_services(self) -> None:
        """Initialize all services with proper dependency injection."""
        logger.info("Initializing GenAI services...")

        # Initialize OpenTelemetry first
        await self._initialize_telemetry()

        # Initialize Meilisearch service
        self.meilisearch_service = MeilisearchService()
        meilisearch_initialized = await self.meilisearch_service.initialize()

        if not meilisearch_initialized:
            logger.warning("Meilisearch service failed to initialize, continuing without it")
            self.meilisearch_service = None

        # Get GitHub token from environment
        github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_PAT")

        # Initialize services first
        self.ingestion_service = ContributionsIngestionService(self.meilisearch_service, github_token)
        self.qa_service = QuestionAnsweringService(self.ingestion_service)
        self.summary_service = SummaryService(self.ingestion_service)

        # Inject summary service into ingestion service to enable full workflow
        self.ingestion_service.summary_service = self.summary_service

        # Initialize metrics
        model_name = os.getenv("LANGCHAIN_MODEL_NAME", DEFAULT_MODEL_NAME)
        initialize_service_info(APP_VERSION, model_name)

        logger.info("GenAI services initialized successfully")

    async def _initialize_telemetry(self) -> None:
        """Initialize OpenTelemetry with proper async context."""
        try:
            # Initialize OpenTelemetry
            self.tracer_provider = TracerProvider()
            trace.set_tracer_provider(self.tracer_provider)

            # Set up OTLP exporter
            self.otlp_exporter = OTLPSpanExporter(
                endpoint=os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4317/v1/traces")
            )
            self.span_processor = BatchSpanProcessor(self.otlp_exporter)
            self.tracer_provider.add_span_processor(self.span_processor)

            logger.info("OpenTelemetry initialized successfully")
        except Exception as e:
            logger.warning("Failed to initialize OpenTelemetry", error=str(e))

    def instrument_app(self, app: FastAPI) -> None:
        """Instrument FastAPI app with OpenTelemetry after telemetry is initialized."""
        try:
            if self.tracer_provider:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI instrumented with OpenTelemetry")
        except Exception as e:
            logger.warning("Failed to instrument FastAPI with OpenTelemetry", error=str(e))

    def cleanup_services(self) -> None:
        """Cleanup services on shutdown."""
        logger.info("Shutting down GenAI services...")

    async def cleanup_services_async(self) -> None:
        """Async cleanup of services on shutdown."""
        logger.info("Shutting down GenAI services...")

        # Clean up QA service async resources
        if self.qa_service:
            try:
                await self.qa_service.cleanup()
            except Exception as e:
                logger.warning("Error cleaning up QA service", error=str(e))

        # Clean up OpenTelemetry resources
        await self._cleanup_telemetry()

    async def _cleanup_telemetry(self) -> None:
        """Clean up OpenTelemetry resources properly."""
        try:
            # Clean up FastAPI instrumentation first
            try:
                FastAPIInstrumentor.uninstrument_app(app)
            except Exception as e:
                logger.warning("Error uninstrumenting FastAPI", error=str(e))

            if self.span_processor:
                # Force flush and shutdown the span processor
                if hasattr(self.span_processor, "force_flush"):
                    self.span_processor.force_flush(timeout_millis=5000)
                if hasattr(self.span_processor, "shutdown"):
                    self.span_processor.shutdown()

            if self.otlp_exporter and hasattr(self.otlp_exporter, "shutdown"):
                # Shutdown the OTLP exporter
                self.otlp_exporter.shutdown()

            if self.tracer_provider and hasattr(self.tracer_provider, "shutdown"):
                # Shutdown the tracer provider
                self.tracer_provider.shutdown()

            logger.info("OpenTelemetry resources cleaned up successfully")
        except Exception as e:
            logger.warning("Error cleaning up OpenTelemetry resources", error=str(e))


def configure_structured_logging() -> None:
    """Configure structured logging with consistent format."""
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
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Initialize logging and service container
configure_structured_logging()
logger = structlog.get_logger()
services = ServiceContainer()


@asynccontextmanager
async def application_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager with proper resource management."""
    await services.initialize_services()
    services.instrument_app(_app)
    yield
    await services.cleanup_services_async()


def create_application() -> FastAPI:
    """Factory function to create FastAPI application with proper configuration."""
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=application_lifespan,
        root_path="/api/genai",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_application()


# Dependency injection helpers
def get_ingestion_service() -> ContributionsIngestionService:
    """Get the contributions ingestion service instance."""
    if services.ingestion_service is None:
        ensure_services_initialized()

    if services.ingestion_service is None:
        raise HTTPException(status_code=503, detail=SERVICE_NOT_INITIALIZED)
    return services.ingestion_service


def get_qa_service() -> QuestionAnsweringService:
    """Get the question answering service instance."""
    if services.qa_service is None:
        ensure_services_initialized()

    if services.qa_service is None:
        raise HTTPException(status_code=503, detail=SERVICE_NOT_INITIALIZED)
    return services.qa_service


def get_summary_service() -> SummaryService:
    """Get the summary service instance."""
    if services.summary_service is None:
        ensure_services_initialized()

    if services.summary_service is None:
        raise HTTPException(status_code=503, detail=SERVICE_NOT_INITIALIZED)
    return services.summary_service


async def assess_meilisearch_health() -> str:
    """Assess Meilisearch service health status."""
    if not services.meilisearch_service:
        return "not_configured"

    try:
        health_check = await services.meilisearch_service.health_check()
        return health_check["status"]
    except Exception as e:
        logger.exception("Meilisearch health check failed", error=str(e))
        return "unhealthy"


def create_service_status_report() -> dict[str, str]:
    """Create a comprehensive service status report."""
    return {
        "contributions_ingestion": "ok" if services.ingestion_service else "not_initialized",
        "question_answering": "ok" if services.qa_service else "not_initialized",
        "summary_generation": "ok" if services.summary_service else "not_initialized",
        "meilisearch": "unknown",  # Will be updated by health endpoint
        "langchain": "ok",
    }


# Health and monitoring endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Enhanced health check endpoint with comprehensive service status."""
    meilisearch_status = await assess_meilisearch_health()

    services_status = create_service_status_report()
    services_status["meilisearch"] = meilisearch_status

    overall_status = "ok" if all(status in ["ok", "healthy"] for status in services_status.values()) else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(UTC),
        services=services_status,
    )


@app.get("/metrics")
async def get_prometheus_metrics() -> Response:
    """Prometheus metrics endpoint for monitoring."""
    data = generate_latest(REGISTRY).decode("utf-8")
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Contributions ingestion endpoints
@app.post("/contributions", response_model=IngestTaskResponse)
async def start_contributions_ingestion_task(
    request: ContributionsIngestRequest,
    service: ContributionsIngestionService = Depends(get_ingestion_service),
) -> IngestTaskResponse:
    """Start an asynchronous ingestion task for GitHub contributions."""
    try:
        logger.info(
            "Starting contributions ingestion task",
            user=request.user,
            week=request.week,
            repository=request.repository,
            contributions_count=len(request.contributions),
        )

        result = await service.start_ingestion_task(request)

        logger.info(
            "Contributions ingestion task started",
            task_id=result.task_id,
            user=result.user,
            week=result.week,
            repository=result.repository,
            total_contributions=result.total_contributions,
        )

        return result

    except Exception as e:
        logger.exception(
            "Failed to start contributions ingestion task",
            user=request.user,
            week=request.week,
            repository=request.repository,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"{INGESTION_TASK_FAILED}: {e!s}")


@app.get("/ingest/{task_id}", response_model=IngestTaskStatus)
async def get_ingestion_task_status(
    task_id: str = Path(..., description="Task ID returned from POST /contributions"),
    service: ContributionsIngestionService = Depends(get_ingestion_service),
) -> IngestTaskStatus:
    """Get the status of a contributions ingestion task."""
    try:
        result = service.get_ingestion_task_status(task_id)

        if result is None:
            raise HTTPException(status_code=404, detail=f"Ingestion task {task_id} not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get ingestion task status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {e!s}")


@app.get(
    "/users/{username}/weeks/{week_id}/contributions/status",
    response_model=ContributionsStatusResponse,
)
async def get_user_week_contributions_status(
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    service: ContributionsIngestionService = Depends(get_ingestion_service),
) -> ContributionsStatusResponse:
    """Get the status of contributions for a specific user and week."""
    try:
        result = await service.get_contributions_status(username, week_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No contributions found for user {username} in week {week_id}",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to get contributions status",
            username=username,
            week_id=week_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get contributions status: {e!s}")


# Question answering endpoints
@app.post("/users/{username}/weeks/{week_id}/questions", response_model=QuestionResponse)
async def ask_question_about_user_contributions(
    request: QuestionRequest,
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    service: QuestionAnsweringService = Depends(get_qa_service),
) -> QuestionResponse:
    """Ask a question about a user's contributions for a specific week."""
    try:
        # Validate that contributions exist for this user/week
        ingestion_service = get_ingestion_service()
        contributions_status = await ingestion_service.get_contributions_status(username, week_id)

        if contributions_status is None or contributions_status.total_contributions == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No contributions found for user {username} in week {week_id}. "
                f"Please ingest contributions first using POST /contributions",
            )

        logger.info(
            "Processing question about user contributions",
            username=username,
            week_id=week_id,
            question=request.question[:100],
        )

        result = await service.answer_question(username, week_id, request)

        logger.info(
            "Question answered successfully",
            username=username,
            week_id=week_id,
            question_id=result.question_id,
            confidence=result.confidence,
            response_time_ms=result.response_time_ms,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to answer question about user contributions",
            username=username,
            week_id=week_id,
            question=request.question[:100],
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {e!s}")


@app.get(
    "/users/{username}/weeks/{week_id}/questions/{question_id}",
    response_model=QuestionResponse,
)
async def get_question_by_id(
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    question_id: str = Path(..., description="UUIDv7 question identifier"),
    service: QuestionAnsweringService = Depends(get_qa_service),
) -> QuestionResponse:
    """Retrieve a previously asked question and its answer by ID."""
    try:
        result = service.get_question(question_id)  # Only pass question_id parameter

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Question {question_id} not found for user {username} in week {week_id}",
            )

        # Validate that the question belongs to the specified user/week
        if result.user != username or result.week != week_id:
            raise HTTPException(
                status_code=404,
                detail=f"Question {question_id} not found for user {username} in week {week_id}",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to retrieve question",
            username=username,
            week_id=week_id,
            question_id=question_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve question: {e!s}")


@app.get("/users/{username}/weeks/{week_id}/conversations/history")
async def get_user_week_conversation_history(
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    service: QuestionAnsweringService = Depends(get_qa_service),
) -> Any:
    """Get conversation history for a user and week."""
    try:
        return service.get_conversation_history(username, week_id)

    except Exception as e:
        logger.exception(
            "Failed to get conversation history",
            username=username,
            week_id=week_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {e!s}")


@app.delete("/users/{username}/weeks/{week_id}/conversations")
async def clear_user_week_conversation(
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    service: QuestionAnsweringService = Depends(get_qa_service),
) -> dict[str, str]:
    """Clear conversation history for a user and week."""
    try:
        service.clear_conversation_history(username, week_id)
        return {"message": f"Conversation history cleared for {username} in {week_id}"}

    except Exception as e:
        logger.exception(
            "Failed to clear conversation history",
            username=username,
            week_id=week_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation history: {e!s}")


# Summary generation endpoints
@app.post("/users/{username}/weeks/{week_id}/summary", response_model=SummaryResponse)
async def generate_user_week_summary(
    request: SummaryRequest,
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    service: SummaryService = Depends(get_summary_service),
) -> SummaryResponse:
    """Generate a summary of a user's contributions for a specific week."""
    try:
        # Validate that contributions exist for this user/week
        ingestion_service = get_ingestion_service()
        contributions_status = await ingestion_service.get_contributions_status(username, week_id)

        if contributions_status is None or contributions_status.total_contributions == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No contributions found for user {username} in week {week_id}. "
                f"Please ingest contributions first using POST /contributions",
            )

        logger.info(
            "Generating summary for user contributions",
            username=username,
            week_id=week_id,
            max_detail_level=request.max_detail_level,
        )

        result = await service.generate_summary(username, week_id, request)

        logger.info(
            "Summary generated successfully",
            username=username,
            week_id=week_id,
            summary_id=result.summary_id,
            processing_time_ms=result.metadata.processing_time_ms,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to generate summary",
            username=username,
            week_id=week_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e!s}")


async def generate_streaming_summary_chunks(
    username: str, week_id: str, request: SummaryRequest, service: SummaryService
) -> AsyncGenerator[str, None]:
    """Generate streaming summary chunks as Server-Sent Events."""
    try:
        async for chunk in service.generate_summary_stream(username, week_id, request):
            chunk_data = chunk.model_dump(mode="json")  # Ensure JSON serialization
            yield f"data: {json.dumps(chunk_data)}\n\n"
    except Exception as e:
        logger.exception(
            "Streaming summary generation failed",
            username=username,
            week_id=week_id,
            error=str(e),
        )
        error_chunk = SummaryChunk(chunk_type="error", content=f"{SUMMARY_GENERATION_FAILED}: {e!s}")
        yield f"data: {json.dumps(error_chunk.model_dump(mode='json'))}\n\n"


@app.post("/users/{username}/weeks/{week_id}/summary/stream")
async def generate_user_week_summary_stream(
    request: SummaryRequest,
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    service: SummaryService = Depends(get_summary_service),
) -> StreamingResponse:
    """Generate a streaming summary of a user's contributions using Server-Sent Events."""
    # Validate that contributions exist for this user/week
    ingestion_service = get_ingestion_service()
    contributions_status = await ingestion_service.get_contributions_status(username, week_id)

    if contributions_status is None or contributions_status.total_contributions == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No contributions found for user {username} in week {week_id}. "
            f"Please ingest contributions first using POST /contributions",
        )

    logger.info(
        "Starting streaming summary generation",
        username=username,
        week_id=week_id,
        max_detail_level=request.max_detail_level,
    )

    return StreamingResponse(
        generate_streaming_summary_chunks(username, week_id, request, service),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get(
    "/users/{username}/weeks/{week_id}/summaries/{summary_id}",
    response_model=SummaryResponse,
)
async def get_summary_by_id(
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
    summary_id: str = Path(..., description="UUIDv7 summary identifier"),
    service: SummaryService = Depends(get_summary_service),
) -> SummaryResponse:
    """Retrieve a previously generated summary by ID."""
    try:
        result = service.get_summary(summary_id)  # Only pass summary_id parameter

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Summary {summary_id} not found for user {username} in week {week_id}",
            )

        # Validate that the summary belongs to the specified user/week
        if result.user != username or result.week != week_id:
            raise HTTPException(
                status_code=404,
                detail=f"Summary {summary_id} not found for user {username} in week {week_id}",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to retrieve summary",
            username=username,
            week_id=week_id,
            summary_id=summary_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {e!s}")


# API documentation endpoints
@app.get("/openapi.json", include_in_schema=False, response_class=JSONResponse)
async def get_openapi_documentation() -> JSONResponse:
    """OpenAPI JSON schema endpoint."""
    return JSONResponse(app.openapi())


@app.get("/reference", include_in_schema=False, response_class=HTMLResponse)
async def get_api_reference() -> str:
    return """
    <!doctype html>
    <html>
      <head>
        <title>Prompteus GenAI API Documentation</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          body { margin: 0; padding: 20px; }
        </style>
      </head>
      <body>
        <script
          id="api-reference"
          data-url="/openapi.json"
          data-configuration='{
            "theme": "purple",
            "layout": "modern",
            "defaultHttpClient": {
              "targetKey": "python",
              "clientKey": "requests"
            }
          }'>
        </script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
      </body>
    </html>
    """


# Exception handlers
@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail, timestamp=datetime.now(UTC)).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with proper logging."""
    logger.error("Unhandled exception in API endpoint", error=str(exc), endpoint=str(request.url))

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred. Please try again later.",
            timestamp=datetime.now(UTC),
        ).model_dump(mode="json"),
    )


# Fallback initialization for TestClient usage
def ensure_services_initialized() -> None:
    """Ensure services are initialized - fallback for TestClient usage."""
    if services.meilisearch_service is None or services.ingestion_service is None:
        import asyncio

        # Use existing event loop if available, otherwise create new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, schedule the coroutine
                asyncio.create_task(services.initialize_services())
            else:
                loop.run_until_complete(services.initialize_services())
        except RuntimeError:
            # No event loop, create one
            asyncio.run(services.initialize_services())


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GENAI_PORT", 3003))
    uvicorn.run(app, host="0.0.0.0", port=port)
