import os
import requests
from dotenv import load_dotenv

load_dotenv(".env.local")
url = os.getenv("SUPABASE_URL", "https://fmcxwoqvxatbrawwtqke.supabase.co")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# 1. Nuevas exclusiones
exclusions = [
    # DMC
    {"institution_id": "c64123d6-f00e-4c89-86a8-7706845c0483", "pattern": "add-to-cart="},
    {"institution_id": "c64123d6-f00e-4c89-86a8-7706845c0483", "pattern": "_filtro_"},
    # UP
    {"institution_id": "cf64d254-733d-4a92-8a2d-5df5b9dc80ac", "pattern": "/noticias/"},
    {"institution_id": "cf64d254-733d-4a92-8a2d-5df5b9dc80ac", "pattern": "/eventos/"},
    {"institution_id": "cf64d254-733d-4a92-8a2d-5df5b9dc80ac", "pattern": "/blog/"},
    # New Horizons
    {"institution_id": "24cc140d-de25-4ef1-9316-b897b451be50", "pattern": "/login"},
    {"institution_id": "24cc140d-de25-4ef1-9316-b897b451be50", "pattern": ".pdf"},
    {"institution_id": "24cc140d-de25-4ef1-9316-b897b451be50", "pattern": ".docx"}
]

print("--- 1. Actualización del Escudo Antiruido ---")
for exc in exclusions:
    res = requests.post(f"{url}/rest/v1/crawler_exclusions", headers=headers, json=exc)
    if res.status_code in [200, 201]:
        print(f"✅ Registrada exclusión: {exc['pattern']} para {exc['institution_id']}")

# 2. Limpieza en Cascada Retroactiva
tables = ["courses", "enriched_programs", "cleansed_programs", "staging_raw"]
print("\n--- 2. Saneamiento Retroactivo (Limpieza de Ruido) ---")
for table in tables:
    total_eliminados = 0
    for exc in exclusions:
        inst_id = exc["institution_id"]
        # Evitamos caracteres especiales en el ilike si podemos, o los manejamos con cuidado
        p = exc["pattern"].replace("/", "").replace("=", "").replace(".", "")
        res = requests.delete(f"{url}/rest/v1/{table}?institution_id=eq.{inst_id}&url=ilike.*{p}*", headers=headers)
        if res.status_code in [200, 204]:
            total_eliminados += len(res.json()) if res.content else 0
    print(f"🗑️ Tabla {table.ljust(18)}: {total_eliminados} registros de ruido eliminados.")

# 3. Consolidación de Subpáginas (UP)
up_inst_id = "cf64d254-733d-4a92-8a2d-5df5b9dc80ac"
up_suffixes = ['/malla-curricular/', '/presentacion/', '/admision/', '/plana-docente/', '/beneficios/', '/sustentacion-tesis/', '/ranking-eduniversal/']

print("\n--- 3. Consolidación de Subpáginas (UP) ---")
for table in ["courses", "enriched_programs", "cleansed_programs"]:
    total_parciales = 0
    for suf in up_suffixes:
        clean_suf = suf.replace("/", "").replace("-", "")
        # Eliminamos usando like para no fallar con guiones
        res = requests.delete(f"{url}/rest/v1/{table}?institution_id=eq.{up_inst_id}&url=ilike.*{clean_suf}*", headers=headers)
        if res.status_code in [200, 204]:
            total_parciales += len(res.json()) if res.content else 0
    print(f"🗑️ Tabla {table.ljust(18)}: {total_parciales} subpáginas parciales eliminadas.")

# Rollback a Staging (UP)
res_staging = requests.get(f"{url}/rest/v1/staging_raw?institution_id=eq.{up_inst_id}&select=id,url", headers=headers)
rollback_count = 0
if res_staging.status_code == 200:
    for r in res_staging.json():
        # Vamos a poner TODO lo de UP en pending para que se consolide
        requests.patch(f"{url}/rest/v1/staging_raw?id=eq.{r['id']}", headers=headers, json={"status": "pending"})
        rollback_count += 1
print(f"🔄 Rollback a pending en staging_raw: {rollback_count} registros de UP listos para consolidar.")

# También rollback para New Horizons y DMC a pending para procesarlos limpios si se requiere, pero el objetivo actual es consolidar UP.
# Para DMC, simplemente eliminamos el ruido y los legítimos se quedan.
