function Header() {
  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-icon">C</div>

        <div>
          <h1>CloudRAG</h1>

          <p>
            Your documents. Your knowledge. Your AI.
          </p>
        </div>
      </div>

      <div className="status-badge">
        <span className="status-dot" />
        Local AI
      </div>
    </header>
  );
}

export default Header;