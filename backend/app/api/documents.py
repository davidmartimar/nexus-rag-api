from fastapi import APIRouter, HTTPException
from app.services.rag_service import get_all_documents, delete_document

router = APIRouter()

@router.get("/documents", tags=["Documents"])
async def list_documents(collection_name: str = "nexus_slot_1"):
    """
    Returns a list of all uploaded documents.
    """
    documents = get_all_documents(collection_name)
    return {"documents": documents}

@router.delete("/documents/{filename}", tags=["Documents"])
async def remove_document(filename: str, collection_name: str = "nexus_slot_1"):
    """
    Deletes a specific document from the knowledge base.
    """
    success = delete_document(filename, collection_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found or could not be deleted.")
    
    return {"status": "success", "message": f"Document '{filename}' deleted."}
