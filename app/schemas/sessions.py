"""
Pydantic models for request/response validation.
These models define the structure of our API's input/output data.
"""
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional

class SessionCreate(BaseModel):
    """
    Schema for creating a new workout session.
    
    Attributes:
        user_id (int): ID of the user creating the session
        session_data (str): JSON string containing workout details
    """
    user_id: int
    session_data: str

    @validator('user_id')
    def user_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('User ID must be positive')
        return v

class SessionResponse(BaseModel):
    """
    Schema for session response data.
    
    Attributes:
        id (int): Session ID
        user_id (int): User ID
        session_data (str): JSON string containing workout details
        created_at (datetime): When the session was created
        updated_at (datetime): When the session was last updated
    """
    id: int
    user_id: int
    session_data: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model 