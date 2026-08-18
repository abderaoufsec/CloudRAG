from dataclasses import dataclass


@dataclass
class TextChunk:
    chunk_id: str
    document_id: str
    text: str
    chunk_index: int


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries."""

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]

    return "\n\n".join(paragraphs)


def create_chunks(
    text: str,
    document_id: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[TextChunk]:
    """
    Split text into overlapping character-based chunks.

    Character-based chunking is intentionally simple for our
    first RAG implementation. We can improve it later.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    text = normalize_text(text)

    if not text:
        return []

    chunks = []

    start = 0
    chunk_index = 0
    step = chunk_size - chunk_overlap

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                TextChunk(
                    chunk_id=f"{document_id}_{chunk_index}",
                    document_id=document_id,
                    text=chunk_text,
                    chunk_index=chunk_index,
                )
            )

        start += step
        chunk_index += 1

    return chunks