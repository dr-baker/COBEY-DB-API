#!/usr/bin/env python3
"""Generate explicit Pydantic models from database schema.

This script connects to the database, introspects its schema, and generates 
explicitly defined Pydantic model files in the src/models directory.

Usage:
    python -m scripts.generate_models
"""
import os
import asyncio
import logging
import inflect
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import the database and introspection modules
from src.db.connection import db
from src.db.introspection import get_table_info, map_postgres_type_to_python
from src.core.config import get_settings

# Define path constants
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "models")

# Inflect engine for singular/plural conversions
p = inflect.engine()

def generate_model_file_content(table_name: str, table_info: Any) -> str:
    """Generate the content for a model file."""
    # Try to get singular form of table name for the model class name
    singular = p.singular_noun(table_name)
    model_class_name = singular.title().replace('_', '') if singular else table_name.title().replace('_', '')
    
    # Import statements
    imports = [
        "from datetime import datetime",
        "from typing import Optional, Dict, Any, List",
        "from pydantic import BaseModel, Field",
        ""
    ]
    
    # Define the model class
    model_definition = [
        f"class {model_class_name}(BaseModel):",
        f'    """Pydantic model for {table_name} table."""',
        ""
    ]
    
    # Add field definitions
    for column in table_info.columns:
        # Map PostgreSQL type to Python type
        python_type, is_optional_based_on_type = map_postgres_type_to_python(column.data_type)
        python_type_name = python_type.__name__
        
        # Determine if field should be optional
        is_optional = column.is_nullable or is_optional_based_on_type
        
        # Special cases for created_at/updated_at
        if column.name in ["created_at", "updated_at"]:
            field_line = f"    {column.name}: Optional[datetime] = Field(default=None, description=\"{column.data_type}\")"
        # Make app_version optional specifically for event_log table
        elif table_name == "event_log" and column.name == "app_version":
            field_line = f"    {column.name}: Optional[str] = Field(default=None, description=\"{column.data_type}\")"
        # Original logic for other fields
        else:
            field_default = "= None" if is_optional else ""
            field_type = f"Optional[{python_type_name}]" if is_optional else python_type_name
            field_line = f"    {column.name}: {field_type} {field_default} = Field(description=\"{column.data_type}\"{', default=None' if is_optional else ''})"
        
        model_definition.append(field_line)
    
    # Add Base Create and Update model classes
    model_definition.extend(["", ""])
    model_definition.append(f"class {model_class_name}Create(BaseModel):")
    model_definition.append(f'    """Schema for creating a new {table_name} record."""')
    
    # Create model shouldn't require id, created_at, updated_at
    create_fields = []
    for column in table_info.columns:
        # Skip auto-generated fields
        if column.name in ["id", "created_at", "updated_at"]:
            continue
            
        # Map PostgreSQL type to Python type
        python_type, is_optional_based_on_type = map_postgres_type_to_python(column.data_type)
        python_type_name = python_type.__name__
        
        # Determine if field should be optional
        is_optional = column.is_nullable or is_optional_based_on_type
        
        # Special case for app_version
        if table_name == "event_log" and column.name == "app_version":
            field_line = f"    {column.name}: Optional[str] = Field(default=None, description=\"{column.data_type}\")"
        else:
            field_default = "= None" if is_optional else ""
            field_type = f"Optional[{python_type_name}]" if is_optional else python_type_name
            field_line = f"    {column.name}: {field_type} {field_default} = Field(description=\"{column.data_type}\"{', default=None' if is_optional else ''})"
        
        create_fields.append(field_line)
    
    if create_fields:
        model_definition.extend(create_fields)
    else:
        model_definition.append("    pass")
    
    # Update model
    model_definition.extend(["", ""])
    model_definition.append(f"class {model_class_name}Update(BaseModel):")
    model_definition.append(f'    """Schema for updating an existing {table_name} record."""')
    
    # All fields should be optional in update
    update_fields = []
    for column in table_info.columns:
        # Skip auto-generated fields (except potentially id for updates)
        if column.name in ["created_at", "updated_at"]:
            continue
            
        # Map PostgreSQL type to Python type
        python_type, _ = map_postgres_type_to_python(column.data_type)
        python_type_name = python_type.__name__
        
        # All fields are optional in update
        field_line = f"    {column.name}: Optional[{python_type_name}] = Field(default=None, description=\"{column.data_type}\")"
        update_fields.append(field_line)
    
    if update_fields:
        model_definition.extend(update_fields)
    else:
        model_definition.append("    pass")
    
    # Combine all parts
    return "\n".join(imports + model_definition)

async def generate_models() -> None:
    """Main function to generate models."""
    logger.info("Connecting to database...")
    await db.connect()
    
    try:
        # Make sure the models directory exists
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        # Get the table info from the database
        logger.info("Introspecting database schema...")
        tables = await get_table_info(db.pool)
        
        # Ensure __init__.py exists in models directory
        init_path = os.path.join(MODELS_DIR, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write('"""Model definitions package."""\n')
        
        generated_models = []
        
        # Generate model files
        for table in tables:
            table_name = table.name
            
            # Skip internal tables like migrations
            if table_name.startswith("_") or table_name == "migrations":
                continue
            
            # Generate the file content
            file_content = generate_model_file_content(table_name, table)
            
            # Write to file
            model_file_path = os.path.join(MODELS_DIR, f"{table_name}.py")
            with open(model_file_path, "w") as f:
                f.write(file_content)
            
            logger.info(f"Generated model file: {model_file_path}")
            generated_models.append(table_name)
        
        # Update the __init__.py to import all models
        with open(init_path, "w") as f:
            f.write('"""Model definitions package."""\n\n')
            for table_name in generated_models:
                singular = p.singular_noun(table_name)
                model_name = singular.title().replace('_', '') if singular else table_name.title().replace('_', '')
                f.write(f"from .{table_name} import {model_name}, {model_name}Create, {model_name}Update\n")
            
            # Export all models
            f.write("\n__all__ = [\n")
            for table_name in generated_models:
                singular = p.singular_noun(table_name)
                model_name = singular.title().replace('_', '') if singular else table_name.title().replace('_', '')
                f.write(f"    '{model_name}',\n")
                f.write(f"    '{model_name}Create',\n")
                f.write(f"    '{model_name}Update',\n")
            f.write("]\n")
        
        logger.info(f"Updated __init__.py with {len(generated_models)} models")
        logger.info(f"Successfully generated models for tables: {', '.join(generated_models)}")
        
    finally:
        logger.info("Disconnecting from database...")
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_models()) 