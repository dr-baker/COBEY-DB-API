"""
SQLAlchemy ORM models for database tables.
These models define the structure of our database tables.
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON, Boolean, Interval, Enum, UniqueConstraint, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

# Create metadata with naming convention
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

Base = declarative_base(metadata=metadata)

class RecordingStatus(enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class SessionStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"

class LogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class User(Base):
    """User table for storing user information."""
    __tablename__ = "users"

    userid = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    firebase_data = Column(JSONB)
    body_data = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    saved_exercises = Column(JSONB, nullable=True)

class Session(Base):
    """Session table for storing workout sessions."""
    __tablename__ = "sessions"

    sessionid = Column(String, primary_key=True)
    ts_start = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    ts_end = Column(TIMESTAMP(timezone=True), nullable=True)
    userid = Column(String, nullable=False)
    status = Column(Enum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE)
    exercises_data = Column(JSONB)
    device_type = Column(String, nullable=False)
    device_os = Column(String, nullable=False)
    useragent = Column(String, nullable=False)
    region = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    session_metadata = Column(JSONB, nullable=True)

class Recording(Base):
    """Recordings table for storing workout recordings."""
    __tablename__ = "recordings"

    recording_id = Column(String, primary_key=True)
    recording_link = Column(String, nullable=False)
    recording_type = Column(String, nullable=False)
    userid = Column(String, nullable=False)
    status = Column(Enum(RecordingStatus), nullable=False, default=RecordingStatus.PROCESSING)
    duration = Column(Interval, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    sessionid = Column(String, nullable=True)

class Algorithm(Base):
    """Algorithms table for storing algorithm information."""
    __tablename__ = "algos"

    algo_id = Column(String, primary_key=True)
    recording_type = Column(String, nullable=False)
    location = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    parameters = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('recording_type', 'version', name='uix_algo_type_version'),
    )

class EventLog(Base):
    """Event log table for tracking system events."""
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    userid = Column(String, nullable=False)
    sessionid = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    event_data = Column(JSONB)
    event_source = Column(String, nullable=False)
    log_level = Column(Enum(LogLevel), nullable=False)
    duration = Column(Interval, nullable=True)
    app_version = Column(String, nullable=True) 