"""Logging configuration for the application."""
import logging
import sys
from typing import Any
import structlog
from .config import get_settings

def setup_logging() -> None:
    """Configure structured logging."""
    settings = get_settings()
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if settings.DEBUG:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name) 