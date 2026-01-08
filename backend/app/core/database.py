import aiosqlite
import logging
import os
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = settings.DB_PATH

async def get_db_connection():
    """Returns an aiosqlite connection to the database.
    Caller is responsible for closing the connection (or using context manager).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        yield db

async def init_db():
    """Initializes the database with required tables and indexes."""
    logger.info(f"Initializing database at {DB_PATH}")
    # Ensure directory exists (critical for usage in /app/data if not pre-created)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Chat Sessions (Volatile)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content_encrypted BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Index for fast retrieval by session_id and cleanup by date
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_session_id ON chat_sessions(session_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_created_at ON chat_sessions(created_at);")

        # 2. Usage Logs (Audit / Rate Limiting)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Index for rate limiting queries (session_id + date)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_usage_session_date ON usage_logs(session_id, created_at);")
        
        # 3. Leads (Persistent)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_info_encrypted BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await db.commit()
    logger.info("Database initialized successfully.")
