"""Fase 74: Seed institution_site_profiles in Pro — reads profiles from Free via db_client, upserts to Pro via raw requests"""
import sys, os, json, requests

sys.path.insert(0, '/app')

PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', os.environ.get('NEXT_SUPABASE_SECRET_KEY', ''))

if not PRO_URL or not PRO_KEY:
    print("ERROR: SUPABASE_PRO_URL and service_role/secret key required")
    print("Usage: set SUPABASE_PRO_URL + NEXT_SUPABASE_SECRET_KEY env vars")
    sys.exit(1)

headers = {
    'apikey': PRO_KEY,
    'Authorization': f'Bearer {PRO_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

# Read profiles from Free (via db_client which reads env from .env.local)
from scripts.shared.db_client import get_db_client
db = get_db_client()

free_profiles = db.select('institution_site_profiles', columns='*')
if not free_profiles:
    print("ERROR: No profiles found in Free DB")
    sys.exit(1)

print(f"Read {len(free_profiles)} profiles from Free")

# Get matching institutions in Pro
r = requests.get(f"{PRO_URL}/rest/v1/institutions?select=id,slug,name", headers=headers)
pro_insts = r.json() if r.status_code == 200 else []
pro_slugs = {i['slug']: i for i in pro_insts}

ok = 0
skip = 0
errors = 0

for profile in free_profiles:
    iid = profile['institution_id']

    # Find matching institution in Free to get slug
    free_inst = db.select('institutions', filters=f'id=eq.{iid}', columns='slug,name')
    if not free_inst:
        print(f"SKIP: institution {iid[:8]}... not found in Free")
        skip += 1
        continue

    slug = free_inst[0]['slug']

    if slug not in pro_slugs:
        print(f"SKIP: {slug} not in Pro institutions")
        skip += 1
        continue

    pro_inst = pro_slugs[slug]
    n = len(profile.get('exclusion_patterns', []) or [])

    # Prepare profile data (remove id, timestamps)
    data = {k: v for k, v in profile.items() if k not in ('id', 'created_at', 'updated_at')}
    data['institution_id'] = pro_inst['id']

    url = f"{PRO_URL}/rest/v1/institution_site_profiles?on_conflict=institution_id"
    r2 = requests.post(url, headers=headers, json=data, timeout=30)
    if r2.status_code in (200, 201):
        print(f"OK: {slug} — {n} exclusions, type={profile.get('site_type')}")
        ok += 1
    else:
        print(f"ERR: {slug} — HTTP {r2.status_code}")
        errors += 1

print(f"\nDone: {ok} OK, {skip} skip, {errors} errors")
