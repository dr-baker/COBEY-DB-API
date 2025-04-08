"""FastAPI dependencies for dependency injection.

This module provides dependencies that can be used in FastAPI routes to access
database connections and query executors. It ensures proper resource management
and type safety throughout the API layer.
"""
from typing import AsyncGenerator, Dict, Any, Callable
from fastapi import Depends
from ..db.connection import db
from ..db.queries.executor import QueryExecutor
from ..core.logging import get_logger
from ..models.dynamic import dynamic_models

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
            # Get the dynamic model for the table
            model = dynamic_models.get_model(table_name)
            if not model:
                raise ValueError(f"No model found for table: {table_name}")
                
            # Create and return the executor
            executor = QueryExecutor(db, model)
            return executor
        except Exception as e:
            logger.error(f"Failed to create query executor for table {table_name}", error=str(e))
            raise
            
    return _get_executor  # Return the function, not Depends(_get_executor)

async def get_query_executor_async(table_name: str) -> AsyncGenerator[QueryExecutor, None]:
    """
    Get a QueryExecutor instance for the specified table.
    
    Args:
        table_name: Name of the table to create queries for
        
    Yields:
        QueryExecutor instance configured for the specified table
    """
    try:
        # Get the dynamic model for the table
        model = dynamic_models.get_model(table_name)
        if not model:
            raise ValueError(f"No model found for table: {table_name}")
            
        # Create and yield the executor
        executor = QueryExecutor(db, model)
        yield executor
    except Exception as e:
        logger.error(f"Failed to create query executor for table {table_name}", error=str(e))
        raise
    finally:
        # Cleanup if needed
        pass 