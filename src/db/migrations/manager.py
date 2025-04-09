"""Database migration manager.

This module manages database schema changes through SQL migration files. Database migrations
are like version control for your database structure - they track changes like creating
tables or adding columns.

Each migration is a .sql file containing the database changes, named with a sequence
(e.g. '001_create_users.sql', '002_add_email.sql') to run in order. The module records
completed migrations in a 'migrations' table to prevent running the same changes twice.

When new migrations are added, this module automatically detects and applies them in
sequence. This allows developers to safely make and share database structure changes
through version control while keeping all environments (dev, staging, prod) consistent.
"""
import os
from typing import List
import asyncpg
from ..connection import db
from ...core.logging import get_logger

logger = get_logger(__name__)
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "versions")

async def clear_migrations_table(conn: asyncpg.Connection) -> None:
    """Clear all records from the migrations table."""
    await conn.execute("DROP TABLE IF EXISTS migrations")
    logger.info("Migrations table cleared")

async def get_applied_migrations(conn: asyncpg.Connection) -> List[str]:
    """Get list of applied migrations."""
    # Create migrations tracking table if it doesn't exist
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    logger.info("Migrations table verified/created")
    
    # Return sorted list of already applied migrations
    migrations = [
        row['name'] 
        for row in await conn.fetch("SELECT name FROM migrations ORDER BY id")
    ]
    logger.info(f"Found {len(migrations)} applied migrations")
    return migrations

async def apply_migrations(clear_existing: bool = False) -> None:
    """Apply pending migrations."""
    try:
        # Establish database connection
        await db.connect()
        async with db.pool.acquire() as conn:
            if clear_existing:
                await clear_migrations_table(conn)
            
            # Get list of already applied migrations
            applied = await get_applied_migrations(conn)
            logger.info(f"Found {len(applied)} previously applied migrations")
            
            # Get all .sql migration files sorted by name
            migration_files = sorted([
                f for f in os.listdir(MIGRATIONS_DIR)
                if f.endswith('.sql')
            ])
            logger.info(f"Found {len(migration_files)} total migration files")
            
            # Apply each pending migration
            pending_migrations = [f for f in migration_files if f not in applied]
            if not pending_migrations:
                logger.info("No pending migrations to apply")
                return
                
            logger.info(f"Found {len(pending_migrations)} pending migrations to apply")
            for file_name in pending_migrations:
                logger.info(f"Starting migration: {file_name}")
                
                # Read migration SQL from file
                path = os.path.join(MIGRATIONS_DIR, file_name)
                with open(path) as f:
                    sql = f.read()
                
                try:
                    # Execute migration
                    await conn.execute(sql)
                    # Record it as applied
                    await conn.execute(
                        "INSERT INTO migrations (name) VALUES ($1)",
                        file_name
                    )
                    logger.info(f"Successfully applied migration: {file_name}")
                except Exception as e:
                    logger.error(f"Failed to apply migration {file_name}: {str(e)}")
                    raise
    
    finally:
        # Always close database connection
        await db.disconnect() 