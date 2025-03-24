import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
from src.bot.commands import BallerCommands

@pytest.mark.asyncio
class TestBallerCommands:
    """Test suite for the BallerCommands class"""
    
    @pytest.fixture
    def bot_cog(self, mock_discord_bot, mock_football_api, mock_llm_client):
        """Create a BallerCommands instance with mocked dependencies"""
        with patch("src.bot.commands.FootballAPI", return_value=mock_football_api), \
             patch("src.bot.commands.LLMClient", return_value=mock_llm_client):
            commands = BallerCommands(mock_discord_bot)
            return commands
    
    async def test_standings_command(self, bot_cog, mock_discord_context, sample_standings_data):
        """Test the standings command"""
        # Setup mock API response
        bot_cog.football_api.get_standings.return_value = sample_standings_data
        
        # Call the command
        await bot_cog.standings(mock_discord_context, 2002)
        
        # Verify the discord context was called with an embed
        assert mock_discord_context.send.called
        # Extract the embed from the call
        call_args = mock_discord_context.send.call_args[1]
        embed = call_args.get("embed")
        
        # Check embed content
        assert embed.title == "Bundesliga Standings"
        assert len(embed.fields) == 2  # Two teams in our sample data
        assert "FC Bayern München" in embed.fields[0].name
        assert "62" in embed.fields[0].value  # Points
    
    async def test_matches_command(self, bot_cog, mock_discord_context, sample_matches_data):
        """Test the matches command"""
        # Setup mock API response
        bot_cog.football_api.get_matches.return_value = sample_matches_data
        bot_cog.football_api.get_competition_matches.return_value = sample_matches_data
        
        # Call the command without competition ID (default flow)
        await bot_cog.matches(mock_discord_context)
        
        # Verify the discord context was called with an embed
        assert mock_discord_context.send.called
        # Extract the embed from the call
        call_args = mock_discord_context.send.call_args[1]
        embed = call_args.get("embed")
        
        # Check embed content
        assert "Matches for" in embed.title
        assert len(embed.fields) == 2  # Two matches in our sample data
        assert "Bayer 04 Leverkusen vs VfL Bochum 1848" in embed.fields[0].name
    
    async def test_competitions_command(self, bot_cog, mock_discord_context):
        """Test the competitions command"""
        # Setup mock API response
        competitions_data = {
            "count": 2,
            "competitions": [
                {"id": 2002, "name": "Bundesliga", "area": {"name": "Germany"}},
                {"id": 2021, "name": "Premier League", "area": {"name": "England"}}
            ]
        }
        bot_cog.football_api.get_competitions.return_value = competitions_data
        
        # Call the command
        await bot_cog.competitions(mock_discord_context)
        
        # Verify the discord context was called with an embed
        assert mock_discord_context.send.called
        # Extract the embed from the call
        call_args = mock_discord_context.send.call_args[1]
        embed = call_args.get("embed")
        
        # Check embed content
        assert embed.title == "Available Football Competitions"
        assert len(embed.fields) == 2
        assert "Bundesliga (Germany)" in embed.fields[0].name
    
    async def test_api_error_handling(self, bot_cog, mock_discord_context):
        """Test error handling in commands"""
        # Setup mock API to raise an exception
        error_message = "API rate limit exceeded"
        bot_cog.football_api.get_standings.side_effect = Exception(error_message)
        
        # Call the command that will trigger the error
        await bot_cog.standings(mock_discord_context, 2002)
        
        # Verify error was handled and communicated to the user
        assert mock_discord_context.send.called
        call_args = mock_discord_context.send.call_args[0]
        error_response = call_args[0]
        
        assert "Sorry" in error_response
        assert error_message in error_response
        
        # Verify error was recorded in LLM client
        assert bot_cog.llm_client.record_command_error.called
    
    async def test_process_conversation(self, bot_cog, mock_discord_message, sample_standings_data):
        """Test conversation processing with standings data"""
        # Setup mock responses
        bot_cog.football_api.get_standings.return_value = sample_standings_data
        bot_cog.llm_client.generate_response.return_value = "Here are the Bundesliga standings..."
        
        # Test processing a conversation about standings
        await bot_cog.process_conversation(mock_discord_message, "Show me the Bundesliga standings")
        
        # Verify API was called correctly
        assert bot_cog.football_api.get_standings.called
        # Verify LLM was called with the right data
        assert bot_cog.llm_client.generate_response.called
        call_args = bot_cog.llm_client.generate_response.call_args
        assert call_args[0][0] == "Show me the Bundesliga standings"
        assert call_args[0][1] == sample_standings_data
        
        # Verify response was sent to the channel
        assert mock_discord_message.channel.send.called
        response_text = mock_discord_message.channel.send.call_args[0][0]
        assert response_text == "Here are the Bundesliga standings..."
    
    async def test_process_conversation_matches(self, bot_cog, mock_discord_message, sample_matches_data):
        """Test conversation processing with matches data"""
        # Setup mock responses
        bot_cog.football_api.get_matches.return_value = sample_matches_data
        bot_cog.llm_client.generate_response.return_value = "Here are the upcoming matches..."
        
        # Test processing a conversation about matches
        await bot_cog.process_conversation(mock_discord_message, "What matches are happening this week?")
        
        # Verify API was called correctly
        assert bot_cog.football_api.get_matches.called
        # Verify LLM was called with the right data
        assert bot_cog.llm_client.generate_response.called
        call_args = bot_cog.llm_client.generate_response.call_args
        assert call_args[0][0] == "What matches are happening this week?"
        assert call_args[0][1] == sample_matches_data
        
        # Verify response was sent to the channel
        assert mock_discord_message.channel.send.called
    
    async def test_on_message_dm(self, bot_cog, mock_discord_dm_message):
        """Test on_message handler with a direct message"""
        # Replace process_conversation with a mock to verify it's called
        bot_cog.process_conversation = AsyncMock()
        
        # Call on_message with a DM
        await bot_cog.on_message(mock_discord_dm_message)
        
        # Verify process_conversation was called correctly
        assert bot_cog.process_conversation.called
        call_args = bot_cog.process_conversation.call_args
        assert call_args[0][0] == mock_discord_dm_message
        assert call_args[0][1] == "test dm message"
    
    async def test_on_message_mention(self, bot_cog, mock_discord_message):
        """Test on_message handler with a message that mentions the bot"""
        # Setup mock message with mention
        mock_discord_message.mentions = [bot_cog.bot.user]
        mock_discord_message.content = f"<@{bot_cog.bot.user.id}> Hello bot!"
        
        # Replace process_conversation with a mock
        bot_cog.process_conversation = AsyncMock()
        
        # Call on_message
        await bot_cog.on_message(mock_discord_message)
        
        # Verify process_conversation was called with mention removed
        assert bot_cog.process_conversation.called
        call_args = bot_cog.process_conversation.call_args
        assert call_args[0][0] == mock_discord_message
        assert call_args[0][1] == "Hello bot!"
    
    async def test_on_message_ignored(self, bot_cog, mock_discord_message):
        """Test that messages without mentions in regular channels are ignored"""
        # Setup message that doesn't mention the bot
        mock_discord_message.mentions = []
        mock_discord_message.content = "Just a regular message"
        
        # Replace process_conversation with a mock
        bot_cog.process_conversation = AsyncMock()
        
        # Call on_message
        await bot_cog.on_message(mock_discord_message)
        
        # Verify process_conversation was NOT called
        assert not bot_cog.process_conversation.called
    
    async def test_conversation_history(self, bot_cog, mock_discord_message):
        """Test that conversation history is properly maintained"""
        # Setup response
        bot_cog.llm_client.generate_response.return_value = "This is a response"
        user_id = str(mock_discord_message.author.id)
        
        # First message
        await bot_cog.process_conversation(mock_discord_message, "First question")
        
        # Check history is created
        assert user_id in bot_cog.conversation_history
        assert len(bot_cog.conversation_history[user_id]) == 2  # User message + bot response
        assert bot_cog.conversation_history[user_id][0]["role"] == "user"
        assert bot_cog.conversation_history[user_id][0]["content"] == "First question"
        assert bot_cog.conversation_history[user_id][1]["role"] == "assistant"
        assert bot_cog.conversation_history[user_id][1]["content"] == "This is a response"
        
        # Second message
        await bot_cog.process_conversation(mock_discord_message, "Second question")
        
        # Check history is updated
        assert len(bot_cog.conversation_history[user_id]) == 4  # Two exchanges
        assert bot_cog.conversation_history[user_id][2]["content"] == "Second question"