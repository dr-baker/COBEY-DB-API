from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class EventLog(BaseModel):
    """Pydantic model for event_log table."""

    event_id: int  = Field(description="integer")
    ts: datetime  = Field(description="timestamp with time zone")
    user_id: str  = Field(description="text")
    session_id: str  = Field(description="text")
    event_type: str  = Field(description="text")
    event_data: dict  = Field(description="jsonb")
    event_source: str  = Field(description="text")
    log_level: str  = Field(description="text")
    app_version: Optional[str] = Field(default=None, description="text")
    created_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")
    updated_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")


class EventLogCreate(BaseModel):
    """Schema for creating a new event_log record."""
    event_id: Optional[int] = Field(default=None, description="integer - auto-generated if not provided")
    ts: datetime  = Field(description="timestamp with time zone")
    user_id: str  = Field(description="text")
    session_id: str  = Field(description="text")
    event_type: str  = Field(description="text")
    event_data: dict  = Field(description="jsonb")
    event_source: str  = Field(description="text")
    log_level: str  = Field(description="text")
    app_version: Optional[str] = Field(default=None, description="text")


class EventLogUpdate(BaseModel):
    """Schema for updating an existing event_log record."""
    event_id: Optional[int] = Field(default=None, description="integer")
    ts: Optional[datetime] = Field(default=None, description="timestamp with time zone")
    user_id: Optional[str] = Field(default=None, description="text")
    session_id: Optional[str] = Field(default=None, description="text")
    event_type: Optional[str] = Field(default=None, description="text")
    event_data: Optional[dict] = Field(default=None, description="jsonb")
    event_source: Optional[str] = Field(default=None, description="text")
    log_level: Optional[str] = Field(default=None, description="text")
    app_version: Optional[str] = Field(default=None, description="text")