from fastapi import APIRouter
from app.services.rag_service import get_document_count

router = APIRouter()

@router.get("/status", tags=["Status"])
async def get_status():
    """
    Returns the status of the knowledge base.
    """
    count = get_document_count()
    return {
        "status": "online",
        "document_count": count,
        "ready": count > 0
    }
