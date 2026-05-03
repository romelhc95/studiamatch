"""Fase 74: Preventive cleanup — now writes to institution_site_profiles.exclusion_patterns (JSONB)"""
import os, sys, json, requests

sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client

db = get_db_client()

INST_SLUGS = [
    "universidad-de-lima",
    "universidad-del-pacifico",
    "dmc",
    "idat",
]

GLOBAL_PATTERNS = [
    "/category/", "/author/", "/tag/", "/archive/",
    "politicas-de-privacidad", "terminos-y-condiciones", "libro-de-reclamaciones",
    "/transparencia/", "/empleabilidad/"
]

print("--- Registrando Exclusiones Preventivas (en perfiles) ---")

institutions = db.select('institutions', columns='id,slug')
inst_map = {i['slug']: i for i in institutions} if institutions else {}

profiles = db.select('institution_site_profiles', columns='institution_id,exclusion_patterns')
profile_map = {p['institution_id']: p for p in profiles} if profiles else {}

for slug in INST_SLUGS:
    if slug not in inst_map:
        print(f"SKIP: {slug} not found")
        continue
    inst = inst_map[slug]
    iid = inst['id']

    if iid not in profile_map:
        print(f"SKIP: {slug} has no profile")
        continue

    current = profile_map[iid]
    current_patterns = set(current.get('exclusion_patterns', []) or [])
    new_patterns = set(GLOBAL_PATTERNS)

    if new_patterns - current_patterns:
        merged = sorted(current_patterns | new_patterns)
        merged = [str(p).strip() for p in merged if p and isinstance(p, (str, int))]
        merged = list(set(merged))[:500]
        result = db.patch('institution_site_profiles', f'institution_id=eq.{iid}', {
            'exclusion_patterns': merged
        })
        added = len(new_patterns - current_patterns)
        print(f"OK: {slug} — added {added} patterns, total={len(merged)}")
    else:
        print(f"OK: {slug} — already has all patterns ({len(current_patterns)})")

print("\n--- De-dup (unchanged legacy logic, uses db_client) ---")
courses = db.select('courses', columns='id,url,institution_id')
if courses:
    url_map = {}
    for c in courses:
        clean_url = c['url'].rstrip('/')
        key = (c['institution_id'], clean_url)
        if key not in url_map:
            url_map[key] = []
        url_map[key].append(c)

    deleted = 0
    for (iid, clean_url), records in url_map.items():
        if len(records) > 1:
            print(f"  Dup detected: {clean_url}")
            for to_delete in records[1:]:
                db.delete('courses', f"id=eq.{to_delete['id']}")
                deleted += 1
    print(f"\nDe-dup complete: {deleted} duplicates removed")
else:
    print("No courses to de-dup")

print("\nDone")
