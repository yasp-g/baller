import asyncio
import uvicorn
import threading
import signal
import logging
import json
import uuid
import os
from .config import config
from .bot.client import BallerBot

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for CloudWatch Logs Insights compatibility."""
    
    def format(self, record):
        """Format the log record as JSON."""
        # Create base log object
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            # Add component for easier filtering
            "component": record.name.split('.')[-1] if '.' in record.name else 'main',
        }
        
        # Add request_id if present
        if hasattr(record, 'request_id'):
            log_object["request_id"] = record.request_id
        
        # Add user context if present    
        if hasattr(record, 'user_id'):
            log_object["user_id"] = record.user_id
            
        # Add intent information if present
        if hasattr(record, 'intent'):
            log_object["intent"] = record.intent
            
        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
            log_object["has_error"] = True
            
        # Add duration if present (for performance tracking)
        if hasattr(record, 'duration_ms'):
            log_object["duration_ms"] = record.duration_ms
            
        return json.dumps(log_object)

class RequestContextFilter(logging.Filter):
    """Filter that adds request context to log records."""
    
    def __init__(self, name=''):
        super().__init__(name)
        self.local = threading.local()
        
    def filter(self, record):
        """Add request_id to the log record if one exists."""
        if hasattr(self.local, 'request_id'):
            record.request_id = self.local.request_id
        if hasattr(self.local, 'user_id'):
            record.user_id = self.local.user_id
        if hasattr(self.local, 'intent'):
            record.intent = self.local.intent
        return True
        
    def set_context(self, **kwargs):
        """Set thread-local context values."""
        for key, value in kwargs.items():
            setattr(self.local, key, value)
            
    def clear_context(self):
        """Clear all thread-local context."""
        if hasattr(self.local, '__dict__'):
            self.local.__dict__.clear()

# Create global request context filter
request_context = RequestContextFilter()

def get_request_id():
    """Generate or get current request ID."""
    if not hasattr(request_context.local, 'request_id'):
        request_context.set_context(request_id=str(uuid.uuid4()))
    return request_context.local.request_id

def setup_logging():
    """Initialize logging optimized for container/AWS deployment."""
    # Remove all existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # Set up the JSON formatter for CloudWatch compatibility
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(JsonFormatter())
    
    # Add request context filter to root logger
    root_logger.addFilter(request_context)
    root_logger.setLevel(config.LOG_LEVEL)
    root_logger.addHandler(json_handler)
    
    # Create loggers for each module with appropriate levels
    loggers = {
        'baller': config.LOG_LEVEL,
        'baller.api': config.LOG_LEVEL,
        'baller.bot': config.LOG_LEVEL,
        'baller.llm': config.LOG_LEVEL,
        'baller.intent': config.LOG_LEVEL,
    }
    
    for logger_name, logger_level in loggers.items():
        module_logger = logging.getLogger(logger_name)
        module_logger.setLevel(logger_level)
        
    # Log startup information
    logger = logging.getLogger('baller.main')
    logger.info("Logging initialized with JSON formatting for CloudWatch", 
                extra={"log_type": "startup"})

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