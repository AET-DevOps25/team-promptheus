"""
Prometheus Metrics Configuration for Prompteus GenAI Service

This module defines all Prometheus metrics used for monitoring the GenAI service.
Metrics are organized by functional area and follow Prometheus naming conventions.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

import structlog
from prometheus_client import Counter, Gauge, Histogram, Info

logger = structlog.get_logger()

# Metric bucket definitions
DURATION_BUCKETS_FAST = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
DURATION_BUCKETS_STANDARD = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
DURATION_BUCKETS_SLOW = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
TOKEN_BUCKETS = [100, 500, 1000, 2000, 5000, 10000, 20000]
COUNT_BUCKETS_SMALL = [0, 1, 5, 10, 20, 50, 100]
COUNT_BUCKETS_LARGE = [1, 5, 10, 25, 50, 100, 250, 500]
CONFIDENCE_BUCKETS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


class SummaryGenerationMetrics:
    """Metrics for summary generation operations"""
    
    requests = Counter(
        'genai_summary_generation_requests_total',
        'Total number of summary generation requests',
        ['repository', 'username', 'status']
    )
    
    duration = Histogram(
        'genai_summary_generation_duration_seconds',
        'Time spent generating summaries',
        ['repository', 'username'],
        buckets=DURATION_BUCKETS_SLOW
    )
    
    tokens = Histogram(
        'genai_summary_generation_tokens_total',
        'Number of tokens used in summary generation',
        ['model', 'type'],  # type: input/output
        buckets=TOKEN_BUCKETS
    )


class QuestionAnsweringMetrics:
    """Metrics for question answering operations"""
    
    requests = Counter(
        'genai_question_answering_requests_total',
        'Total number of question answering requests',
        ['user', 'week', 'status']
    )
    
    duration = Histogram(
        'genai_question_answering_duration_seconds',
        'Time spent answering questions',
        ['user', 'week'],
        buckets=DURATION_BUCKETS_STANDARD
    )
    
    confidence_score = Histogram(
        'genai_question_confidence_score',
        'Confidence scores for question answers',
        ['user', 'week'],
        buckets=CONFIDENCE_BUCKETS
    )
    
    errors = Counter(
        'genai_question_answering_errors_total',
        'Total number of question answering errors',
        ['user', 'week', 'error_type']
    )


class SearchMetrics:
    """Metrics for search operations"""
    
    requests = Counter(
        'genai_search_requests_total',
        'Total number of search requests',
        ['repository', 'status']
    )
    
    duration = Histogram(
        'genai_search_duration_seconds',
        'Time spent on search operations',
        ['repository'],
        buckets=DURATION_BUCKETS_FAST
    )
    
    results_count = Histogram(
        'genai_search_results_count',
        'Number of search results returned',
        ['repository'],
        buckets=COUNT_BUCKETS_SMALL
    )


class LangChainMetrics:
    """Metrics for LangChain model operations"""
    
    requests = Counter(
        'genai_langchain_model_requests_total',
        'Total number of LangChain model requests',
        ['model', 'operation', 'status']
    )
    
    duration = Histogram(
        'genai_langchain_model_duration_seconds',
        'Time spent on LangChain model operations',
        ['model', 'operation'],
        buckets=DURATION_BUCKETS_SLOW
    )
    
    errors = Counter(
        'genai_langchain_model_errors_total',
        'Total number of LangChain model errors',
        ['model', 'operation', 'error_type']
    )


class MeilisearchMetrics:
    """Metrics for Meilisearch integration"""
    
    requests = Counter(
        'genai_meilisearch_requests_total',
        'Total number of Meilisearch requests',
        ['operation', 'status']
    )
    
    duration = Histogram(
        'genai_meilisearch_duration_seconds',
        'Time spent on Meilisearch operations',
        ['operation'],
        buckets=DURATION_BUCKETS_FAST
    )


class ContributionAnalysisMetrics:
    """Metrics for contribution analysis operations"""
    
    requests = Counter(
        'genai_contribution_analysis_requests_total',
        'Total number of contribution analysis requests',
        ['repository', 'username', 'status']
    )
    
    duration = Histogram(
        'genai_contribution_analysis_duration_seconds',
        'Time spent analyzing contributions',
        ['repository'],
        buckets=DURATION_BUCKETS_STANDARD
    )
    
    processed_count = Histogram(
        'genai_contributions_processed_count',
        'Number of contributions processed',
        ['repository', 'contribution_type'],
        buckets=COUNT_BUCKETS_LARGE
    )


class SystemHealthMetrics:
    """System health and performance metrics"""
    
    active_summaries = Gauge(
        'genai_active_summaries_count',
        'Number of active summaries in the system'
    )
    
    cache_hit_rate = Gauge(
        'genai_cache_hit_rate',
        'Cache hit rate for various operations',
        ['operation']
    )


class ServiceInfoMetrics:
    """Service information and metadata"""
    
    info = Info(
        'genai_service_info',
        'Information about the GenAI service'
    )


# Backward compatibility - expose the metrics as module-level variables
summary_generation_requests = SummaryGenerationMetrics.requests
summary_generation_duration = SummaryGenerationMetrics.duration
summary_generation_tokens = SummaryGenerationMetrics.tokens

question_answering_requests = QuestionAnsweringMetrics.requests
question_answering_duration = QuestionAnsweringMetrics.duration
question_confidence_score = QuestionAnsweringMetrics.confidence_score
question_answering_errors = QuestionAnsweringMetrics.errors

search_requests = SearchMetrics.requests
search_duration = SearchMetrics.duration
search_results_count = SearchMetrics.results_count

langchain_model_requests = LangChainMetrics.requests
langchain_model_duration = LangChainMetrics.duration
langchain_model_errors = LangChainMetrics.errors

meilisearch_requests = MeilisearchMetrics.requests
meilisearch_duration = MeilisearchMetrics.duration

contribution_analysis_requests = ContributionAnalysisMetrics.requests
contribution_analysis_duration = ContributionAnalysisMetrics.duration
contributions_processed = ContributionAnalysisMetrics.processed_count

active_summaries = SystemHealthMetrics.active_summaries
cache_hit_rate = SystemHealthMetrics.cache_hit_rate

service_info = ServiceInfoMetrics.info


class OperationTimer:
    """Decorator factory for timing operations and recording metrics"""
    
    @staticmethod
    def time_operation(metric: Histogram, labels: Optional[Dict[str, str]] = None):
        """Decorator to time operations and record metrics"""
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                return OperationTimer._create_async_wrapper(func, metric, labels)
            else:
                return OperationTimer._create_sync_wrapper(func, metric, labels)
        
        return decorator
    
    @staticmethod
    def _create_async_wrapper(func: Callable, metric: Histogram, labels: Optional[Dict[str, str]]):
        """Create async wrapper for timing operations"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                OperationTimer._record_duration(metric, labels, start_time)
                return result
            except Exception as e:
                OperationTimer._record_duration(metric, labels, start_time)
                OperationTimer._log_operation_error(func, start_time, e)
                raise
        
        return async_wrapper
    
    @staticmethod
    def _create_sync_wrapper(func: Callable, metric: Histogram, labels: Optional[Dict[str, str]]):
        """Create sync wrapper for timing operations"""
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                OperationTimer._record_duration(metric, labels, start_time)
                return result
            except Exception as e:
                OperationTimer._record_duration(metric, labels, start_time)
                OperationTimer._log_operation_error(func, start_time, e)
                raise
        
        return sync_wrapper
    
    @staticmethod
    def _record_duration(metric: Histogram, labels: Optional[Dict[str, str]], start_time: float):
        """Record the operation duration in the metric"""
        duration = time.time() - start_time
        if labels:
            metric.labels(**labels).observe(duration)
        else:
            metric.observe(duration)
    
    @staticmethod
    def _log_operation_error(func: Callable, start_time: float, error: Exception):
        """Log operation failure with timing information"""
        duration = time.time() - start_time
        logger.error("Operation failed", 
                   function=func.__name__, 
                   duration=duration, 
                   error=str(error))


class MetricsRecorder:
    """Utility class for recording metrics events"""
    
    @staticmethod
    def record_request_metrics(counter: Counter, labels: Dict[str, str], status: str = "success"):
        """Record request metrics with status"""
        labels_with_status = {**labels, 'status': status}
        counter.labels(**labels_with_status).inc()
    
    @staticmethod
    def record_error_metrics(counter: Counter, labels: Dict[str, str], error_type: str):
        """Record error metrics with error type"""
        labels_with_error = {**labels, 'error_type': error_type}
        counter.labels(**labels_with_error).inc()


def initialize_service_info(version: str, model_name: str):
    """Initialize service information metrics"""
    service_info.info({
        'version': version,
        'model_name': model_name,
        'service': 'prompteus-genai'
    })


# Legacy function aliases for backward compatibility
time_operation = OperationTimer.time_operation
record_request_metrics = MetricsRecorder.record_request_metrics
record_error_metrics = MetricsRecorder.record_error_metrics 