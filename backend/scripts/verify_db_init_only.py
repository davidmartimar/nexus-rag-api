import asyncio
import os
from app.core.database import init_db
from app.core.config import settings

async def test_db_init():
    print(f"Testing direct DB init at: {settings.DB_PATH}")
    if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH) # Start fresh
        
    await init_db()
    
    if os.path.exists(settings.DB_PATH):
        print("SUCCESS: Database created.")
        # Optional: check tables
        import aiosqlite
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                 tables = await cursor.fetchall()
                 print(f"Tables found: {[t[0] for t in tables]}")
    else:
        print("FAILURE: Database not created.")

if __name__ == "__main__":
    asyncio.run(test_db_init())
