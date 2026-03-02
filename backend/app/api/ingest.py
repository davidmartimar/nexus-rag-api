import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form

# Services and Core
from app.services.rag_service import index_document 

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants
UPLOAD_DIR = Path("/app/data_uploads")


@router.post("/ingest", tags=["Ingestion"])
def ingest_documents(
    files: List[UploadFile] = File(...),
    collection_name: str = Form(default="nexus_slot_1", description="Target knowledge base slot")
):
    """
    Uploads multiple files, saves them temporarily, and indexes them into the Vector Database (ChromaDB).
    Runs synchronously in FastAPI's threadpool to prevent blocking the async event loop during heavy I/O.
    """
    results: List[Dict[str, Any]] = []
    
    # Ensure the upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for file in files:
        # Use pathlib for safe cross-platform path joining
        file_path = UPLOAD_DIR / file.filename
        
        try:
            # 1. Save file locally for the indexing service to process
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # 2. Execute RAG indexing pipeline
            logger.info(f"Starting document indexing for {file.filename} into collection '{collection_name}'")
            indexing_result = index_document(str(file_path), collection_name)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "details": indexing_result
            })
            logger.info(f"Successfully indexed: {file.filename}")
            
        except Exception as e:
            logger.error(f"Failed to ingest document {file.filename}: {e}", exc_info=True)
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
        finally:
            # 3. Cleanup: Remove the temporary file after indexing to prevent disk space exhaustion
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as cleanup_error:
                    logger.warning(f"Could not delete temporary upload file {file_path}: {cleanup_error}")
            
    return {"results": results}