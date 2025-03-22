"""
Database connection management.
Handles SSH tunnel and database session creation.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from ..config import get_database_config
from ..utils.ssh import create_ssh_tunnel, close_ssh_tunnel

# Global variables for managing database connection and SSH tunnel
tunnel = None
engine = None
async_session_maker = None

async def init_db():
    """
    Initializes the SSH tunnel, sets up the async database engine,
    and creates tables if they do not exist.
    
    Raises:
        Exception: If database connection or SSH tunnel setup fails
    """
    global tunnel, engine, async_session_maker
    
    try:
        # Get configuration
        config = get_database_config()

        # Create SSH tunnel using utility function
        tunnel = create_ssh_tunnel()
        local_port = tunnel.local_bind_port
        print(f"SSH tunnel established on port {local_port}")

        # Build the database URL using the tunnel's local port
        database_url = f"postgresql+asyncpg://{config['DB_USER']}:{config['DB_PW']}@127.0.0.1:{local_port}/{config['DB_NAME']}"

        # Initialize SQLAlchemy async engine and session maker
        engine = create_async_engine(database_url, echo=True)
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Automatically create tables from SQLAlchemy models
        from .models import Base  # Import here to avoid circular imports
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database engine created using the SSH tunnel.")
    except Exception as e:
        # Clean up resources if initialization fails
        await shutdown_db()
        raise Exception(f"Failed to initialize database: {str(e)}")

async def shutdown_db():
    """
    Closes the database engine and stops the SSH tunnel.
    Ensures all resources are properly cleaned up.
    """
    global tunnel, engine, async_session_maker
    
    if engine:
        try:
            await engine.dispose()
        except Exception as e:
            print(f"Error disposing engine: {str(e)}")
    
    if tunnel:
        try:
            close_ssh_tunnel(tunnel)
        except Exception as e:
            print(f"Error closing SSH tunnel: {str(e)}")
    
    # Reset global variables
    tunnel = None
    engine = None
    async_session_maker = None
    print("Database connection and SSH tunnel closed.")

async def get_db():
    """
    Dependency function to provide a database session.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Use db session here
    
    Yields:
        AsyncSession: Database session for use in API endpoints
    """
    if not async_session_maker:
        raise Exception("Database not initialized. Call init_db() first.")
        
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise 