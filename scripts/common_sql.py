#!/usr/bin/env python3
import asyncio
import sys
from src.db.connection import db

async def execute_sql(sql: str):
    try:
        await db.connect()
        async with db.transaction() as conn:
            result = await conn.fetch(sql)
            for row in result:
                print(dict(row))
    finally:
        await db.disconnect()

async def get_table_names():
    """Get all table names in the database."""
    sql = """
        SELECT table_name 
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """
    await execute_sql(sql)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python common_sql.py --tables")
        print("  python common_sql.py 'SQL QUERY'")
        sys.exit(1)
    
    if sys.argv[1] == '--tables':
        asyncio.run(get_table_names())
    else:
        asyncio.run(execute_sql(sys.argv[1]))