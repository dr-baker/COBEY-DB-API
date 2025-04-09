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
6. Demonstrate API usage
"""
import asyncio
import json
import requests
from datetime import datetime, timezone, timedelta
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.db.connection import db
from src.db.queries.executor import QueryExecutor
from src.db.models import User, Session, EventLog

BASE_URL = "http://localhost:8000"

async def example_database_operations():
    """Demonstrate basic database operations with our new schema."""
    logger = get_logger("example")
    
    # Create executors for each model
    user_executor = QueryExecutor(db, User)
    session_executor = QueryExecutor(db, Session)
    event_executor = QueryExecutor(db, EventLog)
    
    # Example 1: Test database connection
    await db.execute("SELECT 1")
    logger.info("database_connection_test_passed")
    
    # Example 2: Create a user
    user_data = {
        "user_id": "test_user_1",
        "firebase_data": {"email": "test@example.com"},
        "body_data": {"height": 180, "weight": 75}
    }
    
    user = await user_executor.create(user_data)
    logger.info("user_created", user_id=user.user_id)
    
    # Example 3: Create a session
    session_id = "test_session_1"
    session_data = {
        "session_id": session_id,
        "user_id": user_data["user_id"],
        "ts_start": datetime.now(timezone.utc),
        "exercises_data": {"workout_type": "strength", "duration": 3600},
        "device_type": "iphone",
        "device_os": "ios16",
        "region": "us-west",
        "ip": "127.0.0.1",
        "app_version": "1.0.0"
    }
    
    session = await session_executor.create(session_data)
    logger.info("session_created", session_id=session.session_id)
    
    # Example 4: Log some events
    events = [
        {
            "ts": datetime.now(timezone.utc),
            "user_id": user_data["user_id"],
            "session_id": session_id,
            "event_type": "workout_started",
            "event_data": {"workout_id": "w1"},
            "event_source": "mobile_app",
            "log_level": "info",
            "app_version": "1.0.0"
        },
        {
            "ts": datetime.now(timezone.utc),
            "user_id": user_data["user_id"],
            "session_id": session_id,
            "event_type": "exercise_completed",
            "event_data": {"exercise_id": "e1", "reps": 10},
            "event_source": "mobile_app",
            "log_level": "info",
            "app_version": "1.0.0"
        }
    ]
    
    for event_data in events:
        event = await event_executor.create(event_data)
        logger.info("event_created", event_id=event.ts)
    
    logger.info("events_logged", count=len(events))
    
    # Example 5: Query data using the executor
    # Note: This is a more complex query that might need a custom method in the executor
    # For now, we'll use a direct query for this example
    user_sessions = await db.fetch("""
        SELECT s.session_id, s.ts_start, COUNT(e.event_type) as event_count
        FROM sessions s
        LEFT JOIN event_log e ON s.session_id = e.session_id
        WHERE s.user_id = $1
        GROUP BY s.session_id, s.ts_start
        ORDER BY s.ts_start DESC
    """, user_data["user_id"])
    
    logger.info("user_sessions", 
               sessions=[dict(row) for row in user_sessions])

def example_api_usage():
    """Demonstrate API usage with our endpoints."""
    logger = get_logger("example")
    
    # Example 1: Create a user via API
    user_data = {
        "user_id": "test_user_2",
        "firebase_data": {"email": "test2@example.com"},
        "body_data": {"height": 175, "weight": 70}
    }
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    if response.status_code == 201:
        user = response.json()
        logger.info("user_created_via_api", user_id=user["user_id"])
    else:
        logger.error("failed_to_create_user", error=response.text)
    
    # Example 2: Get user details
    response = requests.get(f"{BASE_URL}/users/{user_data['user_id']}")
    if response.status_code == 200:
        user = response.json()
        logger.info("user_retrieved", user=user)
    else:
        logger.error("failed_to_get_user", error=response.text)
    
    # Example 3: Create a recording
    recording_data = {
        "recording_id": "test_recording_1",
        "recording_link": "https://example.com/recording.mp4",
        "recording_type": "video",
        "user_id": user_data["user_id"],
        "created_session_id": "test_session_2"
    }
    response = requests.post(f"{BASE_URL}/recordings/", json=recording_data)
    if response.status_code == 201:
        recording = response.json()
        logger.info("recording_created", recording_id=recording["recording_id"])
    else:
        logger.error("failed_to_create_recording", error=response.text)
    
    # Example 4: List recordings with filters
    response = requests.get(
        f"{BASE_URL}/recordings/",
        params={
            "user_id": user_data["user_id"],
            "recording_type": "video",
            "page": 1,
            "size": 10
        }
    )
    if response.status_code == 200:
        recordings = response.json()
        logger.info("recordings_listed", count=len(recordings))
    else:
        logger.error("failed_to_list_recordings", error=response.text)
    
    # Example 5: Create an algorithm
    algo_data = {
        "algo_id": "test_algo_1",
        "recording_type": "video",
        "location": "cloud",
        "version": "1.0.0"
    }
    response = requests.post(f"{BASE_URL}/algos/", json=algo_data)
    if response.status_code == 201:
        algo = response.json()
        logger.info("algorithm_created", algo_id=algo["algo_id"])
    else:
        logger.error("failed_to_create_algorithm", error=response.text)
    
    # Example 6: Log an event
    event_data = {
        "user_id": user_data["user_id"],
        "session_id": "test_session_2",
        "event_type": "recording_created",
        "event_data": {"recording_id": recording_data["recording_id"]},
        "event_source": "api",
        "log_level": "info",
        "ts": datetime.now(timezone.utc).isoformat()
    }
    response = requests.post(f"{BASE_URL}/events/", json=event_data)
    if response.status_code == 201:
        event = response.json()
        logger.info("event_logged", event_id=event["event_id"])
    else:
        logger.error("failed_to_log_event", error=response.text)
    
    # Example 7: List events with time range
    start_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    end_time = datetime.now(timezone.utc).isoformat()
    response = requests.get(
        f"{BASE_URL}/events/",
        params={
            "user_id": user_data["user_id"],
            "start_time": start_time,
            "end_time": end_time,
            "page": 1,
            "size": 10
        }
    )
    if response.status_code == 200:
        events = response.json()
        logger.info("events_listed", count=len(events))
    else:
        logger.error("failed_to_list_events", error=response.text)

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
        
        # 5. Run API examples
        print("\n=== Running API Examples ===")
        example_api_usage()
        
    except Exception as e:
        logger.error("example_failed", error=str(e))
        raise
    finally:
        # 6. Cleanup
        await db.disconnect()
        logger.info("example_completed")

if __name__ == "__main__":
    asyncio.run(main()) 