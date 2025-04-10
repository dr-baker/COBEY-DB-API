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
    "Session": "sessions",
    "Algo": "algos",
    "EventLog": "event_log"
}

# Define primary key field for each table
PK_FIELD_MAP = {
    "users": "user_id",
    "recordings": "recording_id",
    "sessions": "session_id",
    "algos": "algo_id",
    "event_log": "event_id"
}

# Define JSON fields for each table
JSON_FIELDS_MAP = {
    "users": ["firebase_data", "body_data"],
    "recordings": ["metadata"],
    "sessions": ["exercises_data"],
    "algos": ["parameters"],
    "event_log": ["event_data"]
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
            
        # Get primary key field for this table
        self.pk_field = PK_FIELD_MAP.get(self.table_name, "id")
        
        # Get JSON fields for this table
        self.json_fields = JSON_FIELDS_MAP.get(self.table_name, [])
            
        logger.debug(f"Using model {model_name} with table {self.table_name}")
    
    def _process_params(self, params: List[Any]) -> List[Any]:
        """Pre-process parameters for SQL query to handle JSON objects."""
        processed = []
        for param in params:
            if isinstance(param, (dict, list)):
                processed.append(json.dumps(param))
            else:
                processed.append(param)
        return processed
        
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
    
    def _process_row(self, row: asyncpg.Record) -> Dict[str, Any]:
        """Process a database row, converting JSON strings to dictionaries."""
        row_dict = dict(row)
        
        # Parse JSON fields
        for field in self.json_fields:
            if field in row_dict and isinstance(row_dict[field], str):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except json.JSONDecodeError:
                    # If it's not valid JSON, leave it as is
                    pass
                    
        return row_dict
        
    async def get_by_id(self, item_id: str) -> Optional[BaseModel]:
        """Get a single item by ID."""
        query = SQLBuilder.select(self.table_name)
        query.where(f"{self.pk_field} = $1")
        
        async with self.db.transaction() as conn:
            row = await conn.fetchrow(query.sql, item_id)
            if not row:
                return None
            return self.model(**self._process_row(row))
            
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        size: int = 10
    ) -> List[BaseModel]:
        """List items with optional filtering and pagination."""
        query = SQLBuilder.select(self.table_name)
        
        # Add filters
        param_index = 1
        if filters:
            filter_conditions = []
            params = []
            
            for field, value in filters.items():
                if value is not None:
                    filter_conditions.append(f"{field} = ${param_index}")
                    params.append(value)
                    param_index += 1
                    
            if filter_conditions:
                # Join conditions with AND
                query.where(" AND ".join(filter_conditions))
                query.params = params
        
        # Add pagination
        offset = (page - 1) * size
        query.limit(size)
        query.offset(offset)
        
        async with self.db.transaction() as conn:
            rows = await conn.fetch(query.sql, *query.params)
            return [self.model(**self._process_row(row)) for row in rows]
            
    async def create(self, data: Dict[str, Any]) -> BaseModel:
        """Create a new item."""
        # Pre-process data for JSON fields
        processed_data = {}
        for key, value in data.items():
            if key in self.json_fields and isinstance(value, (dict, list)):
                processed_data[key] = json.dumps(value)
            else:
                processed_data[key] = value
                
        query = SQLBuilder.insert(self.table_name, processed_data)
        
        async with self.db.transaction() as conn:
            row = await conn.fetchrow(query.sql, *query.params)
            return self.model(**self._process_row(row))
            
    async def update(
        self,
        item_id: str,
        data: Dict[str, Any],
        replace: bool = False
    ) -> Optional[BaseModel]:
        """Update an existing item."""
        if not data and not replace:
            return await self.get_by_id(item_id)
            
        # Pre-process data for JSON fields
        processed_data = {}
        for key, value in data.items():
            if key in self.json_fields and isinstance(value, (dict, list)):
                processed_data[key] = json.dumps(value)
            else:
                processed_data[key] = value
                
        query = SQLBuilder.update(self.table_name, processed_data)
        query.where(f"{self.pk_field} = ${len(query.params) + 1}")
        query.params.append(item_id)
        query.returning()
            
        async with self.db.transaction() as conn:
            row = await conn.fetchrow(query.sql, *query.params)
            if not row:
                return None
            return self.model(**self._process_row(row))
            
    async def delete(self, item_id: str) -> bool:
        """Delete an item."""
        query = SQLBuilder.delete(self.table_name)
        query.where(f"{self.pk_field} = $1")
        
        async with self.db.transaction() as conn:
            result = await conn.execute(query.sql, item_id)
            return result.endswith("1") 