from fastapi.testclient import TestClient

from app.main import app
from app.providers.base import LLMProviderError


def test_ollama_failure_is_returned_as_a_safe_service_error(monkeypatch):
    import app.api.rag as rag_api

    def unavailable(**_kwargs):
        raise LLMProviderError("connection details should not reach the user")

    monkeypatch.setattr(rag_api.rag_pipeline, "ask", unavailable)

    with TestClient(app) as client:
        response = client.post("/api/rag/ask", json={"question": "Hello"})

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The local AI service is unavailable. Check Ollama and the configured model."
    )
