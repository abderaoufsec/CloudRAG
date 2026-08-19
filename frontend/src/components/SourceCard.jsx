function SourceCard({
  source,
}) {
  return (
    <div className="source-card">
      <div className="source-icon">
        📎
      </div>

      <div className="source-info">
        <strong>
          {source.filename ||
            source.document_id}
        </strong>

        <span>
          Chunk {source.chunk_index + 1}
        </span>
      </div>

      <div className="source-score">
        {(source.score * 100).toFixed(0)}%
      </div>
    </div>
  );
}


export default SourceCard;