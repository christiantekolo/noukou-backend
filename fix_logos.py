import os
import re

files_to_fix = ['index.html', 'dashboard.html', 'analyse.html', 'rapport.html', 'login.html', 'register.html']

fallback_html_white_text = """
<div class="brand flex items-center gap-3 group decoration-none">
  <img src="img/logo.png" alt="NOUKOU Logo" class="h-10 w-auto object-contain hidden" onload="this.classList.remove('hidden'); this.nextElementSibling.classList.add('hidden');" onerror="this.classList.add('hidden'); this.nextElementSibling.classList.remove('hidden');" />
  <div class="flex items-center gap-2">
    <div class="relative flex items-center justify-center w-10 h-10 rounded-full bg-white shadow-sm border-2 border-emerald-500 group-hover:scale-105 transition-transform">
      <span class="font-['Manrope'] font-black text-[#012d1d] text-sm tracking-tighter">NK</span>
    </div>
    <span class="font-['Manrope'] font-extrabold tracking-tighter text-white text-2xl group-hover:text-emerald-400 transition-colors">NOUKOU</span>
  </div>
</div>
"""

fallback_html_green_text = """
<div class="mobile-brand flex items-center gap-3 group decoration-none">
  <img src="img/logo.png" alt="NOUKOU Logo" class="h-10 w-auto object-contain hidden" onload="this.classList.remove('hidden'); this.nextElementSibling.classList.add('hidden');" onerror="this.classList.add('hidden'); this.nextElementSibling.classList.remove('hidden');" />
  <div class="flex items-center gap-2">
    <div class="relative flex items-center justify-center w-10 h-10 rounded-full bg-white shadow-sm border-2 border-emerald-500 group-hover:scale-105 transition-transform">
      <span class="font-['Manrope'] font-black text-[#012d1d] text-sm tracking-tighter">NK</span>
    </div>
    <span class="font-['Manrope'] font-extrabold tracking-tighter text-[#012d1d] text-2xl group-hover:text-emerald-600 transition-colors">NOUKOU</span>
  </div>
</div>
"""

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for index, dashboard, analyse, rapport
    pattern1 = r'<img src="img/logo\.png" alt="NOUKOU Logo" class="h-12 w-auto object-contain" />'
    if re.search(pattern1, content):
        content = re.sub(pattern1, fallback_html_white_text.strip().replace('class="brand ', 'class="'), content)
    
    # Pattern for login/register (brand)
    pattern2 = r'<img src="img/logo\.png" alt="NOUKOU Logo" style="height: 48px; width: auto; object-fit: contain;" />'
    
    if 'class="brand"' in content or 'class="mobile-brand"' in content:
        # Actually in login and register, it's wrapped in <a class="brand"> and <a class="mobile-brand">
        # Let's replace the <a class="brand">...</a>
        pattern_brand = r'<a href="index\.html" class="brand">\s*<img src="img/logo\.png"[^>]*>\s*</a>'
        if re.search(pattern_brand, content):
            repl = fallback_html_white_text.strip().replace('<div', '<a href="index.html"').replace('</div>\n</div>', '</div>\n</a>')
            content = re.sub(pattern_brand, repl, content)
            
        pattern_mobile = r'<a href="index\.html" class="mobile-brand">\s*<img src="img/logo\.png"[^>]*>\s*</a>'
        if re.search(pattern_mobile, content):
            repl = fallback_html_green_text.strip().replace('<div', '<a href="index.html"').replace('</div>\n</div>', '</div>\n</a>')
            content = re.sub(pattern_mobile, repl, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Logos fixed.")
