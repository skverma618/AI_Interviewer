"""
Configuration management for AI Voice Interviewer System
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for managing environment variables and settings"""
    
    # API Keys
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Audio Settings
    SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", "16000"))
    SILENCE_THRESHOLD: float = float(os.getenv("SILENCE_THRESHOLD", "2.0"))
    MAX_RECORDING_DURATION: int = int(os.getenv("MAX_RECORDING_DURATION", "60"))
    CHUNK_SIZE: int = 1024
    CHANNELS: int = 1
    
    # LLM Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "500"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # File Paths
    QUESTION_BANK_PATH: str = "data/question_bank.json"
    LOGS_DIR: str = "logs"
    SESSIONS_DIR: str = "logs/sessions"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        required_keys = [
            cls.DEEPGRAM_API_KEY,
            cls.OPENAI_API_KEY
        ]
        
        missing_keys = []
        if not cls.DEEPGRAM_API_KEY:
            missing_keys.append("DEEPGRAM_API_KEY")
        if not cls.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
            
        if missing_keys:
            print(f"Missing required environment variables: {', '.join(missing_keys)}")
            return False
            
        return True
    
    @classmethod
    def get_deepgram_config(cls) -> dict:
        """Get Deepgram-specific configuration"""
        return {
            "api_key": cls.DEEPGRAM_API_KEY,
            "sample_rate": cls.SAMPLE_RATE,
            "channels": cls.CHANNELS,
            "encoding": "linear16"
        }
    
    @classmethod
    def get_openai_config(cls) -> dict:
        """Get OpenAI-specific configuration"""
        return {
            "api_key": cls.OPENAI_API_KEY,
            "model": cls.LLM_MODEL,
            "temperature": cls.LLM_TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS
        }
    
    @classmethod
    def get_audio_config(cls) -> dict:
        """Get audio recording configuration"""
        return {
            "sample_rate": cls.SAMPLE_RATE,
            "chunk_size": cls.CHUNK_SIZE,
            "channels": cls.CHANNELS,
            "silence_threshold": cls.SILENCE_THRESHOLD,
            "max_duration": cls.MAX_RECORDING_DURATION
        }