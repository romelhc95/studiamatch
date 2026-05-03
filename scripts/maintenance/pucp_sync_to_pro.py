import sys, os, json, requests
sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client
from dotenv import load_dotenv

db = get_db_client()

PRO_ENV_PATH = '/app/.env.gitprod'
pro_vars = {}
if os.path.exists(PRO_ENV_PATH):
    with open(PRO_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                pro_vars[k.strip()] = v.strip().strip("'\"")

PRO_URL = pro_vars.get('NEXT_PUBLIC_SUPABASE_URL', '')
PRO_KEY = pro_vars.get('NEXT_SUPABASE_SECRET_KEY', '')
PRO_HEADERS = {'apikey': PRO_KEY, 'Authorization': f'Bearer {PRO_KEY}', 'Content-Type': 'application/json'}

# Get PUCP from Free
pucp = db.select('institutions', filters='slug=eq.pucp', limit=1)
if not pucp:
    print("ERROR: PUCP not in Free")
    sys.exit(1)
free_id = pucp[0]['id']

profiles = db.select('institution_site_profiles', filters=f'institution_id=eq.{free_id}', limit=1)
if not profiles:
    print("ERROR: PUCP profile not in Free")
    sys.exit(1)

# Get or create PUCP in Pro
try:
    r = requests.get(f"{PRO_URL}/rest/v1/institutions?slug=eq.pucp&select=id", headers=PRO_HEADERS, timeout=15)
    r.raise_for_status()
    pro_pucp = r.json()
except Exception as e:
    print(f"❌ Pro query failed: {e}")
    sys.exit(1)

if pro_pucp and len(pro_pucp) > 0:
    pro_pucp_id = pro_pucp[0]['id']
    print(f"ℹ️ PUCP exists in Pro: id={pro_pucp_id}")
else:
    # Create PUCP in Pro
    pro_inst_data = {
        "name": "Pontificia Universidad Católica del Perú",
        "slug": "pucp",
        "website_url": "https://www.pucp.edu.pe",
        "status": "Activa",
        "type": "Univ",
    }
    r = requests.post(f"{PRO_URL}/rest/v1/institutions?select=id", json=pro_inst_data, headers={**PRO_HEADERS, 'Prefer': 'return=representation'}, timeout=15)
    if r.status_code in (200, 201):
        pro_pucp_id = r.json()[0]['id']
        print(f"✅ PUCP created in Pro: id={pro_pucp_id}")
    else:
        print(f"❌ Pro insert failed: {r.status_code} {r.text[:200]}")
        sys.exit(1)

# Create/update profile in Pro
pro_profile_url = f"{PRO_URL}/rest/v1/institution_site_profiles?institution_id=eq.{pro_pucp_id}"
r = requests.get(pro_profile_url, headers=PRO_HEADERS, timeout=15)
existing_pro = r.json() if r.status_code == 200 else []

free_profile = profiles[0]
payload = {}
for field in ['site_type', 'discovery_mode', 'seed_urls', 'exclusion_patterns',
               'catalog_url_patterns', 'catalog_link_selector', 'catalog_max_pages',
               'catalog_scroll_iterations', 'requires_stealth', 'requires_cloudflare_bypass',
               'warmup_url', 'popup_close_selectors', 'detail_wait_ms',
               'section_keywords', 'field_defaults', 'section_mode_map',
               'title_prefix_removals', 'title_split_separators', 'price_regex',
               'max_courses_per_run', 'notes']:
    val = free_profile.get(field)
    if val is not None:
        payload[field] = val
payload['institution_id'] = pro_pucp_id

if existing_pro and len(existing_pro) > 0:
    r = requests.patch(pro_profile_url, json=payload, headers=PRO_HEADERS, timeout=15)
    action = "updated"
else:
    r = requests.post(f"{PRO_URL}/rest/v1/institution_site_profiles", json=payload, headers=PRO_HEADERS, timeout=15)
    action = "created"

if r.status_code in (200, 201, 204):
    print(f"✅ PUCP profile {action} in Pro")
else:
    print(f"❌ PUCP profile {action} failed: {r.status_code} {r.text[:200]}")

print("\n🎉 PUCP sync complete")
