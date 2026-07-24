import os, sys, requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.shared.supabase_credentials import build_supabase_headers, get_environment_credentials

PRO = get_environment_credentials('PRO')
PRO_URL, PRO_KEY = PRO.url, PRO.secret_key
h = build_supabase_headers(PRO_KEY, kind="secret")

tables = ["courses","institutions","categories","category_rules","market_salaries",
          "crawler_exclusions","staging_raw","cleansed_programs","enriched_programs",
          "ratings","reviews","leads"]

print("=== Pro Project Tables ===")
for t in tables:
    r = requests.get(PRO_URL + "/rest/v1/" + t + "?select=count",
                     headers={**h, "Prefer": "count=exact"})
    cr = r.headers.get("content-range", "?")
    count = cr.split("/")[-1] if "/" in cr else "?"
    status = r.status_code
    print(t + ": status=" + str(status) + " count=" + count)

print()
print("=== courses columns ===")
r = requests.get(PRO_URL + "/rest/v1/courses?limit=1", headers=h)
if r.status_code == 200 and r.json():
    cols = list(r.json()[0].keys())
    for c in sorted(cols):
        print("  " + c)
    print("  Total: " + str(len(cols)))
else:
    print("status: " + str(r.status_code) + " body: " + r.text[:200])
