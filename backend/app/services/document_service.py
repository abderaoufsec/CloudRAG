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


class DocumentProcessingError(Exception):
    """Raised when a document cannot be processed."""


def validate_file_content(extension: str, content: bytes) -> None:
    """Reject files whose bytes do not match their permitted extension."""

    if not content:
        raise DocumentProcessingError("The uploaded file is empty.")

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise DocumentProcessingError(
            "The uploaded file is not a valid PDF."
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
            content.decode("utf-8")
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


def extract_pdf(path: Path) -> tuple[str, int]:
    reader = PdfReader(str(path))

    pages = len(reader.pages)
    text_parts = []

    for page in reader.pages:
        text = page.extract_text() or ""
        text_parts.append(text)

    return "\n\n".join(text_parts), pages


def extract_docx(path: Path) -> tuple[str, int]:
    document = DocxDocument(str(path))

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n\n".join(paragraphs), 1


def extract_text_file(path: Path) -> tuple[str, int]:
    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    return text, 1


def extract_text(path: Path, extension: str) -> tuple[str, int]:
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
    extension = validate_file_extension(path.name)

    text, pages = extract_text(path, extension)

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
    }
