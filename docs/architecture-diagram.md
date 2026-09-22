# CloudRAG Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Browser / Client                            │
│                     React + Vite Frontend                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend                              │
│                     (Uvicorn ASGI Server)                             │
├──────────────────────────────┬──────────────────────────────────────┤
│                           Security Middleware                          │
│  • CORS validation         │  • Trusted Host                             │
│  • Security headers        │  • Request ID middleware                    │
└──────────────────────────────┴──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API Routes Layer                                │
│  ├─ /api/documents        │  Document upload, list, delete            │
│  ├─ /api/rag              │  Search, ask, index, stats                 │
│  └─ /api/health           │  Health check, readiness check              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Document Processing Pipeline                         │
│  ├─ File Validation       │  Filename sanitization, content checks    │
│  ├─ Extraction            │  PDF (PyMuPDF), DOCX (python-docx), TXT    │
│  ├─ Chunking              │  Overlapping chunks with page mapping     │
│  └─ Metadata Storage     │  SQLite database (Document model)      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Embedding Generation                            │
│              SentenceTransformers (multilingual)                       │
│                    paraphrase-multilingual-MiniLM-L12-v2               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Vector Store Layer                                │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  FAISS (Local)              │  Qdrant Cloud (Optional)        │  │
│  │  • CPU-optimized index       │  • Remote vector database      │  │
│  │  • On-disk persistence       │  • Managed scalability       │  │
│  │  • Deterministic UUIDs        │  • Cloud availability       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Retrieval Pipeline                                  │
│  ├─ Search Query          │  Query embedding generation         │
│  ├─ Vector Search          │  Top-K retrieval with scoring        │
│  ├─ Relevance Filtering    │  Minimum score threshold          │
│  ├─ Cache Management      │  LRU cache with invalidation      │
│  └─ Citation Metadata     │  Page numbers, filenames, scores   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LLM Provider Layer                                │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Ollama (Local)              │  Future: Azure OpenAI, etc.   │  │
│  │  • Local inference           │  • Cloud API integration    │  │
│  │  • HTTP API                  │  • Provider factory pattern   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Response Generation                               │
│  ├─ Context Construction  │  Assemble retrieved chunks        │
│  ├─ System Prompting       │  Grounded generation instructions │
│  ├─ Answer Generation     │  LLM generates response        │
│  └─ Citation Assembly     │  Add source metadata           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Response                                    │
│  ├─ Grounded Answer       │  Based on retrieved context only  │
│  ├─ Rich Citations        │  [1] filename.pdf — Page 12    │
│  ├─ Abstention Handling    │  "Not enough information..."   │
│  └─ Request ID            │  Correlation for debugging     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Document Upload

```
User Upload → Validation → Extraction → Chunking → Embedding → Vector Storage → Database Metadata
     ↓           ↓           ↓           ↓          ↓              ↓              ↓
 File        Security     PDF/DOCX    Page       Sentence      FAISS/        SQLite
 Check       Checks      Text       Mapping    Transformers  Index        Document
                                                           Vectors        Model
```

## Data Flow: Question Answering

```
User Question → Query Embedding → Vector Search → Relevance Filter → Context Construction → LLM Generation → Citations
      ↓              ↓                ↓                ↓                    ↓                ↓              ↓
  Query       Sentence        FAISS/           Minimum            Retrieved        Ollama         Source
  Text        Transformer    Qdrant           Score              Chunks         Local          Metadata
```

## Persistence Layer

```
/data/
├── documents/           # Original uploaded files
├── index/               # FAISS index files (cloudrag.index, metadata.json)
├── processed/           # Extracted text files
└── cloudrag.db          # SQLite database (documents table)
```

## Deployment Architecture

```
Development:
  → Local Python environment
  → Ollama local
  → SQLite database
  → FAISS local index

Docker:
  → Backend container (FastAPI + Uvicorn)
  → Frontend container (Nginx + React build)
  → Volume mounts for persistence
  → Health checks

Azure:
  → Azure Container Registry (private images)
  → Azure Container Apps (managed environment)
  → Managed Identity (ACR pull, no passwords)
  → Azure Files (optional persistence)
  → Ollama (not deployed - architecture note in docs)
```

## Security Architecture

```
Input Validation:
  → Filename sanitization (path traversal, invalid chars)
  → File type validation (magic bytes, archive structure)
  → Size limits (10MB default)
  → Content checks (null bytes, encoding, suspicious patterns)

Application Security:
  → CORS configuration (whitelisted origins)
  → Trusted Host middleware (allowed hostnames)
  → Security headers (CSP, X-Frame-Options, etc.)
  → Request ID correlation (debugging)

RAG Security:
  → Prompt injection protection (content ≠ instructions)
  → Secret request handling (LLM refuses disclosure)
  → Grounded responses (constrained to context)
  → Abstention (low confidence → refusal)

Infrastructure Security:
  → No hardcoded credentials
  → Environment-based configuration
  → .env files ignored by git
  → CI/CD secret scanning
  → Non-root Docker execution
  │
```
