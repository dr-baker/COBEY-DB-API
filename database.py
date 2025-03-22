import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# SSH and Database connection settings
SSH_HOST = os.getenv("SSH_HOST", "your_ssh_host_here")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "your_ssh_user_here")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", "your_ssh_key_path_here")

DB_HOST = os.getenv("DB_HOST", "your_db_host_here")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "your_db_user_here")
DB_PW = os.getenv("DB_PW", "your_db_password_here")
DB_NAME = os.getenv("DB_NAME", "your_db_name_here")

# Global variables for managing database connection and SSH tunnel
tunnel = None
engine = None
async_session_maker = None

async def init_db():
    """
    Initializes the SSH tunnel, sets up the async database engine,
    and creates tables if they do not exist.
    """
    global tunnel, engine, async_session_maker

    # Create SSH tunnel to DB host
    tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_pkey=SSH_KEY_PATH,
        remote_bind_address=(DB_HOST, DB_PORT)
    )
    tunnel.start()

    # Build the new database URL using the tunnel's local port
    local_port = tunnel.local_bind_port
    print(f"SSH tunnel established on port {local_port}")
    database_url = f"postgresql+asyncpg://{DB_USER}:{DB_PW}@127.0.0.1:{local_port}/{DB_NAME}"

    # Initialize SQLAlchemy async engine and session maker
    engine = create_async_engine(database_url, echo=True)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Automatically create tables from SQLAlchemy models
    from models import Base  # Import here to avoid circular imports
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database engine created using the SSH tunnel.")

async def shutdown_db():
    """
    Closes the database engine and stops the SSH tunnel.
    """
    global tunnel, engine
    if engine:
        await engine.dispose()
    if tunnel:
        tunnel.stop()
    print("SSH tunnel closed and database engine disposed.")

async def get_db():
    """
    Dependency function to provide a database session.
    """
    async with async_session_maker() as session:
        yield session
