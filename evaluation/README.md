# CloudRAG Retrieval Evaluation

CloudRAG uses the existing FastAPI backend, SQLAlchemy metadata model, multilingual sentence-transformer embedding model, FAISS vector store, and the local Ollama provider. This evaluation module is a harness around the existing RAG pipeline in the backend rather than a second retrieval implementation.

## Purpose

The evaluation framework measures retrieval and answer quality on the canonical evaluation corpus stored in this repository. It is designed to verify the same evidence-grounded pipeline used by the application.

## Canonical corpus

The source of truth is the canonical corpus:

```text
evaluation/evaluation_document.txt
```

It is deliberately authoritative. Do not replace it with the sample or multilingual corpus files.

## Twenty-question dataset

The project ships with the requested question dataset:

```text
evaluation/questions.json
```

The dataset must contain exactly 20 entries, each with:

- `id`
- `question`
- `expected_keywords`

It is validated by the evaluator before any scoring begins.

## Metrics

The metrics module calculates:

- Hit@1
- Hit@3
- Hit@5
- keyword match rate
- question pass/fail totals
- retrieval failure count

A retrieval hit is recorded when a retrieved source chunk contains evidence for one of the expected keywords. Keyword matching is case-insensitive, whitespace-normalized, and accepts partial keyword coverage.

## Architecture

The evaluator uses the existing CloudRAG RAG pipeline object from `app.rag.pipeline` rather than creating another vector store or a new retrieval loop. It indexes the canonical corpus through the same pipeline object with an isolated vector store only for the evaluation run.

## How evaluation works

The command below runs the default evaluator from the repository root:

```powershell
python evaluation\evaluator.py
```

The evaluator:

1. verifies the canonical corpus exists,
2. verifies the question dataset exists and is well formed,
3. indexes the canonical corpus through `rag_pipeline.index_document(...)`,
4. calls `rag_pipeline.ask(...)` for each question,
5. falls back to retrieval source search when the local LLM provider is unavailable,
6. writes a readable report and optionally a JSON file.

## How to run

```powershell
python evaluation\evaluator.py
python evaluation\evaluator.py --top-k 5
python evaluation\evaluator.py --output evaluation\reports\report.json
```

## Expected local dependencies

The evaluator expects:

- a working workspace Python environment;
- the backend on the Python path;
- the existing vector store and embedding stack;
- a local Ollama server when answer generation is required.

If Ollama is unavailable, the evaluator should report that clearly and continue reporting retrieval evidence only.

## How to interpret results

The output report prints aggregate retrieval metrics and answer-quality metrics. It then prints per-question results with a PASS/FAIL label. A question passes when keyword overlap reaches the configured threshold and retrieval succeeds.

The default pass threshold is 50% coverage:

```python
PASS_THRESHOLD = 0.5
```

## Limitations

This evaluation intentionally uses the project’s existing retrieval pipeline and source fields. It does not implement page-aware citations or add new provider dependencies. It is a local benchmark harness for the current CloudRAG architecture.

