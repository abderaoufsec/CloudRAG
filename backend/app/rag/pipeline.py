from pathlib import Path

from app.rag.chunker import create_chunks
from app.rag.embeddings import embed_query, embed_texts
from app.rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INDEX_DIRECTORY = PROJECT_ROOT / "data" / "index"


class RAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore(
            INDEX_DIRECTORY
        )

    def index_document(
        self,
        document_id: str,
        text: str,
    ):
        chunks = create_chunks(
            text=text,
            document_id=document_id,
        )

        if not chunks:
            return {
                "document_id": document_id,
                "chunks": 0,
            }

        embeddings = embed_texts(
            [chunk.text for chunk in chunks]
        )

        self.vector_store.add_chunks(
            chunks,
            embeddings,
        )

        return {
            "document_id": document_id,
            "chunks": len(chunks),
            "vector_store_size": self.vector_store.size,
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
    ):
        query_embedding = embed_query(query)

        return self.vector_store.search(
            query_embedding,
            top_k=top_k,
        )


rag_pipeline = RAGPipeline()