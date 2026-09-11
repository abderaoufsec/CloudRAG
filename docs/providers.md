# LLM provider architecture

`app.providers.base.LLMProvider` is the application boundary:

```python
generate(question: str, context: str) -> str
```

`LocalOllamaProvider` is the current implementation. It reads its URL, model, and
timeout from settings, sends a grounding prompt and clearly delimited evidence,
and converts connection/model failures into `LLMProviderError`. The API maps this
to a safe HTTP 503 response.

`get_llm_provider()` selects from `LLM_PROVIDER`. Only `local` is implemented.
Adding a future cloud provider needs one implementation and factory branch;
retrieval, citations, storage, and frontend code do not change.
