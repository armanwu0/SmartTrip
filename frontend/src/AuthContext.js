import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getMe, logoutUser } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('smarttrip_access_token') || localStorage.getItem('smarttrip_token');
    if (!token) { setLoading(false); return; }
    try {
      const data = await getMe();
      if (data.success) setUser(data.user);
    } catch {
      localStorage.removeItem('smarttrip_access_token');
      localStorage.removeItem('smarttrip_refresh_token');
      localStorage.removeItem('smarttrip_token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUser(); }, [loadUser]);

  useEffect(() => {
    const handleAuthLogout = () => setUser(null);
    window.addEventListener('auth_logout', handleAuthLogout);
    return () => window.removeEventListener('auth_logout', handleAuthLogout);
  }, []);

  const login = (tokens, userData) => {
    const access = typeof tokens === 'string' ? tokens : (tokens?.access || tokens?.token);
    const refresh = typeof tokens === 'object' ? tokens?.refresh : null;
    if (access) {
      localStorage.setItem('smarttrip_access_token', access);
      localStorage.setItem('smarttrip_token', access);
    }
    if (refresh) {
      localStorage.setItem('smarttrip_refresh_token', refresh);
    }
    setUser(userData);
  };

  const logout = async () => {
    const refresh = localStorage.getItem('smarttrip_refresh_token');
    try { await logoutUser({ refresh }); } catch {}
    localStorage.removeItem('smarttrip_access_token');
    localStorage.removeItem('smarttrip_refresh_token');
    localStorage.removeItem('smarttrip_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

