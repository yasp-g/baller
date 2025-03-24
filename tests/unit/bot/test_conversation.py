import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.conversation import Conversation, ConversationManager

class TestConversation:
    """Tests for the Conversation class"""
    
    def test_init(self):
        """Test conversation initialization"""
        convo = Conversation("user123")
        assert convo.user_id == "user123"
        assert isinstance(convo.created_at, datetime)
        assert isinstance(convo.last_active, datetime)
        assert convo.messages == []
        assert convo.metadata == {}
        assert convo.ttl is None
    
    def test_add_message(self):
        """Test adding messages to a conversation"""
        convo = Conversation("user123")
        
        # Add a message and verify it's stored
        convo.add_message("user", "Hello")
        assert len(convo.messages) == 1
        assert convo.messages[0]["role"] == "user"
        assert convo.messages[0]["content"] == "Hello"
        
        # Add another message
        convo.add_message("assistant", "Hi there")
        assert len(convo.messages) == 2
        assert convo.messages[1]["role"] == "assistant"
        assert convo.messages[1]["content"] == "Hi there"
        
        # Check that last_active was updated
        assert convo.last_active > convo.created_at
    
    def test_get_messages(self):
        """Test getting all messages"""
        convo = Conversation("user123")
        convo.add_message("user", "Hello")
        convo.add_message("assistant", "Hi there")
        
        messages = convo.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there"
    
    def test_get_last_messages(self):
        """Test getting the last user and assistant messages"""
        convo = Conversation("user123")
        
        # Empty conversation
        assert convo.get_last_user_message() is None
        assert convo.get_last_assistant_message() is None
        
        # With messages
        convo.add_message("user", "Message 1")
        convo.add_message("assistant", "Response 1")
        convo.add_message("user", "Message 2")
        convo.add_message("assistant", "Response 2")
        
        assert convo.get_last_user_message() == "Message 2"
        assert convo.get_last_assistant_message() == "Response 2"
    
    def test_is_expired(self):
        """Test expiry checking"""
        convo = Conversation("user123")
        
        # Should not be expired with current timestamp
        assert not convo.is_expired(30)
        
        # Mock last_active to be older
        with patch.object(convo, 'last_active', datetime.now() - timedelta(minutes=40)):
            # Should be expired with 30 min timeout
            assert convo.is_expired(30)
            # Should not be expired with 60 min timeout
            assert not convo.is_expired(60)
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        original = Conversation("user123")
        original.add_message("user", "Hello")
        original.add_message("assistant", "Hi there")
        original.metadata = {"context": "test context"}
        original.ttl = 1234567890
        
        # Convert to dict and back
        data = original.to_dict()
        recreated = Conversation.from_dict(data)
        
        # Verify recreation
        assert recreated.user_id == "user123"
        assert recreated.messages == original.messages
        assert recreated.metadata == {"context": "test context"}
        assert recreated.ttl == 1234567890
        assert recreated.created_at.timestamp() == pytest.approx(original.created_at.timestamp(), abs=1)
        assert recreated.last_active.timestamp() == pytest.approx(original.last_active.timestamp(), abs=1)


@pytest.mark.asyncio
class TestConversationManager:
    """Tests for the ConversationManager class"""
    
    async def test_get_conversation(self):
        """Test getting or creating conversations"""
        with patch('src.bot.conversation.config') as mock_config:
            # Mock configuration
            mock_config.CONVERSATION_EXPIRY_MINUTES = 30
            mock_config.CONVERSATION_MAX_COUNT = 100
            mock_config.AWS_ENABLED = False
            
            manager = ConversationManager()
            
            # Get a new conversation
            convo1 = manager.get_conversation("user1")
            assert convo1.user_id == "user1"
            assert len(manager.conversations) == 1
            
            # Get the same conversation again
            convo2 = manager.get_conversation("user1")
            assert convo1 is convo2  # Should be the same object
            
            # Get a different user's conversation
            convo3 = manager.get_conversation("user2")
            assert convo3 is not convo1
            assert len(manager.conversations) == 2
    
    async def test_add_message(self):
        """Test adding messages through the manager"""
        with patch('src.bot.conversation.config') as mock_config:
            # Mock configuration
            mock_config.CONVERSATION_EXPIRY_MINUTES = 30
            mock_config.CONVERSATION_MAX_COUNT = 100
            mock_config.AWS_ENABLED = False
            
            manager = ConversationManager()
            
            # Add messages for a new user
            manager.add_message("user1", "user", "Hello")
            manager.add_message("user1", "assistant", "Hi there")
            
            convo = manager.get_conversation("user1")
            assert len(convo.messages) == 2
            assert convo.messages[0]["content"] == "Hello"
            assert convo.messages[1]["content"] == "Hi there"
    
    async def test_cleanup_expired(self):
        """Test cleaning up expired conversations"""
        with patch('src.bot.conversation.config') as mock_config:
            # Mock configuration
            mock_config.CONVERSATION_EXPIRY_MINUTES = 30
            mock_config.CONVERSATION_MAX_COUNT = 100
            mock_config.AWS_ENABLED = False
            mock_config.CONVERSATION_RETENTION_DAYS = 30
            
            manager = ConversationManager(expiry_minutes=10)
            
            # Add some conversations
            manager.add_message("user1", "user", "Hello")
            manager.add_message("user2", "user", "Hi")
            manager.add_message("user3", "user", "Hey")
            assert len(manager.conversations) == 3
            
            # Make user1 and user2 conversations expired
            user1_convo = manager.get_conversation("user1")
            user2_convo = manager.get_conversation("user2")
            
            with patch.object(user1_convo, 'last_active', datetime.now() - timedelta(minutes=20)):
                with patch.object(user2_convo, 'last_active', datetime.now() - timedelta(minutes=15)):
                    # Mock AWS archive function
                    with patch.object(manager, '_archive_conversation', AsyncMock()) as mock_archive:
                        # Run cleanup
                        removed = await manager.cleanup_expired()
                        
                        # Should have removed 2 conversations
                        assert removed == 2
                        assert len(manager.conversations) == 1
                        assert "user3" in manager.conversations
                        assert "user1" not in manager.conversations
                        assert "user2" not in manager.conversations
                        
                        # Shouldn't have tried to archive since AWS is disabled
                        assert mock_archive.call_count == 0
    
    async def test_trim_oldest_conversations(self):
        """Test trimming conversations when over the limit"""
        with patch('src.bot.conversation.config') as mock_config:
            # Mock configuration
            mock_config.CONVERSATION_EXPIRY_MINUTES = 30
            mock_config.CONVERSATION_MAX_COUNT = 100
            mock_config.AWS_ENABLED = False
            mock_config.CONVERSATION_RETENTION_DAYS = 30
            
            manager = ConversationManager(max_conversations=2)
            
            # Add 3 conversations (over our limit of 2)
            now = datetime.now()
            
            # Add in reverse order so user1 is oldest
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = now - timedelta(minutes=30)
                manager.add_message("user1", "user", "I'm oldest")
                
                mock_dt.now.return_value = now - timedelta(minutes=20)
                manager.add_message("user2", "user", "I'm in the middle")
                
                mock_dt.now.return_value = now - timedelta(minutes=10)
                manager.add_message("user3", "user", "I'm newest")
            
            # Mock the archive function
            with patch.object(manager, '_archive_conversation', AsyncMock()) as mock_archive:
                await manager._trim_oldest_conversations()
                
                # Should have trimmed user1 (oldest)
                assert len(manager.conversations) == 2
                assert "user1" not in manager.conversations
                assert "user2" in manager.conversations
                assert "user3" in manager.conversations
                
                # Should have tried to archive since we're over the limit
                assert mock_archive.call_count == 1
    
    async def test_shutdown(self):
        """Test proper cleanup on shutdown"""
        with patch('src.bot.conversation.config') as mock_config:
            # Mock configuration
            mock_config.CONVERSATION_EXPIRY_MINUTES = 30
            mock_config.CONVERSATION_MAX_COUNT = 100
            mock_config.AWS_ENABLED = True
            mock_config.CONVERSATION_RETENTION_DAYS = 30
            
            manager = ConversationManager()
            
            # Add a conversation
            manager.add_message("user1", "user", "Hello")
            
            # Start the cleanup task with a mock that will properly support done() and cancel()
            mock_task = MagicMock()
            mock_task.done.return_value = False
            mock_task.cancel = AsyncMock()
            manager.cleanup_task = mock_task
            
            # Mock archive function
            with patch.object(manager, '_archive_conversation', AsyncMock()) as mock_archive:
                # Shutdown
                await manager.shutdown()
                
                # Should have called task.cancel()
                mock_task.cancel.assert_called_once()
                
                # Should have tried to archive the conversation
                assert mock_archive.call_count == 1