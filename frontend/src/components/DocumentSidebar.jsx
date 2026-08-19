import UploadZone from "./UploadZone";

function DocumentSidebar({
  documents,
  selectedDocument,
  onSelectDocument,
  onUpload,
  onDelete,
  uploading,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div>
          <span className="eyebrow">
            Knowledge Base
          </span>

          <h2>Documents</h2>
        </div>

        <span className="document-count">
          {documents.length}
        </span>
      </div>

      <UploadZone
        onUpload={onUpload}
        uploading={uploading}
      />

      <div className="document-list">
        {documents.length === 0 ? (
          <div className="empty-documents">
            <span>📚</span>

            <p>
              No documents yet.
            </p>

            <small>
              Upload your first document to
              start asking questions.
            </small>
          </div>
        ) : (
          documents.map((document) => (
            <div
              key={document.document_id}
              className={`document-item ${
                selectedDocument ===
                document.document_id
                  ? "selected"
                  : ""
              }`}
              onClick={() =>
                onSelectDocument(
                  document.document_id
                )
              }
            >
              <div className="document-icon">
                {getFileIcon(
                  document.file_type
                )}
              </div>

              <div className="document-info">
                <strong title={document.filename}>
                  {document.filename}
                </strong>

                <span>
                  {document.chunk_count} chunks
                  {" · "}
                  {formatBytes(
                    document.file_size_bytes
                  )}
                </span>
              </div>

              <button
                className="delete-button"
                title="Delete document"
                onClick={(event) => {
                  event.stopPropagation();

                  onDelete(
                    document.document_id
                  );
                }}
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}


function getFileIcon(type) {
  switch (type) {
    case ".pdf":
      return "📕";

    case ".docx":
      return "📘";

    case ".md":
      return "📝";

    default:
      return "📄";
  }
}


function formatBytes(bytes) {
  if (!bytes) {
    return "0 B";
  }

  const units = [
    "B",
    "KB",
    "MB",
    "GB",
  ];

  const index = Math.floor(
    Math.log(bytes) /
      Math.log(1024)
  );

  return `${(
    bytes /
    Math.pow(1024, index)
  ).toFixed(index === 0 ? 0 : 1)} ${
    units[index]
  }`;
}


export default DocumentSidebar;