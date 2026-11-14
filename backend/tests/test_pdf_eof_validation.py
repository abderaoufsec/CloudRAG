import pytest

from app.services.document_service import (
    DocumentProcessingError,
    validate_file_content,
)


def _pdf(body: bytes) -> bytes:
    return b"%PDF-1.7\n" + body


def test_large_pdf_with_eof_at_end_is_accepted():
    content = _pdf(b"x" * (300 * 1024) + b"\n%%EOF\n")

    validate_file_content(".pdf", content)


def test_trailing_whitespace_after_eof_is_accepted():
    content = _pdf(b"data\n%%EOF\n   \n\t\n")

    validate_file_content(".pdf", content)


def test_missing_eof_is_rejected():
    content = _pdf(b"x" * 1000)

    with pytest.raises(DocumentProcessingError):
        validate_file_content(".pdf", content)


def test_eof_only_near_start_of_large_file_is_rejected():
    content = _pdf(b"%%EOF\n" + b"x" * (300 * 1024))

    with pytest.raises(DocumentProcessingError):
        validate_file_content(".pdf", content)
