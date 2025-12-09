from fastapi import FastAPI
from app.api import ingest
from app.api import chat
from app.api import status
from app.api import status
from app.api import documents
from app.api import admin

app = FastAPI(title="NEXUS RAG API", version="1.0.0")

# Include routers
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS API. Systems Online."}