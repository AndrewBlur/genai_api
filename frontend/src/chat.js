// Chat page renderer
import { sendMessage, getChats, getChat, deleteChat, uploadFile, clearToken, getUsername } from './api.js';

const MODELS = [
  { id: 'qwen/qwen3-32b', name: 'Qwen 3 32B' },
  { id: 'groq/compound', name: 'Groq Compound' },
  { id: 'groq/compound-mini', name: 'Groq Compound Mini' },
  { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B' },
  { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B' },
  { id: 'meta-llama/llama-4-scout-17b-16e-instruct', name: 'Llama 4 Scout 17B' },
  { id: 'openai/gpt-oss-120b', name: 'GPT OSS 120B' },
  { id: 'openai/gpt-oss-20b', name: 'GPT OSS 20B' },
];

let currentChatId = null;
let messages = [];
let sidebarOpen = true;
let isLoading = false;
let chatHistory = [];

export function renderChat(onLogout) {
  const app = document.getElementById('app');
  const username = getUsername();
  const initial = username.charAt(0).toUpperCase();

  app.innerHTML = `
    <div class="chat-layout">
      <!-- Sidebar -->
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-header">
          <div class="s-logo">⚡</div>
          <span class="s-title">GenAI Chat</span>
        </div>
        <button class="new-chat-btn" id="new-chat-btn">＋ New Chat</button>
        <div class="chat-list" id="chat-list">
          <div class="chat-list-label">Recent</div>
        </div>
        <div class="sidebar-footer">
          <div class="user-avatar">${initial}</div>
          <div class="user-info">
            <div class="user-name">${username}</div>
            <div class="user-status">● Online</div>
          </div>
          <button class="logout-btn" id="logout-btn" title="Sign out">⏻</button>
        </div>
      </aside>

      <!-- Main -->
      <main class="chat-main">
        <div class="chat-topbar">
          <button class="toggle-sidebar-btn" id="toggle-sidebar">☰</button>
          <select class="model-select" id="model-select">
            ${MODELS.map(m => `<option value="${m.id}">${m.name}</option>`).join('')}
          </select>
          <div class="topbar-spacer"></div>
          <button class="upload-btn" id="upload-btn">📎 Upload</button>
        </div>
        <div class="messages-container" id="messages-container">
          <div class="messages-inner" id="messages-inner"></div>
        </div>
        <div class="input-area">
          <div class="input-wrapper">
            <div class="input-box">
              <textarea id="message-input" rows="1" placeholder="Type your message..." ></textarea>
              <button class="send-btn" id="send-btn" title="Send">➤</button>
            </div>
            <div class="input-hint">Press Enter to send · Shift+Enter for new line</div>
          </div>
        </div>
      </main>
    </div>
  `;

  bindEvents(onLogout);
  loadChatHistory();
  renderMessages();
}

function bindEvents(onLogout) {
  document.getElementById('toggle-sidebar').addEventListener('click', toggleSidebar);
  document.getElementById('new-chat-btn').addEventListener('click', startNewChat);
  document.getElementById('logout-btn').addEventListener('click', () => {
    clearToken();
    localStorage.removeItem('username');
    onLogout();
  });
  document.getElementById('send-btn').addEventListener('click', handleSend);
  document.getElementById('upload-btn').addEventListener('click', showUploadModal);

  const textarea = document.getElementById('message-input');
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
  textarea.addEventListener('input', autoResize);
}

function autoResize() {
  const ta = document.getElementById('message-input');
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 150) + 'px';
}

function toggleSidebar() {
  sidebarOpen = !sidebarOpen;
  document.getElementById('sidebar').classList.toggle('collapsed', !sidebarOpen);
}

function startNewChat() {
  currentChatId = null;
  messages = [];
  renderMessages();
  highlightActiveChat();
  document.getElementById('message-input').focus();
}

async function loadChatHistory() {
  try {
    chatHistory = await getChats();
    renderChatList();
  } catch (e) {
    console.error('Failed to load chats:', e);
  }
}

function renderChatList() {
  const list = document.getElementById('chat-list');
  if (!chatHistory.length) {
    list.innerHTML = `<div class="chat-list-label">Recent</div>
      <div style="padding:16px 8px;color:var(--text-muted);font-size:13px;text-align:center;">No conversations yet</div>`;
    return;
  }
  list.innerHTML = `<div class="chat-list-label">Recent</div>` +
    chatHistory.map(c => `
      <div class="chat-item ${c.chat_id === currentChatId ? 'active' : ''}" data-id="${c.chat_id}">
        <span class="chat-title">💬 ${escapeHtml(c.title)}</span>
        <button class="delete-chat-btn" data-id="${c.chat_id}" title="Delete chat">🗑️</button>
      </div>
    `).join('');

  list.querySelectorAll('.chat-item').forEach(el => {
    el.addEventListener('click', async (e) => {
      if (e.target.closest('.delete-chat-btn')) return;
      currentChatId = el.dataset.id;
      messages = [];
      renderMessages();
      highlightActiveChat();
      
      try {
        const chatData = await getChat(currentChatId);
        messages = chatData.chat_history || [];
        renderMessages();
      } catch (e) {
        console.error('Failed to load chat history:', e);
        showWelcomeForExisting();
      }
    });
  });

  list.querySelectorAll('.delete-chat-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = btn.dataset.id;
      if (!confirm("Are you sure you want to delete this chat?")) return;
      try {
        await deleteChat(id);
        chatHistory = chatHistory.filter(c => c.chat_id !== id);
        if (currentChatId === id) {
          startNewChat();
        } else {
          renderChatList();
        }
      } catch (err) {
        showToast('Failed to delete chat', 'error');
      }
    });
  });
}

function showWelcomeForExisting() {
  const inner = document.getElementById('messages-inner');
  inner.innerHTML = `
    <div class="welcome-screen" style="height:auto;padding:60px 20px;">
      <div class="welcome-icon" style="width:56px;height:56px;font-size:28px;border-radius:12px;">💬</div>
      <h2 style="font-size:20px;">Chat resumed</h2>
      <p>Continue your conversation. Your previous context is preserved on the server.</p>
    </div>
  `;
}

function highlightActiveChat() {
  document.querySelectorAll('.chat-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === currentChatId);
  });
}

function renderMessages() {
  const inner = document.getElementById('messages-inner');

  if (!messages.length && !currentChatId) {
    inner.innerHTML = `
      <div class="welcome-screen">
        <div class="welcome-icon">⚡</div>
        <h2>How can I help you?</h2>
        <p>Ask me anything — I can search the web, check the time, and query your uploaded documents.</p>
        <div class="welcome-chips">
          <div class="welcome-chip" data-q="What's the latest news today?">📰 Latest news</div>
          <div class="welcome-chip" data-q="What time is it right now?">🕐 Current time</div>
          <div class="welcome-chip" data-q="Summarize my uploaded documents">📄 Summarize docs</div>
          <div class="welcome-chip" data-q="Explain quantum computing simply">🧠 Explain a topic</div>
        </div>
      </div>
    `;
    inner.querySelectorAll('.welcome-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        document.getElementById('message-input').value = chip.dataset.q;
        handleSend();
      });
    });
    return;
  }

  const visibleMessages = messages.filter(m => m.role === 'user' || (m.role === 'assistant' && m.content));
  
  inner.innerHTML = visibleMessages.map(m => `
    <div class="message ${m.role}">
      <div class="avatar">${m.role === 'user' ? '👤' : '⚡'}</div>
      <div class="content">
        <div class="role-label">${m.role === 'user' ? 'You' : 'Assistant'}</div>
        <div class="text">${formatText(m.content)}</div>
      </div>
    </div>
  `).join('');

  scrollToBottom();
}

function showTyping() {
  const inner = document.getElementById('messages-inner');
  const el = document.createElement('div');
  el.className = 'typing-indicator';
  el.id = 'typing';
  el.innerHTML = `
    <div class="avatar">⚡</div>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  `;
  inner.appendChild(el);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById('typing');
  if (el) el.remove();
}

async function handleSend() {
  const input = document.getElementById('message-input');
  const text = input.value.trim();
  if (!text || isLoading) return;

  const model = document.getElementById('model-select').value;

  messages.push({ role: 'user', content: text });
  renderMessages();
  input.value = '';
  input.style.height = 'auto';

  isLoading = true;
  document.getElementById('send-btn').disabled = true;
  showTyping();

  try {
    const res = await sendMessage(model, text, currentChatId);
    hideTyping();

    // Update chat_id from response
    if (res.chat_id) {
      const isNew = !currentChatId;
      currentChatId = res.chat_id;
      if (isNew) {
        // Add to sidebar
        chatHistory.unshift({ chat_id: res.chat_id, title: text.substring(0, 50) });
        renderChatList();
      }
    }

    // Extract assistant message
    const assistantContent = res.message?.content || res.content || JSON.stringify(res.message);
    messages.push({ role: 'assistant', content: assistantContent });
    renderMessages();
  } catch (err) {
    hideTyping();
    messages.push({ role: 'assistant', content: `❌ Error: ${err.message}` });
    renderMessages();
    showToast(err.message, 'error');
  } finally {
    isLoading = false;
    document.getElementById('send-btn').disabled = false;
    document.getElementById('message-input').focus();
  }
}

function showUploadModal() {
  let selectedFile = null;

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'upload-modal';
  overlay.innerHTML = `
    <div class="modal">
      <h3>Upload to Knowledge Store</h3>
      <p class="modal-desc">Upload a file (.txt, .pdf, .md, .docx) to enhance the AI's knowledge.</p>
      <div class="drop-zone" id="drop-zone">
        <div class="drop-icon">📁</div>
        <div>Click or drag a file here</div>
      </div>
      <div class="file-info" id="file-info" style="display:none;"></div>
      <input type="file" id="file-input" accept=".txt,.pdf,.md,.docx" style="display:none;" />
      <div class="modal-actions">
        <button class="btn-cancel" id="modal-cancel">Cancel</button>
        <button class="btn-upload" id="modal-upload" disabled>Upload</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const fileInfo = document.getElementById('file-info');

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length) selectFile(e.dataTransfer.files[0]);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) selectFile(fileInput.files[0]);
  });

  function selectFile(file) {
    selectedFile = file;
    fileInfo.style.display = 'flex';
    fileInfo.innerHTML = `📄 ${escapeHtml(file.name)} <span style="color:var(--text-muted);margin-left:auto;">${(file.size / 1024).toFixed(1)} KB</span>`;
    document.getElementById('modal-upload').disabled = false;
  }

  document.getElementById('modal-cancel').addEventListener('click', () => overlay.remove());
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });

  document.getElementById('modal-upload').addEventListener('click', async () => {
    if (!selectedFile) return;
    const btn = document.getElementById('modal-upload');
    btn.disabled = true;
    btn.textContent = 'Uploading...';
    try {
      await uploadFile(selectedFile);
      showToast('File uploaded successfully!', 'success');
      overlay.remove();
    } catch (err) {
      showToast('Upload failed: ' + err.message, 'error');
      btn.disabled = false;
      btn.textContent = 'Upload';
    }
  });
}

// ===== Utilities =====

function formatText(text) {
  if (!text) return '';
  // Basic markdown: code blocks, inline code, bold, italic, line breaks
  let html = escapeHtml(text);
  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  return html;
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function scrollToBottom() {
  const container = document.getElementById('messages-container');
  requestAnimationFrame(() => {
    container.scrollTop = container.scrollHeight;
  });
}

function showToast(msg, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    toast.style.transition = '0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
