import aiosqlite
from datetime import datetime

async def create_chat_session(db: aiosqlite.Connection, session_id: str, role: str, encrypted_content: bytes):
    """Inserts a new chat message/session record."""
    await db.execute(
        "INSERT INTO chat_sessions (session_id, role, content_encrypted) VALUES (?, ?, ?)",
        (session_id, role, encrypted_content)
    )
    await db.commit()

async def get_chat_history(db: aiosqlite.Connection, session_id: str):
    """Retrieves encrypted chat history for a session."""
    # Ordered by creation time
    cursor = await db.execute(
        "SELECT role, content_encrypted FROM chat_sessions WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,)
    )
    return await cursor.fetchall()

async def log_usage(db: aiosqlite.Connection, session_id: str):
    """Logs a user interaction for rate limiting purposes."""
    await db.execute("INSERT INTO usage_logs (session_id) VALUES (?)", (session_id,))
    await db.commit()

async def get_usage_count_since(db: aiosqlite.Connection, session_id: str, since_timestamp: str) -> int:
    """Counts usage logs for a session since a specific timestamp."""
    cursor = await db.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE session_id = ? AND created_at > ?",
        (session_id, since_timestamp)
    )
    row = await cursor.fetchone()
    return row[0] if row else 0

async def delete_old_chat_sessions(db: aiosqlite.Connection, before_timestamp: str) -> int:
    """Deletes chat sessions older than the given timestamp."""
    cursor = await db.execute(
        "DELETE FROM chat_sessions WHERE created_at < ?",
        (before_timestamp,)
    )
    await db.commit()
    return cursor.rowcount

async def delete_old_usage_logs(db: aiosqlite.Connection, before_timestamp: str) -> int:
    """Deletes usage logs older than the given timestamp."""
    cursor = await db.execute(
        "DELETE FROM usage_logs WHERE created_at < ?",
        (before_timestamp,)
    )
    await db.commit()
    return cursor.rowcount
