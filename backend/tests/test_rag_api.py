from fastapi.testclient import TestClient

from app.main import app
from app.providers.base import LLMProviderError


def test_search_forwards_document_id(monkeypatch):
    import app.api.rag as rag_api

    captured = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        rag_api.rag_pipeline,
        "search",
        fake_search,
    )
    monkeypatch.setattr(
        rag_api,
        "get_document",
        lambda db, document_id: object(),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/rag/search",
            json={
                "query": "hello",
                "document_id": "doc-1",
            },
        )

    assert response.status_code == 200
    assert captured["query"] == "hello"
    assert captured["document_id"] == "doc-1"


def test_search_unknown_document_returns_404(monkeypatch):
    import app.api.rag as rag_api

    monkeypatch.setattr(
        rag_api.rag_pipeline,
        "search",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        rag_api,
        "get_document",
        lambda db, document_id: None,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/rag/search",
            json={
                "query": "hello",
                "document_id": "missing",
            },
        )

    assert response.status_code == 404


def test_index_endpoint_is_removed(monkeypatch):
    import app.api.rag as rag_api

    monkeypatch.setattr(
        rag_api.rag_pipeline,
        "index_document",
        lambda **_kwargs: {"chunks": 1},
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/rag/index",
            json={
                "document_id": "poisoned",
                "text": "arbitrary text",
            },
        )

    assert response.status_code in (404, 405)


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
