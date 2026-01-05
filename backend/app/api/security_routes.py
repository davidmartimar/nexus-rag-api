from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.services import security_service
from app.core import tasks

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    history_preview: List[dict] = []

@router.post("/secure-chat", response_model=ChatResponse)
async def secure_chat_endpoint(request: ChatRequest):
    """
    Example endpoint showing the secure flow:
    1. Check Rate Limit (throws 429 if exceeded)
    2. Encrypt & Save User Message
    3. Process (Simulated)
    4. Encrypt & Save Assistant Response
    """
    # 1. Rate Limit & Logging
    # This raises RateLimitExceeded (429) if limit reached
    await security_service.validate_user_access(request.user_id)
        
    # 2. Encrypt & Save User Message
    await security_service.save_secure_message(request.user_id, "user", request.message)
    
    # 3. Simulate LLM processing
    fake_llm_response = f"Echo: {request.message} (Securely processed by NEXUS)"
    
    # 4. Encrypt & Save Assistant Response
    await security_service.save_secure_message(request.user_id, "assistant", fake_llm_response)
    
    # Optional: Fetch history to prove it works
    history = await security_service.get_secure_history(request.user_id)
    
    return ChatResponse(response=fake_llm_response, history_preview=history[-2:])

@router.post("/run-cleanup")
async def run_cleanup_endpoint():
    """Manually triggers the database cleanup task."""
    result = await tasks.cleanup_database()
    return {"status": "success", "deleted_counts": result}
