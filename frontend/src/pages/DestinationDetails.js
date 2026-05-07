import React, { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { getDestinationDetail } from '../api';

function DestinationDetails() {
  const { id } = useParams();
  const location = useLocation();
  const { recommendation, tripData } = location.state || {};
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const data = await getDestinationDetail(id);
        setDetails(data);
      } catch (err) {
        setError('Failed to load destination details. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner" />
        <div className="loading-title">Loading destination details<span className="loading-dots"><span>.</span><span>.</span><span>.</span></span></div>
        <div className="loading-sub">Getting tourist spots, food, transport & tips</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <div className="error-msg">{error}</div>
        <Link to="/" className="btn btn-primary">← Back to Home</Link>
      </div>
    );
  }

  const destName = details?.destination_name || recommendation?.destination_name || 'Destination';
  const destDetails = details?.details || {};
  const { tourist_spots = [], local_food = [], transport_info = {}, accommodation_options = [], travel_tips = [], emergency_info = {} } = destDetails;

  return (
    <div className="details-wrapper">
      {/* Navbar */}
      <nav className="navbar">
        <Link to="/" className="navbar-brand">
          <div className="logo-icon">🧭</div>
          <div className="logo-text">Smart Trip <span>AI</span></div>
        </Link>
        <Link to="/results" onClick={() => window.history.back()} className="btn btn-ghost btn-sm">← Back to Results</Link>
      </nav>

      {/* Hero */}
      <div className="details-hero">
        <div className="details-hero-inner">
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', marginBottom: 8 }}>📍 Destination Guide</div>
          <h1>{destName}</h1>
          <p style={{ opacity: 0.85, marginTop: 8 }}>{details?.country}</p>
          {details?.summary && (
            <p style={{ marginTop: 16, maxWidth: 600, opacity: 0.9, lineHeight: 1.7, fontSize: 15 }}>{details.summary}</p>
          )}
          <div style={{ display: 'flex', gap: 20, marginTop: 20, flexWrap: 'wrap' }}>
            {details?.estimated_cost && (
              <div>
                <div style={{ fontSize: 11, opacity: 0.7, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Estimated Cost</div>
                <div style={{ fontSize: 16, fontWeight: 700 }}>{details.estimated_cost}</div>
              </div>
            )}
            {details?.best_time && (
              <div>
                <div style={{ fontSize: 11, opacity: 0.7, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Best Time</div>
                <div style={{ fontSize: 16, fontWeight: 700 }}>{details.best_time}</div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="details-container">

        {/* Tourist Spots */}
        {tourist_spots.length > 0 && (
          <div className="details-section">
            <div className="details-section-header">
              <div className="details-section-icon">🗺</div>
              <h3>Tourist Spots & Attractions</h3>
            </div>
            <div className="details-section-body">
              <div className="spots-grid">
                {tourist_spots.map((spot, i) => (
                  <div key={i} className="spot-card">
                    <h4>📌 {spot.name}</h4>
                    <p>{spot.description}</p>
                    <div className="spot-meta">
                      {spot.entry_fee && <span>🎟 {spot.entry_fee}</span>}
                      {spot.time_needed && <span>⏱ {spot.time_needed}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Local Food */}
        {local_food.length > 0 && (
          <div className="details-section">
            <div className="details-section-header">
              <div className="details-section-icon">🍜</div>
              <h3>Local Food & Restaurants</h3>
            </div>
            <div className="details-section-body">
              <div className="food-list">
                {local_food.map((food, i) => (
                  <div key={i} className="food-item">
                    <div className="food-item-info">
                      <h4>🍽 {food.name}</h4>
                      <p>{food.description}</p>
                    </div>
                    <div className="food-cost">{food.avg_cost}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Transport */}
        {transport_info && Object.keys(transport_info).length > 0 && (
          <div className="details-section">
            <div className="details-section-header">
              <div className="details-section-icon">🚀</div>
              <h3>Transportation</h3>
            </div>
            <div className="details-section-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {transport_info.how_to_reach && (
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6, color: 'var(--primary-dark)' }}>✈️ How to Reach</div>
                    <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{transport_info.how_to_reach}</p>
                  </div>
                )}
                {transport_info.local_transport && (
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6, color: 'var(--primary-dark)' }}>🚕 Local Transport</div>
                    <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{transport_info.local_transport}</p>
                  </div>
                )}
                {transport_info.estimated_transport_budget && (
                  <div style={{ background: 'var(--primary-light)', borderRadius: 'var(--radius-md)', padding: '12px 16px' }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary-dark)' }}>
                      💰 Estimated Transport Budget: {transport_info.estimated_transport_budget}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Accommodation */}
        {accommodation_options.length > 0 && (
          <div className="details-section">
            <div className="details-section-header">
              <div className="details-section-icon">🏨</div>
              <h3>Accommodation Options</h3>
            </div>
            <div className="details-section-body">
              <div className="spots-grid">
                {accommodation_options.map((acc, i) => (
                  <div key={i} className="spot-card">
                    <h4>{acc.type}</h4>
                    <p>{acc.name}</p>
                    <div className="spot-meta">
                      <span>💰 {acc.price_range}</span>
                    </div>
                    {acc.location && <p style={{ fontSize: 12, color: 'var(--text-light)', marginTop: 6 }}>📍 {acc.location}</p>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Travel Tips */}
        {travel_tips.length > 0 && (
          <div className="details-section">
            <div className="details-section-header">
              <div className="details-section-icon">💡</div>
              <h3>Travel Tips</h3>
            </div>
            <div className="details-section-body">
              <div className="tips-list">
                {travel_tips.map((tip, i) => (
                  <div key={i} className="tip-item">
                    <div className="tip-num">{i + 1}</div>
                    <p>{tip}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Emergency Info */}
        {emergency_info && Object.keys(emergency_info).length > 0 && (
          <div className="details-section">
            <div className="details-section-header">
              <div className="details-section-icon">🆘</div>
              <h3>Emergency Information</h3>
            </div>
            <div className="details-section-body">
              <div className="emergency-grid">
                {emergency_info.emergency_number && (
                  <div className="emergency-item">
                    <label>Emergency Number</label>
                    <p>📞 {emergency_info.emergency_number}</p>
                  </div>
                )}
                {emergency_info.nearest_hospital && (
                  <div className="emergency-item">
                    <label>Nearest Hospital</label>
                    <p>🏥 {emergency_info.nearest_hospital}</p>
                  </div>
                )}
                {emergency_info.indian_embassy && (
                  <div className="emergency-item">
                    <label>Indian Embassy</label>
                    <p>🇮🇳 {emergency_info.indian_embassy}</p>
                  </div>
                )}
                {emergency_info.useful_apps && (
                  <div className="emergency-item">
                    <label>Useful Apps</label>
                    <p>📱 {emergency_info.useful_apps}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div style={{ textAlign: 'center', marginTop: 32, display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/plan" className="btn btn-primary btn-lg">Plan Another Trip →</Link>
          <Link to="/" className="btn btn-ghost btn-lg">← Home</Link>
        </div>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: 12, color: 'var(--text-light)' }}>
          Details powered by Google Gemini AI · Smart Trip AI by Arman Ansari
        </p>
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-brand">Smart Trip <span>AI</span></div>
        <div className="footer-author">Made with ❤️ by Arman Ansari</div>
        <div className="footer-copy">© 2026 Smart Trip AI · Django REST + React + Google Gemini AI</div>
      </footer>
    </div>
  );
}

export default DestinationDetails;
