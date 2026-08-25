/* ── Utilities ─────────────────────────────────────────────── */

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle('loading', loading);
}

function showAlert(msg, isError) {
  const el = document.getElementById('statusAlert');
  if (!el) return;
  el.textContent = msg;
  el.className = 'alert ' + (isError ? 'error' : 'success');
}

function fieldError(inputId, msgId, msg) {
  const input = document.getElementById(inputId);
  const msgEl = document.getElementById(msgId);
  if (input) { input.classList.remove('valid'); input.classList.add('invalid'); }
  if (msgEl) { msgEl.textContent = msg; msgEl.className = 'field-msg err'; }
}

function fieldOk(inputId, msgId, msg = '') {
  const input = document.getElementById(inputId);
  const msgEl = document.getElementById(msgId);
  if (input) { input.classList.remove('invalid'); input.classList.add('valid'); }
  if (msgEl) { msgEl.textContent = msg; msgEl.className = 'field-msg ok'; }
}

function fieldReset(inputId, msgId) {
  const input = document.getElementById(inputId);
  const msgEl = document.getElementById(msgId);
  if (input) { input.classList.remove('valid','invalid'); }
  if (msgEl) { msgEl.textContent = ''; msgEl.className = 'field-msg'; }
}

function togglePw(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (!input) return;
  const show = input.type === 'password';
  input.type = show ? 'text' : 'password';
  if (icon) { icon.setAttribute('data-lucide', show ? 'eye-off' : 'eye'); lucide.createIcons(); }
}

/* ── Auto-redirect if already logged in ────────────────────── */
if (api.isLoggedIn()) window.location.replace('dashboard.html');

/* ── Live validation ────────────────────────────────────────── */
const emailInput = document.getElementById('email');
const pwInput    = document.getElementById('password');

emailInput?.addEventListener('blur', () => {
  const v = emailInput.value.trim();
  if (!v)                         fieldReset('email','emailMsg');
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) fieldError('email','emailMsg','Enter a valid email address.');
  else                            fieldOk('email','emailMsg');
});

pwInput?.addEventListener('blur', () => {
  const v = pwInput.value;
  if (!v)           fieldReset('password','pwMsg');
  else if (v.length < 6) fieldError('password','pwMsg','Password must be at least 6 characters.');
  else              fieldOk('password','pwMsg');
});

/* ── Login ─────────────────────────────────────────────────── */
async function doLogin() {
  const email    = document.getElementById('email')?.value.trim();
  const password = document.getElementById('password')?.value;
  const remember = document.getElementById('rememberMe')?.checked;

  let valid = true;
  if (!email)    { fieldError('email','emailMsg','Email is required.'); valid = false; }
  if (!password) { fieldError('password','pwMsg','Password is required.'); valid = false; }
  if (!valid) return;

  setLoading('loginBtn', true);

  const { ok, data, error } = await api.login(email, password);

  setLoading('loginBtn', false);

  if (ok && data.access_token) {
    api.saveToken(data.access_token, remember);
    toast.success('Signed in', 'Redirecting to your dashboard…');
    setTimeout(() => window.location.replace('dashboard.html'), 900);
  } else {
    showAlert(error, true);
    toast.error('Sign in failed', error);
  }
}

/* ── Google login ───────────────────────────────────────────── */
async function handleGoogleLogin(response) {
  const { ok, data, error } = await api.googleLogin(response.credential);
  if (ok && data.access_token) {
    api.saveToken(data.access_token, true);
    toast.success('Signed in with Google');
    setTimeout(() => window.location.replace('dashboard.html'), 900);
  } else {
    toast.error('Google sign-in failed', error);
  }
}

/* ── Guest ──────────────────────────────────────────────────── */
function guestLogin() {
  api.clearToken();
  localStorage.setItem('guest', 'true');
  window.location.replace('dashboard.html');
}

/* ── Enter key ──────────────────────────────────────────────── */
document.addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});