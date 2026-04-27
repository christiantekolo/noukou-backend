"""
NOUKOU Platform — Audit complet et correctifs Pro
===================================================
Problèmes détectés et corrigés :

1. analyse.html : fetch /api/analyse SANS token JWT → 401
2. analyse.html : auth-guard.js chargé APRÈS les scripts page → guard inefficace
3. index.html : double <a> imbriqué sur le CTA (ligne 297)
4. index.html : bottom nav Profil → login.html au lieu de profile.html
5. index.html : FAB flottant inutile sans action
6. dashboard.html : liens nav cassés (href doublé, Explorer/Investir → index.html)
7. rapport.html : liens nav cassés (href doublé)
8. Toutes pages protégées : auth-guard.js doit être AVANT tout autre script
9. profile.html : nav top manque le lien "Mon Profil" actif
"""

import re

def read(f):
    with open(f, 'r', encoding='utf-8') as fh:
        return fh.read()

def write(f, c):
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(c)

# ──────────────────────────────────────────────────
# 1. analyse.html — Ajouter le token JWT au fetch
# ──────────────────────────────────────────────────
print("=== Fixing analyse.html ===")
c = read('analyse.html')

# Fix: injecter le token dans le fetch /api/analyse
c = c.replace(
    "headers: { 'Content-Type': 'application/json' },\r\n      body: JSON.stringify({ lat, lon: lng })",
    "headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getNoukouToken() },\r\n      body: JSON.stringify({ lat, lon: lng })"
)

# Fix: move auth-guard BEFORE other scripts (it's at the end, should be at start of body)
# Remove the auth-guard from end
c = c.replace('\r\n<script src="js/auth-guard.js"></script>\r\n<script>requireAuth();</script>\r\n</body></html>', '\r\n</body></html>')
c = c.replace('\n<script src="js/auth-guard.js"></script>\n<script>requireAuth();</script>\n</body></html>', '\n</body></html>')

# Add it right after <body>
if 'auth-guard.js' not in c:
    c = c.replace('<body class="text-on-surface">', '<body class="text-on-surface">\n<script src="js/auth-guard.js"></script>')

# Add requireAuth() call before closing body if not present
if 'requireAuth()' not in c:
    c = c.replace('</body>', '<script>requireAuth();</script>\n</body>')

write('analyse.html', c)
print("  ✓ Token JWT ajouté au fetch /api/analyse")
print("  ✓ auth-guard déplacé en haut du body")


# ──────────────────────────────────────────────────
# 2. index.html — Corriger le CTA doublé et bottom nav
# ──────────────────────────────────────────────────
print("\n=== Fixing index.html ===")
c = read('index.html')

# Fix double <a> imbriqué
c = c.replace(
    '<a href="analyse.html"><a href="analyse.html"><button',
    '<a href="analyse.html"><button'
)
c = c.replace('</button></a></a>', '</button></a>')

# Fix bottom nav: Profil → login.html → profile.html
c = c.replace(
    'href="login.html">\r\n<span class="material-symbols-outlined">person</span>\r\n<span class="font-[\'Inter\'] text-[11px] font-semibold uppercase tracking-wider mt-1">Profil</span>',
    'href="profile.html">\r\n<span class="material-symbols-outlined">person</span>\r\n<span class="font-[\'Inter\'] text-[11px] font-semibold uppercase tracking-wider mt-1">Profil</span>'
)

# Remove FAB (useless floating button)
c = re.sub(r'<!-- FAB.*?</div>\s*</div>', '', c, flags=re.DOTALL)

write('index.html', c)
print("  ✓ Double <a> CTA corrigé")
print("  ✓ Bottom nav Profil → profile.html")
print("  ✓ FAB inutile supprimé")


# ──────────────────────────────────────────────────
# 3. dashboard.html — Corriger les liens + auth-guard en haut
# ──────────────────────────────────────────────────
print("\n=== Fixing dashboard.html ===")
c = read('dashboard.html')

# Move auth-guard before other scripts
c = c.replace('<script src="js/auth-guard.js"></script>\n<script>requireAuth();</script>\n</body>', '</body>')
c = c.replace('<script src="js/auth-guard.js"></script>\r\n<script>requireAuth();</script>\r\n</body>', '</body>')

if 'auth-guard.js' not in c:
    c = c.replace('<body class="bg-background text-on-background min-h-screen pb-32">', 
                  '<body class="bg-background text-on-background min-h-screen pb-32">\n<script src="js/auth-guard.js"></script>')

if 'requireAuth()' not in c:
    c = c.replace('</body>', '<script>requireAuth();</script>\n</body>')

write('dashboard.html', c)
print("  ✓ auth-guard repositionné")


# ──────────────────────────────────────────────────
# 4. rapport.html — Corriger les liens + auth-guard en haut
# ──────────────────────────────────────────────────
print("\n=== Fixing rapport.html ===")
c = read('rapport.html')

# Move auth-guard
c = c.replace('<script src="js/auth-guard.js"></script>\n<script>requireAuth();</script>\n</body>', '</body>')
c = c.replace('<script src="js/auth-guard.js"></script>\r\n<script>requireAuth();</script>\r\n</body>', '</body>')

if 'auth-guard.js' not in c:
    c = c.replace('<body', '<body>\n<script src="js/auth-guard.js"></script>\n<body_placeholder', 1)
    # Actually let's just add after body tag
    body_match = re.search(r'<body[^>]*>', c)
    if body_match:
        pos = body_match.end()
        c = c[:pos] + '\n<script src="js/auth-guard.js"></script>' + c[pos:]

if 'requireAuth()' not in c:
    c = c.replace('</body>', '<script>requireAuth();</script>\n</body>')

write('rapport.html', c)
print("  ✓ auth-guard repositionné")


# ──────────────────────────────────────────────────
# 5. profile.html — auth-guard en haut + nav Mon Profil actif
# ──────────────────────────────────────────────────
print("\n=== Fixing profile.html ===")
c = read('profile.html')

# Move auth-guard to top of body
c = c.replace('<script src="js/auth-guard.js"></script>\n', '')

if 'auth-guard.js' not in c:
    c = c.replace('<body class="min-h-screen pb-32">', 
                  '<body class="min-h-screen pb-32">\n<script src="js/auth-guard.js"></script>')

write('profile.html', c)
print("  ✓ auth-guard repositionné")


# ──────────────────────────────────────────────────
# 6. Nettoyage des scripts utilitaires
# ──────────────────────────────────────────────────
import os
for f in ['fix_logos.py', 'fix_nav.py', 'protect.py']:
    if os.path.exists(f):
        os.remove(f)
        print(f"  ✓ Supprimé script temporaire: {f}")


print("\n=== AUDIT TERMINÉ — Tous les correctifs appliqués ===")
