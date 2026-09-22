# ADR 004: RAG Evaluation Strategy

## Status
Accepted

## Context
CloudRAG needs an evaluation framework to measure retrieval quality and answer correctness. The evaluation should:
- Measure retrieval accuracy (Hit@K metrics)
- Assess answer quality (keyword matching)
- Test multilingual capabilities
- Include adversarial test cases
- Be runnable without external dependencies

## Decision
Implement a custom evaluation framework with Hit@K retrieval metrics, keyword-based answer quality, and a test dataset approach.

### Evaluation Components
- **Retrieval Metrics**: Hit@1, Hit@3, Hit@5
- **Answer Quality**: Keyword match rate
- **Failure Detection**: Retrieval failure counting
- **Test Dataset**: Canonical document + question set with expected keywords
- **Multilingual**: Cross-language test cases
- **Adversarial**: Prompt injection and unrelated query tests

## Rationale

### Custom Framework Benefits
- **Tailored to RAG**: Focused on retrieval grounding, not general QA
- **No external dependencies**: Runs locally without paid APIs
- **Transparent**: Clear what's being measured
- **Extensible**: Easy to add new metrics
- **Portfolio value**: Demonstrates evaluation thinking

### Metric Selection

#### Hit@K
- **What it measures**: Whether relevant content appears in top K results
- **Why important**: Critical for RAG quality
- **Implementation**: Check if expected document appears in top K retrieved chunks

#### Keyword Match
- **What it measures**: Whether answer contains expected information
- **Why important**: Groundedness check
- **Implementation**: Normalized text matching against expected keywords

### Dataset Approach
- **Canonical document**: Single source document for consistency
- **Question set**: 20 questions with varying difficulty
- **Expected keywords**: Minimal set of terms that must appear in answer
- **Multilingual**: Separate document/questions for cross-language testing

## Alternatives Considered

### RAGAS Framework
- **Pros**: Comprehensive metrics (faithfulness, answer relevance, context recall)
- **Cons**: External dependency, requires LLM calls for some metrics
- **Rejected**: Would require OpenAI/other LLM API, adds complexity

### TruLens
- **Pros**: Well-designed, good metrics
- **Cons**: Steeper learning curve, more dependencies
- **Rejected**: Overkill for current needs

### Manual testing only
- **Pros**: Simple, no code
- **Cons**: Not repeatable, not measurable
- **Rejected**: Need automated, measurable evaluation

## Consequences

### Positive
- Automated, repeatable evaluation
- No external dependencies or costs
- Clear metrics for tracking improvement
- Multilingual validation
- Adversarial testing coverage

### Negative
- Keyword matching is simplistic (doesn't catch nuanced errors)
- Hit@K assumes relevant document is known (may not always be true)
- Limited to predefined test cases
- Doesn't measure semantic quality of answers

### Mitigations
- Document metric limitations clearly
- Future could add LLM-based evaluation for semantic quality
- Expand test dataset over time
- Use metrics as guidance, not absolute truth

## Related Decisions
- ADR 001: Vector Store Selection
- ADR 002: Multilingual Embeddings
- ADR 005: Security Model
