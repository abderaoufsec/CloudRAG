function ChatMessage({
  message,
}) {
  const isUser =
    message.role === "user";

  return (
    <div
      className={`message-row ${
        isUser ? "user-row" : "assistant-row"
      }`}
    >
      <div
        className={`avatar ${
          isUser
            ? "user-avatar"
            : "assistant-avatar"
        }`}
      >
        {isUser ? "U" : "C"}
      </div>

      <div className="message-content">
        <div className="message-label">
          {isUser ? "You" : "CloudRAG"}
        </div>

        <div className="message-bubble" dir="auto">
          <MessageText
            text={message.content}
          />
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
