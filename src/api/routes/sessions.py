"""Session management endpoints.

This module provides CRUD endpoints for managing user sessions in the database.
"""
from typing import Optional, List, Any, Callable
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from ...db.queries.executor import QueryExecutor
from ...api.dependencies import get_query_executor
from ...core.logging import get_logger
from ...models.dynamic import dynamic_models
from pydantic import BaseModel

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Not found"}},
)
logger = get_logger(__name__)

# Define a dependency to get the Session model at runtime
def get_session_model() -> Callable[[], Any]:
    """Dependency to get the dynamic Session model at runtime."""
    async def _get_model():
        model = dynamic_models.get_model("sessions")
        if not model:
            raise HTTPException(status_code=500, detail="Session model not available")
        return model
    return _get_model

@router.get(
    "/{session_id}",
    summary="Get session by ID",
    description="Retrieve a specific session by its unique identifier."
)
async def get_session(
    session_id: str,
    executor: QueryExecutor = Depends(get_query_executor("sessions")),
    SessionModel: Any = Depends(get_session_model())
):
    """Get a session by ID."""
    session = await executor.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get(
    "/",
    summary="List sessions",
    description="Retrieve a paginated list of sessions with optional filtering."
)
async def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    region: Optional[str] = Query(None, description="Filter by region"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    executor: QueryExecutor = Depends(get_query_executor("sessions")),
    SessionModel: Any = Depends(get_session_model())
):
    """List sessions with optional filters and pagination."""
    # Build filters
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if device_type:
        filters["device_type"] = device_type
    if region:
        filters["region"] = region
    if start_time:
        if end_time:
            filters["ts_start"] = {"$gte": start_time, "$lte": end_time}
        else:
            filters["ts_start"] = {"$gte": start_time}
    elif end_time:
        filters["ts_start"] = {"$lte": end_time}
    
    return await executor.list(filters=filters, page=page, size=size)

@router.post(
    "/",
    status_code=201,
    summary="Create session",
    description="Create a new session with the provided data."
)
async def create_session(
    session_data: dict,
    executor: QueryExecutor = Depends(get_query_executor("sessions")),
    SessionModel: Any = Depends(get_session_model())
):
    """Create a new session."""
    try:
        # Validate the input data against the dynamic model
        validated_data = SessionModel(**session_data)
        return await executor.create(validated_data.dict())
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.put(
    "/{session_id}",
    summary="Update session",
    description="Update an existing session's information."
)
async def update_session(
    session_id: str,
    session_data: dict,
    executor: QueryExecutor = Depends(get_query_executor("sessions")),
    SessionModel: Any = Depends(get_session_model())
):
    """Update a session."""
    try:
        # Validate the input data against the dynamic model
        validated_data = SessionModel(**session_data)
        updated = await executor.update(session_id, validated_data.dict())
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")
        return updated
    except Exception as e:
        logger.error("Failed to update session", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{session_id}",
    status_code=204,
    summary="Delete session",
    description="Delete a session by its unique identifier."
)
async def delete_session(
    session_id: str,
    executor: QueryExecutor = Depends(get_query_executor("sessions")),
    SessionModel: Any = Depends(get_session_model())
):
    """Delete a session."""
    deleted = await executor.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return None 