"""Example usage of core backend features.

This example demonstrates basic database operations and API usage with our schema. Before running,
ensure all database migrations have been applied using:

    python scripts/migrate.py

The example will:
1. Test database connectivity
2. Create/update a test user
3. Create a new session
4. Log some example events
5. Query session data
6. Demonstrate API usage with explicit Pydantic models
"""
import asyncio
import json
import requests
from datetime import datetime, timezone, timedelta
import uuid
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.db.connection import db
from src.api.utils.responses import serialize_for_json
# Import explicit models
from src.models import (
    User, UserCreate, UserUpdate,
    Recording, RecordingCreate,
    Session, SessionCreate,
    Algo, AlgoCreate,
    EventLog, EventLogCreate
)

BASE_URL = "http://localhost:8000"

async def example_database_operations():
    """Demonstrate basic database operations with our new schema."""
    logger = get_logger("example")
    
    async with db.transaction() as conn:
        # Example 1: Test database connection
        await conn.execute("SELECT 1")
        logger.info("database_connection_test_passed")
        
        # Example 2: Create a user - Use json.dumps for JSONB columns
        user_data = {
            "user_id": "test_user_1",
            "firebase_data": {"email": "test@example.com"},
            "body_data": {"height": 180, "weight": 75}
        }
        
        await conn.execute("""
            INSERT INTO users (user_id, firebase_data, body_data)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE 
            SET firebase_data = $2, body_data = $3
        """, user_data["user_id"], json.dumps(user_data["firebase_data"]), 
            json.dumps(user_data["body_data"]))
        
        logger.info("user_created", user_id=user_data["user_id"])
        
        # Example 3: Create a session - Use json.dumps for JSONB columns
        session_id = "test_session_1"
        session_data = {
            "session_id": session_id,
            "user_id": user_data["user_id"],
            "ts_start": datetime.now(timezone.utc),
            "exercises_data": {"workout_type": "strength", "duration": 3600}, # This is JSONB
            "device_type": "iphone",
            "device_os": "ios16",
            "region": "us-west",
            "ip": "127.0.0.1",
            "app_version": "1.0.0"
        }
        
        await conn.execute("""
            INSERT INTO sessions 
            (session_id, user_id, ts_start, exercises_data, device_type, 
             device_os, region, ip, app_version)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (session_id) DO NOTHING
        """, session_data["session_id"], session_data["user_id"], 
            session_data["ts_start"], json.dumps(session_data["exercises_data"]), # Use json.dumps
            session_data["device_type"], session_data["device_os"],
            session_data["region"], session_data["ip"], 
            session_data["app_version"])
            
        logger.info("session_created", session_id=session_id)
        
        # Example 4: Log some events - Use json.dumps for JSONB columns
        events = [
            {
                "ts": datetime.now(timezone.utc),
                "user_id": user_data["user_id"],
                "session_id": session_id,
                "event_type": "workout_started",
                "event_data": {"workout_id": "w1"}, # This is JSONB
                "event_source": "mobile_app",
                "log_level": "info",
                "app_version": "1.0.0"
            },
            {
                "ts": datetime.now(timezone.utc),
                "user_id": user_data["user_id"],
                "session_id": session_id,
                "event_type": "exercise_completed",
                "event_data": {"exercise_id": "e1", "reps": 10}, # This is JSONB
                "event_source": "mobile_app",
                "log_level": "info",
                "app_version": "1.0.0"
            }
        ]
        
        for event in events:
            await conn.execute("""
                INSERT INTO event_log 
                (ts, user_id, session_id, event_type, event_data, 
                 event_source, log_level, app_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, event["ts"], event["user_id"], event["session_id"],
                event["event_type"], json.dumps(event["event_data"]), # Use json.dumps
                event["event_source"], event["log_level"], event["app_version"])
        
        logger.info("events_logged", count=len(events))
        
        # Example 5: Query data (no JSONB inserts here)
        user_sessions = await conn.fetch("""
            SELECT s.session_id, s.ts_start, COUNT(e.event_type) as event_count
            FROM sessions s
            LEFT JOIN event_log e ON s.session_id = e.session_id
            WHERE s.user_id = $1
            GROUP BY s.session_id, s.ts_start
            ORDER BY s.ts_start DESC
        """, user_data["user_id"])
        
        # Log results - ensure datetimes from DB are handled if needed (asyncpg usually does this)
        # The serialize_for_json in the logger call might be helpful for display
        logger.info("user_sessions", 
                   sessions=[serialize_for_json(dict(row)) for row in user_sessions])

async def ensure_user_exists(user_id, firebase_data, body_data):
    """Ensure a user exists in the database - Use json.dumps for JSONB."""
    logger = get_logger("example")
    try:
        async with db.transaction() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, firebase_data, body_data)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE 
                SET firebase_data = $2, body_data = $3
            """, user_id, json.dumps(firebase_data), json.dumps(body_data)) # Use json.dumps
        return True
    except Exception as e:
        logger.error("failed_to_ensure_user_exists", error=str(e))
        return False

def example_api_usage():
    """Demonstrate API usage - Use serialize_for_json for request bodies."""
    logger = get_logger("example")
    
    # Example 1: Create a user via API
    user_create = UserCreate(
        user_id="test_user_2",
        firebase_data={"email": "test2@example.com"},
        body_data={"height": 175, "weight": 70}
    )
    response = requests.post(
        f"{BASE_URL}/users/", 
        json=serialize_for_json(user_create) # Correct for requests
    )
    if response.status_code == 201:
        user = User(**response.json())
        logger.info("user_created_via_api", user_id=user.user_id)
    elif response.status_code == 400 and "duplicate key" in response.text:
        logger.warning("user_already_exists_via_api", user_id=user_create.user_id)
    else:
        logger.error("failed_to_create_user", error=response.text)
    
    # Example 2: Get user details
    response = requests.get(f"{BASE_URL}/users/{user_create.user_id}")
    if response.status_code == 200:
        user = User(**response.json())
        logger.info("user_retrieved", user_id=user.user_id)
    else:
        logger.error("failed_to_get_user", error=response.text)
    
    # Example 3: Create a recording via API
    recording_create = RecordingCreate(
        recording_id=f"test_recording_{uuid.uuid4()}",
        recording_link="https://example.com/recording.mp4",
        recording_type="video",
        user_id=user_create.user_id,
        created_session_id="test_session_2"
    )
    response = requests.post(
        f"{BASE_URL}/recordings/", 
        json=serialize_for_json(recording_create) # Correct for requests
    )
    if response.status_code == 201:
        recording = Recording(**response.json())
        logger.info("recording_created", recording_id=recording.recording_id)
    else:
        logger.error("failed_to_create_recording", error=response.text)
    
    # Example 4: Get recordings
    response = requests.get(f"{BASE_URL}/recordings/")
    if response.status_code == 200:
        recordings = [Recording(**rec) for rec in response.json()]
        logger.info("recordings_retrieved", count=len(recordings))
    else:
        logger.error("failed_to_get_recordings", error=response.text)
    
    # Example 5: Create a session via API
    session_create = SessionCreate(
        session_id=f"test_session_{uuid.uuid4()}",
        user_id=user_create.user_id,
        ts_start=datetime.now(timezone.utc),
        exercises_data={"workout_type": "strength", "duration": 3600},
        device_type="iphone",
        device_os="ios16",
        region="us-west",
        ip="127.0.0.1",
        app_version="1.0.0"
    )
    response = requests.post(
        f"{BASE_URL}/sessions/", 
        json=serialize_for_json(session_create)
    )
    if response.status_code == 201:
        session = Session(**response.json())
        logger.info("session_created", session_id=session.session_id)
    else:
        logger.error("failed_to_create_session", error=response.text)
    
    # Example 6: Log an event via API
    event_create = EventLogCreate(
        ts=datetime.now(timezone.utc),
        user_id=user_create.user_id,
        session_id=session_create.session_id,
        event_type="workout_started",
        event_data={"workout_id": "w1"},
        event_source="mobile_app",
        log_level="info",
        app_version="1.0.0"
    )
    response = requests.post(
        f"{BASE_URL}/events/", 
        json=serialize_for_json(event_create)
    )
    if response.status_code == 201:
        event = EventLog(**response.json())
        logger.info("event_logged", event_id=event.event_id)
    else:
        logger.error("failed_to_log_event", error=response.text)
    
    # Example 7: Get events
    response = requests.get(f"{BASE_URL}/events/")
    if response.status_code == 200:
        events = [EventLog(**evt) for evt in response.json()]
        logger.info("events_retrieved", count=len(events))
    else:
        logger.error("failed_to_get_events", error=response.text)

async def main():
    """Run the example."""
    # 1. Load and display configuration
    settings = get_settings()
    print("\n=== Configuration ===")
    print(f"Database: {settings.DB_NAME} on {settings.DB_HOST}")
    print(f"SSH Tunnel: {settings.SSH_USER}@{settings.SSH_HOST}")
    
    # 2. Setup logging
    setup_logging()
    logger = get_logger("example")
    logger.info("example_started", debug_mode=settings.DEBUG)
    
    try:
        # 3. Connect to database
        print("\n=== Connecting to Database ===")
        await db.connect()
        
        # 4. Run database examples
        print("\n=== Running Database Examples ===")
        await example_database_operations()
        
        # 5. Ensure test_user_2 exists before API examples
        print("\n=== Ensuring Test User Exists ===")
        await ensure_user_exists(
            "test_user_2", 
            {"email": "test2@example.com"}, 
            {"height": 175, "weight": 70}
        )
        
        # 6. Run API examples
        print("\n=== Running API Examples ===")
        example_api_usage()
        
    except Exception as e:
        logger.error("example_failed", error=str(e))
        raise
    finally:
        # 7. Cleanup
        await db.disconnect()
        logger.info("example_completed")

if __name__ == "__main__":
    asyncio.run(main()) 