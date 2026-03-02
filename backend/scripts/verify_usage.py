import asyncio
import os
import sys

# Add the backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.core.database import init_db
from app.services import security_service
from app.core.config import settings

async def verify_usage():
    print("--- NEXUS USAGE METADATA VERIFICATION ---")
    await init_db()
    
    user_id = "test_usage_user"
    
    print(f"\n[1] Check Initial Usage for user: {user_id}")
    stats_before = await security_service.get_usage_stats(user_id)
    print(f"Before: Usage={stats_before.current_usage}, Remaining={stats_before.remaining}")
    
    # Simulate a chat interaction (Validate Access -> increments +1)
    print("\n[2] Simulating 1 interaction...")
    try:
        await security_service.validate_user_access(user_id)
        print("Interaction validated.")
    except Exception as e:
        print(f"Blocked: {e}")
        
    # Check Updated Stats
    print("\n[3] Check Updated Usage")
    stats_after = await security_service.get_usage_stats(user_id)
    print(f"After: Usage={stats_after.current_usage}, Remaining={stats_after.remaining}")
    
    if stats_after.current_usage == stats_before.current_usage + 1:
        print("SUCCESS: Usage incremented correctly.")
    else:
        print("FAILURE: Usage did not increment.")

    if stats_after.remaining == settings.MAX_REQUESTS_LIMIT - stats_after.current_usage:
        print("SUCCESS: Remaining count is correct.")
    else:
        print("FAILURE: Remaining count incorrect.")


if __name__ == "__main__":
    asyncio.run(verify_usage())
