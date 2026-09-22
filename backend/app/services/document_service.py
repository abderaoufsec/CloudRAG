import re
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from docx import Document as DocxDocument
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
}

# DOCX files are ZIP archives.  The upload limit limits the compressed file,
# so cap the extracted archive too to avoid accepting a small ZIP bomb.
MAX_DOCX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024

# Maximum extracted text length to prevent processing enormous documents
MAX_EXTRACTED_CHARACTERS = 5_000_000

# Suspicious filename patterns to reject
SUSPICIOUS_FILENAME_PATTERNS = [
    r"\.\.",  # Path traversal
    r"[<>:\"|?*]",  # Invalid Windows characters
    r"\x00",  # Null bytes
    r"^\.+$",  # Hidden files
]


class DocumentProcessingError(Exception):
    """Raised when a document cannot be processed."""


def validate_filename(filename: str) -> None:
    """
    Validate filename for security and safety.
    Rejects path traversal attempts, suspicious characters, and invalid names.
    """
    if not filename or not filename.strip():
        raise DocumentProcessingError("Filename cannot be empty.")

    # Check for suspicious patterns
    for pattern in SUSPICIOUS_FILENAME_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            raise DocumentProcessingError(
                f"Filename contains invalid characters or patterns: {filename}"
            )

    # Check filename length
    if len(filename) > 255:
        raise DocumentProcessingError("Filename exceeds maximum length of 255 characters.")

    # Check for dangerous extensions (even though we only accept certain ones)
    dangerous_extensions = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".js"}
    ext = Path(filename).suffix.lower()
    if ext in dangerous_extensions:
        raise DocumentProcessingError(
            f"Dangerous file extension not allowed: {ext}"
        )


def validate_file_content(extension: str, content: bytes) -> None:
    """
    Reject files whose bytes do not match their permitted extension.
    Also checks for empty files, corrupted archives, and encoding issues.
    """

    if not content:
        raise DocumentProcessingError("The uploaded file is empty.")

    if extension == ".pdf":
        # PDF files must start with %PDF- magic bytes
        if not content.startswith(b"%PDF-"):
            raise DocumentProcessingError(
                "The uploaded file is not a valid PDF."
            )
        # Check for %%EOF marker to verify PDF completeness
        if b"%%EOF" not in content[:1024 * 100]:  # Check first 100KB
            raise DocumentProcessingError(
                "The uploaded PDF appears to be corrupted or incomplete."
            )

    if extension == ".docx":
        try:
            from io import BytesIO

            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
                uncompressed_size = sum(
                    entry.file_size for entry in archive.infolist()
                )
        except BadZipFile as exc:
            raise DocumentProcessingError(
                "The uploaded file is not a valid DOCX document."
            ) from exc

        required_entries = {"[Content_Types].xml", "word/document.xml"}
        if not required_entries.issubset(names):
            raise DocumentProcessingError(
                "The uploaded file is not a valid DOCX document."
            )

        if uncompressed_size > MAX_DOCX_UNCOMPRESSED_SIZE:
            raise DocumentProcessingError(
                "The DOCX expands beyond the allowed processing limit."
            )

    if extension in {".txt", ".md"}:
        if b"\x00" in content:
            raise DocumentProcessingError(
                "Text files cannot contain null bytes."
            )

        try:
            decoded = content.decode("utf-8")
            # Check for suspiciously repetitive content (potential attacks)
            if len(decoded) > 1000:
                char_frequency = {}
                for char in decoded:
                    char_frequency[char] = char_frequency.get(char, 0) + 1
                max_freq = max(char_frequency.values())
                if max_freq / len(decoded) > 0.9:  # 90% same character
                    raise DocumentProcessingError(
                        "File contains suspicious repetitive content."
                    )
        except UnicodeDecodeError as exc:
            raise DocumentProcessingError(
                "Text files must use UTF-8 encoding."
            ) from exc


def validate_file_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise DocumentProcessingError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {supported}"
        )

    return extension


def extract_pdf(path: Path) -> tuple[str, int, list[int]]:
    """
    Extract text from PDF with page mapping.
    Returns (text, page_count, page_mapping) where page_mapping
    maps character positions to page numbers for citation purposes.
    """
    reader = PdfReader(str(path))

    pages = len(reader.pages)
    text_parts = []
    page_mapping = []  # Tracks which page each character belongs to

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text_parts.append(text)
        # Mark each character in this text as belonging to this page
        for _ in text:
            page_mapping.append(page_num + 1)  # 1-indexed page numbers

    return "\n\n".join(text_parts), pages, page_mapping


def extract_docx(path: Path) -> tuple[str, int, list[int]]:
    """
    Extract text from DOCX with page mapping.
    DOCX doesn't have native page boundaries, so we treat the entire document as page 1.
    """
    document = DocxDocument(str(path))

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    text = "\n\n".join(paragraphs)
    # All characters belong to page 1 since DOCX doesn't have page boundaries
    page_mapping = [1] * len(text)

    return text, 1, page_mapping


def extract_text_file(path: Path) -> tuple[str, int, list[int]]:
    """
    Extract text from plain text files with page mapping.
    Treats the entire file as page 1 since plain text doesn't have page boundaries.
    """
    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    # All characters belong to page 1
    page_mapping = [1] * len(text)

    return text, 1, page_mapping


def extract_text(path: Path, extension: str) -> tuple[str, int, list[int]]:
    """
    Extract text from a document with page mapping for citations.
    Returns (text, page_count, page_mapping).
    """
    if extension == ".pdf":
        return extract_pdf(path)

    if extension == ".docx":
        return extract_docx(path)

    if extension in {".txt", ".md"}:
        return extract_text_file(path)

    raise DocumentProcessingError(
        f"No extractor available for {extension}"
    )


def clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]

    cleaned_lines = [
        line for line in lines
        if line
    ]

    return "\n".join(cleaned_lines)


def process_document(path: Path) -> dict:
    """
    Process a document through validation, extraction, and cleaning.
    Returns document metadata, extracted text, and page mapping for citations.
    """
    # Validate filename before processing
    validate_filename(path.name)

    extension = validate_file_extension(path.name)

    text, pages, page_mapping = extract_text(path, extension)

    # Check extracted text length to prevent processing enormous documents
    if len(text) > MAX_EXTRACTED_CHARACTERS:
        raise DocumentProcessingError(
            f"Document exceeds maximum extractable character limit of {MAX_EXTRACTED_CHARACTERS:,}."
        )

    text = clean_text(text)

    if not text.strip():
        raise DocumentProcessingError(
            "The document does not contain extractable text."
        )

    document_id = str(uuid4())

    return {
        "document_id": document_id,
        "filename": path.name,
        "file_type": extension,
        "file_size_bytes": path.stat().st_size,
        "characters": len(text),
        "words": len(text.split()),
        "pages": pages,
        "text": text,
        "page_mapping": page_mapping,  # Include page mapping for citation support
    }
