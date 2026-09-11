from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


def normalize_text(text: str) -> str:
    """Normalize text for case-insensitive, whitespace-insensitive comparisons."""
    if not isinstance(text, str):
        text = str(text or "")
    return re.sub(r"\s+", " ", text.casefold()).strip()


def calculate_keyword_match(
    answer: str,
    expected_keywords: Iterable[str],
) -> float:
    """
    Return keyword coverage from 0.0 to 1.0.
    A keyword can be partially matched inside the answer text.
    Empty answer or empty keyword list safely yields 0.0.
    """
    if not isinstance(answer, str) or not answer.strip():
        return 0.0

    keywords = [str(keyword).strip() for keyword in expected_keywords if str(keyword).strip()]
    if not keywords:
        return 0.0

    normalized_answer = normalize_text(answer)
    matched = 0
    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword in normalized_answer:
            matched += 1

    return matched / len(keywords)


def calculate_hit_at_k(
    sources: list[Mapping[str, Any]],
    expected_keywords: Iterable[str],
    k: int,
) -> float:
    """
    Return 1.0 if any of the first k sources contains evidence for at least
    one expected keyword, otherwise 0.0.
    """
    if k <= 0:
        return 0.0

    keywords = [str(keyword).strip() for keyword in expected_keywords if str(keyword).strip()]
    if not keywords:
        return 0.0

    for source in sources[:k]:
        text = str(source.get("text", "") or "")
        if calculate_keyword_match(text, keywords) > 0.0:
            return 1.0

    return 0.0


def calculate_question_result(
    *,
    id: str,
    question: str,
    answer: str,
    sources: list[Mapping[str, Any]],
    expected_keywords: Iterable[str],
    pass_threshold: float = 0.5,
) -> dict[str, Any]:
    """Return a per-question result dict for the evaluator output."""
    hit_at_1 = calculate_hit_at_k(sources, expected_keywords, 1)
    hit_at_3 = calculate_hit_at_k(sources, expected_keywords, 3)
    hit_at_5 = calculate_hit_at_k(sources, expected_keywords, 5)
    keyword_match = calculate_keyword_match(answer, expected_keywords)

    retrieval_failure = not any(
        value == 1.0 for value in (hit_at_1, hit_at_3, hit_at_5)
    )

    passed = keyword_match >= pass_threshold and not retrieval_failure

    return {
        "id": id,
        "question": question,
        "answer": answer,
        "sources": list(sources),
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
        "keyword_match": keyword_match,
        "passed": passed,
        "retrieval_failure": retrieval_failure,
    }


def calculate_metrics(results: list[Mapping[str, Any]]) -> dict[str, float | int]:
    """
    Aggregate the per-question metrics into the requested evaluation summary.
    Returns percentages for hit@k metrics and keyword match, plus counts.
    """
    total = len(results)
    if not total:
        return {
            "hit_at_1": 0.0,
            "hit_at_3": 0.0,
            "hit_at_5": 0.0,
            "keyword_match_rate": 0.0,
            "questions_passed": 0,
            "questions_failed": 0,
            "retrieval_failures": 0,
        }

    hit_at_1 = sum(float(item.get("hit_at_1", 0.0)) for item in results) / total * 100
    hit_at_3 = sum(float(item.get("hit_at_3", 0.0)) for item in results) / total * 100
    hit_at_5 = sum(float(item.get("hit_at_5", 0.0)) for item in results) / total * 100
    keyword_match_rate = sum(float(item.get("keyword_match", 0.0)) for item in results) / total * 100
    questions_passed = sum(1 for item in results if bool(item.get("passed")))
    questions_failed = total - questions_passed
    retrieval_failures = sum(1 for item in results if bool(item.get("retrieval_failure")))

    return {
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
        "keyword_match_rate": keyword_match_rate,
        "questions_passed": questions_passed,
        "questions_failed": questions_failed,
        "retrieval_failures": retrieval_failures,
    }
