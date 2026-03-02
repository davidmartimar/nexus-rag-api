import os
import sys

# Add the backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

def verify_config():
    print("--- NEXUS CONFIGURATION VERIFICATION ---")
    
    # 1. Test Valid Config (assuming .env is loaded or env vars set by user/shell)
    # We need to manually load dotenv here or ensure it's loaded by the module if we want to test "success" case logic.
    # The module `app.core.config` calls load_dotenv().
    
    try:
        from app.core.config import Settings
        
        # We manually instantiate to test.
        # But `app.core.config` instantiates `settings = Settings()` at module level, so import might have already failed if env is empty!
        # If the import succeeded, likely secrets are there.
        
        from app.core.config import settings
        print(f"SUCCESS: Config loaded.")
        print(f"DB_PATH: {settings.DB_PATH}")
        print(f"DATABASE_URL: {settings.DATABASE_URL}")
        
    except ValueError as e:
        print(f"CONFIG VALIDATION FAILED (Expected if secrets missing): {e}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 2. Test Missing Secrets (Simulate Production Fail)
    print("\n[Testing Missing Secrets Logic]")
    # Save current
    orig_secret = os.environ.get("SECRET_KEY")
    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]
        
    try:
        # Re-import or re-instantiate
        # Since module is cached, we just re-instantiate the class
        from app.core.config import Settings
        s = Settings()
        print("FAILURE: Settings did NOT raise ValueError with missing SECRET_KEY")
    except ValueError as e:
        print(f"SUCCESS: Caught expected error: {e}")
    except Exception as e:
        print(f"ERROR: Caught unexpected exception: {e}")
    finally:
        # Restore
        if orig_secret:
            os.environ["SECRET_KEY"] = orig_secret

if __name__ == "__main__":
    verify_config()
