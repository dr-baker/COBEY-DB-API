"""Health check utilities.

This module provides utility functions for checking the health of the API
and its dependencies.
"""
from typing import Dict, Any
from ...db.connection import db
from ...core.logging import get_logger

logger = get_logger(__name__)

async def check_database_health() -> Dict[str, Any]:
    """Check if the database is healthy and can be connected to.
    
    Returns:
        A dictionary with health status information
    """
    try:
        # Try to execute a simple query to check database connectivity
        async with db.transaction() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

async def check_health() -> Dict[str, Any]:
    """Check the health of all system components.
    
    Returns:
        A dictionary with health status information for all components
    """
    # Check database health
    db_health = await check_database_health()
    
    # Overall health is determined by the database health
    overall_status = db_health["status"]
    
    return {
        "status": overall_status,
        "components": {
            "database": db_health
        }
    } 