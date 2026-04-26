import os, re
files = ['scripts/maintenance/cleanup_ulima_noise_specific.py', 'scripts/maintenance/migrate_dev_to_prod.py', 'scripts/maintenance/migrate_blacklist.py']
for fp in files:
    if not os.path.exists(fp): continue
    with open(fp, 'r', encoding='utf-8') as f: content = f.read()
    # Sanitize Key
    content = re.sub(r'\"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[^\"]+\"', 'os.getenv("SUPABASE_SERVICE_ROLE_KEY")', content)
    # Sanitize URL
    content = re.sub(r'\"https://fmcxwoqvxatbrawwtqke\.supabase\.co\"', 'os.getenv("SUPABASE_URL")', content)
    with open(fp, 'w', encoding='utf-8') as f: f.write(content)
print("Sanitization complete.")
