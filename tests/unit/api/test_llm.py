import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import time
from src.api.llm import LLMClient
from src.api.prompt_templates import ProviderType, PromptTemplate, get_template
from src.api.evaluation import MetricCategory

class TestLLMClient:
    """Test suite for the LLMClient class"""
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_metrics_recording(self, mock_openai):
        """Test that metrics are recorded during response generation."""
        # Setup mock response
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Create a mock completion
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response about football matches"
        
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Test the LLM client
        llm = LLMClient()
        await llm.generate_response("Test question")
        
        # Verify metrics were recorded
        assert "response_latency" in llm.metrics.metrics
        assert len(llm.metrics.metrics["response_latency"].values) == 1
        assert "response_length" in llm.metrics.metrics
        assert llm.metrics.metrics["response_length"].values[0] > 0
        assert "error_rate" in llm.metrics.metrics
        assert llm.metrics.metrics["error_rate"].values[0] == 0
        assert "relevance_score" in llm.metrics.metrics
        
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_evaluation(self, mock_openai):
        """Test response evaluation functionality."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Create a mock completion for the evaluation
        mock_choice = MagicMock()
        mock_choice.message.content = """
RELEVANCE: 9 - Directly addresses the user's question about match information
ACCURACY: 8 - Information appears correct but missing some details
COMPLETENESS: 7 - Covers the basic information but could provide more context
CLARITY: 9 - Very clear and well-structured response
OVERALL: 8.25 - Good quality response that meets the user's needs
"""
        
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Test evaluation
        llm = LLMClient()
        evaluation = await llm.evaluate_response(
            user_message="When is the next Arsenal match?",
            bot_response="Arsenal plays Chelsea this Saturday at 3pm at Emirates Stadium."
        )
        
        # Verify evaluation parsing
        assert "RELEVANCE" in evaluation
        assert "ACCURACY" in evaluation
        assert "OVERALL" in evaluation
        assert evaluation["OVERALL"]["score"] == 8.25
        assert "quality response" in evaluation["OVERALL"]["justification"]
        
        # Verify metric was recorded
        assert "self_evaluation_score" in llm.metrics.metrics
        assert llm.metrics.metrics["self_evaluation_score"].values[0] == 8.25
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_generate_response_basic(self, mock_openai):
        """Test basic response generation without context data"""
        # Setup mock response
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Create a mock completion object with structure matching AsyncOpenAI response
        mock_choice = MagicMock()
        mock_choice.message.content = "AI generated test response"
        
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Test the LLM client
        llm = LLMClient()
        response = await llm.generate_response("Test question")
        
        # Verify the response
        assert response == "AI generated test response"
        assert mock_client.chat.completions.create.called
        
        # Check that the right prompt was used
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args.get("messages", [])
        
        # Verify the system message contains expected football assistant instruction
        system_message = messages[0].get('content', '')
        assert "football assistant" in system_message.lower()
        
        # Verify user message contains the question
        user_message = messages[1].get('content', '')
        assert "Test question" in user_message
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_generate_response_with_data(self, mock_openai, sample_standings_data):
        """Test response generation with context data"""
        # Setup mock response
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Create a mock completion object
        mock_choice = MagicMock()
        mock_choice.message.content = "AI response with standings data"
        
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Test the LLM client with sample data
        llm = LLMClient()
        response = await llm.generate_response("Show me the Bundesliga standings", sample_standings_data)
        
        # Verify the response
        assert response == "AI response with standings data"
        
        # Check that the data was included in the completion call
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args.get("messages", [])
        user_message = messages[1].get('content', '')
        
        # Verify the user message contains data
        assert "FC Bayern München" in user_message
        assert "Bayer 04 Leverkusen" in user_message
    
    def test_register_components(self, mock_football_api):
        """Test registration of API and commands components"""
        llm = LLMClient()
        mock_commands = MagicMock()
        
        # Register components
        llm.register_api(mock_football_api)
        llm.register_commands(mock_commands)
        
        # Verify they were stored correctly
        assert llm.football_api is mock_football_api
        assert llm.commands is mock_commands
    
    def test_error_recording(self):
        """Test that errors are properly recorded and limited"""
        llm = LLMClient()
        
        # Record several API errors
        for i in range(10):  # More than the 5 error limit
            llm.record_api_error(f"Test API error {i}", f"endpoint_{i}")
        
        # Record several command errors
        for i in range(10):  # More than the 5 error limit
            llm.record_command_error(f"Test command error {i}", f"command_{i}")
        
        # Verify errors were recorded and limited to the last 5
        assert len(llm.api_errors) == 5
        assert len(llm.command_errors) == 5
        
        # Verify the most recent errors are kept
        assert "Test API error 9" in llm.api_errors[-1]["message"]
        assert "Test command error 9" in llm.command_errors[-1]["message"]
        
        # Verify the oldest errors were dropped
        for i in range(5):
            error_msg = f"Test API error {i}"
            assert not any(error_msg in err["message"] for err in llm.api_errors)
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_errors_included_in_context(self, mock_openai):
        """Test that recorded errors are included in the LLM context"""
        # Setup mock OpenAI client
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Configure the create method and its return value with proper mocking
        completion_mock = MagicMock()
        choice_mock = MagicMock()
        message_mock = MagicMock()
        
        # Build the structure: completion.choices[0].message.content
        message_mock.content = "Response with error context"
        choice_mock.message = message_mock
        completion_mock.choices = [choice_mock]
        
        # Attach the async method mock to the client
        mock_client.chat.completions.create = AsyncMock(return_value=completion_mock)
        
        # Create LLM client and record some errors
        llm = LLMClient()
        mock_api = MagicMock()
        llm.register_api(mock_api)
        
        llm.record_api_error("Failed to fetch standings", "get_standings")
        llm.record_command_error("User provided invalid competition", "standings")
        
        # Generate a response
        response = await llm.generate_response("Why can't I see the standings?")
        
        # Verify the response
        assert response == "Response with error context"
        
        # Verify method was called
        assert mock_client.chat.completions.create.called
        
        # Just check that the error information was sent in the call in some form
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        messages_str = str(call_kwargs.get("messages", []))
        
        assert "error" in messages_str.lower()
        assert "Failed to fetch standings" in messages_str
        assert "standings" in messages_str
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_generate_relevance_check(self, mock_openai):
        """Test the relevance check functionality"""
        # Setup mock OpenAI client
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Configure the create method and its return value
        mock_choice = MagicMock()
        mock_choice.message.content = "YES\nThis is about football."
        
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Test the relevance check method
        llm = LLMClient()
        response = await llm.generate_relevance_check("Tell me about the Premier League.")
        
        # Verify the response
        assert response == "YES\nThis is about football."
        assert mock_client.chat.completions.create.called
        
        # Verify correct parameters were used
        call_args = mock_client.chat.completions.create.call_args[1]
        
        # Check model and temperature
        assert call_args.get("model") == "deepseek-chat"
        assert call_args.get("temperature") == 0.1  # Should use lower temperature for more consistency
        assert call_args.get("max_tokens") == 100  # Should use fewer tokens for this simple task
        
        # Check system and user message
        messages = call_args.get("messages", [])
        system_message = messages[0].get('content', '')
        user_message = messages[1].get('content', '')
        
        # Verify system message has relevance detection instructions
        assert "relevance detection" in system_message.lower()
        assert "YES or NO" in system_message
        assert "football/soccer" in system_message
        assert "inappropriate" in system_message
        
        # Verify user message
        assert "Premier League" in user_message
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_generate_relevance_check_error_handling(self, mock_openai):
        """Test error handling in relevance check"""
        # Setup mock OpenAI client
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Configure the create method to raise an exception
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        # Test error handling
        llm = LLMClient()
        response = await llm.generate_relevance_check("Test message")
        
        # Verify the response defaults to relevant with error explanation
        assert response.startswith("YES")
        assert "error" in response.lower()
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_generate_relevance_check_empty_response(self, mock_openai):
        """Test handling empty or invalid response from LLM API"""
        # Setup mock OpenAI client with empty response
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Create a mock completion with empty choices
        mock_completion = MagicMock()
        mock_completion.choices = []
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Test the method with empty response
        llm = LLMClient()
        response = await llm.generate_relevance_check("Test message")
        
        # Should default to treating it as relevant
        assert response.startswith("YES")
        assert "default" in response.lower()
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_provider_detection(self, mock_openai):
        """Test that the client detects the right provider based on API keys."""
        # Test with Deepseek
        with patch('src.api.llm.config') as mock_config:
            mock_config.DEEPSEEK_API_KEY = "test-key"
            mock_config.ANTHROPIC_API_KEY = None
            
            llm = LLMClient()
            assert llm.provider_type == ProviderType.OPENAI
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    async def test_template_usage(self, mock_openai):
        """Test that templates are used correctly for generating prompts."""
        # Setup mock
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Create mock completion
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Template test response"
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Create client
        with patch('src.api.llm.config'):
            llm = LLMClient()
            llm.client = mock_client
            llm.provider_type = ProviderType.OPENAI
            
            # Test with football conversation template
            await llm.generate_response("Test question")
            
            # Verify template was used
            template = get_template("football_conversation")
            formatted_prompt = template.format_for_provider("Test question")
            
            # Verify call arguments
            call_args = mock_client.chat.completions.create.call_args[1]
            assert "messages" in call_args
            
            # The structure won't be exactly the same due to additional processing,
            # but the types and basic structure should match
            assert len(call_args["messages"]) == len(formatted_prompt["messages"])
            assert call_args["messages"][0]["role"] == "system"
            assert call_args["messages"][1]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_prepare_context_data(self):
        """Test that context data is properly prepared for templates."""
        llm = LLMClient()
        
        # Register mock components
        mock_api = MagicMock()
        mock_commands = MagicMock()
        llm.register_api(mock_api)
        llm.register_commands(mock_commands)
        
        # Record some errors
        llm.record_api_error("Test API error", "test_endpoint")
        llm.record_command_error("Test command error", "test_command")
        
        # Create mock user preferences
        user_prefs = {
            "followed_teams": set(["Team A", "Team B"]),
            "notification_settings": {
                "match_start": True,
                "goals": False
            }
        }
        
        # Get context data
        context = llm._prepare_context_data(user_prefs)
        
        # Verify context contents
        assert "api_context" in context
        assert "cmd_context" in context
        assert "user_pref_context" in context
        
        # Check API context
        assert "Football API is available" in context["api_context"]
        assert "Test API error" in context["api_context"]
        assert "test_endpoint" in context["api_context"]
        
        # Check command context
        assert "Discord commands are available" in context["cmd_context"]
        assert "Test command error" in context["cmd_context"]
        assert "test_command" in context["cmd_context"]
        
        # Check user preferences context
        assert "Team A" in context["user_pref_context"]
        assert "Team B" in context["user_pref_context"]
        assert "match_start: Enabled" in context["user_pref_context"]
        assert "goals: Disabled" in context["user_pref_context"]
    
    @pytest.mark.asyncio
    @patch("src.api.llm.AsyncOpenAI")
    @patch("src.api.llm.anthropic.AsyncAnthropic")
    async def test_template_provider_override(self, mock_anthropic, mock_openai):
        """Test that template provider type is overridden to match client."""
        # Setup mocks
        mock_anthropic_client = MagicMock()
        mock_anthropic.return_value = mock_anthropic_client
        
        # Create client and patch directly
        with patch('src.api.llm.LLMClient._call_provider') as mock_call_provider:
            # Set up mock return value
            mock_call_provider.return_value = "Test response"
            
            # Create client
            with patch('src.api.llm.config') as mock_config:
                mock_config.ANTHROPIC_API_KEY = "test-key"
                mock_config.DEEPSEEK_API_KEY = None
                
                # Create client - will use Anthropic due to mocked config
                llm = LLMClient()
                
                # Call method that uses templates
                await llm.generate_relevance_check("Test message")
                
                # Verify call parameters
                mock_call_provider.assert_called_once()
                template = mock_call_provider.call_args[1]["template"]
                assert template.provider_type == ProviderType.ANTHROPIC