"""User preferences management for Baller bot."""

import json
import logging
import time
from typing import Dict, List, Optional, Set, Any

from src.config import Config

logger = logging.getLogger(__name__)

class UserPreferencesManager:
    """Manages user preferences including followed teams."""
    
    def __init__(self, config: Config):
        self.config = config
        self.preferences: Dict[str, Dict[str, Any]] = {}
        self.aws_enabled = config.aws_enabled
        self.ttl_days = config.conversation_retention_days  # Reuse same TTL setting
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get preferences for a specific user, loading from AWS if needed."""
        if user_id not in self.preferences:
            self._try_load_from_aws(user_id)
            # Initialize with default preferences if not found
            if user_id not in self.preferences:
                self.preferences[user_id] = {
                    "followed_teams": set(),
                    "preferred_leagues": [],
                    "notification_settings": {
                        "game_reminders": True,
                        "score_updates": False,
                    },
                    "last_updated": time.time()
                }
        
        return self.preferences[user_id]
    
    def follow_team(self, user_id: str, team_name: str) -> bool:
        """Add a team to user's followed teams.
        
        Returns:
            bool: True if team was added, False if it was already followed
        """
        prefs = self.get_user_preferences(user_id)
        
        # Convert to lowercase for case-insensitive comparison
        team_name_lower = team_name.lower()
        
        # Check if team is already followed
        if team_name_lower in {t.lower() for t in prefs["followed_teams"]}:
            return False
        
        # Add team to followed teams using original casing
        prefs["followed_teams"].add(team_name)
        prefs["last_updated"] = time.time()
        
        # Save preferences
        self._save_preferences(user_id)
        return True
    
    def unfollow_team(self, user_id: str, team_name: str) -> bool:
        """Remove a team from user's followed teams.
        
        Returns:
            bool: True if team was removed, False if it wasn't followed
        """
        prefs = self.get_user_preferences(user_id)
        
        # Find team in a case-insensitive way
        team_name_lower = team_name.lower()
        matched_team = None
        
        for team in prefs["followed_teams"]:
            if team.lower() == team_name_lower:
                matched_team = team
                break
        
        if matched_team is None:
            return False
        
        # Remove team and update
        prefs["followed_teams"].remove(matched_team)
        prefs["last_updated"] = time.time()
        
        # Save preferences
        self._save_preferences(user_id)
        return True
    
    def get_followed_teams(self, user_id: str) -> Set[str]:
        """Get the set of teams followed by a user."""
        return self.get_user_preferences(user_id)["followed_teams"]
    
    def set_notification_setting(self, user_id: str, setting: str, value: bool) -> None:
        """Update a notification setting for a user."""
        prefs = self.get_user_preferences(user_id)
        
        if setting not in prefs["notification_settings"]:
            raise ValueError(f"Unknown notification setting: {setting}")
        
        prefs["notification_settings"][setting] = value
        prefs["last_updated"] = time.time()
        
        # Save preferences
        self._save_preferences(user_id)
    
    def _save_preferences(self, user_id: str) -> None:
        """Save user preferences, both locally and to AWS if enabled."""
        # Always store locally first
        self.preferences[user_id]["last_updated"] = time.time()
        
        # Archive to AWS if enabled
        if self.aws_enabled:
            self._archive_preferences(user_id)
            
    def _archive_preferences(self, user_id: str) -> None:
        """Archive user preferences to AWS DynamoDB.
        
        This is a placeholder that will be implemented with actual AWS SDK calls.
        """
        logger.info(f"Would archive preferences for user {user_id} to AWS DynamoDB")
        # TODO: Implement actual AWS SDK call to DynamoDB
        
        # Example implementation (commented out until AWS SDK is added):
        # import boto3
        # dynamodb = boto3.resource('dynamodb')
        # table = dynamodb.Table(self.config.aws_dynamodb_table)
        # 
        # # Convert Set to List for JSON serialization
        # prefs_copy = self.preferences[user_id].copy()
        # prefs_copy["followed_teams"] = list(prefs_copy["followed_teams"])
        # 
        # # Calculate TTL timestamp
        # ttl_timestamp = int(time.time()) + (self.ttl_days * 24 * 60 * 60)
        # 
        # table.put_item(
        #     Item={
        #         'user_id': f"PREF_{user_id}",  # Different prefix from conversations
        #         'data': json.dumps(prefs_copy),
        #         'last_updated': prefs_copy["last_updated"],
        #         'ttl': ttl_timestamp
        #     }
        # )
    
    def _try_load_from_aws(self, user_id: str) -> bool:
        """Try to load user preferences from AWS DynamoDB.
        
        This is a placeholder that will be implemented with actual AWS SDK calls.
        
        Returns:
            bool: True if preferences were loaded from AWS, False otherwise
        """
        if not self.aws_enabled:
            return False
            
        logger.info(f"Would try to load preferences for user {user_id} from AWS DynamoDB")
        # TODO: Implement actual AWS SDK call to DynamoDB
        
        # Example implementation (commented out until AWS SDK is added):
        # import boto3
        # from boto3.dynamodb.conditions import Key
        # from botocore.exceptions import ClientError
        # 
        # dynamodb = boto3.resource('dynamodb')
        # table = dynamodb.Table(self.config.aws_dynamodb_table)
        # 
        # try:
        #     response = table.get_item(Key={'user_id': f"PREF_{user_id}"})
        # except ClientError as e:
        #     logger.error(f"Error loading preferences from DynamoDB: {e}")
        #     return False
        # 
        # if 'Item' in response:
        #     item = response['Item']
        #     prefs_data = json.loads(item['data'])
        #     
        #     # Convert followed_teams back to a set
        #     prefs_data["followed_teams"] = set(prefs_data["followed_teams"])
        #     
        #     self.preferences[user_id] = prefs_data
        #     return True
        
        return False
    
    def reset_user_preferences(self, user_id: str) -> None:
        """Reset a user's preferences to defaults."""
        if user_id in self.preferences:
            del self.preferences[user_id]
        
        # Also delete from AWS if enabled
        if self.aws_enabled:
            # TODO: Implement actual AWS SDK call to delete from DynamoDB
            logger.info(f"Would delete preferences for user {user_id} from AWS DynamoDB")
    
    async def close(self) -> None:
        """Close any resources used by the preferences manager."""
        # Save all preferences before closing
        for user_id in self.preferences:
            self._save_preferences(user_id)