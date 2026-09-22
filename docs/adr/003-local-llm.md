# ADR 003: Local LLM Provider

## Status
Accepted

## Context
CloudRAG needs an LLM provider for generating grounded answers from retrieved document context. The project requires:
- Local-first operation for offline/private use
- No API keys or cloud dependencies for default setup
- Support for multilingual generation
- Provider abstraction for future cloud options

## Decision
Use Ollama as the default local LLM provider with a factory pattern for future cloud provider expansion.

### Ollama Configuration
- **Default Model**: `qwen3:8b` (or `qwen2.5-coder:14b` for development)
- **API**: HTTP REST API on `http://localhost:11434`
- **Protocol**: Ollama-compatible REST API
- **Timeout**: 120 seconds (configurable)
- **Provider Pattern**: Base LLMProvider class with LocalOllamaProvider implementation

## Rationale

### Ollama Advantages
- **Local operation**: Runs entirely on user's machine
- **No API keys**: No credential management needed
- **No cost**: Free to use with hardware you own
- **Model variety**: Many models available (Qwen, Llama, Mistral, etc.)
- **Privacy**: No data leaves the local machine
- **Simple setup**: Single command install

### Model Selection (qwen3:8b)
- **Size**: 8B parameters, reasonable for consumer hardware
- **Performance**: Good multilingual capabilities
- **License**: Permissive license for most use cases
- **Memory**: ~8GB VRAM needed for full precision

### Provider Pattern Benefits
- **Extensibility**: Easy to add Azure OpenAI, Anthropic, etc.
- **Testing**: Can mock LLM for unit tests
- **Flexibility**: Users can choose provider via configuration
- **Consistency**: Same interface across providers

## Alternatives Considered

### OpenAI API
- **Pros**: High quality, reliable, multilingual
- **Cons**: Requires API key, cost per token, cloud-only
- **Rejected**: Conflict with local-first requirement

### Anthropic Claude
- **Pros**: Excellent quality, long context
- **Cons**: API key, cost, cloud-only
- **Rejected**: Same as above

### Local LLM via llama.cpp
- **Pros**: Direct control, many models
- **Cons**: Requires manual model management, more complex
- **Rejected**: Ollama provides better abstraction

### Azure OpenAI
- **Pros**: Good for Azure deployments, managed service
- **Cons**: Cloud-only, requires Azure subscription
- **Rejected**: Not suitable for local-first default

## Consequences

### Positive
- Users can run CloudRAG entirely offline
- No API costs or key management
- Privacy-preserving (no data leaves local machine)
- Easy to upgrade to cloud providers when needed
- Consistent interface across providers

### Negative
- Requires local hardware with sufficient RAM/VRAM
- Model quality may lag behind state-of-the-art cloud models
- Inference speed depends on local hardware
- Ollama must be installed and running separately

### Mitigations
- Clear documentation on hardware requirements
- Recommended models for different hardware capabilities
- Provider factory makes cloud migration straightforward
- Health checks detect when Ollama is unavailable

## Related Decisions
- ADR 001: Vector Store Selection
- ADR 002: Multilingual Embeddings
- ADR 005: Security Model
