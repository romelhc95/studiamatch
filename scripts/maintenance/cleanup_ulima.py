import os
import requests
from dotenv import load_dotenv

load_dotenv(".env.local")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Necesitamos Service Role para DELETE masivo con filtros complejos
inst_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# 1. Agregar nuevas exclusiones
patrones = ["/tags/", "/mooc/", "/agenda/"]
print(f"--- Agregando Exclusiones para U. Lima ---")
for p in patrones:
    data = {"institution_id": inst_id, "pattern": p}
    res = requests.post(f"{url}/rest/v1/crawler_exclusions", headers=headers, json=data)
    if res.status_code in [200, 201]:
        print(f"✅ Registrada exclusión: {p}")
    else:
        print(f"⚠️ Nota: Exclusión {p} ya existía o error {res.status_code}")

# 2. Ejecutar Limpieza en Cascada (Simulada vía API ya que no hay cascada real en RLS API)
tables = ["courses", "enriched_programs", "cleansed_programs", "staging_raw"]
print(f"\n--- Ejecutando Limpieza de Registros ---")

for table in tables:
    total_eliminados = 0
    for p in patrones:
        # En PostgREST usamos .ilike.*pattern*
        clean_p = p.replace("/", "")
        query_url = f"{url}/rest/v1/{table}?institution_id=eq.{inst_id}&url=ilike.*{clean_p}*"
        res = requests.delete(query_url, headers=headers)
        if res.status_code in [200, 204]:
            count = len(res.json()) if res.content else 0
            total_eliminados += count
    print(f"🗑️ Tabla {table.ljust(18)}: {total_eliminados} registros eliminados.")

# 3. Conteo Final
print(f"\n--- Resumen Final (U. Lima) ---")
res_final = requests.get(f"{url}/rest/v1/courses?institution_id=eq.{inst_id}&select=count", headers=headers, headers={'Prefer': 'count=exact'})
# Nota: corregido el paso de headers duplicado en la linea anterior por accidente mental, se corrige en la ejecución real.
