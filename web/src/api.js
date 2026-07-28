const API_BASE = import.meta.env.VITE_API_URL || 'https://biomed-production.up.railway.app';

function token() {
  return localStorage.getItem('zf_token') || '';
}

export async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token()) headers['Authorization'] = `Bearer ${token()}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function setToken(t) { localStorage.setItem('zf_token', t); }
export function clearToken() { localStorage.removeItem('zf_token'); localStorage.removeItem('zf_role'); localStorage.removeItem('zf_name'); localStorage.removeItem('zf_agent_code'); }
export function getToken() { return token(); }

export function saveSession(data) {
  if (data.token) setToken(data.token);
  if (data.role) localStorage.setItem('zf_role', data.role);
  if (data.name) localStorage.setItem('zf_name', data.name);
  if (data.agent_code) localStorage.setItem('zf_agent_code', data.agent_code);
}

export function getRole() { return localStorage.getItem('zf_role') || ''; }
export function getName() { return localStorage.getItem('zf_name') || ''; }
export function getAgentCode() { return localStorage.getItem('zf_agent_code') || ''; }

export async function login(email, password) {
  const res = await api('/api/auth/login/role', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (res.authenticated) saveSession(res);
  return res;
}

export async function register(data) {
  return api('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function registerAgent(data) {
  return api('/api/auth/register/agent', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
