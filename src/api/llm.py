import os
import inspect
import logging
import anthropic
from openai import AsyncOpenAI
from typing import Dict, Any, Optional, List
from ..config import config
from ..exceptions import (
    LLMException,
    ModelUnavailableError,
    PromptError,
    ResponseError
)

# class LLMClient:
#     def __init__(self):
#         self.client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
    
#     async def generate_response(self, user_message, context_data=None):
#         """Generate a conversational response using Claude"""
        
#         system_prompt = """You are a helpful football assistant. You have access to football data
#         provided by API-Sports. Respond conversationally to user queries about football matches,
#         leagues, teams, and players based on the data provided."""
        
#         # Format context data for the LLM
#         context = ""
#         if context_data:
#             context = f"Here is the relevant football data: {context_data}\n\n"
        
#         try:
#             response = await self.client.messages.create(
#                 model="claude-3-opus-20240229",  # Use appropriate model
#                 system=system_prompt,
#                 messages=[
#                     {
#                         "role": "user",
#                         "content": f"{context}User question: {user_message}"
#                     }
#                 ],
#                 max_tokens=1000
#             )
#             return response.content[0].text
#         except Exception as e:
#             return f"I encountered an error generating a response: {str(e)}"

class LLMClient:
    def __init__(self):
        self.logger = logging.getLogger('baller.api.llm')
        self.client = AsyncOpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        self.football_api = None
        self.commands = None
        self.api_errors = []
        self.command_errors = []
        self.logger.debug("LLMClient initialized")
    
    def register_api(self, api):
        """Register the FootballAPI instance"""
        self.football_api = api
        
    def register_commands(self, commands):
        """Register the BallerCommands instance"""
        self.commands = commands
    
    def record_api_error(self, error_message, endpoint=None):
        """Record API errors for context in future responses"""
        self.api_errors.append({
            "endpoint": endpoint,
            "message": str(error_message),
            "timestamp": str(os.times()[4])  # Simple timestamp
        })
        # Keep only the last 5 errors
        self.api_errors = self.api_errors[-5:]
    
    def record_command_error(self, error_message, command=None):
        """Record command execution errors for context in future responses"""
        self.command_errors.append({
            "command": command,
            "message": str(error_message),
            "timestamp": str(os.times()[4])  # Simple timestamp
        })
        # Keep only the last 5 errors
        self.command_errors = self.command_errors[-5:]
    
    async def generate_response(
        self, 
        user_message: str, 
        context_data: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a conversational response using Deepseek's model
        
        Args:
            user_message: The user's question or message
            context_data: Optional context data to include in the prompt
            user_preferences: Optional user preferences to personalize the response
            
        Returns:
            Generated text response from the LLM
            
        Raises:
            ModelUnavailableError: When the LLM service is unavailable
            PromptError: When there's an issue with the prompt
            ResponseError: When there's an issue processing the response
        """
        if not user_message:
            raise PromptError("Empty user message provided")
            
        # Create the system prompt with error context if available
        api_context = ""
        cmd_context = ""
        user_pref_context = ""
        
        # Add API information if available
        if self.football_api:
            api_context = "Football API is available for fetching data."
            if self.api_errors:
                api_context += "\nRecent API errors:"
                for err in self.api_errors:
                    api_context += f"\n- {err['endpoint'] or 'Unknown endpoint'}: {err['message']}"
        
        # Add Commands information if available
        if self.commands:
            cmd_context = "Discord commands are available for user interaction."
            if self.command_errors:
                cmd_context += "\nRecent command errors:"
                for err in self.command_errors:
                    cmd_context += f"\n- {err['command'] or 'Unknown command'}: {err['message']}"
        
        # Add user preferences if available
        if user_preferences:
            followed_teams = user_preferences.get("followed_teams", set())
            if followed_teams:
                teams_list = ", ".join(sorted(followed_teams))
                user_pref_context = f"This user follows these teams: {teams_list}. Prioritize information about these teams when relevant."
                
            notification_settings = user_preferences.get("notification_settings", {})
            if notification_settings:
                user_pref_context += "\nThe user's notification preferences are:"
                for setting, value in notification_settings.items():
                    user_pref_context += f"\n- {setting}: {'Enabled' if value else 'Disabled'}"
        
        system_prompt = f"""
        You are a helpful football assistant. You have access to football data
        provided by football-data API. Respond conversationally to user queries about football matches,
        leagues, teams, and players based on the data provided.
        
        {api_context}
        
        {cmd_context}
        
        {user_pref_context}
        """
        
        # Format context data for the LLM
        context = ""
        if context_data:
            context = f"Here is the relevant football data: {context_data}\n\n"
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",  # Or specific model version
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt.strip()
                    },
                    {
                        "role": "user",
                        "content": f"{context}User question: {user_message.strip()}"
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            if not response.choices or not response.choices[0].message:
                raise ResponseError("Empty response received from LLM")
                
            return response.choices[0].message.content
            
        except ResponseError:
            # Re-raise our custom exceptions
            raise
        except (anthropic.APIError, anthropic.APIConnectionError) as e:
            raise ModelUnavailableError(
                message="Deepseek API is currently unavailable",
                model_name="deepseek-chat",
                details={"original_error": str(e)}
            ) from e
        except (anthropic.APIStatusError, anthropic.BadRequestError) as e:
            raise PromptError(
                message="Error in prompt construction or validation",
                details={
                    "original_error": str(e),
                    "user_message_length": len(user_message),
                    "context_data_provided": context_data is not None
                }
            ) from e
        except Exception as e:
            self.logger.error(f"Unexpected error in LLM response generation: {str(e)}")
            raise LLMException(
                message="Unexpected error in LLM response generation",
                details={"original_error": str(e)}
            ) from e