import { Sparkles } from 'lucide-react';

const SUGGESTED_PROMPTS = [
  'Tell me about Ayan.',
  'What are his technical skills?',
  'Explain his AI/ML internship.',
  'What projects has he built?',
  'Tell me about his education.',
];

/**
 * Welcome screen shown before any messages.
 */
export function ChatWelcome({ onPromptSelect }) {
  return (
    <div className="chat-welcome">
      <div className="chat-welcome__icon">
        <Sparkles />
      </div>
      <h1 className="chat-welcome__title">Hi, I&rsquo;m Bayaan</h1>
      <p className="chat-welcome__subtitle">
        Ask me anything about Syed Ayan Ahmad — his skills, projects, experience, and more.
      </p>
      <SuggestedPrompts prompts={SUGGESTED_PROMPTS} onSelect={onPromptSelect} />
    </div>
  );
}

/**
 * Suggested prompt chips.
 */
export function SuggestedPrompts({ prompts, onSelect }) {
  return (
    <div className="suggested-prompts" role="list" aria-label="Suggested questions">
      {prompts.map((prompt) => (
        <button
          key={prompt}
          role="listitem"
          className="prompt-chip"
          onClick={() => onSelect(prompt)}
          aria-label={`Ask: ${prompt}`}
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
