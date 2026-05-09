import { useState, useEffect, useCallback, useRef } from "react";
import ChatWindow from "./components/ChatWindow";
import { useSSE, type StreamChunk } from "./hooks/useSSE";
import { createSession, sendFeedback } from "./api/client";

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
  const currentPersonaRef = useRef<string | undefined>(undefined);
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
      currentPersonaRef.current = undefined;

      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text, mode: "default" }),
      });

      startStream(
        response,
        (chunk: StreamChunk) => {
          if (chunk.persona) {
            currentPersonaRef.current = chunk.persona;
          }
          pendingMsgRef.current += chunk.content;
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
                persona: currentPersonaRef.current,
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
                persona: currentPersonaRef.current,
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
    const recentContext = messages
      .slice(-4)
      .map((m) => `[${m.role}]${m.persona ? `(${m.persona})` : ""}: ${m.content.slice(0, 100)}`)
      .join("\n");
    await sendFeedback(sessionId, "dispatch_mismatch", recentContext);
  }, [sessionId, messages]);

  return (
    <ChatWindow
      messages={messages}
      streaming={streaming}
      onSend={handleSend}
      onFeedback={handleFeedback}
    />
  );
}
