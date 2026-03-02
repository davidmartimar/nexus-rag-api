import os
import shutil
import logging
import tempfile
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services import rag_service

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Pydantic Models for Request Validation ---
class ResetRequest(BaseModel):
    collection_name: str = "nexus_slot_1"

class SlotCreateRequest(BaseModel):
    name: str = "New Brain"


# NOTE: All endpoints are protected by the global API Key dependency in main.py.
# NOTE: Functions are defined as 'def' (sync) to allow FastAPI to run them in a threadpool,
# preventing the main event loop from being blocked by heavy I/O operations in rag_service.

def remove_file(path: str) -> None:
    """Utility function to remove temporary files asynchronously."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"Error deleting temporary file {path}: {e}", exc_info=True)


@router.post("/reset")
def reset_knowledge_base(request: ResetRequest):
    """Resets a specific knowledge base collection."""
    # Basic path traversal prevention
    if not request.collection_name or ".." in request.collection_name:
         raise HTTPException(status_code=400, detail="Invalid collection name format.")
         
    success = rag_service.reset_knowledge_base(request.collection_name)
    if success:
        return {"status": "success", "message": f"Knowledge base '{request.collection_name}' has been reset."}
    
    logger.error(f"Failed to reset knowledge base: {request.collection_name}")
    raise HTTPException(status_code=500, detail="Failed to reset knowledge base.")


@router.get("/config")
def get_config():
    """Retrieves the current configuration for slots."""
    return rag_service.get_slot_config()


@router.post("/config")
def update_config(config: Dict[str, Any]):
    """Updates the slot configuration."""
    success = rag_service.save_slot_config(config)
    if success:
        return {"status": "success", "message": "Configuration saved successfully."}
    
    logger.error("Failed to save slot configuration.")
    raise HTTPException(status_code=500, detail="Failed to save configuration.")


@router.post("/slots")
def create_new_slot(request: SlotCreateRequest):
    """Creates a new memory slot."""
    slot_id = rag_service.create_slot(request.name)
    if slot_id:
        return {"status": "success", "slot_id": slot_id, "name": request.name}
    
    logger.error(f"Failed to create slot with name: {request.name}")
    raise HTTPException(status_code=500, detail="Failed to create new slot.")


@router.delete("/slots/{slot_id}")
def delete_slot(slot_id: str):
    """Deletes an existing memory slot."""
    if not slot_id.startswith("nexus_slot_"):
         raise HTTPException(status_code=400, detail="Invalid slot ID format. Must start with 'nexus_slot_'.")
         
    success = rag_service.delete_slot(slot_id)
    if success:
        return {"status": "success", "message": f"Slot {slot_id} deleted successfully."}
    
    logger.error(f"Failed to delete slot: {slot_id}")
    raise HTTPException(status_code=500, detail="Failed to delete slot.")


@router.get("/export")
def export_slot(background_tasks: BackgroundTasks, collection_name: str = "nexus_slot_1"):
    """Exports slot data as a ZIP file and cleans up the temp file afterwards."""
    try:
        zip_path = rag_service.export_slot_data(collection_name)
        if not zip_path:
            raise ValueError("Export service returned an empty path.")
            
        # Schedule file deletion after the response is sent to the client
        background_tasks.add_task(remove_file, zip_path)
            
        return FileResponse(
            zip_path, 
            filename=f"nexus_export_{collection_name}.zip", 
            media_type="application/zip"
        )
    except Exception as e:
        logger.error(f"Export failed for collection {collection_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during export.")


@router.post("/import")
def import_slot(collection_name: str = Form(...), file: UploadFile = File(...)):
    """Imports slot data from an uploaded file."""
    temp_path = None
    try:
        # Create a temp file. delete=False allows rag_service to open it safely.
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        
        success = rag_service.import_slot_data(collection_name, temp_path)
        
        if success:
            return {"status": "success", "message": f"Successfully imported knowledge into {collection_name}."}
        
        logger.error(f"Internal import failure for collection: {collection_name}")
        raise HTTPException(status_code=500, detail="Import process failed internally.")
            
    except Exception as e:
        logger.error(f"Exception during import for collection {collection_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during import.")
    finally:
        # Ensure the temporary file is always cleaned up, even if exceptions occur
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {cleanup_error}")