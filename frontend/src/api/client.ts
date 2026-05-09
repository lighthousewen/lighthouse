const API_BASE = import.meta.env.VITE_API_BASE || "";

export async function createSession() {
  const res = await fetch(`${API_BASE}/api/v1/sessions`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function getSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to get session");
  return res.json();
}

export async function getMessages(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error("Failed to get messages");
  return res.json();
}

export function sendMessage(
  sessionId: string | null,
  message: string,
  mode: string = "default"
): {
  stream: ReadableStream<Uint8Array> | null;
  response: Promise<Response>;
} {
  const controller = new AbortController();
  const response = fetch(`${API_BASE}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, mode }),
    signal: controller.signal,
  });

  return {
    stream: null,
    response,
    cancel: () => controller.abort(),
  } as any;
}

export async function sendFeedback(
  sessionId: string,
  feedbackType: string,
  contextSnapshot?: string
) {
  const res = await fetch(`${API_BASE}/api/v1/log/user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      type: "user_feedback",
      feedback_type: feedbackType,
      context_snapshot: contextSnapshot,
    }),
  });
  return res.json();
}
