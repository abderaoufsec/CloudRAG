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


def test_readiness():
    response = client.get("/api/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert "checks" in data
    assert "database" in data["checks"]
    assert "vector_store" in data["checks"]
    assert "embedding_provider" in data["checks"]
    assert "llm_provider" in data["checks"]