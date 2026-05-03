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
        "notes": "102 seed URLs curated. /pregrado/ exclusion removed (Fase 72) — 12 carreras enabled.",
        "seed_urls": [
            "https://www.ulima.edu.pe/pregrado/administracion",
            "https://www.ulima.edu.pe/pregrado/comunicacion",
            "https://www.ulima.edu.pe/pregrado/derecho",
            "https://www.ulima.edu.pe/pregrado/ingenieria-ambiental",
            "https://www.ulima.edu.pe/pregrado/ingenieria-industrial",
            "https://www.ulima.edu.pe/pregrado/ingenieria-de-sistemas",
            "https://www.ulima.edu.pe/pregrado/arquitectura",
            "https://www.ulima.edu.pe/pregrado/contabilidad-y-finanzas",
            "https://www.ulima.edu.pe/pregrado/economia",
            "https://www.ulima.edu.pe/pregrado/ingenieria-civil",
            "https://www.ulima.edu.pe/pregrado/ingenieria-mecatronica",
            "https://www.ulima.edu.pe/pregrado/marketing",
            "https://www.ulima.edu.pe/posgrado/maestria/macp",
            "https://www.ulima.edu.pe/posgrado/maestria/mbf",
            "https://www.ulima.edu.pe/posgrado/maestria/mcdn",
            "https://www.ulima.edu.pe/posgrado/maestria/mcgc",
            "https://www.ulima.edu.pe/posgrado/maestria/mde",
            "https://www.ulima.edu.pe/posgrado/maestria/mdop",
            "https://www.ulima.edu.pe/posgrado/maestria/mdie",
            "https://www.ulima.edu.pe/posgrado/maestria/mgi",
            "https://www.ulima.edu.pe/posgrado/maestria/mgc",
            "https://www.ulima.edu.pe/posgrado/maestria/mid",
            "https://www.ulima.edu.pe/posgrado/maestria/mlp",
            "https://www.ulima.edu.pe/posgrado/maestria/mmgc",
            "https://www.ulima.edu.pe/posgrado/maestria/mtpf",
            "https://www.ulima.edu.pe/posgrado/maestria/mba",
            "https://www.ulima.edu.pe/posgrado/doctorado/da",
            "https://www.ulima.edu.pe/posgrado/doctorado/dc",
            "https://www.ulima.edu.pe/posgrado/doctorado/dge",
            "https://www.ulima.edu.pe/idiomas/programa-integral-ingles",
            "https://www.ulima.edu.pe/idiomas/english-business",
            "https://www.ulima.edu.pe/idiomas/english-media",
            "https://www.ulima.edu.pe/idiomas/english-engineering",
            "https://www.ulima.edu.pe/idiomas/extension-workshops",
            "https://www.ulima.edu.pe/idiomas/intensive-graduation",
            "https://www.ulima.edu.pe/idiomas/b2-first",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-comunicacion-marketing-politico",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-cultura-organizacional",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-presentaciones-alto-impacto",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-alto-impacto-presentaciones",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arbitraje",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-app",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-corporate-compliance",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-legaltech-ia-abogados",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ley-contrataciones-estado",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-obras-impuesto",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-obras-publicas",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-resolucion-conflictos",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-compensacion-total",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-people-analytics",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-domina-tiempo",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-expresate-lidera",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-power-skills",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-soft-skills",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-liderazgo-alto-desempeno",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-fundamental",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-tecnico",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-elaboracion-presupuestos",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-finanzas-no-especialistas",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-tesoreria",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-riesgo-compliance",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-impuesto-renta",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-control-interno",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-niif",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-inversion-bolsa",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-python-aplicado-finanzas",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-fraude-auditoria-forense",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-bloomberg",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-construccion",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-marca-ia",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-growth-hacking",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-marketing-digital",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-kam",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-negociacion-comercial",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-marketing-digital",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-retail-category-management",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-social-media",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-creadores-contenido",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-metodologias-agiles",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-direccion-supply-chain",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-proyectos",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-mejora-rediseno-procesos",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-planeamiento-estrategico",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-seguridad-salud-trabajo",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-future-thinking",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arquitectura-soluciones-digitales",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-business-analytics",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-data-analytics",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-visualizacion-datos-power-bi",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-excel",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gobierno-datos",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-generativa-negocios",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-modernizacion-aplicaciones",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi-desde-cero",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-transformacion-digital",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-fundamentos-power-bi",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-contenido-textual",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-talent-shift",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-transformacion-digital",
            "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-sql-decisiones-negocio"
        ]
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

        profile_data = {
            'institution_id': inst['id'],
            'site_type': profile_cfg.get('site_type', 'traditional_ssr'),
            'discovery_mode': profile_cfg.get('discovery_mode', 'sitemap_bfs'),
            'seed_urls': profile_cfg.get('seed_urls', []),
            'exclusion_patterns': profile_cfg.get('exclusion_patterns', GLOBAL_EXCLUSIONS),
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
        n_exc = len(profile_cfg.get('exclusion_patterns', GLOBAL_EXCLUSIONS))
        logger.info(f"Seeded profile for {inst['name']} ({slug}): {n_exc} exclusions, site_type={profile_cfg['site_type']}")
        seeded += 1

    logger.info(f"Done: {seeded}/{len(PROFILES)} profiles seeded")


if __name__ == '__main__':
    seed()
