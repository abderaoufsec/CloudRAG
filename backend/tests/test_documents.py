from pathlib import Path

from app.services.document_service import (
    DocumentProcessingError,
    validate_filename,
)

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


def test_validate_filename_rejects_empty():
    try:
        validate_filename("")
        assert False, "Should raise DocumentProcessingError"
    except DocumentProcessingError as exc:
        assert "empty" in str(exc).lower()


def test_validate_filename_rejects_path_traversal():
    try:
        validate_filename("../../../etc/passwd")
        assert False, "Should raise DocumentProcessingError"
    except DocumentProcessingError as exc:
        assert "invalid" in str(exc).lower()


def test_validate_filename_rejects_special_characters():
    try:
        validate_filename("test<file>.txt")
        assert False, "Should raise DocumentProcessingError"
    except DocumentProcessingError as exc:
        assert "invalid" in str(exc).lower()


def test_validate_filename_rejects_dangerous_extensions():
    try:
        validate_filename("malware.exe")
        assert False, "Should raise DocumentProcessingError"
    except DocumentProcessingError as exc:
        assert "dangerous" in str(exc).lower()


def test_validate_filename_accepts_valid_names():
    # These should not raise exceptions
    validate_filename("document.pdf")
    validate_filename("my-report.docx")
    validate_filename("notes.md")
    validate_filename("data.txt")


def test_rejects_invalid_filename_via_api(documents_client):
    response = documents_client.post(
        "/api/documents/upload",
        files={
            "file": (
                "../../../etc/passwd",
                b"some content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()
