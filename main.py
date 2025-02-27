import os
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()
# Read configuration from environment variables
SSH_HOST = os.getenv("SSH_HOST", "your_ssh_host_here")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "your_ssh_user_here")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", "your_ssh_key_path_here")

DB_HOST = os.getenv("DB_HOST", "your_db_host_here")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "your_db_user_here")
DB_PW = os.getenv("DB_PW", "your_db_password_here")
DB_NAME = os.getenv("DB_NAME", "your_db_name_here")

# Global variables for the tunnel, engine, and session maker
tunnel = None
engine = None
async_session_maker = None

app = FastAPI()

# Dependency to get DB session
async def get_db():
    async with async_session_maker() as session:
        yield session

# Data model
class SessionData(BaseModel):
    user_id: int
    session_data: str

@app.on_event("startup")
async def startup_event():
    global tunnel, engine, async_session_maker

    # Create SSH tunnel
    tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_pkey=SSH_KEY_PATH,
        remote_bind_address=(DB_HOST, DB_PORT)
    )
    tunnel.start()  # Establish the tunnel

    # Build the new database URL using the local bind port of the tunnel
    local_port = tunnel.local_bind_port
    new_database_url = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PW}@127.0.0.1:{local_port}/{DB_NAME}"
    )

    # Create async engine and session maker with the new URL
    engine = create_async_engine(new_database_url, echo=True)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    print(f"SSH tunnel established on port {local_port}")
    print("Database engine created using the SSH tunnel.")

@app.on_event("shutdown")
async def shutdown_event():
    global tunnel, engine
    if engine:
        await engine.dispose()
    if tunnel:
        tunnel.stop()
    print("SSH tunnel closed and database engine disposed.")

@app.post("/save-session")
async def save_session(session: SessionData, db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(
            text("INSERT INTO sessions (user_id, data) VALUES (:user_id, :session_data)"),
            {"user_id": session.user_id, "session_data": session.session_data},
        )
        await db.commit()
        return {"message": "Session saved."}
    except Exception as e:
        await db.rollback()
        return {"message": f"Failed to save session: {e}"}

@app.get("/")
async def root():
    return {"message": "FastAPI backend is running"}

@app.get("/test-db")
async def test_db(session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(text("SELECT 65+2^2"))
        return {"message": "Database connection successful", "result": result.scalar()}
    except Exception as e:
        return {"error": str(e)}
