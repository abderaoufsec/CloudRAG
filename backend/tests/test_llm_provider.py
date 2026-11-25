import pytest

from app.config import Settings
from app.providers.base import LLMProviderError
from app.providers.factory import get_llm_provider
from app.providers.ollama import LocalOllamaProvider


def _provider(monkeypatch, content):
    provider = LocalOllamaProvider(
        Settings(llm_provider="local")
    )
    monkeypatch.setattr(
        provider.client,
        "chat",
        lambda **_kwargs: {
            "message": {"content": content}
        },
    )
    return provider


def test_generate_strips_think_blocks(monkeypatch):
    provider = _provider(
        monkeypatch,
        "<think>hidden reasoning</think>The answer is 42.",
    )

    answer = provider.generate(
        question="question",
        context="context",
    )

    assert answer == "The answer is 42."


def test_generate_strips_think_blocks_with_whitespace(monkeypatch):
    provider = _provider(
        monkeypatch,
        "<think>a</think>\n\n  Final answer.  ",
    )

    answer = provider.generate(
        question="question",
        context="context",
    )

    assert answer == "Final answer."


def test_generate_raises_when_only_reasoning_remains(monkeypatch):
    provider = _provider(
        monkeypatch,
        "<think>only reasoning</think>",
    )

    with pytest.raises(LLMProviderError):
        provider.generate(
            question="question",
            context="context",
        )


def test_factory_returns_the_local_ollama_provider():
    provider = get_llm_provider(Settings(llm_provider="local"))

    assert provider.__class__.__name__ == "LocalOllamaProvider"


def test_factory_rejects_unimplemented_cloud_provider():
    with pytest.raises(LLMProviderError, match="Unsupported LLM_PROVIDER"):
        get_llm_provider(Settings(llm_provider="cloud"))
