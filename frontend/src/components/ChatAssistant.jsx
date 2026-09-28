import React, { useState, useRef, useEffect } from 'react';
import { apiUrl } from '../api';

const SUGGESTIONS = [
  'Grade all quizzes in samples/generated',
  'Show grading statistics',
  'Which students need human review?',
  'List all grading results',
];

const CHAT_TIMEOUT_MS = 120000;

export function ChatAssistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hi! I can grade quizzes from a folder (e.g. "samples/generated"), show results, flagged students, and statistics.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMessage = { role: 'user', content: trimmed };
    const history = messages.filter((m) => m.role !== 'assistant' || messages.indexOf(m) > 0);

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);

      const response = await fetch(apiUrl('/agent/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          history: history.map(({ role, content }) => ({ role, content })),
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || 'Chat request failed');
      }

      const data = await response.json();
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out after 2 minutes. The assistant may still be working — refresh results shortly.');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="upload-section chat-section">
      <h2>Grading Assistant (LangChain)</h2>
      <p className="section-description">
        Chat with the AI assistant to query results, flagged students, and grading stats.
      </p>

      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`chat-bubble chat-bubble-${msg.role}`}>
            <span className="chat-role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
            <p>{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble chat-bubble-assistant">
            <span className="chat-role">Assistant</span>
            <p className="chat-typing">Thinking...</p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-suggestions">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            className="btn btn-secondary chat-suggestion-btn"
            onClick={() => sendMessage(suggestion)}
            disabled={loading}
          >
            {suggestion}
          </button>
        ))}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about grades, flagged students, statistics..."
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
