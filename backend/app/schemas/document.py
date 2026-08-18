from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    characters: int
    words: int
    pages: int
    chunk_count: int
    status: str
    error_message: str | None
    uploaded_at: datetime


class DocumentListResponse(BaseModel):

    documents: list[DocumentResponse]
    total: int