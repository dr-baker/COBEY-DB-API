"""Configuration management for the application."""
from functools import lru_cache
from typing import Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "Backend API"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Database Settings
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_POOL_MIN_SIZE: int = 10
    DB_POOL_MAX_SIZE: int = 20
    
    # SSH Tunnel Settings
    SSH_HOST: str
    SSH_PORT: int = 22
    SSH_USER: str
    SSH_KEY_PATH: str
    
    # Security Settings
    API_RATE_LIMIT: int = 100  # requests per window
    API_RATE_WINDOW: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 