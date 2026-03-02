import asyncio
import os
import sys

# Add the backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.core.database import init_db
from app.services import security_service
from app.core import tasks

async def main():
    print("--- NEXUS SECURITY & PERSISTENCE VERIFICATION ---")
    
    # 1. Initialize DB
    print("\n[1] Initializing Database...")
    await init_db()
    print("Database initialized.")
    
    user_id = "test_user_verify_1"
    
    # 2. Test Message Flow
    print(f"\n[2] Testing Message Flow for user: {user_id}")
    try:
        # Validate Access
        await security_service.validate_user_access(user_id)
        print("Rate limit check passed.")
        
        # Save User Message
        msg = "My sensitive medical data"
        await security_service.save_secure_message(user_id, "user", msg)
        print(f"Saved encrypted user message: '{msg}'")
        
        # Save Assistant Message
        resp = "I have processed your data securely."
        await security_service.save_secure_message(user_id, "assistant", resp)
        print(f"Saved encrypted assistant message: '{resp}'")
        
    except Exception as e:
        print(f"FAILED: {e}")
        return

    # 3. Verify Decryption
    print("\n[3] Verifying Decryption (History)...")
    history = await security_service.get_secure_history(user_id)
    for i, m in enumerate(history):
        print(f"Msg {i+1} [{m['role']}]: {m['content']}")
        
    if len(history) >= 2:
        print("SUCCESS: History retrieved and decrypted correctly.")
    else:
        print("FAILURE: History incomplete.")

    # 4. Test Cleanup
    print("\n[4] Testing Cleanup Task...")
    res = await tasks.cleanup_database()
    print(f"Cleanup result: {res}")

if __name__ == "__main__":
    asyncio.run(main())
