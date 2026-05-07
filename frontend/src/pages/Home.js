import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const DESTINATIONS = [
  {
    name: 'Bali, Indonesia',
    country: 'Indonesia',
    tags: ['Beach', 'Culture', 'Nature'],
    cost: '₹50,000 – ₹1,20,000',
    time: 'Apr – Oct',
    bg: 'linear-gradient(135deg, #1D9E75, #5DCAA5)',
    emoji: '🏝'
  },
  {
    name: 'Dubai, UAE',
    country: 'UAE',
    tags: ['Luxury', 'Shopping', 'Modern'],
    cost: '₹80,000 – ₹2,50,000',
    time: 'Nov – Apr',
    bg: 'linear-gradient(135deg, #185FA5, #85B7EB)',
    emoji: '🏙'
  },
  {
    name: 'Manali, India',
    country: 'India',
    tags: ['Adventure', 'Snow', 'Mountains'],
    cost: '₹15,000 – ₹40,000',
    time: 'Oct – Jun',
    bg: 'linear-gradient(135deg, #0d4f38, #1D9E75)',
    emoji: '🏔'
  },
  {
    name: 'Rajasthan, India',
    country: 'India',
    tags: ['Heritage', 'Culture', 'Desert'],
    cost: '₹20,000 – ₹60,000',
    time: 'Oct – Mar',
    bg: 'linear-gradient(135deg, #D85A30, #F0997B)',
    emoji: '🏰'
  },
  {
    name: 'Thailand',
    country: 'Thailand',
    tags: ['Beaches', 'Food', 'Budget'],
    cost: '₹40,000 – ₹90,000',
    time: 'Nov – Apr',
    bg: 'linear-gradient(135deg, #534AB7, #AFA9EC)',
    emoji: '🌴'
  },
  {
    name: 'Paris, France',
    country: 'France',
    tags: ['Romance', 'Art', 'Culture'],
    cost: '₹1,50,000 – ₹3,50,000',
    time: 'Apr – Jun',
    bg: 'linear-gradient(135deg, #993C1D, #F0997B)',
    emoji: '🗼'
  },
];

function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <div className="logo-icon">🧭</div>
        <div className="logo-text">Smart Trip <span>AI</span></div>
      </Link>
      <ul className="navbar-links">
        <li><a href="#how">How it Works</a></li>
        <li><a href="#destinations">Destinations</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
      <div className="navbar-cta">
        <Link to="/plan" className="btn btn-primary">Plan My Trip →</Link>
      </div>
    </nav>
  );
}

function Home() {
  const navigate = useNavigate();
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });

  const handleContactSubmit = (e) => {
    e.preventDefault();
    alert('Thanks for reaching out! We\'ll get back to you soon.');
    setContactForm({ name: '', email: '', message: '' });
  };

  return (
    <div>
      <Navbar />

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
              <a href="#destinations" className="btn-hero-outline">Explore Destinations</a>
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
                { num: 4, title: 'Explore the details', desc: 'Tourist spots, food, costs & travel tips' },
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
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="how-it-works" id="how">
        <div className="section section-center">
          <div className="section-badge">Simple Process</div>
          <h2 className="section-title">Plan your dream trip in minutes</h2>
          <p className="section-subtitle">Just 9 quick steps and our AI does all the heavy lifting for you</p>
          <div className="how-grid">
            {[
              { icon: '💬', title: 'Tell Us About You', desc: 'Name, budget, travel companions, and how many days you want to travel' },
              { icon: '🎯', title: 'Set Preferences', desc: 'Choose travel style, food preferences, accommodation, and transport medium' },
              { icon: '🤖', title: 'AI Analyzes', desc: 'Google Gemini AI processes your inputs and finds the perfect destinations' },
              { icon: '✈️', title: 'Get Recommendations', desc: 'Receive 3 AI-curated destination picks with full details and cost estimates' },
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
          <div className="text-center mt-24">
            <Link to="/plan" className="btn btn-primary btn-lg">Get My AI Recommendations →</Link>
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
            <input
              type="text"
              placeholder="Your name"
              value={contactForm.name}
              onChange={e => setContactForm({ ...contactForm, name: e.target.value })}
              required
            />
            <input
              type="email"
              placeholder="Your email"
              value={contactForm.email}
              onChange={e => setContactForm({ ...contactForm, email: e.target.value })}
              required
            />
            <textarea
              rows="4"
              placeholder="Your message..."
              value={contactForm.message}
              onChange={e => setContactForm({ ...contactForm, message: e.target.value })}
              required
            />
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
        <div className="footer-author">Made with ❤️ by Arman Ansari</div>
        <div className="footer-copy">© 2026 Smart Trip AI · Django REST + React + Google Gemini AI</div>
      </footer>
    </div>
  );
}

export default Home;
