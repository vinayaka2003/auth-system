/* ── Toast notification system ─────────────────────────────── */

const toast = (() => {
  let container;

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  function show(type, title, message, duration = 4000) {
    const icons = { success: '✓', error: '✕', info: 'i' };
    const c = getContainer();

    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `
      <div class="toast-icon">${icons[type] || 'i'}</div>
      <div class="toast-body">
        <div class="toast-title">${title}</div>
        ${message ? `<div class="toast-msg">${message}</div>` : ''}
      </div>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;

    el.querySelector('.toast-close').addEventListener('click', () => dismiss(el));
    c.appendChild(el);

    const timer = setTimeout(() => dismiss(el), duration);
    el._timer = timer;
    return el;
  }

  function dismiss(el) {
    clearTimeout(el._timer);
    el.classList.add('hiding');
    el.addEventListener('transitionend', () => el.remove(), { once: true });
    // fallback in case transition doesn't fire
    setTimeout(() => el.remove(), 400);
  }

  return {
    success: (title, msg)  => show('success', title, msg),
    error:   (title, msg)  => show('error',   title, msg),
    info:    (title, msg)  => show('info',    title, msg),
  };
})();
