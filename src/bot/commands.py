import discord
from discord.ext import commands
from ..api.sports import FootballAPI
from ..api.llm import LLMClient

class FootballCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.football_api = FootballAPI()
        self.llm_client = LLMClient()
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
            # Example: fetch Premier League standings (competition ID 2021 is Premier League)
            if "premier" in content.lower() or "epl" in content.lower():
                standings = await self.football_api.get_standings(competition_id=2021)
                relevant_data = standings
        
        elif "match" in content.lower() or "game" in content.lower() or "fixture" in content.lower():
            # Example: get today's matches
            if "today" in content.lower():
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                matches = await self.football_api.get_matches(date_from=today, date_to=today)
                relevant_data = matches
        
        # Generate response using the LLM
        response = await self.llm_client.generate_response(content, relevant_data)
        
        # Add bot response to history
        self.conversation_history[user_id].append({"role": "assistant", "content": response})
        
        # Send the response
        await message.channel.send(response)
    
    @commands.command(name="leagues")
    async def leagues(self, ctx, country=None):
        """Get available leagues, optionally filtered by country"""
        leagues = await self.football_api.get_leagues(country)
        
        embed = discord.Embed(title="Available Football Leagues", color=discord.Color.blue())
        
        for league in leagues.get("response", [])[:10]:  # Limit to top 10
            league_data = league["league"]
            embed.add_field(
                name=f"{league_data['name']} ({league['country']['name']})",
                value=f"ID: {league_data['id']}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="standings")
    async def standings(self, ctx, league_id: int):
        """Get standings for a specific league"""
        standings = await self.football_api.get_standings(league_id)
        
        # Process and display standings
        league_name = standings.get("response", [{}])[0].get("league", {}).get("name", "Unknown League")
        
        embed = discord.Embed(title=f"{league_name} Standings", color=discord.Color.green())
        
        standings_data = standings.get("response", [{}])[0].get("league", {}).get("standings", [[]])[0]
        
        for team in standings_data[:10]:  # Limit to top 10
            embed.add_field(
                name=f"{team['rank']}. {team['team']['name']}",
                value=f"Points: {team['points']} | W-D-L: {team['all']['win']}-{team['all']['draw']}-{team['all']['lose']}",
                inline=False
            )
        
        await ctx.send(embed=embed)