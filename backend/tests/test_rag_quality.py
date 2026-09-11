from types import SimpleNamespace

from app.rag.pipeline import RAGPipeline


def test_low_confidence_results_do_not_call_the_llm(monkeypatch, tmp_path):
    pipeline = RAGPipeline()
    monkeypatch.setattr(
        pipeline,
        "search",
        lambda **_: [
            {
                "document_id": "document-1",
                "chunk_id": "document-1_0",
                "chunk_index": 0,
                "text": "Unrelated text.",
                "score": 0.1,
            }
        ],
    )
    monkeypatch.setattr(
        "app.rag.pipeline.get_settings",
        lambda: SimpleNamespace(
            min_retrieval_score=0.35,
            max_rag_context_characters=12000,
        ),
    )

    def fail_if_called():
        raise AssertionError("The LLM must not run for weak retrieval results.")

    monkeypatch.setattr("app.rag.pipeline.get_llm_provider", fail_if_called)

    result = pipeline.ask("What is the refund policy?")

    assert result["sources"] == []
    assert "could not find relevant information" in result["answer"]


def test_context_is_limited_before_calling_the_llm(monkeypatch):
    pipeline = RAGPipeline()
    captured = {}
    long_text = "A" * 1000

    monkeypatch.setattr(
        pipeline,
        "search",
        lambda **_: [
            {
                "document_id": "document-1",
                "chunk_id": "document-1_0",
                "chunk_index": 0,
                "text": long_text,
                "score": 0.9,
            }
        ],
    )
    monkeypatch.setattr(
        "app.rag.pipeline.get_settings",
        lambda: SimpleNamespace(
            min_retrieval_score=0.35,
            max_rag_context_characters=250,
        ),
    )
    class FakeProvider:
        def generate(self, **kwargs):
            captured.update(kwargs)
            return "Grounded answer."

    monkeypatch.setattr("app.rag.pipeline.get_llm_provider", lambda: FakeProvider())

    result = pipeline.ask("Summarize the document.")

    assert result["answer"] == "Grounded answer."
    assert len(captured["context"]) == 250


def test_selected_document_is_passed_to_retrieval(monkeypatch):
    pipeline = RAGPipeline()
    captured = {}
    monkeypatch.setattr(
        pipeline,
        "search",
        lambda **kwargs: captured.update(kwargs) or [],
    )

    pipeline.ask("Question", document_id="document-1")

    assert captured["document_id"] == "document-1"
