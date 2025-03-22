"""
Migration utility functions.

Utilities to generate migration files when making schema changes.


Practical Usage
When you modify your database models in app/models.py, you would:
Run python -m app.cli.schema migrate -m "Add user email field" to create a migration file
Review the generated migration in app/migrations/versions/
Run python -m app.cli.schema apply to apply the changes to your database
"""
import os
import sys
import datetime
import importlib
import inspect
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.autogenerate import compare_metadata
from alembic.operations import Operations, MigrateOperation
from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import reflection
import uuid
import re

def get_models_module():
    """Import and return the models module."""
    return importlib.import_module("app.models")

def get_alembic_config(script_location="app/migrations"):
    """Get Alembic configuration."""
    config = Config()
    config.set_main_option("script_location", script_location)
    config.set_main_option("prepend_sys_path", ".")
    return config

def generate_migration(message=None, alembic_config=None):
    """
    Generate an Alembic migration based on changes to the models.
    
    Args:
        message (str): Migration message/description
        alembic_config (Config): Alembic configuration
    
    Returns:
        str: Path to the generated migration file
    """
    if message is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        message = f"auto_migration_{timestamp}"
        
    if alembic_config is None:
        alembic_config = get_alembic_config()
    
    command.revision(alembic_config, message=message, autogenerate=True)
    
    # Find the generated migration file
    script_dir = ScriptDirectory.from_config(alembic_config)
    revisions = list(script_dir.walk_revisions())
    if revisions:
        latest_revision = revisions[0]
        return os.path.join(script_dir.dir, f"{latest_revision.path}.py")
    
    return None

def init_migrations():
    """
    Initialize the Alembic migration environment.
    
    Returns:
        bool: Whether initialization was successful
    """
    try:
        config = get_alembic_config()
        
        # Create migrations directory if it doesn't exist
        migrations_dir = config.get_main_option("script_location")
        os.makedirs(migrations_dir, exist_ok=True)
        
        # Initialize Alembic
        command.init(config, migrations_dir)
        
        return True
    except Exception as e:
        print(f"Error initializing migrations: {e}")
        return False

def generate_column_metadata_comment(model, field_name):
    """Generate a comment for a column based on model metadata."""
    if not hasattr(model, "__fields__"):
        return None
        
    field = model.__fields__.get(field_name)
    if field and field.field_info.description:
        return field.field_info.description
    
    return None

def detect_schema_changes():
    """
    Detect schema changes without creating a migration.
    
    Returns:
        list: List of detected changes
    """
    from sqlalchemy import MetaData
    from sqlalchemy.engine import create_engine
    from sqlalchemy.ext.automap import automap_base
    from sqlalchemy.orm import Session
    from ..config import get_database_config
    
    # Get database config
    db_config = get_database_config()
    
    # Connect to database
    engine = create_engine(
        f"postgresql://{db_config['DB_USER']}:{db_config['DB_PW']}@{db_config['DB_HOST']}:{db_config['DB_PORT']}/{db_config['DB_NAME']}"
    )
    
    # Reflect existing database
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Get models
    models_module = get_models_module()
    
    # Get SQLModel metadata
    sqlmodel_metadata = getattr(models_module, "SQLModel").metadata
    
    # Compare metadata
    from alembic.autogenerate import compare_metadata
    return compare_metadata(metadata, sqlmodel_metadata)

def apply_migrations():
    """
    Apply all pending migrations.
    
    Returns:
        bool: Whether migrations were applied successfully
    """
    try:
        config = get_alembic_config()
        command.upgrade(config, "head")
        return True
    except Exception as e:
        print(f"Error applying migrations: {e}")
        return False 