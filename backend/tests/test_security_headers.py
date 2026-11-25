from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_docs_csp_allows_swagger_cdn():
    response = client.get("/docs")

    csp = response.headers.get("content-security-policy", "")

    assert "cdn.jsdelivr.net" in csp


def test_health_csp_is_strict():
    response = client.get("/api/health")

    csp = response.headers.get("content-security-policy", "")

    assert "cdn.jsdelivr.net" not in csp
    assert "default-src 'self'" in csp
