import { useState, useRef, useCallback } from "react";

interface SSEMessage {
  content?: string;
  done?: boolean;
}

export function useSSE() {
  const [streaming, setStreaming] = useState(false);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);

  const startStream = useCallback(
    async (
      response: Response,
      onChunk: (text: string) => void,
      onDone: (sessionId: string) => void
    ) => {
      setStreaming(true);

      const sessionId = response.headers.get("X-Session-Id") || "";
      const reader = response.body?.getReader();
      if (!reader) {
        setStreaming(false);
        return;
      }

      readerRef.current = reader;
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data: SSEMessage = JSON.parse(line.slice(6));
                if (data.content) {
                  onChunk(data.content);
                }
                if (data.done) {
                  onDone(sessionId);
                }
              } catch {
                // skip malformed lines
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
        setStreaming(false);
      }
    },
    []
  );

  const stopStream = useCallback(() => {
    readerRef.current?.cancel();
    setStreaming(false);
  }, []);

  return { streaming, startStream, stopStream };
}
