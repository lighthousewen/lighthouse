import { useState, useEffect, useCallback, useRef } from "react";
import ChatWindow from "./components/ChatWindow";
import { useSSE } from "./hooks/useSSE";
import { createSession, getMessages, sendFeedback } from "./api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  persona?: string;
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const pendingMsgRef = useRef("");
  const { streaming, startStream } = useSSE();

  useEffect(() => {
    createSession().then((data) => {
      setSessionId(data.session_id);
    });
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      if (!sessionId) return;

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      };
      setMessages((prev) => [...prev, userMsg]);
      pendingMsgRef.current = "";

      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text, mode: "default" }),
      });

      startStream(
        response,
        (chunk) => {
          pendingMsgRef.current += chunk;
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant") {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...last,
                content: pendingMsgRef.current,
              };
              return updated;
            }
            return [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: "assistant",
                content: pendingMsgRef.current,
              },
            ];
          });
        },
        (_sid) => {
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant") return prev;
            return [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: "assistant",
                content: pendingMsgRef.current,
              },
            ];
          });
        }
      );
    },
    [sessionId, startStream]
  );

  const handleFeedback = useCallback(async () => {
    if (!sessionId) return;
    await sendFeedback(sessionId, "dispatch_mismatch");
  }, [sessionId]);

  return (
    <ChatWindow
      messages={messages}
      streaming={streaming}
      onSend={handleSend}
      onFeedback={handleFeedback}
    />
  );
}
