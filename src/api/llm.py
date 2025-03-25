import os
import time
import inspect
import logging
import anthropic
from openai import AsyncOpenAI
from typing import Dict, Any, Optional, List, Union
from ..config import config
from ..exceptions import (
    LLMException,
    ModelUnavailableError,
    PromptError,
    ResponseError
)
from .prompt_templates import (
    ProviderType,
    PromptTemplate,
    get_template,
    TEMPLATES
)
from .evaluation import create_default_metrics, MetricCategory

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
        
        # Determine appropriate provider and client
        self.provider_type = self._detect_provider()
        self.client = self._initialize_client()
        
        # State tracking
        self.football_api = None
        self.commands = None
        self.api_errors = []
        self.command_errors = []
        
        # Initialize metrics tracker
        self.metrics = create_default_metrics()
        
        self.logger.debug(f"LLMClient initialized with provider: {self.provider_type.name}")
    
    def _detect_provider(self) -> ProviderType:
        """Detect which LLM provider to use based on available API keys."""
        if config.DEEPSEEK_API_KEY:
            return ProviderType.OPENAI  # Deepseek uses OpenAI-compatible API
        elif config.ANTHROPIC_API_KEY:
            return ProviderType.ANTHROPIC
        else:
            raise ValueError("No API keys configured for any supported LLM provider")
    
    def _initialize_client(self) -> Union[AsyncOpenAI, anthropic.Anthropic]:
        """Initialize the appropriate API client based on provider."""
        if self.provider_type == ProviderType.OPENAI:
            return AsyncOpenAI(
                api_key=config.DEEPSEEK_API_KEY,
                base_url=config.DEEPSEEK_BASE_URL
            )
        elif self.provider_type == ProviderType.ANTHROPIC:
            return anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported provider type: {self.provider_type}")
    
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
        
    def _prepare_context_data(self, user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Prepare context data for templates.
        
        Args:
            user_preferences: Optional user preferences for personalization
            
        Returns:
            Dictionary of context data for template rendering
        """
        # Build API context
        api_context = ""
        if self.football_api:
            api_context = "Football API is available for fetching data."
            if self.api_errors:
                api_context += "\nRecent API errors:"
                for err in self.api_errors:
                    api_context += f"\n- {err['endpoint'] or 'Unknown endpoint'}: {err['message']}"
        
        # Build command context
        cmd_context = ""
        if self.commands:
            cmd_context = "Discord commands are available for user interaction."
            if self.command_errors:
                cmd_context += "\nRecent command errors:"
                for err in self.command_errors:
                    cmd_context += f"\n- {err['command'] or 'Unknown command'}: {err['message']}"
        
        # Build user preferences context
        user_pref_context = ""
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
        
        return {
            "api_context": api_context,
            "cmd_context": cmd_context,
            "user_pref_context": user_pref_context
        }
    
    async def _call_provider(
        self, 
        template: PromptTemplate,
        user_message: str,
        **kwargs
    ) -> str:
        """Call the appropriate LLM provider with the formatted prompt.
        
        Args:
            template: The prompt template to use
            user_message: The user's message
            **kwargs: Additional parameters for the template
            
        Returns:
            The text response from the LLM
        """
        formatted_prompt = template.format_for_provider(user_message, **kwargs)
        
        # Set default parameters
        params = {
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        try:
            if self.provider_type == ProviderType.OPENAI:
                # OpenAI/Deepseek API format
                response = await self.client.chat.completions.create(
                    model=kwargs.get("model", "deepseek-chat"),
                    messages=formatted_prompt["messages"],
                    **params
                )
                
                if not response.choices or not response.choices[0].message:
                    raise ResponseError("Empty response received from LLM")
                    
                return response.choices[0].message.content
                
            elif self.provider_type == ProviderType.ANTHROPIC:
                # Anthropic API format
                response = await self.client.messages.create(
                    model=kwargs.get("model", "claude-3-opus-20240229"),
                    system=formatted_prompt["system"],
                    messages=formatted_prompt["messages"],
                    **params
                )
                
                if not response.content or not response.content[0].text:
                    raise ResponseError("Empty response received from LLM")
                    
                return response.content[0].text
                
            else:
                raise ValueError(f"Unsupported provider type: {self.provider_type}")
                
        except (anthropic.APIError, anthropic.APIConnectionError) as e:
            raise ModelUnavailableError(
                message=f"LLM API is currently unavailable",
                model_name=kwargs.get("model", "unknown"),
                details={"original_error": str(e)}
            ) from e
        except (anthropic.APIStatusError, anthropic.BadRequestError) as e:
            raise PromptError(
                message="Error in prompt construction or validation",
                details={
                    "original_error": str(e),
                    "user_message_length": len(user_message),
                    "context_data_provided": "context_data" in kwargs
                }
            ) from e
        except ResponseError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in LLM response generation: {str(e)}")
            raise LLMException(
                message="Unexpected error in LLM response generation",
                details={"original_error": str(e)}
            ) from e
    
    async def generate_relevance_check(self, user_message: str) -> str:
        """Determine if a message is relevant to football/soccer.
        
        Args:
            user_message: The user's message to check
            
        Returns:
            String response with YES/NO and explanation
        """
        if not user_message:
            return "YES\nEmpty messages are considered relevant."
            
        try:
            template = get_template("relevance_check")
            # Override provider type to match current client
            template.provider_type = self.provider_type
            
            return await self._call_provider(
                template=template,
                user_message=user_message,
                max_tokens=100,
                temperature=0.1  # Low temperature for more predictable response
            )
            
        except Exception as e:
            self.logger.error(f"Error in relevance check: {e}")
            # Default to relevant if there's an error
            return "YES\nDefault to relevant due to error."
    
    async def generate_response(
        self, 
        user_message: str, 
        context_data: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a conversational response using the configured LLM.
        
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
        start_time = time.time()
        error_occurred = False
        
        try:
            if not user_message:
                raise PromptError("Empty user message provided")
            
            # Get conversation template and prepare context
            template = get_template("football_conversation")
            # Override provider type to match current client
            template.provider_type = self.provider_type
            
            # Prepare context data for template
            context_info = self._prepare_context_data(user_preferences)
            
            # Call LLM provider with template
            response = await self._call_provider(
                template=template,
                user_message=user_message,
                context_data=context_data,
                temperature=0.7,
                **context_info
            )
            
            # Record metrics for successful response
            latency = time.time() - start_time
            self.metrics.record("response_latency", latency)
            self.metrics.record("response_length", len(response))
            self.metrics.record("error_rate", 0)  # 0 = success
            
            # Calculate and record a simple relevance score based on football terms
            football_terms = ["football", "soccer", "team", "match", "league", "player", "goal"]
            relevance_score = sum(term in response.lower() for term in football_terms) / len(football_terms)
            self.metrics.record("relevance_score", relevance_score)
            
            return response
            
        except Exception as e:
            # Record error metric
            error_occurred = True
            self.metrics.record("error_rate", 1)  # 1 = error
            latency = time.time() - start_time
            self.metrics.record("response_latency", latency)
            
            # Re-raise the exception
            raise
            
    async def evaluate_response(
        self,
        user_message: str,
        bot_response: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate the quality of a response using the LLM itself.
        
        Args:
            user_message: The original user message
            bot_response: The response to evaluate
            context_data: The same context data used to generate the response
            
        Returns:
            Dictionary containing evaluation scores and feedback
        """
        try:
            # Get evaluation template
            template = get_template("response_evaluation")
            template.provider_type = self.provider_type
            
            # Call LLM for evaluation
            evaluation_text = await self._call_provider(
                template=template,
                user_message=user_message,
                bot_response=bot_response,
                context_data=context_data,
                temperature=0.3,  # Lower temperature for more consistent evaluation
                max_tokens=500
            )
            
            # Parse evaluation results
            evaluation_results = self._parse_evaluation(evaluation_text)
            
            # Record metrics from evaluation
            if "OVERALL" in evaluation_results:
                self.metrics.record("self_evaluation_score", float(evaluation_results["OVERALL"]["score"]))
                
            return evaluation_results
            
        except Exception as e:
            self.logger.error(f"Error evaluating response: {str(e)}")
            return {"error": str(e)}
            
    def _parse_evaluation(self, evaluation_text: str) -> Dict[str, Dict[str, Any]]:
        """Parse the evaluation response into structured data.
        
        Args:
            evaluation_text: Raw evaluation text from LLM
            
        Returns:
            Structured evaluation data
        """
        result = {}
        
        # Split by lines and process each evaluation criterion
        for line in evaluation_text.strip().split("\n"):
            if ":" not in line:
                continue
                
            # Split criterion and content
            criterion, content = [x.strip() for x in line.split(":", 1)]
            
            # Parse score and justification
            if "-" in content:
                score_str, justification = [x.strip() for x in content.split("-", 1)]
                try:
                    score = float(score_str)
                    result[criterion] = {
                        "score": score,
                        "justification": justification
                    }
                except ValueError:
                    # If score can't be parsed, store the whole content
                    result[criterion] = {"content": content}
            else:
                result[criterion] = {"content": content}
        
        return result