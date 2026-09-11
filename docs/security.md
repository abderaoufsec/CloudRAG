# Security notes

CloudRAG is for trusted local deployment, not public multi-user hosting. Its
ingestion protections include extension allowlisting, server-side filename
sanitization, a 10 MB limit, PDF/DOCX/TXT byte validation, UTF-8 text validation,
and a DOCX extracted-size limit. Uploaded content is stored as data, never executed.

Provider settings and future secrets stay in the backend. `.env` and local data
are ignored by Git. CORS defaults to local browser origins.

The model receives explicit grounding rules and only retrieved evidence. This is a
quality guardrail, not a guarantee; do not upload data you would not trust a local
model runtime to process. Add authentication and HTTPS before network exposure.
