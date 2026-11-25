from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "CloudRAG API is running"


def test_health():
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["project"] == "CloudRAG"
    assert data["mode"] == "local"
    assert "environment" not in data


def test_readiness(monkeypatch):
    import ollama

    monkeypatch.setattr(
        ollama.Client,
        "list",
        lambda self: [],
    )

    response = client.get("/api/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert "checks" in data
    assert "database" in data["checks"]
    assert "vector_store" in data["checks"]
    assert "embedding_provider" in data["checks"]
    assert "llm_provider" in data["checks"]


def test_readiness_hides_exception_details(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock

    import ollama

    import app.api.health as health_api

    monkeypatch.setattr(
        ollama.Client,
        "list",
        lambda self: [],
    )

    fake_model = Mock()
    fake_model.cache_info.return_value = SimpleNamespace(
        currsize=1,
    )
    monkeypatch.setattr(
        "app.rag.embeddings.get_embedding_model",
        fake_model,
    )

    class BrokenStore:
        @property
        def size(self):
            raise RuntimeError("secret internal detail")

    monkeypatch.setattr(
        health_api.rag_pipeline,
        "vector_store",
        BrokenStore(),
    )

    response = client.get("/api/ready")

    assert response.status_code == 503
    assert "secret internal detail" not in response.text

    checks = response.json()["detail"]["checks"]
    assert checks["vector_store"] == "unavailable"