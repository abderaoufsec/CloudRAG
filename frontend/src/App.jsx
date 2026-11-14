import { useCallback, useEffect, useState } from "react";

import Header from "./components/Header";
import DocumentSidebar from "./components/DocumentSidebar";
import ChatWindow from "./components/ChatWindow";

import {
  askQuestion,
  deleteDocument,
  getDocuments,
  uploadDocument,
} from "./services/api";


function App() {

  const [documents, setDocuments] =
    useState([]);

  const [selectedDocument, setSelectedDocument] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [asking, setAsking] =
    useState(false);

  const [error, setError] =
    useState(null);


  const loadDocuments = useCallback(async () => {
    try {
      setError(null);
      const data = await getDocuments();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error(err);
      setError("Unable to connect to the CloudRAG backend.");
    }
  }, []);


  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);


  async function handleUpload(file) {

    try {

      setUploading(true);

      setError(null);

      let result;

      try {

        result =
          await uploadDocument(file);

      } catch (err) {

        console.error(err);

        const detail =
          err.response?.data?.detail;

        if (
          typeof detail === "object" &&
          detail?.message
        ) {
          setError(detail.message);
        } else {
          setError(
            typeof detail === "string"
              ? detail
              : "Document upload failed."
          );
        }

        return;
      }

      await loadDocuments();

      setSelectedDocument(
        result.document_id
      );

    } finally {

      setUploading(false);
    }
  }


  async function handleDelete(
    documentId
  ) {

    const document =
      documents.find(
        (item) =>
          item.document_id ===
          documentId
      );

    const confirmed =
      window.confirm(
        `Delete "${document?.filename || "this document"}"?`
      );

    if (!confirmed) {
      return;
    }


    try {

      setError(null);

      await deleteDocument(
        documentId
      );

      if (
        selectedDocument ===
        documentId
      ) {
        setSelectedDocument(null);
      }

      await loadDocuments();

    } catch (err) {

      console.error(err);

      setError(
        "Unable to delete the document."
      );
    }
  }


  async function handleAsk(
    question
  ) {

    try {

      setAsking(true);

      setError(null);

      const result =
        await askQuestion(
          question,
          5,
          selectedDocument
        );

      return result;

    } catch (err) {

      console.error(err);

      setError(
        "The AI could not answer the question."
      );

      throw err;

    } finally {

      setAsking(false);
    }
  }


  return (
    <div className="app">

      <Header />

      {error && (
        <div className="error-banner" role="alert">

          <span>
            ⚠
          </span>

          <span>
            {error}
          </span>

          <button
            onClick={() =>
              setError(null)
            }
          >
            ×
          </button>

        </div>
      )}


      <div className="app-layout">

        <DocumentSidebar
          documents={documents}
          selectedDocument={
            selectedDocument
          }
          onSelectDocument={
            setSelectedDocument
          }
          onUpload={
            handleUpload
          }
          onDelete={
            handleDelete
          }
          uploading={
            uploading
          }
        />


        <ChatWindow
          selectedDocument={
            selectedDocument
          }
          onAsk={
            handleAsk
          }
          asking={
            asking
          }
        />

      </div>

    </div>
  );
}


export default App;
