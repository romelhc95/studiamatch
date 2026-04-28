import requests
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

ulima_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"
new_exclusions = ["/open-registro", "/gabinete-psicometrico/", "/news/", "/registro-exitoso"]

print("--- 1. Registrando Exclusiones en crawler_exclusions ---")
for pat in new_exclusions:
    requests.post(f"{url}/rest/v1/crawler_exclusions", headers=headers, json={
        "institution_id": ulima_id, "pattern": pat, "reason": "Exclusión manual de usuario (Fase 50.1)"
    })

print("\n--- 2. Limpiando Tablas de Producción (Borrado) ---")
for table in ["courses", "enriched_programs", "cleansed_programs"]:
    count = 0
    for pat in new_exclusions:
        clean_p = pat.replace("/", "")
        res = requests.delete(f"{url}/rest/v1/{table}?institution_id=eq.{ulima_id}&url=ilike.*{clean_p}*", headers=headers)
        if res.status_code in [200, 204]: count += len(res.json()) if res.content else 0
    print(f"🗑️ Tabla {table.ljust(18)}: {count} registros eliminados.")

print("\n--- 3. Marcando Staging como 'discarded' (Auditoría) ---")
total_marked = 0
for pat in new_exclusions:
    clean_p = pat.replace("/", "")
    res = requests.patch(f"{url}/rest/v1/staging_raw?institution_id=eq.{ulima_id}&url=ilike.*{clean_p}*", 
                         headers=headers, 
                         json={"status": "discarded", "metadata": {"discard_reason": "manual_user_exclusion"}})
    if res.status_code in [200, 204]: total_marked += len(res.json()) if res.content else 0
print(f"📦 staging_raw: {total_marked} registros marcados como descartados.")
