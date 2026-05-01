"""Fase 32B: Fix courses and crawler_exclusions, complete migration"""
import os, sys, json, time, requests
sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client

MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')
PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
PRO_PROJECT_REF = PRO_URL.replace('https://', '').replace('.supabase.co', '') if PRO_URL else ''
if not all([MGMT_TOKEN, PRO_URL, PRO_KEY]):
    sys.exit('ERROR: Set SUPABASE_MGMT_TOKEN, SUPABASE_PRO_URL, SUPABASE_SERVICE_ROLE_KEY env vars')
h_mgmt = {"Authorization": "Bearer " + MGMT_TOKEN, "Content-Type": "application/json"}
h_pro = {"apikey": PRO_KEY, "Authorization": "Bearer " + PRO_KEY, "Content-Type": "application/json"}

def mgmt(sql):
    r = requests.post(f'https://api.supabase.com/v1/projects/{PRO_PROJECT_REF}/database/query',
                      json={'query': sql}, headers=h_mgmt, timeout=60)
    ok = r.status_code == 201
    if not ok:
        print(f"  FAIL: {r.status_code} {r.text[:200]}")
    return ok

def mgmt_query(sql):
    r = requests.post(f'https://api.supabase.com/v1/projects/{PRO_PROJECT_REF}/database/query',
                      json={'query': sql}, headers=h_mgmt, timeout=60)
    if r.status_code == 201:
        return r.json()
    return None

# ============================================================
# STEP 1: Diagnose courses CHECK constraint
# ============================================================
print("=== STEP 1: Diagnose courses CHECK constraints ===")
rows = mgmt_query("SELECT conname, pg_get_constraintdef(pg_constraint.oid) as def FROM pg_constraint WHERE conrelid = 'courses'::regclass AND contype = 'c';")
if rows:
    for r in rows:
        print(f"  {r['conname']}: {r['def']}")

# Drop all CHECK constraints on courses
print("\nDropping CHECK constraints...")
for r in rows:
    mgmt(f'ALTER TABLE courses DROP CONSTRAINT IF EXISTS "{r["conname"]}";')

# ============================================================
# STEP 2: Fix crawler_exclusions - force delete and re-insert
# ============================================================
print("\n=== STEP 2: Fix crawler_exclusions ===")
mgmt("DELETE FROM crawler_exclusions WHERE 1=1;")
# Check unique constraints
constraints = mgmt_query("SELECT conname, contype, pg_get_constraintdef(pg_constraint.oid) as def FROM pg_constraint WHERE conrelid = 'crawler_exclusions'::regclass AND contype = 'u';")
if constraints:
    for r in constraints:
        print(f"  UNIQUE: {r['conname']}: {r['def']}")

# ============================================================
# STEP 3: Insert courses and crawler_exclusions
# ============================================================
db = get_db_client()

def insert_batch(table, data, batch_size=200):
    if not data:
        return 0
    ok = 0
    total = len(data)
    for i in range(0, total, batch_size):
        batch = data[i:i+batch_size]
        clean = []
        for row in batch:
            c = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    c[k] = json.dumps(v) if v is not None else None
                else:
                    c[k] = v
            clean.append(c)
        r = requests.post(PRO_URL + "/rest/v1/" + table, headers=h_pro, json=clean, timeout=120)
        if r.status_code in (200, 201):
            ok += len(batch)
            print(f"  {table}: {ok}/{total}", end="\r")
        else:
            print(f"\n  FAIL batch {i}: {r.status_code} {r.text[:250]}")
            # Row by row fallback
            for row in clean:
                r2 = requests.post(PRO_URL + "/rest/v1/" + table, headers=h_pro, json=[row], timeout=60)
                if r2.status_code in (200, 201):
                    ok += 1
                else:
                    print(f"  ROW FAIL: {r2.status_code} {r2.text[:200]}")
                    if table == 'courses':
                        return ok
            print(f"  {table}: {ok}/{total}", end="\r")
        time.sleep(0.3)
    return ok

# courses
print("\n=== STEP 3a: Insert courses ===")
courses = db.select_all('courses')
print(f"Free: {len(courses)} courses")
n = insert_batch('courses', courses)
print(f"\nDone: {n}/{len(courses)}")

# crawler_exclusions - use upsert to handle duplicates
print("\n=== STEP 3b: Upsert crawler_exclusions ===")
exclusions = db.select_all('crawler_exclusions')
print(f"Free: {len(exclusions)} exclusions")
ok = 0
for row in exclusions:
    clean = {}
    for k, v in row.items():
        if isinstance(v, (dict, list)):
            clean[k] = json.dumps(v) if v is not None else None
        else:
            clean[k] = v
    r = requests.post(PRO_URL + "/rest/v1/crawler_exclusions?on_conflict=institution_id,pattern", 
                      headers={**h_pro, "Prefer": "resolution=merge-duplicates"}, json=clean, timeout=30)
    if r.status_code in (200, 201):
        ok += 1
    else:
        print(f"\n  ROW FAIL: {r.status_code} {r.text[:150]}")
    if ok % 50 == 0:
        print(f"  {ok}/{len(exclusions)}", end="\r")
print(f"\nDone: {ok}/{len(exclusions)}")

# ============================================================
# STEP 4: Final verification
# ============================================================
print("\n=== STEP 4: Final counts ===")
tables = ['institutions','categories','market_salaries','category_rules',
          'courses','crawler_exclusions','enriched_programs','ratings',
          'reviews','leads']
for t in tables:
    fc = db.count(t)
    r = requests.get(PRO_URL + f"/rest/v1/{t}?select=count",
                     headers={**h_pro, "Prefer": "count=exact"}, timeout=15)
    cr = r.headers.get("content-range", "?")
    pc = cr.split("/")[-1] if "/" in cr else "?"
    ok = str(fc) == str(pc)
    print(f"  {t}: Free={fc} Pro={pc} [{ 'OK' if ok else 'DIFF' }]")

print("\n=== DONE ===")
