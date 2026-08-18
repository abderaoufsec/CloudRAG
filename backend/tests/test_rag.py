from app.rag.chunker import create_chunks


def test_chunking():
    text = "A" * 2000

    chunks = create_chunks(
        text=text,
        document_id="test-document",
        chunk_size=800,
        chunk_overlap=120,
    )

    assert len(chunks) > 1

    assert chunks[0].document_id == "test-document"

    assert chunks[0].chunk_index == 0

    assert chunks[1].chunk_index == 1


def test_empty_text():
    chunks = create_chunks(
        text="",
        document_id="empty",
    )

    assert chunks == []