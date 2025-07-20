"""Prompteus GenAI Service - FastAPI Application.

A comprehensive AI-powered service for analyzing GitHub contributions,
generating intelligent summaries, and providing interactive Q&A capabilities.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import structlog
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from src.llm_service import LLMService
from src.meilisearch import MeilisearchService
from src.metrics import initialize_service_info
from src.models import (
    ContributionsIngestRequest,
    ErrorResponse,
    HealthResponse,
    IngestTaskResponse,
    IngestTaskStatus,
    QuestionRequest,
    QuestionResponse,
)
from src.services import (
    ContributionsIngestionService,
    GitHubContentService,
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
        self.summary_service: SummaryService | None = None
        self.qa_service: QuestionAnsweringService | None = None
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

        # Initialize services first
        self.ingestion_service = ContributionsIngestionService(self.meilisearch_service)
        self.summary_service = SummaryService(self.ingestion_service)

        # Inject summary service into ingestion service to enable full workflow
        self.ingestion_service.summary_service = self.summary_service

        # Initialize metrics
        model_name = LLMService.get_current_model_name()
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
    logger.info("LLM provider configured", provider=LLMService.get_llm_provider())

    """Factory function to create FastAPI application with proper configuration."""
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=application_lifespan,
        root_path="/api/genai",
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
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


# Health and monitoring endpoints
@app.get("/health", response_model=HealthResponse, include_in_schema=False)
async def health_check() -> HealthResponse:
    """Enhanced health check endpoint with comprehensive service status."""
    meilisearch_status = await assess_meilisearch_health()

    return HealthResponse(
        status=meilisearch_status,
        timestamp=datetime.now(UTC),
    )


@app.get("/llm-info", include_in_schema=False)
async def get_llm_info() -> dict[str, Any]:
    """Get current LLM provider configuration and required environment variables."""
    provider_info = LLMService.get_provider_info()
    return {
        "current_provider": provider_info,
        "all_supported_providers": {
            "openai": {
                "required_env_vars": ["OPENAI_API_KEY"],
                "optional_env_vars": ["OPENAI_MODEL_NAME"],
                "default_model": "gpt-4o-mini",
            },
            "anthropic": {
                "required_env_vars": ["ANTHROPIC_API_KEY"],
                "optional_env_vars": ["ANTHROPIC_MODEL_NAME"],
                "default_model": "claude-3-5-sonnet-20241022",
            },
            "ollama": {
                "required_env_vars": ["OLLAMA_API_KEY", "OLLAMA_BASE_URL"],
                "optional_env_vars": ["LANGCHAIN_MODEL_NAME"],
                "default_model": "llama3.3:latest",
                "default_base_url": "https://gpu.aet.cit.tum.de/ollama",
            },
        },
    }


@app.get("/metrics", include_in_schema=False)
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
            # if given, just print the first 10 characters
            github_pat=request.github_pat[:10] if request.github_pat else "not provided",
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


# Question answering endpoints
@app.post("/users/{username}/weeks/{week_id}/questions", response_model=QuestionResponse)
async def ask_question_about_user_contributions(
    request: QuestionRequest,
    username: str = Path(..., description="GitHub username"),
    week_id: str = Path(..., description="ISO week format: 2024-W21"),
) -> QuestionResponse:
    """Ask a question about a user's contributions for a specific week."""
    try:
        pat = request.github_pat or os.getenv("GITHUB_TOKEN")
        github_content_service = GitHubContentService(pat)

        meilisearch_service = services.meilisearch_service

        if not meilisearch_service:
            raise HTTPException(status_code=503, detail="Meilisearch service not initialized")

        service = QuestionAnsweringService(github_content_service, meilisearch_service)

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
