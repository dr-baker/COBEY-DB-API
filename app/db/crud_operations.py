"""
Database CRUD operations.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, Dict, Any, List

from ..db.models import User, Recording, Algorithm, EventLog, Session

async def test_connection(db: AsyncSession) -> bool:
    """Test database connection by executing a simple query."""
    query = text("SELECT 1")
    result = await db.execute(query)
    return bool(result.scalar())

async def create_user(db: AsyncSession, userid: str, firebase_data: Dict[str, Any], body_data: Dict[str, Any]) -> User:
    """Create a new user."""
    db_user = User(
        userid=userid,
        firebase_data=firebase_data,
        body_data=body_data
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, userid: str) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(select(User).filter(User.userid == userid))
    return result.scalar_one_or_none()

async def create_recording(
    db: AsyncSession,
    recording_id: str,
    recording_link: str,
    recording_type: str,
    user_id: str,
    created_session_id: Optional[str] = None
) -> Recording:
    """Create a new recording."""
    db_recording = Recording(
        recording_id=recording_id,
        recording_link=recording_link,
        recording_type=recording_type,
        user_id=user_id,
        created_session_id=created_session_id
    )
    db.add(db_recording)
    await db.commit()
    await db.refresh(db_recording)
    return db_recording

async def create_session(
    db: AsyncSession,
    userid: str,
    sessionid: str,
    exercises_data: Dict[str, Any],
    device_type: str,
    device_os: str,
    useragent: str,
    region: str,
    ip: str
) -> Session:
    """Create a new workout session."""
    db_session = Session(
        userid=userid,
        sessionid=sessionid,
        exercises_data=exercises_data,
        device_type=device_type,
        device_os=device_os,
        useragent=useragent,
        region=region,
        ip=ip
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def log_event(
    db: AsyncSession,
    userid: str,
    sessionid: str,
    event_type: str,
    event_data: Dict[str, Any],
    event_source: str,
    log_level: str,
    app_version: Optional[str] = None
) -> EventLog:
    """Log a new event."""
    db_event = EventLog(
        userid=userid,
        sessionid=sessionid,
        event_type=event_type,
        event_data=event_data,
        event_source=event_source,
        log_level=log_level,
        app_version=app_version
    )
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event

async def create_algorithm(
    db: AsyncSession,
    algo_id: str,
    recording_type: str,
    location: str,
    version: str
) -> Algorithm:
    """Create a new algorithm entry."""
    db_algo = Algorithm(
        algo_id=algo_id,
        recording_type=recording_type,
        location=location,
        version=version
    )
    db.add(db_algo)
    await db.commit()
    await db.refresh(db_algo)
    return db_algo

async def execute_long_query(db: AsyncSession, query_file: str) -> List[Dict[str, Any]]:
    """Execute a long SQL query from a file."""
    with open(query_file, 'r') as f:
        query = text(f.read())
    result = await db.execute(query)
    return [dict(row) for row in result] 