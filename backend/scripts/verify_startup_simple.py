import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

def check_startup():
    print("--- CHECKING BACKEND STARTUP ---")
    try:
        from app.main import app
        print("SUCCESS: 'app.main' imported successfully.")
        print(f"App Title: {app.title}")
    except ImportError as e:
        print(f"FAILURE: Import Error: {e}")
    except Exception as e:
        print(f"FAILURE: Startup Error: {e}")

if __name__ == "__main__":
    check_startup()
