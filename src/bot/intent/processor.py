"""Intent detection and processing system.

This module processes user messages to detect intents and extract entities,
mapping them to API resources.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import date, datetime, timedelta

from .entities import EntityExtractor, Entity, EntityType
from .context import ConversationContext
from .cache import EntityCache

# Get logger for this module
logger = logging.getLogger('baller.intent.processor')

class ApiResource:
    """Represents an API resource with its URI and required/optional parameters."""
    
    def __init__(self, 
                 uri: str, 
                 required_params: List[str] = None, 
                 optional_params: List[str] = None,
                 description: str = ""):
        """Initialize an API resource.
        
        Args:
            uri: The API URI template (e.g., "/v4/competitions/{id}/standings")
            required_params: List of required parameters
            optional_params: List of optional parameters
            description: Human-readable description of the resource
        """
        self.uri = uri
        self.required_params = required_params or []
        self.optional_params = optional_params or []
        self.description = description
    
    def matches_intent(self, intent_name: str) -> bool:
        """Check if this resource matches the given intent name.
        
        Args:
            intent_name: Intent name to check
            
        Returns:
            True if the resource matches the intent name
        """
        # Map intent names to resource URI patterns
        intent_to_uri = {
            "get_standings": "/standings",
            "get_matches": "/matches",
            "get_team": "/teams/",
            "get_team_matches": "/teams/{id}/matches",
            "get_competition": "/competitions/",
            "get_competition_matches": "/competitions/{id}/matches",
            "get_competition_teams": "/competitions/{id}/teams",
            "get_competition_scorers": "/competitions/{id}/scorers",
        }
        
        # Check if the intent maps to a URI pattern that matches this resource
        pattern = intent_to_uri.get(intent_name)
        if pattern:
            return pattern in self.uri
        
        return False

class Intent:
    """Represents a detected intent with entities and confidence score."""
    
    def __init__(self, 
                 name: str, 
                 confidence: float,
                 entities: Dict[str, Entity] = None,
                 api_resource: Optional[ApiResource] = None):
        """Initialize an intent.
        
        Args:
            name: The intent name
            confidence: Confidence score (0-1)
            entities: Dict of entity name to Entity
            api_resource: Associated API resource
        """
        self.name = name
        self.confidence = confidence
        self.entities = entities or {}
        self.api_resource = api_resource
        self.api_params = {}  # Parameters for API call
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the intent to a dict for serialization."""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "entities": {
                name: {
                    "type": entity.type.value,
                    "value": entity.value,
                    "id": entity.id,
                    "confidence": entity.confidence
                } for name, entity in self.entities.items()
            },
            "api_resource": self.api_resource.uri if self.api_resource else None,
            "api_params": self.api_params
        }
    
    def get_api_params(self) -> Dict[str, Any]:
        """Get parameters for the API call based on entities."""
        params = {}
        
        # Process entities to extract API parameters
        for entity_name, entity in self.entities.items():
            # Direct entity-to-param mappings
            if entity.type == EntityType.COMPETITION and "{id}" in self.api_resource.uri:
                params["competition_id"] = entity.id
            elif entity.type == EntityType.TEAM and "{id}" in self.api_resource.uri:
                params["team_id"] = entity.id
            elif entity.type == EntityType.STATUS:
                params["status"] = entity.value
            
            # Handle timeframes with date ranges
            if entity.type == EntityType.TIMEFRAME:
                if "date" in entity.metadata:
                    # Single date
                    date_value = entity.metadata["date"]
                    params["date_from"] = date_value
                    params["date_to"] = date_value
                elif "date_from" in entity.metadata and "date_to" in entity.metadata:
                    # Date range
                    params["date_from"] = entity.metadata["date_from"]
                    params["date_to"] = entity.metadata["date_to"]
        
        self.api_params = params
        return params

class IntentProcessor:
    """Processes user messages to detect intents and map them to API resources."""
    
    # API resources with their URIs and parameters
    API_RESOURCES = {
        "area": ApiResource(
            uri="/v4/areas/{id}",
            required_params=["id"],
            description="Information about a specific area (country/region)"
        ),
        "areas": ApiResource(
            uri="/v4/areas/",
            description="List of all available areas (countries/regions)"
        ),
        "competition": ApiResource(
            uri="/v4/competitions/{id}",
            required_params=["id"],
            description="Information about a specific competition"
        ),
        "competitions": ApiResource(
            uri="/v4/competitions/",
            optional_params=["areas"],
            description="List of all available competitions"
        ),
        "competition_standings": ApiResource(
            uri="/v4/competitions/{id}/standings",
            required_params=["id"],
            optional_params=["matchday", "season", "date"],
            description="Standings for a specific competition"
        ),
        "competition_matches": ApiResource(
            uri="/v4/competitions/{id}/matches",
            required_params=["id"],
            optional_params=["dateFrom", "dateTo", "stage", "status", "matchday", "group", "season"],
            description="Matches for a specific competition"
        ),
        "competition_teams": ApiResource(
            uri="/v4/competitions/{id}/teams",
            required_params=["id"],
            optional_params=["season"],
            description="Teams participating in a specific competition"
        ),
        "competition_scorers": ApiResource(
            uri="/v4/competitions/{id}/scorers",
            required_params=["id"],
            optional_params=["limit", "season"],
            description="Top scorers for a specific competition"
        ),
        "team": ApiResource(
            uri="/v4/teams/{id}",
            required_params=["id"],
            description="Information about a specific team"
        ),
        "teams": ApiResource(
            uri="/v4/teams/",
            optional_params=["limit", "offset"],
            description="List of teams"
        ),
        "team_matches": ApiResource(
            uri="/v4/teams/{id}/matches/",
            required_params=["id"],
            optional_params=["dateFrom", "dateTo", "season", "competitions", "status", "venue", "limit"],
            description="Matches for a specific team"
        ),
        "person": ApiResource(
            uri="/v4/persons/{id}",
            required_params=["id"],
            description="Information about a specific person (player/coach)"
        ),
        "person_matches": ApiResource(
            uri="/v4/persons/{id}/matches",
            required_params=["id"],
            optional_params=["dateFrom", "dateTo", "status", "competitions", "limit", "offset"],
            description="Matches involving a specific person (player/coach)"
        ),
        "match": ApiResource(
            uri="/v4/matches/{id}",
            required_params=["id"],
            description="Information about a specific match"
        ),
        "matches": ApiResource(
            uri="/v4/matches",
            optional_params=["competitions", "ids", "dateFrom", "dateTo", "status"],
            description="List of matches across competitions"
        ),
        "match_head2head": ApiResource(
            uri="/v4/matches/{id}/head2head",
            required_params=["id"],
            optional_params=["limit", "dateFrom", "dateTo", "competitions"],
            description="Previous encounters between teams in a match"
        )
    }
    
    # Define intent patterns
    INTENT_PATTERNS = [
        # Standings-related intents
        (r"\b(?:standing|table|position|rank|league table)\b", "get_standings"),
        
        # Match-related intents
        (r"\b(?:match(?:es)?|game(?:s)?|fixture(?:s)?|schedule|upcoming|played)\b", "get_matches"),
        
        # Specific team-related intents
        (r"\b(?:team|club|squad)\b", "get_team"),
        
        # Player-related intents
        (r"\b(?:player|squad|roster|lineup)\b", "get_team"),
        
        # Scorers-related intents
        (r"\b(?:scorer|goal scorer|top scorer|leading scorer|golden boot)\b", "get_competition_scorers"),
        
        # Head-to-head intents
        (r"\b(?:head to head|h2h|versus|vs)\b", "get_match_head2head"),
    ]
    
    def __init__(self, 
                 entity_extractor: EntityExtractor,
                 entity_cache: EntityCache = None):
        """Initialize the intent processor.
        
        Args:
            entity_extractor: Entity extractor to use
            entity_cache: Optional entity cache for lookups
        """
        self.entity_extractor = entity_extractor
        self.entity_cache = entity_cache
        self.contexts = {}  # User ID -> ConversationContext
    
    def get_or_create_context(self, user_id: str) -> ConversationContext:
        """Get or create a conversation context for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Conversation context for the user
        """
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id)
        return self.contexts[user_id]
    
    async def process_message(self, user_id: str, message: str) -> Optional[Intent]:
        """Process a user message to detect intent and entities.
        
        Args:
            user_id: User ID
            message: Message text
            
        Returns:
            Detected intent or None if no intent could be detected
        """
        logger.debug(f"Processing message for user {user_id}: {message}")
        
        # Get user context
        context = self.get_or_create_context(user_id)
        
        # Extract entities from message
        entities = self.entity_extractor.extract_entities(message)
        if entities:
            logger.debug(f"Extracted entities: {[e.type.value for e in entities]}")
            
            # Add entities to context
            context.add_entities(entities)
        
        # Detect intent
        intent = await self._detect_intent(message, entities, context)
        if intent:
            logger.info(f"Detected intent: {intent.name} with confidence {intent.confidence:.2f}")
            
            # Add intent to context
            context.add_intent(intent.name, intent.confidence, intent.entities)
            
            return intent
        
        logger.warning("No intent detected")
        return None
    
    async def _detect_intent(self, 
                      message: str, 
                      entities: List[Entity], 
                      context: ConversationContext) -> Optional[Intent]:
        """Detect the intent from a message and entities.
        
        Args:
            message: User message
            entities: Extracted entities
            context: Conversation context
            
        Returns:
            Detected intent or None
        """
        # First, try to match intent patterns
        message_lower = message.lower()
        matched_intents = []
        
        # Check for explicit patterns first - if "standings" is mentioned, it gets priority
        if "standings" in message_lower or "table" in message_lower:
            matched_intents.append(("get_standings", 0.8))  # Higher confidence for explicit mentions
        
        # Check other patterns
        for pattern, intent_name in self.INTENT_PATTERNS:
            if re.search(pattern, message_lower):
                matched_intents.append((intent_name, 0.7))  # Base confidence
        
        if not matched_intents:
            # If no patterns matched, try to infer intent from entities
            if any(e.type == EntityType.COMPETITION for e in entities):
                if any(e.type == EntityType.TEAM for e in entities):
                    matched_intents.append(("get_competition_teams", 0.6))
                else:
                    if "standing" in message_lower or "table" in message_lower:
                        matched_intents.append(("get_standings", 0.7))
                    else:
                        matched_intents.append(("get_competition", 0.6))
                        matched_intents.append(("get_standings", 0.5))
            
            elif any(e.type == EntityType.TEAM for e in entities):
                # Message has team but no explicit intent, assume team matches
                matched_intents.append(("get_team_matches", 0.6))
                matched_intents.append(("get_team", 0.5))
            
            elif any(e.type == EntityType.TIMEFRAME for e in entities):
                # Message has timeframe but no explicit intent, assume matches
                matched_intents.append(("get_matches", 0.6))
        
        if not matched_intents:
            # Still no intent, check if this is a follow-up question
            last_intent = context.get_last_intent()
            if last_intent:
                # Assume same intent but lower confidence for follow-up
                matched_intents.append((last_intent["name"], 0.4))
        
        if not matched_intents:
            # No intent detected
            return None
        
        # Sort by confidence (highest first)
        matched_intents.sort(key=lambda x: x[1], reverse=True)
        
        # Get the highest confidence intent
        intent_name, base_confidence = matched_intents[0]
        
        # Create the intent object
        intent = Intent(intent_name, base_confidence)
        
        # Map intent to API resource
        for resource_name, resource in self.API_RESOURCES.items():
            if resource.matches_intent(intent_name):
                intent.api_resource = resource
                break
        
        # Add entities to intent
        intent_entities = {}
        
        # Add explicit entities from current message, deduplicating by value for same type
        added_values = {}  # Keep track of added values by type
        for entity in entities:
            # Create a key for tracking added values
            entity_type = entity.type.value
            if entity_type not in added_values:
                added_values[entity_type] = set()
                
            # Skip if we already have this value for this type
            if entity.value in added_values[entity_type]:
                continue
                
            # Add to tracking set and intent entities
            added_values[entity_type].add(entity.value)
            entity_name = f"{entity.type.value}_{len(intent_entities)}"
            intent_entities[entity_name] = entity
        
        # Add contextual entities if needed
        if "{id}" in intent.api_resource.uri and "competition" not in intent_entities and "team" not in intent_entities:
            # Try to get competition or team from context
            if intent_name in ["get_standings", "get_competition_matches", "get_competition_teams", "get_competition_scorers"]:
                # Need competition context
                comp_entities = context.get_entities_by_type(EntityType.COMPETITION)
                if comp_entities:
                    # Get the most recent/highest confidence competition
                    comp_entities.sort(key=lambda e: context.get_entity_confidence(e), reverse=True)
                    intent_entities["competition_context"] = comp_entities[0]
                    logger.debug(f"Added contextual competition: {comp_entities[0].value}")
            
            elif intent_name in ["get_team_matches"]:
                # Need team context
                team_entities = context.get_entities_by_type(EntityType.TEAM)
                if team_entities:
                    # Get the most recent/highest confidence team
                    team_entities.sort(key=lambda e: context.get_entity_confidence(e), reverse=True)
                    intent_entities["team_context"] = team_entities[0]
                    logger.debug(f"Added contextual team: {team_entities[0].value}")
        
        intent.entities = intent_entities
        
        # Generate API parameters
        intent.get_api_params()
        
        # Update confidence based on entity completeness
        if intent.api_resource:
            # Check if we have all required parameters
            required_params = set(intent.api_resource.required_params)
            for param_name in list(required_params):
                if param_name == "id":
                    # Special case for ID parameters
                    if "competition_id" in intent.api_params or "team_id" in intent.api_params:
                        required_params.remove("id")
            
            # Adjust confidence based on required params coverage
            if required_params:
                # Missing required params, reduce confidence
                intent.confidence *= 0.5
                logger.debug(f"Reduced confidence due to missing required params: {required_params}")
        
        return intent