import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import time
from src.api.evaluation import (
    MetricCategory, ResponseMetric, MetricsTracker,
    create_default_metrics, EvaluationSampler
)

class TestEvaluation:
    """Test suite for response evaluation system."""
    
    def test_metrics_recording(self):
        """Test basic metrics recording and stats calculation."""
        tracker = MetricsTracker()
        
        # Create and register a test metric
        test_metric = ResponseMetric(
            metric_id="test_metric",
            category=MetricCategory.CUSTOM,
            description="Test metric"
        )
        tracker.register_metric(test_metric)
        
        # Record some values
        tracker.record("test_metric", 5.0)
        tracker.record("test_metric", 10.0)
        tracker.record("test_metric", 15.0)
        
        # Get stats
        stats = tracker.get_all_stats()
        
        # Verify
        assert "test_metric" in stats
        assert stats["test_metric"]["count"] == 3
        assert stats["test_metric"]["avg"] == 10.0
        assert stats["test_metric"]["min"] == 5.0
        assert stats["test_metric"]["max"] == 15.0
    
    def test_create_default_metrics(self):
        """Test the default metrics creation."""
        tracker = create_default_metrics()
        
        # Verify all expected default metrics are present
        assert "response_latency" in tracker.metrics
        assert "response_length" in tracker.metrics
        assert "error_rate" in tracker.metrics
        assert "relevance_score" in tracker.metrics
        assert "self_evaluation_score" in tracker.metrics
        
        # Verify categories
        assert tracker.metrics["response_latency"].category == MetricCategory.LATENCY
        assert tracker.metrics["error_rate"].category == MetricCategory.ERROR_RATE
    
    def test_category_filtering(self):
        """Test filtering metrics by category."""
        tracker = create_default_metrics()
        
        # Record some values
        tracker.record("response_latency", 0.5)
        tracker.record("error_rate", 0.0)
        
        # Get stats for just the latency category
        latency_stats = tracker.get_category_stats(MetricCategory.LATENCY)
        
        # Verify
        assert "response_latency" in latency_stats
        assert "error_rate" not in latency_stats
        
    @pytest.mark.asyncio
    async def test_evaluation_sampler(self):
        """Test the evaluation sampling system."""
        # Mock LLM client with evaluate_response method
        mock_llm = MagicMock()
        mock_llm.evaluate_response = AsyncMock(return_value={
            "OVERALL": {"score": 8.5, "justification": "Good response"}
        })
        
        # Create sampler with 100% sampling rate for testing
        sampler = EvaluationSampler(
            llm_client=mock_llm,
            sampling_rate=1.0,
            max_daily_samples=10
        )
        
        # Test evaluation
        result = await sampler.maybe_evaluate(
            user_message="Test message",
            bot_response="Test response"
        )
        
        # Verify
        assert result is not None
        assert "OVERALL" in result
        assert result["OVERALL"]["score"] == 8.5
        assert mock_llm.evaluate_response.called
        
    @pytest.mark.asyncio
    async def test_evaluation_sampling_rate(self):
        """Test the sampling rate logic."""
        # Mock LLM client
        mock_llm = MagicMock()
        mock_llm.evaluate_response = AsyncMock(return_value={})
        
        # Test with 0% sampling rate
        sampler = EvaluationSampler(
            llm_client=mock_llm,
            sampling_rate=0.0,
            max_daily_samples=10
        )
        
        # This should not trigger evaluation due to 0% rate
        result = await sampler.maybe_evaluate(
            user_message="Test message",
            bot_response="Test response"
        )
        
        # Verify no evaluation occurred
        assert result is None
        assert not mock_llm.evaluate_response.called