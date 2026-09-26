import React, { useEffect, useState, useCallback } from 'react';
import { Link, useLocation, useParams, useNavigate } from 'react-router-dom';
import { getDestinationDetail, getReviews, addReview, voteHelpful, getDayWiseItinerary } from '../api';
import { useAuth } from '../AuthContext';

// ─── Star Rating component ───────────────────────────────────────────────────
function StarRating({ value, onChange, readOnly = false }) {
  const [hover, setHover] = useState(0);
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {[1,2,3,4,5].map(s => (
        <span key={s}
          style={{ fontSize: readOnly ? 16 : 24, cursor: readOnly ? 'default' : 'pointer', color: s <= (hover || value) ? '#f59e0b' : '#d1d5db', transition: 'color 0.1s' }}
          onMouseEnter={() => !readOnly && setHover(s)}
          onMouseLeave={() => !readOnly && setHover(0)}
          onClick={() => !readOnly && onChange && onChange(s)}>
          ★
        </span>
      ))}
    </div>
  );
}

// ─── Itinerary day card (collapsible) ────────────────────────────────────────
function ItineraryDayCard({ day }) {
  const [open, setOpen] = useState(day.day === 1); // first day open by default

  const FOOD_ICONS = ['🌄', '☀️', '🌙'];

  return (
    <div className="itinerary-day-card">
      <div className="itinerary-day-header" onClick={() => setOpen(p => !p)}>
        <div className="itinerary-day-title">
          <div className="itinerary-day-badge">{day.day}</div>
          <div>
            <div className="itinerary-day-label">Day {day.day}</div>
            {day.date && <div className="itinerary-day-date">📅 {day.date}</div>}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <div className="itinerary-day-meta">
            {day.estimated_daily_cost && (
              <span className="itinerary-meta-pill">💰 {day.estimated_daily_cost}</span>
            )}
            {day.approximate_travel_time && (
              <span className="itinerary-meta-pill">🕐 {day.approximate_travel_time}</span>
            )}
          </div>
          <span className={`itinerary-collapse-icon${open ? ' open' : ''}`}>▼</span>
        </div>
      </div>

      {open && (
        <div className="itinerary-day-body">

          {/* Activities – three time slots */}
          <div>
            <div className="itinerary-subsection-label">Activities</div>
            <div className="itinerary-slots">
              {/* Morning */}
              {(day.morning?.length > 0) && (
                <div className="itinerary-slot morning">
                  <div className="itinerary-slot-header">
                    <span className="itinerary-slot-icon">🌅</span>
                    <span className="itinerary-slot-label">Morning</span>
                  </div>
                  <ul className="itinerary-slot-activities">
                    {day.morning.map((act, i) => <li key={i}>{act}</li>)}
                  </ul>
                </div>
              )}
              {/* Afternoon */}
              {(day.afternoon?.length > 0) && (
                <div className="itinerary-slot afternoon">
                  <div className="itinerary-slot-header">
                    <span className="itinerary-slot-icon">☀️</span>
                    <span className="itinerary-slot-label">Afternoon</span>
                  </div>
                  <ul className="itinerary-slot-activities">
                    {day.afternoon.map((act, i) => <li key={i}>{act}</li>)}
                  </ul>
                </div>
              )}
              {/* Evening */}
              {(day.evening?.length > 0) && (
                <div className="itinerary-slot evening">
                  <div className="itinerary-slot-header">
                    <span className="itinerary-slot-icon">🌆</span>
                    <span className="itinerary-slot-label">Evening</span>
                  </div>
                  <ul className="itinerary-slot-activities">
                    {day.evening.map((act, i) => <li key={i}>{act}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Recommended places */}
          {day.recommended_places?.length > 0 && (
            <div>
              <div className="itinerary-subsection-label">📍 Recommended Places</div>
              <div className="itinerary-places">
                {day.recommended_places.map((place, i) => (
                  <span key={i} className="itinerary-place-chip">📌 {place}</span>
                ))}
              </div>
            </div>
          )}

          {/* Cost & travel time info cards */}
          <div className="itinerary-info-row">
            {day.estimated_daily_cost && (
              <div className="itinerary-info-card">
                <div className="itinerary-info-card-label">💰 Estimated Daily Cost</div>
                <div className="itinerary-info-card-value">{day.estimated_daily_cost}</div>
              </div>
            )}
            {day.approximate_travel_time && (
              <div className="itinerary-info-card">
                <div className="itinerary-info-card-label">🕐 Approx. Travel Time</div>
                <div className="itinerary-info-card-value">{day.approximate_travel_time}</div>
              </div>
            )}
          </div>

          {/* Food suggestions */}
          {day.food_suggestions?.length > 0 && (
            <div>
              <div className="itinerary-subsection-label">🍽 Food Suggestions</div>
              <div className="itinerary-food-list">
                {day.food_suggestions.map((food, i) => (
                  <div key={i} className="itinerary-food-item">
                    <span className="itinerary-food-icon">{FOOD_ICONS[i] || '🍴'}</span>
                    {food}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Day notes */}
          {day.notes && (
            <div className="itinerary-notes">
              <span className="itinerary-notes-icon">💡</span>
              <span className="itinerary-notes-text">{day.notes}</span>
            </div>
          )}

        </div>
      )}
    </div>
  );
}

// ─── Main Itinerary section ───────────────────────────────────────────────────
function ItinerarySection({ destName, numDays, tripData, isLoggedIn }) {
  const navigate = useNavigate();
  const [state, setState] = useState('idle'); // idle | loading | success | error
  const [itinerary, setItinerary] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const generate = useCallback(async () => {
    if (!isLoggedIn) { navigate('/auth'); return; }
    setState('loading');
    setErrorMsg('');
    try {
      const res = await getDayWiseItinerary({
        destination_name: destName,
        num_days: numDays || 3,
        trip_data: tripData || {},
      });
      if (res.success && Array.isArray(res.itinerary) && res.itinerary.length > 0) {
        setItinerary(res.itinerary);
        setState('success');
      } else {
        setItinerary([]);
        setState('empty');
      }
    } catch (err) {
      const msg = err?.response?.data?.error || err?.message || 'Something went wrong. Please try again.';
      setErrorMsg(msg);
      setState('error');
    }
  }, [destName, numDays, tripData, isLoggedIn, navigate]);

  // Retry handler
  const handleRetry = () => {
    setRetryCount(c => c + 1);
    generate();
  };

  // ── Idle: show trigger button or login prompt ─────────────────────────────
  if (state === 'idle') {
    return (
      <div>
        {isLoggedIn ? (
          <button
            id="generate-itinerary-btn"
            className="itinerary-generate-btn"
            onClick={generate}
          >
            <span className="itinerary-btn-icon">🗓</span>
            Generate AI Day-wise Itinerary
          </button>
        ) : (
          <div className="itinerary-login-prompt">
            <span>🔐 Log in to generate a personalised day-wise itinerary for {destName}.</span>
            <button className="btn btn-primary btn-sm" onClick={() => navigate('/auth')}>
              Login / Sign Up
            </button>
          </div>
        )}
      </div>
    );
  }

  // ── Loading: spinner + shimmer skeleton ──────────────────────────────────
  if (state === 'loading') {
    return (
      <div className="itinerary-loading">
        <div className="itinerary-loading-header">
          <div className="itinerary-loading-spinner" />
          <div className="itinerary-loading-text">Generating your itinerary…</div>
          <div className="itinerary-loading-sub">
            Gemini AI is personalising activities for {destName}
          </div>
        </div>
        <div className="itinerary-skeleton-cards">
          {[1, 2, 3].map(n => (
            <div key={n} className="itinerary-skeleton-card">
              <div className="skeleton-line w-40" style={{ height: 18, marginBottom: 16 }} />
              <div className="skeleton-line w-100" />
              <div className="skeleton-line w-80" />
              <div className="skeleton-line w-60" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────────
  if (state === 'error') {
    return (
      <div className="itinerary-error">
        <div className="itinerary-error-message">
          <span className="itinerary-error-icon">⚠️</span>
          <span className="itinerary-error-text">
            {errorMsg || 'Failed to generate itinerary.'}
          </span>
        </div>
        <button className="itinerary-retry-btn" onClick={handleRetry}>
          🔄 Retry{retryCount > 0 ? ` (attempt ${retryCount + 1})` : ''}
        </button>
      </div>
    );
  }

  // ── Empty state ──────────────────────────────────────────────────────────
  if (state === 'empty') {
    return (
      <div className="itinerary-empty">
        <div className="itinerary-empty-icon">🗺️</div>
        <h4>No itinerary returned</h4>
        <p>AI could not build a plan this time. Please try again.</p>
        <button className="itinerary-retry-btn" onClick={handleRetry} style={{ marginTop: 8 }}>
          🔄 Try Again
        </button>
      </div>
    );
  }

  // ── Success: render day cards ─────────────────────────────────────────────
  return (
    <div>
      <div className="itinerary-header">
        <div className="itinerary-header-left">
          <h4>🗓 {itinerary.length}-Day Itinerary for {destName}</h4>
          <p>Personalised by Gemini AI · Click a day to expand</p>
        </div>
        <button
          className="itinerary-refresh-btn"
          onClick={generate}
          title="Regenerate itinerary"
        >
          🔄 Regenerate
        </button>
      </div>
      <div className="itinerary-days">
        {itinerary.map(day => (
          <ItineraryDayCard key={day.day} day={day} />
        ))}
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
function DestinationDetails() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { tripData } = location.state || {};
  const { isLoggedIn } = useAuth();
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reviews, setReviews] = useState([]);
  const [avgRating, setAvgRating] = useState(null);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewForm, setReviewForm] = useState({ rating: 5, title: '', content: '', visited_month: '', travel_style: '' });
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const data = await getDestinationDetail(id);
        setDetails(data);
        if (data.destination_name) {
          const rv = await getReviews(data.destination_name);
          setReviews(rv.reviews || []);
          setAvgRating(rv.avg_rating);
        }
      } catch {
        setError('Failed to load destination details. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!isLoggedIn) { navigate('/auth'); return; }
    setSubmittingReview(true);
    try {
      const data = await addReview({ ...reviewForm, destination_name: details?.destination_name, country: details?.country });
      if (data.success) {
        setReviews(prev => [data.review, ...prev.filter(r => r.id !== data.review.id)]);
        setShowReviewForm(false);
        setReviewForm({ rating: 5, title: '', content: '', visited_month: '', travel_style: '' });
      }
    } catch {}
    setSubmittingReview(false);
  };

  const handleHelpful = async (reviewId) => {
    if (!isLoggedIn) { navigate('/auth'); return; }
    const data = await voteHelpful(reviewId);
    setReviews(prev => prev.map(r => r.id === reviewId ? { ...r, helpful_count: data.helpful_count, user_has_voted: data.voted } : r));
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner" />
        <div className="loading-title">Loading destination details<span className="loading-dots"><span>.</span><span>.</span><span>.</span></span></div>
        <div className="loading-sub">Getting tourist spots, food, transport &amp; tips</div>
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

  const destName = details?.destination_name || 'Destination';
  const destDetails = details?.details || {};
  const { tourist_spots = [], local_food = [], transport_info = {}, accommodation_options = [], travel_tips = [], emergency_info = {} } = destDetails;

  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const STYLES = ['Solo','Couple','Family','Friends','Adventure','Budget','Luxury'];

  return (
    <div className="details-wrapper">
      <nav className="navbar">
        <Link to="/" className="navbar-brand">
          <div className="logo-icon">🧭</div>
          <div className="logo-text">Smart Trip <span>AI</span></div>
        </Link>
        <div style={{ display: 'flex', gap: 10 }}>
          {isLoggedIn && <Link to="/dashboard" className="btn btn-ghost btn-sm">My Dashboard</Link>}
          <Link to="/community" className="btn btn-ghost btn-sm">Community</Link>
          <button onClick={() => window.history.back()} className="btn btn-ghost btn-sm">← Back</button>
        </div>
      </nav>

      {/* Hero */}
      <div className="details-hero">
        <div className="details-hero-inner">
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', marginBottom: 8 }}>📍 Destination Guide</div>
          <h1>{destName}</h1>
          <p style={{ opacity: 0.85, marginTop: 8 }}>{details?.country}</p>
          {details?.summary && <p style={{ marginTop: 16, maxWidth: 600, opacity: 0.9, lineHeight: 1.7, fontSize: 15 }}>{details.summary}</p>}
          <div style={{ display: 'flex', gap: 20, marginTop: 20, flexWrap: 'wrap', alignItems: 'center' }}>
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
            {avgRating && (
              <div>
                <div style={{ fontSize: 11, opacity: 0.7, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Community Rating</div>
                <div style={{ fontSize: 16, fontWeight: 700 }}>⭐ {avgRating}/5 ({reviews.length} reviews)</div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="details-container">

        {/* ======= AI DAY-WISE ITINERARY (NEW) ======= */}
        <div className="details-section">
          <div className="details-section-header">
            <div className="details-section-icon">🗓</div>
            <h3>AI Day-wise Itinerary</h3>
          </div>
          <div className="details-section-body">
            <ItinerarySection
              destName={destName}
              numDays={tripData?.num_days || details?.num_days || 3}
              tripData={tripData}
              isLoggedIn={isLoggedIn}
            />
          </div>
        </div>

        {/* Tourist Spots */}
        {tourist_spots.length > 0 && (
          <div className="details-section">
            <div className="details-section-header">
              <div className="details-section-icon">🗺</div>
              <h3>Tourist Spots &amp; Attractions</h3>
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
              <h3>Local Food &amp; Restaurants</h3>
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
                    <div className="spot-meta"><span>💰 {acc.price_range}</span></div>
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
                {emergency_info.emergency_number && <div className="emergency-item"><label>Emergency Number</label><p>📞 {emergency_info.emergency_number}</p></div>}
                {emergency_info.nearest_hospital && <div className="emergency-item"><label>Nearest Hospital</label><p>🏥 {emergency_info.nearest_hospital}</p></div>}
                {emergency_info.indian_embassy && <div className="emergency-item"><label>Indian Embassy</label><p>🇮🇳 {emergency_info.indian_embassy}</p></div>}
                {emergency_info.useful_apps && <div className="emergency-item"><label>Useful Apps</label><p>📱 {emergency_info.useful_apps}</p></div>}
              </div>
            </div>
          </div>
        )}

        {/* ======= REVIEWS SECTION ======= */}
        <div className="details-section">
          <div className="details-section-header">
            <div className="details-section-icon">⭐</div>
            <h3>Community Reviews {avgRating && <span style={{ fontSize: 14, fontWeight: 400, color: 'var(--text-secondary)' }}>· {avgRating}/5 avg</span>}</h3>
          </div>
          <div className="details-section-body">
            <div style={{ marginBottom: 20 }}>
              <button onClick={() => { if (!isLoggedIn) { navigate('/auth'); return; } setShowReviewForm(!showReviewForm); }}
                className="btn btn-primary btn-sm">
                {showReviewForm ? '✕ Cancel Review' : '✍️ Write a Review'}
              </button>
            </div>

            {showReviewForm && (
              <form onSubmit={handleReviewSubmit} style={{ background: 'var(--bg-light)', borderRadius: 'var(--radius-md)', padding: 20, marginBottom: 24 }}>
                <h4 style={{ margin: '0 0 16px' }}>Your Review of {destName}</h4>
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 8 }}>Rating</label>
                  <StarRating value={reviewForm.rating} onChange={v => setReviewForm(p => ({ ...p, rating: v }))} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                  <div>
                    <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Month Visited</label>
                    <select className="currency-select" value={reviewForm.visited_month} onChange={e => setReviewForm(p => ({ ...p, visited_month: e.target.value }))}>
                      <option value="">Select month</option>
                      {MONTHS.map(m => <option key={m}>{m}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Travel Style</label>
                    <select className="currency-select" value={reviewForm.travel_style} onChange={e => setReviewForm(p => ({ ...p, travel_style: e.target.value }))}>
                      <option value="">Select style</option>
                      {STYLES.map(s => <option key={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Review Title</label>
                  <input className="step-input" style={{ height: 44 }} placeholder="e.g. Amazing experience!" required value={reviewForm.title} onChange={e => setReviewForm(p => ({ ...p, title: e.target.value }))} />
                </div>
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Your Experience</label>
                  <textarea className="step-input" rows={4} placeholder="Share your honest experience..." required value={reviewForm.content} onChange={e => setReviewForm(p => ({ ...p, content: e.target.value }))} />
                </div>
                <button type="submit" className="btn btn-primary" disabled={submittingReview}>
                  {submittingReview ? 'Submitting...' : 'Submit Review'}
                </button>
              </form>
            )}

            {reviews.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>No reviews yet. Be the first to review {destName}!</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {reviews.map(review => (
                  <div key={review.id} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: 18 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 15 }}>{review.title}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                          by {review.username}
                          {review.visited_month && ` · Visited ${review.visited_month}`}
                          {review.travel_style && ` · ${review.travel_style}`}
                        </div>
                      </div>
                      <StarRating value={review.rating} readOnly />
                    </div>
                    <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 12px' }}>{review.content}</p>
                    <button onClick={() => handleHelpful(review.id)} style={{
                      background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '4px 12px',
                      cursor: 'pointer', fontSize: 12, color: review.user_has_voted ? 'var(--primary)' : 'var(--text-secondary)', fontWeight: 600
                    }}>
                      👍 Helpful ({review.helpful_count})
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 32, display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/plan" className="btn btn-primary btn-lg">Plan Another Trip →</Link>
          {isLoggedIn && <Link to="/dashboard" className="btn btn-ghost btn-lg">📁 My Dashboard</Link>}
          <Link to="/" className="btn btn-ghost btn-lg">← Home</Link>
        </div>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: 12, color: 'var(--text-light)' }}>
          Details &amp; Itinerary powered by Google Gemini AI · Smart Trip AI by Arman Ansari
        </p>
      </div>

      <footer className="footer">
        <div className="footer-brand">Smart Trip <span>AI</span></div>
        <div className="footer-author">Made with ❤️ by Arman Ansari</div>
        <div className="footer-copy">© 2026 Smart Trip AI · Django REST + React + Google Gemini AI</div>
      </footer>
    </div>
  );
}

export default DestinationDetails;
