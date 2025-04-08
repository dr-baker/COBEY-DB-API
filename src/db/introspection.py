"""Database schema introspection for dynamic model generation.

This module provides functionality to introspect PostgreSQL database schemas and generate
Pydantic models automatically. It's a key component of the dynamic model generation system
that allows the API to work with database tables without manually defining Pydantic models.

Key Features:
- Extracts table and column metadata from PostgreSQL information schema
- Maps PostgreSQL data types to Python types
- Handles nullable fields and primary keys
- Generates Pydantic models with proper type hints and field descriptions

Usage:
    # Example of using the introspection system
    pool = await asyncpg.create_pool(...)
    models = await generate_models(pool)
    
    # The models dictionary will contain Pydantic model classes
    # mapped to their table names
    UserModel = models['users']
    
    # Use the model for validation and serialization
    user = UserModel(id=1, name="John Doe")
"""
from typing import Any, Dict, List, Optional, Tuple, Type
import asyncpg
from datetime import datetime
import inflect
from ..core.config import get_settings

class ColumnInfo:
    """Information about a database column."""
    def __init__(
        self,
        name: str,
        data_type: str,
        is_nullable: bool,
        default: Optional[str],
        is_primary_key: bool = False
    ):
        self.name = name
        self.data_type = data_type
        self.is_nullable = is_nullable
        self.default = default
        self.is_primary_key = is_primary_key

class TableInfo:
    """Information about a database table."""
    def __init__(
        self,
        name: str,
        schema: str,
        columns: List[ColumnInfo],
        primary_keys: List[str]
    ):
        self.name = name
        self.schema = schema
        self.columns = columns
        self.primary_keys = primary_keys

async def get_table_info(pool: asyncpg.Pool, schema: str = "public") -> List[TableInfo]:
    """
    Get information about all tables in the specified schema.
    
    Args:
        pool: Database connection pool
        schema: Database schema name (default: "public")
        
    Returns:
        List of TableInfo objects containing table metadata
    """
    # Query to get table information
    table_query = """
    SELECT 
        t.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        tc.constraint_type
    FROM information_schema.tables t
    JOIN information_schema.columns c 
        ON t.table_name = c.table_name 
        AND t.table_schema = c.table_schema
    LEFT JOIN information_schema.key_column_usage kcu 
        ON c.table_name = kcu.table_name 
        AND c.column_name = kcu.column_name
    LEFT JOIN information_schema.table_constraints tc 
        ON kcu.constraint_name = tc.constraint_name
    WHERE t.table_schema = $1
    AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.ordinal_position;
    """
    
    # Query to get primary key information
    pk_query = """
    SELECT
        tc.table_name,
        kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = $1;
    """
    
    async with pool.acquire() as conn:
        # Get all table and column information
        table_rows = await conn.fetch(table_query, schema)
        
        # Get primary key information
        pk_rows = await conn.fetch(pk_query, schema)
        
        # Create a dictionary of primary keys by table
        pk_dict: Dict[str, List[str]] = {}
        for row in pk_rows:
            table_name = row['table_name']
            if table_name not in pk_dict:
                pk_dict[table_name] = []
            pk_dict[table_name].append(row['column_name'])
        
        # Organize table information
        tables: Dict[str, TableInfo] = {}
        for row in table_rows:
            table_name = row['table_name']
            if table_name not in tables:
                tables[table_name] = TableInfo(
                    name=table_name,
                    schema=schema,
                    columns=[],
                    primary_keys=pk_dict.get(table_name, [])
                )
            
            # Create ColumnInfo
            column = ColumnInfo(
                name=row['column_name'],
                data_type=row['data_type'],
                is_nullable=row['is_nullable'] == 'YES',
                default=row['column_default'],
                is_primary_key=row['column_name'] in pk_dict.get(table_name, [])
            )
            tables[table_name].columns.append(column)
        
        return list(tables.values())

def map_postgres_type_to_python(type_name: str) -> Tuple[Type, bool]:
    """
    Map PostgreSQL data type to Python type and whether it's optional.
    
    Args:
        type_name: PostgreSQL data type name
        
    Returns:
        Tuple of (Python type, is_optional)
    """
    type_mapping = {
        'integer': (int, False),
        'bigint': (int, False),
        'smallint': (int, False),
        'numeric': (float, False),
        'real': (float, False),
        'double precision': (float, False),
        'character varying': (str, False),
        'varchar': (str, False),
        'text': (str, False),
        'boolean': (bool, False),
        'timestamp': (datetime, False),
        'timestamp with time zone': (datetime, False),
        'date': (datetime, False),
        'json': (dict, False),
        'jsonb': (dict, False),
        'uuid': (str, False),
    }
    
    return type_mapping.get(type_name.lower(), (Any, True))

async def generate_models(pool: asyncpg.Pool, schema: str = "public") -> Dict[str, Any]:
    """
    Generate Pydantic model classes from database schema.
    
    Args:
        pool: Database connection pool
        schema: Database schema name (default: "public")
        
    Returns:
        Dictionary mapping table names to Pydantic model classes
    """
    from pydantic import BaseModel, Field
    from typing import Optional, List, Dict, Any
    
    tables = await get_table_info(pool, schema)
    models: Dict[str, Any] = {}
    
    for table in tables:
        # Create fields dictionary for the model
        fields: Dict[str, Any] = {}
        
        for column in table.columns:
            # Map PostgreSQL type to Python type
            python_type, is_optional = map_postgres_type_to_python(column.data_type)
            
            # Create field with appropriate type and constraints
            field_type = Optional[python_type] if is_optional else python_type
            field = Field(
                default=None if is_optional else ...,
                description=f"Column: {column.name}, Type: {column.data_type}"
            )
            
            fields[column.name] = (field_type, field)
        
        # Create the model class
        model_name = inflect.engine().singular_noun(table.name) or table.name
        model_name = model_name.title().replace('_', '')
        
        model = type(
            model_name,
            (BaseModel,),
            {
                '__module__': 'models.dynamic',
                '__doc__': f"Dynamic model for table {table.name}",
                '__annotations__': {k: v[0] for k, v in fields.items()},
                **{k: v[1] for k, v in fields.items()}
            }
        )
        
        models[table.name] = model
    
    return models 