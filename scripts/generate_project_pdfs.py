"""Generate CloudRAG's technical report and academic defense dossier."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")


def register_fonts():
    pdfmetrics.registerFont(TTFont("CloudRAG", str(FONT)))
    pdfmetrics.registerFont(TTFont("CloudRAG-Bold", str(FONT_BOLD)))


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="CloudRAG-Bold", fontSize=29,
            leading=35, textColor=colors.HexColor("#10243F"), alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName="CloudRAG", fontSize=13,
            leading=19, textColor=colors.HexColor("#4C617A"), alignment=TA_CENTER,
        ),
        "heading": ParagraphStyle(
            "heading", parent=base["Heading1"], fontName="CloudRAG-Bold", fontSize=21,
            leading=26, textColor=colors.HexColor("#0D5C63"), spaceAfter=13,
        ),
        "subheading": ParagraphStyle(
            "subheading", parent=base["Heading2"], fontName="CloudRAG-Bold", fontSize=12,
            leading=16, textColor=colors.HexColor("#10243F"), spaceBefore=8, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName="CloudRAG", fontSize=10.3,
            leading=15.1, textColor=colors.HexColor("#202B38"), spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["BodyText"], fontName="CloudRAG", fontSize=10,
            leading=14.5, leftIndent=16, firstLineIndent=-10, spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "small", parent=base["BodyText"], fontName="CloudRAG", fontSize=8.5,
            leading=11, textColor=colors.HexColor("#526170"),
        ),
        "quote": ParagraphStyle(
            "quote", parent=base["BodyText"], fontName="CloudRAG-Bold", fontSize=11,
            leading=16, textColor=colors.HexColor("#0D5C63"), leftIndent=14,
            borderColor=colors.HexColor("#57C4C5"), borderWidth=1, borderPadding=8,
            spaceBefore=7, spaceAfter=9,
        ),
    }


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D7E0E9"))
    canvas.line(1.65 * cm, 1.55 * cm, 19.35 * cm, 1.55 * cm)
    canvas.setFont("CloudRAG", 8.5)
    canvas.setFillColor(colors.HexColor("#526170"))
    canvas.drawString(1.65 * cm, 1.0 * cm, "CloudRAG AI - Local-First RAG Project")
    canvas.drawRightString(19.35 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


def p(text, style):
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def table(rows, s):
    header_style = ParagraphStyle(
        "table-header", parent=s["small"], fontName="CloudRAG-Bold",
        textColor=colors.white, fontSize=9.2, leading=11,
    )
    cell_style = ParagraphStyle(
        "table-cell", parent=s["small"], fontName="CloudRAG", fontSize=8.9,
        leading=11.2, textColor=colors.HexColor("#202B38"),
    )
    formatted_rows = [
        [p(str(cell), header_style if row_number == 0 else cell_style) for cell in row]
        for row_number, row in enumerate(rows)
    ]
    result = Table(formatted_rows, colWidths=[5.25 * cm, 12.15 * cm], repeatRows=1)
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10243F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "CloudRAG-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "CloudRAG"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.3),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E0E9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F8FA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return result


def section_story(number, title, overview, details, decisions, evidence, s):
    story = [p(f"{number:02d}. {title}", s["heading"]), p(overview, s["body"])]
    story.append(p("Implementation detail", s["subheading"]))
    story.extend(p(f"- {item}", s["bullet"]) for item in details)
    story.append(p("Engineering decision", s["subheading"]))
    story.append(p(decisions, s["quote"]))
    story.append(p("How it was verified", s["subheading"]))
    story.extend(p(f"- {item}", s["bullet"]) for item in evidence)
    story.append(Spacer(1, 0.25 * cm))
    return story


def report_sections():
    common = [
        ("Executive summary", "CloudRAG AI is a local-first, multilingual Retrieval-Augmented Generation application. It lets a user upload documents and receive answers that are grounded in retrieved passages rather than unsupported model knowledge.", ["React and Vite provide the browser interface.", "FastAPI owns ingestion, retrieval, persistence, and model access.", "SQLite and FAISS keep the knowledge base local and reproducible."], "The project deliberately favors a dependable local architecture over cloud complexity or recurring cost.", ["Docker services started healthy.", "Backend test suite passed with 25 tests."]),
        ("Problem statement", "General-purpose chatbots cannot prove that an answer came from a user's files. CloudRAG addresses this by retrieving evidence before generation and returning the chunks that supported the answer.", ["Users need PDF, TXT, and DOCX ingestion.", "Answers must include source identity and chunk reference.", "Weak retrieval must produce an insufficient-evidence answer."], "Evidence must be a required input to the LLM, not a decorative UI feature.", ["Live unrelated-question request returned no sources.", "Live supported questions returned sources."]),
        ("Objectives and scope", "The finished local product focuses on document intelligence: safe ingestion, semantic search, grounded generation, citations, multilingual behavior, persistence, testing, and reproducible deployment.", ["English, French, and Arabic questions are in scope.", "Local Ollama is the only active LLM provider.", "Public cloud deployment and paid services are explicitly out of scope."], "A narrow scope made it possible to complete and verify the important RAG path end to end.", ["No Azure, OCI, OpenRouter, or paid dependency is required."]),
        ("Technology stack", "The stack is intentionally small and transparent: React/Vite, FastAPI, SQLAlchemy/SQLite, SentenceTransformers, FAISS, Ollama, Docker, and pytest.", ["SentenceTransformers supplies local multilingual embeddings.", "FAISS provides fast inner-product similarity search.", "Ollama hosts qwen3:8b on the Windows machine."], "Each component can run locally and has a clear responsibility.", ["Docker built a CPU-only backend image successfully."]),
        ("Repository structure", "The repository separates backend code, frontend code, evaluation fixtures, deployment files, documentation, and runtime data.", ["backend/app contains APIs, services, RAG code, providers, and database modules.", "frontend contains the React components and API client.", "data holds documents, processed text, FAISS state, and SQLite at runtime."], "Runtime data is ignored by Git so private user documents are not committed.", ["Compose bind-mount inspection confirmed every persistent data path."]),
        ("Development milestones", "CloudRAG was developed incrementally from a FastAPI foundation through ingestion, retrieval, local RAG, persistence, frontend, quality/security, and Docker deployment.", ["Each milestone introduced a verifiable part of the system.", "Tests were expanded instead of replacing the original baseline.", "The final work focused on regression testing and operational readiness."], "Incremental development reduced risk and kept failures diagnosable.", ["Final backend suite: 25 passing tests."]),
        ("Backend API design", "FastAPI exposes health, document, and RAG endpoints. Pydantic request models validate question length, top-k limits, and optional document filtering before processing.", ["POST /api/documents/upload stores and indexes a valid document.", "GET /api/documents lists the local knowledge base.", "POST /api/rag/ask returns answer plus actual retrieved sources."], "The frontend talks only to the backend; it never communicates with Ollama directly.", ["Health endpoint returned production/local status from Docker."]),
        ("Document upload flow", "An upload is read, validated, stored under a generated identifier, hashed for duplicate detection, extracted, processed, indexed, and recorded in SQLite.", ["Original files are placed in data/documents.", "Extracted UTF-8 text is placed in data/processed.", "Metadata includes status, sizes, counts, and error state."], "Generated storage names prevent user-controlled filesystem paths.", ["A real TXT upload was indexed in the live stack."]),
        ("PDF, TXT, and DOCX extraction", "The processing service routes each supported extension to an appropriate reader. PDF uses pypdf, DOCX uses python-docx, and text files require UTF-8.", ["Empty extracted content is rejected.", "Whitespace is cleaned before chunking.", "File type is retained as metadata for the interface."], "Keeping extractors small makes failures visible and testable.", ["Upload validation tests cover supported and unsupported content."]),
        ("Upload security", "Ingestion is constrained before file processing. The server allowlists extensions, sanitizes filenames, applies a size limit, validates bytes, and never executes user content.", ["PDF uploads must start with a PDF signature.", "DOCX uploads must contain expected ZIP entries and respect a 50 MB expanded-size limit.", "TXT and Markdown uploads reject null bytes and non-UTF-8 content."], "Validation is performed server-side; browser validation alone is never trusted.", ["Security-related tests are included in the passing backend suite."]),
        ("Chunking strategy", "Extracted text is normalized and split into overlapping character chunks. Each chunk retains a stable document identifier and chunk index.", ["Default chunk size is 800 characters.", "Default overlap is 120 characters.", "Empty input returns no chunks."], "Simple, inspectable chunking is suitable for a first complete local RAG system and can be refined later.", ["Chunking tests cover creation, empty text, and parameter validation."]),
        ("Multilingual embeddings", "CloudRAG uses the multilingual paraphrase-multilingual-MiniLM-L12-v2 model locally. Questions and chunks are embedded in the same vector space.", ["The model supports semantic matching beyond exact keyword overlap.", "The same pipeline handles English, French, and Arabic Unicode.", "Embedding loading is cached for repeated use."], "A multilingual local model avoids a translation dependency and supports cross-language retrieval.", ["Live English, French, and Arabic requests were executed."]),
        ("FAISS vector search", "FAISS stores float32 embedding vectors with JSON metadata. Search returns the best inner-product matches and merges their scores with stored source information.", ["Index state is written to data/index/cloudrag.index.", "Chunk metadata is written to data/index/metadata.json.", "Deletion rebuilds the index without the deleted document's chunks."], "FAISS is free, local, fast, and appropriate for a personal knowledge base.", ["Vector-store filtering behavior has dedicated automated coverage."]),
        ("Selected-document retrieval", "The user may select a document in the sidebar. The question is then sent with a document identifier and the backend filters FAISS results to that document.", ["The API validates the document identifier.", "FAISS retrieves enough candidates to make filtering correct.", "Keyboard selection is supported in the frontend."], "A visual selection must change retrieval behavior; otherwise it would mislead the user.", ["A dedicated test confirms the filter reaches retrieval."]),
        ("Confidence filtering", "The RAG pipeline filters low-scoring search results before building the prompt. If nothing survives, it returns an insufficient-evidence answer without invoking the LLM.", ["The current threshold is 0.30.", "Context is capped at 12,000 characters.", "No source is fabricated when retrieval is weak."], "The threshold was calibrated after a live Arabic match scored 0.327 and was initially rejected at 0.35.", ["An unrelated live question returned no source and no generated answer."]),
        ("Context construction", "Only retrieved chunk text, document identifiers, and chunk positions are prepared as evidence. Context is clearly separated from system instructions and the user question.", ["Each context part begins with a source label.", "The size cap is applied before model invocation.", "Sources returned to the UI are exactly the retrieved sources."], "Delimited evidence makes prompt behavior easier to inspect and reduces instruction confusion.", ["Context-size and source tests are passing."]),
        ("Local LLM provider", "The LocalOllamaProvider owns all communication with Ollama. It reads URL, model name, and timeout from application settings instead of hardcoding machine-specific values.", ["Default model: qwen3:8b.", "Default development URL: localhost:11434.", "Compose URL: host.docker.internal:11434."], "The provider boundary isolates model transport from the RAG pipeline.", ["Container-to-host model discovery listed qwen3:8b."]),
        ("Grounding prompt", "The provider sends a system prompt that requires answers to use only supplied document context, treat inputs as untrusted data, avoid invented citations, and admit insufficient evidence.", ["Questions do not become executable instructions.", "Context is evidence, not privileged system policy.", "The requested answer language should follow the user's question."], "Prompting is a guardrail layered on top of retrieval and confidence filtering, not a substitute for them.", ["Live answers were grounded in the uploaded test document."]),
        ("Provider architecture", "An abstract LLMProvider interface defines generate(question, context). The factory currently selects only LocalOllamaProvider; unsupported provider values fail clearly.", ["RAG code depends on the interface, not Ollama imports.", "A future cloud provider needs a new implementation and one factory branch.", "No fake cloud provider was created."], "This preserves cloud readiness without forcing cost or credentials into local development.", ["Factory and local-provider tests pass."]),
        ("Ollama error handling", "Connection or model errors are converted to LLMProviderError and exposed through the API as a user-safe HTTP 503 response.", ["No backend stack trace is returned to normal users.", "The frontend shows an understandable local-AI failure message.", "Logs retain operational detail for diagnosis."], "A local service failure should be actionable for the user and safe for the application.", ["HTTP 503 behavior has automated test coverage."]),
        ("SQLite metadata", "SQLite stores document identity, filename, type, hash, status, counts, timestamps, and processing errors. It is the source of truth for the sidebar document list.", ["Duplicate uploads are detected with a content hash.", "Processing progress is recorded as processing, indexed, or failed.", "Deletion removes the metadata and corresponding RAG chunks."], "SQLite keeps local setup simple while providing reliable structured metadata.", ["Repository create, find, and list tests pass."]),
        ("Persistence model", "The local data folder preserves four complementary artifacts: originals, extracted text, FAISS index/metadata, and SQLite database.", ["Documents can be displayed and reprocessed later.", "FAISS can answer without recomputing all embeddings after restart.", "Metadata links files and chunks to the user-facing document record."], "Persistence is deliberately filesystem-based; no external database or storage service is required.", ["Full Compose down/up retained all tested data paths."]),
        ("Frontend experience", "The React interface presents a Knowledge Base sidebar, upload zone, document list, chat area, suggestions, loading state, answer messages, and source cards.", ["Upload supports drag-and-drop and a file picker.", "Long filenames, mobile layout, focus states, and clear errors are handled in CSS.", "Messages use automatic direction for Arabic content."], "The interface explains that answers are document-grounded instead of presenting a generic chatbot.", ["Production Vite build completed cleanly."]),
        ("Accessibility and responsiveness", "Interactive elements have semantic roles or native controls, keyboard handling, visible focus outlines, labels, and accessible alerts.", ["Document cards work with Enter and Space.", "Deletion buttons carry descriptive labels.", "The chat input has an explicit accessible label."], "Accessibility is part of product quality, not an optional visual enhancement.", ["Frontend source was reviewed and production-built."]),
        ("Citations and source cards", "The API enriches retrieved chunk information with the stored filename. The UI presents the filename, chunk reference, and relevance score without inventing page data.", ["Source cards are created only from API sources.", "The system does not cite documents that were not retrieved.", "Source identity remains visible after the answer."], "Citations make the RAG behavior inspectable and defendable in a demonstration.", ["Live RAG results returned the test filename and chunk identifier."]),
        ("CORS and configuration", "Settings are read from environment variables and optional backend/.env files. Compose declares local production origins and no secrets.", ["CORS is limited to the local frontend addresses in Compose.", "Ollama, model, threshold, context size, and timeout are configurable.", "The frontend build uses VITE_API_URL only when an override is needed."], "Configuration is separated from source code so environments can change safely.", ["Compose configuration validation completed successfully."]),
        ("Docker backend image", "The backend image uses Python 3.12 slim, a non-root application user, Uvicorn, and a CPU-only PyTorch wheel before application dependencies.", ["CPU-only PyTorch avoids unnecessary CUDA runtime layers.", "The container exposes port 8000.", "A Python health check calls /api/health."], "The image was corrected after identifying inappropriate CUDA-oriented dependency weight for a local CPU container.", ["Backend image rebuilt successfully."]),
        ("Docker frontend image", "The frontend uses a Node build stage and a minimal Nginx runtime stage. The resulting static bundle is served on port 8080 of the host.", ["npm ci makes the dependency install reproducible.", "The former cloud runtime config injection was removed.", "Nginx health check verifies HTTP service response."], "A static production frontend is simpler and more robust than carrying development configuration into runtime.", ["Frontend image built and served HTTP 200."]),
        ("Compose orchestration", "compose.yml defines backend and frontend services, ports, restart behavior, health checks, service ordering, and a bind mount for local data.", ["Frontend waits for backend health.", "Backend mount is ./data to /app/data.", "No database, Redis, or Ollama container is introduced."], "Compose gives a one-command local deployment while respecting the existing storage architecture.", ["docker compose config, build, up, ps, and logs were run."]),
        ("Docker persistence verification", "A real document was uploaded, indexed, and queried. Containers were fully stopped and removed with docker compose down, then recreated.", ["cloudrag.db remained present.", "FAISS index and metadata remained present.", "The original file and processed text remained present."], "Persistence was tested with the actual bind mount, not assumed from configuration alone.", ["Post-restart API listed stored documents and a RAG query succeeded."]),
        ("Automated testing", "The backend test suite covers health, upload behavior, repositories, chunking, evaluation metrics, RAG quality, vector-store filtering, provider selection, provider error handling, and API failure behavior.", ["Tests isolate database and filesystem state where appropriate.", "RAG quality tests mock the provider rather than requiring Ollama.", "The suite protects against regressions in security and retrieval behavior."], "Deterministic tests complement live tests that depend on embeddings and a local model.", ["Final run: 25 passed in under one second."]),
        ("Retrieval evaluation", "The evaluator creates a temporary FAISS index and measures whether expected evidence appears in the top results. It does not invoke Ollama, so it measures retrieval rather than model fluency.", ["Metrics: Hit@1, Hit@3, and Hit@5.", "Fixture covers English, French, Arabic, and cross-language examples.", "Dataset contains multiple sections so ranking is meaningful."], "Metrics are reported honestly as retrieval evidence checks, not as a claim of overall answer accuracy.", ["Measured fixture result: Hit@1 0.50, Hit@3 0.75, Hit@5 1.00."]),
        ("Live end-to-end validation", "The final validation used Docker, host Ollama, an uploaded document, the public API, and the persistent data directory together.", ["English refund question returned the 30-day receipt policy with a source.", "French refund question returned a French grounded answer with a source.", "Arabic privacy question returned the correct Arabic answer with a source."], "End-to-end proof is essential because unit tests alone cannot prove network, model, index, and persistence integration.", ["All three language requests returned HTTP 200 during validation."]),
        ("Operational workflow", "For normal use, start Ollama, ensure qwen3:8b exists, run docker compose up --build -d, open localhost:8080, upload, select optionally, and ask questions.", ["Use docker compose ps for service health.", "Use docker compose logs backend for diagnosis.", "Use docker compose down to stop without losing data."], "The operation sequence is intentionally short enough for a classroom demonstration.", ["README and deployment documentation include exact commands."]),
        ("Troubleshooting guide", "Most local failures have clear checks: Docker status, port availability, Ollama model presence, backend health, and backend logs.", ["Run ollama list to confirm model availability.", "Run docker compose ps to confirm healthy services.", "Check localhost:8000/api/health and localhost:8080 separately."], "Troubleshooting starts at the dependency boundary before changing application code.", ["Live health and HTTP checks were executed at final validation."]),
        ("Known limitations", "The current system is a local single-user knowledge base. It has no authentication, OCR pipeline, multi-user isolation, background job queue, or managed cloud deployment.", ["Scanned image-only PDFs need OCR before extraction.", "FAISS is local and single-process.", "Embedding and LLM first-request latency depends on local model availability."], "These limits are documented rather than hidden; they define responsible future work.", ["The project remains fully usable for its stated local scope."]),
        ("Future work", "Future improvements can add OCR, page-aware citations, reranking, hybrid search, collections, authentication, and an optional cloud provider behind the existing interface.", ["A future CloudLLMProvider can be added without rewriting RAG.", "Managed storage can be introduced only if deployment requirements justify it.", "Evaluation can grow into a larger human-reviewed benchmark."], "Future features should preserve the local-first default and explicit cost control.", ["No future work is required for the validated current local product."]),
        ("Conclusion", "CloudRAG demonstrates a complete document-grounded assistant rather than a generic chat interface. Its value comes from the full chain: validation, extraction, indexing, retrieval, confidence filtering, grounded generation, citations, persistence, and reproducible operation.", ["The product runs locally in Docker.", "The model integration is modular.", "The project is ready for a technical demonstration or portfolio review."], "The strongest defense is evidence: every major path was implemented, tested, and documented locally.", ["Final Docker services remained healthy at completion."]),
    ]
    return common


def build_report():
    s = styles()
    story = [Spacer(1, 3.3 * cm), p("CloudRAG AI", s["title"]), p("Complete Technical Project Report", s["subtitle"]), Spacer(1, 0.65 * cm), p("A local-first multilingual Retrieval-Augmented Generation application", s["subtitle"]), Spacer(1, 4.5 * cm), p("Prepared as a portfolio-ready technical record", s["subtitle"]), PageBreak()]
    story += [p("Document purpose", s["heading"]), p("This report explains how CloudRAG AI was designed, built, tested, deployed, and validated. It describes the finished local application rather than an abstract plan. The report is suitable for a project supervisor, examiner, recruiter, or future maintainer.", s["body"]), p("Reading guide", s["subheading"]), table([["Part", "Coverage"], ["Foundation", "Objectives, stack, repository, milestones, API"], ["RAG system", "Ingestion, chunking, embeddings, FAISS, providers, grounding"], ["Quality", "Security, testing, evaluation, multilingual behavior"], ["Operations", "Docker, persistence, workflow, troubleshooting, future work"]], s), Spacer(1, 0.5 * cm), p("The report contains 40 numbered technical sections following this page.", s["quote"]), PageBreak()]
    for index, (title, overview, details, decision, evidence) in enumerate(report_sections(), start=1):
        story += section_story(index, title, overview, details, decision, evidence, s)
        story.append(PageBreak())
    story += [p("Appendix A. Key environment variables", s["heading"]), table([["Variable", "Purpose"], ["LLM_PROVIDER", "Selects the local provider implementation."], ["OLLAMA_BASE_URL", "Ollama host URL; Docker uses host.docker.internal."], ["OLLAMA_MODEL", "The locally installed model, normally qwen3:8b."], ["OLLAMA_TIMEOUT_SECONDS", "Maximum duration for a model request."], ["MIN_RETRIEVAL_SCORE", "Filters weak FAISS results before generation."], ["MAX_RAG_CONTEXT_CHARACTERS", "Bounds evidence passed to the LLM."], ["CORS_ORIGINS", "Allowed browser origins for the API."]], s), Spacer(1, 0.7 * cm), p("Appendix B. Reproducible commands", s["heading"]), p("docker compose up --build -d\ndocker compose ps\npython -m pytest backend/tests -q\ncd frontend; npm run build", s["body"])]
    doc = SimpleDocTemplate(str(OUTPUT / "CloudRAG_AI_Technical_Report.pdf"), pagesize=A4, rightMargin=1.65*cm, leftMargin=1.65*cm, topMargin=1.8*cm, bottomMargin=2.1*cm, title="CloudRAG AI - Technical Report", author="CloudRAG AI")
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)


def defense_pages():
    return [
        ("Executive brief", "CloudRAG AI is a local-first multilingual RAG application that answers questions from uploaded files while showing the evidence used.", ["Problem: generic chatbots cannot prove an answer came from user documents.", "Solution: retrieve relevant chunks first, then generate a constrained answer.", "Result: a Docker-deployed, tested local product with citations."]),
        ("The problem to defend", "A useful document assistant must be more trustworthy than a generic chatbot. It needs traceable evidence, safe ingestion, and a predictable local deployment.", ["Why RAG? It inserts retrieval between question and generation.", "Why sources? They let a user inspect the support for an answer.", "Why local-first? It avoids mandatory cloud cost and protects development autonomy."]),
        ("User journey", "The demonstration workflow is simple: start the stack, upload a file, let it be indexed, ask a question, read the answer, and inspect sources.", ["Upload PDF, TXT, or DOCX.", "Optionally select one document to narrow retrieval.", "Ask in English, French, or Arabic."]),
        ("Architecture", "The browser uses React/Vite. FastAPI processes documents and controls RAG. SentenceTransformers produces embeddings, FAISS retrieves chunks, Ollama generates the final grounded answer.", ["SQLite: document metadata.", "Filesystem: originals and processed text.", "FAISS: vector index and retrieval metadata."]),
        ("Document ingestion", "The backend validates a file before extraction and indexing. It stores data under generated identifiers and records the outcome in SQLite.", ["Extensions are allowlisted.", "Bytes are checked for PDF, DOCX, and UTF-8 text.", "Duplicate uploads use a content hash."]),
        ("Retrieval pipeline", "Question -> embedding -> FAISS -> confidence filter -> bounded context -> local provider -> answer plus sources.", ["Every source originates from a retrieved chunk.", "Weak evidence stops generation.", "Selected-document mode filters retrieval correctly."]),
        ("Grounding and hallucination control", "CloudRAG does not promise impossible perfection, but it uses several defenses: confidence filtering, a strict system prompt, bounded evidence, and no fabricated citations.", ["No relevant chunk: insufficient-evidence response.", "Ollama receives evidence only after retrieval.", "Prompt tells the model to use supplied documents only."]),
        ("Multilingual capability", "The embedding model is multilingual, so query and document can be in different supported languages. The UI preserves Unicode and automatic text direction for Arabic messages.", ["English live test: refund policy answer and citation.", "French live test: grounded policy answer and citation.", "Arabic live test: correct privacy answer and citation."]),
        ("Provider architecture", "The RAG pipeline depends on an LLMProvider interface, not directly on Ollama. LocalOllamaProvider is active today; a future cloud provider can be added safely later.", ["Settings control host, model, timeout, and provider choice.", "No paid cloud model is required.", "Provider failures become a clean HTTP 503."]),
        ("Security", "The project treats uploads and prompts as untrusted input. It avoids path traversal, oversized files, invalid document structures, null text files, and archive expansion attacks.", ["Browser has no model credentials.", "CORS is local and explicit.", "Runtime data and environment files are excluded from Git."]),
        ("Docker and persistence", "Docker Compose starts frontend and backend with health checks. Ollama remains on the Windows host. A bind mount preserves all local data across container recreation.", ["Backend: port 8000.", "Frontend: port 8080.", "Persisted: SQLite, FAISS, metadata, originals, processed text."]),
        ("Testing and evaluation", "Automated tests validate core application behavior; a separate evaluator measures retrieval Hit@K without mixing in model fluency.", ["25 backend tests passed.", "Frontend production build passed.", "Multilingual retrieval fixture: Hit@1 0.50, Hit@3 0.75, Hit@5 1.00."]),
        ("Live validation evidence", "The final validation ran the real Docker stack, reached Ollama from inside the backend container, uploaded a document, queried it, restarted containers, and queried data again.", ["Containers healthy.", "Frontend HTTP 200.", "Backend health endpoint returned production/local status."]),
        ("Demo script", "Open localhost:8080. Upload a short policy file. Ask: 'What is the refund policy?' Show the answer and source card. Then ask an unrelated question and show the insufficient-evidence response.", ["Explain the evidence-first path while answering.", "Show document selection to restrict scope.", "Optionally demonstrate French or Arabic."]),
        ("Likely examiner questions", "Why FAISS instead of a cloud vector database? Why not allow the LLM to answer without context? What happens when Ollama is down? How is persistence guaranteed?", ["FAISS is local, free, and sufficient for this scope.", "No-context generation breaks document grounding.", "Ollama failure returns HTTP 503 and a helpful UI message.", "Compose bind-mount persistence was tested with down/up."]),
        ("Limitations and next steps", "The project is intentionally local and single-user. OCR, authentication, multi-user isolation, reranking, page-aware citations, and optional cloud deployment are future upgrades.", ["The core RAG flow is already complete and verified.", "Future work should preserve local-first and cost control.", "The provider interface enables expansion without a rewrite."]),
        ("Closing defense statement", "CloudRAG is not just a chatbot interface. It is a complete, observable RAG product: safe files become indexed knowledge; questions retrieve evidence; the local model answers from that evidence; and the user sees the sources.", ["It works locally without a paid cloud account.", "It is tested, documented, persistent, and containerized.", "It is ready for a live academic or portfolio demonstration."]),
    ]


def build_defense():
    s = styles()
    story = [Spacer(1, 3.4 * cm), p("CloudRAG AI", s["title"]), p("Academic Defense Dossier", s["subtitle"]), Spacer(1, 0.7 * cm), p("A professional guide for presenting and defending the project", s["subtitle"]), Spacer(1, 4.6 * cm), p("Local-first multilingual RAG - architecture, evidence, and demonstration", s["subtitle"]), PageBreak()]
    for page_no, (title, overview, points) in enumerate(defense_pages(), start=1):
        story += [p(f"Defense {page_no:02d}. {title}", s["heading"]), p(overview, s["body"]), Spacer(1, 0.25*cm), p("What to say", s["subheading"])]
        story.extend(p(f"- {point}", s["bullet"]) for point in points)
        story += [Spacer(1, 0.5*cm), p("Defense line", s["subheading"]), p("I designed the project so that the answer is traceable to retrieved document evidence, remains affordable to develop, and can be demonstrated reliably on a local machine.", s["quote"]), PageBreak()]
    story += [p("One-minute conclusion", s["heading"]), p("CloudRAG AI transforms a local document collection into a multilingual, evidence-based assistant. Its strongest technical point is not simply that it calls a language model: it validates input, persists knowledge, retrieves evidence semantically, filters weak matches, constrains the model, and exposes sources to the user. The final system is containerized, tested, and operational without a paid cloud provider.", s["body"])]
    doc = SimpleDocTemplate(str(OUTPUT / "CloudRAG_AI_Defense_Dossier.pdf"), pagesize=A4, rightMargin=1.65*cm, leftMargin=1.65*cm, topMargin=1.8*cm, bottomMargin=2.1*cm, title="CloudRAG AI - Academic Defense Dossier", author="CloudRAG AI")
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)


if __name__ == "__main__":
    register_fonts()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    build_report()
    build_defense()
    print("Created CloudRAG AI PDF documents in output/pdf")
