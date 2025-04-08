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
    # Return sorted list of already applied migrations
    return [
        row['name'] 
        for row in await conn.fetch("SELECT name FROM migrations ORDER BY id")
    ]

async def apply_migrations() -> None:
    """Apply pending migrations."""
    # Get directory containing migration files
    
    try:
        # Establish database connection
        await db.connect()
        async with db.pool.acquire() as conn:
            # Get list of already applied migrations
            applied = await get_applied_migrations(conn)
            
            # Get all .sql migration files sorted by name
            migration_files = sorted([
                f for f in os.listdir(MIGRATIONS_DIR)
                if f.endswith('.sql')
            ])
            
            # Apply each pending migration in a transaction
            for file_name in migration_files:
                if file_name not in applied:
                    logger.info("Applying migration", migration=file_name)
                    
                    # Read migration SQL from file
                    path = os.path.join(MIGRATIONS_DIR, file_name)
                    with open(path) as f:
                        sql = f.read()
                        
                    # Execute migration and record it as applied
                    async with conn.transaction():
                        await conn.execute(sql)
                        await conn.execute(
                            "INSERT INTO migrations (name) VALUES ($1)",
                            file_name
                        )
                    
                    logger.info("Migration applied", migration=file_name)
    
    finally:
        # Always close database connection
        await db.disconnect() 