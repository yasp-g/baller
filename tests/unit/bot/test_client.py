import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import discord
from src.bot.client import BallerBot
from src.config import config

class TestBallerBot:
    """Test suite for the BallerBot class"""
    
    @patch("discord.ext.commands.Bot.__init__", return_value=None)
    def test_bot_initialization(self, mock_bot_init):
        """Test that the bot is initialized with correct parameters"""
        # Initialize the bot
        bot = BallerBot()
        
        # Verify Bot.__init__ was called with expected arguments
        assert mock_bot_init.called
        call_args = mock_bot_init.call_args[1]
        
        # Check command prefix
        assert call_args["command_prefix"] == "!"
        
        # Check intents
        intents = call_args["intents"]
        assert intents.message_content is True
        assert intents.members is True
    
    @pytest.mark.asyncio
    async def test_setup_hook(self):
        """Test the setup_hook method loads the correct cogs"""
        # Create mocks for the required components
        with patch("src.bot.commands.BallerCommands", autospec=True) as mock_commands_class, \
             patch.object(discord.ext.commands.Bot, "add_cog", autospec=True) as mock_add_cog:
            
            # Create mock bot - we need to patch the init and user property
            with patch.object(discord.ext.commands.Bot, "__init__", return_value=None):
                bot = BallerBot()
                
                # Mock the user property
                mock_user = MagicMock()
                mock_user.name = "TestBot"
                
                # Use a property mock to allow setting user
                with patch.object(discord.ext.commands.Bot, "user", new_callable=PropertyMock) as mock_user_prop:
                    mock_user_prop.return_value = mock_user
                    
                    # Create a mock command instance
                    mock_commands_instance = MagicMock()
                    mock_commands_class.return_value = mock_commands_instance
                    
                    # Call setup_hook
                    await bot.setup_hook()
                    
                    # Verify the cog was added
                    assert mock_add_cog.called
    
    @pytest.mark.asyncio
    @patch("discord.ext.commands.Bot.start")
    async def test_start_bot(self, mock_start):
        """Test the start_bot method"""
        # Set up a test token
        test_token = "test-token-12345"
        with patch("src.bot.client.config.DISCORD_TOKEN", test_token):
            # Create a bot
            bot = BallerBot()
            
            # Call start_bot
            await bot.start_bot()
            
            # Verify Bot.start was called with the token
            assert mock_start.called
            assert mock_start.call_args[0][0] == test_token
    
    @pytest.mark.asyncio
    @patch("discord.ext.commands.Bot.start")
    async def test_start_bot_error(self, mock_start):
        """Test error handling in start_bot method"""
        # Make the start method raise an exception
        mock_start.side_effect = discord.errors.LoginFailure("Invalid token")
        
        # Create a bot
        bot = BallerBot()
        
        # Call start_bot and verify it raises the exception
        with pytest.raises(Exception) as exc_info:
            await bot.start_bot()
        
        # Check exception is propagated
        assert "Invalid token" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_on_ready(self):
        """Test the on_ready event handler"""
        # Set up mocks for the bot and its user attribute
        with patch.object(discord.ext.commands.Bot, "__init__", return_value=None), \
             patch("src.bot.client.logger") as mock_logger:
             
            # Create the bot
            bot = BallerBot()
            
            # Create a mock user that can be accessed via properties
            mock_user = MagicMock()
            mock_user.name = "TestBot"
            mock_user.discriminator = "1234"
            mock_user.id = 123456789
            
            # Patch the user property to return our mock
            with patch.object(discord.ext.commands.Bot, "user", new_callable=PropertyMock) as mock_user_prop:
                mock_user_prop.return_value = mock_user
                
                # Call on_ready
                await bot.on_ready()
                
                # Verify logger was called with correct information
                assert mock_logger.info.called
                
                # Collect all log messages
                log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                
                # Check for expected content in log messages
                assert any("TestBot#1234" in call for call in log_calls)
                assert any("123456789" in call for call in log_calls)