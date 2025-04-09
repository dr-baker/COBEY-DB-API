#!/usr/bin/env python3
"""Database reset and migration script.

This script drops all existing tables (except the migrations table) and then
runs all migrations from scratch. Use with caution in production environments.
"""
import asyncio
import os
from src.db.connection import db
from src.db.migrations.manager import apply_migrations, MIGRATIONS_DIR
from src.core.logging import get_logger

logger = get_logger(__name__)

async def reset_database():
    """Drop all tables except migrations table."""
    try:
        # Establish database connection
        await db.connect()
        async with db.pool.acquire() as conn:
            # Get all table names except migrations
            tables = await conn.fetch("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename != 'migrations'
            """)
            
            if tables:
                # Drop all tables in a transaction
                async with conn.transaction():
                    for table in tables:
                        table_name = table['tablename']
                        logger.info(f"Dropping table: {table_name}")
                        await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                
                logger.info(f"Successfully dropped {len(tables)} tables")
            else:
                logger.info("No tables to drop")
                
    finally:
        # Always close database connection
        await db.disconnect()

async def main():
    """Reset database and run migrations."""
    logger.info("Starting database reset and migration")
    
    # Reset database (drop all tables)
    await reset_database()
    
    # Run migrations
    await apply_migrations()
    
    logger.info("Database reset and migration completed successfully")

if __name__ == "__main__":
    asyncio.run(main()) 