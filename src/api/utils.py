"""
Utility functions for API related operations.
"""

import logging
import asyncio
from functools import wraps
from typing import TypeVar, Callable, Any, Dict, Optional

from ..exceptions import APIConnectionError, APIRateLimitError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def async_retry(
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_factor: float = 2.0,
    retry_exceptions: tuple = (APIConnectionError, APIRateLimitError),
):
    """
    Decorator for retrying async functions on specific exceptions.
    
    Args:
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds
        backoff_factor: Factor to multiply backoff by after each attempt
        retry_exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            backoff = initial_backoff
            
            while True:
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    retries += 1
                    
                    # If we've used all our retries, re-raise the exception
                    if retries > max_retries:
                        logger.warning(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    # Check for a retry-after hint from the server (in seconds)
                    retry_after = getattr(e, "retry_after", None)
                    wait_time = retry_after if retry_after is not None else backoff
                    
                    # Log retry attempt
                    logger.info(
                        f"Retrying {func.__name__} in {wait_time:.2f}s "
                        f"(attempt {retries}/{max_retries}) after error: {str(e)}"
                    )
                    
                    # Wait before retrying
                    await asyncio.sleep(wait_time)
                    
                    # Increase backoff for next attempt
                    backoff *= backoff_factor
                
        return wrapper
    
    return decorator


def build_api_error_message(status_code: int, detail: Optional[str] = None) -> str:
    """
    Build a user-friendly error message based on status code.
    
    Args:
        status_code: HTTP status code
        detail: Additional error details
        
    Returns:
        User-friendly error message
    """
    base_message = {
        400: "The request was invalid. Please check your input.",
        401: "Unauthorized. Please check API credentials.",
        403: "Access forbidden. You don't have access to this resource.",
        404: "The requested resource was not found.",
        429: "Rate limit exceeded. Please try again later.",
        500: "Server error. Please try again later.",
        502: "Bad gateway. The server is temporarily unavailable.",
        503: "Service unavailable. Please try again later.",
        504: "Gateway timeout. The server took too long to respond."
    }.get(status_code, f"Error {status_code}. Something went wrong.")
    
    if detail:
        return f"{base_message} Details: {detail}"
    
    return base_message