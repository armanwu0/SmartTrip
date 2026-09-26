import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { getBlogs, getTrending, likeBlog, createBlog } from '../api';

function Community() {
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('blogs');
  const [blogs, setBlogs] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [showCreateBlog, setShowCreateBlog] = useState(false);
  const [blogForm, setBlogForm] = useState({ title: '', destination: '', country: '', content: '', cover_emoji: '✈️', tags: '' });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getBlogs('', 1).then(d => {
        setBlogs(d.blogs || []);
        setHasMore(!!d.next);
        setTotalCount(d.count || (d.blogs ? d.blogs.length : 0));
      }),
      getTrending(1).then(d => setTrending(d.trending || []))
    ]).finally(() => setLoading(false));
  }, []);

  const handleLoadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    const nextPage = page + 1;
    try {
      const data = await getBlogs('', nextPage);
      setBlogs(prev => [...prev, ...(data.blogs || [])]);
      setPage(nextPage);
      setHasMore(!!data.next);
    } catch {
    } finally {
      setLoadingMore(false);
    }
  };

  const handleLike = async (blogId) => {
    if (!isLoggedIn) { navigate('/auth'); return; }
    const data = await likeBlog(blogId);
    setBlogs(prev => prev.map(b => b.id === blogId ? { ...b, likes: data.likes, user_has_liked: data.liked } : b));
  };

  const handleCreateBlog = async (e) => {
    e.preventDefault();
    if (!isLoggedIn) { navigate('/auth'); return; }
    setSubmitting(true);
    try {
      const data = await createBlog(blogForm);
      if (data.success) {
        setBlogs(prev => [data.blog, ...prev]);
        setShowCreateBlog(false);
        setBlogForm({ title: '', destination: '', country: '', content: '', cover_emoji: '✈️', tags: '' });
      }
    } catch {}
    setSubmitting(false);
  };

  const EMOJIS = ['✈️', '🏖️', '🏔️', '🌴', '🏛️', '🍜', '🌿', '💎', '🎭', '🙏', '🏕️', '🚢'];

  return (
    <div>
      <nav className="navbar">
        <Link to="/" className="navbar-brand">
          <div className="logo-icon">🧭</div>
          <div className="logo-text">Smart Trip <span>AI</span></div>
        </Link>
        <ul className="navbar-links">
          <li><Link to="/plan">Plan Trip</Link></li>
          <li><Link to="/community" style={{ color: 'var(--primary)', fontWeight: 600 }}>Community</Link></li>
          {isLoggedIn && <li><Link to="/dashboard">Dashboard</Link></li>}
        </ul>
        <div className="navbar-cta">
          {isLoggedIn
            ? <Link to="/dashboard" className="btn btn-primary">My Dashboard →</Link>
            : <Link to="/auth" className="btn btn-primary">Sign In →</Link>
          }
        </div>
      </nav>

      {/* Hero */}
      <div style={{ background: 'linear-gradient(135deg, var(--primary-dark), var(--primary))', padding: '48px 20px', textAlign: 'center', color: 'white' }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, margin: '0 0 12px' }}>✈️ Travel Community</h1>
        <p style={{ opacity: 0.9, maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.7 }}>
          Share your experiences, read real reviews, and get inspired by fellow travelers
        </p>
        <button onClick={() => { if (!isLoggedIn) { navigate('/auth'); return; } setShowCreateBlog(true); }}
          className="btn" style={{ background: 'white', color: 'var(--primary)', fontWeight: 700, padding: '12px 28px', borderRadius: 12 }}>
          + Write a Travel Blog
        </button>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 20px' }}>

        {/* Create Blog Modal */}
        {showCreateBlog && (
          <div style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-xl)', padding: 28, marginBottom: 32, boxShadow: 'var(--shadow-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0 }}>✍️ Write Your Travel Story</h3>
              <button onClick={() => setShowCreateBlog(false)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
            </div>
            <form onSubmit={handleCreateBlog}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div>
                  <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Blog Title</label>
                  <input className="step-input" style={{ height: 44 }} placeholder="My Amazing Trip to Bali..." required
                    value={blogForm.title} onChange={e => setBlogForm(p => ({ ...p, title: e.target.value }))} />
                </div>
                <div>
                  <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Destination</label>
                  <input className="step-input" style={{ height: 44 }} placeholder="Bali, Indonesia" required
                    value={blogForm.destination} onChange={e => setBlogForm(p => ({ ...p, destination: e.target.value }))} />
                </div>
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Cover Emoji</label>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {EMOJIS.map(em => (
                    <button key={em} type="button" onClick={() => setBlogForm(p => ({ ...p, cover_emoji: em }))}
                      style={{ fontSize: 22, padding: 8, borderRadius: 8, border: `2px solid ${blogForm.cover_emoji === em ? 'var(--primary)' : 'var(--border)'}`, background: 'white', cursor: 'pointer' }}>
                      {em}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Your Story</label>
                <textarea className="step-input" rows={6} placeholder="Share your experience, tips, memorable moments..." required
                  value={blogForm.content} onChange={e => setBlogForm(p => ({ ...p, content: e.target.value }))} />
              </div>
              <div style={{ marginBottom: 20 }}>
                <label style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Tags (comma separated)</label>
                <input className="step-input" style={{ height: 44 }} placeholder="beach, adventure, budget, food..."
                  value={blogForm.tags} onChange={e => setBlogForm(p => ({ ...p, tags: e.target.value }))} />
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Publishing...' : 'Publish Story 🚀'}
                </button>
                <button type="button" onClick={() => setShowCreateBlog(false)} className="btn btn-ghost btn-sm">Cancel</button>
              </div>
            </form>
          </div>
        )}

        {/* Trending */}
        {trending.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ marginBottom: 16, color: 'var(--text-secondary)', fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.5px' }}>🔥 Trending Destinations</h3>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {trending.map((t, i) => (
                <button key={i} onClick={() => navigate('/plan')} style={{
                  padding: '8px 16px', borderRadius: 999, border: '1px solid var(--border)', background: 'white',
                  fontSize: 13, cursor: 'pointer', color: 'var(--text-primary)', fontWeight: 500,
                  display: 'flex', alignItems: 'center', gap: 6
                }}>
                  <span style={{ color: 'var(--text-light)', fontSize: 12 }}>#{i + 1}</span>
                  {t.destination_name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: 'var(--bg-gray)', borderRadius: 10, padding: 4, width: 'fit-content' }}>
          {[{ key: 'blogs', label: `Travel Stories (${totalCount || blogs.length})` }].map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 600,
              background: tab === t.key ? 'white' : 'transparent',
              color: tab === t.key ? 'var(--primary)' : 'var(--text-secondary)',
              boxShadow: tab === t.key ? 'var(--shadow-sm)' : 'none',
            }}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Blogs */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-secondary)' }}>Loading stories...</div>
        ) : blogs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📖</div>
            <h3>No stories yet</h3>
            <p style={{ marginBottom: 20 }}>Be the first to share your travel experience!</p>
            <button onClick={() => { if (!isLoggedIn) { navigate('/auth'); return; } setShowCreateBlog(true); }} className="btn btn-primary">
              Write First Story →
            </button>
          </div>
        ) : (
          <div>
            <div style={{ display: 'grid', gap: 20 }}>
              {blogs.map(blog => (
                <div key={blog.id} style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 24 }}>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                    <div style={{ fontSize: 40, flexShrink: 0, width: 56, height: 56, background: 'var(--bg-light)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {blog.cover_emoji}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <h3 style={{ margin: '0 0 6px', fontSize: 18 }}>{blog.title}</h3>
                      <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 10px' }}>
                        📍 {blog.destination} · ✍️ {blog.username} · 👁 {blog.views} views
                      </p>
                      <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '0 0 12px', lineHeight: 1.6 }}>
                        {blog.content.slice(0, 200)}{blog.content.length > 200 ? '...' : ''}
                      </p>
                      {blog.tags_list?.length > 0 && (
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
                          {blog.tags_list.map((tag, i) => (
                            <span key={i} style={{ fontSize: 11, background: 'var(--primary-light)', color: 'var(--primary-dark)', padding: '2px 10px', borderRadius: 999, fontWeight: 600 }}>
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                      <button onClick={() => handleLike(blog.id)} style={{
                        background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 14px',
                        cursor: 'pointer', fontSize: 13, color: blog.user_has_liked ? '#e11d48' : 'var(--text-secondary)',
                        fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 6
                      }}>
                        {blog.user_has_liked ? '❤️' : '🤍'} {blog.likes} Likes
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {hasMore && (
              <div style={{ textAlign: 'center', marginTop: 28 }}>
                <button
                  onClick={handleLoadMore}
                  className="btn btn-ghost"
                  disabled={loadingMore}
                  style={{ padding: '10px 24px', fontWeight: 600 }}
                >
                  {loadingMore ? '⏳ Loading more stories...' : 'Load More Stories 👇'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <footer className="footer">
        <div className="footer-brand">Smart Trip <span>AI</span></div>
        <div className="footer-copy">© 2026 Smart Trip AI · Made with ❤️ by Arman Ansari</div>
      </footer>
    </div>
  );
}

export default Community;
