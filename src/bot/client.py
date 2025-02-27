import discord
from discord.ext import commands
from ..config import DISCORD_TOKEN

class FootballBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )
    
    async def setup_hook(self):
        # Load extensions/cogs
        from .commands import BallerCommands
        await self.add_cog(BallerCommands(self))
        print(f"Bot is ready as {self.user}")
    
    async def start_bot(self):
        """Start the bot with the provided token"""
        await self.start(DISCORD_TOKEN)