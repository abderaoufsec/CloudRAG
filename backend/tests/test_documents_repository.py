from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.document import Document
from app.services.document_repository import (
    create_document,
    get_document,
    get_document_by_hash,
    list_documents,
)


def create_test_db():

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    Base.metadata.create_all(
        bind=engine
    )

    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )


def test_create_and_get_document():

    Session = create_test_db()

    db = Session()

    document = Document(
        document_id="test-document",
        filename="test.txt",
        file_type=".txt",
        file_size_bytes=100,
        file_hash="a" * 64,
        status="indexed",
        characters=100,
        words=20,
        pages=1,
        chunk_count=2,
    )

    create_document(
        db,
        document,
    )

    result = get_document(
        db,
        "test-document",
    )

    assert result is not None

    assert result.filename == "test.txt"

    db.close()


def test_find_document_by_hash():

    Session = create_test_db()

    db = Session()

    document = Document(
        document_id="hash-test",
        filename="hash.txt",
        file_type=".txt",
        file_size_bytes=100,
        file_hash="b" * 64,
        status="indexed",
    )

    create_document(
        db,
        document,
    )

    result = get_document_by_hash(
        db,
        "b" * 64,
    )

    assert result is not None

    db.close()


def test_list_documents():

    Session = create_test_db()

    db = Session()

    document = Document(
        document_id="list-test",
        filename="list.txt",
        file_type=".txt",
        file_size_bytes=100,
        file_hash="c" * 64,
        status="indexed",
    )

    create_document(
        db,
        document,
    )

    documents = list_documents(db)

    assert len(documents) == 1

    db.close()