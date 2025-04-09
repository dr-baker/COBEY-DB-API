"""Model and table name mappings.

This module provides centralized mappings between database tables and their corresponding
model classes. It ensures consistency across the application and makes it easy to
maintain and update these relationships.
"""
from typing import Dict, Type
from pydantic import BaseModel
import importlib

# Map table names to their model names
TABLE_TO_MODEL_NAME: Dict[str, str] = {
    "users": "User",
    "recordings": "Recording",
    "sessions": "Session",
    "algos": "Algo",
    "event_log": "EventLog",
}

def get_model_class(table_name: str) -> Type[BaseModel]:
    """Get the model class for a given table name.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        The corresponding Pydantic model class
        
    Raises:
        ValueError: If no model is found for the table name
    """
    model_name = get_model_name(table_name)
    module_name = table_name.replace("_", "")  # Convert event_log to eventlog
    try:
        module = importlib.import_module(f"src.models.{module_name}")
        return getattr(module, model_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Failed to import model {model_name} from {module_name}: {str(e)}")

def get_model_name(table_name: str) -> str:
    """Get the model name for a given table name.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        The corresponding model name
        
    Raises:
        ValueError: If no model name is found for the table name
    """
    model_name = TABLE_TO_MODEL_NAME.get(table_name)
    if not model_name:
        raise ValueError(f"No model name found for table: {table_name}")
    return model_name 