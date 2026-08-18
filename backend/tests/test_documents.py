from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_txt(tmp_path, monkeypatch):
    import app.api.documents as documents_api

    documents_dir = tmp_path / "documents"

    monkeypatch.setattr(
        documents_api,
        "DOCUMENTS_DIR",
        documents_dir,
    )

    text = (
        "CloudRAG is a Retrieval-Augmented Generation application.\n"
        "It allows users to ask questions about their documents."
    )

    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "test.txt",
                text.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["success"] is True
    assert data["document"]["filename"] == "test.txt"
    assert data["document"]["file_type"] == ".txt"
    assert data["document"]["words"] > 0


def test_reject_unsupported_file():
    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "malware.exe",
                b"not really an executable",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400