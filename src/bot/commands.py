import logging
import discord
import asyncio
import os
import json
import time
from discord.ext import commands
from discord import ui, ButtonStyle
from typing import Optional, Dict, Any, List, Union
from ..api.sports import FootballAPI
from ..api.llm import LLMClient
from datetime import datetime, date, timedelta
from ..config import config
from .conversation import ConversationManager
from .preferences import UserPreferencesManager
from ..exceptions import (
    BallerException,
    APIException,
    CommandError,
    ValidationError,
    LLMException
)

# Get logger for this module
logger = logging.getLogger('baller.commands')

class BallerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.football_api = FootballAPI()
        self.llm_client = LLMClient()
        self.conversation_manager = ConversationManager()
        self.preferences_manager = UserPreferencesManager(config)

        logger.info(f"BallerCommands initialized with bot ID: {self.bot.user.id if self.bot.user else 'Not available yet'}")
        
        # Register components with LLMClient for error handling
        self.llm_client.register_api(self.football_api)
        self.llm_client.register_commands(self)
        
        # Start conversation cleanup task when bot is ready
        self.bot.loop.create_task(self._start_conversation_manager())
        
    async def _start_conversation_manager(self):
        """Start the conversation manager after the bot is ready."""
        await self.bot.wait_until_ready()
        self.conversation_manager.start_cleanup_task(self.bot.loop)
        logger.info("Conversation manager started")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            logger.debug(f"Ignoring message from self: {message.content[:30]}...")
            return
        
        logger.debug(f"Received message: '{message.content}' from {message.author}")
        logger.debug(f"Channel type: {type(message.channel)}, Is DM: {isinstance(message.channel, discord.DMChannel)}")

        # Check if the message is in a DM or mentions the bot
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.bot.user in message.mentions

        logger.info(f"Message analysis - Is DM: {is_dm}, Is mention: {is_mention}")
        logger.debug(f"Bot mentions in message: {[m.id for m in message.mentions if m.bot]}")
        logger.debug(f"Bot user ID: {self.bot.user.id}")
        
        if is_dm or is_mention:
            logger.info(f"Processing conversational message: {message.content[:50]}...")
            
            # Remove the mention from the message content if present
            content = message.content
            if is_mention:
                # Log the original content and the bot's user ID format
                logger.debug(f"Original content: {content}")
                logger.debug(f"Removing mention format: <@{self.bot.user.id}>")
                
                # Try different mention formats
                mention_formats = [
                    f'<@{self.bot.user.id}>',  # Standard mention
                    f'<@!{self.bot.user.id}>'  # Nickname mention
                ]
                
                for mention_format in mention_formats:
                    if mention_format in content:
                        logger.debug(f"Found mention format: {mention_format}")
                        content = content.replace(mention_format, '').strip()
                        break
                
                logger.debug(f"Content after mention removal: {content}")
            
            # Process the user's message
            await self.process_conversation(message, content)
        else:
            logger.debug(f"Ignoring non-conversational message: {message.content[:30]}...")
    
    # Feedback view for button interactions
    class FeedbackView(ui.View):
        def __init__(self, commands_instance):
            super().__init__(timeout=None)  # Buttons don't time out
            self.commands = commands_instance
            self.config = config
            
            # Add the buttons with configured styles and labels
            positive_style = ButtonStyle(int(self.config.FEEDBACK_POSITIVE_STYLE))
            negative_style = ButtonStyle(int(self.config.FEEDBACK_NEGATIVE_STYLE))
            
            self.add_item(ui.Button(
                style=positive_style, 
                label=self.config.FEEDBACK_POSITIVE_LABEL,
                custom_id="feedback_positive"
            ))
            
            self.add_item(ui.Button(
                style=negative_style, 
                label=self.config.FEEDBACK_NEGATIVE_LABEL,
                custom_id="feedback_negative"
            ))
        
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        """Handle button interactions for feedback."""
        # Only process button interactions with our custom IDs
        if not interaction.data or interaction.data.get("component_type") != 2:  # Type 2 is button
            return
            
        custom_id = interaction.data.get("custom_id", "")
        
        if custom_id == "feedback_positive":
            # Positive feedback (score 8/10)
            user = interaction.user
            message_id = interaction.message.id
            
            logger.info(f"Received positive button feedback from {user.name} (ID: {user.id})")
            self.llm_client.metrics.record("user_feedback_score", 8.0)
            
            # Record detailed feedback
            feedback = {
                "user_id": str(user.id),
                "message_id": str(message_id),
                "rating": 8,
                "type": "button",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store the feedback
            if not hasattr(self, 'user_feedback'):
                self.user_feedback = []
            self.user_feedback.append(feedback)
            
            # Acknowledge the interaction
            await interaction.response.send_message("Thanks for your positive feedback!", ephemeral=True)
            
        elif custom_id == "feedback_negative":
            # Negative feedback (score 3/10)
            user = interaction.user
            message_id = interaction.message.id
            
            logger.info(f"Received negative button feedback from {user.name} (ID: {user.id})")
            self.llm_client.metrics.record("user_feedback_score", 3.0)
            
            # Record detailed feedback
            feedback = {
                "user_id": str(user.id),
                "message_id": str(message_id),
                "rating": 3,
                "type": "button",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store the feedback
            if not hasattr(self, 'user_feedback'):
                self.user_feedback = []
            self.user_feedback.append(feedback)
            
            # Acknowledge the interaction
            await interaction.response.send_message("Thanks for your feedback. We'll work on improving!", ephemeral=True)
    
    async def process_conversation(self, message, content):
        """Process a conversational message using the LLM and football-data API"""
        user_id = str(message.author.id)
        
        # Set user context for all subsequent logs in this request
        from ..main import request_context, get_request_id
        request_id = get_request_id()
        request_context.set_context(user_id=user_id, request_id=request_id)
        
        logger.info(f"Processing conversation for user {user_id} with content: {content[:50]}...")
        
        # Initialize content filter if needed
        if not hasattr(self, 'content_filter'):
            from .content_filter import ContentFilter
            self.content_filter = ContentFilter(self.llm_client)
        
        # Initialize evaluation sampler if needed
        if not hasattr(self, 'evaluator'):
            from ..api.evaluation import EvaluationSampler
            from ..config import config
            self.evaluator = EvaluationSampler(
                self.llm_client,
                sampling_rate=config.EVALUATION_SAMPLING_RATE,
                max_daily_samples=config.EVALUATION_MAX_DAILY_SAMPLES
            )
        
        # Check if content is relevant to football/soccer
        is_relevant, explanation = await self.content_filter.is_relevant(content)
        
        if not is_relevant:
            logger.info(f"Message not relevant to football/soccer: {explanation}")
            response = f"I'm a football/soccer assistant and can only help with football-related questions. {explanation}"
            
            # Add the messages to conversation history
            self.conversation_manager.add_message(user_id, "user", content)
            self.conversation_manager.add_message(user_id, "assistant", response)
            
            # Send the response and return early
            await message.channel.send(response)
            return
        
        # Add user message to conversation history (for relevant messages)
        self.conversation_manager.add_message(user_id, "user", content)
        
        # Get user preferences
        user_prefs = self.preferences_manager.get_user_preferences(user_id)
        followed_teams = user_prefs.get("followed_teams", set())
        
        # Initialize intent system if not already done
        if not hasattr(self, 'intent_processor'):
            from .intent.entities import EntityExtractor
            from .intent.cache import EntityCache
            from .intent.processor import IntentProcessor
            
            # Initialize the entity cache
            logger.info("Initializing entity cache...")
            self.entity_cache = EntityCache(self.football_api)
            
            # Initialize the entity extractor
            self.entity_extractor = EntityExtractor()
            
            # Initialize the intent processor
            self.intent_processor = IntentProcessor(
                entity_extractor=self.entity_extractor,
                entity_cache=self.entity_cache
            )
            
            # Start loading the entity cache (don't wait for it to complete)
            asyncio.create_task(self.entity_cache.initialize())
            logger.info("Intent system initialized")
        
        # Analyze the message to determine what football data we need
        relevant_data = None
        intent_info = None
        logger.debug(f"Processing message with intent system")
        
        try:
            # Process with the intent system
            intent = await self.intent_processor.process_message(user_id, content)
            
            if intent:
                # Add intent to log context
                from ..main import request_context
                intent_data = {
                    "name": intent.name,
                    "confidence": intent.confidence,
                    "has_entities": len(intent.entities) > 0
                }
                request_context.set_context(intent=json.dumps(intent_data))
                
                logger.info(f"Detected intent: {intent.name} with confidence {intent.confidence:.2f}")
                intent_info = intent.to_dict()
                
                # Map intent to API calls
                if intent.name == "get_standings" and "competition_id" in intent.api_params:
                    # Get standings for a competition
                    competition_id = intent.api_params["competition_id"]
                    logger.info(f"Fetching standings for competition {competition_id}")
                    try:
                        standings = await self.football_api.get_standings(competition_id=competition_id)
                        relevant_data = standings
                        logger.debug("Standings fetched successfully")
                    except APIException as e:
                        logger.error(f"API error fetching standings: {e}")
                        self.llm_client.record_api_error(e, f"standings/competition-{competition_id}")
                
                elif intent.name == "get_matches":
                    # Get matches with optional filters
                    date_from = intent.api_params.get("date_from", date.today().isoformat())
                    date_to = intent.api_params.get("date_to")
                    status = intent.api_params.get("status")
                    competition_id = intent.api_params.get("competition_id")
                    
                    logger.info(f"Fetching matches from {date_from} to {date_to or 'N/A'}")
                    try:
                        if competition_id:
                            matches = await self.football_api.get_competition_matches(
                                competition_id=competition_id,
                                date_from=date_from,
                                date_to=date_to,
                                status=status
                            )
                        else:
                            matches = await self.football_api.get_matches(
                                date_from=date_from,
                                date_to=date_to,
                                status=status,
                                competitions=competition_id  # Will be None if not specified
                            )
                        relevant_data = matches
                        logger.debug("Matches fetched successfully")
                    except APIException as e:
                        logger.error(f"API error fetching matches: {e}")
                        self.llm_client.record_api_error(e, "matches/date-range")
                
                elif intent.name == "get_team_matches" and "team_id" in intent.api_params:
                    # Get matches for a specific team
                    team_id = intent.api_params["team_id"]
                    date_from = intent.api_params.get("date_from", date.today().isoformat())
                    date_to = intent.api_params.get("date_to")
                    status = intent.api_params.get("status")
                    
                    logger.info(f"Fetching matches for team {team_id}")
                    try:
                        matches = await self.football_api.get_team_matches(
                            team_id=team_id,
                            date_from=date_from,
                            date_to=date_to,
                            status=status
                        )
                        relevant_data = matches
                        logger.debug("Team matches fetched successfully")
                    except APIException as e:
                        logger.error(f"API error fetching team matches: {e}")
                        self.llm_client.record_api_error(e, f"matches/team-{team_id}")
                
                elif intent.name == "get_competition_teams" and "competition_id" in intent.api_params:
                    # Get teams for a competition
                    competition_id = intent.api_params["competition_id"]
                    logger.info(f"Fetching teams for competition {competition_id}")
                    try:
                        teams = await self.football_api.get_competition_teams(competition_id=competition_id)
                        relevant_data = teams
                        logger.debug("Competition teams fetched successfully")
                    except APIException as e:
                        logger.error(f"API error fetching competition teams: {e}")
                        self.llm_client.record_api_error(e, f"teams/competition-{competition_id}")
                
                elif intent.name == "get_team" and "team_id" in intent.api_params:
                    # Get info about a specific team
                    team_id = intent.api_params["team_id"]
                    logger.info(f"Fetching info for team {team_id}")
                    try:
                        team = await self.football_api.get_team(team_id=team_id)
                        relevant_data = team
                        logger.debug("Team info fetched successfully")
                    except APIException as e:
                        logger.error(f"API error fetching team info: {e}")
                        self.llm_client.record_api_error(e, f"team/{team_id}")
                
                elif intent.name == "get_competition_scorers" and "competition_id" in intent.api_params:
                    # Get scorers for a competition
                    competition_id = intent.api_params["competition_id"]
                    logger.info(f"Fetching scorers for competition {competition_id}")
                    try:
                        scorers = await self.football_api.get_scorers(competition_id=competition_id)
                        relevant_data = scorers
                        logger.debug("Competition scorers fetched successfully")
                    except APIException as e:
                        logger.error(f"API error fetching competition scorers: {e}")
                        self.llm_client.record_api_error(e, f"scorers/competition-{competition_id}")
            
            # Fall back to keyword matching if no intent was detected or confidence is low
            if not intent or intent.confidence < 0.4 or not relevant_data:
                logger.info("Falling back to keyword matching for intent detection")
                
                if "standing" in content.lower() or "table" in content.lower():
                    logger.debug("Found standing/table keyword")
                    # Premier League standings (competition ID 2021 is Premier League)
                    if "premier" in content.lower() or "epl" in content.lower():
                        logger.info("Fetching Premier League standings")
                        try:
                            standings = await self.football_api.get_standings(competition_id=2021)
                            relevant_data = standings
                            logger.debug("Premier League standings fetched successfully")
                        except APIException as e:
                            logger.error(f"API error fetching Premier League standings: {e}")
                            self.llm_client.record_api_error(e, "standings/premier-league")
                    # Bundesliga standings (competition ID 2002)
                    elif "bundesliga" in content.lower():
                        logger.info("Fetching Bundesliga standings")
                        try:
                            standings = await self.football_api.get_standings(competition_id=2002)
                            relevant_data = standings
                            logger.debug("Bundesliga standings fetched successfully")
                        except APIException as e:
                            logger.error(f"API error fetching Bundesliga standings: {e}")
                            self.llm_client.record_api_error(e, "standings/bundesliga")
                    # La Liga standings (competition ID 2014)
                    elif "la liga" in content.lower() or "laliga" in content.lower():
                        logger.info("Fetching La Liga standings")
                        try:
                            standings = await self.football_api.get_standings(competition_id=2014)
                            relevant_data = standings
                            logger.debug("La Liga standings fetched successfully")
                        except APIException as e:
                            logger.error(f"API error fetching La Liga standings: {e}")
                            self.llm_client.record_api_error(e, "standings/la-liga")

                elif "match" in content.lower() or "game" in content.lower() or "fixture" in content.lower():
                    logger.debug("Found match/game/fixture keyword")
                    today = date.today()
                    
                    # Get today's matches
                    if "today" in content.lower():
                        logger.info(f"Fetching today's matches ({today})")
                        try:
                            matches = await self.football_api.get_matches(date_from=today, date_to=today)
                            relevant_data = matches
                            logger.debug("Today's matches fetched successfully")
                        except APIException as e:
                            logger.error(f"API error fetching today's matches: {e}")
                            self.llm_client.record_api_error(e, "matches/today")
                    # Get tomorrow's matches
                    elif "tomorrow" in content.lower():
                        tomorrow = today + timedelta(days=1)
                        logger.info(f"Fetching tomorrow's matches ({tomorrow})")
                        try:
                            matches = await self.football_api.get_matches(date_from=tomorrow, date_to=tomorrow)
                            relevant_data = matches
                            logger.debug("Tomorrows's matches fetched successfully")
                        except APIException as e:
                            logger.error(f"API error fetching tomorrow's matches: {e}")
                            self.llm_client.record_api_error(e, "matches/tomorrow")
                    # Get weekend matches
                    elif "weekend" in content.lower():
                        # Calculate the next weekend (Sat-Sun)
                        days_until_saturday = (5 - today.weekday()) % 7
                        if days_until_saturday == 0:  # It's already Saturday
                            saturday = today
                        else:
                            saturday = today + timedelta(days=days_until_saturday)
                        sunday = saturday + timedelta(days=1)
                        logger.info(f"Fetching weekend matches (from {saturday} to {sunday})")
                        try:
                            matches = await self.football_api.get_matches(date_from=saturday, date_to=sunday)
                            relevant_data = matches
                            logger.debug("Fetching this weekend's matches")
                        except APIException as e:
                            logger.error(f"API error fetching weekend matches: {e}")
                            self.llm_client.record_api_error(e, "matches/weekend")
                    # Default to next 7 days
                    else:
                        next_week = today + timedelta(days=7)
                        logger.info(f"Fetching matches for the next 7 days (until {next_week})")
                        try:
                            matches = await self.football_api.get_matches(date_from=today, date_to=next_week)
                            relevant_data = matches
                            logger.debug("Next 7 days' matches fetched successfully")
                        except APIException as e:
                            logger.error(f"API error fetching next 7 days matches: {e}")
                            self.llm_client.record_api_error(e, "matches/week")
                    
                    # Filter by competition if mentioned
                    if "premier" in content.lower() or "epl" in content.lower() and relevant_data:
                        # Re-fetch with competition filter
                        if isinstance(relevant_data.get("matches"), list):
                            date_from = relevant_data.get("resultSet", {}).get("first")
                            date_to = relevant_data.get("resultSet", {}).get("last")
                            if date_from and date_to:
                                try:
                                    matches = await self.football_api.get_matches(
                                        date_from=date_from, 
                                        date_to=date_to,
                                        competitions="2021"  # Premier League
                                    )
                                    relevant_data = matches
                                except APIException as e:
                                    logger.error(f"API error fetching Premier League filtered matches: {e}")
                                    self.llm_client.record_api_error(e, "matches/premier-league")
            
            logger.info(f"Relevant data type retrieved: {type(relevant_data).__name__ if relevant_data else 'None'}")
            if relevant_data:
                logger.debug(f"Data keys: {relevant_data.keys() if hasattr(relevant_data, 'keys') else 'No keys'}")

            # Generate response using the LLM
            logger.info("Generating response using LLM")
            try:
                # Include intent information in the context data
                context_data = relevant_data
                if intent_info:
                    # If we have intent info but no relevant data, pass the intent info as the context
                    if not context_data:
                        context_data = {"intent": intent_info}
                    # Otherwise, add intent info to the existing context data
                    elif isinstance(context_data, dict):
                        context_data["intent"] = intent_info
                
                # Use streaming response for better user experience
                response_stream = await self.llm_client.generate_response(
                    content, 
                    context_data,
                    user_preferences=user_prefs,
                    stream=True
                )
                
                # Initialize a discord message for streaming updates
                discord_message = await message.channel.send("*Thinking...*")
                
                # For storing the complete response
                full_response = []
                response_text = ""
                buffer = []
                last_update_time = time.time()
                
                # Process streaming chunks
                async for chunk in response_stream:
                    # Add chunk to buffer and complete response
                    buffer.append(chunk)
                    full_response.append(chunk)
                    
                    # Update the message every 0.5 seconds or when buffer reaches certain size
                    current_time = time.time()
                    if current_time - last_update_time > 0.5 or len("".join(buffer)) > 100:
                        response_text += "".join(buffer)
                        buffer = []
                        
                        # Update Discord message (handle message length limits)
                        if len(response_text) > 2000:
                            # If we exceed Discord's limit, split into multiple messages
                            await discord_message.edit(content=response_text[:2000])
                            discord_message = await message.channel.send(response_text[2000:])
                            response_text = response_text[2000:]
                        else:
                            await discord_message.edit(content=response_text)
                            
                        last_update_time = current_time
                
                # Final update with any remaining buffer
                if buffer:
                    response_text += "".join(buffer)
                    
                    # Determine if we should add feedback buttons
                    from ..config import config
                    add_feedback = config.COLLECT_FEEDBACK
                    
                    # Add feedback prompt if configured
                    view = None
                    if add_feedback:
                        # Add the prompt note to the message
                        feedback_note = f"\n\n_{config.FEEDBACK_PROMPT}_"
                        if len(response_text) + len(feedback_note) <= 2000:
                            response_text += feedback_note
                        
                        # Create the feedback view with buttons
                        view = self.FeedbackView(self)
                    
                    # Send or edit the message
                    if len(response_text) > 2000:
                        # For long messages, split them
                        await discord_message.edit(content=response_text[:2000])
                        
                        # Only add feedback to the last part
                        if add_feedback and view:
                            # Send the overflow as a new message with feedback buttons
                            await message.channel.send(content=response_text[2000:], view=view)
                        else:
                            # Send without buttons
                            await message.channel.send(content=response_text[2000:])
                    else:
                        # For messages that fit in one part
                        if add_feedback and view:
                            await discord_message.edit(content=response_text, view=view)
                        else:
                            await discord_message.edit(content=response_text)
                
                # Final complete response for history and evaluation (without feedback prompt)
                response = "".join(full_response)
                logger.debug(f"LLM response generated: {response[:50]}...")
                
            except LLMException as e:
                logger.error(f"LLM error: {e}")
                self.llm_client.record_command_error(e, command="conversation")
                response = f"Sorry, I encountered an issue with my AI service: {e.message}"
                await message.channel.send(response)
            except Exception as e:
                logger.error(f"Unexpected error generating LLM response: {e}")
                error = CommandError(
                    message=f"Unexpected error in conversation processing: {str(e)}",
                    command_name="conversation",
                    details={"content_length": len(content)}
                )
                self.llm_client.record_command_error(error, command="conversation")
                response = f"Sorry, I encountered an unexpected error: {error.message}"
                await message.channel.send(response)
            
            # Add bot response to history
            self.conversation_manager.add_message(user_id, "assistant", response)
            
            # Sample for evaluation (asynchronously, doesn't block user experience)
            logger.info("Scheduling response evaluation")
            asyncio.create_task(self._evaluate_response_sample(
                user_message=content,
                bot_response=response,
                context_data=context_data
            ))
            
            logger.debug("Response processing completed successfully")
                
        except Exception as e:
            logger.error(f"Critical error in conversation processing: {e}")
            try:
                await message.channel.send(f"Sorry, I encountered a critical error processing your message.")
            except:
                pass  # Nothing more we can do if we can't even send an error message
    
    @commands.command(name="competitions")
    async def competitions(self, ctx, area=None):
        """Get available competitions, optionally filtered by country area ID"""
        try:
            if area and not area.isdigit():
                raise ValidationError(
                    message="Area ID must be a number", 
                    field="area"
                )
                
            competitions = await self.football_api.get_competitions(areas=area)
            
            embed = discord.Embed(title="Available Football Competitions", color=discord.Color.blue())
            
            for comp in competitions.get("competitions", [])[:10]:  # Limit to top 10
                embed.add_field(
                    name=f"{comp.get('name')} ({comp.get('area', {}).get('name')})",
                    value=f"ID: {comp.get('id')}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except ValidationError as e:
            # User input validation error
            self.llm_client.record_command_error(e, command="competitions")
            await ctx.send(f"⚠️ {e.message}")
            
        except APIException as e:
            # API-related errors
            self.llm_client.record_command_error(e, command="competitions")
            await ctx.send(f"🔴 API Error: {e.message}")
            
        except Exception as e:
            # Unexpected errors
            error = CommandError(
                message=f"Unexpected error in competitions command: {str(e)}",
                command_name="competitions",
                details={"area": area}
            )
            self.llm_client.record_command_error(error, command="competitions")
            await ctx.send(f"Sorry, I couldn't retrieve the competitions: {error.message}")
    
    @commands.command(name="standings")
    async def standings(self, ctx, competition_id: int):
        """Get standings for a specific competition"""
        try:
            standings = await self.football_api.get_standings(competition_id)
            
            # Process and display standings
            league_name = standings.get("competition", {}).get("name", "Unknown League")
            
            embed = discord.Embed(title=f"{league_name} Standings", color=discord.Color.green())
            
            standings_data = standings.get("standings", [])[0].get("table", []) if standings.get("standings") else []
            
            if not standings_data:
                raise CommandError(
                    message=f"No standings data available for {league_name}",
                    command_name="standings",
                    details={"competition_id": competition_id, "league_name": league_name}
                )
                
            for team in standings_data[:10]:  # Limit to top 10
                embed.add_field(
                    name=f"{team.get('position')}. {team.get('team', {}).get('name')}",
                    value=f"Points: {team.get('points')} | W-D-L: {team.get('won')}-{team.get('draw')}-{team.get('lost')}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except ValidationError as e:
            # User input validation error
            self.llm_client.record_command_error(e, command="standings")
            await ctx.send(f"⚠️ {e.message}")
            
        except APIException as e:
            # API-related errors
            self.llm_client.record_command_error(e, command="standings")
            await ctx.send(f"🔴 API Error: {e.message}")
            
        except CommandError as e:
            # Command-specific errors
            self.llm_client.record_command_error(e, command="standings")
            await ctx.send(f"ℹ️ {e.message}")
            
        except Exception as e:
            # Unexpected errors
            error = CommandError(
                message=f"Unexpected error retrieving standings: {str(e)}",
                command_name="standings",
                details={"competition_id": competition_id}
            )
            self.llm_client.record_command_error(error, command=f"standings {competition_id}")
            await ctx.send(f"Sorry, I couldn't retrieve the standings: {error.message}")
        
    @commands.command(name="conversation_stats")
    async def conversation_stats(self, ctx):
        """Get statistics about active conversations"""
        try:
            stats = self.conversation_manager.get_stats()
            
            embed = discord.Embed(
                title="Conversation Statistics",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Active Conversations",
                value=str(stats["active_count"]),
                inline=True
            )
            
            if stats["active_count"] > 0:
                embed.add_field(
                    name="Total Messages",
                    value=str(stats["total_messages"]),
                    inline=True
                )
                
                embed.add_field(
                    name="Average Messages",
                    value=f"{stats['avg_messages_per_conversation']:.1f} per conversation",
                    inline=True
                )
                
                oldest = stats["oldest_created"]
                if oldest:
                    age = datetime.now() - oldest
                    embed.add_field(
                        name="Oldest Conversation",
                        value=f"{age.days}d {age.seconds//3600}h ago",
                        inline=True
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            await ctx.send("Error retrieving conversation statistics")
    
    @commands.command(name="matches")
    async def matches(self, ctx, competition_id: int = None, days: int = 7, team: str = None):
        """Get upcoming matches, optionally filtered by competition ID or team
        
        Use 'my' as the team parameter to show only matches for your followed teams
        """
        try:
            today = date.today()
            end_date = today + timedelta(days=days)
            user_id = str(ctx.author.id)
            
            # Fetch user preferences for all cases
            user_prefs = self.preferences_manager.get_user_preferences(user_id)
            followed_teams = user_prefs.get("followed_teams", set())
            followed_teams_lower = {t.lower() for t in followed_teams} if followed_teams else set()
            
            # Get matches data
            if competition_id:
                matches = await self.football_api.get_competition_matches(
                    competition_id=competition_id,
                    date_from=today,
                    date_to=end_date,
                    status="SCHEDULED"
                )
            else:
                matches = await self.football_api.get_matches(
                    date_from=today,
                    date_to=end_date,
                    status="SCHEDULED"
                )
                
            # Check if we should filter by user's followed teams
            if team and team.lower() == "my":
                if not followed_teams:
                    await ctx.send("You're not following any teams yet. Use `!follow <team name>` to start following a team.")
                    return
            
            match_list = matches.get("matches", [])
            
            if not match_list:
                await ctx.send("No upcoming matches found for this period.")
                return
                
            # Filter by teams if requested
            if team:
                filtered_matches = []
                
                if team.lower() == "my":
                    # Filter by user's followed teams
                    for match in match_list:
                        home_team = match.get("homeTeam", {}).get("name", "").lower()
                        away_team = match.get("awayTeam", {}).get("name", "").lower()
                        
                        # Check if either team is followed (case-insensitive)
                        if home_team in followed_teams_lower or away_team in followed_teams_lower:
                            filtered_matches.append(match)
                    
                    if not filtered_matches:
                        await ctx.send("No upcoming matches found for your followed teams in this period.")
                        return
                else:
                    # Filter by specific team name
                    team_name_lower = team.lower()
                    for match in match_list:
                        home_team = match.get("homeTeam", {}).get("name", "").lower()
                        away_team = match.get("awayTeam", {}).get("name", "").lower()
                        
                        # Check if either team matches the provided name (case-insensitive)
                        if team_name_lower in home_team or team_name_lower in away_team:
                            filtered_matches.append(match)
                    
                    if not filtered_matches:
                        await ctx.send(f"No upcoming matches found for teams matching '{team}' in this period.")
                        return
                
                match_list = filtered_matches
            
            # Group matches by date
            matches_by_date = {}
            for match in match_list:
                match_date = match.get("utcDate", "")[:10]  # Get YYYY-MM-DD format
                if match_date not in matches_by_date:
                    matches_by_date[match_date] = []
                matches_by_date[match_date].append(match)
            
            # Create embeds - one embed per date to avoid hitting limits
            for match_date, day_matches in matches_by_date.items():
                if len(day_matches) == 0:
                    continue
                    
                # Format date nicely
                try:
                    nice_date = datetime.strptime(match_date, "%Y-%m-%d").strftime("%A, %B %d")
                except:
                    nice_date = match_date
                    
                embed = discord.Embed(
                    title=f"Matches for {nice_date}",
                    color=discord.Color.blue()
                )
                
                # Add competition name to title if filtering by competition
                if competition_id:
                    comp_name = day_matches[0].get("competition", {}).get("name", "")
                    embed.title = f"{comp_name} Matches for {nice_date}"
                    
                # Update title based on team filtering
                if team:
                    if team.lower() == "my":
                        embed.title = f"Your Teams' Matches for {nice_date}"
                        embed.color = discord.Color.green()  # Use a different color for personalized content
                    else:
                        embed.title = f"Matches for {team} on {nice_date}"
                        embed.color = discord.Color.gold()  # Use a different color for team filtering
                
                # Add up to 25 matches (Discord field limit)
                for match in day_matches[:25]:
                    home = match.get("homeTeam", {}).get("name", "Unknown")
                    away = match.get("awayTeam", {}).get("name", "Unknown")
                    time = match.get("utcDate", "")
                    # Format time nicely - from ISO format to HH:MM
                    if time:
                        try:
                            time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M UTC")
                        except:
                            time = time.split("T")[1][:5] if "T" in time else ""
                    
                    comp = match.get("competition", {}).get("name", "")
                    match_title = f"{home} vs {away}"
                    
                    # Highlight followed teams with stars if showing all matches 
                    # (no need if already filtered to just followed teams)
                    if team is None and 'followed_teams_lower' in locals():
                        if home.lower() in followed_teams_lower:
                            match_title = f"⭐ {home} vs {away}"
                        elif away.lower() in followed_teams_lower:
                            match_title = f"{home} vs ⭐ {away}"
                    
                    embed.add_field(
                        name=match_title,
                        value=f"🕒 {time}" + (f" | 🏆 {comp}" if not competition_id else ""),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
        except Exception as e:
            # Record the error for LLM context
            self.llm_client.record_command_error(e, command=f"standings {competition_id}")
            await ctx.send(f"Sorry, I couldn't retrieve the standings: {str(e)}")
            
    @commands.command(name="follow")
    async def follow_team(self, ctx, *, team_name):
        """Follow a team to get updates and customize responses"""
        user_id = str(ctx.author.id)
        
        try:
            # Add the team to user's followed list
            result = self.preferences_manager.follow_team(user_id, team_name)
            
            if result:
                await ctx.send(f"✅ You're now following **{team_name}**! You'll get customized responses and updates about this team.")
            else:
                await ctx.send(f"ℹ️ You're already following **{team_name}**.")
                
        except ValidationError as e:
            self.llm_client.record_command_error(e, command="follow")
            await ctx.send(f"⚠️ {e.message}")
            
        except Exception as e:
            logger.error(f"Error following team: {e}")
            error = CommandError(
                message=f"Unexpected error following team: {str(e)}",
                command_name="follow",
                details={"team_name": team_name}
            )
            self.llm_client.record_command_error(error, command="follow")
            await ctx.send(f"Sorry, I couldn't follow that team: {error.message}")
    
    @commands.command(name="unfollow")
    async def unfollow_team(self, ctx, *, team_name):
        """Unfollow a team"""
        user_id = str(ctx.author.id)
        
        try:
            # Remove the team from user's followed list
            result = self.preferences_manager.unfollow_team(user_id, team_name)
            
            if result:
                await ctx.send(f"✅ You're no longer following **{team_name}**.")
            else:
                await ctx.send(f"ℹ️ You weren't following **{team_name}**.")
                
        except ValidationError as e:
            self.llm_client.record_command_error(e, command="unfollow")
            await ctx.send(f"⚠️ {e.message}")
            
        except Exception as e:
            logger.error(f"Error unfollowing team: {e}")
            error = CommandError(
                message=f"Unexpected error unfollowing team: {str(e)}",
                command_name="unfollow",
                details={"team_name": team_name}
            )
            self.llm_client.record_command_error(error, command="unfollow")
            await ctx.send(f"Sorry, I couldn't unfollow that team: {error.message}")
    
    @commands.command(name="myteams")
    async def my_teams(self, ctx):
        """List all teams you're currently following"""
        user_id = str(ctx.author.id)
        
        try:
            # Get the user's followed teams
            teams = self.preferences_manager.get_followed_teams(user_id)
            
            if not teams:
                await ctx.send("You're not following any teams yet. Use `!follow <team name>` to start following a team.")
                return
                
            # Create an embed to display the teams
            embed = discord.Embed(
                title="Your Followed Teams",
                description="Teams you're currently following:",
                color=discord.Color.blue()
            )
            
            # Add each team to the embed
            for team in sorted(teams):
                embed.add_field(name=team, value="Use `!matches` to see upcoming games", inline=True)
                
            embed.set_footer(text="To unfollow a team, use !unfollow <team name>")
            
            await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error listing teams: {e}")
            error = CommandError(
                message=f"Unexpected error listing followed teams: {str(e)}",
                command_name="myteams"
            )
            self.llm_client.record_command_error(error, command="myteams")
            await ctx.send(f"Sorry, I couldn't list your followed teams: {error.message}")
    
    @commands.command(name="monitor")
    async def monitor(self, ctx):
        """Show system health and monitoring statistics"""
        try:
            # Gather monitoring data
            stats = {
                "conversations": self.conversation_manager.get_stats(),
                "uptime": self.bot.get_uptime() if hasattr(self.bot, 'get_uptime') else "N/A"
            }
            
            # Intent processing stats if available
            if hasattr(self, 'intent_processor'):
                intent_counts = {}
                for user_id, context in self.intent_processor.contexts.items():
                    for intent in context.recent_intents:
                        intent_name = intent.get("name", "unknown")
                        if intent_name not in intent_counts:
                            intent_counts[intent_name] = 0
                        intent_counts[intent_name] += 1
                stats["intents"] = intent_counts
                
            # Create embed for monitoring stats
            embed = discord.Embed(
                title="System Monitoring Stats",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Conversations section
            if "conversations" in stats:
                conv_stats = stats["conversations"]
                embed.add_field(
                    name="Active Conversations",
                    value=f"{conv_stats.get('active_count', 0)}"
                )
                embed.add_field(
                    name="Total Messages",
                    value=f"{conv_stats.get('total_messages', 0)}"
                )
                embed.add_field(
                    name="Avg Messages/Conversation",
                    value=f"{conv_stats.get('avg_messages_per_conversation', 0):.1f}"
                )
            
            # Intent stats section
            if "intents" in stats:
                intent_str = "\n".join([f"{name}: {count}" for name, count in stats["intents"].items()])
                if not intent_str:
                    intent_str = "No intents processed yet"
                embed.add_field(
                    name="Intent Distribution",
                    value=f"```\n{intent_str}\n```",
                    inline=False
                )
            
            # System info section
            embed.add_field(
                name="Uptime",
                value=f"{stats.get('uptime', 'N/A')}"
            )
            
            # Send the monitoring data
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error generating monitoring stats: {e}")
            await ctx.send(f"Error generating monitoring stats: {str(e)}")
    
    @commands.command(name="preferences")
    async def preferences(self, ctx, setting=None, value=None):
        """View or update your notification preferences"""
        user_id = str(ctx.author.id)
        
        if not setting:
            # Display current preferences
            prefs = self.preferences_manager.get_user_preferences(user_id)
            
            embed = discord.Embed(
                title="Your Preferences",
                color=discord.Color.blue()
            )
            
            # Show followed teams
            teams = prefs.get("followed_teams", set())
            teams_str = ", ".join(sorted(teams)) if teams else "None"
            embed.add_field(
                name="Followed Teams",
                value=teams_str,
                inline=False
            )
            
            # Show notification settings
            notifications = prefs.get("notification_settings", {})
            embed.add_field(
                name="Game Reminders",
                value="Enabled" if notifications.get("game_reminders", False) else "Disabled",
                inline=True
            )
            
            embed.add_field(
                name="Score Updates",
                value="Enabled" if notifications.get("score_updates", False) else "Disabled",
                inline=True
            )
            
            embed.set_footer(text="Use !preferences <setting> <on/off> to change settings")
            
            await ctx.send(embed=embed)
            return
            
        # Update a specific preference
        if setting.lower() not in ["game_reminders", "score_updates"]:
            await ctx.send("⚠️ Unknown preference setting. Available settings: game_reminders, score_updates")
            return
            
        if not value or value.lower() not in ["on", "off", "true", "false"]:
            await ctx.send("⚠️ Please specify 'on' or 'off' for the setting value.")
            return
            
        # Convert value to boolean
        bool_value = value.lower() in ["on", "true"]
        
        try:
            self.preferences_manager.set_notification_setting(user_id, setting.lower(), bool_value)
            await ctx.send(f"✅ Your preference for **{setting}** has been set to **{'on' if bool_value else 'off'}**.")
        except Exception as e:
            logger.error(f"Error updating preference: {e}")
            await ctx.send(f"Sorry, I couldn't update your preference: {str(e)}")
    
    async def _evaluate_response_sample(
        self,
        user_message: str,
        bot_response: str,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """Sample responses for evaluation."""
        try:
            # Maybe evaluate (based on sampling rate)
            evaluation = await self.evaluator.maybe_evaluate(
                user_message=user_message,
                bot_response=bot_response,
                context_data=context_data
            )
            
            # Log evaluation results if performed
            if evaluation:
                logger.info(f"Response evaluation: {json.dumps(evaluation)}")
                
                # Record the overall score if present
                if evaluation and "OVERALL" in evaluation:
                    overall_score = evaluation["OVERALL"].get("score")
                    if overall_score:
                        self.llm_client.metrics.record("self_evaluation_score", float(overall_score))
        except Exception as e:
            logger.error(f"Error in response evaluation: {str(e)}")
    
    @commands.command(name="feedback")
    async def feedback_command(self, ctx, rating: int, *, comment: str = None):
        """Record user feedback on recent bot responses
        
        Args:
            rating: Score from 1-10
            comment: Optional feedback comment
        """
        if not 1 <= rating <= 10:
            await ctx.send("⚠️ Please provide a rating between 1 and 10")
            return
            
        user_id = str(ctx.author.id)
        timestamp = datetime.now().isoformat()
        
        # Store the feedback
        feedback = {
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "timestamp": timestamp
        }
        
        # Log feedback and store in memory (could be persisted to DB later)
        logger.info(f"User feedback received: {json.dumps(feedback)}")
        if not hasattr(self, 'user_feedback'):
            self.user_feedback = []
        self.user_feedback.append(feedback)
        
        # Also record the score in metrics system
        self.llm_client.metrics.record("user_feedback_score", float(rating))
        
        await ctx.send(f"✅ Thank you for your feedback! (Rating: {rating}/10)")
    
    @commands.command(name="metrics")
    async def metrics_command(self, ctx):
        """Show LLM metrics and response quality statistics"""
        try:
            # Get metrics from LLM client
            all_stats = self.llm_client.metrics.get_all_stats()
            
            # Format the metrics report
            embed = discord.Embed(
                title="Response Quality Metrics",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Add latency stats
            latency = all_stats.get("response_latency", {})
            if latency and latency.get("count", 0) > 0:
                avg = latency.get("avg", 0)
                embed.add_field(
                    name="Average Response Time",
                    value=f"{avg:.2f}s",
                    inline=True
                )
                embed.add_field(
                    name="Min/Max Response Time",
                    value=f"{latency.get('min', 0):.2f}s / {latency.get('max', 0):.2f}s",
                    inline=True
                )
            
            # Add error rate
            error_rate = all_stats.get("error_rate", {})
            if error_rate and error_rate.get("count", 0) > 0:
                rate = error_rate.get("avg", 0) * 100
                embed.add_field(
                    name="Error Rate",
                    value=f"{rate:.2f}%",
                    inline=True
                )
            
            # Add relevance scores
            relevance = all_stats.get("relevance_score", {})
            if relevance and relevance.get("count", 0) > 0:
                avg = relevance.get("avg", 0) * 10  # Scale to 0-10
                embed.add_field(
                    name="Average Relevance Score",
                    value=f"{avg:.1f}/10",
                    inline=True
                )
            
            # Add self-evaluation scores if available
            eval_score = all_stats.get("self_evaluation_score", {})
            if eval_score and eval_score.get("count", 0) > 0:
                avg = eval_score.get("avg", 0)
                embed.add_field(
                    name="LLM Self-Evaluation Score",
                    value=f"{avg:.1f}/10",
                    inline=True
                )
                embed.add_field(
                    name="Evaluations Performed",
                    value=f"{eval_score.get('count', 0)}",
                    inline=True
                )
                
            # Add user feedback scores if available
            user_score = all_stats.get("user_feedback_score", {})
            if user_score and user_score.get("count", 0) > 0:
                avg = user_score.get("avg", 0)
                embed.add_field(
                    name="User Feedback Score",
                    value=f"{avg:.1f}/10",
                    inline=True
                )
                embed.add_field(
                    name="Feedback Count",
                    value=f"{user_score.get('count', 0)}",
                    inline=True
                )
            
            # Add general stats
            total_responses = latency.get("count", 0)
            embed.add_field(
                name="Total Responses",
                value=f"{total_responses}",
                inline=True
            )
            
            # Add message length stats
            length = all_stats.get("response_length", {})
            if length and length.get("count", 0) > 0:
                avg = length.get("avg", 0)
                embed.add_field(
                    name="Average Response Length",
                    value=f"{avg:.0f} characters",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            await ctx.send(f"Error retrieving metrics: {str(e)}")
    
    async def shutdown(self):
        """Clean up resources when shutting down."""
        logger.info("BallerCommands shutting down...")
        
        # Shut down the conversation manager
        try:
            await self.conversation_manager.shutdown()
            logger.info("Conversation manager shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down conversation manager: {e}")
        
        # Shut down the preferences manager
        try:
            await self.preferences_manager.close()
            logger.info("Preferences manager shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down preferences manager: {e}")
        
        # Close the football API client
        try:
            await self.football_api.close()
            logger.info("Football API client closed successfully")
        except Exception as e:
            logger.error(f"Error closing Football API client: {e}")