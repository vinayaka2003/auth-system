/* ── Forgot password ────────────────────────────────────────── */

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

/* ── Forgot ──────────────────────────────────────────────────── */
async function doForgot() {
  const email = document.getElementById('email')?.value.trim();

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    fieldError('email', 'emailMsg', 'Enter a valid email address.');
    return;
  }

  setLoading('resetBtn', true);

  const { ok, error } = await api.forgotPw(email);

  setLoading('resetBtn', false);

  if (ok) {
    showAlert('If that email is registered, a reset link has been sent.', false);
    toast.success('Email sent', 'Check your inbox for the reset link.');
    document.getElementById('email').value = '';
  } else {
    // Show generic message to avoid user enumeration
    showAlert('If that email is registered, a reset link has been sent.', false);
    toast.info('Reset requested', 'Check your inbox.');
  }
}

document.addEventListener('keydown', e => { if (e.key === 'Enter') doForgot(); });