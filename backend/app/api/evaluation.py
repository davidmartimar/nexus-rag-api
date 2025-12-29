from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.services.evaluation_service import generate_evaluation_testset, run_evaluation
import json
import os

router = APIRouter()

# Simple storage for the last generated testset (in memory for now, or file)
LAST_TESTSET_PATH = "latest_testset.json"

class GenerateRequest(BaseModel):
    limit: int = 15

class RunRequest(BaseModel):
    testset: Optional[List[dict]] = None
    
@router.post("/evaluate/generate", tags=["Evaluation"])
async def generate_testset(request: GenerateRequest):
    """
    Generates a synthetic test set from the current knowledge base.
    This can take a while (minutes).
    """
    try:
        data = generate_evaluation_testset(limit=request.limit)
        
        # Save to disk
        with open(LAST_TESTSET_PATH, "w") as f:
            json.dump(data, f)
            
        return {
            "status": "success",
            "count": len(data),
            "preview": data[:3],
            "message": "Testset generated and saved."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/run", tags=["Evaluation"])
async def evaluate_system(request: RunRequest):
    """
    Runs the generic RAGAS evaluation metrics on the testset.
    If no testset provided, tries to load the last generated one.
    """
    try:
        data = request.testset
        if not data:
            if os.path.exists(LAST_TESTSET_PATH):
                with open(LAST_TESTSET_PATH, "r") as f:
                    data = json.load(f)
            else:
                raise HTTPException(status_code=400, detail="No testset provided and no cached testset found.")
        
        results = run_evaluation(data)
        
        # Calculate averages for easy reading
        # results is a list of dicts with scores per row? 
        # Actually evaluate returns a Result object which behaves like a dict of averages, 
        # but to_pandas().to_dict gave us rows.
        # Let's fix evaluation_service return if we want summary.
        # But row-level is good for details.
        
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
