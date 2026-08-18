\# CloudRAG AI



A multilingual document-grounded AI assistant built around Retrieval-Augmented Generation (RAG).



\## Project Goals



\- Document ingestion

\- Semantic search

\- Multilingual retrieval

\- Grounded LLM responses

\- Source citations

\- Local-first development

\- Optional Azure OpenAI integration

\- Cost-controlled cloud deployment



\## Architecture



Next.js

↓

FastAPI

↓

Document Processing

↓

Embeddings

↓

FAISS

↓

RAG

↓

LLM Provider

├── Local

└── Azure OpenAI



\## Development Strategy



The application is developed locally first to minimize cloud costs.



Azure OpenAI is an optional LLM provider and is not required for local development.



\## Current Status



\- \[x] Project initialization

\- \[x] Python environment

\- \[x] FastAPI backend

\- \[x] Health endpoint

\- \[x] Backend tests

\- \[ ] Document ingestion

\- \[ ] Chunking

\- \[ ] Embeddings

\- \[ ] FAISS

\- \[ ] Local RAG

\- \[ ] Local LLM

\- \[ ] Multilingual evaluation

\- \[ ] Azure OpenAI

\- \[ ] Frontend

\- \[ ] Deployment

