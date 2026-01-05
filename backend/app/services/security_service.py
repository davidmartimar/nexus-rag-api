from datetime import datetime, timedelta
import aiosqlite
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import hash_user_id, encrypt_data, decrypt_data
from app.services import crud
from app.core.database import DB_PATH

class RateLimitExceeded(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Daily limit reached."
        )

async def validate_user_access(user_id: str) -> str:
    """
    Checks rate limits for a user.
    Returns the hashed user ID if allowed.
    Raises RateLimitExceeded if blocked.
    """
    user_hash = hash_user_id(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Calculate cutoff for 24h window
        since = (datetime.utcnow() - timedelta(hours=settings.LOG_RETENTION_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Check usage
        count = await crud.get_usage_count_since(db, user_hash, since)
        if count >= settings.MAX_REQUESTS_LIMIT:
            raise RateLimitExceeded()
            
        # Log this new interaction
        await crud.log_usage(db, user_hash)
        
    return user_hash

async def save_secure_message(user_id: str, role: str, content: str):
    """Encrypts and saves a message to the ephemeral chat storage."""
    # We re-hash here to be safe, or we could pass the hash. 
    # Hashing is fast enough to do again.
    user_hash = hash_user_id(user_id)
    encrypted = encrypt_data(content)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await crud.create_chat_session(db, user_hash, role, encrypted)

async def get_secure_history(user_id: str):
    """Retrieves and decrypts chat history for a user."""
    user_hash = hash_user_id(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await crud.get_chat_history(db, user_hash)
        
    history = []
    for role, encrypted_content in rows:
        decrypted = decrypt_data(encrypted_content)
        history.append({"role": role, "content": decrypted})
        
    return history

from app.schemas import UsageMetadata

async def get_usage_stats(user_id: str) -> UsageMetadata:
    """Calculates usage statistics for a user."""
    user_hash = hash_user_id(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Calculate cutoff for 24h window
        since = (datetime.utcnow() - timedelta(hours=settings.LOG_RETENTION_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Check usage
        count = await crud.get_usage_count_since(db, user_hash, since)
        
    limit = settings.MAX_REQUESTS_LIMIT
    remaining = max(0, limit - count)
    
    return UsageMetadata(
        daily_limit=limit,
        current_usage=count,
        remaining=remaining,
        is_limit_reached=(remaining == 0)
    )
