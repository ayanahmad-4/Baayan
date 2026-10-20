import { AlertTriangle, RotateCcw } from 'lucide-react';

/**
 * Error message with optional retry button.
 */
export function ErrorMessage({ message, onRetry }) {
  return (
    <div className="error-message" role="alert">
      <AlertTriangle aria-hidden="true" />
      <div>
        <p className="error-message__text">{message}</p>
        {onRetry && (
          <button className="error-retry-btn" onClick={onRetry} aria-label="Retry last message">
            <RotateCcw />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
