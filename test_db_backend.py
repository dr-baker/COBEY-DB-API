import requests
from requests.exceptions import RequestException, Timeout

BASE_URL = "http://127.0.0.1:8000"

# Test root endpoint
def test_root():
    try:
        response = requests.get(f"{BASE_URL}/")
        response.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)
        print("Root Response:", response.json())
    except Timeout:
        print("Error: The request timed out while trying to reach the server.")
    except RequestException as e:
        print(f"Error: There was an issue with the request - {e}")
    except ValueError:
        print("Error: Could not decode the response JSON.")

# Test database connection
def test_db():
    try:
        response = requests.get(f"{BASE_URL}/test-db")
        response.raise_for_status()
        print("DB Test Response:", response.json())
    except Timeout:
        print("Error: The request timed out while trying to reach the server.")
    except RequestException as e:
        print(f"Error: There was an issue with the request - {e}")
    except ValueError:
        print("Error: Could not decode the response JSON.")

# Test saving session data
def test_save_session():
    payload = {"user_id": 1, "session_data": "Sample session data"}
    try:
        response = requests.post(f"{BASE_URL}/save-session", json=payload)
        response.raise_for_status()
        print("Save Session Response:", response.json())
    except Timeout:
        print("Error: The request timed out while trying to reach the server.")
    except RequestException as e:
        print(f"Error: There was an issue with the request - {e}")
    except ValueError:
        print("Error: Could not decode the response JSON.")

if __name__ == "__main__":
    print("Test root.")
    test_root()
    print("Test db.")
    test_db()
    print("Test save session.")
    test_save_session()
