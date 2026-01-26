# ネ NEXUS: Enterprise RAG Knowledge Engine

**NEXUS** is a production-ready, "Pure RAG" system designed for secure enterprise document ingestion, intelligent querying, and automated evaluation. It features a microservices architecture fully containerized with Docker, featuring **Dynamic Memory Slots** and **Scientific Performance Metrics**.

![Status](https://img.shields.io/badge/Status-Production-success)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Python](https://img.shields.io/badge/Python-3.10-yellow)
![Ragas](https://img.shields.io/badge/AI_Eval-RAGAS-orange)
![License](https://img.shields.io/badge/License-MIT-green)

## Key Features v5.0 (Clean Architecture)

* **Enterprise Security**:
    * **Frontend Gateway**: Simple yet effective password protection for the UI.
    * **API Shield**: Backend endpoints protected by `X-NEXUS-KEY` header, ready for n8n/Make integration.
* **CI/CD for AI (RAGAS)**: Integrated evaluation pipeline to measure *Faithfulness*, *Context Precision*, and *Answer Relevance* using synthetic test sets.
* **Dynamic Memory Slots**: Create unlimited, isolated knowledge bases (Collections) without data overlap. Perfect for managing multiple clients or departments (e.g., HR vs. Finance).
* **Advanced Ingestion**: Powered by `PyMuPDF` to accurately parse complex layouts, multi-column PDFs, and tables.
* **Contextual Memory**: "Sliding Window" conversation memory (last 5 exchanges) for natural follow-up questions.
* **Knowledge Portability**: Full Import/Export capabilities to move "Brains" (Vectors + Source Files) between environments.

## Architecture

The system follows a **Microservices** pattern, decoupling logic from the interface:

| Component | Tech Stack | Role |
| :--- | :--- | :--- |
| **The Brain (Backend)** | **FastAPI** + **LangChain** | Async API handling RAG logic and LLM orchestration (OpenAI GPT-4). |
| **The Memory (Store)** | **ChromaDB** | Persistent local vector storage with Docker Volume persistence. |
| **The Eyes (Ingest)** | **PyMuPDF** | High-fidelity document parsing and chunking strategies. |
| **The Face (Frontend)** | **Streamlit** | Reactive UI for chat, ingestion, and slot management. |
| **The Judge (Eval)** | **Ragas** | Automated quality assurance framework. |

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
    NEXUS_API_KEY=sk-your-secure-internal-key
    ```
    *Note: The system includes a `setup_secrets.py` script to help configure the Frontend password securely.*

3.  **Ignition**
    Launch the cluster:
    ```bash
    docker-compose up --build
    ```

4.  **Access**
    * **Frontend UI:** `http://localhost:8501` (Login Required)
    * **API Docs:** `http://localhost:8000/docs` (Protected)

## n8n / Automation Integration

NEXUS is built to be the "Brain" of your automation workflows. Connect it using the **HTTP Request** node in n8n:

* **Method:** `POST`
* **URL:** `http://your-nexus-host:8000/api/v1/chat`
* **Headers:** `X-NEXUS-KEY: [Your Key]`
* **Body:**
    ```json
    {
      "query": "Analyze this CV against the job description...",
      "collection_name": "nexus_slot_hr_department"
    }
    ```

## Performance Evaluation

To run the scientific quality assessment:

1.  Access the backend container.
2.  Trigger the evaluation endpoint (or run the script):
    ```bash
    POST /api/v1/evaluate/run
    ```
3.  The system will generate synthetic questions based on your documents and grade the answers.

## Project Structure

```text
nexus-rag-api/
├── backend/            # FastAPI Microservice
│   ├── app/
│   │   ├── api/        # Endpoints (Chat, Ingest, Eval)
│   │   ├── services/   # Business Logic (RAG, Chroma, Ragas)
│   │   └── core/       # Auth & Config
│   └── Dockerfile
├── frontend/           # Streamlit Microservice
│   ├── app/main.py     # UI & State Logic
│   └── Dockerfile
├── docker-compose.yml  # Orchestration & Volumes
└── README.md

## Author & License

**David Martínez** - *AI Automation Engineer*
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/davidmartimar)
[![GitHub](https://img.shields.io/badge/GitHub-davidmartimar-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/davidmartimar)

Built for Barnalytics. Open source under the MIT License.
