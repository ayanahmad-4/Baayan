/**
 * Animated typing indicator shown while waiting for assistant response.
 */
export function TypingIndicator() {
  return (
    <div className="typing-indicator" role="status" aria-label="Bayaan is thinking">
      <div className="typing-dots" aria-hidden="true">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
      <span className="typing-label">Thinking…</span>
    </div>
  );
}
