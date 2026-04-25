import os
import requests
from dotenv import load_dotenv

url = "https://fmcxwoqvxatbrawwtqke.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtY3h3b3F2eGF0YnJhd3d0cWtlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3MjE5MjcsImV4cCI6MjA5MDI5NzkyN30.yHThxpyDnVEgZ3dpI5WD4qBgIJE7PHITuJYeapLSVi8"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Obtener todas las instituciones activas para registrarles las reglas "globales"
res_inst = requests.get(f"{url}/rest/v1/institutions?select=id", headers=headers)
if res_inst.status_code == 200:
    institutions = [i['id'] for i in res_inst.json()]
    
    legacy_patterns = [
        r'/noticias/', r'/blog/', r'/eventos/', r'/medios/', r'/prensa/',
        r'\.pdf$', r'\.jpg$', r'\.png$', r'\.xls', r'\.doc'
    ]
    
    print("--- Migrando Hardcoded Blacklist a crawler_exclusions ---")
    count = 0
    for inst_id in institutions:
        for pat in legacy_patterns:
            # Limpiamos un poco el regex básico para que el 'ilike' de Supabase lo entienda mejor
            # o simplemente lo guardamos como patrón de texto. El harvester actual compila la regla con `re.search`
            # así que podemos guardar el regex crudo.
            payload = {
                "institution_id": inst_id,
                "pattern": pat,
                "reason": "Migrado de blacklist_patterns (Código Legacy)"
            }
            res = requests.post(f"{url}/rest/v1/crawler_exclusions", headers=headers, json=payload)
            if res.status_code in [200, 201]:
                count += 1
    print(f"✅ Se registraron {count} reglas de exclusión en la base de datos.")
else:
    print(f"❌ Error obteniendo instituciones: {res_inst.status_code}")
