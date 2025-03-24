import logging
import discord
from discord.ext import commands
from ..config import config

logger = logging.getLogger('baller.client')

class BallerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )

        logger.info("BallerBot initialized")
    
    async def setup_hook(self):
        # Load extensions/cogs
        from .commands import BallerCommands
        await self.add_cog(BallerCommands(self))
        print(f"Bot is ready as {self.user}")
    
    async def start_bot(self):
        """Start the bot with the provided token"""
        logger.info(f"Starting bot with token: {config.DISCORD_TOKEN[:5]}...")
        try:
            await self.start(config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

    async def on_ready(self):
        # Your existing on_ready method
        logger.info(f"Bot is ready as {self.user.name}#{self.user.discriminator}")
        logger.info(f"Bot user ID: {self.user.id}")
        