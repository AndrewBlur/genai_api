// Auth page renderer
import { login, register } from './api.js';

export function renderAuth(onSuccess) {
  let mode = 'login'; // or 'register'

  function render() {
    const app = document.getElementById('app');
    app.innerHTML = `
      <div class="auth-wrapper">
        <div class="auth-card">
          <div class="logo">
            <div class="logo-icon">⚡</div>
            <span class="logo-text">GenAI Chat</span>
          </div>
          <h1 id="auth-title">${mode === 'login' ? 'Welcome back' : 'Create account'}</h1>
          <p class="subtitle">${mode === 'login' ? 'Sign in to continue your conversations' : 'Get started with GenAI Chat'}</p>
          <div class="auth-error" id="auth-error"></div>
          <form id="auth-form">
            <div class="form-group">
              <label for="username">Username</label>
              <input type="text" id="username" placeholder="Enter your username" autocomplete="username" required />
            </div>
            <div class="form-group">
              <label for="password">Password</label>
              <input type="password" id="password" placeholder="Enter your password" autocomplete="current-password" required />
            </div>
            <button type="submit" class="btn-primary" id="auth-submit">
              ${mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>
          <div class="auth-switch">
            ${mode === 'login'
              ? 'Don\'t have an account? <a id="switch-mode">Sign up</a>'
              : 'Already have an account? <a id="switch-mode">Sign in</a>'}
          </div>
        </div>
      </div>
    `;

    // Event listeners
    document.getElementById('auth-form').addEventListener('submit', handleSubmit);
    document.getElementById('switch-mode').addEventListener('click', () => {
      mode = mode === 'login' ? 'register' : 'login';
      render();
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('auth-error');
    const btn = document.getElementById('auth-submit');

    if (!username || !password) {
      showError(errorEl, 'Please fill in all fields');
      return;
    }

    btn.disabled = true;
    btn.textContent = mode === 'login' ? 'Signing in...' : 'Creating account...';

    try {
      if (mode === 'register') {
        await register(username, password);
        // Auto login after register
        await login(username, password);
      } else {
        await login(username, password);
      }
      onSuccess();
    } catch (err) {
      showError(errorEl, err.message);
      btn.disabled = false;
      btn.textContent = mode === 'login' ? 'Sign In' : 'Create Account';
    }
  }

  function showError(el, msg) {
    el.textContent = msg;
    el.classList.add('visible');
    setTimeout(() => el.classList.remove('visible'), 4000);
  }

  render();
}
