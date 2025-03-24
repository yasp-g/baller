import logging
import discord
import asyncio
from discord.ext import commands
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
    
    async def process_conversation(self, message, content):
        """Process a conversational message using the LLM and football-data API"""
        user_id = str(message.author.id)
        logger.info(f"Processing conversation for user {user_id} with content: {content[:50]}...")
        
        # Add user message to conversation history
        self.conversation_manager.add_message(user_id, "user", content)
        
        # Get user preferences
        user_prefs = self.preferences_manager.get_user_preferences(user_id)
        followed_teams = user_prefs.get("followed_teams", set())
        
        # Analyze the message to determine what football data we need
        relevant_data = None
        logger.debug(f"Analyzing message for football data keywords")
        
        try:
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
                response = await self.llm_client.generate_response(
                    content, 
                    relevant_data,
                    user_preferences=user_prefs
                )
                logger.debug(f"LLM response generated: {response[:50]}...")
            except LLMException as e:
                logger.error(f"LLM error: {e}")
                self.llm_client.record_command_error(e, command="conversation")
                response = f"Sorry, I encountered an issue with my AI service: {e.message}"
            except Exception as e:
                logger.error(f"Unexpected error generating LLM response: {e}")
                error = CommandError(
                    message=f"Unexpected error in conversation processing: {str(e)}",
                    command_name="conversation",
                    details={"content_length": len(content)}
                )
                self.llm_client.record_command_error(error, command="conversation")
                response = f"Sorry, I encountered an unexpected error: {error.message}"
            
            # Add bot response to history
            self.conversation_manager.add_message(user_id, "assistant", response)
            
            # Send the response
            logger.info(f"Sending response to channel {message.channel.id}")
            try:
                await message.channel.send(response)
                logger.debug("Response sent successfully")
            except Exception as e:
                logger.error(f"Error sending response: {e}")
                
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