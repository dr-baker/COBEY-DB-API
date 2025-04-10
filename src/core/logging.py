"""Logging configuration for the application.

This module provides structured logging using structlog with JSON output.
"""
import sys
import logging
import structlog
import json
import codecs
from typing import Any
from datetime import datetime

def format_timestamp(_, __, event_dict):
    """Format timestamp as YYYY-MM-DD HH:MM:SS"""
    if "timestamp" in event_dict:
        # Parse the ISO timestamp and format it
        dt = datetime.fromisoformat(event_dict["timestamp"].replace("Z", "+00:00"))
        event_dict["timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
    return event_dict

def format_error_message(_, __, event_dict):
    """Format error messages, especially JSON responses."""
    if "error" in event_dict:
        error = event_dict["error"]
        # print(f"DEBUG: Raw error input to format_error_message: {repr(error)}") # Removed debug print
        if isinstance(error, str):
            parsed_error = None
            # Try parsing as JSON first
            if error.strip().startswith('{') and error.strip().endswith('}'):
                try:
                    parsed_error = json.loads(error)
                except json.JSONDecodeError:
                    pass # Will attempt unicode_escape below
            
            # If not parsed as JSON, try decoding escapes
            if parsed_error is None:
                try:
                    parsed_error = codecs.decode(error, 'unicode_escape')
                except Exception:
                    pass # Keep original error string if decoding fails
            
            # Update event_dict if parsing/decoding was successful
            if parsed_error is not None:
                event_dict["error"] = parsed_error
            # Otherwise, the original string remains
            
    return event_dict

class MultiLineConsoleRenderer(structlog.dev.ConsoleRenderer):
    """Renders logs with structured data indented with two tabs."""

    def __call__(self, logger, name, event_dict):
        # Let the base ConsoleRenderer format the log entry with colors
        rendered_line = super().__call__(logger, name, event_dict.copy())

        # If the line contains structured data (key=value pairs), format it
        if '=' in rendered_line:
            try:
                # Find the first key=value pair
                first_kv_idx = rendered_line.find('=')
                
                # Find the start of the key
                key_start = first_kv_idx
                while key_start > 0 and rendered_line[key_start-1] != ' ':
                    key_start -= 1
                
                # Split into message and structured data
                message_part = rendered_line[:key_start].rstrip()
                kv_part = rendered_line[key_start:]
                
                # Combine message and formatted structured data with two tabs
                return f"{message_part}\t{kv_part}"
                
            except Exception:
                # If formatting fails, return the original line
                return rendered_line
        
        return rendered_line

def setup_logging() -> None:
    """Configure structured logging.
    
    This function sets up the global logging configuration using structlog.
    It should be called once at application startup.
    """
    try:
        from .config import get_settings
        settings = get_settings()
        # Map string log level to logging module level
        log_level = getattr(logging, settings.LOG_LEVEL.upper())
        print(f"Setting log level to: {settings.LOG_LEVEL} ({log_level})")  # Debug print
    except (ImportError, AttributeError) as e:
        print(f"Error getting settings: {e}")  # Debug print
        # Default to DEBUG if settings aren't available yet
        log_level = logging.DEBUG
    
    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout
    )
    
    # Filter out verbose logging from specific libraries
    logging.getLogger('paramiko').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Configure structlog with our settings
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        format_timestamp,  # Custom processor to format timestamp
        format_error_message,  # Custom processor to format error messages
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.dict_tracebacks,
    ]
    
    # Always use the MultiLineConsoleRenderer
    processors.append(MultiLineConsoleRenderer(
        colors=True,
        exception_formatter=structlog.dev.plain_traceback,
        force_colors=True
    ))
    
    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        cache_logger_on_first_use=True
    )
    
    # Test debug logging
    test_logger = get_logger("test")
    test_logger.debug("Debug logging is enabled")
    test_logger.info("Info logging is enabled")

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: The name of the logger, typically __name__ from the calling module
        
    Returns:
        A configured structlog logger instance
    """
    # Get a logger with the module name
    logger = structlog.get_logger(name)
    
    # Bind common fields
    return logger.bind(
        module=name,
        service="mycloud_backend"
    )

# Create a default logger for the root module
logger = get_logger(__name__) 