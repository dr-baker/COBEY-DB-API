"""CRUD router factory.

This module provides a factory function to create standardized CRUD routers
with common operations and error handling.
"""
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from ...db.queries.executor import QueryExecutor
from ...api.dependencies import get_query_executor
from ...core.logging import get_logger
from ...models.dynamic import dynamic_models
from ...core.config import get_settings
from .responses import success_response, error_response, paginated_response

logger = get_logger(__name__)

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
    # Map API table names to actual database table names
    table_name_mapping = {
        "users": "users",
        "recordings": "recordings",
        "sessions": "sessions",
        "algos": "algos",
        "events": "event_log"  # Map 'events' to 'event_log' table
    }
    
    # Use the mapped table name for database operations
    db_table_name = table_name_mapping.get(table_name, table_name)
    
    router = APIRouter(
        prefix=prefix,
        tags=tags,
        responses={404: {"description": "Not found"}},
    )
    
    # Define a dependency to get the model at runtime
    def get_model() -> Callable[[], Any]:
        """Dependency to get the dynamic model at runtime."""
        async def _get_model():
            model = dynamic_models.get_model(db_table_name)
            if not model:
                raise HTTPException(
                    status_code=500, 
                    detail=f"{table_name} model not available"
                )
            return model
        return _get_model

    def add_timestamps(data: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp fields to the data if auto_timestamps is enabled."""
        if not auto_timestamps:
            return data
            
        current_time = datetime.now(timezone.utc).isoformat()
        if "created_at" not in data:
            data["created_at"] = current_time
        data["updated_at"] = current_time
        return data

    @router.get(
        "/{item_id}",
        summary=f"Get {table_name} by ID",
        description=f"Retrieve a specific {table_name} entry by its unique identifier."
    )
    async def get_item(
        item_id: str,
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
        Model: Any = Depends(get_model())
    ):
        """Get an item by ID."""
        item = await executor.get_by_id(item_id)
        if not item:
            return error_response(
                message=f"{table_name} not found",
                status_code=404
            )
        return success_response(
            data=item,
            message=f"{table_name} retrieved successfully"
        )

    # Build the list endpoint with any custom filters
    list_params = [
        Query(1, ge=1, description="Page number", alias="page"),
        Query(10, ge=1, le=100, description="Items per page", alias="size"),
    ]
    
    if list_filters:
        list_params.extend(filter_param for filter_func in list_filters for filter_param in filter_func())

    @router.get(
        "/",
        summary=f"List {table_name}",
        description=f"Retrieve a paginated list of {table_name} with optional filtering."
    )
    async def list_items(
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Items per page"),
        # Explicitly define common filter parameters
        user_id: Optional[str] = Query(None, description="Filter by user ID"),
        recording_type: Optional[str] = Query(None, description="Filter by recording type (for recordings, algos)"),
        version: Optional[str] = Query(None, description="Filter by version (for algos)"),
        session_id: Optional[str] = Query(None, description="Filter by session ID (for events)"),
        event_type: Optional[str] = Query(None, description="Filter by event type (for events)"),
        event_source: Optional[str] = Query(None, description="Filter by event source (for events)"),
        start_time: Optional[datetime] = Query(None, description="Filter by start time (for events)"),
        end_time: Optional[datetime] = Query(None, description="Filter by end time (for events)"),
        # Add other potential filters if needed, e.g., for sessions
        region: Optional[str] = Query(None, description="Filter by region (for sessions)")
    ):
        """List items with pagination and optional filters."""
        try:
            # Build filters dict from explicit parameters
            filters = {}
            local_vars = locals()
            potential_filters = [
                'user_id', 'recording_type', 'version', 'session_id', 
                'event_type', 'event_source', 'start_time', 'end_time', 'region'
            ]
            for key in potential_filters:
                value = local_vars.get(key)
                if value is not None:
                    filters[key] = value
            
            items = await executor.list(filters=filters, page=page, size=size)
            # Correctly get total count for pagination
            total = await executor.count(filters=filters) 
            
            # Convert items to dicts for the response
            items_dict = [item.model_dump() for item in items]

            return paginated_response(
                items=items_dict,
                total=total,
                page=page,
                size=size,
                message=f"{table_name} list retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error listing {table_name}", error=str(e))
            return error_response(str(e))

    @router.post("/", response_model=Any, status_code=201)
    async def create(
        data: Dict[str, Any],
        executor: QueryExecutor = Depends(get_query_executor(table_name))
    ):
        """Create a new record."""
        try:
            # Add timestamps and any extra fields
            data = add_timestamps(data)
            if extra_fields:
                for field, value_fn in extra_fields.items():
                    if field not in data:
                        data[field] = value_fn()
                        
            result = await executor.create(data)
            # Explicitly dump model to dict for JSON response
            return success_response(result.model_dump())
        except Exception as e:
            logger.error(f"Error creating {table_name}", error=str(e))
            return error_response(str(e))

    @router.put("/{record_id}", response_model=Any)
    async def update(
        record_id: str,
        data: Dict[str, Any],
        executor: QueryExecutor = Depends(get_query_executor(table_name))
    ):
        """Update an existing record."""
        try:
            # Add updated_at timestamp
            data = add_timestamps(data)
            result = await executor.update(record_id, data)
            if not result:
                raise HTTPException(status_code=404, detail=f"{table_name} not found")
            # Explicitly dump model to dict for JSON response
            return success_response(result.model_dump())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating {table_name}", error=str(e))
            return error_response(str(e))

    @router.delete(
        "/{item_id}",
        status_code=204,
        summary=f"Delete {table_name}",
        description=f"Delete a {table_name} entry by its unique identifier."
    )
    async def delete_item(
        item_id: str,
        executor: QueryExecutor = Depends(get_query_executor(table_name)),
        Model: Any = Depends(get_model())
    ):
        """Delete an item."""
        deleted = await executor.delete(item_id)
        if not deleted:
            return error_response(
                message=f"{table_name} not found",
                status_code=404
            )
        return success_response(
            message=f"{table_name} deleted successfully",
            status_code=204
        )

    return router 