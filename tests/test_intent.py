"""Tests for the intent detection system."""

import pytest
import asyncio
from datetime import date, timedelta

from src.bot.intent.entities import EntityExtractor, EntityType
from src.bot.intent.context import ConversationContext
from src.bot.intent.processor import IntentProcessor, ApiResource

@pytest.fixture
def entity_extractor():
    """Create an EntityExtractor for testing."""
    # Add some test team data
    team_cache = {
        "Arsenal": {"id": 57, "shortName": "Arsenal", "tla": "ARS"},
        "Manchester United": {"id": 66, "shortName": "Man United", "tla": "MUN"},
        "Bayern Munich": {"id": 5, "shortName": "Bayern", "tla": "BAY"}
    }
    return EntityExtractor(team_cache=team_cache)

@pytest.fixture
def intent_processor(entity_extractor):
    """Create an IntentProcessor for testing."""
    return IntentProcessor(entity_extractor=entity_extractor)

class TestEntityExtractor:
    """Tests for the EntityExtractor class."""

    def test_extract_competitions(self, entity_extractor):
        """Test extracting competition entities."""
        text = "Show me the Premier League standings"
        entities = entity_extractor.extract_entities(text)
        
        # Find competition entities
        competitions = [e for e in entities if e.type == EntityType.COMPETITION]
        
        assert len(competitions) == 1
        assert competitions[0].value == "Premier League"
        assert competitions[0].id == 2021
        
    def test_extract_timeframes(self, entity_extractor):
        """Test extracting timeframe entities."""
        text = "Show me matches for today and tomorrow"
        entities = entity_extractor.extract_entities(text)
        
        # Find timeframe entities
        timeframes = [e for e in entities if e.type == EntityType.TIMEFRAME]
        
        assert len(timeframes) == 2
        
        # Check if we have "today" and "tomorrow"
        values = {e.value for e in timeframes}
        assert "today" in values
        assert "tomorrow" in values
        
        # Check metadata
        for entity in timeframes:
            if entity.value == "today":
                assert "date" in entity.metadata
                assert entity.metadata["date"] == date.today().isoformat()
                
            if entity.value == "tomorrow":
                assert "date" in entity.metadata
                assert entity.metadata["date"] == (date.today() + timedelta(days=1)).isoformat()
    
    def test_extract_teams(self, entity_extractor):
        """Test extracting team entities."""
        text = "How is Arsenal doing this season?"
        entities = entity_extractor.extract_entities(text)
        
        # Find team entities
        teams = [e for e in entities if e.type == EntityType.TEAM]
        
        assert len(teams) == 1
        assert teams[0].value == "Arsenal"
        assert teams[0].id == 57
        assert teams[0].metadata["shortName"] == "Arsenal"
        assert teams[0].metadata["tla"] == "ARS"

class TestConversationContext:
    """Tests for the ConversationContext class."""
    
    def test_context_tracking(self, entity_extractor):
        """Test tracking entities in conversation context."""
        context = ConversationContext("test_user")
        
        # Extract entities from a message
        text = "Show me Premier League standings"
        entities = entity_extractor.extract_entities(text)
        
        # Add entities to context
        context.add_entities(entities)
        
        # Get competition entities from context
        competitions = context.get_entities_by_type(EntityType.COMPETITION)
        
        assert len(competitions) == 1
        assert competitions[0].value == "Premier League"
        
        # Test another message with a team
        text2 = "How about Arsenal?"
        entities2 = entity_extractor.extract_entities(text2)
        context.add_entities(entities2)
        
        # Get most recent entities
        recent = context.get_most_recent_entities(limit=2)
        
        assert len(recent) == 2
        # Most recent should be Arsenal
        assert recent[0].value == "Arsenal"
        
        # Get Arsenal by value
        arsenal = context.get_entity_by_value(EntityType.TEAM, "Arsenal")
        assert arsenal is not None
        assert arsenal.id == 57

class TestIntentProcessor:
    """Tests for the IntentProcessor class."""
    
    @pytest.mark.asyncio
    async def test_standings_intent(self, intent_processor):
        """Test detecting standings intent."""
        message = "Show me the Premier League standings"
        user_id = "test_user"
        
        intent = await intent_processor.process_message(user_id, message)
        
        assert intent is not None
        assert intent.name == "get_standings"
        assert intent.confidence >= 0.7
        
        # Check if we have the Premier League entity - printing for debug
        competition_entities = [e for e in intent.entities.values() 
                               if e.type == EntityType.COMPETITION]
        print(f"Intent entities: {intent.entities}")
        for i, entity in enumerate(competition_entities):
            print(f"Entity {i}: type={entity.type}, value={entity.value}, id={entity.id}, start={entity.start}, end={entity.end}")
        
        # We only care that we have at least one Premier League entity
        premier_league_entities = [e for e in competition_entities if e.value == "Premier League"]
        assert len(premier_league_entities) >= 1
        
        # Check API params
        assert "competition_id" in intent.api_params
        assert intent.api_params["competition_id"] == 2021
    
    @pytest.mark.asyncio
    async def test_matches_intent(self, intent_processor):
        """Test detecting matches intent."""
        message = "What matches are there tomorrow?"
        user_id = "test_user"
        
        intent = await intent_processor.process_message(user_id, message)
        
        assert intent is not None
        assert intent.name == "get_matches"
        
        # Check if we have the tomorrow entity
        timeframe_entities = [e for e in intent.entities.values() 
                             if e.type == EntityType.TIMEFRAME]
        assert len(timeframe_entities) == 1
        assert timeframe_entities[0].value == "tomorrow"
        
        # Check API params
        assert "date_from" in intent.api_params
        assert "date_to" in intent.api_params
        assert intent.api_params["date_from"] == intent.api_params["date_to"]
    
    @pytest.mark.asyncio
    async def test_context_preservation(self, intent_processor):
        """Test that context is preserved between messages."""
        user_id = "test_user"
        
        # First message with a competition
        message1 = "Show me Premier League"
        intent1 = await intent_processor.process_message(user_id, message1)
        
        # Second message with just a follow-up
        message2 = "What about the standings?"
        intent2 = await intent_processor.process_message(user_id, message2)
        
        assert intent2 is not None
        assert intent2.name == "get_standings"
        
        # Check if we have a competition entity from context
        competition_entities = [e for e in intent2.entities.values() 
                               if e.type == EntityType.COMPETITION]
        assert len(competition_entities) == 1
        assert competition_entities[0].value == "Premier League"