import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const EMOJI_MAP = {
  beach: '🏝', adventure: '🧗', culture: '🏛', food: '🍜', nature: '🌿',
  luxury: '💎', mountain: '🏔', desert: '🏜', snow: '❄️', default: '✈️'
};

function getEmoji(destination) {
  const name = (destination || '').toLowerCase();
  if (name.includes('bali') || name.includes('goa') || name.includes('beach')) return '🏝';
  if (name.includes('dubai') || name.includes('singapore') || name.includes('paris')) return '🏙';
  if (name.includes('manali') || name.includes('shimla') || name.includes('mountain')) return '🏔';
  if (name.includes('rajasthan') || name.includes('jaipur') || name.includes('desert')) return '🏰';
  if (name.includes('thailand') || name.includes('bali')) return '🌴';
  if (name.includes('kerala') || name.includes('forest')) return '🌿';
  return EMOJI_MAP.default;
}

function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const { result, tripData } = location.state || {};

  if (!result) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <h2>No results found</h2>
        <Link to="/plan" className="btn btn-primary">Start Planning →</Link>
      </div>
    );
  }

  const { recommendations = [], user_name } = result;

  return (
    <div className="results-wrapper">
      {/* Hero */}
      <div className="results-hero">
        <h1>🎉 Hey {user_name}, here are your picks!</h1>
        <p>Google Gemini AI found these destinations based on your preferences</p>
      </div>

      <div className="results-container">
        {/* Trip summary */}
        <div style={{
          background: 'white',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px 24px',
          marginBottom: 28,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 20
        }}>
          {[
            { label: 'Budget', value: `${tripData?.currency} ${tripData?.budget}` },
            { label: 'Duration', value: `${tripData?.num_days} days` },
            { label: 'Group', value: tripData?.group_type },
            { label: 'From', value: tripData?.departure_location },
            { label: 'Transport', value: tripData?.travel_medium },
          ].map((item, i) => (
            <div key={i}>
              <div style={{ fontSize: 11, color: 'var(--text-light)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>{item.label}</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{item.value}</div>
            </div>
          ))}
        </div>

        {/* Recommendation cards */}
        {recommendations.map((rec, i) => (
          <div key={rec.id || i} className="result-card">
            <div className="result-card-header">
              <div className="result-icon-wrapper" style={{ fontSize: 28 }}>
                {getEmoji(rec.destination_name)}
              </div>
              <div className="result-card-info">
                <h3>{rec.destination_name}</h3>
                <div className="country">📍 {rec.country}</div>
                <p className="summary">{rec.summary}</p>
                <div className="result-highlights">
                  {(rec.highlights || []).map((h, j) => (
                    <span key={j} className="highlight-tag">✓ {h}</span>
                  ))}
                </div>
                <span className={`budget-badge budget-${rec.budget_category}`}>
                  {rec.budget_category === 'budget' ? '💚 Budget Friendly' :
                   rec.budget_category === 'luxury' ? '💎 Luxury Pick' : '⭐ Mid Range'}
                </span>
              </div>
            </div>

            <div className="result-meta">
              <div className="result-meta-item">
                <span className="result-meta-label">Estimated Cost</span>
                <span className="result-meta-value">{rec.estimated_cost}</span>
              </div>
              <div className="result-meta-item">
                <span className="result-meta-label">Best Time to Visit</span>
                <span className="result-meta-value">{rec.best_time}</span>
              </div>
            </div>

            <div className="result-card-footer">
              <button
                className="btn btn-outline"
                onClick={() => navigate(`/destination/${rec.id}`, { state: { recommendation: rec, tripData } })}
              >
                View Full Details →
              </button>
            </div>
          </div>
        ))}

        {/* Actions */}
        <div style={{ textAlign: 'center', marginTop: 32, display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/plan" className="btn btn-primary btn-lg">🔄 Plan Another Trip</Link>
          <Link to="/" className="btn btn-ghost btn-lg">← Back to Home</Link>
        </div>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: 12, color: 'var(--text-light)' }}>
          Recommendations powered by Google Gemini AI · Smart Trip AI by Arman Ansari
        </p>
      </div>
    </div>
  );
}

export default Results;
