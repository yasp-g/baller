"""Content relevance filter for Baller bot."""

import logging
from typing import Dict, Any, Tuple

from ..api.llm import LLMClient

logger = logging.getLogger('baller.bot.filter')

class ContentFilter:
    """Determines if user messages are relevant to football/soccer."""
    
    def __init__(self, llm_client: LLMClient):
        """Initialize the content filter.
        
        Args:
            llm_client: LLM client for relevance detection
        """
        self.llm_client = llm_client
    
    async def is_relevant(self, content: str) -> Tuple[bool, str]:
        """Check if a message is relevant to football/soccer.
        
        Args:
            content: User message content
            
        Returns:
            Tuple of (is_relevant, explanation)
        """
        logger.debug(f"Checking relevance of message: {content[:50]}...")
        
        # Use the template-based relevance check
        response = await self.llm_client.generate_relevance_check(content)
        
        # Parse the response to get boolean result and explanation
        try:
            lines = response.strip().split('\n', 1)
            relevance = lines[0].lower().strip()
            explanation = lines[1].strip() if len(lines) > 1 else ""
            
            is_relevant = relevance in ('yes', 'true', 'relevant')
            logger.info(f"Message relevance: {is_relevant}")
            
            return is_relevant, explanation
        except Exception as e:
            logger.error(f"Error parsing relevance check response: {e}")
            # Default to relevant if parsing fails
            return True, "Error determining relevance"