"""SQL query execution with explicit model support.

This module provides a QueryExecutor class that bridges the SQLBuilder with the database
connection and explicit Pydantic models. It handles:
- Executing queries safely
- Converting database rows to Pydantic models
- Managing transactions
- Error handling and logging
"""
from typing import Any, Dict, List, Optional, Type
import json
from pydantic import BaseModel
from ..connection import db
from ...core.logging import get_logger
from .builder import SQLBuilder
import asyncpg

logger = get_logger(__name__)

# Define table name mapping for models to database tables
TABLE_NAME_MAP = {
    "User": "users",
    "Recording": "recordings",
    "EventLog": "event_log",
    "Algo": "algos"
}

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
        
        # Get table name from mapping
        model_name = model_class.__name__
        self.table_name = TABLE_NAME_MAP.get(model_name)
        if not self.table_name:
            raise ValueError(f"No table mapping found for model: {model_name}")
            
        logger.debug(f"Using model {model_name} with table {self.table_name}")
    
    def _process_data_for_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for DB insertion/update, serializing JSON fields."""
        processed_data = {}
        for key, value in data.items():
            # Serialize dicts and lists to JSON for database storage
            if isinstance(value, (dict, list)):
                processed_data[key] = json.dumps(value)
            else:
                processed_data[key] = value
        return processed_data

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            filters: Optional dictionary of field names and values for filtering
            
        Returns:
            Count of matching records
        """
        builder = SQLBuilder()
        builder.query_parts.append(f"SELECT COUNT(*) FROM {self.table_name}")
        
        if filters:
            where_parts = []
            for field, value in filters.items():
                if isinstance(value, dict) and "$gte" in value:
                    where_parts.append(f"{field} >= {builder._add_param(value['$gte'])}")
                elif isinstance(value, dict) and "$lte" in value:
                    where_parts.append(f"{field} <= {builder._add_param(value['$lte'])}")
                else:
                    where_parts.append(f"{field} = {builder._add_param(value)}")
            
            if where_parts:
                builder.query_parts.append("WHERE " + " AND ".join(where_parts))
        
        query, params = builder.build()
        
        async with self.db.transaction() as conn:
            result = await conn.fetchval(query, *params)
            return int(result)
    
    async def get_by_id(self, record_id: str) -> Optional[Any]:
        """
        Get a record by its ID.
        
        Args:
            record_id: Primary key value of the record
            
        Returns:
            Pydantic model instance if found, None otherwise
        """
        builder = SQLBuilder()
        builder.SELECT().FROM(self.table_name)
        # Get PK field name based on table name
        pk_field = f'{self.table_name[:-1]}_id' if self.table_name.endswith('s') else f'{self.table_name}_id'
        builder.WHERE(f"{pk_field} = {builder._add_param(record_id)}")
        builder.LIMIT(1)
        
        query, params = builder.build()
        
        async with self.db.transaction() as conn:
            row = await conn.fetchrow(query, *params)
            if row:
                # Convert row to dict and process JSON fields
                row_dict = dict(row)
                for key, value in row_dict.items():
                    # Parse any JSON strings into Python objects
                    if isinstance(value, str):
                        try:
                            json_value = json.loads(value)
                            if isinstance(json_value, (dict, list)):
                                row_dict[key] = json_value
                        except json.JSONDecodeError:
                            # Not a JSON string, keep original value
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
        try:
            builder = SQLBuilder()
            builder.SELECT().FROM(self.table_name)
            
            where_conditions = []
            if filters:
                logger.debug(f"Applying filters: {filters}")
                for field, value in filters.items():
                    if value is not None:
                        condition = f"{field} = {builder._add_param(value)}"
                        where_conditions.append(condition)
                        logger.debug(f"Added filter condition: {condition}")
            
            if where_conditions:
                where_clause = " AND ".join(where_conditions)
                builder.WHERE(where_clause)
                logger.debug(f"Built WHERE clause: {where_clause}")
            else:
                logger.debug("No filters applied.")

            offset = (page - 1) * size
            builder.LIMIT(size).OFFSET(offset)
            
            query, params = builder.build()
            logger.info(f"Executing final list query for {self.table_name}: {query}")
            logger.info(f"Final query parameters: {params}")
            
            async with self.db.transaction() as conn:
                rows = await conn.fetch(query, *params)
                logger.debug(f"Query returned {len(rows)} rows.")
                result = []
                for row in rows:
                    row_dict = dict(row)
                    # Parse JSON strings
                    for key, value in row_dict.items():
                        if isinstance(value, str):
                            try:
                                json_value = json.loads(value)
                                if isinstance(json_value, (dict, list)):
                                    row_dict[key] = json_value
                            except json.JSONDecodeError:
                                # Not JSON, keep original
                                pass
                    result.append(self.model(**row_dict))
                return result
        except Exception as e:
            logger.exception(f"Failed to list records from {self.table_name} with filters {filters}. Error type: {type(e).__name__}", exc_info=True)
            raise
    
    async def create(self, data: Dict[str, Any]) -> Any:
        """
        Create a new record.
        
        Args:
            data: Dictionary of field names and values
            
        Returns:
            Pydantic model instance of the created record
            
        Raises:
            ValueError: If record creation fails
            asyncpg.exceptions.UniqueViolationError: If record with same ID already exists
        """
        try:
            # Serialize JSON fields before creating the record
            data = self._process_data_for_db(data)
            
            builder = SQLBuilder()
            builder.INSERT_INTO(self.table_name, **data)
            builder.RETURNING()
            
            query, params = builder.build()
            
            async with self.db.transaction() as conn:
                try:
                    row = await conn.fetchrow(query, *params)
                    if row:
                        # Deserialize JSON fields before creating model
                        row_dict = dict(row)
                        for key, value in row_dict.items():
                            if isinstance(value, str):
                                try:
                                    json_value = json.loads(value)
                                    if isinstance(json_value, (dict, list)):
                                        row_dict[key] = json_value
                                except json.JSONDecodeError:
                                    # Not JSON, keep original
                                    pass
                        return self.model(**row_dict)
                    raise ValueError("Failed to create record")
                except asyncpg.exceptions.UniqueViolationError as e:
                    logger.warning(f"Record already exists in {self.table_name}", error=str(e))
                    # Re-raise the unique violation error to be handled by the API layer
                    raise
                except Exception as e:
                    logger.error(f"Error creating record in {self.table_name}", error=str(e))
                    raise
        except Exception as e:
            logger.error(f"Failed to create record in {self.table_name}", error=str(e))
            raise
    
    async def update(
        self,
        record_id: str,
        data: Dict[str, Any],
        replace: bool = False
    ) -> Optional[Any]:
        """
        Update a record by ID.
        
        Args:
            record_id: Primary key value of the record to update
            data: Dictionary of field names and values to update
            replace: If True, completely replace the record with the provided data
            
        Returns:
            Updated Pydantic model instance or None if not found
        """
        if not data and not replace:
             return await self.get_by_id(record_id)
            
        processed_data = self._process_data_for_db(data)
            
        builder = SQLBuilder()
        pk_field = f'{self.table_name[:-1]}_id' if self.table_name.endswith('s') else f'{self.table_name}_id'

        if replace:
            # For replace, we need to include all fields
            update_payload = processed_data
        else:
            # For update, filter out the PK and only include provided fields
            update_payload = {k: v for k, v in processed_data.items() if k != pk_field}

        if not update_payload and not replace:
             return await self.get_by_id(record_id) # Nothing to update except maybe PK?

        builder.UPDATE(self.table_name, **update_payload)
        builder.WHERE(f"{pk_field} = {builder._add_param(record_id)}")
        builder.RETURNING()
        
        query, params = builder.build()
        
        async with self.db.transaction() as conn:
            try:
                row = await conn.fetchrow(query, *params)
                if row:
                    row_dict = dict(row)
                    # Parse JSON strings
                    for key, value in row_dict.items():
                        if isinstance(value, str):
                            try:
                                json_value = json.loads(value)
                                if isinstance(json_value, (dict, list)):
                                    row_dict[key] = json_value
                            except json.JSONDecodeError:
                                # Not JSON, keep original
                                pass
                    return self.model(**row_dict)
                return None  # Record not found
            except Exception as e:
                logger.error(f"Error updating record in {self.table_name}", query=query, params=params, error=str(e))
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
        pk_field = f'{self.table_name[:-1]}_id' if self.table_name.endswith('s') else f'{self.table_name}_id'
        builder.WHERE(f"{pk_field} = {builder._add_param(record_id)}")
        
        query, params = builder.build()
        
        async with self.db.transaction() as conn:
            try:
                result = await conn.execute(query, *params)
                return result.startswith("DELETE") and not result.endswith(" 0")
            except Exception as e:
                logger.error(f"Error deleting record from {self.table_name}", query=query, params=params, error=str(e))
                raise 