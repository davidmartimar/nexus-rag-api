import logging
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Query
from app.services.rag_service import get_all_documents, delete_document

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/documents", tags=["Documents"])
def list_documents(
    collection_name: str = Query(
        default="nexus_slot_1", 
        description="The target memory slot to retrieve documents from"
    )
) -> Dict[str, List[Any]]:
    """
    Retrieves a list of all indexed documents in the specified knowledge base.
    Runs synchronously to prevent blocking the async event loop during database queries.
    """
    try:
        documents = get_all_documents(collection_name)
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error retrieving documents for collection '{collection_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Internal server error while retrieving documents from the vector database."
        )

@router.delete("/documents/{filename}", tags=["Documents"])
def remove_document(
    filename: str, 
    collection_name: str = Query(
        default="nexus_slot_1", 
        description="The target memory slot to delete the document from"
    )
) -> Dict[str, str]:
    """
    Removes a specific document and its associated embeddings from the knowledge base.
    """
    try:
        success = delete_document(filename, collection_name)
        
        if not success:
            logger.warning(f"Deletion failed: Document '{filename}' not found in '{collection_name}'.")
            raise HTTPException(
                status_code=404, 
                detail=f"Document '{filename}' not found in the specified collection."
            )
        
        logger.info(f"Successfully deleted document '{filename}' from '{collection_name}'.")
        return {"status": "success", "message": f"Document '{filename}' deleted successfully."}
        
    except HTTPException:
        # Re-raise the 404 intentionally thrown above
        raise
    except Exception as e:
        logger.error(f"Critical error deleting document '{filename}' from '{collection_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Internal server error while attempting to delete the document."
        )