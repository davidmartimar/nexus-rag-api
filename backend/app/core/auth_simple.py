from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os
import secrets
import logging
from dotenv import load_dotenv

load_dotenv()

NEXUS_API_KEY = os.getenv("NEXUS_API_KEY")
logger = logging.getLogger(__name__)
if not NEXUS_API_KEY:
    logger.critical("NEXUS_API_KEY is not set! API will reject ALL requests.")

API_KEY_NAME = "X-NEXUS-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    if not NEXUS_API_KEY or not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured. Access denied.",
        )
    if secrets.compare_digest(api_key_header, NEXUS_API_KEY):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )