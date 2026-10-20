import { useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

/**
 * Auto-growing textarea + send button.
 */
export function ChatInput({ value, onChange, onSubmit, isLoading, disabled }) {
  const textareaRef = useRef(null);

  // Auto-resize textarea height
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  }, [value]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && !isLoading && value.trim()) {
        onSubmit(e);
      }
    }
  };

  return (
    <div className="chat-input-area">
      <form
        className="chat-input-form"
        onSubmit={onSubmit}
        aria-label="Chat input"
      >
        <textarea
          ref={textareaRef}
          className="chat-input-textarea"
          placeholder="Ask anything about Ayan…"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          aria-label="Your message"
          aria-multiline="true"
          disabled={isLoading || disabled}
          maxLength={1000}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!value.trim() || isLoading || disabled}
          aria-label="Send message"
          title="Send (Enter)"
        >
          <Send aria-hidden="true" />
        </button>
      </form>
      <p className="chat-input-hint">
        Press <kbd>Enter</kbd> to send &middot; <kbd>Shift + Enter</kbd> for new line
      </p>
    </div>
  );
}
