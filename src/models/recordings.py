from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Recording(BaseModel):
    """Pydantic model for recordings table."""

    recording_id: str  = Field(description="text")
    recording_link: str  = Field(description="text")
    recording_type: str  = Field(description="text")
    user_id: str  = Field(description="text")
    created_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")
    updated_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")
    created_session_id: str  = Field(description="text")


class RecordingCreate(BaseModel):
    """Schema for creating a new recordings record."""
    recording_id: str  = Field(description="text")
    recording_link: str  = Field(description="text")
    recording_type: str  = Field(description="text")
    user_id: str  = Field(description="text")
    created_session_id: str  = Field(description="text")


class RecordingUpdate(BaseModel):
    """Schema for updating an existing recordings record."""
    recording_id: Optional[str] = Field(default=None, description="text")
    recording_link: Optional[str] = Field(default=None, description="text")
    recording_type: Optional[str] = Field(default=None, description="text")
    user_id: Optional[str] = Field(default=None, description="text")
    created_session_id: Optional[str] = Field(default=None, description="text")