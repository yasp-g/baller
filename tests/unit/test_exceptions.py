import pytest
from src.exceptions import (
    BallerException,
    APIException, 
    APIConnectionError,
    APIAuthenticationError,
    APIRateLimitError,
    APIResourceNotFoundError,
    BotException,
    CommandError,
    PermissionError,
    ValidationError,
    LLMException,
    ModelUnavailableError,
    PromptError,
    ResponseError
)

class TestExceptions:
    """Tests for custom exception classes"""
    
    def test_base_exception(self):
        """Test the base BallerException class"""
        exc = BallerException("Test error message")
        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.status_code is None
        assert exc.details == {}
        
        # Test with status code and details
        exc = BallerException(
            message="Test with details", 
            status_code=500, 
            details={"source": "test", "severity": "high"}
        )
        assert exc.message == "Test with details"
        assert exc.status_code == 500
        assert exc.details == {"source": "test", "severity": "high"}
    
    def test_api_exceptions(self):
        """Test API exception hierarchy"""
        # Test connection error
        exc = APIConnectionError("Connection failed")
        assert isinstance(exc, APIException)
        assert isinstance(exc, BallerException)
        assert exc.message == "Connection failed"
        
        # Test default message
        exc = APIConnectionError()
        assert "Failed to connect to the API" in exc.message
        
        # Test authentication error
        exc = APIAuthenticationError("Auth failed")
        assert isinstance(exc, APIException)
        assert exc.status_code == 401
        
        # Test rate limit error with retry_after
        exc = APIRateLimitError(retry_after=30)
        assert exc.retry_after == 30
        assert exc.details["retry_after"] == 30
        assert exc.status_code == 429
        
        # Test resource not found error with resource info
        exc = APIResourceNotFoundError(
            resource_type="competition",
            resource_id="12345"
        )
        assert exc.details["resource_type"] == "competition"
        assert exc.details["resource_id"] == "12345"
        assert exc.status_code == 404
    
    def test_bot_exceptions(self):
        """Test bot exception hierarchy"""
        # Test command error
        exc = CommandError("Command failed", command_name="test_command")
        assert isinstance(exc, BotException)
        assert isinstance(exc, BallerException)
        assert exc.message == "Command failed"
        assert exc.details["command_name"] == "test_command"
        
        # Test permission error
        exc = PermissionError()
        assert isinstance(exc, BotException)
        assert "permission" in exc.message.lower()
        
        # Test validation error
        exc = ValidationError("Invalid input", field="user_id")
        assert isinstance(exc, BotException)
        assert exc.message == "Invalid input"
        assert exc.details["field"] == "user_id"
    
    def test_llm_exceptions(self):
        """Test LLM exception hierarchy"""
        # Test model unavailable error
        exc = ModelUnavailableError("Model offline", model_name="test-model")
        assert isinstance(exc, LLMException)
        assert isinstance(exc, BallerException)
        assert exc.message == "Model offline"
        assert exc.details["model_name"] == "test-model"
        
        # Test prompt error
        exc = PromptError()
        assert isinstance(exc, LLMException)
        assert "prompt" in exc.message.lower()
        
        # Test response error
        exc = ResponseError("Bad response")
        assert isinstance(exc, LLMException)
        assert exc.message == "Bad response"