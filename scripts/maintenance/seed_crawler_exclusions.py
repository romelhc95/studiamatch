import os, sys, json, requests
sys.path.insert(0, '/app')

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', '')
secret = os.environ.get('NEXT_SUPABASE_SECRET_KEY', '') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
if not url or not secret:
    sys.exit('ERROR: Set NEXT_PUBLIC_SUPABASE_URL and NEXT_SUPABASE_SECRET_KEY')

h = {'apikey': secret, 'Authorization': f'Bearer {secret}', 'Content-Type': 'application/json'}

r = requests.get(f'{url}/rest/v1/institutions?select=id,name,slug', headers=h, timeout=15)
if r.status_code != 200:
    sys.exit(f'FAIL: {r.status_code} {r.text[:200]}')
insts = r.json()
by_slug = {i['slug']: i for i in insts}
by_name = {i['name'].lower(): i for i in insts}

def inst_id(slug_or_name):
    i = by_slug.get(slug_or_name) or by_name.get(slug_or_name.lower())
    return i['id'] if i else None

GLOBAL = [
    '/noticias/', '/blog/', '/eventos/', '/categoria/',
    '/tag/', '/tags/', '/author/', '/archive/', '/page/',
    '/login', '/register/', '/search/', '/carrito/',
    '/wp-content/', '/wp-json/', '/feed/', '/rss/',
    '/politica/', '/terminos/', '/privacidad/', '/faq/',
    '/contacto/', '/nosotros/', '/about/',
    '/transparencia/', '/biblioteca/', '/admision/',
    '/media/', '/assets/', '/static/', '/img/',
]

CMS = ['/category/', '/author/']  # /tag/ and /archive/ already in GLOBAL

SPECIFIC = {
    'universidad-de-lima': ['/pregrado/', '/blog-tags/', '/ventana-indiscreta/',
        '/node/', '/promociones/', '/taxonomy/', '/la-universidad/',
        '/centros-e-institutos/', '/internacional/'],
    'upc': ['/pregrado/', '/vida-universitaria/', '/info-importante/'],
    'usil': ['/pregrado/', '/vida-universitaria/'],
    'universidad-del-pacifico': ['/egp/', '/idiomas/', '/maestrias/'],
    'utp': ['/pregrado/', '/vida-universitaria/'],
    'uni': ['/index.php/'],
    'universidad-continental': ['/uc-global/'],
    'unmsm': ['/pregrado/', '/facultad/', '/laboratorio/'],
    'idat': ['/pregrado/'],
    'senati': ['/pregrado/'],
}

DMC = ['/profesores/', '/egresado/', '/legales/', '/termino-y-condicion-/',
       '/categoria-termino-y-condicion/', '/etiqueta-producto/',
       '/programa-libre/', '/termino-y-condicion/']

all_rows = []

# Build all rows first, deduplicate by (institution_id, pattern)
seen = set()
for inst in insts:
    for p in GLOBAL:
        key = (inst['id'], p)
        if key not in seen:
            seen.add(key)
            all_rows.append({'institution_id': inst['id'], 'pattern': p, 'reason': 'Static exclusion (Phase 49)'})
    for p in CMS:
        key = (inst['id'], p)
        if key not in seen:
            seen.add(key)
            all_rows.append({'institution_id': inst['id'], 'pattern': p, 'reason': 'CMS directory block (Phase 49)'})

for slug, patterns in SPECIFIC.items():
    iid = inst_id(slug)
    if iid:
        for p in patterns:
            key = (iid, p)
            if key not in seen:
                seen.add(key)
                all_rows.append({'institution_id': iid, 'pattern': p, 'reason': 'Noise AI-Sentinel'})

dmc = inst_id('dmc')
if dmc:
    for p in DMC:
        key = (dmc, p)
        if key not in seen:
            seen.add(key)
            all_rows.append({'institution_id': dmc, 'pattern': p, 'reason': 'DMC Exclusion Cascade'})
else:
    print('DMC institution not found, skipping DMC patterns')

print(f'Total rows to insert: {len(all_rows)}')

# Batch insert with upsert
batch_size = 100
ok = 0
for i in range(0, len(all_rows), batch_size):
    batch = all_rows[i:i+batch_size]
    r = requests.post(f'{url}/rest/v1/crawler_exclusions?on_conflict=institution_id,pattern',
                      headers={**h, 'Prefer': 'resolution=merge-duplicates'},
                      json=batch, timeout=60)
    if r.status_code in (200, 201, 204):
        ok += len(batch)
        print(f'  {ok}/{len(all_rows)}', end='\r')
    else:
        print(f'\nFAIL batch {i}: {r.status_code} {r.text[:200]}')

print(f'\nInserted: {ok}/{len(all_rows)}')

# Verify
r = requests.get(f'{url}/rest/v1/crawler_exclusions?select=count&limit=0',
                 headers={**h, 'Prefer': 'count=exact'}, timeout=15)
cr = r.headers.get('content-range', '?')
print(f'Total in DB: {cr.split("/")[-1] if "/" in cr else "?"} exclusion patterns')