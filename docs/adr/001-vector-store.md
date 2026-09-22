# ADR 001: Vector Store Selection

## Status
Accepted

## Context
CloudRAG needs a vector store for semantic search of document chunks. The project requires:
- Local-first operation for offline/private use
- Optional cloud deployment path for scalability
- Efficient storage and retrieval of embeddings
- Support for multilingual embeddings (384 dimensions)

## Decision
Use FAISS as the primary local vector store with Qdrant Cloud as an optional cloud alternative via a provider abstraction.

### FAISS Configuration
- **Index Type**: IndexFlatIP (inner product for cosine similarity)
- **Persistence**: On-disk index files (`cloudrag.index`, `metadata.json`)
- **Deterministic IDs**: Document-based UUIDs for idempotent operations
- **Location**: `data/index/` directory

### Qdrant Configuration
- **Provider**: qdrant-client Python library
- **Deployment**: Optional cloud service via environment variables
- **Collection**: Configurable collection name (`cloudrag` default)
- **Distance Metric**: Cosine similarity
- **ID Strategy**: UUIDv5 based on chunk_id for deterministic upserts

## Rationale

### FAISS Advantages
- **Local operation**: No external dependencies, works offline
- **Performance**: CPU-optimized, no network latency
- **Cost**: No infrastructure costs
- **Simplicity**: Minimal setup, no service management
- **Control**: Complete control over index lifecycle

### Qdrant Advantages
- **Scalability**: Cloud-native, handles large datasets
- **Persistence**: Managed storage, no manual backup
- **Features**: Built-in filtering, replication, monitoring
- **API**: RESTful API with client libraries

### Abstraction Benefits
- **Flexibility**: Easy to switch between local and cloud
- **Testing**: Can mock vector store for unit tests
- **Future-proof**: Easy to add other providers (Pinecone, Weaviate, etc.)

## Alternatives Considered

### Pinecone
- **Pros**: Fully managed, excellent performance
- **Cons**: Requires API key, only cloud option, cost
- **Rejected**: Would require cloud-only deployment

### Weaviate
- **Pros**: Open-source with managed option, good features
- **Cons**: More complex than needed, requires Docker for local
- **Rejected**: Overkill for local-first requirements

### Milvus
- **Pros**: Powerful, open-source, scalable
- **Cons**: Complex setup, requires separate service
- **Rejected**: Too complex for local-first needs

## Consequences

### Positive
- Users can run CloudRAG entirely offline with FAISS
- Cloud deployment path exists for when needed
- Codebase has clean provider abstraction
- Tests can run without external dependencies

### Negative
- Two vector store implementations to maintain
- Index file format changes could break compatibility
- Qdrant Cloud requires paid account for production use

### Mitigations
- Index metadata includes model name and dimension for compatibility checks
- Qdrant is optional, FAISS works as default
- Clear documentation on when to use each option

## Related Decisions
- ADR 002: Multilingual Embeddings
- ADR 003: Local LLM Provider
