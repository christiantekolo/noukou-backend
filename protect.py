pages = ['dashboard.html', 'analyse.html', 'rapport.html']
for page in pages:
    with open(page, 'r', encoding='utf-8') as f:
        content = f.read()
    guard = '<script src="js/auth-guard.js"></script>\n<script>requireAuth();</script>\n</body>'
    if 'auth-guard.js' not in content:
        content = content.replace('</body>', guard)
        with open(page, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Protected:', page)
    else:
        print('Already protected:', page)
print('Done.')
