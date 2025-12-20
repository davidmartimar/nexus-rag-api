import shutil
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse
from app.services import rag_service

router = APIRouter()

# NOTE: All endpoints are protected by the global API Key dependency in main.py.
# NOTE: Functions are defined as 'def' (sync) to allow FastAPI to run them in a threadpool,
# preventing the main event loop from being blocked by heavy I/O in rag_service.

def remove_file(path: str):
    try:
        os.remove(path)
    except Exception as e:
        print(f"Error deleting temp file {path}: {e}")

@router.post("/reset")
def reset_knowledge_base(payload: dict):
    collection_name = payload.get("collection_name", "nexus_slot_1")
    # Clean input to prevent path traversal or weirdness, though underlying logic handles it.
    if not collection_name or ".." in collection_name:
         raise HTTPException(status_code=400, detail="Invalid collection name")
         
    success = rag_service.reset_knowledge_base(collection_name)
    if success:
        return {"status": "success", "message": f"Knowledge base '{collection_name}' has been reset."}
    else:
        raise HTTPException(status_code=500, detail="Failed to reset knowledge base.")

@router.get("/config")
def get_config():
    return rag_service.get_slot_config()

@router.post("/config")
def update_config(config: dict):
    success = rag_service.save_slot_config(config)
    if success:
        return {"status": "success", "message": "Configuration saved."}
    else:
        raise HTTPException(status_code=500, detail="Failed to save configuration.")

@router.post("/slots")
def create_new_slot(payload: dict):
    name = payload.get("name", "New Brain")
    slot_id = rag_service.create_slot(name)
    if slot_id:
        return {"status": "success", "slot_id": slot_id, "name": name}
    else:
        raise HTTPException(status_code=500, detail="Failed to create slot.")

@router.delete("/slots/{slot_id}")
def delete_slot(slot_id: str):
    # Basic validation
    if not slot_id.startswith("nexus_slot_"):
         raise HTTPException(status_code=400, detail="Invalid slot ID format.")
         
    success = rag_service.delete_slot(slot_id)
    if success:
        return {"status": "success", "message": f"Slot {slot_id} deleted."}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete slot.")

@router.get("/export")
def export_slot(background_tasks: BackgroundTasks, collection_name: str = "nexus_slot_1"):
    try:
        zip_path = rag_service.export_slot_data(collection_name)
        if not zip_path:
            raise HTTPException(status_code=500, detail="Export failed")
            
        # Schedule file deletion after response is sent
        background_tasks.add_task(remove_file, zip_path)
            
        return FileResponse(zip_path, filename=f"nexus_export_{collection_name}.zip", media_type="application/zip")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
def import_slot(collection_name: str = Form(...), file: UploadFile = File(...)):
    # Use tempfile to avoid collisions and ensure cleanup
    temp_path = None
    try:
        # Create a temp file. delete=False because we need to close it and let rag_service open it.
        # We manually unlink later.
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        
        success = rag_service.import_slot_data(collection_name, temp_path)
        
        if success:
            return {"status": "success", "message": f"Successfully imported knowledge into {collection_name}"}
        else:
            raise HTTPException(status_code=500, detail="Import failed internally.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always clean up the temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass # logging.warning("Could not delete temp file")
