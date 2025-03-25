"""Prompt templates for various LLM providers.

This module provides a flexible template system for creating prompts for various
LLM models, ensuring consistent formatting and best practices.
"""

import enum
from typing import Dict, Any, List, Optional, Union


class ProviderType(enum.Enum):
    """Types of LLM providers supported."""
    OPENAI = "openai"  # Includes Deepseek which uses OpenAI-compatible API
    ANTHROPIC = "anthropic"
    GENERIC = "generic"  # For future providers


class PromptTemplate:
    """Base class for all prompt templates."""
    
    def __init__(
        self,
        template_id: str,
        description: str,
        version: str = "1.0",
        provider_type: ProviderType = ProviderType.GENERIC
    ):
        """Initialize a prompt template.
        
        Args:
            template_id: Unique identifier for this template
            description: Human-readable description of template purpose
            version: Version string for tracking changes
            provider_type: The LLM provider this template is designed for
        """
        self.template_id = template_id
        self.description = description
        self.version = version
        self.provider_type = provider_type
        
    def get_system_prompt(self, **kwargs) -> str:
        """Get the system prompt with variables filled in.
        
        Args:
            **kwargs: Variables to fill in the template
            
        Returns:
            Formatted system prompt string
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_user_prompt(self, user_message: str, **kwargs) -> str:
        """Get the user prompt with context and user message.
        
        Args:
            user_message: The user's message/question
            **kwargs: Additional context variables
            
        Returns:
            Formatted user prompt string
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def format_for_provider(
        self, 
        user_message: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Format the complete prompt for the specific provider's API.
        
        Args:
            user_message: The user's message
            **kwargs: Additional context and parameters
            
        Returns:
            Dictionary containing formatted messages ready for API call
        """
        if self.provider_type == ProviderType.OPENAI:
            return {
                "messages": [
                    {
                        "role": "system",
                        "content": self.get_system_prompt(**kwargs).strip()
                    },
                    {
                        "role": "user", 
                        "content": self.get_user_prompt(user_message, **kwargs).strip()
                    }
                ]
            }
        elif self.provider_type == ProviderType.ANTHROPIC:
            return {
                "system": self.get_system_prompt(**kwargs).strip(),
                "messages": [
                    {
                        "role": "user",
                        "content": self.get_user_prompt(user_message, **kwargs).strip()
                    }
                ]
            }
        else:
            # Generic format (may need customization for other providers)
            return {
                "system_prompt": self.get_system_prompt(**kwargs).strip(),
                "user_prompt": self.get_user_prompt(user_message, **kwargs).strip()
            }


class FootballConversationTemplate(PromptTemplate):
    """Template for general football conversation responses."""
    
    def __init__(
        self,
        version: str = "1.0",
        provider_type: ProviderType = ProviderType.OPENAI
    ):
        """Initialize the football conversation template."""
        super().__init__(
            template_id="football_conversation",
            description="General template for football conversation responses",
            version=version,
            provider_type=provider_type
        )
    
    def get_system_prompt(
        self,
        api_context: str = "",
        cmd_context: str = "",
        user_pref_context: str = "",
        **kwargs
    ) -> str:
        """Get the system prompt for football conversations.
        
        Args:
            api_context: Information about API status/errors
            cmd_context: Information about command status/errors
            user_pref_context: User's preferences
            **kwargs: Additional context variables
            
        Returns:
            Formatted system prompt
        """
        return f"""
You are a helpful football assistant. You have access to football data
provided by football-data API. Respond conversationally to user queries about football matches,
leagues, teams, and players based on the data provided.

{api_context}

{cmd_context}

{user_pref_context}
"""
    
    def get_user_prompt(
        self, 
        user_message: str, 
        context_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Get the user prompt with context data.
        
        Args:
            user_message: The user's message/question
            context_data: Optional football context data
            **kwargs: Additional variables
            
        Returns:
            Formatted user prompt
        """
        context = ""
        if context_data:
            context = f"Here is the relevant football data: {context_data}\n\n"
        
        return f"{context}User question: {user_message}"


class RelevanceCheckTemplate(PromptTemplate):
    """Template for checking if content is relevant to football."""
    
    def __init__(
        self,
        version: str = "1.0",
        provider_type: ProviderType = ProviderType.OPENAI
    ):
        """Initialize the relevance check template."""
        super().__init__(
            template_id="relevance_check",
            description="Template for determining if content is relevant to football",
            version=version,
            provider_type=provider_type
        )
    
    def get_system_prompt(self, **kwargs) -> str:
        """Get the system prompt for relevance checking.
        
        Args:
            **kwargs: Additional variables (unused)
            
        Returns:
            Formatted system prompt
        """
        return """
You are a football/soccer relevance detection system. Your job is to determine if a 
user's message is relevant to football/soccer topics.

Respond with only:
YES or NO on the first line
A very brief explanation on the second line

Examples of relevant topics:
- Teams, players, matches, leagues, scores
- Football history, rules, events
- Sports statistics related to football
- Transfer news, football management 
- Football gaming (FIFA, Football Manager, etc.)

Examples of irrelevant topics:
- Other sports not related to football/soccer
- Completely unrelated topics (politics, movies, etc.)
- Personal questions not related to football
- Technical support unrelated to football
- Anything inappropriate or NSFW that may be related to football/soccer
"""
    
    def get_user_prompt(self, user_message: str, **kwargs) -> str:
        """Get the user prompt for relevance checking.
        
        Args:
            user_message: The user's message to check
            **kwargs: Additional variables (unused)
            
        Returns:
            Formatted user prompt (just the user message)
        """
        return user_message


# Template registry to store and retrieve templates
TEMPLATES = {
    "football_conversation": FootballConversationTemplate(),
    "relevance_check": RelevanceCheckTemplate(),
}


def get_template(template_id: str) -> PromptTemplate:
    """Get a prompt template by ID.
    
    Args:
        template_id: ID of the template to retrieve
        
    Returns:
        The requested template
        
    Raises:
        ValueError: If template_id is not found
    """
    if template_id not in TEMPLATES:
        raise ValueError(f"Template '{template_id}' not found")
    return TEMPLATES[template_id]