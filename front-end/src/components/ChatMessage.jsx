import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * A single message (user or assistant) with its label and actions.
 */
export function ChatMessage({ role, content }) {
  const isAssistant = role === 'assistant';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available
    }
  };

  return (
    <div className={`message-group message-group--${role}`}>
      <span className="message-role-label" aria-hidden="true">
        {isAssistant ? 'Bayaan' : 'You'}
      </span>

      <div
        className={`message-bubble message-bubble--${role}`}
        aria-label={`${isAssistant ? 'Bayaan' : 'You'}: ${content}`}
      >
        {isAssistant ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        ) : (
          content
        )}
      </div>

      {isAssistant && (
        <div className="message-actions">
          <button
            className={`message-action-btn ${copied ? 'message-action-btn--copied' : ''}`}
            onClick={handleCopy}
            aria-label={copied ? 'Copied!' : 'Copy response'}
            title={copied ? 'Copied!' : 'Copy'}
          >
            {copied ? <Check /> : <Copy />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      )}
    </div>
  );
}
