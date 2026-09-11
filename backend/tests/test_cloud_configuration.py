from app.config import Settings
from app.providers.factory import get_llm_provider
from app.providers.ollama import LocalOllamaProvider


def test_cors_origins_are_parsed_from_the_environment_value():
    settings = Settings(cors_origins="https://web.example, https://admin.example")

    assert settings.cors_origin_list == [
        "https://web.example",
        "https://admin.example",
    ]


def test_non_local_deployment_does_not_call_ollama(monkeypatch):
    from app.providers.base import LLMProviderError

    try:
        get_llm_provider(Settings(llm_provider="disabled"))
    except LLMProviderError as exc:
        assert "Unsupported LLM_PROVIDER" in str(exc)
    else:
        raise AssertionError("Unsupported providers must fail clearly.")


def test_local_ollama_uses_configured_host_and_model(monkeypatch):
    captured = {}

    class FakeClient:
        def chat(self, **kwargs):
            captured.update(kwargs)
            return {"message": {"content": "Grounded answer."}}

    settings = Settings(
        ollama_base_url="http://host.docker.internal:11434",
        ollama_model="qwen3:8b",
    )
    provider = LocalOllamaProvider(settings)
    provider.client = FakeClient()

    answer = provider.generate(question="What is CloudRAG?", context="CloudRAG context")

    assert answer == "Grounded answer."
    assert captured["model"] == "qwen3:8b"
