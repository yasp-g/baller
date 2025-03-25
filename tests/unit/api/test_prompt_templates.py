"""Tests for the prompt_templates module."""

import pytest
from typing import Dict, Any

from src.api.prompt_templates import (
    ProviderType,
    PromptTemplate,
    FootballConversationTemplate,
    RelevanceCheckTemplate,
    get_template,
    TEMPLATES
)


class TestPromptTemplateBase:
    """Tests for the base PromptTemplate class."""
    
    class SimpleTemplate(PromptTemplate):
        """Simple template implementation for testing."""
        
        def get_system_prompt(self, **kwargs) -> str:
            return "System: " + kwargs.get("system_var", "default")
            
        def get_user_prompt(self, user_message: str, **kwargs) -> str:
            return f"User: {user_message} {kwargs.get('user_var', '')}"
    
    def test_template_initialization(self):
        """Test that template is initialized with correct properties."""
        template = self.SimpleTemplate(
            template_id="test_template",
            description="Test template",
            version="0.1",
            provider_type=ProviderType.OPENAI
        )
        
        assert template.template_id == "test_template"
        assert template.description == "Test template"
        assert template.version == "0.1"
        assert template.provider_type == ProviderType.OPENAI
    
    def test_format_for_openai(self):
        """Test formatting for OpenAI provider."""
        template = self.SimpleTemplate(
            template_id="test_template",
            description="Test template",
            provider_type=ProviderType.OPENAI
        )
        
        result = template.format_for_provider(
            user_message="Hello",
            system_var="test system",
            user_var="test user"
        )
        
        assert "messages" in result
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "system"
        assert result["messages"][0]["content"] == "System: test system"
        assert result["messages"][1]["role"] == "user"
        assert result["messages"][1]["content"] == "User: Hello test user"
    
    def test_format_for_anthropic(self):
        """Test formatting for Anthropic provider."""
        template = self.SimpleTemplate(
            template_id="test_template",
            description="Test template",
            provider_type=ProviderType.ANTHROPIC
        )
        
        result = template.format_for_provider(
            user_message="Hello",
            system_var="test system",
            user_var="test user"
        )
        
        assert "system" in result
        assert "messages" in result
        assert result["system"] == "System: test system"
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "User: Hello test user"


class TestFootballConversationTemplate:
    """Tests for the FootballConversationTemplate class."""
    
    def test_system_prompt_generation(self):
        """Test system prompt generation with various contexts."""
        template = FootballConversationTemplate()
        
        # Test with empty contexts
        basic_prompt = template.get_system_prompt()
        assert "helpful football assistant" in basic_prompt
        
        # Test with API context
        api_context = "API context test"
        prompt_with_api = template.get_system_prompt(api_context=api_context)
        assert api_context in prompt_with_api
        
        # Test with command context
        cmd_context = "Command context test"
        prompt_with_cmd = template.get_system_prompt(cmd_context=cmd_context)
        assert cmd_context in prompt_with_cmd
        
        # Test with user preferences context
        user_pref_context = "User preferences test"
        prompt_with_prefs = template.get_system_prompt(user_pref_context=user_pref_context)
        assert user_pref_context in prompt_with_prefs
        
        # Test with all contexts
        full_prompt = template.get_system_prompt(
            api_context=api_context,
            cmd_context=cmd_context,
            user_pref_context=user_pref_context
        )
        assert api_context in full_prompt
        assert cmd_context in full_prompt
        assert user_pref_context in full_prompt
    
    def test_user_prompt_generation(self):
        """Test user prompt generation with and without context data."""
        template = FootballConversationTemplate()
        
        # Test without context data
        user_message = "Who won the match yesterday?"
        basic_prompt = template.get_user_prompt(user_message)
        assert user_message in basic_prompt
        assert not basic_prompt.startswith("Here is the relevant football data")
        
        # Test with context data
        context_data = {"match": {"home": "Team A", "away": "Team B", "score": "2-1"}}
        prompt_with_context = template.get_user_prompt(user_message, context_data=context_data)
        assert "Here is the relevant football data" in prompt_with_context
        assert str(context_data) in prompt_with_context
        assert user_message in prompt_with_context


class TestRelevanceCheckTemplate:
    """Tests for the RelevanceCheckTemplate class."""
    
    def test_system_prompt(self):
        """Test system prompt for relevance checking."""
        template = RelevanceCheckTemplate()
        system_prompt = template.get_system_prompt()
        
        assert "football/soccer relevance detection" in system_prompt
        assert "YES or NO" in system_prompt
        assert "Examples of relevant topics" in system_prompt
        assert "Examples of irrelevant topics" in system_prompt
    
    def test_user_prompt(self):
        """Test user prompt for relevance checking."""
        template = RelevanceCheckTemplate()
        user_message = "Who won the World Cup?"
        
        user_prompt = template.get_user_prompt(user_message)
        assert user_prompt == user_message


class TestTemplateRegistry:
    """Tests for the template registry."""
    
    def test_get_template(self):
        """Test retrieving templates from the registry."""
        # Test getting existing templates
        football_template = get_template("football_conversation")
        assert isinstance(football_template, FootballConversationTemplate)
        
        relevance_template = get_template("relevance_check")
        assert isinstance(relevance_template, RelevanceCheckTemplate)
    
    def test_get_nonexistent_template(self):
        """Test error when trying to get a nonexistent template."""
        with pytest.raises(ValueError):
            get_template("nonexistent_template")
    
    def test_templates_registered(self):
        """Test that expected templates are in the registry."""
        assert "football_conversation" in TEMPLATES
        assert "relevance_check" in TEMPLATES