"""Seed Pro profiles from an explicit, isolated Free identity."""
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

headers = {
    **build_supabase_headers(PRO_KEY, kind="secret"),
    'Prefer': 'resolution=merge-duplicates',
}

# Read profiles from Free through an isolated explicit client.
db = DatabaseClient(FREE.url, FREE.secret_key)

free_profiles = db.select_service('institution_site_profiles', columns='*')
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
    free_inst = db.select_service('institutions', filters=f'id=eq.{iid}', columns='slug,name')
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
