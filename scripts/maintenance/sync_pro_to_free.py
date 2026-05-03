#!/usr/bin/env python3
"""Sync Pro pipeline data to Free/Desarrollo DB with institution UUID mapping."""
import json, urllib.request, sys, time, os

sys.path.insert(0, '/app')
from dotenv import load_dotenv

# Cargar Free primero y capturar sus valores
load_dotenv('/app/.env.local')
FREE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
FREE_KEY = os.environ.get("NEXT_SUPABASE_SECRET_KEY", "")

# Cargar Pro (sobrescribe) y capturar sus valores
load_dotenv('/app/.env.gitprod', override=True)
PRO_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
PRO_KEY = os.environ.get("NEXT_SUPABASE_SECRET_KEY", "")

if not all([PRO_URL, PRO_KEY, FREE_URL, FREE_KEY]):
    print("ERROR: Verifica que .env.local (Free) y .env.gitprod (Pro) tengan NEXT_PUBLIC_SUPABASE_URL y NEXT_SUPABASE_SECRET_KEY")
    sys.exit(1)

t_out = 30

def api(path, key, base_url):
    r = urllib.request.Request(f"{base_url}/rest/v1/{path}", headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"})
    with urllib.request.urlopen(r, timeout=t_out) as resp:
        return json.loads(resp.read().decode())

def get_all(path, key, base_url):
    all_data = []
    offset = 0
    limit = 1000
    while True:
        sep = "&" if "?" in path else "?"
        r = urllib.request.Request(f"{base_url}/rest/v1/{path}{sep}limit={limit}&offset={offset}", headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=t_out) as resp:
                chunk = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  Error fetching: {e}")
            break
        if not chunk:
            break
        all_data.extend(chunk)
        if len(chunk) < limit:
            break
        offset += limit
    return all_data

def insert_batch(rows, table, key, base_url):
    if not rows:
        print(f"  (empty) -> {table}, skipping")
        return
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        batch = rows[i:i+chunk_size]
        data = json.dumps(batch).encode()
        r = urllib.request.Request(
            f"{base_url}/rest/v1/{table}", data=data,
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(r, timeout=t_out):
                print(f"  {len(batch)} -> {table} (batch {i//chunk_size +1}/{(len(rows)-1)//chunk_size+1})")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print(f"  FAIL {table} batch {i//chunk_size +1}: {e.code} {body[:120]}")
        except Exception as e:
            print(f"  FAIL {table} batch {i//chunk_size +1}: {e}")
        time.sleep(0.3)

# Step 1: Get institutions from both DBs
print("=== Mapeando instituciones PRO vs FREE ===")
pro_inst = api("institutions?select=id,name,slug", PRO_KEY, PRO_URL)
free_inst = api("institutions?select=id,name,slug", FREE_KEY, FREE_URL)

# Build mapping: Pro slug -> Free ID
inst_map = {}
for p in pro_inst:
    slug = p["slug"]
    match = [f for f in free_inst if f["slug"] == slug]
    if match:
        inst_map[p["id"]] = match[0]["id"]
        print(f"  {p['name']}: {p['id'][:8]}... -> {match[0]['id'][:8]}...")
    else:
        print(f"  WARN: {p['name']} ({slug}) NO EXISTE en Free")

def remap_institution_id(records, id_field="institution_id"):
    """Replace Pro institution_id with Free institution_id."""
    for rec in records:
        if rec.get(id_field) in inst_map:
            rec[id_field] = inst_map[rec[id_field]]
        else:
            print(f"  WARN: {id_field} {rec.get(id_field)} not mapped, skipping record")
    return [r for r in records if r.get(id_field) in inst_map.values()]

# Step 2: Export from Pro
print("\n=== Exportando desde PRO ===")
print("staging_raw discovered...")
sr_d = get_all("staging_raw?status=eq.discovered&select=*", PRO_KEY, PRO_URL)
print("staging_raw pending...")
sr_p = get_all("staging_raw?status=eq.pending&select=*", PRO_KEY, PRO_URL)
print("cleansed_programs...")
cl = get_all("cleansed_programs?select=*", PRO_KEY, PRO_URL)
print("enriched_programs...")
en = get_all("enriched_programs?select=*", PRO_KEY, PRO_URL)

staging = sr_d + sr_p
print(f"\n  staging_raw: {len(staging)}")
print(f"  cleansed_programs: {len(cl)}")
print(f"  enriched_programs: {len(en)}")

# Step 3: Remap institution_ids
print("\n=== Remapeando institution_ids → FREE ===")
staging = remap_institution_id(staging)
cl = remap_institution_id(cl)
en = remap_institution_id(en)
print(f"  staging_raw: {len(staging)} (after remap)")
print(f"  cleansed_programs: {len(cl)} (after remap)")
print(f"  enriched_programs: {len(en)} (after remap)")

# Step 4: Clear Free staging_raw before import
print("\n=== Limpiando FREE antes de importar ===")
for table in ["staging_raw", "cleansed_programs", "enriched_programs"]:
    try:
        r = urllib.request.Request(
            f"{FREE_URL}/rest/v1/{table}?id=neq.00000000-0000-0000-0000-000000000000",  # match all
            headers={"apikey": FREE_KEY, "Authorization": f"Bearer {FREE_KEY}"},
            method="DELETE"
        )
        with urllib.request.urlopen(r, timeout=t_out):
            print(f"  Cleared {table}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:100]
        print(f"  Clear {table}: {e.code} {body}")

# Step 5: Import to Free
print("\n=== Importando a FREE ===")
insert_batch(staging, "staging_raw", FREE_KEY, FREE_URL)
insert_batch(cl, "cleansed_programs", FREE_KEY, FREE_URL)
insert_batch(en, "enriched_programs", FREE_KEY, FREE_URL)

print("\n✅ Sync PRO → FREE completado.")
print("\nPara procesar los datos en desarrollo, ejecuta en orden:")
print("  1. docker exec studiamatch-dev python3 scripts/core/cleansing_worker.py")
print("  2. docker exec studiamatch-dev python3 scripts/core/enrichment_worker.py")
print("  3. docker exec studiamatch-dev python3 scripts/core/sync_vector_worker.py")
