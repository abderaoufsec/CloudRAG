# Architecture

CloudRAG is a small, local-first application. React/Vite provides the document
and chat experience. FastAPI owns validation, storage, retrieval, and LLM access,
so the browser never accesses model configuration or future credentials.

```text
React UI -> /api/documents -> extraction -> chunks -> embeddings -> FAISS
React UI -> /api/rag/ask -> embeddings -> FAISS -> confidence filter
                                              -> bounded context -> provider -> answer
```

SQLite holds document metadata. `data/documents` contains original uploads,
`data/processed` has extracted UTF-8 text, and `data/index` contains FAISS and
chunk metadata. Compose persists all of these through one `./data` bind mount.

The multilingual embedding model supports cross-language retrieval. The RAG
pipeline cannot invoke an LLM without chunks above `MIN_RETRIEVAL_SCORE`; it caps
evidence with `MAX_RAG_CONTEXT_CHARACTERS` and returns retrieved chunks as sources.
