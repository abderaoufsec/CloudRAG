function ChatMessage({
  message,
}) {
  const isUser =
    message.role === "user";

  return (
    <div
      className={`message ${isUser ? "user" : "assistant"}`}
    >
      <div className="message-avatar">
        {isUser ? "👤" : "🤖"}
      </div>

      <div className="message-content">
        <div className="message-bubble" dir="auto">
          <MessageText
            text={message.content}
          />
        </div>

        <div className="message-time">
          {isUser ? "You" : "CloudRAG"}
        </div>
      </div>
    </div>
  );
}


function MessageText({ text }) {
  return (
    <div className="message-text">
      {text
        .split("\n")
        .map((line, index) => (
          <p key={index}>
            {line || "\u00A0"}
          </p>
        ))}
    </div>
  );
}


export default ChatMessage;
