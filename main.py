"""
Main application entry point.
Initializes FastAPI app and includes all routes.
"""
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

# Import app modules
from app.db.connection import init_db, shutdown_db, get_db
from app.api import sessions_router
from app.db.crud_operations import execute_long_query, test_connection
from app.utils.ssh import SSHError

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to manage database initialization and shutdown.
    Ensures proper cleanup of resources.
    """
    try:
        await init_db()  # Initialize DB and SSH tunnel
        yield
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        raise
    finally:
        await shutdown_db()  # Cleanup DB and close SSH tunnel

# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="Workout Session API",
    description="API for managing workout sessions with PostgreSQL backend",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "FastAPI backend is running"}

@app.get("/test-db")
async def test_db(db: AsyncSession = Depends(get_db)):
    """
    Test database connection.
    
    Raises:
        HTTPException: If database connection fails
    """
    try:
        result = await test_connection(db)
        return {"message": "Database connection successful", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

@app.get("/long-query")
async def long_query(db: AsyncSession = Depends(get_db)):
    """
    Execute a long SQL query from an external file.
    
    Raises:
        HTTPException: If query execution fails
    """
    try:
        result = await execute_long_query(db, "app/sql/long_query.sql")
        return {"data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )
