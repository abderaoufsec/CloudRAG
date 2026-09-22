import { useState } from "react";

function Header() {
  const [showSystemInfo, setShowSystemInfo] = useState(false);

  return (
    <header className="header">
      <div className="header-logo">
        <span className="logo-icon">📚</span>
        <div>
          <span className="logo-text">CloudRAG</span>
          <span className="logo-tagline">Multilingual Local-First RAG</span>
        </div>
      </div>

      <div className="header-right">
        <div className="header-status">
          <span className="status-dot"></span>
          Local AI
        </div>

        <button
          className="icon-button"
          onClick={() => setShowSystemInfo(!showSystemInfo)}
          aria-label="System information"
          title="System information"
        >
          ℹ
        </button>
      </div>

      {showSystemInfo && (
        <div className="system-info-panel">
          <div className="system-info-header">
            <h3>System Information</h3>
            <button
              className="close-button"
              onClick={() => setShowSystemInfo(false)}
              aria-label="Close"
            >
              ×
            </button>
          </div>

          <div className="system-info-content">
            <div className="info-section">
              <span className="info-label">Architecture</span>
              <span className="info-value">FastAPI + React</span>
            </div>

            <div className="info-section">
              <span className="info-label">Embeddings</span>
              <span className="info-value">SentenceTransformers</span>
            </div>

            <div className="info-section">
              <span className="info-label">Vector Store</span>
              <span className="info-value">FAISS / Qdrant</span>
            </div>

            <div className="info-section">
              <span className="info-label">LLM</span>
              <span className="info-value">Ollama (Local)</span>
            </div>

            <div className="info-section">
              <span className="info-label">Retrieval</span>
              <span className="info-value">Top-K + Relevance Filter</span>
            </div>

            <div className="info-section">
              <span className="info-label">Security</span>
              <span className="info-value">Upload Validation + Prompt Protection</span>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

export default Header;