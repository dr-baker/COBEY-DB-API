"""API response utilities.

This module provides utility functions for creating standardized API responses.
"""
from typing import Any, Dict, Optional, Union
from fastapi.responses import JSONResponse
from fastapi import status

def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a standardized success response.
    
    Args:
        data: The data to include in the response
        message: A success message
        status_code: HTTP status code
        
    Returns:
        A JSONResponse with the standardized format
    """
    response_data = {
        "success": True,
        "message": message,
    }
    
    if data is not None:
        response_data["data"] = data
        
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
        response_data["errors"] = errors
        
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

def paginated_response(
    items: list,
    total: int,
    page: int,
    size: int,
    message: str = "Success"
) -> JSONResponse:
    """Create a standardized paginated response.
    
    Args:
        items: The list of items for the current page
        total: Total number of items across all pages
        page: Current page number
        size: Items per page
        message: A success message
        
    Returns:
        A JSONResponse with the standardized paginated format
    """
    total_pages = (total + size - 1) // size if size > 0 else 0
    
    response_data = {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_data
    ) 