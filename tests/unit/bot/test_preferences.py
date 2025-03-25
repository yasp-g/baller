import pytest
import time
from unittest.mock import MagicMock, patch
from src.bot.preferences import UserPreferencesManager
from src.config import Config

@pytest.fixture
def config_mock():
    config = MagicMock(spec=Config)
    config.AWS_ENABLED = False
    config.CONVERSATION_RETENTION_DAYS = 30
    return config

@pytest.fixture
def preferences_manager(config_mock):
    manager = UserPreferencesManager(config_mock)
    return manager

def test_user_preferences_initialization(preferences_manager):
    # Test initializing a new user's preferences
    user_id = "test_user_123"
    prefs = preferences_manager.get_user_preferences(user_id)
    
    # Verify default structure
    assert "followed_teams" in prefs
    assert isinstance(prefs["followed_teams"], set)
    assert len(prefs["followed_teams"]) == 0
    
    assert "notification_settings" in prefs
    assert "game_reminders" in prefs["notification_settings"]
    assert prefs["notification_settings"]["game_reminders"] is True
    assert "score_updates" in prefs["notification_settings"]
    assert prefs["notification_settings"]["score_updates"] is False
    
    assert "last_updated" in prefs
    assert isinstance(prefs["last_updated"], float)

def test_follow_team(preferences_manager):
    user_id = "test_user_123"
    
    # Test following a team
    result = preferences_manager.follow_team(user_id, "Arsenal")
    assert result is True
    
    # Verify team was added
    teams = preferences_manager.get_followed_teams(user_id)
    assert "Arsenal" in teams
    assert len(teams) == 1
    
    # Test following same team again (should return False)
    result = preferences_manager.follow_team(user_id, "Arsenal")
    assert result is False
    
    # Verify no duplicate
    teams = preferences_manager.get_followed_teams(user_id)
    assert len(teams) == 1
    
    # Test case insensitivity
    result = preferences_manager.follow_team(user_id, "arsenal")
    assert result is False
    
    # Test following a second team
    result = preferences_manager.follow_team(user_id, "Chelsea")
    assert result is True
    
    # Verify both teams are in the list
    teams = preferences_manager.get_followed_teams(user_id)
    assert "Arsenal" in teams
    assert "Chelsea" in teams
    assert len(teams) == 2

def test_unfollow_team(preferences_manager):
    user_id = "test_user_123"
    
    # Setup - follow some teams
    preferences_manager.follow_team(user_id, "Arsenal")
    preferences_manager.follow_team(user_id, "Chelsea")
    
    # Test unfollowing a team
    result = preferences_manager.unfollow_team(user_id, "Arsenal")
    assert result is True
    
    # Verify team was removed
    teams = preferences_manager.get_followed_teams(user_id)
    assert "Arsenal" not in teams
    assert "Chelsea" in teams
    assert len(teams) == 1
    
    # Test unfollowing a team that's not followed
    result = preferences_manager.unfollow_team(user_id, "Liverpool")
    assert result is False
    
    # Test case-insensitive unfollowing
    result = preferences_manager.unfollow_team(user_id, "chelsea")
    assert result is True
    
    # Verify all teams are unfollowed
    teams = preferences_manager.get_followed_teams(user_id)
    assert len(teams) == 0

def test_notification_settings(preferences_manager):
    user_id = "test_user_123"
    
    # Get default preferences
    prefs = preferences_manager.get_user_preferences(user_id)
    assert prefs["notification_settings"]["game_reminders"] is True
    
    # Update a notification setting
    preferences_manager.set_notification_setting(user_id, "game_reminders", False)
    
    # Verify update
    prefs = preferences_manager.get_user_preferences(user_id)
    assert prefs["notification_settings"]["game_reminders"] is False
    
    # Test updating with same value
    preferences_manager.set_notification_setting(user_id, "game_reminders", False)
    
    # Test updating other settings
    preferences_manager.set_notification_setting(user_id, "score_updates", True)
    
    # Verify all updates
    prefs = preferences_manager.get_user_preferences(user_id)
    assert prefs["notification_settings"]["game_reminders"] is False
    assert prefs["notification_settings"]["score_updates"] is True
    
    # Test invalid setting name
    with pytest.raises(ValueError):
        preferences_manager.set_notification_setting(user_id, "invalid_setting", True)

@pytest.mark.asyncio
async def test_close(preferences_manager):
    # This test just ensures the close method can be called without errors
    await preferences_manager.close()

def test_reset_preferences(preferences_manager):
    user_id = "test_user_123"
    
    # Setup - add some preferences
    preferences_manager.follow_team(user_id, "Arsenal")
    preferences_manager.set_notification_setting(user_id, "game_reminders", False)
    
    # Verify setup
    prefs = preferences_manager.get_user_preferences(user_id)
    assert "Arsenal" in prefs["followed_teams"]
    assert prefs["notification_settings"]["game_reminders"] is False
    
    # Reset preferences
    preferences_manager.reset_user_preferences(user_id)
    
    # Verify defaults after reset
    prefs = preferences_manager.get_user_preferences(user_id)
    assert len(prefs["followed_teams"]) == 0
    assert prefs["notification_settings"]["game_reminders"] is True