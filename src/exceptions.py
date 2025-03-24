"""
Custom exception classes for the Baller application.

This module defines a hierarchy of custom exceptions used throughout the application
to provide consistent error handling and reporting.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BallerException(Exception):
    """Base exception for all Baller-specific exceptions."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
        
        # Log the exception with details
        log_message = f"{self.__class__.__name__}: {message}"
        if details:
            log_message += f" - Details: {details}"
        logger.error(log_message)


# API Exceptions
class APIException(BallerException):
    """Base exception for all API-related errors."""
    pass


class APIConnectionError(APIException):
    """Exception raised when connection to an API fails."""
    
    def __init__(
        self, 
        message: str = "Failed to connect to the API", 
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class APIAuthenticationError(APIException):
    """Exception raised when API authentication fails."""
    
    def __init__(
        self, 
        message: str = "API authentication failed", 
        status_code: Optional[int] = 401,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, details)


class APIRateLimitError(APIException):
    """Exception raised when API rate limit is exceeded."""
    
    def __init__(
        self, 
        message: str = "API rate limit exceeded", 
        status_code: Optional[int] = 429,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        self.retry_after = retry_after
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code, details)


class APIResourceNotFoundError(APIException):
    """Exception raised when a requested API resource is not found."""
    
    def __init__(
        self, 
        message: str = "Resource not found", 
        status_code: Optional[int] = 404,
        details: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, status_code, details)


# Bot Exceptions
class BotException(BallerException):
    """Base exception for all bot-related errors."""
    pass


class CommandError(BotException):
    """Exception raised when a command execution fails."""
    
    def __init__(
        self, 
        message: str = "Command execution failed", 
        command_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if command_name:
            details["command_name"] = command_name
        super().__init__(message, None, details)


class PermissionError(BotException):
    """Exception raised when a user doesn't have permission for an action."""
    
    def __init__(
        self, 
        message: str = "You don't have permission to use this command", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, None, details)


class ValidationError(BotException):
    """Exception raised when command input validation fails."""
    
    def __init__(
        self, 
        message: str = "Invalid input provided", 
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, None, details)


# LLM Exceptions
class LLMException(BallerException):
    """Base exception for all LLM-related errors."""
    pass


class ModelUnavailableError(LLMException):
    """Exception raised when an LLM model is unavailable."""
    
    def __init__(
        self, 
        message: str = "LLM model is currently unavailable", 
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if model_name:
            details["model_name"] = model_name
        super().__init__(message, None, details)


class PromptError(LLMException):
    """Exception raised when there is an issue with the prompt."""
    
    def __init__(
        self, 
        message: str = "Error in prompt construction or validation", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, None, details)


class ResponseError(LLMException):
    """Exception raised when there is an issue with the LLM response."""
    
    def __init__(
        self, 
        message: str = "Error processing model response", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, None, details)