"""API validation utilities.

This module provides utility functions for common validation tasks.
"""
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

def validate_model(
    data: Dict[str, Any],
    model_class: Type[BaseModel],
    error_message: str = "Validation error"
) -> BaseModel:
    """Validate data against a Pydantic model.
    
    Args:
        data: The data to validate
        model_class: The Pydantic model class to validate against
        error_message: Custom error message for validation failures
        
    Returns:
        The validated model instance
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": error_message, "errors": e.errors()}
        )

def validate_id_exists(
    item_id: str,
    item: Optional[Any],
    item_type: str = "Item"
) -> None:
    """Validate that an item exists.
    
    Args:
        item_id: The ID of the item
        item: The item to check
        item_type: The type of item for error messages
        
    Raises:
        HTTPException: If the item doesn't exist
    """
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{item_type} with ID '{item_id}' not found"
        )

def validate_pagination_params(
    page: int,
    size: int,
    max_size: int = 100
) -> None:
    """Validate pagination parameters.
    
    Args:
        page: Page number
        size: Items per page
        max_size: Maximum allowed items per page
        
    Raises:
        HTTPException: If pagination parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    if size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be greater than 0"
        )
    
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page size cannot exceed {max_size}"
        )

def parse_datetime(
    date_str: str,
    field_name: str = "date"
) -> datetime:
    """Parse a datetime string.
    
    Args:
        date_str: The datetime string to parse
        field_name: The name of the field for error messages
        
    Returns:
        The parsed datetime
        
    Raises:
        HTTPException: If parsing fails
    """
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format. Expected ISO format (e.g., '2023-01-01T12:00:00Z')"
        ) 