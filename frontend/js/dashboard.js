/* ── Dashboard ──────────────────────────────────────────────── */

const isGuest = localStorage.getItem('guest') === 'true';

if (isGuest) {
  renderGuest();
} else if (!api.getToken()) {
  window.location.replace('login.html');
} else {
  loadUser();
}

function renderGuest() {
  setGreeting('Welcome, Guest', 'You are browsing as a guest.');
  setAvatar('G');
  fillCards({
    email:    '—',
    verified: badge('Not verified', 'badge-red'),
    provider: badge('Guest', 'badge-blue'),
    status:   badge('Active', 'badge-green'),
  });
}

async function loadUser() {
  const { ok, data, error } = await api.me();

  if (!ok) {
    api.clearToken();
    window.location.replace('login.html');
    return;
  }

  const initials = (data.name || '?').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
  setAvatar(initials);
  setGreeting(`Welcome back, ${data.name}`, 'Here is your account at a glance.');

  fillCards({
    email:    data.email || '—',
    verified: data.verified
      ? badge('Verified', 'badge-green')
      : badge('Unverified', 'badge-red'),
    provider: badge(capitalize(data.auth_provider || 'email'), 'badge-blue'),
    status:   badge('Active', 'badge-green'),
  });
}

function setGreeting(title, sub) {
  document.getElementById('welcomeMsg').textContent = title;
  document.getElementById('welcomeSub').textContent = sub;
}

function setAvatar(text) {
  const el = document.getElementById('navAvatar');
  if (el) el.textContent = text;
}

function fillCards({ email, verified, provider, status }) {
  set('infoEmail',    email,    'cardEmail');
  setHtml('infoVerified', verified, 'cardVerified');
  setHtml('infoProvider', provider, 'cardProvider');
  setHtml('infoStatus',   status,   'cardStatus');
}

function set(id, value, cardId) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
  removeSkeleton(cardId);
}

function setHtml(id, html, cardId) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
  removeSkeleton(cardId);
}

function removeSkeleton(cardId) {
  const card = document.getElementById(cardId);
  if (card) card.classList.remove('skeleton');
}

function badge(label, cls) {
  return `<span class="badge ${cls}">${label}</span>`;
}

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : '—';
}

function logout() {
  api.clearToken();
  window.location.replace('login.html');
}