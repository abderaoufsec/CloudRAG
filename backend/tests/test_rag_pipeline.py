from app.rag.chunker import create_chunks


def test_rag_chunk_creation():

    text = """
    Retrieval-Augmented Generation combines
    information retrieval with language models.

    The retrieval system finds relevant information
    from a knowledge base before generating an answer.
    """

    chunks = create_chunks(
        text=text,
        document_id="rag-test",
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(chunks) >= 2

    assert all(
        chunk.document_id == "rag-test"
        for chunk in chunks
    )

    assert all(
        chunk.text
        for chunk in chunks
    )