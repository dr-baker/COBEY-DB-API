from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Session(BaseModel):
    """Pydantic model for sessions table."""

    session_id: str  = Field(description="text")
    ts_start: datetime  = Field(description="timestamp with time zone")
    user_id: str  = Field(description="text")
    exercises_data: dict  = Field(description="jsonb")
    device_type: str  = Field(description="text")
    device_os: str  = Field(description="text")
    region: str  = Field(description="text")
    ip: str  = Field(description="text")
    app_version: str  = Field(description="text")


class SessionCreate(BaseModel):
    """Schema for creating a new sessions record."""
    session_id: str  = Field(description="text")
    ts_start: datetime  = Field(description="timestamp with time zone")
    user_id: str  = Field(description="text")
    exercises_data: dict  = Field(description="jsonb")
    device_type: str  = Field(description="text")
    device_os: str  = Field(description="text")
    region: str  = Field(description="text")
    ip: str  = Field(description="text")
    app_version: str  = Field(description="text")


class SessionUpdate(BaseModel):
    """Schema for updating an existing sessions record."""
    session_id: Optional[str] = Field(default=None, description="text")
    ts_start: Optional[datetime] = Field(default=None, description="timestamp with time zone")
    user_id: Optional[str] = Field(default=None, description="text")
    exercises_data: Optional[dict] = Field(default=None, description="jsonb")
    device_type: Optional[str] = Field(default=None, description="text")
    device_os: Optional[str] = Field(default=None, description="text")
    region: Optional[str] = Field(default=None, description="text")
    ip: Optional[str] = Field(default=None, description="text")
    app_version: Optional[str] = Field(default=None, description="text")