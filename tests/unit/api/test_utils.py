import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from src.api.utils import async_retry, build_api_error_message
from src.exceptions import APIConnectionError, APIRateLimitError

class TestAPIUtils:
    """Tests for API utility functions"""
    
    @pytest.mark.asyncio
    async def test_retry_decorator_success(self):
        """Test retry decorator with successful function execution"""
        mock_func = AsyncMock(return_value="success")
        
        # Apply decorator to mock function
        decorated_func = async_retry(max_retries=3)(mock_func)
        
        # Call function
        result = await decorated_func("arg1", kwarg1="value1")
        
        # Should be called only once since it succeeds
        assert mock_func.call_count == 1
        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    @pytest.mark.asyncio
    async def test_retry_decorator_retry_then_success(self):
        """Test retry decorator with failed execution followed by success"""
        # Create a mock that fails twice then succeeds
        mock_func = AsyncMock(side_effect=[
            APIConnectionError("Connection error"),
            APIConnectionError("Connection error"),
            "success"
        ])
        
        # Patch sleep to speed up test
        with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
            # Apply decorator
            decorated_func = async_retry(
                max_retries=3,
                initial_backoff=0.1,
                backoff_factor=2.0
            )(mock_func)
            
            # Call function
            result = await decorated_func()
            
            # Should be called 3 times (2 failures + 1 success)
            assert mock_func.call_count == 3
            assert result == "success"
            
            # Check backoff sleep times
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_await(0.1)  # First retry
            mock_sleep.assert_any_await(0.2)  # Second retry
    
    @pytest.mark.asyncio
    async def test_retry_decorator_max_retries_exceeded(self):
        """Test retry decorator when max retries is exceeded"""
        # Create a mock that always fails
        error = APIConnectionError("Connection error")
        mock_func = AsyncMock(side_effect=error)
        
        # Patch sleep to speed up test
        with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
            # Apply decorator
            decorated_func = async_retry(
                max_retries=2,
                initial_backoff=0.1
            )(mock_func)
            
            # Call function - should raise the error after retries
            with pytest.raises(APIConnectionError) as exc_info:
                await decorated_func()
            
            # Should be called 3 times (initial + 2 retries)
            assert mock_func.call_count == 3
            assert exc_info.value == error
            
            # Check backoff sleep times (2 retries)
            assert mock_sleep.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_with_rate_limit_retry_after(self):
        """Test retry with rate limit error containing retry_after value"""
        # Create a mock that fails with rate limit error then succeeds
        rate_limit_error = APIRateLimitError(
            message="Rate limit exceeded",
            retry_after=5
        )
        mock_func = AsyncMock(side_effect=[rate_limit_error, "success"])
        
        # Patch sleep to speed up test
        with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
            # Apply decorator
            decorated_func = async_retry(
                max_retries=2,
                initial_backoff=0.1
            )(mock_func)
            
            # Call function
            result = await decorated_func()
            
            # Should be called twice (failure + success)
            assert mock_func.call_count == 2
            assert result == "success"
            
            # Should use the retry_after value from the exception
            mock_sleep.assert_called_once_with(5)
    
    def test_build_api_error_message(self):
        """Test error message builder function"""
        # Test known status codes
        assert "invalid" in build_api_error_message(400).lower()
        assert "unauthorized" in build_api_error_message(401).lower()
        assert "not found" in build_api_error_message(404).lower()
        assert "rate limit" in build_api_error_message(429).lower()
        assert "server error" in build_api_error_message(500).lower()
        
        # Test unknown status code
        assert "Error 499" in build_api_error_message(499)
        
        # Test with details
        assert "Details: Something went wrong" in build_api_error_message(400, "Something went wrong")