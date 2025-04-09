"""Health check endpoints for the API.

This module provides endpoints to check the health of the API and its dependencies,
including database connectivity.
"""
from fastapi import APIRouter
from ...api.utils.health import check_health

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Check if the API is healthy and can connect to the database."""
    return await check_health()

# Health check routes will be implemented here 