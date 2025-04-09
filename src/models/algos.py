from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Algo(BaseModel):
    """Pydantic model for algos table."""

    algo_id: str  = Field(description="text")
    recording_type: str  = Field(description="text")
    location: str  = Field(description="text")
    version: str  = Field(description="text")
    created_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")
    updated_at: Optional[datetime] = Field(default=None, description="timestamp with time zone")


class AlgoCreate(BaseModel):
    """Schema for creating a new algos record."""
    algo_id: str  = Field(description="text")
    recording_type: str  = Field(description="text")
    location: str  = Field(description="text")
    version: str  = Field(description="text")


class AlgoUpdate(BaseModel):
    """Schema for updating an existing algos record."""
    algo_id: Optional[str] = Field(default=None, description="text")
    recording_type: Optional[str] = Field(default=None, description="text")
    location: Optional[str] = Field(default=None, description="text")
    version: Optional[str] = Field(default=None, description="text")