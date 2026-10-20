import { useState, useCallback, useEffect, useRef } from 'react';
import { ChatHeader } from './ChatHeader';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { sendChatMessage, checkHealth } from '../api';

/**
 * Max number of history turns sent to the backend per request.
 * Keeps prompts short and costs low.
 */
const MAX_HISTORY_TURNS = 10;

/**
 * ChatPage — the full conversation experience.
 *
 * @param {{ embed?: boolean }} props
 *   embed: when true, applies compact embed styles
 */
export function ChatPage({ embed = false }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  // Track the last user message for retry
  const lastUserMessage = useRef(null);

  // ── Health check on mount ────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await checkHealth();
        if (!cancelled) setConnectionStatus('online');
      } catch {
        if (!cancelled) setConnectionStatus('error');
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // ── Send a message ───────────────────────────────────────────
  const sendMessage = useCallback(async (userText) => {
    const text = userText.trim();
    if (!text || isLoading) return;

    lastUserMessage.current = text;
    setError(null);
    setIsLoading(true);

    // Optimistically add user message
    setMessages((prev) => [...prev, { role: 'user', content: text }]);

    // Build history slice for the backend (exclude the message we just added)
    const historySlice = messages
      .slice(-MAX_HISTORY_TURNS * 2)
      .map(({ role, content }) => ({ role, content }));

    try {
      const data = await sendChatMessage(text, historySlice);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
      setConnectionStatus('online');
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
      setConnectionStatus((s) => (s === 'online' ? 'online' : 'error'));
    } finally {
      setIsLoading(false);
    }
  }, [messages, isLoading]);

  // ── Submit handler ───────────────────────────────────────────
  const handleSubmit = useCallback((e) => {
    e?.preventDefault();
    const text = inputValue.trim();
    if (!text) return;
    setInputValue('');
    sendMessage(text);
  }, [inputValue, sendMessage]);

  // ── Prompt chip handler ──────────────────────────────────────
  const handlePromptSelect = useCallback((prompt) => {
    sendMessage(prompt);
  }, [sendMessage]);

  // ── Retry last message ───────────────────────────────────────
  const handleRetry = useCallback(() => {
    if (!lastUserMessage.current) return;
    // Remove the last user message that failed (it was already added optimistically)
    setMessages((prev) => prev.slice(0, -1));
    setError(null);
    sendMessage(lastUserMessage.current);
  }, [sendMessage]);

  // ── Reset conversation ───────────────────────────────────────
  const handleReset = useCallback(() => {
    setMessages([]);
    setInputValue('');
    setError(null);
    lastUserMessage.current = null;
  }, []);

  return (
    <div className={`chat-app${embed ? ' chat-app--embed' : ''}`}>
      <ChatHeader
        connectionStatus={connectionStatus}
        onReset={handleReset}
      />
      <ChatMessages
        messages={messages}
        isLoading={isLoading}
        error={error}
        onRetry={handleRetry}
        onPromptSelect={handlePromptSelect}
      />
      <ChatInput
        value={inputValue}
        onChange={setInputValue}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        disabled={connectionStatus === 'error' && messages.length === 0}
      />
    </div>
  );
}
