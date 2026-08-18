from datetime import datetime

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    characters: int
    words: int
    pages: int | None = None
    uploaded_at: datetime
    status: str = "processed"


class DocumentResponse(BaseModel):
    success: bool
    message: str
    document: DocumentMetadata