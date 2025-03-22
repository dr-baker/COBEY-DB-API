"""
Configuration management for the application.
Loads and validates environment variables.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database_config() -> Dict[str, Any]:
    """Get database configuration from environment variables."""
    return {
        "SSH_HOST": os.getenv("SSH_HOST", "your_ssh_host_here"),
        "SSH_PORT": int(os.getenv("SSH_PORT", "22")),
        "SSH_USER": os.getenv("SSH_USER", "your_ssh_user_here"),
        "SSH_KEY_PATH": os.getenv("SSH_KEY_PATH", "your_ssh_key_path_here"),
        "DB_HOST": os.getenv("DB_HOST", "your_db_host_here"),
        "DB_PORT": int(os.getenv("DB_PORT", "5432")),
        "DB_USER": os.getenv("DB_USER", "your_db_user_here"),
        "DB_PW": os.getenv("DB_PW", "your_db_password_here"),
        "DB_NAME": os.getenv("DB_NAME", "your_db_name_here"),
    }

def validate_config() -> None:
    """
    Validate that all required configuration is present.
    Raises ValueError if any required config is missing.
    """
    required_configs = [
        "SSH_HOST", "SSH_USER", "SSH_KEY_PATH",
        "DB_HOST", "DB_USER", "DB_PW", "DB_NAME"
    ]
    
    for config in required_configs:
        if not os.getenv(config):
            raise ValueError(f"Missing required configuration: {config}")

# Validate configuration on module import
validate_config() 