from collections import OrderedDict
from pathlib import Path

from app.rag.chunker import create_chunks
from app.rag.embeddings import embed_query, embed_texts
from app.providers.factory import get_llm_provider
from app.rag.vector_store import QdrantVectorStore, VectorStore
from app.config import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INDEX_DIRECTORY = PROJECT_ROOT / "data" / "index"


class RAGPipeline:

    def __init__(self):
        settings = get_settings()
        if settings.vector_store.lower() == "qdrant":
            self.vector_store = QdrantVectorStore(INDEX_DIRECTORY)
        else:
            self.vector_store = VectorStore(INDEX_DIRECTORY)
        self._search_cache = OrderedDict()
        self._max_cache_entries = 128

    def _ensure_cache(self):
        if not hasattr(self, "_search_cache"):
            self._search_cache = OrderedDict()
        if not hasattr(self, "_max_cache_entries"):
            self._max_cache_entries = 128

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
        document_id: str | None = None,
    ):

        self._ensure_cache()
        cache_key = (query, top_k, document_id)
        if cache_key in self._search_cache:
            self._search_cache.move_to_end(cache_key)
            return list(self._search_cache[cache_key])

        query_embedding = embed_query(query)
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            document_id=document_id,
        )

        self._search_cache[cache_key] = list(results)
        self._search_cache.move_to_end(cache_key)
        if len(self._search_cache) > self._max_cache_entries:
            self._search_cache.popitem(last=False)

        return list(results)



    def delete_document(
        self,
        document_id: str,
    ):
        self.vector_store.delete_document(
            document_id
        )

    def ask(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
    ):

        results = self.search(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        settings = get_settings()

        results = [
            result
            for result in results
            if result["score"] >= settings.min_retrieval_score
        ]

        if not results:
            return {
                "answer": (
                    "I could not find relevant information "
                    "in the indexed documents."
                ),
                "sources": [],
            }

        context_parts = []
        context_length = 0

        sources = []

        for result in results:

            context_part = (
                f"[Source: {result['document_id']} | "
                f"Chunk: {result['chunk_index']}]\n"
                f"{result['text']}"
            )

            remaining = (
                settings.max_rag_context_characters
                - context_length
            )
            if remaining <= 0:
                break

            context_parts.append(context_part[:remaining])
            context_length += len(context_parts[-1])

            sources.append(
              {
               "document_id": result["document_id"],
               "chunk_id": result["chunk_id"],
               "chunk_index": result["chunk_index"],
               "score": result["score"],
               "filename": result.get(
               "filename",
                 result["document_id"],
                  ),
                   }
              )

        context = "\n\n---\n\n".join(
            context_parts
        )

        answer = get_llm_provider().generate(
            question=question,
            context=context,
        )

         

        return {
            "answer": answer,
            "sources": sources,
        }


rag_pipeline = RAGPipeline()
