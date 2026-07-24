import os, sys, json, re, requests
sys.path.insert(0, '/app')
from scripts.shared.supabase_credentials import build_supabase_headers, get_secret_key

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', '')
secret = get_secret_key(required=False)
if not url or not secret:
    sys.exit('ERROR: Set NEXT_PUBLIC_SUPABASE_URL and NEXT_SUPABASE_SECRET_KEY')

with open('/app/config/institution_sources.json') as f:
    sources = json.load(f)

def make_slug(name):
    s = name.lower().replace('\u00f1', 'n').replace('\u00fa', 'u').replace('\u00f3', 'o').replace('\u00ed', 'i').replace('\u00e1', 'a').replace('\u00e9', 'e')
    s = re.sub(r'[^a-z0-9-]', '-', s)
    return re.sub(r'-+', '-', s).strip('-')

def get_type(name):
    return 'Univ' if 'universidad' in name.lower() else 'Inst'

rows = [{'name': s['name'], 'slug': make_slug(s['name']), 'website_url': s['url'], 'type': get_type(s['name']), 'status': 'Activa', 'region': 'Lima'} for s in sources]

h = build_supabase_headers(secret, kind="secret")
inserted = 0
for row in rows:
    r = requests.post(f'{url}/rest/v1/institutions', headers={**h, 'Prefer': 'resolution=merge-duplicates'}, json=[row], timeout=30)
    if r.status_code in (200, 201, 204):
        inserted += 1
        print(f'  OK: {row["name"]}')
    else:
        print(f'  EXISTS/SKIP: {row["name"]} ({r.status_code})')
print(f'Done: {inserted}/{len(rows)} institutions')
