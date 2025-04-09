#!/usr/bin/env python3
"""Database migration script.

This script handles database migrations with options to:
1. Apply pending migrations only (default)
2. Clear existing migrations and reapply all (--clear)
3. Reset database and reapply all migrations (--reset)
"""
import asyncio
import logging
import argparse
from src.db.migrations.manager import apply_migrations
from src.core.logging import get_logger

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Database migration tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add mutually exclusive options for migration behavior
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--clear",
        action="store_true",
        help="Clear migration history and reapply all migrations without dropping tables"
    )
    group.add_argument(
        "--reset",
        action="store_true",
        help="Reset entire database (drop all tables) and reapply all migrations"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting database migration...")
    
    try:
        # Run migrations based on command line arguments
        if args.reset:
            logger.info("Resetting database and reapplying all migrations...")
            # Import here to avoid circular imports
            from src.db.reset import reset_database
            asyncio.run(reset_database())
            asyncio.run(apply_migrations())
        else:
            # Regular migration with optional clear
            asyncio.run(apply_migrations(clear_existing=args.clear))
        
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        raise 