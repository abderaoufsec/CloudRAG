from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

try:
    from evaluation.metrics import (  # type: ignore
        calculate_hit_at_k,
        calculate_metrics,
        calculate_question_result,
    )
except ModuleNotFoundError:
    from metrics import (  # type: ignore
        calculate_hit_at_k,
        calculate_metrics,
        calculate_question_result,
    )

from app.providers.base import LLMProviderError  # noqa: E402
from app.rag.pipeline import rag_pipeline  # noqa: E402
from app.rag.vector_store import VectorStore  # noqa: E402


DEFAULT_DOCUMENT = ROOT / "evaluation" / "evaluation_document.txt"
DEFAULT_DATASET = ROOT / "evaluation" / "questions.json"


def verify_canonical_corpus(document_path: Path) -> None:
    """Validate the canonical corpus exists and is readable."""
    if not document_path.exists():
        raise FileNotFoundError(
            "Canonical evaluation corpus is missing: "
            f"{document_path}. "
            "Do not substitute another corpus."
        )
    if not document_path.is_file():
        raise ValueError(f"Canonical evaluation corpus is not a file: {document_path}")


def verify_dataset(dataset_path: Path) -> None:
    """Validate dataset file exists and has the requested schema."""
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset is missing: {dataset_path}"
        )


def load_dataset(path: Path) -> list[dict]:
    """Load and validate a question JSON dataset with exactly 20 entries."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("The evaluation dataset must be a JSON list/array.")
    if len(data) != 20:
        raise ValueError("The evaluation dataset must contain exactly 20 questions.")

    seen_ids = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each evaluation entry must be an object.")
        item_id = item.get("id")
        question = item.get("question")
        expected_keywords = item.get("expected_keywords")

        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("Each dataset entry requires a non-empty string 'id'.")
        if item_id in seen_ids:
            raise ValueError(f"Duplicate question id in dataset: {item_id}")
        seen_ids.add(item_id)

        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Question '{item_id}' must be a non-empty string.")

        if not isinstance(expected_keywords, list) or not expected_keywords:
            raise ValueError(
                f"Question '{item_id}' requires a non-empty list of expected_keywords."
            )
        for keyword in expected_keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                raise ValueError(f"Question '{item_id}' has an invalid expected keyword.")

    return data


def process_question_result(
    *,
    id: str,
    question: str,
    answer: str,
    sources: list[dict],
    expected_keywords: list[str],
    pass_threshold: float = 0.5,
) -> dict:
    """Process a single question by calling the same metric result helper."""
    return calculate_question_result(
        id=id,
        question=question,
        answer=answer,
        sources=sources,
        expected_keywords=expected_keywords,
        pass_threshold=pass_threshold,
    )


def evaluate(
    document_path: Path,
    dataset_path: Path,
    top_k: int = 5,
    pass_threshold: float = 0.5,
) -> dict:
    """
    Run an isolated evaluation using the existing CloudRAG RAG pipeline object.
    It indexes the canonical corpus into a temporary VectorStore-backed index by
    swapping the existing pipeline's vector store object in memory.
    """
    verify_canonical_corpus(document_path)
    verify_dataset(dataset_path)

    dataset = load_dataset(dataset_path)
    document_text = document_path.read_text(encoding="utf-8")

    with TemporaryDirectory(prefix="cloudrag-evaluation-") as temp_dir:
        temp_index_dir = Path(temp_dir)
        isolated_store = VectorStore(temp_index_dir)

        original_vector_store = rag_pipeline.vector_store
        rag_pipeline.vector_store = isolated_store

        provider_warning = None
        try:
            rag_pipeline.index_document(
                document_id="evaluation_document.txt",
                text=document_text,
            )

            results = []
            for item in dataset:
                question = item["question"]
                try:
                    answer_result = rag_pipeline.ask(
                        question=question,
                        top_k=top_k,
                        document_id="evaluation_document.txt",
                    )
                    answer = str(answer_result.get("answer", "") or "")
                    sources = list(answer_result.get("sources", []) or [])
                except LLMProviderError as exc:
                    provider_warning = str(exc)
                    sources = rag_pipeline.search(
                        query=question,
                        top_k=top_k,
                        document_id="evaluation_document.txt",
                    )
                    answer = ""

                result = process_question_result(
                    id=item["id"],
                    question=question,
                    answer=answer,
                    sources=sources,
                    expected_keywords=item["expected_keywords"],
                    pass_threshold=pass_threshold,
                )
                results.append(result)
        finally:
            rag_pipeline.vector_store = original_vector_store

    metrics = calculate_metrics(results)
    return {
        "results": results,
        "metrics": metrics,
        "provider_warning": provider_warning,
    }


def render_report(report: dict, *, total_questions: int = 20) -> str:
    """Render the requested plain-text evaluation report."""
    metrics = report["metrics"]
    results = report["results"]
    lines = []
    lines.append("# ========================================")
    lines.append("CloudRAG RAG Evaluation")
    lines.append(f"Questions: {total_questions}")
    lines.append("")
    lines.append("## Retrieval")
    lines.append(f"Hit@1: {metrics['hit_at_1']:.1f}%")
    lines.append(f"Hit@3: {metrics['hit_at_3']:.1f}%")
    lines.append(f"Hit@5: {metrics['hit_at_5']:.1f}%")
    lines.append("")
    lines.append("## Answer Quality")
    lines.append(f"Keyword Match Rate: {metrics['keyword_match_rate']:.1f}%")
    lines.append("")
    lines.append(f"Questions Passed: {metrics['questions_passed']}/{total_questions}")
    lines.append(f"Questions Failed: {metrics['questions_failed']}/{total_questions}")
    lines.append("")
    lines.append(f"Retrieval Failures: {metrics['retrieval_failures']}/{total_questions}")
    lines.append("========================================")
    lines.append("")

    for result in results:
        label = "PASS" if result["passed"] else "FAIL"
        lines.append(f"Q{result['id'].replace('q', '').zfill(2)} {label}")
        lines.append(f"Question: {result['question']}")
        lines.append(f"Keyword Match: {result['keyword_match'] * 100:.1f}%")
        lines.append(f"Hit@1: {'PASS' if result['hit_at_1'] == 1.0 else 'FAIL'}")
        lines.append(f"Hit@3: {'PASS' if result['hit_at_3'] == 1.0 else 'FAIL'}")
        lines.append(f"Hit@5: {'PASS' if result['hit_at_5'] == 1.0 else 'FAIL'}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CloudRAG RAG locally.")
    parser.add_argument("--document", type=Path, default=DEFAULT_DOCUMENT)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--top-k", type=int, default=5, choices=range(1, 21))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    try:
        report = evaluate(
            document_path=args.document,
            dataset_path=args.dataset,
            top_k=args.top_k,
            pass_threshold=args.threshold,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Evaluation setup error: {exc}", file=sys.stderr)
        return 2

    rendered = render_report(report)
    if report.get("provider_warning"):
        print("WARNING: Local Ollama provider is unavailable; retrieval evidence is still evaluated, but answer quality cannot be generated.", file=sys.stderr)
        print(f"Provider message: {report['provider_warning']}", file=sys.stderr)
    print(rendered)

    if args.output:
        output_dir = args.output.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved JSON evaluation report to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
