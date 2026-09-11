import pytest

from app.config import Settings
from app.providers.base import LLMProviderError
from app.providers.factory import get_llm_provider


def test_factory_returns_the_local_ollama_provider():
    provider = get_llm_provider(Settings(llm_provider="local"))

    assert provider.__class__.__name__ == "LocalOllamaProvider"


def test_factory_rejects_unimplemented_cloud_provider():
    with pytest.raises(LLMProviderError, match="Unsupported LLM_PROVIDER"):
        get_llm_provider(Settings(llm_provider="cloud"))
