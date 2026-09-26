import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginUser, registerUser } from '../api';
import { useAuth } from '../AuthContext';

function AuthPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    username: '', email: '', first_name: '', last_name: '',
    password: '', password2: ''
  });

  const update = (k, v) => { setForm(p => ({ ...p, [k]: v })); setError(''); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      let data;
      if (mode === 'login') {
        data = await loginUser({ username: form.username, password: form.password });
      } else {
        data = await registerUser(form);
      }
      if (data.success) {
        login(data.tokens || { access: data.access, refresh: data.refresh, token: data.token }, data.user);
        navigate('/dashboard');
      } else {
        const errs = data.errors || {};
        setError(Object.values(errs).flat().join(' ') || 'Something went wrong.');
      }
    } catch (err) {
      const errs = err.response?.data?.errors || {};
      setError(Object.values(errs).flat().join(' ') || 'Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <Link to="/" className="auth-logo">
          <div className="logo-icon">🧭</div>
          <div className="logo-text">Smart Trip <span>AI</span></div>
        </Link>

        <div className="auth-tabs">
          <button className={`auth-tab ${mode === 'login' ? 'active' : ''}`} onClick={() => { setMode('login'); setError(''); }}>
            Sign In
          </button>
          <button className={`auth-tab ${mode === 'register' ? 'active' : ''}`} onClick={() => { setMode('register'); setError(''); }}>
            Create Account
          </button>
        </div>

        <h2 className="auth-title">
          {mode === 'login' ? 'Welcome back! 👋' : 'Join Smart Trip AI ✈️'}
        </h2>
        <p className="auth-sub">
          {mode === 'login'
            ? 'Sign in to access your saved trips and plan new adventures'
            : 'Create an account to save trips, write reviews, and explore the community'
          }
        </p>

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'register' && (
            <div className="auth-row">
              <div className="auth-field">
                <label>First Name</label>
                <input type="text" placeholder="Arman" value={form.first_name} onChange={e => update('first_name', e.target.value)} required />
              </div>
              <div className="auth-field">
                <label>Last Name</label>
                <input type="text" placeholder="Ansari" value={form.last_name} onChange={e => update('last_name', e.target.value)} />
              </div>
            </div>
          )}

          <div className="auth-field">
            <label>Username</label>
            <input
              type="text" placeholder="arman123"
              value={form.username} onChange={e => update('username', e.target.value)} required
            />
          </div>

          {mode === 'register' && (
            <div className="auth-field">
              <label>Email</label>
              <input type="email" placeholder="arman@example.com" value={form.email} onChange={e => update('email', e.target.value)} required />
            </div>
          )}

          <div className="auth-field">
            <label>Password</label>
            <input type="password" placeholder="Min 6 characters" value={form.password} onChange={e => update('password', e.target.value)} required />
          </div>

          {mode === 'register' && (
            <div className="auth-field">
              <label>Confirm Password</label>
              <input type="password" placeholder="Re-enter password" value={form.password2} onChange={e => update('password2', e.target.value)} required />
            </div>
          )}

          {error && <div className="error-msg">⚠️ {error}</div>}

          <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
            {loading ? '⏳ Please wait...' : mode === 'login' ? 'Sign In →' : 'Create Account →'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--text-light)' }}>
          {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}
            style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}
          >
            {mode === 'login' ? 'Create one' : 'Sign in'}
          </button>
        </p>

        <p style={{ textAlign: 'center', marginTop: 8 }}>
          <Link to="/" style={{ fontSize: 13, color: 'var(--text-light)' }}>← Back to Home</Link>
        </p>
      </div>
    </div>
  );
}

export default AuthPage;
