import { useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import FeedbackButton from "./FeedbackButton";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  persona?: string;
}

interface ChatWindowProps {
  messages: Message[];
  streaming: boolean;
  onSend: (message: string) => void;
  onFeedback: () => void;
}

export default function ChatWindow({
  messages,
  streaming,
  onSend,
  onFeedback,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h1>灯塔 · Lighthouse</h1>
        <span className="chat-status">v0.1.0 · MVP 开发中</span>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>深筑已就位。发送消息开始对话。</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={msg.id || i} {...msg} />
        ))}
        {streaming && <div className="streaming-indicator">▍</div>}
        <div ref={bottomRef} />
      </div>

      <FeedbackButton onFeedback={onFeedback} />
      <ChatInput onSend={onSend} disabled={streaming} />
    </div>
  );
}
