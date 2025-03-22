"""
Database connection management.
"""
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from ..utils.ssh import create_ssh_tunnel, close_ssh_tunnel
from ..config import get_database_config

# Get database configuration
db_config = get_database_config()

# Database configuration
DB_HOST = db_config["DB_HOST"]
DB_PORT = db_config["DB_PORT"]
DB_NAME = db_config["DB_NAME"]
DB_USER = db_config["DB_USER"]
DB_PASSWORD = db_config["DB_PW"]

# SSH Tunnel configuration
SSH_HOST = db_config["SSH_HOST"]
SSH_PORT = db_config["SSH_PORT"]
SSH_USERNAME = db_config["SSH_USER"]
SSH_PRIVATE_KEY = db_config["SSH_KEY_PATH"]

# Global variables for connection management
ssh_tunnel: Optional[object] = None
engine = None
async_session_factory = None

def get_db_url() -> str:
    """Get database URL with proper credentials."""
    return f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def init_db() -> None:
    """
    Initialize database connection and create tables.
    This should be called during application startup.
    """
    global engine, async_session_factory, ssh_tunnel
    
    try:
        if SSH_HOST:
            # Create SSH tunnel if SSH configuration is provided
            ssh_tunnel = create_ssh_tunnel()
        
        # Create engine with connection pooling settings
        engine = create_async_engine(
            get_db_url(),
            echo=True,
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300  # Recycle connections every 5 minutes
        )
        
        # Create session factory
        async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        # Create all tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            
    except Exception as e:
        await close_db()  # Ensure resources are cleaned up
        raise Exception(f"Failed to initialize database: {str(e)}")

async def close_db() -> None:
    """
    Close database connections and SSH tunnel.
    This should be called during application shutdown.
    """
    global engine, ssh_tunnel
    
    if engine:
        await engine.dispose()
        engine = None
    
    if ssh_tunnel:
        close_ssh_tunnel(ssh_tunnel)
        ssh_tunnel = None

@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    AsyncContextManager for database sessions.
    Prefer this over get_db for non-FastAPI contexts.
    """
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_db first.")
    
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting async database session.
    
    Yields:
        AsyncSession: Database session for use in FastAPI endpoints
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_db first.")
    
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 