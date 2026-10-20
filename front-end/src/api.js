/**
 * Bayaan API client
 * All communication with the FastAPI backend goes through here.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/** @typedef {{ role: 'user' | 'assistant', content: string }} Message */

/**
 * Send a chat message and return the assistant's answer.
 * @param {string} message
 * @param {Message[]} history
 * @returns {Promise<{ answer: string, model: string }>}
 */
export async function sendChatMessage(message, history = []) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
    signal: AbortSignal.timeout(45_000), // 45 second timeout
  });

  if (!response.ok) {
    let detail = 'Something went wrong. Please try again.';
    try {
      const data = await response.json();
      detail = data.error || data.detail || detail;
    } catch {
      // ignore JSON parse error
    }
    if (response.status === 429) {
      throw new Error('Too many messages. Please wait a moment before trying again.');
    }
    if (response.status >= 500) {
      throw new Error('The AI service is temporarily unavailable. Please try again shortly.');
    }
    throw new Error(detail);
  }

  return response.json();
}

/**
 * Check API health status.
 * @returns {Promise<{ status: string, resume_loaded: boolean, model: string }>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error('Health check failed');
  return response.json();
}
