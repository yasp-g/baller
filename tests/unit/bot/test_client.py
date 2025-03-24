import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from src.bot.client import BallerBot
from src.config import config

@pytest.mark.asyncio
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
    
    @patch("discord.ext.commands.Bot.add_cog")
    @patch("src.bot.client.BallerCommands")
    async def test_setup_hook(self, mock_commands, mock_add_cog):
        """Test the setup_hook method loads the correct cogs"""
        # Create a bot with mocked methods
        bot = BallerBot()
        bot.user = MagicMock()
        
        # Call setup_hook
        await bot.setup_hook()
        
        # Verify BallerCommands cog was created and added
        assert mock_commands.called
        assert mock_add_cog.called
    
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
    
    async def test_on_ready(self):
        """Test the on_ready event handler"""
        # Create a bot with a mock user
        bot = BallerBot()
        bot.user = MagicMock()
        bot.user.name = "TestBot"
        bot.user.discriminator = "1234"
        bot.user.id = 123456789
        
        # Call the on_ready method
        await bot.on_ready()
        
        # No assertions needed - this just tests that the method runs without errors