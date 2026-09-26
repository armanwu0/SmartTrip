import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { getTrips, getTripDashboard, deleteTrip, getWishlist, removeFromWishlist, updateProfile } from '../api';
import AIChatbot from '../components/AIChatbot';

function Dashboard() {
  const { user, setUser, logout, isLoggedIn, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('trips');
  const [savedTrips, setSavedTrips] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({
    total_trips: 0,
    active_trips: 0,
    completed_trips: 0,
    saved_trips: 0,
    total_planned_budget: 0,
    recent_trips: [],
    recent_conversations: [],
  });
  const [wishlist, setWishlist] = useState([]);
  const [loadingTrips, setLoadingTrips] = useState(true);
  const [editProfile, setEditProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({ first_name: '', last_name: '', email: '', profile: { bio: '', location: '', phone: '' } });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) { navigate('/auth'); return; }
    if (user) {
      setProfileForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        profile: {
          bio: user.profile?.bio || '',
          location: user.profile?.location || '',
          phone: user.profile?.phone || '',
        }
      });
    }
  }, [user, isLoggedIn, authLoading, navigate]);

  useEffect(() => {
    if (!isLoggedIn) return;
    setLoadingTrips(true);
    Promise.all([
      getTrips(),
      getTripDashboard(),
    ])
      .then(([tripData, dashboardData]) => {
        const trips = Array.isArray(tripData) ? tripData : tripData?.results || tripData?.trips || [];
        setSavedTrips(trips);
        setDashboardStats(dashboardData || {
          total_trips: 0,
          active_trips: 0,
          completed_trips: 0,
          saved_trips: 0,
          total_planned_budget: 0,
          recent_trips: [],
          recent_conversations: [],
        });
        setLoadingTrips(false);
      })
      .catch(() => setLoadingTrips(false));
    getWishlist().then(d => setWishlist(d.wishlist || [])).catch(() => {});
  }, [isLoggedIn]);

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this trip?')) return;
    await deleteTrip(id);
    setSavedTrips(prev => prev.filter(t => t.id !== id));
  };

  const handleWishlistRemove = async (id) => {
    await removeFromWishlist(id);
    setWishlist(prev => prev.filter(w => w.id !== id));
  };

  const handleProfileSave = async () => {
    setSaving(true);
    try {
      const data = await updateProfile(profileForm);
      if (data.success) {
        setUser(data.user);
        setMsg('Profile updated!');
        setEditProfile(false);
        setTimeout(() => setMsg(''), 3000);
      }
    } catch { setMsg('Failed to update.'); }
    setSaving(false);
  };

  if (authLoading || !isLoggedIn) return null;

  const displayName = user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.username;

  return (
    <div>
      {/* Navbar */}
      <nav className="navbar">
        <Link to="/" className="navbar-brand">
          <div className="logo-icon">🧭</div>
          <div className="logo-text">Smart Trip <span>AI</span></div>
        </Link>
        <ul className="navbar-links">
          <li><Link to="/plan">Plan Trip</Link></li>
          <li><Link to="/community">Community</Link></li>
        </ul>
        <div className="navbar-cta" style={{ display: 'flex', gap: 10 }}>
          <button onClick={logout} className="btn btn-ghost btn-sm">Logout</button>
          <Link to="/plan" className="btn btn-primary">Plan My Trip →</Link>
        </div>
      </nav>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 20px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 32, flexWrap: 'wrap' }}>
          <div style={{ width: 64, height: 64, background: 'var(--primary)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, flexShrink: 0 }}>
            {user?.profile?.avatar || displayName?.[0]?.toUpperCase() || '👤'}
          </div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Hey, {displayName}! 👋</h1>
            <p style={{ color: 'var(--text-secondary)', margin: '4px 0 0', fontSize: 14 }}>
              {user?.profile?.location || 'Explorer'} · {user?.saved_trips_count || 0} trips saved · {user?.wishlist_count || 0} on wishlist
            </p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 10 }}>
            <Link to="/plan" className="btn btn-primary">+ Plan New Trip</Link>
            <button onClick={() => setEditProfile(!editProfile)} className="btn btn-ghost btn-sm">✏️ Edit Profile</button>
          </div>
        </div>

        {/* Edit Profile */}
        {editProfile && (
          <div style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 24, marginBottom: 28 }}>
            <h3 style={{ marginBottom: 20 }}>Edit Profile</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              {['first_name', 'last_name'].map(field => (
                <div key={field}>
                  <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                    {field === 'first_name' ? 'First Name' : 'Last Name'}
                  </label>
                  <input className="step-input" style={{ height: 44 }} value={profileForm[field]}
                    onChange={e => setProfileForm(p => ({ ...p, [field]: e.target.value }))} />
                </div>
              ))}
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Bio</label>
              <textarea className="step-input" rows={3} placeholder="Tell us about yourself..."
                value={profileForm.profile.bio}
                onChange={e => setProfileForm(p => ({ ...p, profile: { ...p.profile, bio: e.target.value } }))} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div>
                <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Location</label>
                <input className="step-input" style={{ height: 44 }} placeholder="e.g. Mumbai, India"
                  value={profileForm.profile.location}
                  onChange={e => setProfileForm(p => ({ ...p, profile: { ...p.profile, location: e.target.value } }))} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Phone</label>
                <input className="step-input" style={{ height: 44 }} placeholder="+91 98765 43210"
                  value={profileForm.profile.phone}
                  onChange={e => setProfileForm(p => ({ ...p, profile: { ...p.profile, phone: e.target.value } }))} />
              </div>
            </div>
            {msg && <div style={{ color: 'var(--primary)', marginBottom: 12, fontSize: 14 }}>✓ {msg}</div>}
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={handleProfileSave} className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button onClick={() => setEditProfile(false)} className="btn btn-ghost btn-sm">Cancel</button>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: 'var(--bg-gray)', borderRadius: 10, padding: 4, width: 'fit-content', flexWrap: 'wrap' }}>
          {[
            { key: 'trips', label: `My Trips (${savedTrips.length})` },
            { key: 'wishlist', label: `Wishlist (${wishlist.length})` },
            { key: 'assistant', label: '🤖 AI Chatbot' },
            { key: 'stats', label: 'My Stats' },
          ].map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 600, transition: 'all 0.2s',
              background: tab === t.key ? 'white' : 'transparent',
              color: tab === t.key ? 'var(--primary)' : 'var(--text-secondary)',
              boxShadow: tab === t.key ? 'var(--shadow-sm)' : 'none',
            }}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Saved Trips Tab */}
        {tab === 'trips' && (
          <div>
            {loadingTrips ? (
              <p style={{ color: 'var(--text-secondary)' }}>Loading your trips...</p>
            ) : savedTrips.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>🗺️</div>
                <h3>No trips yet</h3>
                <p style={{ marginBottom: 20 }}>Start planning your first AI-powered trip.</p>
                <Link to="/plan" className="btn btn-primary">Plan My Trip</Link>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 16 }}>
                {savedTrips.map(trip => (
                  <div key={trip.id} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: 200 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                        <h3 style={{ margin: 0, fontSize: 18 }}>{trip.trip_name || trip.destination || 'Untitled trip'}</h3>
                        {trip.status === 'COMPLETED' && <span style={{ fontSize: 11, background: '#dcfce7', color: '#166534', padding: '2px 8px', borderRadius: 999, fontWeight: 600 }}>✓ Completed</span>}
                      </div>
                      <p style={{ color: 'var(--text-secondary)', fontSize: 13, margin: '0 0 8px' }}>📍 {trip.source || 'Unknown'} → {trip.destination} · 💰 {trip.currency} {trip.total_budget}</p>
                      <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: 0 }}>{trip.number_of_travelers} traveller{trip.number_of_travelers > 1 ? 's' : ''} • {trip.travel_style || 'Travel'} • {trip.status}</p>
                      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>Created: {trip.created_at ? new Date(trip.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}</p>
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                      <button onClick={() => navigate(`/trips/${trip.id}`)} className="btn btn-ghost btn-sm">View Trip</button>
                      <button onClick={() => handleDelete(trip.id)} className="btn btn-ghost btn-sm" style={{ color: '#ef4444' }}>Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Wishlist Tab */}
        {tab === 'wishlist' && (
          <div>
            {wishlist.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>🌟</div>
                <h3>Your wishlist is empty</h3>
                <p>Add destinations to your wishlist from the results page!</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px,1fr))', gap: 16 }}>
                {wishlist.map(item => (
                  <div key={item.id} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🌍</div>
                    <h4 style={{ margin: '0 0 4px' }}>{item.destination_name}</h4>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 16px' }}>📍 {item.country}</p>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <Link to="/plan" className="btn btn-ghost btn-sm" style={{ fontSize: 12 }}>Plan Trip</Link>
                      <button onClick={() => handleWishlistRemove(item.id)} className="btn btn-ghost btn-sm" style={{ color: '#ef4444', fontSize: 12 }}>Remove</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* AI Assistant Tab */}
        {tab === 'assistant' && (
          <div style={{ maxWidth: 700, margin: '0 auto' }}>
            <AIChatbot embedded={true} onTripCreated={(trip) => setSavedTrips(previous => [trip, ...previous.filter(item => item.id !== trip.id)])} />
          </div>
        )}

        {/* Stats Tab */}
        {tab === 'stats' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px,1fr))', gap: 20 }}>
            {[
              { icon: '🗺️', label: 'Total Trips', value: dashboardStats.total_trips || savedTrips.length || 0 },
              { icon: '✅', label: 'Active Trips', value: dashboardStats.active_trips || 0 },
              { icon: '🏁', label: 'Completed Trips', value: dashboardStats.completed_trips || 0 },
              { icon: '💰', label: 'Budget Planned', value: `₹${Number(dashboardStats.total_planned_budget || 0).toLocaleString('en-IN')}` },
            ].map((stat, i) => (
              <div key={i} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 28, textAlign: 'center' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>{stat.icon}</div>
                <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--primary)', lineHeight: 1 }}>{stat.value}</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 6 }}>{stat.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
