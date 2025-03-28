import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Make sure src is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Environment setup for testing
os.environ["ENV"] = "test"
os.environ["DISCORD_TOKEN"] = "test-token"
os.environ["FOOTBALL_DATA_API_KEY"] = "test-api-key"
os.environ["DEEPSEEK_API_KEY"] = "test-deepseek-key"
os.environ["AWS_ENABLED"] = "false"  # Set AWS integration to disabled for tests
os.environ["CONVERSATION_RETENTION_DAYS"] = "30"  # Set retention days

# Set up logging for tests
import logging
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_football_api():
    """Create a mock FootballAPI instance"""
    from src.api.sports import FootballAPI
    
    api = MagicMock(spec=FootballAPI)
    # Add common method mocks
    api.get_standings = AsyncMock()
    api.get_matches = AsyncMock()
    api.get_competition = AsyncMock()
    api.get_competition_matches = AsyncMock()
    api.get_competition_teams = AsyncMock()
    api.get_top_scorers = AsyncMock()
    api.get_team = AsyncMock()
    api.get_team_matches = AsyncMock()
    api.get_person = AsyncMock()
    api.get_person_matches = AsyncMock()
    api.get_match = AsyncMock()
    api.get_head_to_head = AsyncMock()
    api.close = AsyncMock()
    return api

@pytest.fixture
def mock_llm_client():
    """Create a mock LLMClient instance"""
    from src.api.llm import LLMClient
    
    llm = MagicMock(spec=LLMClient)
    llm.generate_response = AsyncMock()
    llm.generate_relevance_check = AsyncMock()
    llm.register_api = MagicMock()
    llm.register_commands = MagicMock()
    llm.record_api_error = MagicMock()
    llm.record_command_error = MagicMock()
    # Set default return for common methods
    llm.generate_response.return_value = "This is a test LLM response"
    llm.generate_relevance_check.return_value = "YES\nThis is relevant to football"
    return llm

@pytest.fixture
def mock_content_filter():
    """Create a mock ContentFilter instance"""
    from src.bot.content_filter import ContentFilter
    
    filter_mock = MagicMock(spec=ContentFilter)
    filter_mock.is_relevant = AsyncMock()
    # Default to relevant for most tests
    filter_mock.is_relevant.return_value = (True, "Relevant to football")
    return filter_mock

@pytest.fixture
def mock_preferences_manager():
    """Create a mock UserPreferencesManager instance"""
    from src.bot.preferences import UserPreferencesManager
    
    prefs = MagicMock(spec=UserPreferencesManager)
    prefs.get_user_preferences = MagicMock()
    prefs.follow_team = MagicMock()
    prefs.unfollow_team = MagicMock()
    prefs.get_followed_teams = MagicMock()
    prefs.set_notification_setting = MagicMock()
    prefs.close = AsyncMock()
    
    # Set default returns
    prefs.get_user_preferences.return_value = {
        "followed_teams": {"Arsenal", "Chelsea"},
        "notification_settings": {"game_reminders": True, "score_updates": False},
        "last_updated": 123456789.0
    }
    prefs.get_followed_teams.return_value = {"Arsenal", "Chelsea"}
    prefs.follow_team.return_value = True
    prefs.unfollow_team.return_value = True
    
    return prefs

@pytest.fixture
def mock_discord_bot():
    """Create a mock Discord Bot instance"""
    from src.bot.client import BallerBot
    
    bot = MagicMock(spec=BallerBot)
    bot.start_bot = AsyncMock()
    bot.close = AsyncMock()
    bot.user = MagicMock()
    bot.user.id = 123456789
    bot.user.name = "TestBot"
    bot.user.discriminator = "1234"
    
    # Add event loop for async tasks
    bot.loop = MagicMock()
    bot.loop.create_task = MagicMock() 
    
    return bot

@pytest.fixture
def mock_discord_context():
    """Create a mock Discord context for command testing"""
    ctx = MagicMock()
    ctx.send = AsyncMock()
    return ctx

@pytest.fixture
def mock_discord_message():
    """Create a mock Discord message"""
    import discord
    
    msg = MagicMock()
    msg.content = "test message"
    msg.author = MagicMock()
    msg.author.id = 987654321
    msg.channel = MagicMock()
    msg.channel.send = AsyncMock()
    msg.mentions = []
    # Mock Channel type
    msg.channel.__class__ = discord.TextChannel
    return msg

@pytest.fixture
def mock_discord_dm_message():
    """Create a mock Discord direct message"""
    import discord
    
    msg = MagicMock()
    msg.content = "test dm message"
    msg.author = MagicMock()
    msg.author.id = 987654321
    msg.channel = MagicMock()
    msg.channel.send = AsyncMock()
    msg.mentions = []
    # Set channel type to DMChannel
    msg.channel.__class__ = discord.DMChannel
    return msg

@pytest.fixture
def sample_standings_data():
    """Return sample standings data for testing"""
    return {
        "competition": {"name": "Bundesliga", "id": 2002},
        "standings": [{
            "stage": "REGULAR_SEASON",
            "type": "TOTAL",
            "table": [
                {
                    "position": 1,
                    "team": {"id": 5, "name": "FC Bayern München"},
                    "playedGames": 26,
                    "won": 20,
                    "draw": 2,
                    "lost": 4,
                    "points": 62
                },
                {
                    "position": 2,
                    "team": {"id": 3, "name": "Bayer 04 Leverkusen"},
                    "playedGames": 26,
                    "won": 17,
                    "draw": 5,
                    "lost": 4,
                    "points": 56
                }
            ]
        }]
    }

@pytest.fixture
def sample_matches_data():
    """Return sample matches data for testing"""
    return {
        "resultSet": {"count": 2},
        "competition": {"id": 2002, "name": "Bundesliga"},
        "matches": [
            {
                "id": 123456,
                "utcDate": "2025-03-28T19:30:00Z",
                "status": "SCHEDULED",
                "matchday": 27,
                "homeTeam": {"id": 3, "name": "Bayer 04 Leverkusen"},
                "awayTeam": {"id": 36, "name": "VfL Bochum 1848"},
                "score": {"winner": None, "fullTime": {"home": None, "away": None}}
            },
            {
                "id": 123457,
                "utcDate": "2025-03-29T14:30:00Z",
                "status": "SCHEDULED",
                "matchday": 27,
                "homeTeam": {"id": 5, "name": "FC Bayern München"},
                "awayTeam": {"id": 44, "name": "FC St. Pauli"},
                "score": {"winner": None, "fullTime": {"home": None, "away": None}}
            }
        ]
    }