"""CRUD route definitions.

This module provides consolidated CRUD endpoints for all database tables.
"""
from ...api.utils.crud_router import create_crud_router
from ...core.config import get_settings

def get_app_version():
    """Get the current app version from settings."""
    return get_settings().APP_VERSION

# Users router
users_router = create_crud_router(
    table_name="users",
    prefix="/users",
    tags=["users"],
    auto_timestamps=True
)

# Recordings router
recordings_router = create_crud_router(
    table_name="recordings",
    prefix="/recordings",
    tags=["recordings"],
    auto_timestamps=True
)

# Sessions router
sessions_router = create_crud_router(
    table_name="sessions",
    prefix="/sessions",
    tags=["sessions"],
    auto_timestamps=True
)

# Algorithms router
algos_router = create_crud_router(
    table_name="algos",
    prefix="/algos",
    tags=["algos"],
    auto_timestamps=True
)

# Event log router with app_version
event_log_router = create_crud_router(
    table_name="event_log",
    prefix="/events",
    tags=["events"],
    auto_timestamps=True,
    extra_fields={
        "app_version": get_app_version
    }
) 