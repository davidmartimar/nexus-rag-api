# ネ NEXUS: Enterprise RAG Knowledge Engine

NEXUS is a production-ready **Retrieval-Augmented Generation (RAG)** system designed for secure enterprise document ingestion and intelligent querying. It features a microservices architecture fully containerized with Docker.

![Status](https://img.shields.io/badge/Status-Active-success)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Python](https://img.shields.io/badge/Python-3.10-yellow)

## Architecture

The system is composed of two isolated microservices:

1.  **Backend Node (The Brain):**
    * **FastAPI:** High-performance async API.
    * **LangChain:** RAG logic orchestration.
    * **ChromaDB:** Local vector persistence (Embeddings).
    * **OpenAI GPT-4/3.5:** Generative intelligence.
    
2.  **Frontend Node (The Interface):**
    * **Streamlit:** Reactive UI for document ingestion and chat.
    * **Dynamic SVG Generation:** JIT asset creation for branding.

## Quick Start

### Prerequisites
* Docker & Docker Compose
* OpenAI API Key

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/davidmartimar/nexus-rag-api.git](https://github.com/davidmartimar/nexus-rag-api.git)
    cd nexus-rag-api
    ```

2.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=sk-your-key-here
    ```

3.  **Ignition**
    Launch the cluster:
    ```bash
    docker-compose up --build
    ```

4.  **Access**
    * **Frontend UI:** `http://localhost:8501`
    * **Backend Swagger:** `http://localhost:8000/docs`

## Project Structure

```text
nexus-rag-api/
├── backend/            # FastAPI Service
│   ├── app/
│   │   ├── api/        # Endpoints (Chat, Ingest)
│   │   ├── services/   # RAG Logic & Vector Store
│   │   └── core/       # Config
├── frontend/           # Streamlit Service
│   ├── app/
│   │   └── main.py     # UI Logic & Animation
├── docker-compose.yml  # Orchestration
└── README.md
```
## License

This project is open-source and available under the [MIT License](LICENSE).
Built with ❤️ by **David Martínez Martín** (davidmartimar).
