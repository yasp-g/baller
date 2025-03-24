"""
Conversation management module for Baller bot.

This module provides conversation history tracking, timeout management, 
and AWS persistence for user interactions.
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from ..config import config

logger = logging.getLogger('baller.conversation')

class Conversation:
    """Represents a single conversation with a user."""
    
    def __init__(self, user_id: str):
        """Initialize a new conversation.
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.messages: List[Dict[str, str]] = []
        self.metadata: Dict[str, Any] = {}
        self.ttl: Optional[int] = None
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation.
        
        Args:
            role: The message role (user or assistant)
            content: The message content
        """
        self.messages.append({"role": role, "content": content})
        self.last_active = datetime.now()
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages in the conversation.
        
        Returns:
            List of message dictionaries with role and content
        """
        return self.messages
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message.
        
        Returns:
            The content of the last user message, or None if no user messages
        """
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message["content"]
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """Get the most recent assistant message.
        
        Returns:
            The content of the last assistant message, or None if no assistant messages
        """
        for message in reversed(self.messages):
            if message["role"] == "assistant":
                return message["content"]
        return None
    
    def is_expired(self, expiry_minutes: int) -> bool:
        """Check if the conversation has expired based on inactivity.
        
        Args:
            expiry_minutes: Number of minutes of inactivity before expiry
            
        Returns:
            True if conversation is expired, False otherwise
        """
        expiry_delta = timedelta(minutes=expiry_minutes)
        return datetime.now() - self.last_active > expiry_delta
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to a dictionary for storage.
        
        Returns:
            Dictionary representation of the conversation
        """
        return {
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "messages": self.messages,
            "metadata": self.metadata,
            "ttl": self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a conversation from a dictionary.
        
        Args:
            data: Dictionary representation of conversation
            
        Returns:
            Conversation object
        """
        conversation = cls(data["user_id"])
        conversation.created_at = datetime.fromisoformat(data["created_at"])
        conversation.last_active = datetime.fromisoformat(data["last_active"])
        conversation.messages = data["messages"]
        conversation.metadata = data.get("metadata", {})
        conversation.ttl = data.get("ttl")
        return conversation
    
    def get_summary(self) -> str:
        """Generate a summary of this conversation.
        
        Returns:
            Short summary of the conversation
        """
        total_messages = len(self.messages)
        user_messages = sum(1 for msg in self.messages if msg["role"] == "user")
        duration = (self.last_active - self.created_at).total_seconds() / 60
        
        return (
            f"Conversation with {self.user_id}: "
            f"{total_messages} messages ({user_messages} from user) "
            f"over {duration:.1f} minutes"
        )


class ConversationManager:
    """Manages all user conversations with timeout and AWS integration."""
    
    def __init__(
        self, 
        expiry_minutes: int = None,
        max_conversations: int = None,
        cleanup_interval: int = 300
    ):
        """Initialize the conversation manager.
        
        Args:
            expiry_minutes: Minutes of inactivity before conversation expiry
            max_conversations: Maximum number of in-memory conversations
            cleanup_interval: Seconds between cleanup runs
        """
        self.conversations: Dict[str, Conversation] = {}
        self.expiry_minutes = expiry_minutes or config.CONVERSATION_EXPIRY_MINUTES
        self.max_conversations = max_conversations or config.CONVERSATION_MAX_COUNT
        self.cleanup_interval = cleanup_interval
        self.cleanup_task = None
        self.aws_enabled = config.AWS_ENABLED
        
        logger.info(
            f"ConversationManager initialized with expiry={self.expiry_minutes}m, "
            f"max={self.max_conversations}, AWS={'enabled' if self.aws_enabled else 'disabled'}"
        )
    
    def start_cleanup_task(self, loop=None) -> None:
        """Start the periodic cleanup task.
        
        Args:
            loop: Optional asyncio event loop to use
        """
        if self.cleanup_task is None:
            loop = loop or asyncio.get_event_loop()
            self.cleanup_task = loop.create_task(self._periodic_cleanup())
            logger.debug("Conversation cleanup task started")
    
    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired conversations."""
        while True:
            try:
                count = await self.cleanup_expired()
                if count > 0:
                    logger.info(f"Cleaned up {count} expired conversations")
                    
                # Also check if we need to trim due to max_conversations
                if len(self.conversations) > self.max_conversations:
                    await self._trim_oldest_conversations()
            except Exception as e:
                logger.error(f"Error in conversation cleanup: {e}")
                
            await asyncio.sleep(self.cleanup_interval)
    
    async def _trim_oldest_conversations(self) -> None:
        """Trim the oldest conversations when we exceed max_conversations."""
        if len(self.conversations) <= self.max_conversations:
            return
            
        # Sort conversations by last_active
        sorted_convos = sorted(
            self.conversations.items(),
            key=lambda item: item[1].last_active
        )
        
        # Determine how many to remove
        to_remove = len(self.conversations) - self.max_conversations
        conversations_to_remove = sorted_convos[:to_remove]
        
        # Archive and remove
        for user_id, conversation in conversations_to_remove:
            await self._archive_conversation(conversation)
            del self.conversations[user_id]
            
        logger.info(f"Trimmed {to_remove} oldest conversations due to max limit")
    
    async def cleanup_expired(self) -> int:
        """Clean up expired conversations.
        
        Returns:
            Number of conversations removed
        """
        expired_user_ids = []
        
        for user_id, conversation in self.conversations.items():
            if conversation.is_expired(self.expiry_minutes):
                expired_user_ids.append(user_id)
                # Archive to AWS if enabled
                if self.aws_enabled:
                    await self._archive_conversation(conversation)
        
        # Remove expired conversations
        for user_id in expired_user_ids:
            del self.conversations[user_id]
            
        return len(expired_user_ids)
    
    def get_conversation(self, user_id: str) -> Conversation:
        """Get or create a conversation for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            The user's conversation
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = Conversation(user_id)
            logger.debug(f"Created new conversation for user {user_id}")
            
            # If AWS is enabled, try to load previous conversation
            # Note: In a real implementation, we would await this
            # For now we'll skip the loading since it's just a placeholder
            # if self.aws_enabled:
            #    await self._try_load_from_aws(user_id)
        
        return self.conversations[user_id]
    
    def add_message(self, user_id: str, role: str, content: str) -> None:
        """Add a message to a user's conversation.
        
        Args:
            user_id: The user's ID
            role: Message role (user or assistant)
            content: Message content
        """
        conversation = self.get_conversation(user_id)
        conversation.add_message(role, content)
    
    async def _archive_conversation(self, conversation: Conversation) -> None:
        """Archive a conversation to AWS.
        
        This is a placeholder for AWS DynamoDB integration.
        
        Args:
            conversation: The conversation to archive
        """
        try:
            # Set TTL for DynamoDB (current time + retention period)
            retention_days = config.CONVERSATION_RETENTION_DAYS
            ttl_timestamp = int((datetime.now() + timedelta(days=retention_days)).timestamp())
            conversation.ttl = ttl_timestamp
            
            # In a real implementation, we would store in DynamoDB:
            # await dynamodb_client.put_item(
            #     TableName="conversations",
            #     Item={
            #         "user_id": {"S": conversation.user_id},
            #         "data": {"S": json.dumps(conversation.to_dict())},
            #         "ttl": {"N": str(ttl_timestamp)}
            #     }
            # )
            
            logger.debug(
                f"Archived conversation for user {conversation.user_id} "
                f"with {len(conversation.messages)} messages"
            )
        except Exception as e:
            logger.error(f"Failed to archive conversation: {e}")
    
    async def _try_load_from_aws(self, user_id: str) -> bool:
        """Try to load a conversation from AWS DynamoDB.
        
        This is a placeholder for AWS DynamoDB integration.
        
        Args:
            user_id: The user ID to load conversation for
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # In a real implementation, we would retrieve from DynamoDB:
            # response = await dynamodb_client.get_item(
            #     TableName="conversations",
            #     Key={"user_id": {"S": user_id}}
            # )
            # if "Item" in response:
            #     data = json.loads(response["Item"]["data"]["S"])
            #     self.conversations[user_id] = Conversation.from_dict(data)
            #     return True
            
            return False  # Placeholder
        except Exception as e:
            logger.error(f"Failed to load conversation from AWS: {e}")
            return False
            
    def get_active_count(self) -> int:
        """Get the count of active conversations.
        
        Returns:
            Number of active conversations
        """
        return len(self.conversations)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about conversations.
        
        Returns:
            Dictionary of statistics
        """
        if not self.conversations:
            return {
                "active_count": 0,
                "oldest_created": None,
                "newest_created": None,
                "total_messages": 0,
                "avg_messages_per_conversation": 0
            }
            
        total_messages = sum(len(c.messages) for c in self.conversations.values())
        created_times = [c.created_at for c in self.conversations.values()]
        
        return {
            "active_count": len(self.conversations),
            "oldest_created": min(created_times),
            "newest_created": max(created_times),
            "total_messages": total_messages,
            "avg_messages_per_conversation": total_messages / len(self.conversations)
        }
    
    async def shutdown(self) -> None:
        """Clean up resources when shutting down."""
        try:
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                # In a real implementation, we would await the task
                # but that's not needed for testing
                try:
                    # Only await if it's actually a coroutine
                    if hasattr(self.cleanup_task, "__await__"):
                        await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Archive all conversations if AWS is enabled
            if self.aws_enabled:
                for conversation in self.conversations.values():
                    await self._archive_conversation(conversation)
        except Exception as e:
            logger.error(f"Error during conversation manager shutdown: {e}")