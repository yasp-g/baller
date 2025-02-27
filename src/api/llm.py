import os
import inspect
import anthropic
from openai import AsyncOpenAI
from ..config import ANTHROPIC_API_KEY, DEEPSEEK_API_KEY

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
        self.client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"  # Deepseek API endpoint
        )
        self.football_api = None
        self.commands = None
        self.api_errors = []
        self.command_errors = []
    
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
    
    async def generate_response(self, user_message, context_data=None):
        """Generate a conversational response using Deepseek's model"""
        
        # Create the system prompt with error context if available
        api_context = ""
        cmd_context = ""
        
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
        
        system_prompt = f"""
        You are a helpful football assistant. You have access to football data
        provided by football-data API. Respond conversationally to user queries about football matches,
        leagues, teams, and players based on the data provided.
        
        {api_context}
        
        {cmd_context}
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
            return response.choices[0].message.content
        except Exception as e:
            return f"I encountered an error generating a response: {str(e)}"