# CloudRAG

CloudRAG is a multilingual, local-first Retrieval-Augmented Generation (RAG) document assistant built as a full-stack portfolio project. Users can upload documents, extract and chunk their content, generate embeddings, perform semantic search, and ask grounded questions through a local or cloud-capable LLM provider.

The project combines a FastAPI backend, a Vite + React frontend, a persistent SQLite metadata layer, multilingual SentenceTransformer embeddings, a FAISS local vector index, and an optional Qdrant Cloud vector-store path. The project is designed to show a complete generative AI application workflow from document ingestion to retrieval, question answering, source tracking, evaluation, and deployment-ready configuration.

## Why this project exists

CloudRAG demonstrates how to build a practical knowledge assistant that answers questions from a user’s uploaded documents while keeping the answer grounded in retrieved evidence. The main design goal is to build a retrieval pipeline that is useful for private and offline-first document knowledge bases, while still leaving a clear upgrade path toward cloud vector storage and managed LLM providers.

This repository is structured as a portfolio-grade demonstration of software engineering, backend API development, vector search integration, document processing, frontend user experience, and production deployment thinking.

## Project highlights

- Multilingual document ingestion and semantic retrieval
- Local-first RAG workflow with optional cloud vector storage
- FAISS and Qdrant vector-store support via a common abstraction
- FastAPI API with document upload, indexing, search, and chat routes
- Provider abstraction for local Ollama and optional cloud LLM providers
- Security middleware, trusted-host controls, and CORS settings
- Search caching for repeated retrieval workloads
- Docker Compose deployment workflow
- Evaluation utilities for retrieval quality measurement

## Architecture

The core execution path is:

```text
Frontend (React/Vite)
    -> FastAPI API
    -> Document parsing and chunking
    -> SentenceTransformer embeddings
    -> Vector search (FAISS locally or Qdrant Cloud)
    -> LLM generation with retrieved context
    -> Answer + source citations returned to the UI
```

The repository includes the following major runtime components:

- Frontend: React + Vite
- Backend: FastAPI + Pydantic + Uvicorn
- Metadata: SQLite + SQLAlchemy
- Embeddings: SentenceTransformers multilingual model
- Vector store: FAISS local adapter and Qdrant Cloud adapter
- LLM provider: Ollama local provider, with provider architecture in place for future expansion

## Technology stack

### Backend

- Python 3.12+
- FastAPI
- Pydantic + Pydantic Settings
- SQLAlchemy / SQLite
- Uvicorn
- Qdrant Python client

### Frontend

- React
- Vite
- JavaScript / JSX
- CSS styling

### AI and retrieval

- SentenceTransformers multilingual embeddings
- FAISS vector store
- Qdrant Cloud vector store adapter
- Ollama local LLM provider

### Document processing

- PDF extraction support
- TXT and DOCX ingestion support
- Chunk generation and controlled context retrieval

## Features

- Upload and index PDF, TXT, and DOCX documents
- Chunk text into retrieval-friendly passages
- Vectorize chunk text for semantic search
- Search documents by query with optional document-scoping
- Generate grounded answers using retrieved evidence only
- Return source metadata and evidence chunks to the frontend
- Support multilingual English, French, and Arabic retrieval patterns
- Support both local and cloud vector-store execution environments
- Provide endpoints for API testing and backend health verification
- Add evaluation and quality scoring utilities for retrieval evaluation

## Project structure

```text
CloudRAG/
├── backend/                 # FastAPI application
│   ├── app/                 # application modules
│   ├── tests/              # backend tests
│   └── requirements.txt    # backend dependencies
├── frontend/                # Vite + React UI
├── data/                    # documents, vector index, and metadata
├── docs/                    # architecture, security, provider, deployment docs
├── evaluation/              # evaluator and sample datasets
├── deploy/                  # Azure deployment scripts and Bicep infra
└── compose.yml              # local Docker Compose configuration
```

## Configuration

The backend uses environment-driven configuration from the settings object in the backend application. The project supports the following configuration model:

- LLM provider: Ollama local provider
- Embedding provider: local SentenceTransformers
- Vector store: FAISS by default, Qdrant when selected
- Qdrant cluster variables:
  - QDRANT_URL
  - QDRANT_API_KEY
  - QDRANT_COLLECTION
  - VECTOR_STORE=qdrant

The repository expects the backend configuration file to live under the backend folder. The project includes environment examples for a local developer setup.

## Local development setup

### 1. Clone and create the environment

```powershell
cd CloudRAG
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### 2. Start the backend

From the repository root:

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 3. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend should be reachable through the Vite development server, and the backend API will be served through the Uvicorn process.

## Docker quick start

The repository includes a Compose file that can be used for a local deployment demonstration:

```powershell
ollama pull qwen3:8b
docker compose up --build -d
docker compose ps
```

The frontend is usually exposed through the Docker Compose stack while the backend health and API docs are served through the FastAPI app routes.

## Production and cloud integration notes

Qdrant Cloud integration is supported by a dedicated vector-store adapter. The cloud path is controlled through environment variables and a provider abstraction that allows the backend runtime to change the vector store strategy without redesigning the retrieval system.

The backend currently supports:

- Local FAISS vector-store mode
- Qdrant Cloud vector-store mode via the QdrantClient adapter

The collection shape for the cloud path should align with the embedding dimension used by the project and use cosine distance for semantic search.

## Testing and evaluation

The project includes automated backend tests and an evaluation harness. They can be run locally with:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

The evaluation workflow measures retrieval quality and allows the repository to test hits across different retrieval thresholds.

## Security and reliability

The project includes security-oriented primitives such as:

- CORS origin configuration
- Trusted-host configuration
- Request and response security model
- Provider isolation
- A structured route layer for RAG indexing, search, and answer generation

## Limitations

This project is a local-first RAG prototype and portfolio project, not a full enterprise multi-tenant SaaS. The current design is intentionally simple and focused on the core system pipeline. It is best viewed as an implementation demonstration of vector search, retrieval-grounded answers, and cloud-vector store adaptation.

## Documentation

For deeper technical details, see:

- [docs/architecture.md](docs/architecture.md)
- [docs/local-deployment.md](docs/local-deployment.md)
- [docs/security.md](docs/security.md)
- [docs/providers.md](docs/providers.md)
- [deploy/azure/README.md](deploy/azure/README.md)

## Repository purpose

CloudRAG is a portfolio-style project that presents modern AI application engineering in a real codebase:

- API-first backend design
- Retrieval-grounded generation
- Docker deployment style
- AI provider abstraction
- Cloud vector-store integration path
- Evaluation and testing discipline

The repository is suitable as a showcase for building a document intelligence assistant from ingestion through retrieval, generation, and deployment readiness.
