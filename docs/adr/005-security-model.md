# ADR 005: Security Model

## Status
Accepted

## Context
CloudRAG handles user-uploaded documents and processes them through an LLM. The security model must address:
- Upload security (malicious files, path traversal, oversized uploads)
- RAG security (prompt injection, secret leakage, ungrounded answers)
- Application security (CORS, trusted hosts, headers)
- Secret management (no hardcoded credentials)

## Decision
Implement defense-in-depth security with upload validation, prompt injection protection, untrusted context treatment, and environment-based secret management.

### Security Layers

#### 1. Upload Validation
- **Filename sanitization**: Reject path traversal, invalid characters, dangerous extensions
- **File type validation**: Magic byte checks for PDF, ZIP structure for DOCX
- **Size limits**: 10MB default, configurable
- **Content validation**: Null byte rejection, encoding checks, ZIP bomb detection
- **Storage**: Store under generated UUID, not user-provided filename

#### 2. RAG Security
- **Untrusted context**: Document content is treated as data, not instructions
- **System prompt**: Explicitly instructs LLM to treat context as evidence only
- **Prompt injection tests**: Verify malicious documents don't override instructions
- **Secret handling**: LLM instructed to refuse secret disclosure requests
- **Abstention**: Low confidence results trigger refusal to answer

#### 3. Application Security
- **CORS**: Configurable allowed origins, defaults to safe values
- **Trusted hosts**: Middleware rejects requests to untrusted hostnames
- **Security headers**: X-Content-Type-Options, X-Frame-Options, CSP
- **Request IDs**: Correlation for debugging without exposing internals

#### 4. Secret Management
- **No hardcoded credentials**: All secrets via environment variables
- **.env ignored**: .env files excluded from git
- **Env examples**: Placeholder values only, no real credentials
- **CI/CD scanning**: Secret scanning in GitHub Actions

## Rationale

### Defense in Depth
Multiple independent security layers reduce risk. If one layer fails, others still protect.

### Upload Security
- **Why**: Users can upload arbitrary files; must protect against file-based attacks
- **Approach**: Validate before processing, reject suspicious content early

### Prompt Injection Protection
- **Why**: Document content could contain malicious instructions
- **Approach**: System prompt explicitly distinguishes context from instructions
- **Testing**: Adversarial test cases verify protection works

### Untrusted Context
- **Why**: RAG systems are vulnerable to injection through retrieved context
- **Approach**: Treat all document content as untrusted data, never as instructions

### Environment Secrets
- **Why**: Credentials in git are a common security mistake
- **Approach**: Environment variables only, .env files gitignored, examples use placeholders

## Alternatives Considered

### No upload validation
- **Pros**: Simpler code
- **Cons**: Vulnerable to path traversal, ZIP bombs, malformed files
- **Rejected**: Unacceptable security risk

### Trust document content as instructions
- **Pros**: More flexible retrieval
- **Cons**: Prompt injection vulnerability
- **Rejected**: Critical security risk

### Hardcode secrets in code
- **Pros**: Simpler deployment
- **Cons**: Secrets exposed in git history
- **Rejected**: Security anti-pattern

### No CORS/trusted host checks
- **Pros**: Simpler setup
- **Cons**: Cross-origin attacks possible
- **Rejected**: Not production-acceptable

## Consequences

### Positive
- Multiple independent security layers
- Protection against common attack vectors
- Clear security model documented
- Test coverage for security behaviors
- Portfolio-ready security posture

### Negative
- More complex upload handling
- Some overhead in validation
- May reject valid edge cases (e.g., unusual filenames)
- System prompt constrains LLM flexibility

### Mitigations
- Clear error messages for rejected uploads
- Document validation rules
- Tests ensure security doesn't break valid use cases
- Configuration options where reasonable

## Related Decisions
- ADR 003: Local LLM Provider
- ADR 004: RAG Evaluation Strategy
