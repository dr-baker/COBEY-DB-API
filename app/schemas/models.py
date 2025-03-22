"""
Pydantic models for request/response validation.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from enum import Enum

class RecordingStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class UserBase(BaseModel):
    userid: str
    email: EmailStr
    is_active: bool = True
    firebase_data: Dict[str, Any]
    body_data: Dict[str, Any]
    saved_exercises: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RecordingBase(BaseModel):
    recording_link: str
    recording_type: str
    user_id: str
    status: RecordingStatus = RecordingStatus.PROCESSING
    duration: Optional[timedelta] = None
    created_session_id: Optional[str] = None

class RecordingCreate(RecordingBase):
    pass

class Recording(RecordingBase):
    recording_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AlgorithmBase(BaseModel):
    algo_id: str
    recording_type: str
    location: str
    version: str
    status: str = "active"
    parameters: Optional[Dict[str, Any]] = None

class AlgorithmCreate(AlgorithmBase):
    pass

class Algorithm(AlgorithmBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EventLogBase(BaseModel):
    userid: str
    sessionid: str
    event_type: str
    event_data: Dict[str, Any]
    event_source: str
    log_level: LogLevel
    duration: Optional[timedelta] = None
    app_version: Optional[str] = None

class EventLogCreate(EventLogBase):
    pass

class EventLog(EventLogBase):
    id: int
    ts: datetime

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    userid: str
    sessionid: str
    status: SessionStatus = SessionStatus.ACTIVE
    exercises_data: Dict[str, Any]
    device_type: str
    device_os: str
    useragent: str
    region: str
    ip: str
    session_metadata: Optional[Dict[str, Any]] = None

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    ts_start: datetime
    ts_end: Optional[datetime] = None

    class Config:
        from_attributes = True 