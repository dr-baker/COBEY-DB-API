from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class User(BaseModel):
    """Pydantic model for users table."""

    user_id: str  = Field(description="text")
    firebase_data: dict  = Field(description="jsonb")
    body_data: dict  = Field(description="jsonb")
    created_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")
    updated_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")


class UserCreate(BaseModel):
    """Schema for creating a new users record."""
    user_id: str  = Field(description="text")
    firebase_data: dict  = Field(description="jsonb")
    body_data: dict  = Field(description="jsonb")


class UserUpdate(BaseModel):
    """Schema for updating an existing users record."""
    user_id: Optional[str] = Field(default=None, description="text")
    firebase_data: Optional[dict] = Field(default=None, description="jsonb")
    body_data: Optional[dict] = Field(default=None, description="jsonb")