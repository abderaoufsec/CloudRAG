import { useEffect, useRef, useState } from "react";

import ChatMessage from "./ChatMessage";
import SourceCard from "./SourceCard";


function ChatWindow({
  selectedDocument,
  onAsk,
  asking,
}) {
  const [messages, setMessages] =
    useState([]);

  const [question, setQuestion] =
    useState("");

  const [lastSources, setLastSources] =
    useState([]);

  const messagesEndRef =
    useRef(null);


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, asking]);


  async function handleSubmit(event) {
    event.preventDefault();

    const trimmed =
      question.trim();

    if (!trimmed || asking) {
      return;
    }

    const userMessage = {
      role: "user",
      content: trimmed,
    };

    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    setQuestion("");

    try {
      const result =
        await onAsk(trimmed);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            result.answer,
        },
      ]);

      setLastSources(
        result.sources || []
      );

    } catch {

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "Sorry, I couldn't process that question. Please check that the backend and local AI model are running.",
        },
      ]);

      setLastSources([]);
    }
  }


  function clearChat() {
    setMessages([]);
    setLastSources([]);
  }


  return (
    <main className="chat-area" aria-label="Document chat">

      <div className="chat-header">

        <div>
          <span className="eyebrow">
            AI Assistant
          </span>

          <h1>
            Ask your documents
          </h1>

          <p>
            {selectedDocument
              ? "Searching your selected document"
              : "Select a document to start asking questions"}
          </p>
        </div>

        {messages.length > 0 && (
          <button
            className="secondary-button"
            onClick={clearChat}
          >
            Clear chat
          </button>
        )}

      </div>


      <div className="chat-messages">

        {messages.length === 0 ? (

          <div className="empty-state">
            <div className="empty-icon">
              {selectedDocument ? "✦" : "📄"}
            </div>

            <h2>
              {selectedDocument
                ? "Ask CloudRAG anything"
                : "Select a document first"}
            </h2>

            <p>
              {selectedDocument
                ? "CloudRAG searches your documents first, then uses the local AI model to generate a grounded answer."
                : "Upload and select a document to start asking questions about its content."}
            </p>

            {selectedDocument && (
              <div className="suggestion-grid">

                <button
                  onClick={() =>
                    setQuestion(
                      "What is this document about?"
                    )
                  }
                >
                  <strong>
                    Summarize
                  </strong>

                  <span>
                    What is this document about?
                  </span>
                </button>

                <button
                  onClick={() =>
                    setQuestion(
                      "What are the main concepts discussed?"
                    )
                  }
                >
                  <strong>
                    Find concepts
                  </strong>

                  <span>
                    What are the main concepts?
                  </span>
                </button>

                <button
                  onClick={() =>
                    setQuestion(
                      "What are the most important points?"
                    )
                  }
                >
                  <strong>
                    Key points
                  </strong>

                  <span>
                    Show me the most important points.
                  </span>
                </button>

                <button
                  onClick={() =>
                    setQuestion(
                      "Explain the main idea simply."
                    )
                  }
                >
                  <strong>
                    Explain
                  </strong>

                  <span>
                    Explain the main idea simply.
                  </span>
                </button>

              </div>
            )}
          </div>

        ) : (

          <>
            {messages.map(
              (message, index) => (
                <ChatMessage
                  key={index}
                  message={message}
                />
              )
            )}

            {asking && (
              <div className="message assistant">
                <div className="message-avatar">
                  🤖
                </div>

                <div className="message-content">
                  <div className="message-bubble">
                    Searching your documents...
                  </div>
                </div>
              </div>
            )}

            {lastSources.length > 0 && (
              <div className="sources">
                <div className="sources-header">
                  Sources
                </div>

                {lastSources.map(
                  (source, index) => (
                    <SourceCard
                      key={`${source.chunk_id}-${index}`}
                      source={source}
                    />
                  )
                )}
              </div>
            )}

            <div
              ref={messagesEndRef}
            />
          </>
        )}

      </div>


      <form
        className="chat-input-area"
        onSubmit={handleSubmit}
      >

        <div className="chat-input-wrapper">

          <textarea
            aria-label="Question about your documents"
            dir="auto"
            value={question}
            onChange={(event) =>
              setQuestion(
                event.target.value
              )
            }
            placeholder={
              selectedDocument
                ? "Ask a question about this document..."
                : "Select a document first..."
            }
            rows={1}
            disabled={asking || !selectedDocument}
            onKeyDown={(event) => {

              if (
                event.key === "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();

                handleSubmit(event);
              }

            }}
          />

          <button
            type="submit"
            className="send-button"
            disabled={
              asking ||
              !question.trim() ||
              !selectedDocument
            }
          >
            Send
          </button>

        </div>

      </form>

    </main>
  );
}


export default ChatWindow;
