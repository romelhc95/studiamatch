import sys, json, requests
sys.path.insert(0, '/app')
from scripts.shared.db_client import DatabaseClient
from scripts.shared.supabase_credentials import (
    build_supabase_headers,
    get_environment_credentials,
    require_distinct_environments,
)

# ── Connect to Free DB ──
FREE = get_environment_credentials("FREE")
PRO = get_environment_credentials("PRO")
require_distinct_environments(FREE, PRO)
db = DatabaseClient(FREE.url, FREE.secret_key)
PRO_URL, PRO_KEY = PRO.url, PRO.secret_key
PRO_HEADERS = build_supabase_headers(PRO_KEY, kind="secret")
print(f"✅ Pro connection: {PRO_URL[:40]}...")

# ──────────────────────────────────────────────
# 1. Create PUCP institution in Free
# ──────────────────────────────────────────────

pucp_inst_data = {
    "name": "Pontificia Universidad Católica del Perú",
    "slug": "pucp",
    "website_url": "https://www.pucp.edu.pe",
    "status": "Activa",
    "type": "Univ",
}

existing = db.select_service('institutions', filters='slug=eq.pucp', limit=1)
if existing:
    pucp_id = existing[0]['id']
    print(f"ℹ️ PUCP already exists in Free: id={pucp_id}")
else:
    result = db.insert('institutions', pucp_inst_data)
    if result and isinstance(result, list) and len(result) > 0:
        pucp_id = result[0]['id']
    elif result and isinstance(result, dict):
        pucp_id = result.get('id')
    else:
        # Fallback: query by slug
        existing2 = db.select_service('institutions', filters='slug=eq.pucp', limit=1)
        pucp_id = existing2[0]['id'] if existing2 else None
    print(f"✅ PUCP created in Free: id={pucp_id}")

# ──────────────────────────────────────────────
# 2. Create/update PUCP profile in Free
# ──────────────────────────────────────────────

profiles = db.select_service('institution_site_profiles', filters=f'institution_id=eq.{pucp_id}', limit=1)
pucp_profile_data = {
    "site_type": "spa_js_heavy",
    "discovery_mode": "paginated_catalog",
    "catalog_url_patterns": json.dumps(["https://www.pucp.edu.pe/programas/?jsf=jet-engine&pagenum={page}"]),
    "catalog_link_selector": "a.jet-listing-dynamic-image__link",
    "catalog_max_pages": 13,
    "exclusion_patterns": json.dumps([
        "/blog/", "/noticias/", "/eventos/", "/about/", "/contacto/",
        "/admision/", "/becas/", "/investigacion/", "/publicaciones/",
        "/biblioteca/", "/internacional/", "/vida-universitaria/",
        ".pdf", ".jpg", ".png", ".zip",
        "/tag/", "/category/", "/author/",
        "/profesores/", "/egresado/",
    ]),
    "allowed_url_patterns": json.dumps(["re:.*programas.*"]),
    "requires_stealth": False,
    "requires_cloudflare_bypass": False,
    "detail_wait_ms": 4000,
    "field_defaults": json.dumps({"mode": "Presencial"}),
    "pipeline_ready": False,
    "notes": "PUCP website. Paginated catalog discovery via JetEngine.",
}

if profiles:
    db.patch('institution_site_profiles', f"id=eq.{profiles[0]['id']}", pucp_profile_data)
    print(f"✅ PUCP profile updated in Free (id={profiles[0]['id']})")
else:
    pucp_profile_data['institution_id'] = str(pucp_id)
    result = db.insert('institution_site_profiles', pucp_profile_data)
    print(f"✅ PUCP profile created in Free")

# ──────────────────────────────────────────────
# 3. Sync all profiles to Pro
# ──────────────────────────────────────────────

if has_pro:
    free_profiles = db.select_all('institution_site_profiles')
    free_insts = db.select_all('institutions')
    free_inst_map = {str(i['id']): i for i in free_insts}
    print(f"\n--- Syncing {len(free_profiles)} profiles to Pro ---")

    # Get Pro institutions and profiles
    try:
        r = requests.get(f"{PRO_URL}/rest/v1/institutions?select=id,slug", headers=PRO_HEADERS, timeout=15)
        r.raise_for_status()
        pro_insts = r.json()
    except Exception as e:
        print(f"❌ Pro institutions query failed: {e}")
        sys.exit(1)

    pro_inst_map = {i['slug']: i['id'] for i in pro_insts}
    print(f"Pro institutions: {len(pro_inst_map)} ({', '.join(pro_inst_map.keys())})")

    # Get Pro profiles
    try:
        r = requests.get(f"{PRO_URL}/rest/v1/institution_site_profiles?select=institution_id", headers=PRO_HEADERS, timeout=15)
        r.raise_for_status()
        pro_profile_inst_ids = {p['institution_id'] for p in r.json()}
    except Exception as e:
        print(f"❌ Pro profiles query failed: {e}")
        pro_profile_inst_ids = set()

    synced = 0
    for p in free_profiles:
        free_inst = free_inst_map.get(str(p['institution_id']))
        if not free_inst:
            continue
        slug = free_inst['slug']
        pro_inst_id = pro_inst_map.get(slug)
        if not pro_inst_id:
            print(f"  SKIP {slug}: not in Pro")
            continue

        # Build profile payload — all fields now that Pro has pipeline_ready + allowed_url_patterns
        payload = {}
        for field in ['site_type', 'discovery_mode', 'seed_urls', 'exclusion_patterns',
                       'catalog_url_patterns', 'catalog_link_selector', 'catalog_max_pages',
                       'catalog_scroll_iterations', 'requires_stealth', 'requires_cloudflare_bypass',
                       'warmup_url', 'popup_close_selectors', 'detail_wait_ms',
                       'section_keywords', 'field_defaults', 'section_mode_map', 'section_course_type_map',
                       'title_prefix_removals', 'title_split_separators', 'price_regex', 'duration_regex',
                       'max_courses_per_run', 'soft_delete_before_scrape', 'notes',
                       'pipeline_ready', 'allowed_url_patterns']:
            val = p.get(field)
            if val is not None:
                payload[field] = val

        payload['institution_id'] = pro_inst_id

        if pro_inst_id in pro_profile_inst_ids:
            # UPDATE existing profile
            api_url = f"{PRO_URL}/rest/v1/institution_site_profiles?institution_id=eq.{pro_inst_id}"
            r = requests.patch(api_url, json=payload, headers=PRO_HEADERS, timeout=15)
            if r.status_code in (200, 204):
                print(f"  ✅ {slug}: profile updated in Pro")
                synced += 1
            else:
                print(f"  ❌ {slug}: PATCH failed HTTP {r.status_code}")
        else:
            # INSERT new profile
            api_url = f"{PRO_URL}/rest/v1/institution_site_profiles"
            r = requests.post(api_url, json=payload, headers=PRO_HEADERS, timeout=15)
            if r.status_code in (200, 201):
                print(f"  ✅ {slug}: profile created in Pro")
                synced += 1
            else:
                print(f"  ❌ {slug}: POST failed HTTP {r.status_code}")

    print(f"\n✅ Pro sync complete: {synced}/{len(free_profiles)} profiles synced")

print("\n🎉 Done")
