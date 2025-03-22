"""
Session management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ...db import get_db, session as crud_session
from ...schemas.models import SessionCreate, SessionRead, SessionUpdate

router = APIRouter()

@router.post("/", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
) -> SessionRead:
    """
    Create a new workout session.
    
    Args:
        session_data (SessionCreate): Session data from request body
        db (AsyncSession): Database session (injected by FastAPI)
    
    Returns:
        SessionRead: Created session data
    
    Raises:
        HTTPException: If session creation fails
    """
    try:
        db_session = await crud_session.create(db=db, obj_in=session_data)
        return SessionRead.model_validate(db_session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> SessionRead:
    """
    Get a session by ID.
    
    Args:
        session_id (str): Session ID to retrieve
        db (AsyncSession): Database session (injected by FastAPI)
    
    Returns:
        SessionRead: Session data
    
    Raises:
        HTTPException: If session is not found
    """
    db_session = await crud_session.get_by_sessionid(db=db, sessionid=session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return SessionRead.model_validate(db_session)

@router.get("/user/{user_id}", response_model=List[SessionRead])
async def get_user_sessions(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[SessionRead]:
    """
    Get all sessions for a user.
    
    Args:
        user_id (str): User ID to get sessions for
        db (AsyncSession): Database session (injected by FastAPI)
    
    Returns:
        List[SessionRead]: List of session data
    """
    db_sessions = await crud_session.get_user_sessions(db=db, userid=user_id)
    return [SessionRead.model_validate(s) for s in db_sessions]

@router.patch("/{session_id}/status", response_model=SessionRead)
async def update_session_status(
    session_id: str,
    status: str,
    db: AsyncSession = Depends(get_db)
) -> SessionRead:
    """
    Update a session's status.
    
    Args:
        session_id (str): Session ID to update
        status (str): New status value
        db (AsyncSession): Database session (injected by FastAPI)
    
    Returns:
        SessionRead: Updated session data
    
    Raises:
        HTTPException: If session is not found or update fails
    """
    try:
        db_session = await crud_session.update_status(db=db, sessionid=session_id, status=status)
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        return SessionRead.model_validate(db_session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session status: {str(e)}"
        ) 