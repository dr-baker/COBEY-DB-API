"""
Example usage of the Workout Session API.
This script demonstrates how to interact with the API endpoints
in a production environment.
"""
import sys
import os
import httpx
import json
from datetime import datetime
from typing import Dict, Any

# API configuration
API_BASE_URL = "http://localhost:8000"  # Change this to your production API URL
TIMEOUT = 30.0  # Timeout in seconds

class WorkoutSessionClient:
    """Client for interacting with the Workout Session API."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
    
    def check_api_status(self) -> Dict[str, Any]:
        """Check if the API is running."""
        response = self.client.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()
    
    def test_database(self) -> Dict[str, Any]:
        """Test the database connection."""
        response = self.client.get(f"{self.base_url}/test-db")
        response.raise_for_status()
        return response.json()
    
    def save_workout_session(self, user_id: int, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a new workout session.
        
        Args:
            user_id: ID of the user
            workout_data: Workout session details
        """
        session_data = {
            "user_id": user_id,
            "session_data": json.dumps(workout_data)
        }
        response = self.client.post(
            f"{self.base_url}/api/sessions/save-session",
            json=session_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def query_sessions(self) -> Dict[str, Any]:
        """Query all workout sessions."""
        response = self.client.get(f"{self.base_url}/long-query")
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close the client session."""
        self.client.close()

def main():
    """Main execution function."""
    client = WorkoutSessionClient(API_BASE_URL, TIMEOUT)
    
    try:
        # 1. Check API Status
        print("\n=== Testing API Status ===")
        status = client.check_api_status()
        print(f"API Status: {status}")
        
        # 2. Test Database Connection
        print("\n=== Testing Database Connection ===")
        db_status = client.test_database()
        print(f"Database Status: {db_status}")
        
        # 3. Save a Workout Session
        print("\n=== Saving a Workout Session ===")
        workout_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "workout_type": "strength",
            "exercises": [
                {
                    "name": "Bench Press",
                    "sets": 3,
                    "reps": 10,
                    "weight": 225,
                    "notes": "Felt strong today"
                },
                {
                    "name": "Squats",
                    "sets": 4,
                    "reps": 8,
                    "weight": 275,
                    "notes": "Focused on form"
                }
            ],
            "duration": "60 minutes",
            "notes": "Great session, hit all planned exercises",
            "mood": "Energetic",
            "energy_level": 8
        }
        
        result = client.save_workout_session(1, workout_data)
        print(f"Save Session Result: {result}")
        
        # 4. Query Sessions
        print("\n=== Querying Session Data ===")
        sessions = client.query_sessions()
        print(f"Query Result: {sessions}")
        
    except httpx.ConnectError:
        print(f"\nError: Could not connect to API at {API_BASE_URL}")
        print("Make sure the API server is running and the URL is correct.")
        sys.exit(1)
    except httpx.TimeoutException:
        print("\nError: Request timed out. The server might be slow or unresponsive.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main() 