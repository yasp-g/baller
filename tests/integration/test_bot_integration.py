import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import discord
from src.bot.client import BallerBot
from src.bot.commands import BallerCommands
from src.api.sports import FootballAPI
from src.api.llm import LLMClient

@pytest.mark.asyncio
class TestBotIntegration:
    """Integration tests for the Discord bot with its components"""
    
    @pytest.fixture
    async def bot_instance(self):
        """Create a bot instance with mocked discord client but real components"""
        with patch("discord.ext.commands.Bot.start", AsyncMock()), \
             patch("discord.ext.commands.Bot.add_cog", side_effect=lambda cog: None):
            
            bot = BallerBot()
            # Mock user attribute which would normally be set after connection
            bot.user = MagicMock()
            bot.user.id = 123456789
            bot.user.name = "TestBot"
            bot.user.discriminator = "1234"
            
            # Allow setup to complete
            await bot.setup_hook()
            yield bot
    
    @pytest.fixture
    def cog_instance(self, bot_instance):
        """Create a BallerCommands instance with mocked APIs"""
        with patch("src.bot.commands.FootballAPI") as mock_football_api_cls, \
             patch("src.bot.commands.LLMClient") as mock_llm_client_cls:
            
            # Create mock instances
            mock_football_api = MagicMock()
            mock_llm_client = MagicMock()
            
            # Configure the class mocks to return our instance mocks
            mock_football_api_cls.return_value = mock_football_api
            mock_llm_client_cls.return_value = mock_llm_client
            
            # Create the cog
            cog = BallerCommands(bot_instance)
            
            # Add some useful attributes for testing
            cog._mock_football_api = mock_football_api
            cog._mock_llm_client = mock_llm_client
            
            yield cog
    
    async def test_bot_initialization(self, bot_instance):
        """Test bot initialization and cog loading"""
        # Check bot configuration
        assert bot_instance.command_prefix == "!"
        assert bot_instance.intents.message_content is True
        
        # Attempt to start the bot (with mocked connection)
        with patch("src.bot.client.config.DISCORD_TOKEN", "test-token"):
            await bot_instance.start_bot()
    
    async def test_commands_registration_and_api_integration(self, cog_instance, sample_standings_data):
        """Test that the commands cog properly integrates with APIs"""
        # Setup mock API responses
        cog_instance._mock_football_api.get_standings = AsyncMock(return_value=sample_standings_data)
        cog_instance._mock_llm_client.generate_response = AsyncMock(return_value="Test LLM response")
        
        # Create a mock context
        ctx = MagicMock()
        ctx.send = AsyncMock()
        
        # Call the standings command
        await cog_instance.standings(ctx, 2002)
        
        # Verify the football API was called correctly
        assert cog_instance._mock_football_api.get_standings.called
        assert cog_instance._mock_football_api.get_standings.call_args[1]["competition_id"] == 2002
        
        # Verify the response was sent
        assert ctx.send.called
    
    async def test_message_to_response_flow(self, cog_instance, mock_discord_message, sample_matches_data):
        """Test the full flow from message to response"""
        # Setup mock API responses
        cog_instance._mock_football_api.get_matches = AsyncMock(return_value=sample_matches_data)
        cog_instance._mock_llm_client.generate_response = AsyncMock(return_value="Here are the upcoming matches")
        
        # Setup message with match-related content
        mock_discord_message.content = "What matches are happening this week?"
        
        # Process the message
        await cog_instance.process_conversation(mock_discord_message, mock_discord_message.content)
        
        # Verify football API was called to get matches
        assert cog_instance._mock_football_api.get_matches.called
        
        # Verify LLM client was called with matches data
        assert cog_instance._mock_llm_client.generate_response.called
        call_args = cog_instance._mock_llm_client.generate_response.call_args
        assert call_args[0][0] == "What matches are happening this week?"
        assert call_args[0][1] == sample_matches_data
        
        # Verify response was sent to channel
        assert mock_discord_message.channel.send.called
        assert mock_discord_message.channel.send.call_args[0][0] == "Here are the upcoming matches"
    
    async def test_api_component_registration(self, cog_instance):
        """Test that API components are properly registered with each other"""
        # Setup a new cog with real components to test registration
        with patch.object(FootballAPI, "__init__", return_value=None), \
             patch.object(LLMClient, "__init__", return_value=None), \
             patch.object(LLMClient, "register_api") as mock_register_api, \
             patch.object(LLMClient, "register_commands") as mock_register_commands:
            
            # Create necessary attributes
            api = FootballAPI()
            api.close = AsyncMock()
            llm = LLMClient()
            
            # Mock the actual API clients
            with patch("src.bot.commands.FootballAPI", return_value=api), \
                 patch("src.bot.commands.LLMClient", return_value=llm):
                
                # Create a bot and commands cog
                bot = MagicMock()
                bot.user = MagicMock(id=123456)
                commands_cog = BallerCommands(bot)
                
                # Verify components were registered
                assert mock_register_api.called
                assert mock_register_api.call_args[0][0] is api
                
                assert mock_register_commands.called
                assert mock_register_commands.call_args[0][0] is commands_cog