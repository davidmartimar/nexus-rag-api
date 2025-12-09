import shutil
import threading
import os
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from app.services import rag_service
import shutil
import os

router = APIRouter()

@router.post("/reset")
async def reset_knowledge_base(payload: dict):
    collection_name = payload.get("collection_name", "nexus_slot_1")
    success = rag_service.reset_knowledge_base(collection_name)
    if success:
        return {"status": "success", "message": f"Knowledge base '{collection_name}' has been reset."}
    else:
        raise HTTPException(status_code=500, detail="Failed to reset knowledge base.")

@router.get("/config")
async def get_config():
    return rag_service.get_slot_config()

@router.post("/config")
async def update_config(config: dict):
    success = rag_service.save_slot_config(config)
    if success:
        return {"status": "success", "message": "Configuration saved."}
    else:
        raise HTTPException(status_code=500, detail="Failed to save configuration.")

@router.post("/slots")
async def create_new_slot(payload: dict):
    name = payload.get("name", "New Brain")
    slot_id = rag_service.create_slot(name)
    if slot_id:
        return {"status": "success", "slot_id": slot_id, "name": name}
    else:
        raise HTTPException(status_code=500, detail="Failed to create slot.")

@router.delete("/slots/{slot_id}")
async def delete_slot(slot_id: str):
    success = rag_service.delete_slot(slot_id)
    if success:
        return {"status": "success", "message": f"Slot {slot_id} deleted."}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete slot.")

@router.get("/export")
async def export_slot(collection_name: str = "nexus_slot_1"):
    try:
        zip_path = rag_service.export_slot_data(collection_name)
        if not zip_path:
            raise HTTPException(status_code=500, detail="Export failed")
            
        return FileResponse(zip_path, filename=f"nexus_export_{collection_name}.zip", media_type="application/zip")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_slot(collection_name: str = Form(...), file: UploadFile = File(...)):
    try:
        temp_file = f"/app/temp_import_{file.filename}"
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        success = rag_service.import_slot_data(collection_name, temp_file)
        
        os.remove(temp_file)
        
        if success:
            return {"status": "success", "message": f"Successfully imported knowledge into {collection_name}"}
        else:
            raise HTTPException(status_code=500, detail="Import failed internally.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
