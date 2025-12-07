from fastapi import FastAPI
from app.api import ingest
from app.api import chat

app = FastAPI(title="NEXUS RAG API", version="1.0.0")

# Include routers
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS API. Systems Online."}