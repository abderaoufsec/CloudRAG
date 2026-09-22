# ADR 002: Multilingual Embeddings

## Status
Accepted

## Context
CloudRAG supports document search across multiple languages (English, French, Arabic). The embedding model must:
- Support multiple languages without separate models
- Provide reasonable performance for semantic search
- Be compatible with our vector store (384 dimensions preferred)
- Work offline with local models

## Decision
Use SentenceTransformers with the `paraphrase-multilingual-MiniLM-L12-v2` model as the default embedding provider.

### Model Configuration
- **Model Name**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Dimensions**: 384
- **Languages**: 50+ languages including English, French, Arabic
- **Size**: ~420MB
- **Provider**: SentenceTransformers library

## Rationale

### Model Selection
- **Multilingual support**: Single model handles multiple languages
- **Dimensionality**: 384 dimensions balances quality and index size
- **Performance**: Reasonable speed for CPU inference
- **Quality**: Good semantic search performance across languages
- **License**: Apache 2.0, commercial-friendly

### Alternatives Considered

#### OpenAI text-embedding-ada-002
- **Pros**: High quality, multilingual, managed service
- **Cons**: Requires API key, cost per token, cloud-only
- **Rejected**: Conflict with local-first requirement

#### OpenAI text-embedding-3-small
- **Pros**: Newer, better quality, configurable dimensions
- **Cons**: Cloud-only, cost, API dependency
- **Rejected**: Same as above

#### e5-multilingual-base
- **Pros**: Good multilingual performance, open-source
- **Cons**: 768 dimensions (larger index), slower inference
- **Rejected**: Larger index size not justified for this use case

#### LaBSE
- **Pros**: Excellent multilingual alignment
- **Cons**: 768 dimensions, slower inference
- **Rejected**: Trade-off favors MiniLM for this project

## Consequences

### Positive
- Single model handles multiple languages without switching
- Local operation, no API calls or costs
- Reasonable performance on CPU
- Index size manageable (384 dimensions)

### Negative
- Lower dimensional than some alternatives (may reduce fine-grained semantic distinction)
- First download requires ~420MB download
- Inference is CPU-bound (no GPU acceleration configured)

### Mitigations
- Index metadata stores model name to detect incompatibility
- Model can be upgraded in future with migration path
- Documentation on model trade-offs

## Related Decisions
- ADR 001: Vector Store Selection
- ADR 003: Local LLM Provider
