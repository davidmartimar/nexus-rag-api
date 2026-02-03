import requests
import time
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_KEY = os.getenv("NEXUS_API_KEY", "sk-nexus-1234567890abcdef")
HEADERS = {"X-NEXUS-KEY": API_KEY}

def get_config():
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/config", headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        print(f"Error getting config: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")
    return None

def update_config(config):
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/config", json=config, headers=HEADERS)
        if response.status_code == 200:
            return True
        print(f"Error updating config: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")
    return False

def test_persistence():
    print("--- Starting Persistence Test ---")
    
    # 1. Get initial config
    initial_config = get_config()
    print(f"Initial Config: {initial_config}")
    
    if not initial_config:
        print("Failed to get initial config. Aborting.")
        return

    # 2. Modify config
    test_name = f"Test Brain {int(time.time())}"
    new_config = initial_config.copy()
    new_config["nexus_slot_1"] = test_name
    
    print(f"Attempting to rename 'nexus_slot_1' to '{test_name}'...")
    if update_config(new_config):
        print("Update request successful.")
    else:
        print("Update request failed. Aborting.")
        return

    # 3. Verify modification immediately
    updated_config = get_config()
    print(f"Config after update: {updated_config}")
    
    if updated_config.get("nexus_slot_1") == test_name:
        print("SUCCESS: Config updated in memory/file.")
    else:
        print("FAILURE: Config did not update immediately.")

    print("\nNOTE: To fully verify persistence, restart the backend container and run get_config() again.")
    print("--- Test Complete ---")

if __name__ == "__main__":
    test_persistence()
