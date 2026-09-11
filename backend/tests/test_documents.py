from pathlib import Path

def test_upload_txt(documents_client):

    text = (
        "CloudRAG is a Retrieval-Augmented Generation application.\n"
        "It allows users to ask questions about their documents."
    )

    response = documents_client.post(
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

    assert data["filename"] == "test.txt"
    assert data["file_type"] == ".txt"
    assert data["words"] > 0
    assert data["status"] == "indexed"


def test_reject_unsupported_file(documents_client):
    response = documents_client.post(
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


def test_rejects_disguised_pdf(documents_client):
    response = documents_client.post(
        "/api/documents/upload",
        files={
            "file": (
                "not-a-pdf.pdf",
                b"this is plain text, not a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The uploaded file is not a valid PDF."


def test_rejects_text_with_null_bytes(documents_client):
    response = documents_client.post(
        "/api/documents/upload",
        files={
            "file": (
                "unsafe.txt",
                b"safe text\x00unsafe bytes",
                "text/plain",
            )
        },
    )

    assert response.status_code == 422
