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
    """Renders logs with structured data indented on a new line."""

    def __call__(self, logger, name, event_dict):
        # Let the base ConsoleRenderer format the log entry with colors
        rendered_line = super().__call__(logger, name, event_dict.copy())

        # Find the end of the level marker (e.g., '] ' after '[info ]')
        level = event_dict.get('level', '')
        level_marker_end = f"[{level}"
        try:
            idx1 = rendered_line.index(level_marker_end)
            idx2 = rendered_line.find(']', idx1) + 1
            # Look for the space immediately after the bracket
            if idx2 > 0 and idx2 < len(rendered_line) and rendered_line[idx2] == ' ':
                start_of_event_idx = idx2 + 1
            else:
                 # If no space, the event starts right after ']' (less common)
                 start_of_event_idx = idx2 

            # Heuristic: Find the start of the key=value pairs.
            # Assume they start after the event message + padding.
            # Find the first '=' significantly after the start of the event.
            # This relies on the event message not containing '= ' unlikely sequence.
            first_kv_idx = -1
            search_start = start_of_event_idx + self._pad_event # Start search after padding
            if search_start < len(rendered_line):
                 # Search for pattern ' key=' to be more specific
                 first_kv_idx = rendered_line.find(' =', search_start)
                 if first_kv_idx != -1: 
                     # Go back to find the start of the key
                     while first_kv_idx > 0 and rendered_line[first_kv_idx-1] != ' ':
                        first_kv_idx -= 1
                 else: 
                    # Fallback: Find first '=' after padding
                    first_kv_idx = rendered_line.find('=', search_start)
            
            # If we found a likely start for key-value pairs
            if first_kv_idx != -1 and first_kv_idx > start_of_event_idx:
                main_part = rendered_line[:first_kv_idx].rstrip()
                kv_part = rendered_line[first_kv_idx:]
                
                # Check if the value part contains newlines
                if '\n' in kv_part:
                    # Split by newlines and indent each line
                    lines = kv_part.split('\n')
                    indented_lines = [lines[0]]  # First line (with the key=)
                    for line in lines[1:]:
                        if line.strip():  # Only add non-empty lines
                            indented_lines.append(f"    {line}")
                    
                    # Join the lines back together
                    kv_part = '\n'.join(indented_lines)
                
                indent = "    "  # 4 spaces
                return f"{main_part}\n{indent}{kv_part}"

        except ValueError:
            # If parsing fails (e.g., level marker not found), return original
            pass

        # Default return if splitting logic fails
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
    
    # Filter out verbose SSH tunnel logging
    logging.getLogger('paramiko').setLevel(logging.WARNING)
    
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
        # Removed format_json_on_new_line
    ]
    
    # Use pretty printing in development mode
    if settings.DEBUG:
        # Use the new MultiLineConsoleRenderer
        processors.append(MultiLineConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
            pad_event=20, # Ensure this matches the renderer's logic
            force_colors=True
        ))
    else:
        processors.append(structlog.processors.JSONRenderer(
            serializer=lambda obj, **kwargs: json.dumps(
                obj,
                indent=2,
                default=str,
                ensure_ascii=False
            )
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