# ネ NEXUS: Enterprise RAG Knowledge Engine

NEXUS is a production-ready **Retrieval-Augmented Generation (RAG)** system designed for secure enterprise document ingestion and intelligent querying. It features a microservices architecture fully containerized with Docker, with **Dynamic Memory Slots** and **Knowledge Portability**.

![Status](https://img.shields.io/badge/Status-Active-success)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Python](https://img.shields.io/badge/Python-3.10-yellow)
![Version](https://img.shields.io/badge/Version-4.1-purple)

## Key Features v4.1

*   **🛡️ Enterprise Security**: 
    *   **Frontend Login**: Secure access gateway protected by password.
    *   **API Key Protection**: Backend endpoints shielded by `X-NEXUS-KEY` to prevent unauthorized usage and billing abuse.
*   **Conversation Memory**: Remembers context from previous messages (last 5 exchanges) for natural follow-up questions.
*   **Chat Download**: Export your complete conversation history to a PDF file.
*   **Enhanced PDF Ingestion**: New `PyMuPDF` integration for accurate text extraction from complex, multi-column PDFs.
*   **Dynamic Memory Slots**: Create unlimited, isolated knowledge bases without data overlap.
*   **Import / Export**: Portable knowledge slots (Vectors + Files).

## Architecture

The system is composed of two isolated microservices:

1.  **Backend Node (The Core):**
    *   **FastAPI:** High-performance async API.
    *   **LangChain:** RAG logic orchestration.
    *   **ChromaDB:** Local vector persistence (Embeddings).
    *   **OpenAI GPT-4/3.5:** Generative intelligence.

2.  **Frontend Node (The Interface):**
    *   **Streamlit:** Reactive UI for document ingestion and chat.
    *   **Dynamic SVG Generation:** JIT asset creation for branding.

## Quick Start

### Prerequisites
*   Docker & Docker Compose
*   OpenAI API Key

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/davidmartimar/nexus-rag-api.git
    cd nexus-rag-api
    ```

2.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=sk-your-key-here
    NEXUS_API_KEY=sk-your-secure-internal-key
    ```
    > **Note:** Access `setup_secrets.py` to configure the Frontend Login Password.

3.  **Ignition**
    Launch the cluster:
    ```bash
    docker-compose up --build
    ```

4.  **Access**
    *   **Frontend UI:** `http://localhost:8501` (Login Required)
    *   **Backend Swagger:** `http://localhost:8000/docs` (API Key Required)

## n8n Integration Guide

To connect n8n to NEXUS, use the **HTTP Request** node:

*   **Method:** `POST` / `GET`
*   **URL:** `http://your-nexus-host:8000/api/v1/...`
*   **Headers:**
    *   `X-NEXUS-KEY`: `[Value of NEXUS_API_KEY]`

## Usage Guide

### Managing Memory Slots
*   Use the **Sidebar** to switch between active Memory Slots.
*   Go to **Advanced Options** to Rename, Create, or Delete slots.

### Ingestion & Chat
*   Drag & Drop documents into the uploader.
*   Wait for the "Knowledge is Ready" green indicator.
*   Chat with the active Memory Slot. The context provided is strictly limited to the selected slot.

### Backup & Portability
*   Navigate to **Advanced Options > Export/Import**.
*   Click **Export** to download a full snapshot of the current Memory Slot.
*   Use **Import** to restore knowledge from a previous export zip file.

## Project Structure

```text
nexus-rag-api/
├── backend/            # FastAPI Service
│   ├── app/
│   │   ├── api/        # Endpoints (Admin, Chat, Ingest)
│   │   ├── services/   # RAG Logic, Vector Store & Import/Export
│   │   └── core/       # Config & Constants
├── frontend/           # Streamlit Service
│   ├── app/
│   │   └── main.py     # UI Logic, State Management & Animations
├── docker-compose.yml  # Orchestration & Volume Persistence
└── README.md
```

## License

This project is open-source and available under the [MIT License](LICENSE).
Built by **David Martínez Martín** (davidmartimar).
