// App entry point — routes between auth and chat
import './style.css';
import { getToken } from './api.js';
import { renderAuth } from './auth.js';
import { renderChat } from './chat.js';

function boot() {
  if (getToken()) {
    renderChat(() => boot());
  } else {
    renderAuth(() => boot());
  }
}

boot();
