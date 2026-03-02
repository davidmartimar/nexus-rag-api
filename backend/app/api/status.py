import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query
from app.services.rag_service import get_document_count

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status", tags=["Status"])
def get_status(
    collection_name: str = Query(
        default="nexus_slot_1", 
        description="The name of the memory slot to check"
    )
) -> Dict[str, Any]:
    """
    Health check endpoint. 
    Retrieves the operational status and document count of a specific knowledge base slot.
    Runs synchronously to prevent event loop blocking during database queries.
    """
    try:
        # Query the vector database for the current document count
        count = get_document_count(collection_name)
        
        return {
            "status": "online",
            "collection_name": collection_name,
            "document_count": count,
            "ready": count > 0
        }
        
    except Exception as e:
        logger.error(f"Health check failed for collection '{collection_name}': {e}", exc_info=True)
        # Return a 503 instead of a 500. 503 explicitly means "Service Unavailable" 
        # which is the standard HTTP code when a backend dependency (like ChromaDB) is down.
        raise HTTPException(
            status_code=503, 
            detail="Service unavailable: Could not connect to the vector database."
        )