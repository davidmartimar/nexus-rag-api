from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from app.services.rag_service import index_document 

router = APIRouter()

@router.post("/ingest", tags=["Ingestion"])
async def ingest_documents(
    files: List[UploadFile] = File(...),
    collection_name: str = "nexus_slot_1"
):
    """
    Uploads multiple files and indexes them into ChromaDB.
    """
    results = []
    upload_dir = "/app/data_uploads"
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        try:
            # 1. Save File
            file_path = os.path.join(upload_dir, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # 2. Trigger Indexing (RAG Magic)
            indexing_result = index_document(file_path, collection_name)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "details": indexing_result
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
            
    return {"results": results}