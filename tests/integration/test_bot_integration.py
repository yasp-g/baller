import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
import discord
from src.bot.client import BallerBot
from src.bot.commands import BallerCommands
from src.api.sports import FootballAPI
from src.api.llm import LLMClient

@pytest.mark.asyncio
class TestBotIntegration:
    """Integration tests for the Discord bot with its components"""
    
    @pytest.fixture
    async def bot_instance(self, mock_preferences_manager):
        """Create a bot instance with mocked discord client but real components"""
        with patch("discord.ext.commands.Bot.start", AsyncMock()), \
             patch("discord.ext.commands.Bot.add_cog", side_effect=lambda cog: None), \
             patch.object(discord.ext.commands.Bot, "user", new_callable=PropertyMock) as mock_user_prop, \
             patch("src.bot.commands.UserPreferencesManager", return_value=mock_preferences_manager):
            
            # Create bot
            bot = BallerBot()
            
            # Set up mock user
            mock_user = MagicMock()
            mock_user.id = 123456789
            mock_user.name = "TestBot"
            mock_user.discriminator = "1234"
            mock_user_prop.return_value = mock_user
            
            # Mock the loop properly
            bot.loop = AsyncMock()
            bot.loop.create_task = MagicMock()
            
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
        
        # Verify user property was mocked correctly
        assert bot_instance.user.name == "TestBot"
        assert bot_instance.user.id == 123456789
    
    async def test_commands_registration_and_api_integration(self, cog_instance, sample_standings_data):
        """Test that the commands cog properly integrates with APIs"""
        # Setup mock API responses
        cog_instance._mock_football_api.get_standings = AsyncMock(return_value=sample_standings_data)
        cog_instance._mock_llm_client.generate_response = AsyncMock(return_value="Test LLM response")
        
        # Create a mock context
        ctx = MagicMock()
        ctx.send = AsyncMock()
        
        # Call the standings command callback directly
        await cog_instance.standings.callback(cog_instance, ctx, 2002)
        
        # Verify the football API was called correctly
        assert cog_instance._mock_football_api.get_standings.called
        assert cog_instance._mock_football_api.get_standings.call_args[0][0] == 2002
        
        # Verify the response was sent
        assert ctx.send.called
    
    async def test_message_to_response_flow(self, cog_instance, mock_discord_message, sample_matches_data, mock_content_filter):
        """Test the full flow from message to response"""
        # Setup mock API responses
        cog_instance._mock_football_api.get_matches = AsyncMock(return_value=sample_matches_data)
        cog_instance._mock_llm_client.generate_response = AsyncMock(return_value="Here are the upcoming matches")
        
        # Setup message with match-related content
        mock_discord_message.content = "What matches are happening this week?"
        
        # Setup content filter to return relevant
        mock_content_filter.is_relevant = AsyncMock(return_value=(True, "About football"))
        cog_instance.content_filter = mock_content_filter
        
        # Process the message
        await cog_instance.process_conversation(mock_discord_message, mock_discord_message.content)
        
        # Verify content filter was called
        assert mock_content_filter.is_relevant.called
        
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
    
    async def test_api_component_registration(self):
        """Test that API components are properly registered with each other"""
        # Setup mocks for the API components
        mock_football_api = MagicMock(spec=FootballAPI)
        mock_llm = MagicMock(spec=LLMClient)
        mock_bot = MagicMock()
        
        # Configure user property for the bot
        mock_bot.user = MagicMock()
        mock_bot.user.id = 123456789
        mock_bot.loop = MagicMock()
        mock_bot.loop.create_task = MagicMock()
        
        # Patch config to include aws_enabled
        with patch("src.config.config.AWS_ENABLED", False), \
             patch("src.config.config.CONVERSATION_RETENTION_DAYS", 30), \
             patch.object(FootballAPI, "__init__", return_value=None), \
             patch.object(LLMClient, "__init__", return_value=None):
             
            # Create the module objects without calling real init
            api = FootballAPI()
            llm = LLMClient()
            
            # Patch the API and LLM classes to return our mocks
            with patch("src.bot.commands.FootballAPI", return_value=mock_football_api), \
                 patch("src.bot.commands.LLMClient", return_value=mock_llm), \
                 patch("src.bot.commands.ConversationManager", return_value=MagicMock()), \
                 patch("src.bot.commands.UserPreferencesManager", return_value=MagicMock()):
                
                # Create a bot and commands cog
                commands_cog = BallerCommands(mock_bot)
                
                # The init of BallerCommands should have called these methods
                assert mock_llm.register_api.called
                assert mock_llm.register_commands.called
                
                # Verify correct registration
                assert mock_llm.register_api.call_args[0][0] is mock_football_api
                assert mock_llm.register_commands.call_args[0][0] is commands_cog