"""
Fix navigation on all NOUKOU pages:
1. Fix top nav: proper links for each page
2. Add bottom mobile nav with profile.html for protected pages
3. Add logout button on protected pages
"""

BOTTOM_NAV_PROTECTED = """
<!-- BottomNavBar Mobile -->
<nav class="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-6 pt-3 bg-white/90 backdrop-blur-xl border-t border-gray-200/50 shadow-lg rounded-t-3xl">
  <a class="flex flex-col items-center text-gray-400 hover:text-[#012d1d] transition-colors" href="index.html">
    <span class="material-symbols-outlined">home</span>
    <span class="text-[11px] font-semibold mt-1">Accueil</span>
  </a>
  <a class="flex flex-col items-center text-gray-400 hover:text-[#012d1d] transition-colors" href="analyse.html">
    <span class="material-symbols-outlined">query_stats</span>
    <span class="text-[11px] font-semibold mt-1">Analyser</span>
  </a>
  <a class="flex flex-col items-center text-gray-400 hover:text-[#012d1d] transition-colors" href="dashboard.html">
    <span class="material-symbols-outlined">dashboard</span>
    <span class="text-[11px] font-semibold mt-1">Tableau</span>
  </a>
  <a class="flex flex-col items-center text-gray-400 hover:text-[#012d1d] transition-colors" href="rapport.html">
    <span class="material-symbols-outlined">layers</span>
    <span class="text-[11px] font-semibold mt-1">Projets</span>
  </a>
  <a class="flex flex-col items-center text-gray-400 hover:text-[#012d1d] transition-colors" href="profile.html">
    <span class="material-symbols-outlined">person</span>
    <span class="text-[11px] font-semibold mt-1">Profil</span>
  </a>
</nav>"""

TOP_NAV_PROTECTED = """<!-- TopAppBar -->
<header class="bg-[#012d1d] flex justify-between items-center w-full px-6 py-4 h-20 fixed top-0 z-50">
  <a href="index.html" class="flex items-center gap-3">
    <img src="img/logo.png" alt="NOUKOU Logo" class="h-12 w-auto object-contain"/>
  </a>
  <nav class="hidden md:flex gap-6 items-center">
    <a class="text-white/70 hover:text-white font-medium text-sm transition-colors px-3 py-2 rounded-lg hover:bg-white/10" href="index.html">Accueil</a>
    <a class="text-white/70 hover:text-white font-medium text-sm transition-colors px-3 py-2 rounded-lg hover:bg-white/10" href="analyse.html">Analyser</a>
    <a class="text-white/70 hover:text-white font-medium text-sm transition-colors px-3 py-2 rounded-lg hover:bg-white/10" href="dashboard.html">Tableau</a>
    <a class="text-white/70 hover:text-white font-medium text-sm transition-colors px-3 py-2 rounded-lg hover:bg-white/10" href="rapport.html">Projets</a>
    <a class="text-white/70 hover:text-white font-medium text-sm transition-colors px-3 py-2 rounded-lg hover:bg-white/10" href="profile.html">Mon Profil</a>
    <button onclick="logout()" class="flex items-center gap-1 text-sm font-semibold text-white bg-red-700/30 hover:bg-red-700/60 px-4 py-2 rounded-lg transition-colors border border-red-500/30">
      <span class="material-symbols-outlined text-base">logout</span> Déconnexion
    </button>
  </nav>
  <a href="profile.html" class="md:hidden flex items-center justify-center w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
    <span class="material-symbols-outlined text-white">person</span>
  </a>
</header>"""

import re

def replace_header(content, new_header):
    """Replace everything between <!-- TopAppBar --> and </header>"""
    pattern = r'<!--\s*TopAppBar\s*-->.*?</header>'
    if re.search(pattern, content, re.DOTALL):
        return re.sub(pattern, new_header.strip(), content, flags=re.DOTALL)
    return content

def replace_or_add_bottom_nav(content, new_nav):
    """Replace existing bottom nav or add before </body>"""
    pattern = r'<!--\s*BottomNavBar[^>]*-->.*?</nav>'
    if re.search(pattern, content, re.DOTALL):
        return re.sub(pattern, new_nav.strip(), content, flags=re.DOTALL)
    # No existing bottom nav — add before </body>
    return content.replace('</body>', new_nav + '\n</body>')

pages = ['dashboard.html', 'analyse.html', 'rapport.html']

for page in pages:
    try:
        with open(page, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print('NOT FOUND:', page)
        continue

    content = replace_header(content, TOP_NAV_PROTECTED)
    content = replace_or_add_bottom_nav(content, BOTTOM_NAV_PROTECTED)

    with open(page, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed:', page)

print('Done.')
