import { useRef, useState } from "react";

function UploadZone({
  onUpload,
  uploading,
}) {
  const inputRef = useRef(null);

  const [dragging, setDragging] =
    useState(false);

  function handleFiles(files) {
    const file = files?.[0];

    if (!file) {
      return;
    }

    onUpload(file);
  }

  function handleDrop(event) {
    event.preventDefault();

    setDragging(false);

    handleFiles(event.dataTransfer.files);
  }

  function handleDragOver(event) {
    event.preventDefault();

    setDragging(true);
  }

  function handleDragLeave() {
    setDragging(false);
  }

  return (
    <div
      className="upload-zone"
    >
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a PDF, DOCX, TXT, or Markdown document"
        className={`upload-area ${dragging ? "dragover" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
      >
        <input
          ref={inputRef}
          type="file"
          hidden
          accept=".pdf,.docx,.txt,.md"
          onChange={(event) =>
            handleFiles(event.target.files)
          }
        />

        <div className="upload-icon">
          {uploading ? "⏳" : "📤"}
        </div>

        <div className="upload-text">
          {uploading
            ? "Processing document..."
            : "Drop files here"}
        </div>

        <div className="upload-subtext">
          {uploading
            ? "Extracting, embedding and indexing"
            : "or click to browse"}
        </div>
      </div>
    </div>
  );
}

export default UploadZone;
