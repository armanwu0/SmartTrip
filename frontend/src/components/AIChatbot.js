import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { savePersistentTrip, sendChatMessage } from '../api';

const DEFAULT_SUGGESTIONS = [
  "🏖️ Top budget beaches in India",
  "🏔️ 4-day trip itinerary for Manali",
  "✈️ Best international places under ₹50,000",
  "🍱 Must-try food in Rajasthan"
];

export default function AIChatbot({ embedded = false, onTripCreated }) {
  const [isOpen, setIsOpen] = useState(embedded ? true : false);
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: "👋 **Namaste & Welcome!** I'm your **Smart Trip AI Assistant** created by Arman Ansari.\n\nAsk me anything about destinations, budget planning, best months to visit, local street food, or travel tips!",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(DEFAULT_SUGGESTIONS);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend) => {
    const text = textToSend || inputMsg;
    if (!text.trim() || loading) return;

    const userMessage = {
      sender: 'user',
      text: text.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInputMsg('');
    setLoading(true);

    try {
      const res = await sendChatMessage({ message: text.trim() });
      if (res && res.reply) {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'bot',
            text: res.reply,
            tripId: res.trip?.id,
            saved: res.saved,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
        if (res.trip) onTripCreated?.(res.trip);
        if (res.suggestions && res.suggestions.length > 0) {
          setSuggestions(res.suggestions);
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: err.response?.data?.error || "Sorry, I couldn't complete that request. Please try again.",
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTrip = async (messageIndex, tripId) => {
    try {
      await savePersistentTrip(tripId);
      setMessages(previous => previous.map((message, index) => index === messageIndex ? { ...message, saved: true } : message));
    } catch (err) {
      setMessages(previous => [...previous, {
        sender: 'bot',
        text: err.response?.data?.detail || 'The trip could not be saved.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        sender: 'bot',
        text: "✨ Chat reset! How can I assist your travel plans now?",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setSuggestions(DEFAULT_SUGGESTIONS);
  };

  const formatMessageText = (text) => {
    if (!text) return '';
    // Basic Markdown Formatting: Bold (**text**), Bullet points (• or -)
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let formattedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      formattedLine = formattedLine.replace(/\*(.*?)\*/g, '<em>$1</em>');
      return (
        <div key={idx} style={{ minHeight: line.trim() === '' ? '8px' : 'auto' }}
          dangerouslySetInnerHTML={{ __html: formattedLine }}
        />
      );
    });
  };

  if (embedded) {
    return (
      <div className="embedded-chatbot-card">
        <div className="chatbot-header">
          <div className="chatbot-title">
            <div className="bot-avatar-glow">🤖</div>
            <div>
              <div className="bot-name">Smart Trip AI Assistant</div>
                <div className="bot-status"><span className="online-dot"></span> AI trip planning</div>
            </div>
              </div>
          <button className="chat-action-btn" onClick={handleClearChat} title="Reset Chat">
            🔄 Clear
          </button>
        </div>

        <div className="chat-messages-container" style={{ height: '380px' }}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble-wrapper ${msg.sender}`}>
              {msg.sender === 'bot' && <div className="bubble-avatar">🤖</div>}
              <div className={`chat-bubble ${msg.sender}`}>
                <div className="bubble-text">{formatMessageText(msg.text)}</div>
                {msg.tripId && <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 10 }}>
                  <Link className="btn btn-ghost btn-sm" to={`/trips/${msg.tripId}`}>Open trip</Link>
                  {!msg.saved && <button className="btn btn-ghost btn-sm" onClick={() => handleSaveTrip(i, msg.tripId)}>Save Trip</button>}
                  {msg.saved && <span>✓ Saved</span>}
                </div>}
                <div className="bubble-time">{msg.time}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-bubble-wrapper bot">
              <div className="bubble-avatar">🤖</div>
              <div className="chat-bubble bot loading-bubble">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-suggestions">
          {suggestions.slice(0, 3).map((sug, idx) => (
            <button key={idx} className="suggestion-chip" onClick={() => handleSend(sug)}>
              {sug}
            </button>
          ))}
        </div>

        <div className="chat-input-area">
          <textarea
            className="chat-textarea"
            placeholder="Ask AI anything about your travel plan..."
            value={inputMsg}
            onChange={(e) => setInputMsg(e.target.value)}
            onKeyDown={handleKeyPress}
            rows={1}
          />
          <button className="chat-send-btn" onClick={() => handleSend()} disabled={!inputMsg.trim() || loading}>
             Send
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="floating-chatbot-wrapper">
      {!isOpen && (
        <button className="chatbot-trigger-btn" onClick={() => setIsOpen(true)}>
          <span className="trigger-icon">🤖</span>
          <span className="trigger-text">AI Travel Assistant</span>
          <span className="online-badge"></span>
        </button>
      )}

      {isOpen && (
        <div className="floating-chat-window">
          <div className="chatbot-header">
            <div className="chatbot-title">
              <div className="bot-avatar-glow">🤖</div>
              <div>
                <div className="bot-name">Smart Trip AI Assistant</div>
                <div className="bot-status"><span className="online-dot"></span> Powered by Gemini AI</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="chat-action-btn" onClick={handleClearChat} title="Clear Chat">🔄</button>
              <button className="chat-action-btn" onClick={() => setIsOpen(false)} title="Close Chat">✖</button>
            </div>
          </div>

          <div className="chat-messages-container">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble-wrapper ${msg.sender}`}>
                {msg.sender === 'bot' && <div className="bubble-avatar">🤖</div>}
                <div className={`chat-bubble ${msg.sender}`}>
                  <div className="bubble-text">{formatMessageText(msg.text)}</div>
                  {msg.tripId && <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 10 }}>
                    <Link className="btn btn-ghost btn-sm" to={`/trips/${msg.tripId}`}>Open trip</Link>
                    {!msg.saved && <button className="btn btn-ghost btn-sm" onClick={() => handleSaveTrip(i, msg.tripId)}>Save Trip</button>}
                    {msg.saved && <span>✓ Saved</span>}
                  </div>}
                  <div className="bubble-time">{msg.time}</div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble-wrapper bot">
                <div className="bubble-avatar">🤖</div>
                <div className="chat-bubble bot loading-bubble">
                  <div className="typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-suggestions">
            {suggestions.slice(0, 3).map((sug, idx) => (
              <button key={idx} className="suggestion-chip" onClick={() => handleSend(sug)}>
                {sug}
              </button>
            ))}
          </div>

          <div className="chat-input-area">
            <textarea
              className="chat-textarea"
              placeholder="Ask AI anything about travels..."
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              onKeyDown={handleKeyPress}
              rows={1}
            />
            <button className="chat-send-btn" onClick={() => handleSend()} disabled={!inputMsg.trim() || loading}>
              ✈️
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
