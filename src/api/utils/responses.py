"""API response utilities.

This module provides utility functions for creating standardized API responses.
"""
from typing import Any, Dict, List, Optional, Union
from fastapi import status
from fastapi.responses import JSONResponse
import json
from datetime import datetime
from pydantic import BaseModel

def serialize_for_json(obj: Any) -> Any:
    """
    Serialize objects for JSON response.
    
    This function handles:
    - datetime objects
    - Pydantic models (using JSON mode)
    - dictionaries and lists
    - other basic types
    
    Args:
        obj: The object to serialize
        
    Returns:
        JSON serializable version of the object
    """
    if isinstance(obj, datetime):
        # Should ideally be handled by model_dump(mode='json') or direct serialization
        return obj.isoformat()
    elif isinstance(obj, BaseModel):
        # Use mode='json' for built-in JSON-compatible serialization (e.g., datetime -> str)
        return obj.model_dump(mode='json')
    elif isinstance(obj, dict):
        # Recursively serialize dictionary values
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Recursively serialize list items
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Fallback for other objects, might be risky
        return serialize_for_json(obj.__dict__)
    else:
        # Basic types
        return obj

def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        A JSONResponse with the standardized format
    """
    response_data = {
        "success": True,
        "message": message,
    }
    
    if data is not None:
        response_data["data"] = serialize_for_json(data)
        
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

def error_response(
    message: str = "An error occurred",
    errors: Optional[Union[str, Dict[str, Any], list]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        message: An error message
        errors: Additional error details
        status_code: HTTP status code
        
    Returns:
        A JSONResponse with the standardized format
    """
    response_data = {
        "success": False,
        "message": message,
    }
    
    if errors is not None:
        response_data["errors"] = serialize_for_json(errors)
        
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int,
    message: str = "Success"
) -> JSONResponse:
    """Create a standardized paginated response.
    
    Args:
        items: List of items for the current page
        total: Total number of items
        page: Current page number
        size: Page size
        message: Success message
        
    Returns:
        A JSONResponse with the standardized paginated format
    """
    response_data = {
        "success": True,
        "message": message,
        "data": {
            "items": serialize_for_json(items),
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size > 0 else 0
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_data
    ) 