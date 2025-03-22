"""
CLI commands for schema management.
"""
import argparse
import os
import sys
import importlib
from datetime import datetime

# Add parent directory to path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.utils.migration import init_migrations, generate_migration, apply_migrations, detect_schema_changes
from app.utils.schema_docs import generate_schema_docs

def get_all_models():
    """Import and return all SQLModel models from app.models."""
    models_module = importlib.import_module("app.models")
    
    # Get all SQLModel classes
    from sqlmodel import SQLModel
    models = []
    
    for name in dir(models_module):
        obj = getattr(models_module, name)
        if (isinstance(obj, type) and 
            issubclass(obj, SQLModel) and 
            obj != SQLModel and
            hasattr(obj, "__tablename__")):
            models.append(obj)
    
    return models

def init_command(args):
    """Initialize migrations."""
    print("Initializing migrations...")
    success = init_migrations()
    if success:
        print("Migrations initialized successfully.")
    else:
        print("Failed to initialize migrations.")
        sys.exit(1)

def migrate_command(args):
    """Generate a new migration."""
    print("Generating migration...")
    migration_file = generate_migration(args.message)
    if migration_file:
        print(f"Migration generated: {migration_file}")
    else:
        print("Failed to generate migration.")
        sys.exit(1)

def apply_command(args):
    """Apply migrations."""
    print("Applying migrations...")
    success = apply_migrations()
    if success:
        print("Migrations applied successfully.")
    else:
        print("Failed to apply migrations.")
        sys.exit(1)

def detect_command(args):
    """Detect schema changes."""
    print("Detecting schema changes...")
    changes = detect_schema_changes()
    if not changes:
        print("No schema changes detected.")
    else:
        print(f"Detected {len(changes)} changes:")
        for change in changes:
            print(f"  - {change}")

def docs_command(args):
    """Generate schema documentation."""
    print("Generating schema documentation...")
    models = get_all_models()
    if not models:
        print("No models found.")
        sys.exit(1)
    
    output_dir = args.output or "docs/schema"
    generate_schema_docs(models, output_dir)
    print(f"Documentation generated in {output_dir}")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Database schema management tools")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize migrations")
    init_parser.set_defaults(func=init_command)
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Generate a new migration")
    migrate_parser.add_argument("-m", "--message", help="Migration message")
    migrate_parser.set_defaults(func=migrate_command)
    
    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply migrations")
    apply_parser.set_defaults(func=apply_command)
    
    # Detect command
    detect_parser = subparsers.add_parser("detect", help="Detect schema changes")
    detect_parser.set_defaults(func=detect_command)
    
    # Docs command
    docs_parser = subparsers.add_parser("docs", help="Generate schema documentation")
    docs_parser.add_argument("-o", "--output", help="Output directory")
    docs_parser.set_defaults(func=docs_command)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == "__main__":
    main() 