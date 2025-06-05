"""Configuration settings for ReTool-for-Life backend"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""
    
    # API Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_DEFAULT = "gpt-4.1"
    OPENAI_MODEL_FAST = "gpt-4.1"
    
    # Twilio Settings
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    DEMO_PHONE_NUMBER = os.getenv("DEMO_PHONE_NUMBER", "+1234567890")
    
    # Server Settings
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # CORS Settings
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3003",
        FRONTEND_URL
    ]
    
    # Demo Settings
    DEMO_MODE = os.getenv("NODE_ENV", "development") == "development"
    DEMO_DELAY_SECONDS = 2
    
    # Agent Settings
    MAX_CONVERSATION_HISTORY = 20
    AGENT_TEMPERATURE = 0.7
    
    # Evaluation Settings
    EVALUATION_SCENARIOS_PER_AGENT = 4
    MIN_AGENT_SCORE_THRESHOLD = 0.7
    
    # RLAIF Settings
    RLAIF_IMPROVEMENT_THRESHOLD = 0.8  # Trigger improvement if score < this
    RLAIF_WEAK_AREA_THRESHOLD = 0.7   # Areas scoring below this need improvement
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL = 30  # seconds
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        required = ["OPENAI_API_KEY"]
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        return True


# Export settings instance
settings = Settings()