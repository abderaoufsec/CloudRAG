from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.rag.pipeline import rag_pipeline
from app.schemas.document import DocumentResponse
from app.services.document_service import (
    DocumentProcessingError,
    process_document,
)


router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    supported = {
        ".pdf",
        ".docx",
        ".txt",
        ".md",
    }

    if extension not in supported:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{extension}'. "
                "Supported types: .pdf, .docx, .txt, .md"
            ),
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MB limit.",
        )

    safe_filename = Path(file.filename).name

    destination = DOCUMENTS_DIR / safe_filename

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_bytes(content)

    try:
        result = process_document(destination)

    except DocumentProcessingError as exc:
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    processed_text_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / f"{result['document_id']}.txt"
    )

    processed_text_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    processed_text_path.write_text(
        result["text"],
        encoding="utf-8",
    )

    # Automatically add the document to the vector index.
    indexing_result = rag_pipeline.index_document(
        document_id=result["document_id"],
        text=result["text"],
    )

    return {
        "success": True,
        "message": (
            "Document uploaded, processed, "
            "and indexed successfully."
        ),
        "document": {
            "document_id": result["document_id"],
            "filename": result["filename"],
            "file_type": result["file_type"],
            "file_size_bytes": result["file_size_bytes"],
            "characters": result["characters"],
            "words": result["words"],
            "pages": result["pages"],
            "uploaded_at": datetime.now(timezone.utc),
            "status": "indexed",
        },
    }