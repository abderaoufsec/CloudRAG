from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.document import Document
from app.rag.pipeline import rag_pipeline
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_repository import (
    create_document,
    delete_document,
    get_document,
    get_document_by_hash,
    list_documents,
    update_document,
)
from app.services.document_service import (
    DocumentProcessingError,
    process_document,
)
from app.services.file_hash import calculate_file_hash


router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MAX_FILE_SIZE = 10 * 1024 * 1024

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
}


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{extension}'. "
                "Supported types: "
                ".pdf, .docx, .txt, .md"
            ),
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MB limit.",
        )

    safe_filename = Path(
        file.filename
    ).name

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    document_id = uuid4().hex

    destination = (
        DOCUMENTS_DIR
        / f"{document_id}{extension}"
    )

    destination.write_bytes(content)

    file_hash = calculate_file_hash(
        destination
    )

    existing_document = get_document_by_hash(
        db,
        file_hash,
    )

    if existing_document:

        destination.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=409,
            detail={
                "message": "This file has already been uploaded.",
                "document_id": existing_document.document_id,
                "filename": existing_document.filename,
            },
        )

    document = Document(
        document_id=document_id,
        filename=safe_filename,
        file_type=extension,
        file_size_bytes=len(content),
        file_hash=file_hash,
        status="processing",
        uploaded_at=datetime.now(
            timezone.utc
        ),
    )

    create_document(
        db,
        document,
    )

    try:

        result = process_document(
            destination
        )

        processed_text_path = (
            PROCESSED_DIR
            / f"{document_id}.txt"
        )

        processed_text_path.write_text(
            result["text"],
            encoding="utf-8",
        )

        indexing_result = (
            rag_pipeline.index_document(
                document_id=document_id,
                text=result["text"],
            )
        )

        update_document(
            db,
            document,
            characters=result["characters"],
            words=result["words"],
            pages=result["pages"],
            chunk_count=indexing_result.get(
                "chunks",
                0,
            ),
            status="indexed",
            error_message=None,
        )

    except DocumentProcessingError as exc:

        update_document(
            db,
            document,
            status="failed",
            error_message=str(exc),
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        update_document(
            db,
            document,
            status="failed",
            error_message=str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed."
            ),
        ) from exc

    return document


@router.get(
    "",
    response_model=DocumentListResponse,
)
def get_documents(
    db: Session = Depends(get_db),
):

    documents = list_documents(db)

    return {
        "documents": documents,
        "total": len(documents),
    }


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document_by_id(
    document_id: str,
    db: Session = Depends(get_db),
):

    document = get_document(
        db,
        document_id,
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


@router.delete(
    "/{document_id}",
)
def remove_document(
    document_id: str,
    db: Session = Depends(get_db),
):

    document = get_document(
        db,
        document_id,
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

        rag_pipeline.delete_document(
        document_id
    )

    extension = document.file_type

    original_file = (
        DOCUMENTS_DIR
        / f"{document.document_id}{extension}"
    )

    processed_file = (
        PROCESSED_DIR
        / f"{document.document_id}.txt"
    )

    original_file.unlink(
        missing_ok=True
    )

    processed_file.unlink(
        missing_ok=True
    )

    delete_document(
        db,
        document,
    )

    return {
        "success": True,
        "message": "Document metadata deleted.",
        "document_id": document_id,
    }