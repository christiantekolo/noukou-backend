/**
 * NOUKOU — Guard d'authentification
 * Inclure sur TOUTES les pages protégées (dashboard, analyse, rapport, profile).
 * Si l'utilisateur n'a pas de token, il est redirigé immédiatement vers login.html.
 */

const API_URL = 'https://web-production-11c8c.up.railway.app';

// ── Cache tokens ──────────────────────────────────────────────
function getNoukouToken() {
  return localStorage.getItem('noukou_token') || sessionStorage.getItem('noukou_token') || null;
}

function getNoukouUser() {
  const raw = localStorage.getItem('noukou_user') || sessionStorage.getItem('noukou_user');
  try { return raw ? JSON.parse(raw) : null; } catch { return null; }
}

// ── Déconnexion ────────────────────────────────────────────────
function logout() {
  localStorage.removeItem('noukou_token');
  localStorage.removeItem('noukou_user');
  sessionStorage.removeItem('noukou_token');
  sessionStorage.removeItem('noukou_user');
  window.location.replace('login.html');
}

// ── Redirection immédiate si pas de token ──────────────────────
// (exécuté SYNCHRONEMENT avant tout rendu de la page)
(function immediateGuard() {
  const token = getNoukouToken();
  if (!token) {
    window.location.replace('login.html');
  }
})();

// ── Vérification complète + injection UI ──────────────────────
async function requireAuth(onReady) {
  const token = getNoukouToken();
  if (!token) {
    window.location.replace('login.html');
    return;
  }

  try {
    const res = await fetch(`${API_URL}/api/auth/me`, {
      headers: { 'Authorization': 'Bearer ' + token }
    });

    if (!res.ok) {
      logout();
      return;
    }

    const data = await res.json();
    const user = data.user;

    // Rafraîchir le cache local
    const storage = localStorage.getItem('noukou_token') ? localStorage : sessionStorage;
    storage.setItem('noukou_user', JSON.stringify(user));

    injectUserUI(user);

    if (typeof onReady === 'function') onReady(user);

  } catch (err) {
    // Erreur réseau — utiliser le cache local plutôt que déconnecter
    const cachedUser = getNoukouUser();
    if (cachedUser) {
      injectUserUI(cachedUser);
      if (typeof onReady === 'function') onReady(cachedUser);
    } else {
      logout();
    }
  }
}

// ── Injection du nom/avatar dans l'UI ─────────────────────────
function injectUserUI(user) {
  if (!user) return;

  document.querySelectorAll('[data-user-name]').forEach(el => {
    el.textContent = user.name || user.email || 'Mon compte';
  });

  const initials = (user.name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  document.querySelectorAll('[data-user-initials]').forEach(el => {
    el.textContent = initials;
  });

  if (user.photo_url) {
    const src = user.photo_url.startsWith('http')
      ? user.photo_url
      : API_URL + user.photo_url;
    document.querySelectorAll('[data-user-avatar]').forEach(el => {
      el.src = src;
      el.classList.remove('hidden');
      const sib = el.nextElementSibling;
      if (sib) sib.classList.add('hidden');
    });
  }
}
