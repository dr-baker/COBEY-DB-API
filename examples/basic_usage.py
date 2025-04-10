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
    """Demonstrate API usage with our endpoints using explicit Pydantic models.
    
    This example demonstrates:
    1. User management (create, update, get)
    2. Recording management (create, list with filters)
    3. Algorithm management (create)
    4. Event logging (create)
    5. Error handling and logging
    6. Response structure handling
    """
    logger = get_logger("example")
    
    # Example 1: User Management
    user_id = "test_user_2"
    user_data = {
        "user_id": user_id,
        "firebase_data": {"email": "test2@example.com"},
        "body_data": {"height": 175, "weight": 70}
    }
    
    # 1a. Check if user exists
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        # 1b. User exists, update it with PUT (complete replacement)
        user_create = UserCreate(**user_data)
        response = requests.put(
            f"{BASE_URL}/users/{user_id}",
            json=user_create.model_dump()
        )
        if response.status_code == 200:
            user_data = response.json()["data"]
            user = User(**user_data)
            logger.info("user_updated", user_id=user.user_id)
        else:
            logger.error("failed_to_update_user", error=response.text)
    else:
        # 1c. User doesn't exist, create it
        user_create = UserCreate(**user_data)
        response = requests.post(
            f"{BASE_URL}/users/",
            json=user_create.model_dump()
        )
        if response.status_code == 201:
            user_data = response.json()["data"]
            user = User(**user_data)
            logger.info("user_created_via_api", user_id=user.user_id)
        else:
            logger.error("failed_to_create_user", error=response.text)
    
    # 1d. Get user details
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        user_data = response.json()["data"]
        user = User(**user_data)
        logger.info("user_retrieved", user_id=user.user_id)
    else:
        logger.error("failed_to_get_user", error=response.text)
    
    # Create a recording
    recording_create = RecordingCreate(
        recording_id=f"test_recording_{uuid.uuid4()}",
        recording_link="https://example.com/recording.mp4",
        recording_type="video",
        user_id=user_id,
        created_session_id="test_session_1"
    )
    
    response = requests.post(
        f"{BASE_URL}/recordings/",
        json=recording_create.model_dump()
    )
    response.raise_for_status()
    recording = Recording(**response.json()["data"])
    logger.info("recording_created", 
                recording_id=recording.recording_id,
                recording_type=recording.recording_type,
                user_id=recording.user_id)
    
    # List recordings with simple filters
    response = requests.get(
        f"{BASE_URL}/recordings/",
        params={
            "page": 1,
            "size": 10,
            "user_id": user_id,
            "recording_type": "video"
        }
    )
    response.raise_for_status()
    recordings = [Recording(**item) for item in response.json()["data"]["items"]]
    logger.info("recordings_listed", 
                count=len(recordings),
                user_id=user_id,
                recording_type="video")
    
    # Example 3: Algorithm Management
    # 3a. Create an algorithm
    algo_create = AlgoCreate(
        algo_id=f"test_algo_{uuid.uuid4()}",  # Make ID unique
        recording_type="video",
        user_id=user_id,
        created_session_id="test_session_2",
        location="us-west-2",  # Required field
        version="1.0.0"  # Required field
    )
    response = requests.post(
        f"{BASE_URL}/algos/",
        json=algo_create.model_dump()
    )
    if response.status_code == 201:
        algo_data = response.json()["data"]
        algo = Algo(**algo_data)
        logger.info("algo_created", algo_id=algo.algo_id)
    else:
        logger.error("failed_to_create_algo", error=response.text)
    
    # Example 4: Event Logging
    # 4a. Create an event
    # event_create = EventLogCreate(
    #     # event_id is auto-generated by the database
    #     ts=datetime.now(timezone.utc),
    #     user_id=user_id,
    #     session_id="test_session_2",
    #     event_type="workout_started",
    #     event_data={"workout_id": "w1"},
    #     event_source="mobile_app",
    #     log_level="info",
    #     app_version="1.0.0"
    # )
    # response = requests.post(
    #     f"{BASE_URL}/events/",
    #     json=event_create.model_dump(mode='json')
    # )
    # if response.status_code == 201:
    #     event_data = response.json()["data"]
    #     event = EventLog(**event_data)
    #     logger.info("event_created", event_id=event.event_id)
    # else:
    #     logger.error("failed_to_create_event", error=response.text)

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