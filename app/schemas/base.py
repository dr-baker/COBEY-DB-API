"""
Base models and mixins for SQLModel classes.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, ClassVar, Type, get_type_hints
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, String, Boolean, JSON, Interval
from sqlalchemy.dialects.postgresql import JSONB
from enum import Enum
import inspect

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

class TimestampMixin(SQLModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(
        sa_column=Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
            server_default="CURRENT_TIMESTAMP"
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            "updated_at",
            DateTime(timezone=True),
            nullable=False,
            server_default="CURRENT_TIMESTAMP",
            onupdate="CURRENT_TIMESTAMP"
        )
    )

class JsonMixin(SQLModel):
    """Mixin for JSONB fields"""
    @classmethod
    def configure_jsonb_fields(cls, *field_names):
        """Configure JSON fields as JSONB in PostgreSQL"""
        for field_name in field_names:
            field = cls.__fields__[field_name]
            field.field_info.sa_column = Column(
                field_name, 
                JSONB,
                nullable=field.required is False
            )
            
class BaseModel(SQLModel):
    """Base configuration for all models."""
    
    class Config:
        arbitrary_types_allowed = True
        orm_mode = True
