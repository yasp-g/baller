import discord
from discord.ext import commands
from ..api.sports import FootballAPI
from ..api.llm import LLMClient
from datetime import datetime, date, timedelta

class BallerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.football_api = FootballAPI()
        self.llm_client = LLMClient()
        
        # Register components with LLMClient for error handling
        self.llm_client.register_api(self.football_api)
        self.llm_client.register_commands(self)
        
        self.conversation_history = {}  # Store conversation history by user
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return
        
        # Check if the message is in a DM or mentions the bot
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.bot.user in message.mentions
        
        if is_dm or is_mention:
            # Remove the mention from the message content if present
            content = message.content
            if is_mention:
                content = content.replace(f'<@{self.bot.user.id}>', '').strip()
            
            # Process the user's message
            await self.process_conversation(message, content)
    
    async def process_conversation(self, message, content):
        """Process a conversational message using the LLM and football-data API"""
        user_id = str(message.author.id)
        
        # Initialize conversation history for this user if it doesn't exist
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # Add user message to history
        self.conversation_history[user_id].append({"role": "user", "content": content})
        
        # Analyze the message to determine what football data we need
        relevant_data = None
        
        if "standing" in content.lower() or "table" in content.lower():
            # Premier League standings (competition ID 2021 is Premier League)
            if "premier" in content.lower() or "epl" in content.lower():
                standings = await self.football_api.get_standings(competition_id=2021)
                relevant_data = standings
            # Bundesliga standings (competition ID 2002)
            elif "bundesliga" in content.lower():
                standings = await self.football_api.get_standings(competition_id=2002)
                relevant_data = standings
            # La Liga standings (competition ID 2014)
            elif "la liga" in content.lower() or "laliga" in content.lower():
                standings = await self.football_api.get_standings(competition_id=2014)
                relevant_data = standings

        elif "match" in content.lower() or "game" in content.lower() or "fixture" in content.lower():
            today = date.today()
            
            # Get today's matches
            if "today" in content.lower():
                matches = await self.football_api.get_matches(date_from=today, date_to=today)
                relevant_data = matches
            # Get tomorrow's matches
            elif "tomorrow" in content.lower():
                tomorrow = today + timedelta(days=1)
                matches = await self.football_api.get_matches(date_from=tomorrow, date_to=tomorrow)
                relevant_data = matches
            # Get weekend matches
            elif "weekend" in content.lower():
                # Calculate the next weekend (Sat-Sun)
                days_until_saturday = (5 - today.weekday()) % 7
                if days_until_saturday == 0:  # It's already Saturday
                    saturday = today
                else:
                    saturday = today + timedelta(days=days_until_saturday)
                sunday = saturday + timedelta(days=1)
                matches = await self.football_api.get_matches(date_from=saturday, date_to=sunday)
                relevant_data = matches
            # Default to next 7 days
            else:
                next_week = today + timedelta(days=7)
                matches = await self.football_api.get_matches(date_from=today, date_to=next_week)
                relevant_data = matches
            
            # Filter by competition if mentioned
            if "premier" in content.lower() or "epl" in content.lower() and relevant_data:
                # Re-fetch with competition filter
                if isinstance(relevant_data.get("matches"), list):
                    date_from = relevant_data.get("resultSet", {}).get("first")
                    date_to = relevant_data.get("resultSet", {}).get("last")
                    if date_from and date_to:
                        matches = await self.football_api.get_matches(
                            date_from=date_from, 
                            date_to=date_to,
                            competitions="2021"  # Premier League
                        )
                        relevant_data = matches
        
        # Generate response using the LLM
        response = await self.llm_client.generate_response(content, relevant_data)
        
        # Add bot response to history
        self.conversation_history[user_id].append({"role": "assistant", "content": response})
        
        # Send the response
        await message.channel.send(response)
    
    @commands.command(name="competitions")
    async def competitions(self, ctx, area=None):
        """Get available competitions, optionally filtered by country area ID"""
        try:
            competitions = await self.football_api.get_competitions(areas=area)
            
            embed = discord.Embed(title="Available Football Competitions", color=discord.Color.blue())
            
            for comp in competitions.get("competitions", [])[:10]:  # Limit to top 10
                embed.add_field(
                    name=f"{comp.get('name')} ({comp.get('area', {}).get('name')})",
                    value=f"ID: {comp.get('id')}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        except Exception as e:
            # Record the error for LLM context
            self.llm_client.record_command_error(e, command="competitions")
            await ctx.send(f"Sorry, I couldn't retrieve the competitions: {str(e)}")
    
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
                await ctx.send(f"No standings data available for {league_name}")
                return
                
            for team in standings_data[:10]:  # Limit to top 10
                embed.add_field(
                    name=f"{team.get('position')}. {team.get('team', {}).get('name')}",
                    value=f"Points: {team.get('points')} | W-D-L: {team.get('won')}-{team.get('draw')}-{team.get('lost')}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        except Exception as e:
            # Record the error for LLM context
            self.llm_client.record_command_error(e, command=f"standings {competition_id}")
            await ctx.send(f"Sorry, I couldn't retrieve the standings: {str(e)}")
        
    @commands.command(name="matches")
    async def matches(self, ctx, competition_id: int = None, days: int = 7):
        """Get upcoming matches, optionally filtered by competition ID"""
        try:
            today = date.today()
            end_date = today + timedelta(days=days)
            
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
            
            match_list = matches.get("matches", [])
            
            if not match_list:
                await ctx.send("No upcoming matches found for this period.")
                return
            
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
                
                # Add competition name to title if filtering
                if competition_id:
                    comp_name = day_matches[0].get("competition", {}).get("name", "")
                    embed.title = f"{comp_name} Matches for {nice_date}"
                
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
                    embed.add_field(
                        name=f"{home} vs {away}",
                        value=f"🕒 {time}" + (f" | 🏆 {comp}" if not competition_id else ""),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
        except Exception as e:
            # Record the error for LLM context
            self.llm_client.record_command_error(e, command=f"standings {competition_id}")
            await ctx.send(f"Sorry, I couldn't retrieve the standings: {str(e)}")