"""Caching system for entity data (teams, competitions, players).

This module provides functionality for caching entity data to improve
performance and reduce API calls.
"""

import logging
import time
import json
import os
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from ..preferences import UserPreferencesManager

# Get logger for this module
logger = logging.getLogger('baller.intent.cache')

class EntityCache:
    """Caches entity data for quick lookup."""
    
    # Default TTL for cached items (in seconds)
    DEFAULT_TTL = 86400  # 24 hours
    
    # Cache directory
    CACHE_DIR = "cache"
    
    def __init__(self, football_api=None):
        """Initialize the entity cache.
        
        Args:
            football_api: Optional Football API client for fetching data
        """
        self.football_api = football_api
        self.teams = {}  # name -> team data
        self.teams_by_id = {}  # id -> team data
        self.competitions = {}  # name -> competition data
        self.competitions_by_id = {}  # id -> competition data
        self.cache_timestamps = {}  # entity_type -> timestamp
        self.load_event = asyncio.Event()
        self.load_event.set()  # Start as set, clear during loading
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.CACHE_DIR, exist_ok=True)
    
    async def initialize(self):
        """Initialize cache from disk or API."""
        # First try to load from disk
        cache_loaded = self._load_cache_from_disk()
        
        # If cache wasn't found or is expired, load from API
        if not cache_loaded and self.football_api:
            await self._load_cache_from_api()
    
    async def get_team(self, team_name_or_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get team data by name or ID, waiting for cache to be loaded if needed.
        
        Args:
            team_name_or_id: Team name or ID
            
        Returns:
            Team data or None if not found
        """
        # Wait for any ongoing cache load to complete
        await self.load_event.wait()
        
        if isinstance(team_name_or_id, int) or (isinstance(team_name_or_id, str) and team_name_or_id.isdigit()):
            # Look up by ID
            team_id = int(team_name_or_id)
            return self.teams_by_id.get(team_id)
        else:
            # Look up by name
            return self.teams.get(team_name_or_id)
    
    async def get_competition(self, comp_name_or_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get competition data by name or ID, waiting for cache to be loaded if needed.
        
        Args:
            comp_name_or_id: Competition name or ID
            
        Returns:
            Competition data or None if not found
        """
        # Wait for any ongoing cache load to complete
        await self.load_event.wait()
        
        if isinstance(comp_name_or_id, int) or (isinstance(comp_name_or_id, str) and comp_name_or_id.isdigit()):
            # Look up by ID
            comp_id = int(comp_name_or_id)
            return self.competitions_by_id.get(comp_id)
        else:
            # Look up by name
            return self.competitions.get(comp_name_or_id)
    
    async def load_user_followed_teams(self, preferences_manager: UserPreferencesManager, user_id: str) -> Dict[str, Any]:
        """Load team data for a user's followed teams.
        
        Args:
            preferences_manager: User preferences manager
            user_id: ID of the user
            
        Returns:
            Dict of team name -> team data for followed teams
        """
        # Wait for any ongoing cache load to complete
        await self.load_event.wait()
        
        followed_teams = preferences_manager.get_followed_teams(user_id)
        result = {}
        
        for team_name in followed_teams:
            team_data = self.teams.get(team_name)
            if team_data:
                result[team_name] = team_data
                logger.debug(f"Loaded cached data for followed team: {team_name}")
            else:
                logger.warning(f"No cached data found for followed team: {team_name}")
        
        return result
    
    def add_team(self, team_data: Dict[str, Any]):
        """Add or update a team in the cache.
        
        Args:
            team_data: Team data to cache
        """
        team_name = team_data.get("name")
        team_id = team_data.get("id")
        
        if team_name and team_id:
            self.teams[team_name] = team_data
            self.teams_by_id[team_id] = team_data
            logger.debug(f"Added team to cache: {team_name} (ID: {team_id})")
        else:
            logger.warning(f"Could not add team to cache: missing name or ID")
    
    def add_competition(self, competition_data: Dict[str, Any]):
        """Add or update a competition in the cache.
        
        Args:
            competition_data: Competition data to cache
        """
        comp_name = competition_data.get("name")
        comp_id = competition_data.get("id")
        
        if comp_name and comp_id:
            self.competitions[comp_name] = competition_data
            self.competitions_by_id[comp_id] = competition_data
            logger.debug(f"Added competition to cache: {comp_name} (ID: {comp_id})")
        else:
            logger.warning(f"Could not add competition to cache: missing name or ID")
    
    def _load_cache_from_disk(self) -> bool:
        """Load cached entities from disk.
        
        Returns:
            True if cache was loaded, False otherwise
        """
        try:
            # Try to load teams
            teams_cache_path = os.path.join(self.CACHE_DIR, "teams.json")
            if os.path.exists(teams_cache_path):
                with open(teams_cache_path, 'r') as f:
                    cache_data = json.load(f)
                    self.teams = cache_data.get("teams", {})
                    self.teams_by_id = cache_data.get("teams_by_id", {})
                    timestamp = cache_data.get("timestamp", 0)
                    
                    # Check if cache is still valid
                    if time.time() - timestamp > self.DEFAULT_TTL:
                        logger.warning("Teams cache is expired, will reload from API")
                        return False
                    
                    logger.info(f"Loaded {len(self.teams)} teams from cache")
                    
            # Try to load competitions
            comps_cache_path = os.path.join(self.CACHE_DIR, "competitions.json")
            if os.path.exists(comps_cache_path):
                with open(comps_cache_path, 'r') as f:
                    cache_data = json.load(f)
                    self.competitions = cache_data.get("competitions", {})
                    self.competitions_by_id = cache_data.get("competitions_by_id", {})
                    timestamp = cache_data.get("timestamp", 0)
                    
                    # Check if cache is still valid
                    if time.time() - timestamp > self.DEFAULT_TTL:
                        logger.warning("Competitions cache is expired, will reload from API")
                        return False
                    
                    logger.info(f"Loaded {len(self.competitions)} competitions from cache")
            
            # Check if we loaded anything
            return len(self.teams) > 0 or len(self.competitions) > 0
            
        except Exception as e:
            logger.error(f"Error loading cache from disk: {e}")
            return False
    
    async def _load_cache_from_api(self):
        """Load entity data from the API."""
        if not self.football_api:
            logger.warning("No football API client provided, cannot load from API")
            return
        
        # Mark cache as loading
        self.load_event.clear()
        
        try:
            # Load competitions
            logger.info("Loading competitions from API")
            competitions_data = await self.football_api.get_competitions()
            competitions = competitions_data.get("competitions", [])
            
            for comp in competitions:
                comp_name = comp.get("name")
                comp_id = comp.get("id")
                if comp_name and comp_id:
                    self.competitions[comp_name] = comp
                    self.competitions_by_id[comp_id] = comp
            
            logger.info(f"Loaded {len(self.competitions)} competitions from API")
            
            # Save competitions to disk
            comps_cache_path = os.path.join(self.CACHE_DIR, "competitions.json")
            with open(comps_cache_path, 'w') as f:
                json.dump({
                    "competitions": self.competitions,
                    "competitions_by_id": self.competitions_by_id,
                    "timestamp": time.time()
                }, f)
            
            # Load teams for major competitions
            logger.info("Loading teams from API for major competitions")
            for comp_id in [2021, 2014, 2002, 2019, 2015]:  # Top 5 leagues
                try:
                    teams_data = await self.football_api.get_competition_teams(comp_id)
                    teams = teams_data.get("teams", [])
                    
                    for team in teams:
                        team_name = team.get("name")
                        team_id = team.get("id")
                        if team_name and team_id:
                            self.teams[team_name] = team
                            self.teams_by_id[team_id] = team
                    
                    logger.info(f"Loaded teams for competition {comp_id}")
                    
                except Exception as e:
                    logger.error(f"Error loading teams for competition {comp_id}: {e}")
            
            logger.info(f"Loaded {len(self.teams)} teams from API")
            
            # Save teams to disk
            teams_cache_path = os.path.join(self.CACHE_DIR, "teams.json")
            with open(teams_cache_path, 'w') as f:
                json.dump({
                    "teams": self.teams,
                    "teams_by_id": self.teams_by_id,
                    "timestamp": time.time()
                }, f)
            
        except Exception as e:
            logger.error(f"Error loading entity data from API: {e}")
        finally:
            # Mark cache as loaded, even if there was an error
            self.load_event.set()