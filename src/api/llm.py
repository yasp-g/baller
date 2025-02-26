import os
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
            base_url="https://api.deepseek.com/v1"  # Deepseek API endpoint
        )
    
    async def generate_response(self, user_message, context_data=None):
        """Generate a conversational response using Deepseek's model"""
        
        system_prompt = """You are a helpful football assistant. You have access to football data 
        provided by API-Sports. Respond conversationally to user queries about football matches, 
        leagues, teams, and players based on the data provided."""
        
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
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"{context}User question: {user_message}"
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I encountered an error generating a response: {str(e)}"