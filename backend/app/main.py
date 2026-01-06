from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv
from app.api import ingest
from app.api import chat
from app.api import status as status_api
from app.api import documents
from app.api import admin

load_dotenv()

API_KEY_NAME = "X-NEXUS-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    correct_key = os.getenv("NEXUS_API_KEY")
    if not correct_key:
         # Fail open or closed? Closed is safer, but if user forgot to set env, it breaks.
         # For this user, we just set it.
         print("WARNING: NEXUS_API_KEY not set in backend environment.")
         # Allow if not configured? No, user wants security.
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server Security Config Error"
        )
        
    if api_key_header == correct_key:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )

from contextlib import asynccontextmanager
from app.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    await init_db()
    yield
    # Shutdown: Clean up if needed (nothing for now)

app = FastAPI(title="NEXUS RAG API", version="1.0.0", lifespan=lifespan)

# Include routers
app.include_router(ingest.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(chat.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(status_api.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(documents.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])
app.include_router(admin.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])

from app.api import evaluation
app.include_router(evaluation.router, prefix="/api/v1", dependencies=[Depends(get_api_key)])


@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS API. Systems Online."}