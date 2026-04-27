/**
 * NOUKOU — Guard d'authentification
 * À inclure sur TOUTES les pages protégées (dashboard, analyse, rapport).
 * Si l'utilisateur n'a pas de token valide, il est redirigé vers login.html.
 */

const API_URL = 'https://web-production-11c8c.up.railway.app';

/**
 * Retourne le token stocké (localStorage ou sessionStorage) ou null.
 */
function getNoukoуToken() {
  return localStorage.getItem('noukou_token') || sessionStorage.getItem('noukou_token') || null;
}

/**
 * Retourne l'objet user sérialisé ou null.
 */
function getNoukoуUser() {
  const raw = localStorage.getItem('noukou_user') || sessionStorage.getItem('noukou_user');
  try { return raw ? JSON.parse(raw) : null; } catch { return null; }
}

/**
 * Déconnecte l'utilisateur et redirige vers login.
 */
function logout() {
  localStorage.removeItem('noukou_token');
  localStorage.removeItem('noukou_user');
  sessionStorage.removeItem('noukou_token');
  sessionStorage.removeItem('noukou_user');
  window.location.href = 'login.html';
}

/**
 * Vérifie l'auth ET rafraîchit le profil depuis l'API.
 * Redirige vers login.html si non authentifié.
 * @param {Function} [onReady] callback(user) appelé après vérification
 */
async function requireAuth(onReady) {
  const token = getNoukoуToken();
  if (!token) {
    window.location.href = 'login.html';
    return;
  }

  try {
    const res = await fetch(`${API_URL}/api/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!res.ok) {
      // Token expiré ou invalide
      logout();
      return;
    }

    const data = await res.json();
    const user = data.user;

    // Rafraîchir le cache local
    const storage = localStorage.getItem('noukou_token') ? localStorage : sessionStorage;
    storage.setItem('noukou_user', JSON.stringify(user));

    // Injecter le nom et la photo dans l'UI si présents
    injectUserUI(user);

    if (typeof onReady === 'function') onReady(user);

  } catch (err) {
    // Erreur réseau : on garde le cache local sans bloquer
    const cachedUser = getNoukoуUser();
    if (cachedUser) {
      injectUserUI(cachedUser);
      if (typeof onReady === 'function') onReady(cachedUser);
    } else {
      logout();
    }
  }
}

/**
 * Injecte le nom et la photo de l'utilisateur dans les éléments
 * portant les data-attributes data-user-name et data-user-avatar.
 */
function injectUserUI(user) {
  if (!user) return;

  // Nom d'affichage
  document.querySelectorAll('[data-user-name]').forEach(el => {
    el.textContent = user.name || user.email || 'Mon compte';
  });

  // Initiales dans les avatars texte
  const initials = (user.name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  document.querySelectorAll('[data-user-initials]').forEach(el => {
    el.textContent = initials;
  });

  // Photo de profil
  if (user.photo_url) {
    const photoSrc = user.photo_url.startsWith('http')
      ? user.photo_url
      : `${API_URL}${user.photo_url}`;
    document.querySelectorAll('[data-user-avatar]').forEach(el => {
      el.src = photoSrc;
      el.classList.remove('hidden');
      el.nextElementSibling?.classList.add('hidden'); // cache l'avatar initiales
    });
  }
}
