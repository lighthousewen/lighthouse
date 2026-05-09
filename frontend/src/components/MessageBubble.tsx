interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  persona?: string;
}

export default function MessageBubble({ role, content, persona }: MessageBubbleProps) {
  return (
    <div className={`message-bubble ${role}`}>
      <div className="message-meta">
        {persona && <span className="message-persona">{persona}</span>}
      </div>
      <div className="message-content">{content}</div>
    </div>
  );
}
