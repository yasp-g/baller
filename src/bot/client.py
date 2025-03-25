import logging
import discord
import time
from datetime import datetime, timedelta
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
        
        # Track bot start time for uptime calculation
        self.start_time = time.time()
        
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
    
    def get_uptime(self):
        """Return the bot's uptime in a human-readable format."""
        uptime_seconds = time.time() - self.start_time
        uptime = timedelta(seconds=int(uptime_seconds))
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    async def close(self):
        """Override close to perform proper shutdown."""
        logger.info("Bot is shutting down, performing cleanup...")
        
        # Log uptime on shutdown
        logger.info(f"Bot uptime at shutdown: {self.get_uptime()}")
        
        # Properly shut down any cogs with cleanup needs
        for cog_name, cog in self.cogs.items():
            if hasattr(cog, 'shutdown'):
                try:
                    logger.info(f"Shutting down cog: {cog_name}")
                    await cog.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down cog {cog_name}: {e}")
        
        # Call parent close method
        await super().close()
        