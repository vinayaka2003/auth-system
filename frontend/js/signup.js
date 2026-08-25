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

/* ── Password strength ──────────────────────────────────────── */
function getStrength(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8)        score++;
  if (/[A-Z]/.test(pw))     score++;
  if (/[0-9]/.test(pw))     score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (pw.length < 6)        return 1;
  if (score <= 1)            return 1;
  if (score === 2)           return 2;
  return 3;
}

const labels = ['', 'Weak', 'Fair', 'Strong'];
const labelColors = ['', 'var(--red)', 'var(--yellow)', 'var(--green)'];

function updateStrength(pw) {
  const bar   = document.getElementById('strengthBar');
  const label = document.getElementById('strengthLabel');
  if (!bar || !label) return;

  if (!pw) { bar.style.display = 'none'; label.textContent = ''; return; }

  const s = getStrength(pw);
  bar.style.display = 'flex';
  bar.className = `strength-bar strength-${s}`;
  label.textContent = labels[s];
  label.style.color = labelColors[s];
}

/* ── Live validation ────────────────────────────────────────── */
document.getElementById('name')?.addEventListener('input', e => {
  const v = e.target.value.trim();
  if (v.length < 2)  fieldError('name','nameMsg','Name must be at least 2 characters.');
  else               fieldOk('name','nameMsg');
});

document.getElementById('email')?.addEventListener('blur', e => {
  const v = e.target.value.trim();
  if (!v)                                             fieldReset('email','emailMsg');
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v))   fieldError('email','emailMsg','Enter a valid email address.');
  else                                                fieldOk('email','emailMsg');
});

document.getElementById('password')?.addEventListener('input', e => {
  const v = e.target.value;
  updateStrength(v);
  if (v.length > 0 && v.length < 6)  fieldError('password','pwMsg','Password must be at least 6 characters.');
  else if (v.length >= 6)            fieldOk('password','pwMsg');
  else                               fieldReset('password','pwMsg');
});

/* ── Signup ─────────────────────────────────────────────────── */
async function doSignup() {
  const name     = document.getElementById('name')?.value.trim();
  const email    = document.getElementById('email')?.value.trim();
  const password = document.getElementById('password')?.value;

  let valid = true;
  if (!name || name.length < 2)                       { fieldError('name','nameMsg','Name is required (min 2 chars).'); valid = false; }
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { fieldError('email','emailMsg','Valid email is required.'); valid = false; }
  if (!password || password.length < 6)               { fieldError('password','pwMsg','Password must be at least 6 characters.'); valid = false; }
  if (!valid) return;

  setLoading('signupBtn', true);

  const { ok, data, error } = await api.signup(name, email, password);

  setLoading('signupBtn', false);

  if (ok) {
    showAlert('Account created! Signing you in…', false);
    toast.success('Account created', 'Redirecting to sign in…');
    setTimeout(() => window.location.replace('login.html'), 1400);
  } else {
    showAlert(error, true);
    toast.error('Sign up failed', error);
  }
}

/* ── Google signup ──────────────────────────────────────────── */
async function handleGoogleSignup(response) {
  const { ok, data, error } = await api.googleLogin(response.credential);
  if (ok && data.access_token) {
    api.saveToken(data.access_token, true);
    toast.success('Signed up with Google');
    setTimeout(() => window.location.replace('dashboard.html'), 900);
  } else {
    toast.error('Google sign-up failed', error);
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
  if (e.key === 'Enter') doSignup();
});