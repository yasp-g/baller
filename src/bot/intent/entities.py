"""Entity extraction and management for intent detection.

This module provides functionality for extracting entities (teams, competitions, 
players, dates) from user messages and resolving them to their canonical forms.
"""

import re
import logging
import enum
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Union, NamedTuple

# Get logger for this module
logger = logging.getLogger('baller.intent.entities')

class EntityType(enum.Enum):
    """Types of entities that can be extracted from user messages."""
    TEAM = "team"
    COMPETITION = "competition"
    PLAYER = "player"
    DATE = "date"
    MATCHDAY = "matchday"
    TIMEFRAME = "timeframe"  # e.g., "this weekend", "next week"
    STATUS = "status"  # e.g., "scheduled", "finished"
    GROUP = "group"  # e.g., "Group A"
    STAGE = "stage"  # e.g., "QUARTER_FINAL"
    VENUE = "venue"  # e.g., "home", "away"
    SCORE = "score"  # e.g., "2-1"
    LIMIT = "limit"  # e.g., "top 5"
    UNKNOWN = "unknown"

class Entity(NamedTuple):
    """Represents an entity extracted from user input."""
    type: EntityType
    value: str  # The raw string from user input
    id: Optional[Union[int, str]] = None  # API ID if available
    confidence: float = 1.0  # How confident we are in the extraction
    start: int = -1  # Start position in original text
    end: int = -1  # End position in original text
    metadata: Dict[str, Any] = {}  # Additional data

class EntityExtractor:
    """Extracts entities from user messages."""
    
    # Competition patterns
    COMPETITION_PATTERNS = [
        # Premier League variations
        (r'\b(?:premier league|epl|english premier league)\b', 'Premier League', 2021),
        # La Liga variations
        (r'\b(?:la liga|laliga|spanish la liga)\b', 'La Liga', 2014),
        # Bundesliga variations
        (r'\b(?:bundesliga|german bundesliga)\b', 'Bundesliga', 2002),
        # Serie A variations
        (r'\b(?:serie a|italian serie a)\b', 'Serie A', 2019),
        # Ligue 1 variations
        (r'\b(?:ligue 1|french ligue 1)\b', 'Ligue 1', 2015),
        # Champions League variations
        (r'\b(?:champions league|ucl|uefa champions league)\b', 'UEFA Champions League', 2001),
        # Europa League variations
        (r'\b(?:europa league|uel|uefa europa league)\b', 'UEFA Europa League', 2146),
        # World Cup
        (r'\b(?:world cup|fifa world cup)\b', 'FIFA World Cup', 2000),
        # Generic competitions (need more context to resolve)
        (r'\b(?:competition)\b', None, None)
        # Note: We removed the "league" generic pattern as it's too broad and causes duplicate matches
    ]
    
    # Timeframe patterns
    TIMEFRAME_PATTERNS = [
        (r'\b(?:today|tonight)\b', 'today', 0),
        (r'\b(?:tomorrow)\b', 'tomorrow', 1),
        (r'\b(?:yesterday)\b', 'yesterday', -1),
        (r'\b(?:this weekend|upcoming weekend)\b', 'weekend', None),
        (r'\b(?:this week|current week)\b', 'week', None),
        (r'\b(?:next week)\b', 'next_week', None),
        (r'\b(?:next weekend)\b', 'next_weekend', None),
    ]
    
    # Status patterns
    STATUS_PATTERNS = [
        (r'\b(?:scheduled|upcoming|future)\b', 'SCHEDULED', None),
        (r'\b(?:live|ongoing|in progress)\b', 'IN_PLAY', None),
        (r'\b(?:finished|completed|past|final|full-?time)\b', 'FINISHED', None),
        (r'\b(?:postponed)\b', 'POSTPONED', None),
        (r'\b(?:canceled|cancelled)\b', 'CANCELLED', None),
    ]
    
    def __init__(self, team_cache: Dict[str, Dict[str, Any]] = None):
        """Initialize the entity extractor.
        
        Args:
            team_cache: Optional pre-loaded cache of team names to IDs and metadata
        """
        self.team_cache = team_cache or {}
        # Lowercase team names for case-insensitive matching
        self.team_names_lower = {name.lower(): name for name in self.team_cache.keys()} if team_cache else {}
    
    def extract_entities(self, text: str) -> List[Entity]:
        """Extract all entities from the given text.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            List of extracted entities
        """
        entities = []
        text_lower = text.lower()
        
        # Extract competitions
        competitions = self._extract_competitions(text, text_lower)
        entities.extend(competitions)
        
        # Extract timeframes
        timeframes = self._extract_timeframes(text, text_lower)
        entities.extend(timeframes)
        
        # Extract match statuses
        statuses = self._extract_statuses(text, text_lower)
        entities.extend(statuses)
        
        # Extract teams (if we have a team cache)
        if self.team_cache:
            teams = self._extract_teams(text, text_lower)
            entities.extend(teams)
            
        # Sort entities by their position in the text
        return sorted([e for e in entities if e.start != -1], key=lambda e: e.start)
    
    def _extract_competitions(self, text: str, text_lower: str) -> List[Entity]:
        """Extract competition entities from text."""
        entities = []
        for pattern, name, competition_id in self.COMPETITION_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                entities.append(Entity(
                    type=EntityType.COMPETITION,
                    value=name or match.group(),
                    id=competition_id,
                    confidence=0.9 if competition_id else 0.7,
                    start=match.start(),
                    end=match.end()
                ))
        return entities
    
    def _extract_timeframes(self, text: str, text_lower: str) -> List[Entity]:
        """Extract timeframe entities from text."""
        entities = []
        for pattern, name, days_offset in self.TIMEFRAME_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                metadata = {}
                
                # Calculate actual dates for timeframes
                if days_offset is not None:
                    # Simple offset from today
                    target_date = date.today() + timedelta(days=days_offset)
                    metadata['date'] = target_date.isoformat()
                elif name == 'weekend':
                    # Calculate this weekend (Saturday and Sunday)
                    today = date.today()
                    days_until_saturday = (5 - today.weekday()) % 7
                    saturday = today + timedelta(days=days_until_saturday)
                    sunday = saturday + timedelta(days=1)
                    metadata['date_from'] = saturday.isoformat()
                    metadata['date_to'] = sunday.isoformat()
                elif name == 'week':
                    # Calculate this week (today to 7 days later)
                    today = date.today()
                    next_week = today + timedelta(days=7)
                    metadata['date_from'] = today.isoformat()
                    metadata['date_to'] = next_week.isoformat()
                elif name == 'next_week':
                    # Calculate next week (7 days from today to 14 days from today)
                    today = date.today()
                    next_week_start = today + timedelta(days=7)
                    next_week_end = today + timedelta(days=14)
                    metadata['date_from'] = next_week_start.isoformat()
                    metadata['date_to'] = next_week_end.isoformat()
                elif name == 'next_weekend':
                    # Calculate next weekend
                    today = date.today()
                    days_until_saturday = (5 - today.weekday()) % 7
                    if days_until_saturday == 0:  # It's already Saturday
                        days_until_saturday = 7  # Go to next Saturday
                    next_saturday = today + timedelta(days=days_until_saturday)
                    next_sunday = next_saturday + timedelta(days=1)
                    metadata['date_from'] = next_saturday.isoformat()
                    metadata['date_to'] = next_sunday.isoformat()
                
                entities.append(Entity(
                    type=EntityType.TIMEFRAME,
                    value=name,
                    id=None,
                    confidence=0.9,
                    start=match.start(),
                    end=match.end(),
                    metadata=metadata
                ))
        return entities
    
    def _extract_statuses(self, text: str, text_lower: str) -> List[Entity]:
        """Extract match status entities from text."""
        entities = []
        for pattern, status, _ in self.STATUS_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                entities.append(Entity(
                    type=EntityType.STATUS,
                    value=status,
                    id=None,
                    confidence=0.8,
                    start=match.start(),
                    end=match.end()
                ))
        return entities
    
    def _extract_teams(self, text: str, text_lower: str) -> List[Entity]:
        """Extract team entities from text using the team cache."""
        entities = []
        
        # First try exact matches with team names
        for team_name_lower, original_name in self.team_names_lower.items():
            for match in re.finditer(r'\b' + re.escape(team_name_lower) + r'\b', text_lower):
                team_data = self.team_cache[original_name]
                entities.append(Entity(
                    type=EntityType.TEAM,
                    value=original_name,
                    id=team_data.get('id'),
                    confidence=0.95,
                    start=match.start(),
                    end=match.end(),
                    metadata={"shortName": team_data.get('shortName'), 
                              "tla": team_data.get('tla')}
                ))
        
        # TODO: Add fuzzy matching for team names
        
        return entities
    
    def update_team_cache(self, teams: Dict[str, Dict[str, Any]]):
        """Update the team cache with new teams."""
        self.team_cache.update(teams)
        # Update lowercase names dictionary
        self.team_names_lower = {name.lower(): name for name in self.team_cache.keys()}