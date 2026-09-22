import { useState } from "react";

function SourceCard({
  source,
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="source-card">
      <div className="source-header">
        <div className="source-title">
          <strong title={source.filename || source.document_id}>
            {source.filename || source.document_id}
          </strong>

          <div className="source-meta">
            {source.page && `Page ${source.page}`}
            {source.page && source.chunk_index !== undefined && " · "}
            {source.chunk_index !== undefined && `Chunk ${source.chunk_index + 1}`}
            {source.score !== undefined && ` · Relevance ${(source.score * 100).toFixed(0)}%`}
          </div>
        </div>

        {source.text && (
          <button
            className="source-expand"
            onClick={() => setExpanded(!expanded)}
            aria-label={expanded ? "Hide source text" : "Show source text"}
          >
            {expanded ? "−" : "+"}
          </button>
        )}
      </div>

      {expanded && source.text && (
        <div className="source-text">
          {source.text}
        </div>
      )}
    </article>
  );
}


export default SourceCard;
