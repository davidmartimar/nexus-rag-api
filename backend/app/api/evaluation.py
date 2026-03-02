import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.evaluation_service import generate_evaluation_testset, run_evaluation

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants
# Using Path for robust cross-platform path handling
LAST_TESTSET_PATH = Path("latest_testset.json")

class GenerateRequest(BaseModel):
    limit: int = Field(default=15, ge=1, le=100, description="Number of test cases to generate")

class RunRequest(BaseModel):
    testset: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional custom testset to evaluate")


@router.post("/evaluate/generate", tags=["Evaluation"])
def generate_testset(request: GenerateRequest):
    """
    Generates a synthetic test set from the current knowledge base.
    Warning: This is a computationally intensive task and runs in the background threadpool.
    """
    try:
        logger.info(f"Starting testset generation with limit: {request.limit}")
        data = generate_evaluation_testset(limit=request.limit)
        
        # Persist to disk safely with UTF-8 encoding
        with LAST_TESTSET_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return {
            "status": "success",
            "count": len(data),
            "preview": data[:3] if data else [],
            "message": "Testset generated and saved successfully."
        }
        
    except Exception as e:
        logger.error("Error during testset generation", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during testset generation.")


@router.post("/evaluate/run", tags=["Evaluation"])
def evaluate_system(request: RunRequest):
    """
    Runs evaluation metrics on the provided testset or the last locally cached one.
    """
    try:
        data = request.testset
        
        # Load cached testset if none is explicitly provided in the request
        if not data:
            if LAST_TESTSET_PATH.exists():
                with LAST_TESTSET_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                logger.warning("Evaluation requested but no testset provided or found on disk.")
                raise HTTPException(status_code=400, detail="No testset provided and no cached testset found.")
        
        logger.info(f"Starting evaluation on {len(data)} items.")
        results = run_evaluation(data)
        
        return {
            "status": "success",
            "results": results
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions intentionally thrown (like the 400 above)
        raise
    except Exception as e:
        logger.error("Error executing evaluation metrics", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during evaluation.")