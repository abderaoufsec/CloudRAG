import pytest

from app.rag.chunker import create_chunks
from app.services.document_service import build_normalized_text


def test_page_mapping_stays_aligned_after_normalization():
    pages = ["alpha\n\n\nbeta", "gamma", "delta epsilon"]

    text, mapping = build_normalized_text(pages)

    assert len(mapping) == len(text)

    chunks = create_chunks(
        text=text,
        document_id="doc",
        chunk_size=8,
        chunk_overlap=0,
        page_mapping=mapping,
    )

    cursor = 0

    for chunk in chunks:

        index = text.find(chunk.text, cursor)

        assert index != -1
        assert chunk.page == mapping[index]

        cursor = index + 1


def test_create_chunks_rejects_mismatched_page_mapping():
    with pytest.raises(ValueError):
        create_chunks(
            text="abcdef",
            document_id="doc",
            page_mapping=[1, 1],
        )
