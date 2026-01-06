import asyncio
from app.main import lifespan
from fastapi import FastAPI
from app.core.config import settings
import os

async def test_startup():
    print(f"Testing DB initialization at: {settings.DB_PATH}")
    
    # Create a dummy app
    app = FastAPI()
    
    # Manually trigger the lifespan context manager
    async with lifespan(app):
        print("Lifespan startup complete.")
        
    # Check if DB file exists
    if os.path.exists(settings.DB_PATH):
        print("SUCCESS: Database file found.")
    else:
        print("FAILURE: Database file NOT found.")
        
if __name__ == "__main__":
    asyncio.run(test_startup())
