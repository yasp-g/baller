import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

def get_env(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """Get environment variable with validation"""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

class Config:
    """Centralized configuration with validation"""
    
    # Environment
    ENV = get_env("ENV", "development")
    DEBUG = ENV == "development"
    
    # Application modes
    MODE_DEVELOPMENT = "development"  # Local developer testing
    MODE_BETA = "beta"                # Beta testing phase
    MODE_PRODUCTION = "production"    # Live production environment
    
    # Current mode (defaults to ENV value or can be set separately)
    APP_MODE = get_env("APP_MODE", ENV)
    
    # Discord configuration
    DISCORD_TOKEN = get_env("DISCORD_TOKEN", required=True)
    DISCORD_GUILD_ID = get_env("DISCORD_GUILD_ID")
    
    # Football Data API
    FOOTBALL_DATA_API_KEY = get_env("FOOTBALL_DATA_API_KEY", required=True)
    FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
    
    # LLM Configuration
    DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY", required=True)
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")  # Kept for backwards compatibility
    
    # Competition IDs for common leagues
    COMPETITIONS = {
        "premier_league": 2021,
        "la_liga": 2014,
        "bundesliga": 2002,
        "serie_a": 2019,
        "ligue_1": 2015
    }
    
    # Logging
    LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
    
    # Conversation Management
    CONVERSATION_EXPIRY_MINUTES = int(get_env("CONVERSATION_EXPIRY_MINUTES", "30"))
    CONVERSATION_MAX_COUNT = int(get_env("CONVERSATION_MAX_COUNT", "100"))
    CONVERSATION_RETENTION_DAYS = int(get_env("CONVERSATION_RETENTION_DAYS", "30"))
    
    # AWS Integration
    AWS_ENABLED = get_env("AWS_ENABLED", "false").lower() in ("true", "1", "yes")
    
    # LLM Evaluation Settings
    EVALUATION_SAMPLING_RATE = float(get_env("EVALUATION_SAMPLING_RATE", "1.0" if ENV == "development" else "0.05"))
    EVALUATION_MAX_DAILY_SAMPLES = int(get_env("EVALUATION_MAX_DAILY_SAMPLES", "100"))
    
    # Feedback Collection
    COLLECT_FEEDBACK = get_env("COLLECT_FEEDBACK", "true" if APP_MODE in [MODE_DEVELOPMENT, MODE_BETA] else "false").lower() in ("true", "1", "yes")
    FEEDBACK_PROMPT = get_env("FEEDBACK_PROMPT", "🧪 Beta phase: How was this response?")
    FEEDBACK_POSITIVE_LABEL = get_env("FEEDBACK_POSITIVE_LABEL", "Good bot")
    FEEDBACK_NEGATIVE_LABEL = get_env("FEEDBACK_NEGATIVE_LABEL", "Bad bot")
    FEEDBACK_POSITIVE_STYLE = get_env("FEEDBACK_POSITIVE_STYLE", "3")  # Discord Button Style (3=Green)
    FEEDBACK_NEGATIVE_STYLE = get_env("FEEDBACK_NEGATIVE_STYLE", "4")  # Discord Button Style (4=Red)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present"""
        required_keys = [
            cls.DISCORD_TOKEN,
            cls.FOOTBALL_DATA_API_KEY,
            cls.DEEPSEEK_API_KEY
        ]
        
        # Verify all required values are present
        for key in required_keys:
            if not key:
                return False
        return True

# Initialize configuration at import time
config = Config()

# For backwards compatibility
DISCORD_TOKEN = config.DISCORD_TOKEN
DISCORD_GUILD_ID = config.DISCORD_GUILD_ID
FOOTBALL_DATA_API_KEY = config.FOOTBALL_DATA_API_KEY
DEEPSEEK_API_KEY = config.DEEPSEEK_API_KEY
ANTHROPIC_API_KEY = config.ANTHROPIC_API_KEY