#!/usr/bin/env python3
"""Database migration script."""
import asyncio
from src.db.migrations.manager import apply_migrations

if __name__ == "__main__":
    asyncio.run(apply_migrations()) 