import aiosqlite
import logging
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.database import DB_PATH
from app.services import crud

logger = logging.getLogger(__name__)

async def cleanup_database():
    """
    Periodic task to clean up old data.
    - Chat sessions: Deleted after 2 hours (Privacy)
    - Usage logs: Deleted after 24 hours (Cost Control)
    """
    logger.info("Starting database cleanup task...")
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Cleanup Chat Sessions
        chat_cutoff = (datetime.utcnow() - timedelta(hours=settings.CHAT_RETENTION_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        deleted_chats = await crud.delete_old_chat_sessions(db, chat_cutoff)
        
        # 2. Cleanup Usage Logs
        log_cutoff = (datetime.utcnow() - timedelta(hours=settings.LOG_RETENTION_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        deleted_logs = await crud.delete_old_usage_logs(db, log_cutoff)
        
        logger.info(f"Database cleanup complete. Removed {deleted_chats} chat sessions and {deleted_logs} usage logs.")
        
    return {"deleted_chats": deleted_chats, "deleted_logs": deleted_logs}
