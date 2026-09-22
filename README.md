# CloudRAG

CloudRAG is a production-grade, multilingual Retrieval-Augmented Generation (RAG) document assistant built as a full-stack portfolio project. Users can upload documents, extract and chunk their content, generate embeddings, perform semantic search, and ask grounded questions with source citations using a local or cloud-capable LLM provider.

The project demonstrates modern AI application engineering through a complete generative AI workflow: document ingestion, vector search, retrieval-grounded generation, observability, security, evaluation, and deployment readiness.

## Features

- **Multilingual document ingestion**: Support for PDF, DOCX, TXT, and Markdown files with validation and security checks
- **Local-first RAG workflow**: Built around local FAISS vector store with optional Qdrant Cloud integration
- **Grounded answers**: LLM responses are constrained to retrieved document content with abstention for low-confidence queries
- **Rich citations**: Source metadata includes filename, page numbers, chunk indices, and relevance scores
- **Idempotent indexing**: Document re-indexing is safe and prevents duplicate vectors
- **Cache invalidation**: Retrieval cache is automatically invalidated on document changes
- **Security-focused**: Upload validation, filename sanitization, prompt injection protection, and secret management
- **Observability**: Structured logging with request IDs, health/readiness endpoints, and security headers
- **Evaluation framework**: Retrieval quality metrics (Hit@K, keyword matching) and adversarial testing
- **Docker deployment**: Production-ready Docker Compose configuration with health checks
- **Azure deployment**: Azure Container Apps deployment with managed identity authentication

## Architecture

The core execution path:

```text
Frontend (React + Vite)
    ↓
FastAPI API
    ↓
Document Processing (validation → extraction → chunking)
    ↓
SentenceTransformer Embeddings (multilingual)
    ↓
Vector Search (FAISS local / Qdrant Cloud)
    ↓
Context Construction (relevance filtering, citation metadata)
    ↓
LLM Generation (Ollama local / extensible cloud providers)
    ↓
Grounded Answer + Rich Citations
```

### Components

- **Frontend**: React + Vite with Axios for API communication
- **Backend**: FastAPI + Pydantic + SQLAlchemy (SQLite) + Uvicorn
- **Embeddings**: SentenceTransformers multilingual model (paraphrase-multilingual-MiniLM-L12-v2)
- **Vector Store**: FAISS local adapter and Qdrant Cloud adapter with provider abstraction
- **LLM Provider**: Ollama local provider with factory pattern for cloud provider expansion
- **Document Processing**: PyMuPDF (PDF), python-docx (DOCX), custom chunking with page mapping
- **Evaluation**: Custom metrics (Hit@K, keyword match, retrieval quality) and dataset runner

## Technology Stack

### Backend
- Python 3.12+
- FastAPI with Pydantic Settings
- SQLAlchemy + SQLite for metadata persistence
- Uvicorn ASGI server
- Qdrant Python client (optional cloud vector store)
- Structlog for structured logging

### Frontend
- React 19
- Vite 8
- Axios for HTTP requests
- CSS Modules for styling

### AI and Retrieval
- SentenceTransformers multilingual embeddings
- FAISS CPU-optimized vector search
- Qdrant Cloud vector store adapter
- Ollama local LLM provider
- Custom chunking with page number preservation

### Document Processing
- PDF extraction with page boundary detection
- DOCX paragraph extraction
- TXT/Markdown processing with validation
- Security-focused file validation (path traversal, suspicious content, ZIP bombs)

## Project Structure

```text
CloudRAG/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes (documents, health, RAG)
│   │   ├── config.py       # Environment configuration
│   │   ├── db/             # Database setup and session management
│   │   ├── models/         # SQLAlchemy models (Document)
│   │   ├── providers/      # LLM provider abstraction
│   │   ├── rag/            # RAG pipeline (chunking, embeddings, vector store)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (document processing, repository)
│   │   └── main.py         # FastAPI application entry point
│   ├── tests/             # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/                # Vite + React UI
│   ├── src/
│   │   ├── components/     # React components (chat, documents, sources)
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API client
│   │   └── App.jsx         # Main application component
│   └── package.json
├── data/                   # Runtime data (documents, index, database)
├── docs/                   # Architecture and deployment documentation
├── evaluation/             # Evaluation framework and datasets
├── deploy/                 # Deployment configurations
│   ├── docker/           # Dockerfiles
│   └── azure/            # Azure Container Apps deployment
├── .github/workflows/      # CI/CD pipeline
└── compose.yml             # Docker Compose configuration
```

## Configuration

The backend uses environment-driven configuration from `backend/.env`:

### Core Settings
- `APP_NAME`: Application name (default: CloudRAG)
- `ENVIRONMENT`: Environment (development/production)
- `CORS_ORIGINS`: Comma-separated allowed origins
- `TRUSTED_HOSTS`: Comma-separated trusted hostnames

### LLM Configuration
- `LLM_PROVIDER`: LLM provider (local)
- `OLLAMA_BASE_URL`: Ollama API URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model name (default: qwen3:8b)
- `OLLAMA_TIMEOUT_SECONDS`: Request timeout (default: 120)

### Vector Store Configuration
- `VECTOR_STORE`: Vector store backend (faiss/qdrant)
- `QDRANT_URL`: Qdrant Cloud URL (when using qdrant)
- `QDRANT_API_KEY`: Qdrant API key (when using qdrant)
- `QDRANT_COLLECTION`: Qdrant collection name (default: cloudrag)

### RAG Parameters
- `MAX_UPLOAD_SIZE_MB`: Maximum upload size (default: 10)
- `MIN_RETRIEVAL_SCORE`: Minimum relevance threshold (default: 0.30)
- `MAX_RAG_CONTEXT_CHARACTERS`: Maximum context length (default: 12000)

## Local Development Setup

### 1. Clone and create environment

```powershell
cd CloudRAG
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### 2. Configure environment

```powershell
cd backend
copy .env.example .env
# Edit .env with your configuration
```

### 3. Start the backend

```powershell
cd backend
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 4. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and the backend API at `http://localhost:8001`.

## Docker Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) Ollama running locally: `ollama pull qwen3:8b`

### Build and run

```powershell
docker compose up --build -d
docker compose ps
```

The application will be available at:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Stop the application

```powershell
docker compose down
```

## Testing

### Backend tests

```powershell
cd backend
python -m pytest tests -v
```

The test suite includes:
- Unit tests for chunking, validation, and utilities
- Integration tests for document lifecycle and RAG pipeline
- Security tests for malicious uploads and prompt injection
- Quality tests for retrieval accuracy and cache behavior

### Frontend lint and build

```powershell
cd frontend
npm run lint
npm run build
```

### Evaluation

Run the evaluation framework to measure retrieval quality:

```powershell
cd evaluation
python evaluator.py
```

The evaluation measures:
- Hit@1, Hit@3, Hit@5 retrieval accuracy
- Keyword match rate for answer quality
- Retrieval failure detection
- Question-level pass/fail classification

## Security

CloudRAG implements multiple security layers:

### Upload Validation
- Filename sanitization (path traversal, invalid characters, dangerous extensions)
- File content validation (magic bytes, archive limits, encoding checks)
- Size limits (max 10MB default, configurable)
- Suspicious content detection (repetitive characters, null bytes)

### Application Security
- CORS origin configuration
- Trusted host middleware
- Security headers (X-Content-Type-Options, X-Frame-Options, CSP)
- Request ID correlation for debugging

### RAG Security
- Prompt injection protection (document content treated as text, not instructions)
- Secret request handling (LLM instructed to refuse secret disclosure)
- Grounded responses (LLM constrained to retrieved context)
- Abstention behavior (refuses to answer when confidence is low)

### Secret Management
- No hardcoded credentials in source code
- Environment-based configuration
- `.env` files ignored by git
- Secret scanning in CI/CD pipeline

## Observability

### Logging
- Structured logging with structlog
- Request ID correlation across all logs
- Key events logged: document upload, indexing, retrieval, errors
- No sensitive data logged (no API keys, passwords, document contents)

### Health Checks
- `/api/health`: Lightweight application health check
- `/api/ready`: Dependency health check (database, vector store, embedding provider, LLM provider)

### Metrics
- Retrieval metrics (Hit@K, relevance scores)
- Document lifecycle metrics (upload, index, delete)
- Error rates and types

## Deployment

### Docker Compose
Production-ready Docker Compose configuration with:
- Health checks for both services
- Volume mounts for data persistence
- Non-root user execution
- Environment configuration

### Azure Container Apps
See `deploy/azure/README.md` for Azure deployment instructions.

The Azure deployment includes:
- Azure Container Registry for private images
- Managed identity authentication (no passwords in code)
- Optional Azure Files for persistent storage
- Container Apps with auto-scaling

## Evaluation

The evaluation framework provides automated quality measurement:

### Metrics
- **Hit@K**: Whether relevant content appears in top K results
- **Keyword Match Rate**: Answer quality based on expected keywords
- **Retrieval Failures**: Queries with no relevant results
- **Pass/Fail**: Per-question classification

### Running Evaluation

```powershell
cd evaluation
python evaluator.py --document evaluation_document.txt --dataset questions.json
```

### Datasets
- `evaluation_document.txt`: Canonical evaluation corpus
- `questions.json`: 20 questions with expected keywords
- `multilingual_document.txt`: Multilingual test document
- `multilingual_questions.json`: Cross-language test questions

## Development Guidelines

### Code Quality
- Follow existing code style and patterns
- Add docstrings to public classes and functions
- Write tests for new features
- Use type annotations where useful
- Keep functions focused and composable

### Testing Strategy
- Unit tests for individual components
- Integration tests for cross-component workflows
- Security tests for attack vectors
- Regression tests for bug fixes
- End-to-end tests for critical user journeys

### Commit Guidelines
- Use meaningful commit messages
- One logical change per commit
- Test before committing
- Update documentation for user-facing changes

## Troubleshooting

### Backend fails to start
- Check Python version (3.12+ required)
- Verify dependencies are installed: `pip install -r backend/requirements.txt`
- Check database permissions: `data/` directory must be writable

### Ollama unavailable
- Verify Ollama is running: `ollama list`
- Check Ollama model is available: `ollama pull qwen3:8b`
- Verify `OLLAMA_BASE_URL` configuration

### Frontend build fails
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version (22+ recommended)
- Verify no TypeScript errors

### Docker issues
- Verify Docker is running: `docker ps`
- Check port conflicts (8000, 8080)
- Review Docker logs: `docker compose logs`

## Contributing

This is a portfolio project demonstrating RAG engineering. For suggestions or issues, please refer to the project repository.

## License

This project is provided as-is for educational and portfolio demonstration purposes.
