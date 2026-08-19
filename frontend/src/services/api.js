import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,
});


export async function getDocuments() {
  const response = await api.get("/api/documents");
  return response.data;
}


export async function getDocument(documentId) {
  const response = await api.get(
    `/api/documents/${documentId}`
  );

  return response.data;
}


export async function uploadDocument(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post(
    "/api/documents/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}


export async function deleteDocument(documentId) {
  const response = await api.delete(
    `/api/documents/${documentId}`
  );

  return response.data;
}


export async function askQuestion(
  question,
  topK = 5
) {
  const response = await api.post(
    "/api/rag/ask",
    {
      question,
      top_k: topK,
    }
  );

  return response.data;
}


export async function getRagStats() {
  const response = await api.get(
    "/api/rag/stats"
  );

  return response.data;
}


export async function getHealth() {
  const response = await api.get(
    "/api/health"
  );

  return response.data;
}