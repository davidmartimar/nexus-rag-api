from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.chat_service import get_answer

router = APIRouter()

# Define the data model for the request
class QueryRequest(BaseModel):
    query: str
    collection_name: str = "nexus_slot_1"

@router.post("/chat", tags=["Chat"])
async def chat_endpoint(request: QueryRequest):
    """
    Asks a question to the NEXUS Knowledge Base.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        response = get_answer(request.query, request.collection_name)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))