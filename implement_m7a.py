from pathlib import Path
import json


ROOT = Path(__file__).resolve().parent
EVAL = ROOT / "evaluation"

EVAL.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Package marker
# ---------------------------------------------------------------------------

(EVAL / "__init__.py").write_text(
    "",
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# Evaluation dataset
# ---------------------------------------------------------------------------

questions = [
    {
        "id": "Q01",
        "question": "What event is considered the official birth of Artificial Intelligence as an independent academic discipline?",
        "expected_keywords": ["Dartmouth", "1956"],
    },
    {
        "id": "Q02",
        "question": "Who coined the term Artificial Intelligence?",
        "expected_keywords": ["John McCarthy"],
    },
    {
        "id": "Q03",
        "question": "What was the core philosophy of symbolic AI or GOFAI?",
        "expected_keywords": ["Physical Symbol System", "formal symbols"],
    },
    {
        "id": "Q04",
        "question": "What programming language did John McCarthy develop for AI?",
        "expected_keywords": ["LISP"],
    },
    {
        "id": "Q05",
        "question": "What technical and funding problems contributed to the first AI Winter?",
        "expected_keywords": [
            "machine translation",
            "combinatorial explosion",
            "funding",
        ],
    },
    {
        "id": "Q06",
        "question": "What were expert systems and how did they work?",
        "expected_keywords": [
            "expert systems",
            "if-then",
            "knowledge base",
        ],
    },
    {
        "id": "Q07",
        "question": "What was the Knowledge Acquisition Bottleneck?",
        "expected_keywords": [
            "Knowledge Acquisition Bottleneck",
            "human experts",
            "if-then",
        ],
    },
    {
        "id": "Q08",
        "question": "What happened when IBM's Deep Blue played Garry Kasparov in 1997?",
        "expected_keywords": [
            "Deep Blue",
            "Garry Kasparov",
            "1997",
        ],
    },
    {
        "id": "Q09",
        "question": "Why was the growth of the World Wide Web important for modern AI?",
        "expected_keywords": [
            "World Wide Web",
            "data",
            "datasets",
        ],
    },
    {
        "id": "Q10",
        "question": "Which classical machine-learning techniques became standard tools during the late 1990s and 2000s?",
        "expected_keywords": [
            "Support Vector Machines",
            "Random Forests",
            "Hidden Markov Models",
        ],
    },
    {
        "id": "Q11",
        "question": "What technological development helped trigger the Deep Learning Revolution?",
        "expected_keywords": [
            "GPUs",
            "2012",
            "deep neural networks",
        ],
    },
    {
        "id": "Q12",
        "question": "Who developed AlexNet?",
        "expected_keywords": [
            "Alex Krizhevsky",
            "Ilya Sutskever",
            "Geoffrey Hinton",
        ],
    },
    {
        "id": "Q13",
        "question": "How much lower was AlexNet's ImageNet error rate than the runner-up?",
        "expected_keywords": [
            "10.8",
            "percentage points",
        ],
    },
    {
        "id": "Q14",
        "question": "What are GANs and who introduced them?",
        "expected_keywords": [
            "Generative Adversarial Networks",
            "Ian Goodfellow",
        ],
    },
    {
        "id": "Q15",
        "question": "How did AlphaGo learn to play Go?",
        "expected_keywords": [
            "deep neural networks",
            "tree search",
            "reinforcement learning",
        ],
    },
    {
        "id": "Q16",
        "question": "What societal risks of AI deployment are described in the document?",
        "expected_keywords": [
            "bias",
            "misinformation",
            "labor displacement",
        ],
    },
    {
        "id": "Q17",
        "question": "Why can AI systems reproduce or amplify cultural biases?",
        "expected_keywords": [
            "historical human data",
            "cultural biases",
        ],
    },
    {
        "id": "Q18",
        "question": "How does the document describe the European Union's AI Act?",
        "expected_keywords": [
            "European Union",
            "AI Act",
            "risk levels",
        ],
    },
    {
        "id": "Q19",
        "question": "What does Artificial General Intelligence (AGI) mean according to the document?",
        "expected_keywords": [
            "Artificial General Intelligence",
            "human cognitive abilities",
        ],
    },
    {
        "id": "Q20",
        "question": "According to the conclusion, what will influence the future of AI?",
        "expected_keywords": [
            "govern",
            "human values",
            "benefits",
        ],
    },
]

(EVAL / "questions.json").write_text(
    json.dumps(questions, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

(EVAL / "metrics.py").write_text(
r'''from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


def normalize_text(value: str) -> str:
    """Normalize text for forgiving, case-insensitive evaluation."""
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def calculate_keyword_match(
    answer: str,
    expected_keywords: Iterable[str],
) -> float:
    """
    Return the fraction of expected keywords/concepts found in the answer.

    Matching is case-insensitive and whitespace-normalized.
    """
    if not expected_keywords:
        return 1.0

    normalized_answer = normalize_text(answer)

    matched = 0

    for keyword in expected_keywords:
        if normalize_text(keyword) in normalized_answer:
            matched += 1

    return matched / len(list(expected_keywords))


def _source_text(source: Any) -> str:
    """Extract textual content from several possible source shapes."""
    if isinstance(source, str):
        return source

    if not isinstance(source, Mapping):
        return ""

    candidates = [
        source.get("text"),
        source.get("content"),
        source.get("chunk_text"),
        source.get("document_text"),
        source.get("page_content"),
    ]

    metadata = source.get("metadata")

    if isinstance(metadata, Mapping):
        candidates.extend(
            [
                metadata.get("text"),
                metadata.get("content"),
                metadata.get("chunk_text"),
                metadata.get("page_content"),
            ]
        )

    return " ".join(
        str(value)
        for value in candidates
        if value
    )


def _source_filename(source: Any) -> str:
    if not isinstance(source, Mapping):
        return ""

    for key in ("filename", "document", "document_name", "source"):
        value = source.get(key)
        if value:
            return str(value)

    metadata = source.get("metadata")

    if isinstance(metadata, Mapping):
        for key in ("filename", "document", "document_name", "source"):
            value = metadata.get(key)
            if value:
                return str(value)

    return ""


def source_contains_expected_keywords(
    source: Any,
    expected_keywords: Iterable[str],
) -> bool:
    text = normalize_text(_source_text(source))

    if not text:
        return False

    keywords = list(expected_keywords)

    if not keywords:
        return True

    # Retrieval is considered relevant when at least one expected
    # concept is present in the retrieved chunk.
    return any(
        normalize_text(keyword) in text
        for keyword in keywords
    )


def calculate_hit_at_k(
    sources: list[Any],
    expected_document: str | None,
    k: int,
    expected_keywords: Iterable[str] | None = None,
) -> float:
    """
    Calculate Hit@K.

    If retrieved chunks contain textual content, keyword evidence is used
    to determine whether the relevant chunk was retrieved.

    If chunks do not expose their text but source filenames are available,
    document-level matching is used.

    This fallback is intentionally conservative and is documented in the
    evaluation README.
    """
    if not sources or k <= 0:
        return 0.0

    top_sources = sources[:k]

    keywords = list(expected_keywords or [])

    if keywords:
        if any(
            source_contains_expected_keywords(source, keywords)
            for source in top_sources
        ):
            return 1.0

    if expected_document:
        expected = normalize_text(expected_document)

        for source in top_sources:
            filename = normalize_text(_source_filename(source))

            if filename and (
                filename == expected
                or expected in filename
                or filename in expected
            ):
                return 1.0

    return 0.0


def calculate_metrics(results: list[Mapping[str, Any]]) -> dict[str, float | int]:
    """Aggregate evaluation results into deterministic metrics."""
    total = len(results)

    if total == 0:
        return {
            "questions": 0,
            "hit_at_1": 0.0,
            "hit_at_3": 0.0,
            "hit_at_5": 0.0,
            "keyword_match_rate": 0.0,
            "passed": 0,
            "failed": 0,
        }

    hit1 = sum(float(result.get("hit_at_1", 0.0)) for result in results)
    hit3 = sum(float(result.get("hit_at_3", 0.0)) for result in results)
    hit5 = sum(float(result.get("hit_at_5", 0.0)) for result in results)

    keyword_rate = sum(
        float(result.get("keyword_match", 0.0))
        for result in results
    )

    passed = sum(
        1
        for result in results
        if bool(result.get("passed", False))
    )

    return {
        "questions": total,
        "hit_at_1": hit1 / total,
        "hit_at_3": hit3 / total,
        "hit_at_5": hit5 / total,
        "keyword_match_rate": keyword_rate / total,
        "passed": passed,
        "failed": total - passed,
    }
''',
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

(EVAL / "evaluator.py").write_text(
r'''from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
DATASET = Path(__file__).resolve().parent / "questions.json"
CORPUS = ROOT / "evaluation_document.txt"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.rag.pipeline import rag_pipeline  # noqa: E402

from evaluation.metrics import (  # noqa: E402
    calculate_hit_at_k,
    calculate_keyword_match,
    calculate_metrics,
)


def load_questions() -> list[dict[str, Any]]:
    with DATASET.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Evaluation dataset must contain a JSON array.")

    return data


def source_list(result: Any) -> list[Any]:
    if not isinstance(result, dict):
        return []

    sources = result.get("sources", [])

    if isinstance(sources, list):
        return sources

    return []


def run_question(item: dict[str, Any]) -> dict[str, Any]:
    question_id = item["id"]
    question = item["question"]
    expected_keywords = item.get("expected_keywords", [])

    result = rag_pipeline.ask(
        question=question,
        top_k=5,
    )

    answer = ""

    if isinstance(result, dict):
        answer = str(result.get("answer", ""))

    sources = source_list(result)

    keyword_match = calculate_keyword_match(
        answer,
        expected_keywords,
    )

    hit1 = calculate_hit_at_k(
        sources,
        CORPUS.name,
        1,
        expected_keywords,
    )

    hit3 = calculate_hit_at_k(
        sources,
        CORPUS.name,
        3,
        expected_keywords,
    )

    hit5 = calculate_hit_at_k(
        sources,
        CORPUS.name,
        5,
        expected_keywords,
    )

    passed = keyword_match >= 0.5 and hit5 == 1.0

    return {
        "id": question_id,
        "question": question,
        "answer": answer,
        "sources": sources,
        "keyword_match": keyword_match,
        "hit_at_1": hit1,
        "hit_at_3": hit3,
        "hit_at_5": hit5,
        "passed": passed,
    }


def print_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> int:
    print("=" * 48)
    print("       CloudRAG RAG Evaluation")
    print("=" * 48)
    print()

    if not CORPUS.exists():
        print(
            f"WARNING: evaluation corpus not found: {CORPUS}"
        )
        print(
            "The evaluator can still run, but the canonical "
            "document name cannot be verified."
        )
        print()

    questions = load_questions()

    results: list[dict[str, Any]] = []

    for index, item in enumerate(questions, start=1):
        print(
            f"[{index:02d}/{len(questions):02d}] "
            f"{item['id']}: {item['question']}"
        )

        try:
            result = run_question(item)
            results.append(result)

            print(
                "       "
                f"Hit@5={print_percent(result['hit_at_5'])} "
                f"Keyword={print_percent(result['keyword_match'])} "
                f"Pass={'YES' if result['passed'] else 'NO'}"
            )

        except Exception as exc:
            print(f"       ERROR: {exc}")

            results.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "answer": "",
                    "sources": [],
                    "keyword_match": 0.0,
                    "hit_at_1": 0.0,
                    "hit_at_3": 0.0,
                    "hit_at_5": 0.0,
                    "passed": False,
                    "error": str(exc),
                }
            )

    metrics = calculate_metrics(results)

    print()
    print("=" * 48)
    print("Retrieval")
    print("-" * 48)
    print(f"Hit@1: {print_percent(metrics['hit_at_1'])}")
    print(f"Hit@3: {print_percent(metrics['hit_at_3'])}")
    print(f"Hit@5: {print_percent(metrics['hit_at_5'])}")
    print()
    print("Answer Quality")
    print("-" * 48)
    print(
        "Keyword Match Rate: "
        f"{print_percent(metrics['keyword_match_rate'])}"
    )
    print()
    print(
        f"Questions Passed: "
        f"{metrics['passed']}/{metrics['questions']}"
    )
    print(
        f"Questions Failed: "
        f"{metrics['failed']}/{metrics['questions']}"
    )
    print("=" * 48)

    return 0 if metrics["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

(EVAL / "test_metrics.py").write_text(
r'''from evaluation.metrics import (
    calculate_hit_at_k,
    calculate_keyword_match,
    calculate_metrics,
)


def test_keyword_match_full():
    answer = "John McCarthy coined the term Artificial Intelligence in 1956."
    keywords = ["John McCarthy", "Artificial Intelligence", "1956"]

    assert calculate_keyword_match(answer, keywords) == 1.0


def test_keyword_match_case_insensitive():
    answer = "DEEP BLUE defeated GARRY KASPAROV."
    keywords = ["deep blue", "garry kasparov"]

    assert calculate_keyword_match(answer, keywords) == 1.0


def test_keyword_match_partial():
    answer = "The system uses GPUs and deep neural networks."
    keywords = ["GPUs", "deep neural networks", "AlexNet"]

    assert calculate_keyword_match(answer, keywords) == 2 / 3


def test_keyword_match_zero():
    answer = "No relevant information was found."
    keywords = ["AlphaGo", "GANs"]

    assert calculate_keyword_match(answer, keywords) == 0.0


def test_empty_keywords():
    assert calculate_keyword_match("anything", []) == 1.0


def test_hit_at_k_from_chunk_text():
    sources = [
        {"text": "Unrelated information."},
        {
            "text": (
                "IBM's Deep Blue defeated Garry Kasparov "
                "in 1997."
            )
        },
    ]

    keywords = ["Deep Blue", "Kasparov"]

    assert calculate_hit_at_k(
        sources,
        "evaluation_document.txt",
        1,
        keywords,
    ) == 0.0

    assert calculate_hit_at_k(
        sources,
        "evaluation_document.txt",
        3,
        keywords,
    ) == 1.0


def test_hit_at_k_document_fallback():
    sources = [
        {"filename": "other.txt"},
        {"filename": "evaluation_document.txt"},
    ]

    assert calculate_hit_at_k(
        sources,
        "evaluation_document.txt",
        1,
    ) == 0.0

    assert calculate_hit_at_k(
        sources,
        "evaluation_document.txt",
        3,
    ) == 1.0


def test_empty_retrieval():
    assert calculate_hit_at_k(
        [],
        "evaluation_document.txt",
        5,
        ["AI"],
    ) == 0.0


def test_aggregate_metrics():
    results = [
        {
            "hit_at_1": 1.0,
            "hit_at_3": 1.0,
            "hit_at_5": 1.0,
            "keyword_match": 1.0,
            "passed": True,
        },
        {
            "hit_at_1": 0.0,
            "hit_at_3": 1.0,
            "hit_at_5": 1.0,
            "keyword_match": 0.5,
            "passed": True,
        },
    ]

    metrics = calculate_metrics(results)

    assert metrics["questions"] == 2
    assert metrics["hit_at_1"] == 0.5
    assert metrics["hit_at_3"] == 1.0
    assert metrics["hit_at_5"] == 1.0
    assert metrics["keyword_match_rate"] == 0.75
    assert metrics["passed"] == 2
    assert metrics["failed"] == 0


def test_empty_aggregate_metrics():
    metrics = calculate_metrics([])

    assert metrics["questions"] == 0
    assert metrics["passed"] == 0
    assert metrics["failed"] == 0
''',
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

(EVAL / "README.md").write_text(
r'''# CloudRAG — RAG Evaluation

## Purpose

This directory contains the Milestone 7A evaluation framework for CloudRAG.

The goal is to measure the existing RAG pipeline rather than create a
separate retrieval implementation.

## Evaluation corpus

Canonical corpus:

`evaluation_document.txt`

The corpus contains material covering:

- AI history
- Dartmouth and the origins of AI
- symbolic AI and GOFAI
- LISP
- AI winters
- expert systems
- machine learning
- Deep Learning
- AlexNet
- GANs
- AlphaGo
- generative AI
- societal risks
- AI governance
- AGI

## Dataset

`questions.json` contains 20 questions covering different parts of the
corpus.

Each question contains:

- `id`
- `question`
- `expected_keywords`

## Metrics

### Hit@1

Checks whether relevant evidence is present in the first retrieved source.

### Hit@3

Checks the first three retrieved sources.

### Hit@5

Checks the first five retrieved sources.

When retrieved source objects expose chunk text, keyword evidence is used
to determine relevance.

When source objects do not expose text, the evaluator falls back to
document-level source matching.

Because this first evaluation corpus contains one canonical document,
document-level fallback should not be interpreted as a strong measure of
chunk retrieval quality. Later Milestone 7 quality work should improve
chunk-level evaluation using stable chunk identifiers and metadata.

### Keyword Match Rate

Measures the fraction of expected concepts appearing in the generated
answer.

Matching is case-insensitive and whitespace-normalized.

### Question Pass

A question currently passes when:

- at least 50% of expected keywords are present in the answer, and
- Hit@5 succeeds.

This is intentionally simple and deterministic.

## Architecture

```text
evaluation/questions.json
          |
          v
     evaluator.py
          |
          v
existing app.rag.pipeline.rag_pipeline
          |
          v
    answer + sources
          |
          v
       metrics
          |
          v
     evaluation report