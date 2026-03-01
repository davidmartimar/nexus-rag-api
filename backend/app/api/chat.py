import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Services and Core
from app.services.chat_service import get_answer

router = APIRouter()
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    """Unified model for chat requests (Supports Frontend v4.1 and Legacy API)."""
    # Core fields
    message: Optional[str] = None
    collection_name: str = "nexus_slot_1" 
    
    # Business / Context fields
    business_context: Optional[str] = None
    user_id: Optional[str] = None

    # Legacy fields (Maintained for backward compatibility with older n8n workflows)
    query: Optional[str] = None 
    system_instruction: Optional[str] = None


@router.post("/chat", tags=["Chat"])
def chat_endpoint(request: QueryRequest, background_tasks: BackgroundTasks):
    # 1. Normalize input (priority to 'message' over 'query')
    final_query = request.message or request.query
    
    if not final_query:
        raise HTTPException(status_code=400, detail="The 'message' or 'query' field is required.")

    try:
        # 2. Call the RAG core service
        response = get_answer(
            query=final_query, 
            collection_name=request.collection_name, 
            history=[]  # TODO: Implement persistent state management (e.g., Redis/PostgreSQL)
        )
        
        # 3. Defensive response structuring
        if isinstance(response, dict):
            bot_answer = response.get("answer", "")
            lead_data = response.get("lead_data")
            sources = response.get("sources", [])
        else:
            bot_answer = str(response)
            lead_data = None
            sources = []

        # 4. Return standardized payload
        return {
            "answer": bot_answer,
            "sources": sources,
            "lead_data": lead_data,
            "usage": {"remaining": 20, "limit_reached": False}  # TODO: Connect to actual quota/rate-limiting system
        }
        
    except Exception as e:
        logger.error("Critical error processing query in /chat", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while processing the request.")