import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.schemas import ChatRequest

def test_chat_schema():
    print("--- TESTING CHAT SCHEMA ---")
    
    # Test 1: Full payload
    print("\n[1] Testing Full Payload (message + collection_name)")
    payload1 = {
        "message": "Hello Nexus",
        "collection_name": "custom_slot"
    }
    req1 = ChatRequest(**payload1)
    print(f"Result: message='{req1.message}', collection_name='{req1.collection_name}'")
    
    if req1.collection_name == "custom_slot":
        print("SUCCESS: collection_name accepted.")
    else:
        print(f"FAILURE: Expected 'custom_slot', got '{req1.collection_name}'")
        
    # Test 2: Default payload (Legacy/Fallback)
    print("\n[2] Testing Default Payload (message only)")
    payload2 = {
        "message": "Hello Nexus"
    }
    req2 = ChatRequest(**payload2)
    print(f"Result: message='{req2.message}', collection_name='{req2.collection_name}'")
    
    if req2.collection_name == "nexus_slot_1":
        print("SUCCESS: Default collection_name applied.")
    else:
        print(f"FAILURE: Expected 'nexus_slot_1', got '{req2.collection_name}'")

if __name__ == "__main__":
    test_chat_schema()
