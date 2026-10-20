import { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';
import { ErrorMessage } from './ErrorMessage';
import { ChatWelcome } from './ChatWelcome';

/**
 * Scrollable message list with welcome screen.
 */
export function ChatMessages({ messages, isLoading, error, onRetry, onPromptSelect }) {
  const bottomRef = useRef(null);

  // Auto-scroll to the bottom when messages change or loading starts
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  const isEmpty = messages.length === 0 && !isLoading && !error;

  return (
    <div
      className="chat-messages"
      role="log"
      aria-live="polite"
      aria-label="Conversation"
    >
      {isEmpty ? (
        <ChatWelcome onPromptSelect={onPromptSelect} />
      ) : (
        <>
          {messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} />
          ))}
          {isLoading && <TypingIndicator />}
          {error && !isLoading && (
            <ErrorMessage message={error} onRetry={onRetry} />
          )}
        </>
      )}
      <div ref={bottomRef} aria-hidden="true" style={{ height: '1.5rem' }} />
    </div>
  );
}
