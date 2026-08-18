from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.

    This model supports multiple languages and is suitable
    for our multilingual RAG prototype.
    """

    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]):
    if not texts:
        return []

    model = get_embedding_model()

    return model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )


def embed_query(query: str):
    model = get_embedding_model()

    return model.encode(
        [query],
        normalize_embeddings=True,
        show_progress_bar=False,
    )