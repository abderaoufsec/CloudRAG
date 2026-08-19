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

    } catch (error) {

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
    <main className="chat-area">

      <div className="chat-header">

        <div>
          <span className="eyebrow">
            AI Assistant
          </span>

          <h2>
            Ask your documents
          </h2>
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


      <div className="chat-content">

        {messages.length === 0 ? (

          <div className="welcome-state">

            <div className="welcome-icon">
              ✦
            </div>

            <h2>
              Ask CloudRAG anything
            </h2>

            <p>
              CloudRAG searches your documents
              first, then uses the local AI
              model to generate a grounded answer.
            </p>

            {selectedDocument && (
              <div className="active-document">
                <span>📄</span>
                Searching selected document
              </div>
            )}

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

          </div>

        ) : (

          <div className="messages-container">

            {messages.map(
              (message, index) => (
                <ChatMessage
                  key={index}
                  message={message}
                />
              )
            )}

            {asking && (
              <div className="message-row assistant-row">

                <div className="avatar assistant-avatar">
                  C
                </div>

                <div className="message-content">

                  <div className="message-label">
                    CloudRAG
                  </div>

                  <div className="message-bubble typing">
                    <span />
                    <span />
                    <span />
                  </div>

                </div>

              </div>
            )}

            {lastSources.length > 0 && (
              <div className="sources-section">

                <div className="sources-header">
                  <span>
                    📎
                  </span>

                  <strong>
                    Sources
                  </strong>
                </div>

                <div className="sources-grid">

                  {lastSources.map(
                    (source, index) => (
                      <SourceCard
                        key={`${source.chunk_id}-${index}`}
                        source={source}
                      />
                    )
                  )}

                </div>

              </div>
            )}

            <div
              ref={messagesEndRef}
            />

          </div>
        )}

      </div>


      <form
        className="chat-input-area"
        onSubmit={handleSubmit}
      >

        <div className="chat-input-wrapper">

          <textarea
            value={question}
            onChange={(event) =>
              setQuestion(
                event.target.value
              )
            }
            placeholder="Ask a question about your documents..."
            rows={1}
            disabled={asking}
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
              !question.trim()
            }
          >
            ↑
          </button>

        </div>

        <span className="input-hint">
          Enter to send · Shift + Enter for a new line
        </span>

      </form>

    </main>
  );
}


export default ChatWindow;