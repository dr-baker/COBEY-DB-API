"""Main application entry point."""
from fastapi import FastAPI
from .api.routes import health, crud_routes
from .core import config
from .core.logging import setup_logging, get_logger
from .db.connection import db
from .models.dynamic import dynamic_models

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Backend API",
    description="FastAPI backend service with PostgreSQL database access",
    version="0.1.0",
)

# Register routers
app.include_router(health.router)
app.include_router(crud_routes.users_router)
app.include_router(crud_routes.recordings_router)
app.include_router(crud_routes.sessions_router)
app.include_router(crud_routes.algos_router)
app.include_router(crud_routes.event_log_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and load dynamic models on startup."""
    logger.info("Connecting to database...")
    await db.connect()
    logger.info("Database connected. Loading dynamic models...")
    await dynamic_models.load_models()
    logger.info("Dynamic models loaded.")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    logger.info("Disconnecting from database...")
    await db.disconnect()
    logger.info("Database disconnected.") 