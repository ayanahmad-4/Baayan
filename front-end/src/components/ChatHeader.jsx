import { Sparkles, RotateCcw } from 'lucide-react';

/**
 * Sticky header with logo, status indicator, and reset button.
 */
export function ChatHeader({ connectionStatus, onReset }) {
  const statusLabel = {
    online: 'Online',
    connecting: 'Connecting',
    error: 'Unavailable',
  }[connectionStatus] ?? 'Connecting';

  return (
    <header className="chat-header" role="banner">
      <div className="chat-header__brand">
        <div className="chat-header__logo" aria-hidden="true">
          <Sparkles />
        </div>
        <div>
          <div className="chat-header__title">Bayaan</div>
          <div className="chat-header__subtitle">AI assistant for Ayan Ahmad</div>
        </div>
      </div>

      <div className="chat-header__actions">
        <div
          className="chat-header__status"
          role="status"
          aria-live="polite"
          aria-label={`Connection status: ${statusLabel}`}
        >
          <span
            className={`status-dot status-dot--${connectionStatus}`}
            aria-hidden="true"
          />
          {statusLabel}
        </div>

        <button
          className="icon-btn"
          onClick={onReset}
          aria-label="Start new conversation"
          title="New chat"
        >
          <RotateCcw aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
