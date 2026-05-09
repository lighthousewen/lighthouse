import { useState } from "react";

interface FeedbackButtonProps {
  onFeedback: () => Promise<void>;
}

export default function FeedbackButton({ onFeedback }: FeedbackButtonProps) {
  const [feedbackState, setFeedbackState] = useState<"idle" | "sending" | "done">("idle");

  const handleClick = async () => {
    if (feedbackState !== "idle") return;
    setFeedbackState("sending");
    try {
      await onFeedback();
      setFeedbackState("done");
      setTimeout(() => setFeedbackState("idle"), 3000);
    } catch {
      setFeedbackState("idle");
    }
  };

  const labels: Record<string, string> = {
    idle: "这不是我要的帮助",
    sending: "提交中...",
    done: "已记录",
  };

  return (
    <div className="feedback-area">
      <button
        className={`feedback-btn ${feedbackState}`}
        onClick={handleClick}
        disabled={feedbackState !== "idle"}
        title="这不是我要的帮助"
      >
        {labels[feedbackState]}
      </button>
    </div>
  );
}
