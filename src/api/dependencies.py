"""FastAPI dependencies for dependency injection.

This module provides dependencies that can be used in FastAPI routes to access
database connections and query executors. It ensures proper resource management
and type safety throughout the API layer.
"""
from typing import Callable
from fastapi import Depends

from ..db.connection import db
from ..db.queries.executor import QueryExecutor
from ..core.logging import get_logger
from ..models.mapping import get_model_class

logger = get_logger(__name__)

def get_query_executor(table_name: str) -> Callable:
    """
    Dependency factory that provides a QueryExecutor for a specific table.
    
    Args:
        table_name: Name of the database table to work with
        
    Returns:
        A dependency function that provides a QueryExecutor
    """
    async def _get_executor() -> QueryExecutor:
        try:
            # Get the model class for the table
            model_class = get_model_class(table_name)
                
            # Create and return the executor
            executor = QueryExecutor(db, model_class)
            return executor
        except Exception as e:
            logger.error(f"Failed to create query executor for table {table_name}", error=str(e))
            raise
            
    return _get_executor 