import sys
import os
import json

sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client
from scripts.shared.utils import setup_lima_logging

logger = setup_lima_logging('seed_site_profiles')

PROFILES = [
    {
        "slug": "universidad-de-lima",
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "section_mode_map": {"/pregrado/": "Presencial", "/maestria/": "Presencial", "/doctorado/": "Presencial", "/idiomas/": "Presencial", "/cursos-talleres/": "Remoto"},
        "section_course_type_map": {"/pregrado/": "Pregrado", "/maestria/": "Maestria", "/doctorado/": "Doctorado", "/idiomas/": "Curso", "/cursos-talleres/": "Curso"},
        "section_keywords": {"Perfil del egresado": "graduate_profile", "Malla curricular": "curriculum_summary", "Plan de estudios": "curriculum_summary", "Requisitos": "requirements", "Dirigido a": "target_audience", "Inversión": "total_cost_est", "Inicio": "start_date", "Duración": "duration_text"},
        "field_defaults": {"mode": "Presencial"},
        "title_prefix_removals": ["U. Lima | ", "Universidad de Lima | ", "ULIMA - "],
        "detail_wait_ms": 3000,
        "notes": "136 seed URLs by section. Avoid /noticias/, /agradecimiento/, /thank-you-page/"
    },
    {
        "slug": "universidad-continental",
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "notes": "SPA-like pages but SSR accessible. 3 seed URLs for discovery."
    },
    {
        "slug": "utp",
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "notes": "UTP website. 3 seed URLs for discovery."
    },
    {
        "slug": "upc",
        "site_type": "spa_js_heavy",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "detail_wait_ms": 4000,
        "notes": "UPC uses heavy JS rendering. Playwright required for full extraction."
    },
    {
        "slug": "pucp",
        "site_type": "paginated_catalog",
        "discovery_mode": "paginated_catalog",
        "catalog_url_patterns": ["https://www.pucp.edu.pe/carreras/"],
        "catalog_link_selector": "a.jet-listing-dynamic-image__link",
        "catalog_max_pages": 10,
        "field_defaults": {"mode": "Presencial"},
        "section_keywords": {"Malla curricular": "curriculum_summary", "Perfil de egresado": "graduate_profile", "Plan de estudios": "curriculum_summary"},
        "notes": "PUCP uses paginated catalog with JetEngine listings. Extract links from catalog page."
    },
    {
        "slug": "idat",
        "site_type": "spa_js_heavy",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "detail_wait_ms": 4000,
        "notes": "IDAT uses heavy JS. 9 seed URLs."
    },
    {
        "slug": "senati",
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "notes": "SENATI website. 3 seed URLs."
    },
    {
        "slug": "usil",
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "notes": "USIL website. 3 seed URLs. Previously failed — may need stealth."
    },
    {
        "slug": "universidad-del-pacifico",
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "section_keywords": {"Plan de estudios": "curriculum_summary", "Perfil del egresado": "graduate_profile"},
        "notes": "U. del Pacifico. Already in Golden Path."
    },
    {
        "slug": "unmsm",
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "notes": "UNMSM. Minimal data expected."
    },
    {
        "slug": "uni",
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "field_defaults": {"mode": "Presencial"},
        "notes": "UNI. Minimal data expected."
    },
]

GLOBAL_EXCLUSIONS = [
    ".pdf", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico",
    ".mp4", ".mp3", ".avi", ".mov", ".wmv",
    ".css", ".js", ".json", ".xml",
    "/about/", "/admision/", "/archive/", "/assets/", "/author/",
    "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/",
    "/contacto/", "/eventos/", "/faq/", "/feed/", "/img/",
    "/login", "/media/", "/nosotros/", "/noticias/", "/page/",
    "/politica/", "/privacidad/", "/register/", "/rss/", "/search/",
    "/static/", "/tag/", "/agradecimiento/", "/thank-you-page/",
    "/publicaciones/"
]


def migrate_exclusions_to_profile(db, institution_id):
    rows = db.select('crawler_exclusions',
                     filters=f"institution_id=eq.{institution_id},is_active=eq.true",
                     columns='pattern')
    if not rows:
        return GLOBAL_EXCLUSIONS
    inst_patterns = [r['pattern'] for r in rows]
    return GLOBAL_EXCLUSIONS + inst_patterns


def seed():
    db = get_db_client()
    institutions = db.select('institutions', columns='id,name,slug')
    if not institutions:
        logger.error("No institutions found")
        return

    inst_map = {i['slug']: i for i in institutions}
    seeded = 0

    for profile_cfg in PROFILES:
        slug = profile_cfg['slug']
        if slug not in inst_map:
            logger.warning(f"Institution not found: {slug}")
            continue

        inst = inst_map[slug]
        exclusions = migrate_exclusions_to_profile(db, inst['id'])

        profile_data = {
            'institution_id': inst['id'],
            'site_type': profile_cfg.get('site_type', 'traditional_ssr'),
            'discovery_mode': profile_cfg.get('discovery_mode', 'sitemap_bfs'),
            'seed_urls': profile_cfg.get('seed_urls', []),
            'exclusion_patterns': exclusions,
            'catalog_url_patterns': profile_cfg.get('catalog_url_patterns', []),
            'catalog_link_selector': profile_cfg.get('catalog_link_selector'),
            'catalog_max_pages': profile_cfg.get('catalog_max_pages', 5),
            'catalog_scroll_iterations': profile_cfg.get('catalog_scroll_iterations', 0),
            'requires_stealth': profile_cfg.get('requires_stealth', False),
            'requires_cloudflare_bypass': profile_cfg.get('requires_cloudflare_bypass', False),
            'warmup_url': profile_cfg.get('warmup_url'),
            'popup_close_selectors': profile_cfg.get('popup_close_selectors', []),
            'detail_wait_ms': profile_cfg.get('detail_wait_ms', 2000),
            'section_keywords': profile_cfg.get('section_keywords', {}),
            'field_defaults': profile_cfg.get('field_defaults', {}),
            'section_mode_map': profile_cfg.get('section_mode_map', {}),
            'section_course_type_map': profile_cfg.get('section_course_type_map', {}),
            'title_prefix_removals': profile_cfg.get('title_prefix_removals', []),
            'title_split_separators': profile_cfg.get('title_split_separators', []),
            'price_regex': profile_cfg.get('price_regex'),
            'duration_regex': profile_cfg.get('duration_regex'),
            'max_courses_per_run': profile_cfg.get('max_courses_per_run', 500),
            'soft_delete_before_scrape': profile_cfg.get('soft_delete_before_scrape', False),
            'notes': profile_cfg.get('notes'),
        }

        result = db.upsert('institution_site_profiles', profile_data, on_conflict='institution_id')
        logger.info(f"Seeded profile for {inst['name']} ({slug}): {len(exclusions)} exclusions, site_type={profile_cfg['site_type']}")
        seeded += 1

    logger.info(f"Done: {seeded}/{len(PROFILES)} profiles seeded")


if __name__ == '__main__':
    seed()
