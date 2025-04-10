"""CRUD router factory.

This module provides a factory function to create standardized CRUD routers
with common operations and error handling.

Example usage:
    ```python
    # Create a router for a 'users' table
    users_router = create_crud_router(
        table_name="users",
        prefix="/users",
        tags=["users"],
        auto_timestamps=True
    )
    
    # Include the router in your FastAPI app
    app.include_router(users_router)
    ```

The router will automatically create the following endpoints:
- GET /{prefix}/ - List items with pagination
- GET /{prefix}/{item_id} - Get item by ID
- POST /{prefix}/ - Create new item
- PUT /{prefix}/{item_id} - Replace item
- PATCH /{prefix}/{item_id} - Update item
- DELETE /{prefix}/{item_id} - Delete item
"""
from typing import Any, Callable, Dict, Optional, List, Type
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from ...db.queries.executor import QueryExecutor
from ...api.dependencies import get_query_executor
from ...core.logging import get_logger
from ...models.mapping import get_model_name
import json

logger = get_logger(__name__)

# Map table names to their model names
TABLE_TO_MODEL_MAP = {
    "users": "User",
    "recordings": "Recording",
    "sessions": "Session",
    "algos": "Algo",
    "event_log": "EventLog"
}

def create_crud_router(
    *,
    table_name: str,
    prefix: str,
    tags: list[str],
    auto_timestamps: bool = True,
    extra_fields: Optional[Dict[str, Callable[[], Any]]] = None,
    list_filters: Optional[List[Callable]] = None,
) -> APIRouter:
    """Create a router with standard CRUD operations.
    
    Args:
        table_name: Name of the database table
        prefix: URL prefix for the router
        tags: OpenAPI tags for the router
        auto_timestamps: Whether to automatically add created_at/updated_at
        extra_fields: Dict of field names to callables that provide their values
        list_filters: List of filter functions to add to the list endpoint
        
    Returns:
        APIRouter: A FastAPI router with CRUD endpoints
        
    Example:
        ```python
        # Create a router for users
        users_router = create_crud_router(
            table_name="users",
            prefix="/users",
            tags=["users"],
            auto_timestamps=True
        )
        ```
    """
    router = APIRouter(
        prefix=prefix,
        tags=tags,
        responses={
            404: {"description": "Resource not found"},
            422: {"description": "Validation error"},
            500: {"description": "Internal server error"}
        },
    )
    
    # Import model classes directly by name
    import importlib
    module = importlib.import_module(f"src.models.{table_name}")
    model_name = get_model_name(table_name)
    
    base_model_class = getattr(module, model_name)
    create_model_class = getattr(module, f"{model_name}Create")
    update_model_class = getattr(module, f"{model_name}Update")

    @router.get(
        "/{item_id}",
        response_model=Dict[str, base_model_class],
        summary=f"Get {table_name} by ID",
        description=f"""
        Retrieve a specific {table_name} entry by its unique identifier.
        
        This endpoint returns a single {table_name} record with all its fields.
        If the record is not found, a 404 error is returned.
        """,
        responses={
            200: {
                "description": f"{table_name} found",
                "content": {
                    "application/json": {
                        "example": {
                            "data": {
                                "id": "123",
                                "name": "Example",
                                "created_at": "2024-04-10T12:00:00Z",
                                "updated_at": "2024-04-10T12:00:00Z"
                            }
                        }
                    }
                }
            },
            404: {
                "description": f"{table_name} not found",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": f"{table_name} not found"
                        }
                    }
                }
            }
        }
    )
    async def get_item(
        item_id: str,
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
    ):
        """Get an item by ID."""
        try:
            item = await executor.get_by_id(item_id)
            if not item:
                raise HTTPException(status_code=404, detail=f"{table_name} not found")
            return {"data": item}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to get {table_name} by ID: {item_id}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve {table_name}: {str(e)}"
            )

    # Define a dynamic response model for the list endpoint
    class PaginatedResponse(BaseModel):
        """Paginated response model."""
        items: List[base_model_class]

    @router.get(
        "/",
        response_model=Dict[str, PaginatedResponse],
        summary=f"List {table_name}",
        description=f"""
        Retrieve a paginated list of {table_name} with optional filtering.
        
        This endpoint supports:
        - Pagination (page and size parameters)
        - Filtering by various fields
        - Sorting (if implemented)
        
        The response includes a list of {table_name} records and pagination metadata.
        """,
        responses={
            200: {
                "description": "List of items",
                "content": {
                    "application/json": {
                        "example": {
                            "data": {
                                "items": [
                                    {
                                        "id": "123",
                                        "name": "Example 1",
                                        "created_at": "2024-04-10T12:00:00Z"
                                    },
                                    {
                                        "id": "124",
                                        "name": "Example 2",
                                        "created_at": "2024-04-10T12:01:00Z"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    )
    async def list_items(
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Items per page"),
        user_id: Optional[str] = Query(None, description="Filter by user ID"),
        recording_type: Optional[str] = Query(None, description="Filter by recording type"),
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
    ):
        """List items with pagination and optional filters."""
        try:
            # Build filters from query parameters
            filters = {}
            if user_id is not None:
                filters["user_id"] = user_id
            if recording_type is not None:
                filters["recording_type"] = recording_type
            
            items = await executor.list(filters=filters, page=page, size=size)
            
            # Return structure matches the client and the new PaginatedResponse model
            return {"data": {"items": items}}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to list {table_name}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list {table_name}: {str(e)}"
            )

    @router.post(
        "/",
        status_code=status.HTTP_201_CREATED,
        response_model=Dict[str, base_model_class],
        summary=f"Create {table_name}",
        description=f"""
        Create a new {table_name} entry with the provided data.
        
        This endpoint:
        - Validates the input data
        - Adds automatic timestamps (if enabled)
        - Adds any extra fields (if specified)
        - Creates the record in the database
        
        Returns the created record with all fields.
        """,
        responses={
            201: {
                "description": f"{table_name} created successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "data": {
                                "id": "123",
                                "name": "New Example",
                                "created_at": "2024-04-10T12:00:00Z",
                                "updated_at": "2024-04-10T12:00:00Z"
                            }
                        }
                    }
                }
            },
            422: {
                "description": "Validation error",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": [
                                {
                                    "loc": ["body", "name"],
                                    "msg": "field required",
                                    "type": "value_error.missing"
                                }
                            ]
                        }
                    }
                }
            }
        }
    )
    async def create_item(
        data: create_model_class,
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
    ):
        """Create a new item."""
        logger.info(f"Creating item for table: {executor.table_name}")
        try:
            # Convert Pydantic model to dict
            data_dict = data.model_dump(exclude_unset=True)
            
            # Add automatic fields
            if auto_timestamps:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                data_dict["created_at"] = now
                data_dict["updated_at"] = now
            
            # Add any extra fields
            if extra_fields:
                for field_name, field_provider in extra_fields.items():
                    if field_name not in data_dict:
                        data_dict[field_name] = field_provider()
            
            # Create the item
            item = await executor.create(data_dict)
            return {"data": item}
        except Exception as e:
            logger.exception(f"Failed to create {table_name}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create {table_name}: {str(e)}"
            )

    @router.put(
        "/{item_id}",
        response_model=Dict[str, base_model_class],
        summary=f"Replace {table_name}",
        description=f"""
        Completely replace an existing {table_name} entry with the provided data.
        
        This endpoint:
        - Validates the input data
        - Replaces all fields of the existing record
        - Updates the timestamp (if enabled)
        - Returns the updated record
        
        Note: This is a complete replacement, not a partial update.
        """,
        responses={
            200: {
                "description": f"{table_name} replaced successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "data": {
                                "id": "123",
                                "name": "Updated Example",
                                "created_at": "2024-04-10T12:00:00Z",
                                "updated_at": "2024-04-10T12:02:00Z"
                            }
                        }
                    }
                }
            },
            404: {
                "description": f"{table_name} not found",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": f"{table_name} not found"
                        }
                    }
                }
            }
        }
    )
    async def replace_item(
        item_id: str,
        data: create_model_class,
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
    ):
        """Replace an existing item completely."""
        try:
            # Convert Pydantic model to dict
            data_dict = data.model_dump(exclude_unset=True)
            
            # Add automatic fields
            if auto_timestamps:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                data_dict["updated_at"] = now
            
            # Add any extra fields
            if extra_fields:
                for field_name, field_provider in extra_fields.items():
                    if field_name not in data_dict:
                        data_dict[field_name] = field_provider()
            
            # Replace the item
            item = await executor.update(item_id, data_dict, replace=True)
            if not item:
                raise HTTPException(status_code=404, detail=f"{table_name} not found")
            return {"data": item}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to replace {table_name}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to replace {table_name}: {str(e)}"
            )

    @router.patch(
        "/{item_id}",
        response_model=Dict[str, base_model_class],
        summary=f"Update {table_name}",
        description=f"""
        Update an existing {table_name} entry with the provided data.
        
        This endpoint:
        - Validates the input data
        - Updates only the provided fields
        - Updates the timestamp (if enabled)
        - Returns the updated record
        
        Note: This is a partial update, only the provided fields will be changed.
        """,
        responses={
            200: {
                "description": f"{table_name} updated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "data": {
                                "id": "123",
                                "name": "Updated Example",
                                "created_at": "2024-04-10T12:00:00Z",
                                "updated_at": "2024-04-10T12:03:00Z"
                            }
                        }
                    }
                }
            },
            404: {
                "description": f"{table_name} not found",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": f"{table_name} not found"
                        }
                    }
                }
            }
        }
    )
    async def update_item(
        item_id: str,
        data: update_model_class,
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
    ):
        """Update an existing item."""
        try:
            # Convert Pydantic model to dict
            data_dict = data.model_dump(exclude_unset=True)
            
            # Add updated_at timestamp
            if auto_timestamps and data_dict:
                from datetime import datetime, timezone
                data_dict["updated_at"] = datetime.now(timezone.utc)
            
            # Update the item
            item = await executor.update(item_id, data_dict)
            if not item:
                raise HTTPException(status_code=404, detail=f"{table_name} not found")
            return {"data": item}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to update {table_name}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update {table_name}: {str(e)}"
            )

    @router.delete(
        "/{item_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Delete {table_name}",
        description=f"""
        Delete a {table_name} entry by its unique identifier.
        
        This endpoint:
        - Deletes the record from the database
        - Returns 204 No Content on success
        - Returns 404 if the record is not found
        """,
        responses={
            204: {
                "description": f"{table_name} deleted successfully"
            },
            404: {
                "description": f"{table_name} not found",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": f"{table_name} not found"
                        }
                    }
                }
            }
        }
    )
    async def delete_item(
        item_id: str,
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
    ):
        """Delete an item."""
        try:
            success = await executor.delete(item_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"{table_name} not found")
            return None
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to delete {table_name}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete {table_name}: {str(e)}"
            )
    
    return router 