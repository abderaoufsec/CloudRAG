import json

from unittest.mock import Mock

from evaluation.evaluator import load_dataset, process_question_result
from evaluation.metrics import (
    calculate_hit_at_k,
    calculate_keyword_match,
    calculate_metrics,
    calculate_question_result,
    normalize_text,
)


def test_keyword_match_is_case_insensitive_and_normalized():
    assert calculate_keyword_match(
        "FAISS uses Local Embeddings",
        ["faiss", "local   embeddings"],
    ) == 1.0


def test_keyword_match_handles_empty_answer_and_empty_keywords_safely():
    assert calculate_keyword_match("", ["faiss"]) == 0.0
    assert calculate_keyword_match("FAISS", []) == 0.0


def test_hit_at_k_uses_only_requested_results():
    results = [{"text": "unrelated"}, {"text": "FAISS retrieves chunks"}]
    assert calculate_hit_at_k(results, ["FAISS"], 1) == 0.0
    assert calculate_hit_at_k(results, ["FAISS"], 2) == 1.0


def test_hit_at_k_supports_partial_keyword_matches():
    results = [{"text": "The deep learning model is trained."}]
    assert calculate_hit_at_k(results, ["deep learning"], 1) == 1.0


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  AI\n\nHistory   ") == "ai history"


def test_aggregate_metrics():
    metrics = calculate_metrics([
        {
            "hit_at_1": 1.0,
            "hit_at_3": 1.0,
            "hit_at_5": 1.0,
            "keyword_match": 1.0,
            "passed": True,
            "retrieval_failure": False,
        },
        {
            "hit_at_1": 0.0,
            "hit_at_3": 1.0,
            "hit_at_5": 1.0,
            "keyword_match": 0.5,
            "passed": False,
            "retrieval_failure": False,
        },
    ])
    assert metrics["hit_at_1"] == 50.0
    assert metrics["hit_at_3"] == 100.0
    assert metrics["hit_at_5"] == 100.0
    assert metrics["keyword_match_rate"] == 75.0
    assert metrics["questions_passed"] == 1
    assert metrics["questions_failed"] == 1
    assert metrics["retrieval_failures"] == 0


def test_question_result_tracks_pass_and_retrieval_failure(tmp_path):
    result = calculate_question_result(
        id="q01",
        question="Origins of AI",
        answer="AI came from early symbolic work and later machine learning.",
        sources=[
            {"text": "Origins of AI started with symbolic methods."},
        ],
        expected_keywords=["Origins", "symbolic"],
        pass_threshold=0.5,
    )
    assert result["hit_at_1"] == 1.0
    assert result["hit_at_3"] == 1.0
    assert result["hit_at_5"] == 1.0
    assert result["keyword_match"] == 0.5
    assert result["passed"] is True
    assert result["retrieval_failure"] is False


def test_load_dataset_validates_shape_and_counts(tmp_path):
    dataset_path = tmp_path / "questions.json"
    dataset_path.write_text(json.dumps([
        {
            "id": "q01",
            "question": "What is AI?",
            "expected_keywords": ["AI"],
        },
    ]), encoding="utf-8")

    try:
        load_dataset(dataset_path)
    except ValueError as exc:
        assert "exactly 20" in str(exc).lower()
    else:
        raise AssertionError("Dataset validation should reject a dataset that is not 20 questions.")


def test_evaluator_process_question_result_handles_mocked_rag_response():
    response = {
        "answer": "John McCarthy organized the Dartmouth conference.",
        "sources": [
            {
                "document_id": "evaluation_document.txt",
                "chunk_id": "evaluation_document.txt_1",
                "chunk_index": 1,
                "score": 0.82,
                "text": "John McCarthy organized the Dartmouth...",
            }
        ],
    }

    result = process_question_result(
        id="q03",
        question="Who organized the Dartmouth conference?",
        expected_keywords=["John McCarthy", "Dartmouth"],
        answer=response["answer"],
        sources=response["sources"],
    )

    assert result["hit_at_1"] == 1.0
    assert result["keyword_match"] > 0.0
    assert result["retrieval_failure"] is False
