from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY_NAME = "X-NEXUS-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
NEXUS_API_KEY = os.getenv("NEXUS_API_KEY")

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    if not NEXUS_API_KEY:
        # If no key is configured, we allow access (or log a warning)
        # For security, one might want to block, but for this demo/user preference:
        return True 
    if api_key_header == NEXUS_API_KEY:
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
