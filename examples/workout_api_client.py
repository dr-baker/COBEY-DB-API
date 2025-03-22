"""
Example implementation of a Workout API client.
Demonstrates how to interact with the API in a production environment.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
import httpx
import json
import sys
from dataclasses import dataclass

@dataclass
class Exercise:
    """Represents a single exercise in a workout session."""
    name: str
    sets: int
    reps: int
    weight: float
    notes: Optional[str] = None

@dataclass
class WorkoutSession:
    """Represents a complete workout session."""
    date: str
    workout_type: str
    exercises: List[Exercise]
    duration: str
    notes: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None

class WorkoutAPIClient:
    """Client for interacting with the Workout Session API."""

    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        verify_ssl: bool = True
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(
            timeout=timeout,
            verify=verify_ssl,
            headers={"Content-Type": "application/json"}
        )

    def check_health(self) -> Dict[str, Any]:
        """
        Check if the API is running and healthy.

        Returns:
            Dict containing API status information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        response = self.client.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()

    def test_database(self) -> Dict[str, Any]:
        """
        Test the database connection.

        Returns:
            Dict containing database connection status

        Raises:
            httpx.HTTPError: If the database connection fails
        """
        response = self.client.get(f"{self.base_url}/test-db")
        response.raise_for_status()
        return response.json()

    def save_session(self, user_id: int, session: WorkoutSession) -> Dict[str, Any]:
        """
        Save a workout session.

        Args:
            user_id: ID of the user
            session: WorkoutSession object containing workout details

        Returns:
            Dict containing the saved session information

        Raises:
            httpx.HTTPError: If the save operation fails
        """
        session_data = {
            "user_id": user_id,
            "session_data": json.dumps({
                "date": session.date,
                "workout_type": session.workout_type,
                "exercises": [vars(ex) for ex in session.exercises],
                "duration": session.duration,
                "notes": session.notes,
                "mood": session.mood,
                "energy_level": session.energy_level
            })
        }

        response = self.client.post(
            f"{self.base_url}/api/sessions/save-session",
            json=session_data
        )
        response.raise_for_status()
        return response.json()

    def query_sessions(self) -> Dict[str, Any]:
        """
        Query all workout sessions.

        Returns:
            Dict containing the query results

        Raises:
            httpx.HTTPError: If the query fails
        """
        response = self.client.get(f"{self.base_url}/long-query")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the client session."""
        self.client.close()

def main():
    """Example usage of the WorkoutAPIClient."""
    # Initialize client
    client = WorkoutAPIClient(
        base_url="http://localhost:8000",
        timeout=30.0
    )

    try:
        # 1. Check API health
        print("\n=== Checking API Health ===")
        health = client.check_health()
        print(f"API Health Status: {health}")

        # 2. Test database connection
        print("\n=== Testing Database Connection ===")
        db_status = client.test_database()
        print(f"Database Status: {db_status}")

        # 3. Create and save a workout session
        print("\n=== Saving Workout Session ===")
        workout = WorkoutSession(
            date=datetime.now().strftime("%Y-%m-%d"),
            workout_type="strength",
            exercises=[
                Exercise(
                    name="Bench Press",
                    sets=3,
                    reps=10,
                    weight=225.0,
                    notes="Felt strong today"
                ),
                Exercise(
                    name="Squats",
                    sets=4,
                    reps=8,
                    weight=275.0,
                    notes="Focused on form"
                )
            ],
            duration="60 minutes",
            notes="Great session overall",
            mood="Energetic",
            energy_level=8
        )

        result = client.save_session(user_id=1, session=workout)
        print(f"Save Session Result: {result}")

        # 4. Query all sessions
        print("\n=== Querying Sessions ===")
        sessions = client.query_sessions()
        print(f"Found {len(sessions.get('data', []))} sessions")

    except httpx.ConnectError:
        print(f"\nError: Could not connect to API at {client.base_url}")
        print("Make sure the API server is running and the URL is correct.")
        sys.exit(1)
    except httpx.TimeoutException:
        print("\nError: Request timed out. The server might be slow or unresponsive.")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"\nHTTP Error {e.response.status_code}: {e.response.json()}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main() 