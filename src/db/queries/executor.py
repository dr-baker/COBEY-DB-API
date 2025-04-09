"""SQL query execution with dynamic model support.

This module provides a QueryExecutor class that bridges the SQLBuilder with the database
connection and dynamic models. It handles:
- Executing queries safely
- Converting database rows to Pydantic models
- Managing transactions
- Error handling and logging
"""
from typing import Any, Dict, List, Optional, Type, Union
import asyncpg
from pydantic import BaseModel
from ..connection import db
from ...core.logging import get_logger
from .builder import SQLBuilder
import json
from datetime import datetime

logger = get_logger(__name__)

class QueryExecutor:
    """Executes SQL queries and converts results to Pydantic models."""
    
    def __init__(self, db_connection, model_class: Type[BaseModel]):
        """
        Initialize the query executor.
        
        Args:
            db_connection: Database connection pool
            model_class: Pydantic model class for data mapping
        """
        self.db = db_connection
        self.model = model_class
        
        # Get the table name from the model class name
        self.table_name = model_class.__name__.lower()
        
        # Map model names to actual table names
        table_name_mapping = {
            "user": "users",
            "recording": "recordings",
            "session": "sessions",
            "algo": "algos",
            "eventlog": "event_log"  # Map 'eventlog' model to 'event_log' table
        }
        
        # Use the mapped table name if available
        self.table_name = table_name_mapping.get(self.table_name, self.table_name)
        
        if self.table_name.endswith("model"):
            self.table_name = self.table_name[:-5]  # Remove "model" suffix
    
    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for database insertion/update."""
        prepared = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Try to parse as JSON first
                if value.strip().startswith('{') and value.strip().endswith('}'):
                    try:
                        # Parse JSON string back into dict for Pydantic validation
                        prepared[key] = json.loads(value)
                        logger.debug(f"Successfully converted {key} from JSON string to dict")
                        continue
                    except json.JSONDecodeError:
                        pass
                
                # Try to parse as datetime
                try:
                    prepared[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    logger.debug(f"Successfully converted {key} from string to datetime")
                    continue
                except ValueError:
                    prepared[key] = value
            elif isinstance(value, dict):
                prepared[key] = value  # Keep dicts as is for Pydantic validation
                logger.debug(f"Using dict value for {key} as is")
            elif isinstance(value, datetime):
                prepared[key] = value
                logger.debug(f"Using datetime value for {key} as is")
            else:
                prepared[key] = value
                logger.debug(f"Using raw value for {key}: {type(value)}")
        return prepared

    async def get_by_id(self, record_id: Union[str, int]) -> Optional[BaseModel]:
        """
        Get a record by its ID.
        
        Args:
            record_id: Primary key value of the record
            
        Returns:
            Pydantic model instance if found, None otherwise
        """
        primary_key_column = self.model.get_primary_key_name()
        
        builder = SQLBuilder()
        builder.SELECT().FROM(self.table_name)
        builder.WHERE(f"{primary_key_column} = {builder._add_param(record_id)}")
        builder.LIMIT(1)
        
        query, params = builder.build()
        
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            if row:
                # Convert row to dict and parse JSON fields if needed
                row_dict = dict(row)
                for field in row_dict:
                    try:
                        row_dict[field] = json.loads(row_dict[field])
                    except json.JSONDecodeError:
                        # If it's not valid JSON, keep the string (might be an issue)
                        logger.warning(f"Field {field} for {self.table_name} id {record_id} is not valid JSON: {row_dict[field]}")
                        pass 
                return self.model(**row_dict)
            return None
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        size: int = 10
    ) -> List[Any]:
        """
        List records with pagination and filtering.
        
        Args:
            filters: Optional dictionary of field names and values for filtering
            page: Page number (1-based)
            size: Page size
            
        Returns:
            List of Pydantic model instances
        """
        builder = SQLBuilder()
        builder.SELECT().FROM(self.table_name)
        
        # Add filters if provided
        if filters:
            for field, value in filters.items():
                if value is not None:  # Only add filter if value is not None
                    if isinstance(value, (list, tuple)):
                        builder.WHERE(f"{field} = ANY({builder._add_param(value)})")
                    else:
                        builder.WHERE(f"{field} = {builder._add_param(value)}")
        
        # Add pagination
        offset = (page - 1) * size
        builder.LIMIT(size).OFFSET(offset)
        
        query, params = builder.build()
        
        async with self.db.transaction() as conn:
            rows = await conn.fetch(query, *params)
            return [self.model(**dict(row)) for row in rows]
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        builder = SQLBuilder()
        builder.SELECT("COUNT(*)").FROM(self.table_name)
        
        # Add filters if provided
        if filters:
            for field, value in filters.items():
                if value is not None:
                    # Use appropriate operator based on value type
                    if isinstance(value, (list, tuple)):
                        builder.WHERE(f"{field} = ANY({builder._add_param(value)})")
                    elif isinstance(value, datetime) and field == 'start_time':
                        builder.WHERE(f"ts >= {builder._add_param(value)}")
                    elif isinstance(value, datetime) and field == 'end_time':
                        builder.WHERE(f"ts <= {builder._add_param(value)}")
                    else:
                        builder.WHERE(f"{field} = {builder._add_param(value)}")
        
        query, params = builder.build()
        
        async with self.db.pool.acquire() as conn:
            count_result = await conn.fetchval(query, *params)
            return count_result if count_result is not None else 0
    
    async def create(self, data: Dict[str, Any]) -> Any:
        """Create a new record."""
        try:
            # Prepare data (handles type conversions like datetime)
            logger.debug(f"Preparing data for creation: {data}")
            prepared_data = self._prepare_data(data)
            logger.debug(f"Prepared data: {prepared_data}")

            # Validate data against the Pydantic model first
            validated_model = self.model(**prepared_data)
            insert_data = {}
            known_json_fields = {'firebase_data', 'body_data', 'exercises_data', 'event_data'}

            # Convert dict/list values for known JSON fields to JSON strings
            for field, value in validated_model.model_dump().items():
                if field in known_json_fields and isinstance(value, (dict, list)):
                    insert_data[field] = json.dumps(value)
                else:
                    insert_data[field] = value

            # Build the query using the processed data
            builder = SQLBuilder()
            builder.INSERT_INTO(self.table_name, **insert_data)  # Use insert_data
            builder.RETURNING()

            query, params = builder.build()

            async with self.db.transaction() as conn:
                row = await conn.fetchrow(query, *params)
                if row:
                    # Return the Pydantic model instance based on DB result
                    return self.model(**dict(row))
                raise ValueError("Failed to create record")
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}", error=str(e))
            raise
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Any:
        """Update a record."""
        try:
            # Prepare data (handles type conversions like datetime)
            prepared_data = self._prepare_data(data)
            
            # Pass prepared data directly (asyncpg handles dict -> JSONB)
            
            # Build the query
            builder = SQLBuilder()
            builder.UPDATE(self.table_name)
            builder.SET(**prepared_data)
            builder.WHERE(f"id = {builder._add_param(record_id)}")
            builder.RETURNING()
            
            query, params = builder.build()
            
            async with self.db.transaction() as conn:
                row = await conn.fetchrow(query, *params)
                if row:
                    return self.model(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error updating record in {self.table_name}", error=str(e))
            raise
    
    async def delete(
        self,
        record_id: str
    ) -> bool:
        """
        Delete a record by ID.
        
        Args:
            record_id: Primary key value of the record to delete
            
        Returns:
            True if the record was deleted, False if not found
        """
        builder = SQLBuilder()
        builder.query_parts.append(f"DELETE FROM {self.table_name}")
        builder.WHERE(f"id = {builder._add_param(record_id)}")
        
        query, params = builder.build()
        
        async with self.db.transaction() as conn:
            try:
                result = await conn.execute(query, *params)
                # Parse the DELETE result which contains count
                return "DELETE 1" in result
            except Exception as e:
                logger.error(f"Error deleting record from {self.table_name}", error=str(e))
                raise 