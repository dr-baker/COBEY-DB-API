"""Health check endpoints for the API.

This module provides endpoints to check the health of the API and its dependencies,
including database connectivity.
"""
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any
from ...api.utils.health import check_health

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    database: Dict[str, Any]
    timestamp: str

router = APIRouter(tags=["health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API Health",
    description="""
    Check the health status of the API and its dependencies.
    
    This endpoint verifies:
    - API service status
    - Database connectivity
    - Current API version
    
    Returns a detailed health status report.
    """,
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "0.1.0",
                        "database": {
                            "status": "connected",
                            "pool_size": 10
                        },
                        "timestamp": "2024-04-10T12:00:00Z"
                    }
                }
            }
        },
        503: {
            "description": "API is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "0.1.0",
                        "database": {
                            "status": "disconnected",
                            "error": "Connection refused"
                        },
                        "timestamp": "2024-04-10T12:00:00Z"
                    }
                }
            }
        }
    }
)
async def health_check() -> HealthResponse:
    """Check if the API is healthy and can connect to the database."""
    return await check_health()

# Health check routes will be implemented here 