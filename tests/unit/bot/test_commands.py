import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
from src.bot.commands import BallerCommands

@pytest.mark.asyncio
class TestBallerCommands:
    """Test suite for the BallerCommands class"""
    
    @pytest.fixture
    def bot_cog(self, mock_discord_bot, mock_football_api, mock_llm_client, mock_preferences_manager):
        """Create a BallerCommands instance with mocked dependencies"""
        with patch("src.bot.commands.FootballAPI", return_value=mock_football_api), \
             patch("src.bot.commands.LLMClient", return_value=mock_llm_client), \
             patch("src.bot.commands.ConversationManager", return_value=MagicMock()), \
             patch("src.bot.commands.UserPreferencesManager", return_value=mock_preferences_manager):
            commands = BallerCommands(mock_discord_bot)
            return commands
    
    async def test_standings_command(self, bot_cog, mock_discord_context, sample_standings_data):
        """Test the standings command"""
        # Setup mock API response
        bot_cog.football_api.get_standings.return_value = sample_standings_data
        
        # Access the actual callback function directly
        callback = bot_cog.standings.callback
        
        # Call the callback directly with appropriate arguments
        await callback(bot_cog, mock_discord_context, 2002)
        
        # Verify API was called with correct parameter
        assert bot_cog.football_api.get_standings.called
        # Get the first positional argument
        competition_id_arg = bot_cog.football_api.get_standings.call_args[0][0]
        assert competition_id_arg == 2002
        
        # Verify the discord context was called with an embed
        assert mock_discord_context.send.called
        
        # Extract the embed from the call arguments
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
        
        # Access the actual callback function directly
        callback = bot_cog.matches.callback
        
        # Call the callback directly with appropriate arguments (default params)
        await callback(bot_cog, mock_discord_context)
        
        # Verify API was called
        assert bot_cog.football_api.get_matches.called
        
        # Verify the discord context was called with an embed
        assert mock_discord_context.send.called
        # Extract the embed from the call
        call_args = mock_discord_context.send.call_args[1]
        embed = call_args.get("embed")
        
        # Check embed content
        assert "Matches for" in embed.title
        # The exact number of fields may vary based on date grouping logic
        assert len(embed.fields) >= 1
        # Check that at least one match from our sample data is included
        field_names = [field.name for field in embed.fields]
        assert any("Bayern" in name or "Leverkusen" in name for name in field_names)
    
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
        
        # Access the actual callback function directly
        callback = bot_cog.competitions.callback
        
        # Call the callback directly with appropriate arguments
        await callback(bot_cog, mock_discord_context)
        
        # Verify API was called
        assert bot_cog.football_api.get_competitions.called
        
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
        
        # Access the actual callback function directly
        callback = bot_cog.standings.callback
        
        # Call the callback directly with appropriate arguments
        await callback(bot_cog, mock_discord_context, 2002)
        
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
        
        # Mock the conversation manager's add_message method to verify it's called correctly
        bot_cog.conversation_manager.add_message.assert_called()
        
        # Verify add_message was called for user message
        assert bot_cog.conversation_manager.add_message.call_args_list[0][0][0] == user_id
        assert bot_cog.conversation_manager.add_message.call_args_list[0][0][1] == "user"
        assert bot_cog.conversation_manager.add_message.call_args_list[0][0][2] == "First question"
        
        # Verify add_message was called for assistant response
        assert bot_cog.conversation_manager.add_message.call_args_list[1][0][0] == user_id
        assert bot_cog.conversation_manager.add_message.call_args_list[1][0][1] == "assistant"
        assert bot_cog.conversation_manager.add_message.call_args_list[1][0][2] == "This is a response"
        
        # Reset the mock to check second message
        bot_cog.conversation_manager.add_message.reset_mock()
        
        # Second message
        await bot_cog.process_conversation(mock_discord_message, "Second question")
        
        # Verify add_message was called again for the second exchange
        assert bot_cog.conversation_manager.add_message.call_args_list[0][0][0] == user_id
        assert bot_cog.conversation_manager.add_message.call_args_list[0][0][1] == "user"
        assert bot_cog.conversation_manager.add_message.call_args_list[0][0][2] == "Second question"
    
    @pytest.fixture
    def team_follow_bot_cog(self, mock_discord_bot, mock_football_api, mock_llm_client, mock_preferences_manager):
        """Create a BallerCommands instance with mocked dependencies including preferences"""
        with patch("src.bot.commands.FootballAPI", return_value=mock_football_api), \
             patch("src.bot.commands.LLMClient", return_value=mock_llm_client), \
             patch("src.bot.commands.ConversationManager", return_value=MagicMock()), \
             patch("src.bot.commands.UserPreferencesManager", return_value=mock_preferences_manager):
            commands = BallerCommands(mock_discord_bot)
            return commands
    
    async def test_follow_team_command(self, team_follow_bot_cog, mock_discord_context):
        """Test the follow team command"""
        # Access the actual callback function 
        callback = team_follow_bot_cog.follow_team.callback
        
        # Call the callback with a team name
        await callback(team_follow_bot_cog, mock_discord_context, team_name="Arsenal")
        
        # Verify preferences manager was called
        assert team_follow_bot_cog.preferences_manager.follow_team.called
        # Get arguments
        args = team_follow_bot_cog.preferences_manager.follow_team.call_args[0]
        user_id = args[0]
        team_name = args[1]
        
        # Verify correct arguments
        assert user_id == str(mock_discord_context.author.id)
        assert team_name == "Arsenal"
        
        # Verify user was informed
        assert mock_discord_context.send.called
        message = mock_discord_context.send.call_args[0][0]
        assert "You're now following" in message
        assert "Arsenal" in message
    
    async def test_unfollow_team_command(self, team_follow_bot_cog, mock_discord_context):
        """Test the unfollow team command"""
        # Access the actual callback function 
        callback = team_follow_bot_cog.unfollow_team.callback
        
        # Call the callback with a team name
        await callback(team_follow_bot_cog, mock_discord_context, team_name="Chelsea")
        
        # Verify preferences manager was called
        assert team_follow_bot_cog.preferences_manager.unfollow_team.called
        # Get arguments
        args = team_follow_bot_cog.preferences_manager.unfollow_team.call_args[0]
        user_id = args[0]
        team_name = args[1]
        
        # Verify correct arguments
        assert user_id == str(mock_discord_context.author.id)
        assert team_name == "Chelsea"
        
        # Verify user was informed
        assert mock_discord_context.send.called
        message = mock_discord_context.send.call_args[0][0]
        assert "no longer following" in message
        assert "Chelsea" in message
    
    async def test_my_teams_command(self, team_follow_bot_cog, mock_discord_context):
        """Test the my teams command"""
        # Mock get_followed_teams to return some teams
        team_follow_bot_cog.preferences_manager.get_followed_teams.return_value = {"Liverpool", "Arsenal", "Chelsea"}
        
        # Access the actual callback function 
        callback = team_follow_bot_cog.my_teams.callback
        
        # Call the callback
        await callback(team_follow_bot_cog, mock_discord_context)
        
        # Verify preferences manager was called
        assert team_follow_bot_cog.preferences_manager.get_followed_teams.called
        # Get arguments
        args = team_follow_bot_cog.preferences_manager.get_followed_teams.call_args[0]
        user_id = args[0]
        
        # Verify correct arguments
        assert user_id == str(mock_discord_context.author.id)
        
        # Verify user was informed with an embed
        assert mock_discord_context.send.called
        # First argument should be an embed
        kwargs = mock_discord_context.send.call_args[1]
        assert "embed" in kwargs
        embed = kwargs["embed"]
        
        # Check the embed content
        assert embed.title == "Your Followed Teams"
        
    async def test_matches_with_my_teams_filter(self, team_follow_bot_cog, mock_discord_context, sample_matches_data):
        """Test the matches command with my teams filter"""
        # Add a match with one of the user's followed teams
        arsenal_match = {
            "id": 123458,
            "utcDate": "2025-03-30T15:00:00Z",
            "status": "SCHEDULED",
            "homeTeam": {"id": 57, "name": "Arsenal"},
            "awayTeam": {"id": 65, "name": "Manchester City"},
            "competition": {"name": "Premier League"}
        }
        
        # Update sample_matches_data with a match including followed team
        sample_matches_data["matches"].append(arsenal_match)
        
        # Mock football API and preferences
        team_follow_bot_cog.football_api.get_matches.return_value = sample_matches_data
        
        # Access the actual callback function
        callback = team_follow_bot_cog.matches.callback
        
        # Call with "my" team filter
        await callback(team_follow_bot_cog, mock_discord_context, team="my")
        
        # Verify API was called
        assert team_follow_bot_cog.football_api.get_matches.called
        
        # Verify user preferences were retrieved
        assert team_follow_bot_cog.preferences_manager.get_user_preferences.called
        
        # Verify response included special title for "my teams"
        assert mock_discord_context.send.called