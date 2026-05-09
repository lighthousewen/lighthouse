const PERSONA_LABELS: Record<string, string> = {
  igniter: "引信",
  deep_mirror: "深度镜",
  executor: "执行手",
  spotlight_tutor: "陪学",
  spotlight_ask: "追问",
};

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  persona?: string;
}

export default function MessageBubble({ role, content, persona }: MessageBubbleProps) {
  const personaLabel = persona ? PERSONA_LABELS[persona] || persona : undefined;

  return (
    <div className={`message-bubble ${role}`}>
      {personaLabel && (
        <div className="message-meta">
          <span className="message-persona">{personaLabel}</span>
        </div>
      )}
      <div className="message-content">{content}</div>
    </div>
  );
}
