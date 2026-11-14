import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException

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


def test_failed_upload_is_cleaned_up_and_can_be_retried(
    documents_client,
    monkeypatch,
):
    import app.api.documents as documents_api

    pipeline_class = type(documents_api.rag_pipeline)

    def failing_index(*args, **kwargs):
        raise RuntimeError("index exploded")

    monkeypatch.setattr(
        documents_api.rag_pipeline,
        "index_document",
        failing_index,
    )

    content = b"CloudRAG failed upload cleanup test."

    response = documents_client.post(
        "/api/documents/upload",
        files={
            "file": (
                "retry.txt",
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 500

    listing = documents_client.get(
        "/api/documents"
    )

    assert listing.json()["total"] == 0

    if documents_api.DOCUMENTS_DIR.exists():
        assert list(
            documents_api.DOCUMENTS_DIR.iterdir()
        ) == []

    monkeypatch.setattr(
        documents_api,
        "rag_pipeline",
        pipeline_class(),
    )

    response = documents_client.post(
        "/api/documents/upload",
        files={
            "file": (
                "retry.txt",
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201


def test_processing_runs_off_event_loop_thread(
    documents_client,
    monkeypatch,
):
    import threading

    import app.api.documents as documents_api

    event_loop_thread = {}
    worker_thread = {}

    original_validate = documents_api.validate_file_content

    def record_validate(extension, content):
        event_loop_thread["thread"] = threading.current_thread()
        return original_validate(extension, content)

    def fake_process(path):
        worker_thread["thread"] = threading.current_thread()
        return {
            "document_id": "ignored",
            "filename": path.name,
            "file_type": path.suffix,
            "file_size_bytes": path.stat().st_size,
            "characters": 4,
            "words": 1,
            "pages": 1,
            "text": "test",
            "page_mapping": [1, 1, 1, 1],
        }

    monkeypatch.setattr(
        documents_api,
        "validate_file_content",
        record_validate,
    )
    monkeypatch.setattr(
        documents_api,
        "process_document",
        fake_process,
    )

    response = documents_client.post(
        "/api/documents/upload",
        files={
            "file": (
                "thread.txt",
                b"test",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    assert (
        event_loop_thread["thread"]
        is not worker_thread["thread"]
    )


def test_upload_exceeding_limit_returns_413(
    documents_client,
    monkeypatch,
):
    import app.api.documents as documents_api

    monkeypatch.setattr(
        documents_api,
        "MAX_FILE_SIZE",
        10,
    )

    response = documents_client.post(
        "/api/documents/upload",
        files={
            "file": (
                "big.txt",
                b"x" * 100,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
    assert "limit" in response.json()["detail"].lower()
    assert not documents_api.DOCUMENTS_DIR.exists()


def test_size_check_aborts_before_reading_whole_stream(
    monkeypatch,
):
    import app.api.documents as documents_api

    class FakeUpload:
        filename = "big.txt"

        def __init__(self, total):
            self.total = total
            self.consumed = 0

        async def read(self, size=-1):
            if size is None or size < 0:
                size = self.total - self.consumed
            count = min(
                size,
                self.total - self.consumed,
            )
            self.consumed += count
            return b"x" * count

    monkeypatch.setattr(
        documents_api,
        "MAX_FILE_SIZE",
        10,
    )

    fake = FakeUpload(5 * 1024 * 1024)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            documents_api.upload_document(
                fake,
                None,
            )
        )

    assert excinfo.value.status_code == 413
    assert fake.consumed < fake.total


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
