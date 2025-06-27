"""Tests for Prometheus metrics functionality."""

import pytest

from src.metrics import (
    question_answering_duration,
    question_answering_errors,
    question_answering_requests,
    question_confidence_score,
    record_error_metrics,
    record_request_metrics,
)


class TestMetrics:
    """Test Prometheus metrics functionality."""

    def test_question_answering_metrics_labels(self) -> None:
        """Test that question answering metrics have correct labels."""
        # Test that metrics can be created with correct labels
        try:
            # This should not raise "Incorrect label names" error
            record_request_metrics(
                question_answering_requests,
                {"user": "testuser", "week": "2024-W21"},
                "success",
            )

            # Test duration metric
            question_answering_duration.labels(user="testuser", week="2024-W21").observe(1.5)

            # Test confidence metric
            question_confidence_score.labels(user="testuser", week="2024-W21").observe(0.8)

        except ValueError as e:
            if "Incorrect label names" in str(e):
                pytest.fail(f"Metrics have incorrect label configuration: {e}")
            else:
                raise

    def test_record_request_metrics_success(self) -> None:
        """Test recording successful request metrics."""
        labels = {"user": "testuser", "week": "2024-W21"}

        # Should not raise any exceptions
        record_request_metrics(question_answering_requests, labels, "success")
        record_request_metrics(question_answering_requests, labels, "started")
        record_request_metrics(question_answering_requests, labels, "error")

    def test_record_error_metrics(self) -> None:
        """Test recording error metrics."""
        labels = {"user": "testuser", "week": "2024-W21"}

        # Should not raise any exceptions
        record_error_metrics(question_answering_errors, labels, "ValueError")
        record_error_metrics(question_answering_errors, labels, "TimeoutError")

    def test_metrics_with_different_users_and_weeks(self) -> None:
        """Test metrics with various user/week combinations."""
        test_cases = [
            {"user": "alice", "week": "2024-W01"},
            {"user": "bob", "week": "2024-W52"},
            {"user": "charlie", "week": "2025-W10"},
        ]

        for labels in test_cases:
            # Should not raise "Incorrect label names" error
            record_request_metrics(question_answering_requests, labels, "success")

            question_answering_duration.labels(**labels).observe(2.0)
            question_confidence_score.labels(**labels).observe(0.9)
