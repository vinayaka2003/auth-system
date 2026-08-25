/* ── Centralized API client ────────────────────────────────── */

// Automatically uses local backend when testing locally, or your deployed backend URL in production
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : 'https://auth-system-backend-7rq4.onrender.com';

const api = {
  /** Attach auth token from storage */
  _headers(extra = {}) {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...extra
    };
  },

  /** Core fetch wrapper — returns { ok, status, data, error } */
  async _req(method, path, body) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: this._headers(),
        ...(body !== undefined ? { body: JSON.stringify(body) } : {})
      });
      let data;
      try { data = await res.json(); } catch { data = {}; }
      if (!res.ok) return { ok: false, status: res.status, error: data.detail || 'Something went wrong', data };
      return { ok: true, status: res.status, data, error: null };
    } catch (err) {
      return { ok: false, status: 0, error: 'Cannot reach server. Make sure the backend is running.', data: null };
    }
  },

  get:   (path)       => api._req('GET',  path),
  post:  (path, body) => api._req('POST', path, body),

  /** Auth helpers */
  signup:        (name, email, password) => api.post('/signup',       { name, email, password }),
  login:         (email, password)       => api.post('/login',        { email, password }),
  googleLogin:   (token)                 => api.post('/google-login', { token }),
  forgotPw:      (email)                 => api.post('/forgot-password', { email }),
  me:            ()                      => api.get('/me'),

  /** Persist token depending on remember-me */
  saveToken(token, remember = false) {
    if (remember) {
      localStorage.setItem('token', token);
      sessionStorage.removeItem('token');
    } else {
      sessionStorage.setItem('token', token);
      localStorage.removeItem('token');
    }
  },

  getToken() {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  },

  clearToken() {
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    localStorage.removeItem('guest');
  },

  isLoggedIn() {
    return !!(this.getToken() || localStorage.getItem('guest') === 'true');
  }
};
