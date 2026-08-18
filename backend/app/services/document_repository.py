from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def create_document(
    db: Session,
    document: Document,
) -> Document:

    db.add(document)

    db.commit()

    db.refresh(document)

    return document


def get_document(
    db: Session,
    document_id: str,
) -> Document | None:

    statement = select(Document).where(
        Document.document_id == document_id
    )

    return db.scalar(statement)


def get_document_by_hash(
    db: Session,
    file_hash: str,
) -> Document | None:

    statement = select(Document).where(
        Document.file_hash == file_hash
    )

    return db.scalar(statement)


def list_documents(
    db: Session,
) -> list[Document]:

    statement = select(Document).order_by(
        Document.uploaded_at.desc()
    )

    return list(
        db.scalars(statement)
    )


def delete_document(
    db: Session,
    document: Document,
) -> None:

    db.delete(document)

    db.commit()


def update_document(
    db: Session,
    document: Document,
    **fields,
) -> Document:

    for field, value in fields.items():
        setattr(
            document,
            field,
            value,
        )

    db.commit()

    db.refresh(document)

    return document