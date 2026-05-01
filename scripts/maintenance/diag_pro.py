import os, requests

PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
if not all([PRO_URL, PRO_KEY]):
    raise SystemExit('ERROR: Set SUPABASE_PRO_URL and SUPABASE_SERVICE_ROLE_KEY env vars')
h = {"apikey": PRO_KEY, "Authorization": "Bearer " + PRO_KEY, "Content-Type": "application/json"}

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
