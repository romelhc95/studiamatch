import os
import requests
import re
from dotenv import load_dotenv

load_dotenv(".env.local")
url = os.getenv("SUPABASE_URL", os.getenv("SUPABASE_URL"))
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
inst_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"
CURRENT_YEAR = 2026

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

patrones = ["agradecimiento", "/publicaciones/"]

print(f"--- Saneamiento U. Lima Fase 2 (Incluye Regla de Fechas) ---")

# 1. Nuevas exclusiones
for p in patrones:
    requests.post(f"{url}/rest/v1/crawler_exclusions", headers=headers, json={"institution_id": inst_id, "pattern": p})

# 2. Limpieza masiva por tablas
for table in ["courses", "enriched_programs", "cleansed_programs", "staging_raw"]:
    eliminados_p = 0
    eliminados_f = 0
    
    # Por patrones
    for p in patrones:
        clean_p = p.replace("/", "")
        res = requests.delete(f"{url}/rest/v1/{table}?institution_id=eq.{inst_id}&url=ilike.*{clean_p}*", headers=headers)
        if res.status_code in [200, 204]:
            eliminados_p += len(res.json()) if res.content else 0
            
    # Por regla de fecha obsoleta (< 2026)
    # Obtenemos todos los restantes para procesar localmente el regex
    res_all = requests.get(f"{url}/rest/v1/{table}?institution_id=eq.{inst_id}&select=id,url", headers=headers)
    if res_all.status_code == 200:
        for r in res_all.json():
            # Buscar años de 4 dígitos entre 2000 y 2025
            found_years = re.findall(r'20[0-2][0-9]', r['url'])
            is_obsolete = False
            for y in found_years:
                if int(y) < CURRENT_YEAR:
                    is_obsolete = True
                    break
            
            if is_obsolete:
                requests.delete(f"{url}/rest/v1/{table}?id=eq.{r['id']}", headers=headers)
                eliminados_f += 1
                
    print(f"TABLA {table.ljust(18)}: {eliminados_p} (Patrones) | {eliminados_f} (Fechas < 2026)")

# 3. Investigar Duplicado Específico
print(f"\n--- Investigando Duplicados: architecture-and-design-culture ---")
res_dup = requests.get(f"{url}/rest/v1/courses?slug=eq.architecture-and-design-culture&select=id,name,url", headers=headers)
if res_dup.status_code == 200:
    dups = res_dup.json()
    if len(dups) > 1:
        print(f"Detectados {len(dups)} duplicados. Eliminando sobrantes...")
        # Mantener el primero, borrar el resto
        for d in dups[1:]:
            requests.delete(f"{url}/rest/v1/courses?id=eq.{d['id']}", headers=headers)
            print(f"🗑️ Eliminado duplicado ID: {d['id']} | URL: {d['url']}")
    else:
        print("No se encontraron duplicados del slug solicitado en la tabla final.")

# Conteo final
res_c = requests.get(f"{url}/rest/v1/courses?institution_id=eq.{inst_id}&select=count", headers={"apikey": key, "Authorization": f"Bearer {key}", "Prefer": "count=exact"})
print(f"\n--- RESULTADO FINAL: {res_c.json()} registros restantes en U. Lima ---")
