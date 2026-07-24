import sys, json, requests
sys.path.insert(0, '/app')
from scripts.shared.db_client import DatabaseClient
from scripts.shared.supabase_credentials import (
    build_supabase_headers,
    get_environment_credentials,
    require_distinct_environments,
)

FREE = get_environment_credentials("FREE")
PRO = get_environment_credentials("PRO")
require_distinct_environments(FREE, PRO)
PRO_URL, PRO_KEY = PRO.url, PRO.secret_key
h = build_supabase_headers(PRO_KEY, kind="secret")

db = DatabaseClient(FREE.url, FREE.secret_key)
insts = db.select_all_service('institutions')
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
