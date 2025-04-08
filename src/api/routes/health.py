"""Health check endpoints for the API.

This module provides endpoints to check the health of the API and its dependencies,
including database connectivity.
"""
from fastapi import APIRouter, Depends
from ...db.connection import db
from ...core.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)

@router.get("/health")
async def health_check():
    """Check if the API is healthy and can connect to the database."""
    try:
        # Try to execute a simple query to check database connectivity
        async with db.transaction() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# Health check routes will be implemented here 