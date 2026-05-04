import sys, json
sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client

db = get_db_client()

def get_inst_id(slug):
    r = db.select('institutions', filters=f'slug=eq.{slug}', columns='id')
    return r[0]['id'] if r else None

def update_profile(inst_slug, updates):
    inst_id = get_inst_id(inst_slug)
    if not inst_id:
        print(f"  SKIP {inst_slug}: not found")
        return
    profiles = db.select('institution_site_profiles', filters=f'institution_id=eq.{inst_id}', columns='id')
    if not profiles:
        print(f"  SKIP {inst_slug}: no profile")
        return
    profile_id = profiles[0]['id']
    data = {}
    for k, v in updates.items():
        if isinstance(v, (list, dict)):
            data[k] = json.dumps(v)
        else:
            data[k] = v
    db.patch('institution_site_profiles', f"id=eq.{profile_id}", data)
    print(f"  OK {inst_slug}: {list(updates.keys())}")

# ── DMC (ecommerce, catalog_link_extraction, stealth, Cloudflare) ──
update_profile('dmc', {
    'discovery_mode': 'catalog_link_extraction',
    'catalog_link_selector': '.elementor-post__title a, .elementor-post__read-more, .elementor-button-link',
    'catalog_scroll_iterations': 15,
    'requires_stealth': True,
    'requires_cloudflare_bypass': True,
    'warmup_url': 'https://www.dmc.pe/',
    'detail_wait_ms': 3000,
})

# ── PUCP (paginated_catalog) — NOTA: PUCP no está en Free DB
# Cuando se agregue:
#   discovery_mode=paginated_catalog
#   catalog_url_patterns=["https://www.pucp.edu.pe/programas/?jsf=jet-engine&pagenum={page}"]
#   catalog_max_pages=13
#   catalog_link_selector="a.jet-listing-dynamic-image__link"
#   detail_wait_ms=4000

# ── UTP (title_prefix_removals for ▷) ──
update_profile('utp', {
    'title_prefix_removals': ['▷ ', '▷', '> '],
    'title_split_separators': [' | ', ' - '],
})

# ── UPC (title_prefix_removals for "Carrera de ") ──
update_profile('upc', {
    'title_prefix_removals': ['Carrera de '],
    'detail_wait_ms': 4000,
})

# ── USIL (popup_close_selectors) ──
update_profile('usil', {
    'popup_close_selectors': ['button.close', '.modal-close', '[data-dismiss="modal"]'],
})

# ── IDAT (title quality via detail_wait_ms already 4000, add split separators) ──
update_profile('idat', {
    'title_split_separators': [' | ', ' - '],
    'detail_wait_ms': 4000,
})

# ── U. Lima (already has hardcoded_urls, section_keywords — just add split separators) ──
update_profile('universidad-de-lima', {
    'title_split_separators': [' | ', ' - '],
    'detail_wait_ms': 3000,
})

# ── Pacifico (section_keywords already has 2, add split separators) ──
update_profile('universidad-del-pacifico', {
    'title_split_separators': [' | ', ' - '],
})

# ── Continental, SENATI, UNMSM, UNI: already fine with defaults

print("\n✅ All profiles updated")

# Verify
print("\n=== Verification ===")
for slug in ['dmc', 'utp', 'upc', 'usil', 'idat', 'universidad-de-lima', 'universidad-del-pacifico', 'senati', 'universidad-continental', 'unmsm', 'uni']:
    inst_id = get_inst_id(slug)
    if not inst_id: continue
    p = db.select('institution_site_profiles', filters=f'institution_id=eq.{inst_id}', limit=1)
    if not p: continue
    p = p[0]
    print(f"  {slug:15s} dm={p.get('discovery_mode','NONE'):25s} stealth={p.get('requires_stealth')} cf={p.get('requires_cloudflare_bypass')} sel={(p.get('catalog_link_selector') or '')[0:50]}")
