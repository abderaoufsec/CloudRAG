from app.rag.chunker import create_chunks, TextChunk


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


def test_chunking_with_page_mapping():
    """Test that chunks correctly inherit page numbers from page mapping."""
    text = "A" * 2000
    # Simulate a document with 3 pages: first 800 chars = page 1, next 800 = page 2, rest = page 3
    page_mapping = [1] * 800 + [2] * 800 + [3] * 400

    chunks = create_chunks(
        text=text,
        document_id="test-document",
        chunk_size=800,
        chunk_overlap=120,
        page_mapping=page_mapping,
    )

    assert len(chunks) > 1
    # First chunk should be on page 1
    assert chunks[0].page == 1
    # Second chunk starts at position 680 (800-120), still on page 1
    assert chunks[1].page == 1
    # Third chunk starts at position 1360, should be on page 2
    assert chunks[2].page == 2
    # Verify page field is set for all chunks
    assert all(chunk.page is not None for chunk in chunks)