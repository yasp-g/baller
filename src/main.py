import asyncio
import uvicorn
import threading
import signal
import logging
from .config import config
from .bot.client import BallerBot

def setup_logging():
    """Initialize logging for the application"""
    logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=logging_format
    )
    
    # Create loggers for each module with appropriate levels
    loggers = {
        'baller': config.LOG_LEVEL,
        'baller.api': config.LOG_LEVEL,
        'baller.bot': config.LOG_LEVEL,
        'baller.llm': config.LOG_LEVEL,
    }
    
    for logger_name, logger_level in loggers.items():
        logging.getLogger(logger_name).setLevel(logger_level)

def setup():
    """Initialize application with configuration validation"""
    # Setup logging first so we can log validation results
    setup_logging()
    
    # Get logger for this module
    logger = logging.getLogger('baller.main')
    
    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration. Please check your environment variables.")
        raise ValueError("Invalid configuration. Please check your environment variables.")
    
    logger.info(f"Application initialized in {config.ENV} environment")

def run_api_server():
    """Run the FastAPI server in a separate thread"""
    logger = logging.getLogger('baller.main')
    logger.info("Starting API server...")
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=False)

async def run_discord_bot():
    """Run the Discord bot"""
    logger = logging.getLogger('baller.main')
    logger.info("Initializing Discord bot...")
    bot = BallerBot()
    try:
        await bot.start_bot()
    except asyncio.CancelledError:
        logger.info("Bot shutdown initiated...")
    finally:
        logger.info("Closing bot connection...")
        await bot.close()
        logger.info("Bot shutdown complete")

async def main():
    # Initialize the application
    setup()
    
    # Get logger for this module
    logger = logging.getLogger('baller.main')
    
    # Start the API server in a separate thread
    logger.info("Starting API server thread...")
    api_thread = threading.Thread(target=run_api_server)
    api_thread.daemon = True  # Thread will exit when main program exits
    api_thread.start()
    
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda sig=sig: asyncio.create_task(shutdown(sig, loop))
        )
    
    # Run the Discord bot in the main thread
    await run_discord_bot()

async def shutdown(sig, loop):
    """Clean shutdown of the application"""
    logger = logging.getLogger('baller.main')
    logger.info(f"Received exit signal {sig.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    logger.debug(f"Cancelling {len(tasks)} outstanding tasks...")
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("All tasks cancelled, stopping event loop...")
    loop.stop()

if __name__ == "__main__":
    try:
        # Set up minimal logging before main() so we can log early errors
        setup_logging()
        logger = logging.getLogger('baller.main')
        
        logger.info("Starting Baller application...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application shut down by keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)