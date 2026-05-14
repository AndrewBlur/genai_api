// API helper module
const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  localStorage.setItem('token', token);
}

function clearToken() {
  localStorage.removeItem('token');
}

function getUsername() {
  return localStorage.getItem('username') || '';
}

function setUsername(name) {
  localStorage.setItem('username', name);
}

async function request(path, options = {}) {
  const headers = { ...options.headers };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.reload();
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }

  return res.json();
}

export async function login(username, password) {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(err.detail || 'Login failed');
  }
  const data = await res.json();
  setToken(data.access_token);
  setUsername(username);
  return data;
}

export async function register(username, password) {
  return request('/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function sendMessage(modelName, message, chatId) {
  const payload = { model_name: modelName, message };
  if (chatId) payload.chat_id = chatId;
  return request('/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getChats() {
  return request('/chats');
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/store', {
    method: 'POST',
    body: formData,
  });
}

export { getToken, clearToken, getUsername, setUsername };
