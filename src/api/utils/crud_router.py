"""CRUD router factory.

This module provides a factory function to create standardized CRUD routers
with common operations and error handling.
"""
from typing import Any, Callable, Dict, Optional, List, Type
from fastapi import APIRouter, Depends, HTTPException, Query
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
    """
    router = APIRouter(
        prefix=prefix,
        tags=tags,
        responses={404: {"description": "Not found"}},
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
        response_model=base_model_class,
        summary=f"Get {table_name} by ID",
        description=f"Retrieve a specific {table_name} entry by its unique identifier."
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
            return item
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to get {table_name} by ID: {item_id}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve {table_name}: {str(e)}"
            )

    @router.get(
        "/",
        response_model=List[base_model_class],
        summary=f"List {table_name}",
        description=f"Retrieve a paginated list of {table_name} with optional filtering."
    )
    async def list_items(
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Items per page"),
        kwargs: str = Query("{}", description="JSON string for additional key-value filters"),
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
    ):
        """List items with pagination and optional filters."""
        try:
            # Parse kwargs string into a dictionary
            try:
                additional_filters = json.loads(kwargs)
                if not isinstance(additional_filters, dict):
                     raise ValueError("kwargs must be a JSON object string")
            except (json.JSONDecodeError, ValueError) as json_err:
                 raise HTTPException(status_code=400, detail=f"Invalid kwargs format: {json_err}")
            
            # Apply any custom filters if defined
            filters = {}
            if list_filters:
                for filter_func in list_filters:
                    filter_dict = filter_func()
                    filters.update(filter_dict)
            
            # Combine with additional filters
            filters.update(additional_filters)
            
            # Remove None values from filters
            filters = {k: v for k, v in filters.items() if v is not None}
            
            items = await executor.list(filters=filters, page=page, size=size)
            
            return items
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
        status_code=201,
        response_model=base_model_class,
        summary=f"Create {table_name}",
        description=f"Create a new {table_name} entry with the provided data."
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
            return item
        except Exception as e:
            logger.exception(f"Failed to create {table_name}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create {table_name}: {str(e)}"
            )

    @router.patch(
        "/{item_id}",
        response_model=base_model_class,
        summary=f"Update {table_name}",
        description=f"Update an existing {table_name} entry with the provided data."
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
            return item
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
        status_code=204,
        summary=f"Delete {table_name}",
        description=f"Delete a {table_name} entry by its unique identifier."
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