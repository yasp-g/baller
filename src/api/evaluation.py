"""
Response quality evaluation and metrics tracking.

This module provides a flexible system for measuring and tracking the quality
of LLM responses, including latency, relevance, accuracy and other metrics.
"""

import enum
import time
import random
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable

logger = logging.getLogger('baller.api.evaluation')

class MetricCategory(enum.Enum):
    RELEVANCE = "relevance"
    ACCURACY = "accuracy" 
    COHERENCE = "coherence"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    CUSTOM = "custom"

class ResponseMetric:
    """Base class for all response metrics."""
    
    def __init__(
        self,
        metric_id: str,
        category: MetricCategory,
        description: str
    ):
        self.metric_id = metric_id
        self.category = category
        self.description = description
        self.values = []
        
    def record(self, value: float) -> None:
        """Record a metric value."""
        self.values.append(value)
    
    def get_stats(self) -> Dict[str, float]:
        """Get basic statistics for this metric."""
        if not self.values:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
            
        return {
            "count": len(self.values),
            "avg": sum(self.values) / len(self.values),
            "min": min(self.values),
            "max": max(self.values)
        }

class LatencyMetric(ResponseMetric):
    """Measures response generation time."""
    
    def __init__(self):
        super().__init__(
            metric_id="response_latency",
            category=MetricCategory.LATENCY,
            description="Measures time taken to generate a response in seconds"
        )

class ResponseLengthMetric(ResponseMetric):
    """Measures response length."""
    
    def __init__(self):
        super().__init__(
            metric_id="response_length",
            category=MetricCategory.CUSTOM,
            description="Measures response length in characters"
        )

class ErrorRateMetric(ResponseMetric):
    """Tracks error rate in response generation."""
    
    def __init__(self):
        super().__init__(
            metric_id="error_rate",
            category=MetricCategory.ERROR_RATE,
            description="Tracks error rate in response generation (0=success, 1=error)"
        )

class RelevanceScoreMetric(ResponseMetric):
    """Measures content relevance score."""
    
    def __init__(self):
        super().__init__(
            metric_id="relevance_score",
            category=MetricCategory.RELEVANCE,
            description="Measures content relevance score (0-1)"
        )

class SelfEvaluationMetric(ResponseMetric):
    """Tracks LLM self-evaluation scores."""
    
    def __init__(self):
        super().__init__(
            metric_id="self_evaluation_score",
            category=MetricCategory.ACCURACY,
            description="LLM-generated quality score (0-10)"
        )

class UserFeedbackMetric(ResponseMetric):
    """Tracks user-provided feedback scores."""
    
    def __init__(self):
        super().__init__(
            metric_id="user_feedback_score",
            category=MetricCategory.CUSTOM,
            description="User-provided feedback score (1-10)"
        )

class MetricsTracker:
    """Tracks and manages multiple response metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, ResponseMetric] = {}
        
    def register_metric(self, metric: ResponseMetric) -> None:
        """Register a new metric to track."""
        self.metrics[metric.metric_id] = metric
        
    def record(self, metric_id: str, value: float) -> None:
        """Record a value for a specific metric."""
        if metric_id in self.metrics:
            self.metrics[metric_id].record(value)
        else:
            logger.warning(f"Attempted to record unknown metric: {metric_id}")
            
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all metrics."""
        return {
            metric_id: metric.get_stats() 
            for metric_id, metric in self.metrics.items()
        }
    
    def get_category_stats(self, category: MetricCategory) -> Dict[str, Dict[str, float]]:
        """Get statistics for a specific category."""
        return {
            metric_id: metric.get_stats()
            for metric_id, metric in self.metrics.items()
            if metric.category == category
        }

class EvaluationSampler:
    """Samples a percentage of responses for quality evaluation."""
    
    def __init__(self, 
                 llm_client,
                 sampling_rate: float = 0.05,  # 5% by default
                 max_daily_samples: int = 100):
        self.llm_client = llm_client
        self.sampling_rate = sampling_rate
        self.max_daily_samples = max_daily_samples
        self.daily_samples = 0
        self.last_reset_day = time.strftime("%Y-%m-%d")
        
    async def maybe_evaluate(
        self,
        user_message: str,
        bot_response: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Probabilistically decide whether to evaluate this response.
        
        Args:
            user_message: The original user message
            bot_response: The response to evaluate
            context_data: The context data used to generate the response
            
        Returns:
            Evaluation results if performed, None otherwise
        """
        # Reset counter if it's a new day
        current_day = time.strftime("%Y-%m-%d")
        if current_day != self.last_reset_day:
            self.daily_samples = 0
            self.last_reset_day = current_day
            
        # Check if we should sample this response
        if (self.daily_samples < self.max_daily_samples and 
            random.random() < self.sampling_rate):
            
            # Increment sample counter
            self.daily_samples += 1
            
            # Perform evaluation
            evaluation = await self.llm_client.evaluate_response(
                user_message=user_message,
                bot_response=bot_response,
                context_data=context_data
            )
            
            return evaluation
            
        return None

def create_default_metrics() -> MetricsTracker:
    """Create and return a tracker with the default metrics."""
    tracker = MetricsTracker()
    
    # Register all default metrics
    tracker.register_metric(LatencyMetric())
    tracker.register_metric(ResponseLengthMetric())
    tracker.register_metric(ErrorRateMetric())
    tracker.register_metric(RelevanceScoreMetric())
    tracker.register_metric(SelfEvaluationMetric())
    tracker.register_metric(UserFeedbackMetric())
    
    return tracker