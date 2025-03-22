"""
API routes for session management.
Handles all session-related endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.connection import get_db
from ..db.crud_operations import create_session
from ..schemas.models import SessionCreate, Session

router = APIRouter()

@router.post("/save-session", response_model=Session)
async def save_session(session: SessionCreate, db: AsyncSession = Depends(get_db)):
    """
    Save a new workout session.
    
    Args:
        session (SessionCreate): Session data from request body
        db (AsyncSession): Database session (injected by FastAPI)
    
    Returns:
        Session: Created session data
    
    Raises:
        HTTPException: If session creation fails
    """
    try:
        saved_session = await create_session(
            db=db,
            userid=session.userid,
            sessionid=session.sessionid,
            exercises_data=session.exercises_data,
            device_type=session.device_type,
            device_os=session.device_os,
            useragent=session.useragent,
            region=session.region,
            ip=session.ip
        )
        return saved_session
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save session: {str(e)}"
        ) 