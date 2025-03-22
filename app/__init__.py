"""
Main application package.
"""
from fastapi import FastAPI
from .config import validate_config

# Validate configuration on app package import
validate_config() 