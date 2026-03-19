# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NEXUS RAG API v5.0 is a production-ready Retrieval-Augmented Generation system built for Barnalytics. It consists of a FastAPI backend, a Streamlit frontend, and an optional n8n automation service — all orchestrated via Docker Compose.

## Commands

### Running the full stack
```bash
docker-compose up --build
```
- Frontend UI: http://localhost:8501 (password via `NEXUS_FRONTEND_PASSWORD`)
- Backend API docs: http://localhost:8000/docs (requires `X-NEXUS-KEY` header)
- n8n: http://localhost:5678

### Local development (without Docker)
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
pip install -r requirements.txt
streamlit run app/main.py
```

### Running test scripts
```bash
python test_status.py        # Verifies document indexing
python test_persistence.py   # Tests data persistence
python backend/test_import.py  # Quick import verification
```

## Architecture

### Service Boundaries
- **Frontend** (`frontend/app/main.py`): Streamlit UI — password-protected, calls the backend API using the `X-NEXUS-KEY` header. All state is derived from API responses; there is no local state persistence.
- **Backend** (`backend/app/`): Stateless FastAPI service. All knowledge is stored in ChromaDB. No transactional DB for conversations.
- **n8n** (port 5678): Optional workflow automation. Can call the backend `/api/v1/chat` endpoint.

### Backend Layers
```
backend/app/
├── main.py           # FastAPI app, lifespan, router registration
├── schemas.py        # All Pydantic request/response models (ChatRequest, ChatResponse, UniversalLead)
├── core/
│   ├── config.py     # Env var loading and startup validation
│   └── auth_simple.py # API key validation (X-NEXUS-KEY header applied globally)
├── api/              # Thin routers — delegate immediately to services
│   ├── chat.py       # POST /api/v1/chat
│   ├── ingest.py     # POST /api/v1/ingest
│   ├── documents.py  # GET/DELETE /api/v1/documents
│   ├── status.py     # GET /api/v1/status
│   ├── admin.py      # /reset, /config, /slots, /export, /import
│   └── evaluate.py   # /generate, /run
└── services/
    ├── rag_service.py        # Document loading, chunking, embedding, ChromaDB ops, import/export
    ├── chat_service.py       # RAG pipeline: vector search → conversation memory → GPT-4o-mini → lead extraction
    └── evaluation_service.py # RAGAS evaluation (Faithfulness, Context Precision, Answer Relevance)
```

### Key Design Decisions
- **Multi-tenant via memory slots**: Each slot maps to an isolated ChromaDB collection (e.g., `nexus_slot_1`). Slot metadata is persisted in `slots.json`.
- **Conversation memory**: `ConversationBufferWindowMemory` with a sliding window of the last 5 exchanges — stored in-process, not persisted.
- **LLM**: GPT-4o-mini (cost-optimized). Embeddings also use OpenAI's API.
- **Audio ingestion**: MP3/WAV/M4A files are transcribed via OpenAI Whisper before being indexed.
- **Lead extraction**: Chat responses optionally extract a `UniversalLead` schema from the conversation using a secondary LLM call.

### Storage
- `backend/chroma_db/` (mapped to Docker volume `nexus-chroma`): Vector database — source of truth for all knowledge.
- `backend/data_uploads/`: Temporary upload staging; files are cleaned up after ingestion.
- `slots.json`: Persists memory slot names and metadata.
- `nexus.db` (SQLite at `/app/data/nexus.db`): Present but minimally used in current version.

## Environment Variables

Required in `.env` (see docker-compose.yml for how they are passed to containers):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI API access (embeddings + LLM + Whisper) |
| `NEXUS_API_KEY` | Backend authentication key (sent as `X-NEXUS-KEY`) |
| `NEXUS_FRONTEND_PASSWORD` | Streamlit login password |
| `SECRET_KEY` | Application secret for signing |
| `WEBHOOK_URL` | n8n webhook endpoint |
| `DB_PATH` | SQLite path (default: `/app/data/nexus.db`) |
| `MAX_REQUESTS_LIMIT` | Rate limiting |
| `LOG_RETENTION_HOURS` | Log TTL |
| `CHAT_RETENTION_HOURS` | Chat history TTL |
