import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import AIChatbot from '../components/AIChatbot';
import { searchPlaces } from '../api';

const DESTINATIONS = [
  { name: 'Bali, Indonesia', country: 'Indonesia', tags: ['Beach', 'Culture', 'Nature'], cost: '₹50,000 – ₹1,20,000', time: 'Apr – Oct', bg: 'linear-gradient(135deg, #1D9E75, #5DCAA5)', emoji: '🏝' },
  { name: 'Dubai, UAE', country: 'UAE', tags: ['Luxury', 'Shopping', 'Modern'], cost: '₹80,000 – ₹2,50,000', time: 'Nov – Apr', bg: 'linear-gradient(135deg, #185FA5, #85B7EB)', emoji: '🏙' },
  { name: 'Manali, India', country: 'India', tags: ['Adventure', 'Snow', 'Mountains'], cost: '₹15,000 – ₹40,000', time: 'Oct – Jun', bg: 'linear-gradient(135deg, #0d4f38, #1D9E75)', emoji: '🏔' },
  { name: 'Rajasthan, India', country: 'India', tags: ['Heritage', 'Culture', 'Desert'], cost: '₹20,000 – ₹60,000', time: 'Oct – Mar', bg: 'linear-gradient(135deg, #D85A30, #F0997B)', emoji: '🏰' },
  { name: 'Thailand', country: 'Thailand', tags: ['Beaches', 'Food', 'Budget'], cost: '₹40,000 – ₹90,000', time: 'Nov – Apr', bg: 'linear-gradient(135deg, #534AB7, #AFA9EC)', emoji: '🌴' },
  { name: 'Paris, France', country: 'France', tags: ['Romance', 'Art', 'Culture'], cost: '₹1,50,000 – ₹3,50,000', time: 'Apr – Jun', bg: 'linear-gradient(135deg, #993C1D, #F0997B)', emoji: '🗼' },
];

function Home() {
  const navigate = useNavigate();
  const { user, isLoggedIn, logout } = useAuth();
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });
  const [darkMode, setDarkMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('Manali');
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);

  const toggleDark = () => {
    setDarkMode(d => {
      document.body.classList.toggle('dark-mode', !d);
      return !d;
    });
  };

  const handleContactSubmit = (e) => {
    e.preventDefault();
    alert("Thanks for reaching out! We'll get back to you soon.");
    setContactForm({ name: '', email: '', message: '' });
  };

  const handlePlaceSearch = async (event) => {
    const value = event?.target?.value ?? searchQuery;
    const query = value.trim();
    setSearchQuery(value);

    if (!query) {
      setSearchResults([]);
      setSearchError('');
      return;
    }

    setSearchLoading(true);
    setSearchError('');
    try {
      const response = await searchPlaces(query, '');
      const results = response?.results || [];
      setSearchResults(results.slice(0, 6));
      if (!results.length) setSearchError('No matching places were found.');
    } catch (error) {
      setSearchError('Live place search is unavailable until GOOGLE_MAPS_API_KEY is configured.');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const displayName = user?.first_name || user?.username;

  return (
    <div>
      {/* NAVBAR - Updated with Auth links */}
      <nav className="navbar">
        <Link to="/" className="navbar-brand">
          <div className="logo-icon">🧭</div>
          <div className="logo-text">Smart Trip <span>AI</span></div>
        </Link>
        <ul className="navbar-links">
          <li><a href="#how">How it Works</a></li>
          <li><a href="#destinations">Destinations</a></li>
          <li><a href="#chatbot-section">🤖 AI Chatbot</a></li>
          <li><Link to="/community">Community</Link></li>
          <li><a href="#contact">Contact</a></li>
        </ul>
        <div className="navbar-cta">
          {isLoggedIn ? (
            <>
              <Link to="/dashboard" className="btn btn-ghost btn-sm">👋 {displayName}</Link>
              <button onClick={logout} className="btn btn-ghost btn-sm">Logout</button>
              <Link to="/plan" className="btn btn-primary">Plan My Trip →</Link>
            </>
          ) : (
            <>
              <Link to="/auth" className="btn btn-ghost btn-sm">Sign In</Link>
              <Link to="/plan" className="btn btn-primary">Plan My Trip →</Link>
            </>
          )}
        </div>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-bg-shapes">
          <div className="hero-shape hero-shape-1" />
          <div className="hero-shape hero-shape-2" />
          <div className="hero-shape hero-shape-3" />
        </div>
        <div className="hero-content">
          <div className="hero-left">
            <div className="hero-badge">✨ Powered by Google Gemini AI</div>
            <h1>You have the money,<br /><span>we have the map.</span></h1>
            <p className="hero-subtitle">
              Get personalized travel recommendations tailored to your budget, travel style,
              and preferences — all powered by cutting-edge AI.
            </p>
            <div className="hero-buttons">
              <Link to="/plan" className="btn-hero-primary">Start Planning →</Link>
              {isLoggedIn
                ? <Link to="/dashboard" className="btn-hero-outline">📁 My Dashboard</Link>
                : <Link to="/auth" className="btn-hero-outline">Join Free</Link>
              }
            </div>
            <div className="hero-stats">
              <div className="hero-stat">
                <div className="hero-stat-num">500+</div>
                <div className="hero-stat-label">Destinations</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-num">20+</div>
                <div className="hero-stat-label">Travel Styles</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-num">AI</div>
                <div className="hero-stat-label">Powered</div>
              </div>
            </div>
          </div>
          <div className="hero-card">
            <div className="hero-card-title">🗺 How Smart Trip AI works</div>
            <div className="hero-card-steps">
              {[
                { num: 1, title: 'Tell us your budget', desc: 'Multi-currency support — INR, USD, EUR & more' },
                { num: 2, title: 'Set your preferences', desc: 'Solo/group, travel style, duration & more' },
                { num: 3, title: 'AI recommends', desc: 'Gemini AI picks top 3 destinations for you' },
                { num: 4, title: 'Save & share', desc: 'Save trips, write reviews, share with friends' },
              ].map(s => (
                <div key={s.num} className="hero-card-step">
                  <div className="hero-step-num">{s.num}</div>
                  <div className="hero-step-text">
                    <strong>{s.title}</strong>
                    {s.desc}
                  </div>
                </div>
              ))}
            </div>
            {!isLoggedIn && (
              <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border)' }}>
                <Link to="/auth" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                  Create Free Account →
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      <section style={{ maxWidth: 1200, margin: '0 auto', padding: '20px 24px 8px' }}>
        <div style={{ background: 'rgba(255,255,255,0.82)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-sm)', padding: 18 }}>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ flex: 1, minWidth: 240 }}>
              <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-secondary)', fontWeight: 700 }}>Global Search</div>
              <input
                value={searchQuery}
                onChange={handlePlaceSearch}
                placeholder="Search places, cities, landmarks, hotels, restaurants..."
                style={{ width: '100%', marginTop: 8, padding: '14px 16px', borderRadius: 12, border: '1px solid var(--border)', fontSize: 15 }}
              />
            </div>
            <button className="btn btn-primary" onClick={() => handlePlaceSearch({ target: { value: searchQuery } })}>
              Search
            </button>
          </div>

          {searchLoading && <p style={{ marginTop: 12, color: 'var(--text-secondary)' }}>Loading live search results…</p>}
          {searchError && <p style={{ marginTop: 12, color: '#b91c1c' }}>{searchError}</p>}
          {searchResults.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginTop: 16 }}>
              {searchResults.map((place, idx) => (
                <div key={place.place_id || idx} style={{ border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden', background: '#fff' }}>
                  <div style={{ height: 120, background: place.photo_url ? `url(${place.photo_url}) center/cover no-repeat` : 'linear-gradient(135deg, #d5f7ec, #cfe8ff)' }} />
                  <div style={{ padding: 14 }}>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{place.name || 'Place'}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 6 }}>{place.address || 'Address unavailable'}</div>
                    <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--primary-dark)', fontSize: 12 }}>
                      <span>⭐ {place.rating || 'N/A'}</span>
                      <span>{place.data_status === 'verified' ? '✓ Verified' : '≈ Estimated'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* NEW FEATURES BANNER */}
      <section style={{ background: 'var(--primary-light)', borderTop: '1px solid #c8edd9', borderBottom: '1px solid #c8edd9', padding: '20px 32px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', gap: 32, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center' }}>
          {[
            { icon: '🔖', label: 'Save Trips', desc: 'Save your favourite recommendations' },
            { icon: '⭐', label: 'Reviews', desc: 'Read & write destination reviews' },
            { icon: '✍️', label: 'Travel Blogs', desc: 'Share your travel stories' },
            { icon: '🌟', label: 'Wishlist', desc: 'Build your travel bucket list' },
          ].map((f, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 22 }}>{f.icon}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary-dark)' }}>{f.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{f.desc}</div>
              </div>
            </div>
          ))}
          {!isLoggedIn && (
            <Link to="/auth" className="btn btn-primary btn-sm" style={{ marginLeft: 'auto' }}>
              Sign Up Free →
            </Link>
          )}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="how-it-works" id="how">
        <div className="section section-center">
          <div className="section-badge">Simple Process</div>
          <h2 className="section-title">Plan your dream trip in minutes</h2>
          <p className="section-subtitle">Just a few quick steps and our AI does all the heavy lifting for you</p>
          <div className="how-grid">
            {[
              { icon: '💬', title: 'Tell Us About You', desc: 'Name, budget, travel companions, and how many days you want to travel' },
              { icon: '🎯', title: 'Set Preferences', desc: 'Choose travel style, food preferences, accommodation, and transport medium' },
              { icon: '🤖', title: 'AI Analyzes', desc: 'Google Gemini AI processes your inputs and finds the perfect destinations' },
              { icon: '✈️', title: 'Save & Explore', desc: 'Get recommendations, save trips, read reviews & write travel blogs' },
            ].map((item, i) => (
              <div key={i} className="how-card">
                <div className="how-num">{i + 1}</div>
                <div className="how-icon">{item.icon}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DESTINATIONS */}
      <section id="destinations">
        <div className="section">
          <div className="section-center">
            <div className="section-badge">Explore</div>
            <h2 className="section-title">Popular destinations</h2>
            <p className="section-subtitle">AI-curated picks based on trending traveler preferences</p>
          </div>
          <div className="dest-grid">
            {DESTINATIONS.map((dest, i) => (
              <div key={i} className="dest-card" onClick={() => navigate('/plan')}>
                <div className="dest-img" style={{ background: dest.bg }}>
                  <div className="dest-img-overlay" />
                  <div className="dest-img-content">
                    <h3>{dest.emoji} {dest.name}</h3>
                    <span>{dest.country}</span>
                  </div>
                </div>
                <div className="dest-card-body">
                  <div className="dest-tags">
                    {dest.tags.map((t, j) => <span key={j} className="dest-tag">{t}</span>)}
                  </div>
                  <div className="dest-cost">{dest.cost}</div>
                  <div className="dest-time">Best: {dest.time}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-24" style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/plan" className="btn btn-primary btn-lg">Get My AI Recommendations →</Link>
            <Link to="/community" className="btn btn-ghost btn-lg">✍️ Travel Community</Link>
          </div>
        </div>
      </section>

      {/* AI CHATBOT SPOTLIGHT & EMBEDDED CHAT */}
      <section id="chatbot-section" style={{ padding: '60px 32px', background: 'linear-gradient(135deg, #0f766e 0%, #064e3b 100%)', color: 'white' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ background: 'rgba(255,255,255,0.2)', color: 'white', padding: '6px 16px', borderRadius: 20, fontSize: 13, fontWeight: 600, display: 'inline-block', marginBottom: 12 }}>
              ✨ Instant AI Travel Assistant (No Login Required)
            </div>
            <h2 style={{ fontSize: 32, fontWeight: 800, margin: '0 0 12px 0' }}>Ask AI Assistant Anything About Your Trip 🤖</h2>
            <p style={{ fontSize: 16, opacity: 0.95, lineHeight: 1.6, margin: 0, maxWidth: 650, marginLeft: 'auto', marginRight: 'auto' }}>
              Get instant recommendations on budget places in India, best seasons, packing lists, flight options, and local foods powered by Google Gemini AI!
            </p>
          </div>

          <div style={{ maxWidth: 720, margin: '0 auto' }}>
            <AIChatbot embedded={true} />
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section style={{ background: 'var(--bg-light)', padding: '80px 32px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', textAlign: 'center' }}>
          <div className="section-badge">Community Love</div>
          <h2 className="section-title">What travelers say</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px,1fr))', gap: 20, marginTop: 40 }}>
            {[
              { name: 'Priya S.', location: 'Mumbai', text: 'Planned my Bali trip in under 10 minutes! The AI recommendations were spot on for my budget.', rating: 5 },
              { name: 'Rohit K.', location: 'Delhi', text: 'The community reviews helped me pick the best time to visit Manali. Amazing app!', rating: 5 },
              { name: 'Sneha M.', location: 'Bangalore', text: 'Saved 3 trips and wrote my first travel blog here. Love the wishlist feature!', rating: 5 },
            ].map((t, i) => (
              <div key={i} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 24, textAlign: 'left' }}>
                <div style={{ color: '#f59e0b', fontSize: 18, marginBottom: 12 }}>{'★'.repeat(t.rating)}</div>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 16 }}>"{t.text}"</p>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{t.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-light)' }}>📍 {t.location}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CONTACT */}
      <section className="contact-section" id="contact">
        <div className="contact-inner">
          <div className="section-badge">Get In Touch</div>
          <h2 className="section-title">Contact Us</h2>
          <p className="section-subtitle">Have questions or feedback? We'd love to hear from you.</p>
          <form className="contact-form" onSubmit={handleContactSubmit}>
            <input type="text" placeholder="Your name" value={contactForm.name}
              onChange={e => setContactForm({ ...contactForm, name: e.target.value })} required />
            <input type="email" placeholder="Your email" value={contactForm.email}
              onChange={e => setContactForm({ ...contactForm, email: e.target.value })} required />
            <textarea rows="4" placeholder="Your message..." value={contactForm.message}
              onChange={e => setContactForm({ ...contactForm, message: e.target.value })} required />
            <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%', justifyContent: 'center' }}>
              Send Message ✉️
            </button>
          </form>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="footer-brand">Smart Trip <span>AI</span></div>
        <div className="footer-tagline">"You have the money, we have the map."</div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 24, margin: '16px 0', flexWrap: 'wrap' }}>
          <Link to="/plan" style={{ color: 'rgba(255,255,255,0.65)', fontSize: 13, textDecoration: 'none' }}>Plan Trip</Link>
          <Link to="/community" style={{ color: 'rgba(255,255,255,0.65)', fontSize: 13, textDecoration: 'none' }}>Community</Link>
          {isLoggedIn
            ? <Link to="/dashboard" style={{ color: 'rgba(255,255,255,0.65)', fontSize: 13, textDecoration: 'none' }}>Dashboard</Link>
            : <Link to="/auth" style={{ color: 'rgba(255,255,255,0.65)', fontSize: 13, textDecoration: 'none' }}>Sign In</Link>
          }
        </div>
        <div className="footer-author">Made with ❤️ by Arman Ansari</div>
        <div className="footer-copy">© 2026 Smart Trip AI · Django REST + React + Google Gemini AI</div>
      </footer>

      {/* Dark Mode Toggle */}
      <button className="dark-toggle" onClick={toggleDark} title="Toggle dark mode">
        {darkMode ? '☀️' : '🌙'}
      </button>
    </div>
  );
}

export default Home;
