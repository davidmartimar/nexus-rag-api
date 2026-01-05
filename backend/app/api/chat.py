from fastapi import APIRouter, HTTPException
from app.services import chat_service, security_service
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main Chat Endpoint with:
    1. Security & Rate Limiting (if user_id provided)
    2. RAG Retrieval
    3. Structural Lead Extraction (Universal)
    4. Secure Logging
    """
    try:
        # 1. Security Check (if user_id present)
        # Allows anonymous chat if no user_id, or enforce it? 
        # Requirement said "Gestión de datos sensibles... privacidad".
        # Assuming we want to track rate limits by user_id if provided.
        if request.user_id:
            await security_service.validate_user_access(request.user_id)
            # Log incoming message securely
            await security_service.save_secure_message(request.user_id, "user", request.message)

        # 2. Get RAG Answer + Lead Data
        result = chat_service.get_answer(
            query=request.message, 
            history=request.history,
            business_context=request.business_context
        )
        
        # 3. Secure Logging of Response (if user_id present)
        usage_stats = None
        if request.user_id:
            await security_service.save_secure_message(request.user_id, "assistant", result["answer"])
            # Get updated usage stats to return to client
            usage_stats = await security_service.get_usage_stats(request.user_id)

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            lead_data=result.get("lead_data"),
            usage=usage_stats
        )
            
    except security_service.RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e.detail))
    except Exception as e:
        # Handle other errors
        raise HTTPException(status_code=500, detail=str(e))