from app.config import Settings, get_settings
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.ollama import LocalOllamaProvider


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Return the configured local provider.

    New cloud providers can be registered here later without changing RAG.
    """

    settings = settings or get_settings()

    if settings.llm_provider == "local":
        return LocalOllamaProvider(settings)

    raise LLMProviderError(
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. "
        "Use 'local'."
    )
