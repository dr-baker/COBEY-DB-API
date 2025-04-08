"""Dynamic Pydantic model generation from database schema.

This module provides a manager class for handling dynamically generated Pydantic models.
It serves as the main interface for the dynamic model generation system, managing
database connections and providing access to generated models.

The DynamicModels class:
- Manages database connection pool
- Handles model generation and caching
- Provides methods to access models by table name
- Ensures proper resource cleanup

Usage in FastAPI:
    from fastapi import FastAPI
    from .models.dynamic import dynamic_models

    app = FastAPI()

    @app.on_event("startup")
    async def startup_event():
        await dynamic_models.load_models()

    @app.get("/items/{item_id}")
    async def get_item(item_id: int):
        ItemModel = dynamic_models.get_model("items")
        if not ItemModel:
            raise HTTPException(status_code=404, detail="Table not found")
        return ItemModel(...)

    @app.on_event("shutdown")
    async def shutdown_event():
        await dynamic_models.close()
"""
from typing import Dict, Type, Any, Optional
from datetime import datetime
import asyncpg
from pydantic import BaseModel
from ..db.introspection import generate_models
from ..core.config import get_settings
from ..db.connection import db
from ..core.logging import get_logger

logger = get_logger(__name__)

class DynamicModels:
    """Manager for dynamically generated Pydantic models."""
    
    def __init__(self):
        self._models: Dict[str, Type[BaseModel]] = {}
        self._initialized = False
    
    async def load_models(self) -> None:
        """
        Load dynamic models from the database schema.
        Uses the global db connection pool from src.db.connection.
        """
        if self._initialized:
            logger.info("Models already loaded, skipping")
            return
            
        try:
            logger.info("Generating dynamic models from database schema")
            self._models = await generate_models(db)
            self._initialized = True
            logger.info(f"Successfully loaded {len(self._models)} models: {', '.join(self._models.keys())}")
        except Exception as e:
            logger.error(f"Failed to load dynamic models: {str(e)}")
            raise
    
    async def initialize(self, pool: Optional[asyncpg.Pool] = None) -> None:
        """
        Initialize the dynamic models manager.
        
        Args:
            pool: Optional database connection pool. If not provided, will use the global one.
            
        Deprecated: Use load_models() instead which uses the global db connection pool.
        """
        logger.warning("initialize() is deprecated, use load_models() instead")
        if pool is None:
            await self.load_models()
        else:
            self._models = await generate_models(pool)
            self._initialized = True
    
    async def close(self) -> None:
        """Close resources if needed."""
        # No need to close the db connection, it's handled by the global db object
        self._initialized = False
    
    def get_model(self, table_name: str) -> Optional[Type[BaseModel]]:
        """
        Get a Pydantic model for a specific table.
        
        Args:
            table_name: Name of the database table
            
        Returns:
            Pydantic model class if found, None otherwise
        """
        return self._models.get(table_name)
    
    def get_all_models(self) -> Dict[str, Type[BaseModel]]:
        """
        Get all generated Pydantic models.
        
        Returns:
            Dictionary mapping table names to Pydantic model classes
        """
        return self._models.copy()

# Global instance
dynamic_models = DynamicModels() 