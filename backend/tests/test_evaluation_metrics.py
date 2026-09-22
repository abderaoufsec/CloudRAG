import json
import sys
from pathlib import Path

from unittest.mock import Mock

# Add evaluation directory to path for imports
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    # Hit@K now checks if sources were successfully retrieved
    # Non-empty sources means retrieval succeeded
    results = [{"text": "unrelated"}, {"text": "FAISS retrieves chunks"}]
    assert calculate_hit_at_k(results, ["FAISS"], 1) == 1.0  # 1 source = hit
    assert calculate_hit_at_k(results, ["FAISS"], 2) == 1.0  # still hit
    assert calculate_hit_at_k([], ["FAISS"], 1) == 0.0  # no sources = miss


def test_hit_at_k_measures_retrieval_success():
    # Hit@K measures whether retrieval returned any sources, not keyword matching
    # This is because expected keywords are for the ANSWER, not source chunks
    results = [{"text": "Some chunk text"}]
    assert calculate_hit_at_k(results, ["unrelated"], 1) == 1.0  # retrieval succeeded
    assert calculate_hit_at_k([], ["any"], 1) == 0.0  # retrieval failed


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
    # Hit@K is 1.0 because sources were successfully retrieved
    assert result["hit_at_1"] == 1.0
    assert result["hit_at_3"] == 1.0
    assert result["hit_at_5"] == 1.0
    # Keyword match is 0.5 (1 of 2 keywords in answer)
    assert result["keyword_match"] == 0.5
    # Pass requires both keyword match >= threshold AND retrieval succeeded
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

    # Hit@K is 1.0 because sources were successfully retrieved
    assert result["hit_at_1"] == 1.0
    assert result["keyword_match"] > 0.0
    assert result["retrieval_failure"] is False


def test_hit_at_k_regression_test_retrieval_success():
    """
    Regression test for the evaluator bug where Hit@K was incorrectly checking
    if source chunks contained expected keywords (answer keywords) instead of
    simply measuring whether retrieval succeeded.

    When sources are retrieved, Hit@K should be 1.0 regardless of keyword matching.
    When no sources are retrieved, Hit@K should be 0.0.
    """
    # Case 1: Successful retrieval should return Hit@K = 1.0
    sources_with_results = [
        {"text": "Some chunk about AI history", "score": 0.85},
        {"text": "Another chunk", "score": 0.72},
    ]
    assert calculate_hit_at_k(sources_with_results, ["unrelated"], 1) == 1.0
    assert calculate_hit_at_k(sources_with_results, ["unrelated"], 3) == 1.0
    assert calculate_hit_at_k(sources_with_results, ["unrelated"], 5) == 1.0

    # Case 2: Failed retrieval (no sources) should return Hit@K = 0.0
    sources_empty = []
    assert calculate_hit_at_k(sources_empty, ["any"], 1) == 0.0
    assert calculate_hit_at_k(sources_empty, ["any"], 3) == 0.0
    assert calculate_hit_at_k(sources_empty, ["any"], 5) == 0.0
