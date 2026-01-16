from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from app.api import ingest
from app.api import chat
from app.api import status as status_api
from app.api import documents
from app.api import admin
from app.api import evaluation
from app.core.auth_simple import verify_api_key

load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 
    # removed init_db() as we are now pure RAG
    yield
    # Shutdown: Clean up if needed (nothing for now)

app = FastAPI(title="NEXUS RAG API", version="1.0.0", lifespan=lifespan)

# Include routers with global security dependency
app.include_router(ingest.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])
app.include_router(chat.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])
app.include_router(status_api.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])
app.include_router(documents.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])
app.include_router(admin.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])
app.include_router(evaluation.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])


@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS API. Systems Online."}
