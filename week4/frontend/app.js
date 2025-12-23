// Theme Management
const THEME_STORAGE_KEY = 'theme-preference';

function getPreferredTheme() {
  // Check localStorage first
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored) {
    return stored;
  }

  // Fall back to system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }

  return 'light';
}

function setTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark-mode');
  } else {
    document.documentElement.classList.remove('dark-mode');
  }

  localStorage.setItem(THEME_STORAGE_KEY, theme);
  updateThemeIcon(theme === 'dark');
  updateThemeButtonLabel(theme);
}

function updateThemeIcon(isDark) {
  const sunIcon = document.querySelector('.sun-icon');
  const moonIcon = document.querySelector('.moon-icon');

  if (sunIcon && moonIcon) {
    sunIcon.style.display = isDark ? 'none' : 'block';
    moonIcon.style.display = isDark ? 'block' : 'none';
  }
}

function updateThemeButtonLabel(theme) {
  const button = document.getElementById('theme-toggle');
  if (button) {
    const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    button.setAttribute('aria-label', label);
    button.setAttribute('title', label);
  }
}

function toggleTheme() {
  const isDarkMode = document.documentElement.classList.contains('dark-mode');
  const newTheme = isDarkMode ? 'light' : 'dark';
  setTheme(newTheme);
}

// Initialize theme immediately (before DOMContentLoaded)
setTheme(getPreferredTheme());

// State management
let currentUser = null;

// Tab switching functions
window.switchToLogin = function() {
  document.getElementById('login-view').style.display = 'block';
  document.getElementById('register-view').style.display = 'none';
  document.getElementById('login-tab').classList.add('active');
  document.getElementById('register-tab').classList.remove('active');
};

window.switchToRegister = function() {
  document.getElementById('login-view').style.display = 'none';
  document.getElementById('register-view').style.display = 'block';
  document.getElementById('login-tab').classList.remove('active');
  document.getElementById('register-tab').classList.add('active');
};

async function fetchJSON(url, options = {}) {
  // Always include credentials to send cookies
  const res = await fetch(url, { ...options, credentials: 'same-origin' });
  if (!res.ok) {
    if (res.status === 401) {
      // Unauthorized - redirect to login
      showAuthSection();
      throw new Error('Unauthorized');
    }
    throw new Error(await res.text());
  }
  return res.json();
}

function showAuthSection() {
  document.getElementById('auth-section').style.display = 'block';
  document.getElementById('app-section').style.display = 'none';
  currentUser = null;
}

function showAppSection(username) {
  document.getElementById('auth-section').style.display = 'none';
  document.getElementById('app-section').style.display = 'block';
  document.getElementById('current-user').textContent = username;
  currentUser = username;
  loadNotes();
  loadActions();
}

async function checkAuth() {
  try {
    const user = await fetchJSON('/auth/me');
    showAppSection(user.username);
  } catch (err) {
    showAuthSection();
  }
}

async function loadNotes() {
  const list = document.getElementById('notes');
  list.innerHTML = '';
  try {
    const notes = await fetchJSON('/notes/');
    for (const n of notes) {
      const li = document.createElement('li');
      li.textContent = `${n.title}: ${n.content}`;
      list.appendChild(li);
    }
  } catch (err) {
    console.error('Error loading notes:', err);
  }
}

async function loadActions() {
  const list = document.getElementById('actions');
  list.innerHTML = '';
  try {
    const items = await fetchJSON('/action-items/');
    for (const a of items) {
      const li = document.createElement('li');
      li.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
      if (!a.completed) {
        const btn = document.createElement('button');
        btn.textContent = 'Complete';
        btn.onclick = async () => {
          await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
          loadActions();
        };
        li.appendChild(btn);
      }
      list.appendChild(li);
    }
  } catch (err) {
    console.error('Error loading actions:', err);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  // Theme toggle button
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);

    // Keyboard accessibility (Enter and Space keys)
    themeToggle.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleTheme();
      }
    });
  }

  // Listen for system theme changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      // Only auto-update if user hasn't set explicit preference
      if (!localStorage.getItem(THEME_STORAGE_KEY)) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  // Auth tab switching
  document.getElementById('login-tab').addEventListener('click', () => {
    document.getElementById('login-view').style.display = 'block';
    document.getElementById('register-view').style.display = 'none';
    document.getElementById('login-tab').classList.add('active');
    document.getElementById('register-tab').classList.remove('active');
  });

  document.getElementById('register-tab').addEventListener('click', () => {
    document.getElementById('login-view').style.display = 'none';
    document.getElementById('register-view').style.display = 'block';
    document.getElementById('login-tab').classList.remove('active');
    document.getElementById('register-tab').classList.add('active');
  });

  // Login form
  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const result = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
        credentials: 'same-origin',
      });

      if (!result.ok) {
        throw new Error('Login failed');
      }

      const data = await result.json();
      e.target.reset();
      showAppSection(data.username);
    } catch (err) {
      alert('Login failed: ' + err.message);
    }
  });

  // Register form
  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;

    try {
      await fetchJSON('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      e.target.reset();
      alert('Registration successful! Please login.');
    } catch (err) {
      alert('Registration failed: ' + err.message);
    }
  });

  // Logout button
  document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
      await fetchJSON('/auth/logout', { method: 'POST' });
      showAuthSection();
    } catch (err) {
      console.error('Logout error:', err);
    }
  });

  // Note form
  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    await fetchJSON('/notes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    e.target.reset();
    loadNotes();
  });

  document.getElementById('note-clear').addEventListener('click', () => {
    document.getElementById('note-form').reset();
  });

  // Action form
  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    loadActions();
  });

  document.getElementById('action-clear').addEventListener('click', () => {
    document.getElementById('action-form').reset();
  });

  // Check auth status on page load
  checkAuth();
});
