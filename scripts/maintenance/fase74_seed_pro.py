"""Fase 74: Seed institution_site_profiles in Pro (merge CE + full seed)"""
import sys, os, json

SUPABASE_PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
SUPABASE_PRO_PUBLISHABLE = os.environ.get('SUPABASE_PRO_PUBLISHABLE_KEY', '')
SUPABASE_PRO_SECRET = os.environ.get('NEXT_SUPABASE_SECRET_KEY', os.environ.get('SUPABASE_SERVICE_ROLE_KEY', ''))

if not SUPABASE_PRO_URL or not SUPABASE_PRO_SECRET:
    print("ERROR: SUPABASE_PRO_URL and NEXT_SUPABASE_SECRET_KEY env vars required")
    sys.exit(1)

sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client
from scripts.shared.utils import setup_lima_logging

logger = setup_lima_logging('fase74_seed_pro')
db = get_db_client()

# ============================================================
# PART 1: Merge CE -> SP (same logic as merge_exclusions_to_profiles.py)
# ============================================================
logger.info("=== Part 1: Merge CE -> SP ===")

institutions = db.select('institutions', columns='id,slug,name')
if not institutions:
    logger.error("No institutions found in Pro")
    sys.exit(1)

inst_map = {i['id']: i for i in institutions}
profiles = db.select('institution_site_profiles', columns='institution_id,exclusion_patterns,site_type,discovery_mode')
profile_map = {p['institution_id']: p for p in profiles} if profiles else {}

ce_rows = db.select('crawler_exclusions', filters='is_active=eq.true', columns='institution_id,pattern')
ce_by_inst = {}
if ce_rows:
    for r in ce_rows:
        iid = r['institution_id']
        if iid not in ce_by_inst:
            ce_by_inst[iid] = set()
        ce_by_inst[iid].add(r['pattern'])

merged = 0
created_profiles = 0
summary = []

for inst in institutions:
    iid = inst['id']
    slug = inst['slug']
    ce_set = ce_by_inst.get(iid, set())

    if iid in profile_map:
        sp_set = set(profile_map[iid].get('exclusion_patterns', []) or [])
        merged_set = ce_set | sp_set
        has_new = len(merged_set) > len(sp_set)

        if has_new:
            profile_data = dict(profile_map[iid])
            profile_data['exclusion_patterns'] = sorted(merged_set)
            profile_data['institution_id'] = iid
            db.upsert('institution_site_profiles', profile_data, on_conflict='institution_id')
            merged += 1
            logger.info(f"  {slug}: {len(sp_set)} + {len(ce_set - sp_set)} CE-only = {len(merged_set)} total")
        else:
            logger.info(f"  {slug}: {len(sp_set)} (no changes needed)")
        summary.append((slug, len(ce_set), len(sp_set), len(merged_set)))
    elif ce_set:
        logger.info(f"  {slug}: CREATING PROFILE from {len(ce_set)} CE patterns")
        profile_data = {
            'institution_id': iid,
            'site_type': 'ecommerce' if 'dmc' in slug.lower() else 'traditional_ssr',
            'discovery_mode': 'sitemap_bfs',
            'seed_urls': [],
            'exclusion_patterns': sorted(ce_set),
            'catalog_url_patterns': [],
            'catalog_max_pages': 5,
            'catalog_scroll_iterations': 0,
            'requires_stealth': False,
            'requires_cloudflare_bypass': False,
            'popup_close_selectors': [],
            'detail_wait_ms': 2000,
            'section_keywords': {},
            'field_defaults': {},
            'section_mode_map': {},
            'section_course_type_map': {},
            'title_prefix_removals': [],
            'title_split_separators': [],
            'max_courses_per_run': 500,
            'soft_delete_before_scrape': False,
        }
        db.upsert('institution_site_profiles', profile_data, on_conflict='institution_id')
        created_profiles += 1
        summary.append((slug, len(ce_set), 0, len(ce_set)))
    else:
        logger.info(f"  {slug}: NO profile, NO CE patterns (skipped)")

logger.info(f"--- Part 1 Summary ---")
for slug, ce_cnt, sp_cnt, final_cnt in summary:
    logger.info(f"  {slug}: CE={ce_cnt} SP={sp_cnt} -> FINAL={final_cnt}")
logger.info(f"Profiles updated: {merged}")
logger.info(f"Profiles created: {created_profiles}")

# ============================================================
# PART 2: Apply Rich Profile Data (seed_urls, section_keywords, etc.)
# Uses data from seed_site_profiles.py PROFILE definitions
# ============================================================
logger.info("\n=== Part 2: Rich Profile Data ===")

RICH_PROFILES = {
    "universidad-de-lima": {
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "section_mode_map": {"/pregrado/": "Presencial", "/maestria/": "Presencial", "/doctorado/": "Presencial", "/idiomas/": "Presencial", "/cursos-talleres/": "Remoto"},
        "section_course_type_map": {"/pregrado/": "Pregrado", "/maestria/": "Maestria", "/doctorado/": "Doctorado", "/idiomas/": "Curso", "/cursos-talleres/": "Curso"},
        "section_keywords": {"Perfil del egresado": "graduate_profile", "Malla curricular": "curriculum_summary", "Plan de estudios": "curriculum_summary", "Requisitos": "requirements", "Dirigido a": "target_audience", "Inversion": "total_cost_est", "Inicio": "start_date", "Duracion": "duration_text"},
        "field_defaults": {"mode": "Presencial"},
        "title_prefix_removals": ["U. Lima | ", "Universidad de Lima | ", "ULIMA - "],
        "detail_wait_ms": 3000,
        "notes": "102 seed URLs curated. /pregrado/ exclusion removed (Fase 72) — 12 carreras enabled.",
    },
    "universidad-continental": {
        "site_type": "traditional_ssr",
        "field_defaults": {"mode": "Presencial"},
        "notes": "SPA-like pages but SSR accessible."
    },
    "utp": {
        "site_type": "traditional_ssr",
        "field_defaults": {"mode": "Presencial"},
        "notes": "UTP website."
    },
    "upc": {
        "site_type": "spa_js_heavy",
        "field_defaults": {"mode": "Presencial"},
        "detail_wait_ms": 4000,
        "notes": "UPC uses heavy JS rendering."
    },
    "pucp": {
        "site_type": "paginated_catalog",
        "discovery_mode": "paginated_catalog",
        "catalog_url_patterns": ["https://www.pucp.edu.pe/carreras/"],
        "catalog_link_selector": "a.jet-listing-dynamic-image__link",
        "catalog_max_pages": 10,
        "field_defaults": {"mode": "Presencial"},
        "section_keywords": {"Malla curricular": "curriculum_summary", "Perfil de egresado": "graduate_profile", "Plan de estudios": "curriculum_summary"},
        "notes": "PUCP uses paginated catalog with JetEngine listings."
    },
    "idat": {
        "site_type": "spa_js_heavy",
        "field_defaults": {"mode": "Presencial"},
        "detail_wait_ms": 4000,
        "notes": "IDAT uses heavy JS."
    },
    "senati": {
        "site_type": "traditional_ssr",
        "field_defaults": {"mode": "Presencial"},
        "notes": "SENATI website."
    },
    "usil": {
        "site_type": "traditional_ssr",
        "field_defaults": {"mode": "Presencial"},
        "notes": "USIL website."
    },
    "universidad-del-pacifico": {
        "site_type": "traditional_ssr",
        "field_defaults": {"mode": "Presencial"},
        "section_keywords": {"Plan de estudios": "curriculum_summary", "Perfil del egresado": "graduate_profile"},
        "notes": "U. del Pacifico."
    },
    "unmsm": {
        "site_type": "traditional_ssr",
        "field_defaults": {"mode": "Presencial"},
        "notes": "UNMSM."
    },
    "uni": {
        "site_type": "traditional_ssr",
        "field_defaults": {"mode": "Presencial"},
        "notes": "UNI."
    },
}

inst_by_slug = {i['slug']: i for i in institutions}
rich_seeded = 0

for slug, rich in RICH_PROFILES.items():
    if slug not in inst_by_slug:
        logger.warning(f"  SKIP: {slug} not in Pro institutions")
        continue
    inst = inst_by_slug[slug]
    iid = inst['id']

    # Read current profile (preserve exclusions from Part 1)
    current = db.select('institution_site_profiles', filters=f'institution_id=eq.{iid}', columns='*', limit=1)
    if not current:
        logger.warning(f"  SKIP: {slug} no profile found (should have been created in Part 1)")
        continue

    current = current[0]
    update_data = {
        'institution_id': iid,
        'site_type': rich.get('site_type', current.get('site_type', 'traditional_ssr')),
        'discovery_mode': rich.get('discovery_mode', current.get('discovery_mode', 'sitemap_bfs')),
        'section_keywords': rich.get('section_keywords', current.get('section_keywords', {})),
        'field_defaults': rich.get('field_defaults', current.get('field_defaults', {})),
        'section_mode_map': rich.get('section_mode_map', current.get('section_mode_map', {})),
        'section_course_type_map': rich.get('section_course_type_map', current.get('section_course_type_map', {})),
        'title_prefix_removals': rich.get('title_prefix_removals', current.get('title_prefix_removals', [])),
        'title_split_separators': rich.get('title_split_separators', current.get('title_split_separators', [])),
        'detail_wait_ms': rich.get('detail_wait_ms', current.get('detail_wait_ms', 2000)),
        'catalog_url_patterns': rich.get('catalog_url_patterns', current.get('catalog_url_patterns', [])),
        'catalog_link_selector': rich.get('catalog_link_selector', current.get('catalog_link_selector')),
        'catalog_max_pages': rich.get('catalog_max_pages', current.get('catalog_max_pages', 5)),
        'notes': rich.get('notes', current.get('notes')),
        'exclusion_patterns': current.get('exclusion_patterns', []),
        'seed_urls': current.get('seed_urls', []),
        'catalog_scroll_iterations': current.get('catalog_scroll_iterations', 0),
        'requires_stealth': current.get('requires_stealth', False),
        'requires_cloudflare_bypass': current.get('requires_cloudflare_bypass', False),
        'popup_close_selectors': current.get('popup_close_selectors', []),
        'max_courses_per_run': current.get('max_courses_per_run', 500),
        'soft_delete_before_scrape': current.get('soft_delete_before_scrape', False),
    }
    db.upsert('institution_site_profiles', update_data, on_conflict='institution_id')
    n = len(current.get('exclusion_patterns', []) or [])
    logger.info(f"  {inst['name']} ({slug}): enriched profile, exclusions={n}")
    rich_seeded += 1

logger.info(f"\nRich profiles seeded: {rich_seeded}/{len(RICH_PROFILES)}")
logger.info("=== Fase 74 Pro seed COMPLETE ===")
