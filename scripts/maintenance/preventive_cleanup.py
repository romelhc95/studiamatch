import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(".env.local")
url = os.getenv("SUPABASE_URL", os.getenv("SUPABASE_URL"))
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

inst_ids = [
    "ccd04100-1bde-427b-b94f-ab24ae233a2a", # U. Lima
    "cf64d254-733d-4a92-8a2d-5df5b9dc80ac", # U. Pacífico
    "c64123d6-f00e-4c89-86a8-7706845c0483", # DMC
    "2aa0d175-bfbd-46d0-b84c-14083d2336b0", # IDAT
    "24cc140d-de25-4ef1-9316-b897b451be50"  # New Horizons
]

global_patterns = [
    "/category/", "/author/", "/tag/", "/archive/", 
    "politicas-de-privacidad", "terminos-y-condiciones", "libro-de-reclamaciones",
    "/transparencia/", "/empleabilidad/"
]

print("--- 1. Registrando Exclusiones Preventivas ---")
for i_id in inst_ids:
    for pat in global_patterns:
        res = requests.post(f"{url}/rest/v1/crawler_exclusions", headers=headers, json={
            "institution_id": i_id,
            "pattern": pat,
            "reason": "Patrón de ruido preventivo / Página de servicio"
        })
        if res.status_code in [200, 201]:
            print(f"✅ Exclusión registrada: {pat} para {i_id[:8]}")

print("\n--- 2. Saneando Duplicados por Trailing Slash (/) ---")
# Obtenemos todos los cursos
res_courses = requests.get(f"{url}/rest/v1/courses?select=id,url,institution_id", headers=headers)
if res_courses.status_code == 200:
    courses = res_courses.json()
    url_map = {} # (inst_id, clean_url) -> [ids]
    
    for c in courses:
        clean_url = c['url'].rstrip('/')
        key_tuple = (c['institution_id'], clean_url)
        if key_tuple not in url_map:
            url_map[key_tuple] = []
        url_map[key_tuple].append(c)
    
    deleted_count = 0
    for key_tuple, records in url_map.items():
        if len(records) > 1:
            # Tenemos duplicados (con y sin /)
            # Priorizamos el que NO termina en / o simplemente el primero
            print(f"🔍 Duplicado detectado: {key_tuple[1]}")
            # Mantener el primero, borrar el resto
            to_keep = records[0]
            for to_delete in records[1:]:
                del_res = requests.delete(f"{url}/rest/v1/courses?id=eq.{to_delete['id']}", headers=headers)
                if del_res.status_code in [200, 204]:
                    deleted_count += 1
                    print(f"  🗑️ Borrado ID: {to_delete['id']}")

    print(f"\n✅ Saneamiento completado. Se eliminaron {deleted_count} duplicados técnicos.")
else:
    print("❌ Error al obtener cursos para de-duplicación.")
