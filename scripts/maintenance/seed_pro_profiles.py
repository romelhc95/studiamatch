import sys
import os
import json
import requests

sys.path.insert(0, '/app')

PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', os.environ.get('NEXT_SUPABASE_SECRET_KEY', ''))

if not PRO_URL or not PRO_KEY:
    print("ERROR: SUPABASE_PRO_URL and service_role key required")
    sys.exit(1)

headers_service = {
    'apikey': PRO_KEY,
    'Authorization': f'Bearer {PRO_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}
headers_anon = {
    'apikey': PRO_KEY,
    'Authorization': f'Bearer {PRO_KEY}',
    'Content-Type': 'application/json'
}

PROFILES = [
    {"slug": "universidad-de-lima", "site_type": "traditional_ssr", "discovery_mode": "hardcoded_urls"},
    {"slug": "universidad-continental", "site_type": "traditional_ssr", "discovery_mode": "sitemap_bfs"},
    {"slug": "utp", "site_type": "traditional_ssr", "discovery_mode": "sitemap_bfs"},
    {"slug": "upc", "site_type": "spa_js_heavy", "discovery_mode": "sitemap_bfs"},
    {"slug": "idat", "site_type": "spa_js_heavy", "discovery_mode": "sitemap_bfs"},
    {"slug": "senati", "site_type": "traditional_ssr", "discovery_mode": "sitemap_bfs"},
    {"slug": "usil", "site_type": "traditional_ssr", "discovery_mode": "sitemap_bfs"},
    {"slug": "universidad-del-pacifico", "site_type": "traditional_ssr", "discovery_mode": "sitemap_bfs"},
    {"slug": "unmsm", "site_type": "traditional_ssr", "discovery_mode": "sitemap_bfs"},
    {"slug": "uni", "site_type": "traditional_ssr", "discovery_mode": "sitemap_bfs"},
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


def get_inst_exclusions(inst_id):
    url = f"{PRO_URL}/rest/v1/crawler_exclusions?institution_id=eq.{inst_id}&is_active=eq.true&select=pattern"
    r = requests.get(url, headers=headers_anon)
    if r.status_code == 200 and r.json():
        return GLOBAL_EXCLUSIONS + [row['pattern'] for row in r.json()]
    return GLOBAL_EXCLUSIONS


def seed_pro():
    url = f"{PRO_URL}/rest/v1/institutions?select=id,name,slug&order=name"
    r = requests.get(url, headers=headers_anon)
    institutions = r.json()
    inst_map = {i['slug']: i for i in institutions}

    for p in PROFILES:
        slug = p['slug']
        if slug not in inst_map:
            print(f"SKIP: {slug} not found in Pro")
            continue
        inst = inst_map[slug]
        exclusions = get_inst_exclusions(inst['id'])

        data = {
            'institution_id': inst['id'],
            'site_type': p['site_type'],
            'discovery_mode': p['discovery_mode'],
            'exclusion_patterns': exclusions,
        }
        upsert_url = f"{PRO_URL}/rest/v1/institution_site_profiles?on_conflict=institution_id"
        r = requests.post(upsert_url, headers={**headers_service, 'Prefer': 'resolution=merge-duplicates,return=representation'}, json=data)
        if r.status_code in (200, 201):
            print(f"OK: {inst['name']} — {len(exclusions)} exclusions")
        else:
            print(f"ERR: {inst['name']} — {r.status_code}: {r.text[:200]}")

    print("Done seeding Pro profiles")


if __name__ == '__main__':
    seed_pro()
