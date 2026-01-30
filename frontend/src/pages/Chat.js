import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './Chat.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AGENT_INFO = {
  'RootAgent': {
    icon: '🎯',
    color: '#667eea',
    description: 'Coordinator'
  },
  'RAGAgent': {
    icon: '📚',
    color: '#48bb78',
    description: 'Internal Docs Search'
  },
  'WebSearchAgent': {
    icon: '🌐',
    color: '#ed8936',
    description: 'External Standards'
  },
  'AnalyzerAgent': {
    icon: '🔍',
    color: '#9f7aea',
    description: 'Final Analysis'
  },
  'ComplianceWorkflow': {
    icon: '⚙️',
    color: '#38b2ac',
    description: 'Sequential Workflow'
  }
};

export default function Chat() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState(null);
  const [agentHistory, setAgentHistory] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: query
    };

    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setLoading(true);
    setActiveAgent('RootAgent');
    setAgentHistory(['RootAgent']);

    const agentMessage = {
      role: 'assistant',
      content: '',
      events: [],
      agentsUsed: new Set(['RootAgent'])
    };

    setMessages(prev => [...prev, agentMessage]);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'agent_start' || data.type === 'agent_active') {
                setActiveAgent(data.agent);
                setAgentHistory(prev => {
                  if (!prev.includes(data.agent)) {
                    return [...prev, data.agent];
                  }
                  return prev;
                });
              }

              if (data.type === 'agent_text') {
                setMessages(prev => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  lastMsg.content += data.content;
                  lastMsg.agentsUsed.add(data.agent);
                  return updated;
                });
              }

              setMessages(prev => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                lastMsg.events = [...(lastMsg.events || []), data];
                if (data.agent) {
                  lastMsg.agentsUsed.add(data.agent);
                }
                return updated;
              });

            } catch (err) {
              console.error('Failed to parse event:', err);
            }
          }
        }
      }

      setActiveAgent(null);
    } catch (error) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1].content = `Error: ${error.message}`;
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-title">
          <h1>🤖 Compliance Analysis Chat</h1>
          <p className="header-subtitle">Multi-Agent System powered by Google ADK</p>
        </div>

        {activeAgent && (
          <div className="agent-indicator">
            <span className="pulse"></span>
            <span className="agent-icon">{AGENT_INFO[activeAgent]?.icon}</span>
            <div className="agent-details">
              <strong>{activeAgent}</strong>
              <span className="agent-desc">{AGENT_INFO[activeAgent]?.description}</span>
            </div>
          </div>
        )}
      </div>

      {agentHistory.length > 0 && loading && (
        <div className="agent-timeline">
          <span className="timeline-label">Execution Flow:</span>
          {agentHistory.map((agent, idx) => (
            <div
              key={idx}
              className={`timeline-agent ${activeAgent === agent ? 'active' : 'completed'}`}
            >
              <span className="timeline-icon">{AGENT_INFO[agent]?.icon}</span>
              <span className="timeline-name">{agent}</span>
              {idx < agentHistory.length - 1 && <span className="timeline-arrow">→</span>}
            </div>
          ))}
        </div>
      )}

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome">
            <div className="welcome-icon">💬</div>
            <h2>Welcome to Compliance Analysis</h2>
            <p>Ask questions about insurance policy compliance</p>

            <div className="agent-cards">
              {Object.entries(AGENT_INFO).map(([name, info]) => (
                <div key={name} className="agent-card" style={{ borderColor: info.color }}>
                  <span className="card-icon">{info.icon}</span>
                  <strong>{name}</strong>
                  <span className="card-desc">{info.description}</span>
                </div>
              ))}
            </div>

            <div className="examples">
              <div className="example">💡 "Does this request comply with our policy?"</div>
              <div className="example">💡 "Check compliance with state regulations"</div>
              <div className="example">💡 "What does our policy say about pre-existing conditions?"</div>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              {msg.content && (
                <div className="message-text">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              )}

              {msg.agentsUsed && msg.agentsUsed.size > 0 && (
                <div className="agents-used">
                  <span className="agents-label">Agents Used:</span>
                  {Array.from(msg.agentsUsed).map((agent, i) => (
                    <span
                      key={i}
                      className="agent-badge"
                      style={{ background: AGENT_INFO[agent]?.color }}
                    >
                      {AGENT_INFO[agent]?.icon} {agent}
                    </span>
                  ))}
                </div>
              )}

              {msg.events && msg.events.length > 0 && (
                <details className="event-details">
                  <summary>🔍 View Agent Execution ({msg.events.length} events)</summary>
                  <div className="events-list">
                    {msg.events.map((event, i) => (
                      <div key={i} className={`event-item ${event.type}`}>
                        {event.type === 'agent_start' && (
                          <div className="event-start">
                            <span className="event-icon">▶️</span>
                            <span className="event-agent">{event.agent}</span>
                            <span className="event-message">{event.message}</span>
                          </div>
                        )}
                        {event.type === 'tool_call' && (
                          <div className="event-tool-call">
                            <span className="event-icon">🔧</span>
                            <span className="event-agent">{event.agent}</span>
                            <strong>{event.tool}</strong>
                            <pre>{JSON.stringify(event.args, null, 2)}</pre>
                          </div>
                        )}
                        {event.type === 'tool_result' && (
                          <div className="event-tool-result">
                            <span className="event-icon">✅</span>
                            <span className="tool-result-preview">
                              Result from {event.tool}
                            </span>
                          </div>
                        )}
                        {event.type === 'agent_complete' && (
                          <div className="event-complete">
                            <span className="event-icon">🏁</span>
                            <span className="event-message">{event.message}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <textarea
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about insurance compliance..."
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading || !query.trim()} className="send-button">
          {loading ? '⏳' : '🚀'}
        </button>
      </form>
    </div>
  );
}
