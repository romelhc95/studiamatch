import os, re
folder = 'scripts/maintenance'
files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.py')]
for fp in files:
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
        # Sanitize Key
        new_content = re.sub(r'\"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[^\"]+\"', 'os.getenv("SUPABASE_SERVICE_ROLE_KEY")', content)
        # Sanitize URL
        new_content = re.sub(r'\"https://fmcxwoqvxatbrawwtqke\.supabase\.co\"', 'os.getenv("SUPABASE_URL")', new_content)
        
        if content != new_content:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Saneado: {fp}")
    except: pass
print("Proceso de sanitización finalizado.")
