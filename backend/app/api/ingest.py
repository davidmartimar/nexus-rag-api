from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from app.services.rag_service import index_document 

router = APIRouter()

@router.post("/ingest", tags=["Ingestion"])
async def ingest_document(file: UploadFile = File(...)):
    """
    Uploads a PDF and indexes it into ChromaDB.
    """
    try:
        # 1. Save File
        upload_dir = "/app/data_uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Trigger Indexing (RAG Magic)
        indexing_result = index_document(file_path)
            
        return {
            "message": "File processed and indexed successfully",
            "filename": file.filename,
            "indexing_stats": indexing_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")