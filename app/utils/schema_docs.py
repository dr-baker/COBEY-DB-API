"""
Schema documentation generator.

Utilities to automatically generate documentation from SQLModel models.
This helps maintain up-to-date documentation as the schema evolves.
"""
import inspect
import json
from typing import Dict, List, Any, Optional, Type, get_origin, get_args
from enum import Enum
from datetime import datetime, timedelta
from sqlmodel import SQLModel
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import inspect as sa_inspect
import markdown
import os

def get_type_name(type_hint: Any) -> str:
    """Convert a type hint to a readable string."""
    if type_hint is None:
        return "None"
    
    if isinstance(type_hint, type):
        if issubclass(type_hint, str):
            return "string"
        elif issubclass(type_hint, int):
            return "integer"
        elif issubclass(type_hint, float):
            return "float"
        elif issubclass(type_hint, bool):
            return "boolean"
        elif issubclass(type_hint, datetime):
            return "timestamp"
        elif issubclass(type_hint, timedelta):
            return "interval"
        elif issubclass(type_hint, dict):
            return "object"
        elif issubclass(type_hint, list):
            return "array"
        elif issubclass(type_hint, Enum):
            return f"enum: {[e.value for e in type_hint]}"
        else:
            return type_hint.__name__
    
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    
    if origin is None:
        return str(type_hint)
    
    if origin is list or origin is List:
        if args:
            return f"array[{get_type_name(args[0])}]"
        return "array"
    
    if origin is dict or origin is Dict:
        if len(args) >= 2:
            return f"object[{get_type_name(args[0])}, {get_type_name(args[1])}]"
        return "object"
    
    if origin is Optional or origin is Union:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return f"{get_type_name(non_none_args[0])} (optional)"
        return f"Union[{', '.join(get_type_name(arg) for arg in non_none_args)}] (optional)"
    
    return str(type_hint)

def generate_model_schema(model_class: Type[SQLModel]) -> Dict[str, Any]:
    """Generate schema documentation for a SQLModel class."""
    schema = {
        "name": model_class.__name__,
        "table_name": getattr(model_class, "__tablename__", model_class.__name__.lower()),
        "description": inspect.getdoc(model_class) or "",
        "fields": [],
        "relationships": [],
    }
    
    # Process model fields
    for name, field in model_class.__fields__.items():
        if name.startswith("_"):
            continue
            
        field_info = field.field_info
        field_type = field.outer_type_
        
        # Skip relationship fields
        if name in getattr(model_class, "__sqlmodel_relationships__", {}):
            relationship = getattr(model_class, "__sqlmodel_relationships__", {})[name]
            schema["relationships"].append({
                "name": name,
                "target": relationship.argument.__name__ if hasattr(relationship.argument, "__name__") else str(relationship.argument),
                "back_populates": relationship.back_populates,
                "type": "one-to-many" if get_origin(field_type) is list else "many-to-one"
            })
            continue
            
        field_schema = {
            "name": name,
            "type": get_type_name(field_type),
            "description": field_info.description or "",
            "required": field.required,
            "nullable": not field.required or field_info.allow_none,
            "default": str(field_info.default) if field_info.default is not ... else None,
            "primary_key": field_info.primary_key,
            "foreign_key": getattr(field_info, "foreign_key", None),
        }
        
        schema["fields"].append(field_schema)
    
    return schema

def generate_markdown_doc(schema: Dict[str, Any]) -> str:
    """Generate Markdown documentation from a schema dictionary."""
    md = f"# {schema['name']}\n\n"
    
    if schema['description']:
        md += f"{schema['description']}\n\n"
    
    md += f"**Table name:** `{schema['table_name']}`\n\n"
    
    # Fields
    md += "## Fields\n\n"
    md += "| Name | Type | Required | Nullable | Default | Description |\n"
    md += "|------|------|----------|----------|---------|-------------|\n"
    
    for field in schema['fields']:
        primary_key = "🔑 " if field['primary_key'] else ""
        foreign_key = f"↗️ " if field['foreign_key'] else ""
        
        md += f"| {primary_key}{foreign_key}{field['name']} | {field['type']} | "
        md += f"{'Yes' if field['required'] else 'No'} | "
        md += f"{'Yes' if field['nullable'] else 'No'} | "
        md += f"{field['default'] or '-'} | {field['description']} |\n"
    
    # Relationships
    if schema['relationships']:
        md += "\n## Relationships\n\n"
        md += "| Name | Target | Type | Back Reference |\n"
        md += "|------|--------|------|---------------|\n"
        
        for rel in schema['relationships']:
            md += f"| {rel['name']} | {rel['target']} | {rel['type']} | {rel['back_populates'] or '-'} |\n"
    
    return md

def generate_schema_docs(models: List[Type[SQLModel]], output_dir: str) -> None:
    """Generate documentation for a list of SQLModel classes."""
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create an index file
    index_md = "# Database Schema Documentation\n\n"
    index_md += "## Tables\n\n"
    
    for model in models:
        schema = generate_model_schema(model)
        md = generate_markdown_doc(schema)
        
        # Write markdown file
        filename = f"{schema['name'].lower()}.md"
        with open(os.path.join(output_dir, filename), "w") as f:
            f.write(md)
            
        # Add to index
        index_md += f"- [{schema['name']}]({filename}) - {schema['description'].split('.')[0]}.\n"
    
    # Write index file
    with open(os.path.join(output_dir, "index.md"), "w") as f:
        f.write(index_md)
        
    # Also generate a JSON schema
    full_schema = {
        "models": [generate_model_schema(model) for model in models]
    }
    
    with open(os.path.join(output_dir, "schema.json"), "w") as f:
        json.dump(full_schema, f, indent=2) 