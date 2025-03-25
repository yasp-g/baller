"""Conversation context management for tracking entities across multiple turns.

This module maintains conversation context, allowing for resolution of
ambiguous references and tracking of entities mentioned in previous turns.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta

from .entities import Entity, EntityType

# Get logger for this module
logger = logging.getLogger('baller.intent.context')

class ConversationContext:
    """Manages conversation context for a single user conversation."""
    
    # How long to keep entities in active context (in seconds)
    ACTIVE_CONTEXT_TTL = 600  # 10 minutes
    
    # How long to track conversation history (in seconds)
    HISTORY_TTL = 3600  # 1 hour
    
    # How quickly confidence decays for past entities (0-1 per turn, higher = faster decay)
    CONFIDENCE_DECAY = 0.1
    
    def __init__(self, user_id: str):
        """Initialize conversation context for a user.
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
        self.entities = {}  # Type -> List of entities
        self.entity_timestamps = {}  # Entity id -> timestamp
        self.recent_intents = []  # List of recent intents
        self.last_active = time.time()
    
    def add_entities(self, entities: List[Entity]):
        """Add extracted entities to the conversation context.
        
        Args:
            entities: List of entities to add
        """
        current_time = time.time()
        self.last_active = current_time
        
        for entity in entities:
            # Initialize type entry if needed
            if entity.type not in self.entities:
                self.entities[entity.type] = []
            
            # Store a unique identifier for the entity
            entity_id = f"{entity.type.value}:{entity.value}"
            if entity.id:
                entity_id += f":{entity.id}"
            
            # Check if this entity already exists in context
            existing_entity = next((e for e in self.entities[entity.type] 
                                   if (e.value.lower() == entity.value.lower() and 
                                       e.id == entity.id)), None)
            
            if existing_entity:
                # Update existing entity with new confidence
                idx = self.entities[entity.type].index(existing_entity)
                # Take the higher confidence between existing and new
                adjusted_confidence = max(existing_entity.confidence, entity.confidence)
                # Create updated entity with higher confidence
                updated_entity = Entity(
                    type=entity.type,
                    value=entity.value,
                    id=entity.id,
                    confidence=adjusted_confidence,
                    start=entity.start,
                    end=entity.end,
                    metadata=entity.metadata
                )
                self.entities[entity.type][idx] = updated_entity
            else:
                # Add new entity
                self.entities[entity.type].append(entity)
            
            # Update timestamp
            self.entity_timestamps[entity_id] = current_time
    
    def add_intent(self, intent_name: str, confidence: float, entities: Dict[str, Any]):
        """Add an intent to the conversation history.
        
        Args:
            intent_name: Name of the intent
            confidence: Confidence score for the intent
            entities: Entities used in the intent
        """
        self.last_active = time.time()
        
        # Add to recent intents, keep last 5
        self.recent_intents.append({
            "name": intent_name,
            "confidence": confidence,
            "entities": entities,
            "timestamp": time.time()
        })
        self.recent_intents = self.recent_intents[-5:]
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type.
        
        Args:
            entity_type: Type of entities to retrieve
            
        Returns:
            List of entities of the specified type
        """
        self._clean_expired_entities()
        return self.entities.get(entity_type, [])
    
    def get_entity_by_value(self, entity_type: EntityType, value: str) -> Optional[Entity]:
        """Get an entity by type and value (case insensitive).
        
        Args:
            entity_type: Type of entity to find
            value: Value to match
            
        Returns:
            Matching entity or None
        """
        entities = self.get_entities_by_type(entity_type)
        for entity in entities:
            if entity.value.lower() == value.lower():
                return entity
        return None
    
    def get_most_recent_entities(self, limit: int = 5) -> List[Entity]:
        """Get the most recently mentioned entities.
        
        Args:
            limit: Max number of entities to return
            
        Returns:
            List of most recent entities
        """
        self._clean_expired_entities()
        
        # Flatten all entities
        all_entities = []
        for entity_list in self.entities.values():
            all_entities.extend(entity_list)
        
        # Sort by timestamp (most recent first)
        sorted_entities = []
        for entity in all_entities:
            entity_id = f"{entity.type.value}:{entity.value}"
            if entity.id:
                entity_id += f":{entity.id}"
            timestamp = self.entity_timestamps.get(entity_id, 0)
            sorted_entities.append((entity, timestamp))
        
        sorted_entities.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the entities (without timestamps)
        return [e[0] for e in sorted_entities[:limit]]
    
    def get_last_intent(self) -> Optional[Dict[str, Any]]:
        """Get the most recent intent.
        
        Returns:
            Most recent intent or None
        """
        if not self.recent_intents:
            return None
        return self.recent_intents[-1]
    
    def _clean_expired_entities(self):
        """Remove entities with expired TTL."""
        current_time = time.time()
        
        # Remove expired entities
        for entity_type in list(self.entities.keys()):
            self.entities[entity_type] = [
                e for e in self.entities[entity_type]
                if self._is_entity_active(e, current_time)
            ]
            
            # Remove entity type if empty
            if not self.entities[entity_type]:
                del self.entities[entity_type]
        
        # Remove expired entity timestamps
        for entity_id in list(self.entity_timestamps.keys()):
            timestamp = self.entity_timestamps[entity_id]
            if current_time - timestamp > self.HISTORY_TTL:
                del self.entity_timestamps[entity_id]
        
        # Remove expired intents
        self.recent_intents = [
            intent for intent in self.recent_intents
            if current_time - intent["timestamp"] <= self.HISTORY_TTL
        ]
    
    def _is_entity_active(self, entity: Entity, current_time: float) -> bool:
        """Check if an entity is still active based on its timestamp.
        
        Args:
            entity: Entity to check
            current_time: Current timestamp
            
        Returns:
            True if entity is still active, False otherwise
        """
        entity_id = f"{entity.type.value}:{entity.value}"
        if entity.id:
            entity_id += f":{entity.id}"
        
        timestamp = self.entity_timestamps.get(entity_id, 0)
        return current_time - timestamp <= self.HISTORY_TTL
    
    def get_entity_confidence(self, entity: Entity) -> float:
        """Get current confidence for an entity, accounting for time decay.
        
        Args:
            entity: Entity to check confidence for
            
        Returns:
            Current confidence (with decay applied)
        """
        entity_id = f"{entity.type.value}:{entity.value}"
        if entity.id:
            entity_id += f":{entity.id}"
        
        timestamp = self.entity_timestamps.get(entity_id, 0)
        current_time = time.time()
        
        # Calculate elapsed time and decay confidence
        elapsed_seconds = current_time - timestamp
        if elapsed_seconds > self.ACTIVE_CONTEXT_TTL:
            # Strong decay for older entities
            turns_passed = elapsed_seconds / self.ACTIVE_CONTEXT_TTL
            decay = self.CONFIDENCE_DECAY * turns_passed
            return max(0, entity.confidence - decay)
        
        return entity.confidence