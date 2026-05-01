import os, sys, json, requests
sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client

PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
if not all([PRO_URL, PRO_KEY]):
    sys.exit('ERROR: Set SUPABASE_PRO_URL and SUPABASE_SERVICE_ROLE_KEY env vars')
h = {"apikey": PRO_KEY, "Authorization": "Bearer " + PRO_KEY, "Content-Type": "application/json"}

db = get_db_client()
insts = db.select_all('institutions')
print("Free institutions:", len(insts))

# Test: insert 1 institution
test = {}
for k, v in insts[0].items():
    if v is not None:
        test[k] = v

print("Test:", test["name"], test["id"])

# Insert single
r2 = requests.post(PRO_URL + "/rest/v1/institutions", headers=h, json=[test], timeout=30)
print("INSERT status:", r2.status_code)
print("Response:", r2.text[:300])

# Count
r3 = requests.get(PRO_URL + "/rest/v1/institutions?select=count", headers={**h, "Prefer": "count=exact"})
cr = r3.headers.get("content-range", "?")
print("Pro count:", cr.split("/")[-1])
