"""
Database models using SQLModel.

This module defines all database models using SQLModel, which combines
SQLAlchemy and Pydantic models into a single definition.

This approach reduces redundancy and maintenance overhead by defining
schema, validation, and DB structure in one place.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import Column, UniqueConstraint
from sqlalchemy import String, Interval, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
import uuid

from .schemas.base import BaseModel, TimestampMixin, JsonMixin
from .schemas.base import RecordingStatus, SessionStatus, LogLevel

def generate_id() -> str:
    """Generate a unique ID for database records."""
    return str(uuid.uuid4())


class User(TimestampMixin, BaseModel, table=True):
    """User table for storing user information."""
    __tablename__ = "users"

    userid: str = Field(
        default_factory=generate_id,
        primary_key=True,
    )
    email: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    firebase_data: Dict[str, Any] = Field(default={})
    body_data: Dict[str, Any] = Field(default={})
    saved_exercises: Optional[Dict[str, Any]] = Field(default=None)
    
    # Relationships
    sessions: List["Session"] = Relationship(back_populates="user")
    recordings: List["Recording"] = Relationship(back_populates="user")
    events: List["EventLog"] = Relationship(back_populates="user")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class Session(TimestampMixin, BaseModel, table=True):
    """Session table for storing workout sessions."""
    __tablename__ = "sessions"

    sessionid: str = Field(
        default_factory=generate_id,
        primary_key=True,
    )
    ts_start: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("ts_start", TIMESTAMP(timezone=True), index=True)
    )
    ts_end: Optional[datetime] = Field(default=None)
    userid: str = Field(foreign_key="users.userid", nullable=False)
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    exercises_data: Dict[str, Any] = Field(default={})
    device_type: str
    device_os: str
    useragent: str
    region: str
    ip: str
    session_metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    # Relationships
    user: User = Relationship(back_populates="sessions")
    recordings: List["Recording"] = Relationship(back_populates="session")
    events: List["EventLog"] = Relationship(back_populates="session")


class Recording(TimestampMixin, BaseModel, table=True):
    """Recordings table for storing workout recordings."""
    __tablename__ = "recordings"

    recording_id: str = Field(
        default_factory=generate_id,
        primary_key=True,
    )
    recording_link: str
    recording_type: str
    user_id: str = Field(foreign_key="users.userid", index=True)
    status: RecordingStatus = Field(default=RecordingStatus.PROCESSING)
    duration: Optional[timedelta] = Field(default=None)
    created_session_id: Optional[str] = Field(default=None, foreign_key="sessions.sessionid")
    
    # Relationships
    user: User = Relationship(back_populates="recordings")
    session: Optional[Session] = Relationship(back_populates="recordings")


class Algorithm(TimestampMixin, BaseModel, table=True):
    """Algorithms table for storing algorithm information."""
    __tablename__ = "algos"

    algo_id: str = Field(
        default_factory=generate_id,
        primary_key=True,
    )
    recording_type: str
    location: str
    version: str
    status: str = Field(default="active")
    parameters: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        table_args = (
            UniqueConstraint("recording_type", "version", name="uix_algo_type_version"),
        )


class EventLog(BaseModel, table=True):
    """Event log table for tracking system events."""
    __tablename__ = "event_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("ts", TIMESTAMP(timezone=True), index=True)
    )
    userid: str = Field(foreign_key="users.userid")
    sessionid: str = Field(foreign_key="sessions.sessionid")
    event_type: str
    event_data: Dict[str, Any] = Field(default={})
    event_source: str
    log_level: LogLevel
    duration: Optional[timedelta] = Field(default=None)
    app_version: Optional[str] = Field(default=None)
    
    # Relationships
    user: User = Relationship(back_populates="events")
    session: Session = Relationship(back_populates="events")


# Configure JSON fields to use PostgreSQL JSONB
User.configure_jsonb_fields("firebase_data", "body_data", "saved_exercises")
Session.configure_jsonb_fields("exercises_data", "session_metadata")
Algorithm.configure_jsonb_fields("parameters")
EventLog.configure_jsonb_fields("event_data") 