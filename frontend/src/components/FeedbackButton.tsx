interface FeedbackButtonProps {
  onFeedback: () => void;
}

export default function FeedbackButton({ onFeedback }: FeedbackButtonProps) {
  return (
    <div className="feedback-area">
      <button className="feedback-btn" onClick={onFeedback} title="这不是我要的帮助">
        这不是我要的帮助
      </button>
    </div>
  );
}
