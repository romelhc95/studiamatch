"""Add crawler exclusion patterns to both Free and Pro databases.

DEPRECATED (Fase 61): Esta herramienta escribe en crawler_exclusions (tabla legacy).
Ahora usa seed_site_profiles.py para escribir en institution_site_profiles.exclusion_patterns
o apply_noise_exclusions.py que ya migraron a la nueva tabla.

Usage:
  python3 scripts/maintenance/seed_site_profiles.py
  python3 scripts/maintenance/apply_noise_exclusions.py --json noise_audit.json
"""
import os
import sys
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

FREE_URL = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', '')
FREE_KEY = os.environ.get('NEXT_SUPABASE_SECRET_KEY', '') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')
PRO_REF = os.environ.get('SUPABASE_PRO_PROJECT_REF', '')


def _headers(key):
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }


def _find_institution(url, key, identifier):
    h = _headers(key)
    by_slug = requests.get(f'{url}/rest/v1/institutions?slug=eq.{identifier}&select=id,name,slug', headers=h, timeout=15)
    if by_slug.status_code == 200 and by_slug.json():
        return by_slug.json()[0]
    by_name = requests.get(f'{url}/rest/v1/institutions?name=ilike.*{identifier}*&select=id,name,slug', headers=h, timeout=15)
    if by_name.status_code == 200 and by_name.json():
        return by_name.json()[0]
    return None


def _get_existing(url, key, inst_id):
    h = _headers(key)
    r = requests.get(f'{url}/rest/v1/crawler_exclusions?institution_id=eq.{inst_id}&select=pattern', headers=h, timeout=15)
    if r.status_code == 200:
        return {row['pattern'] for row in r.json()}
    return set()


def _insert_exclusions(url, key, inst_id, patterns, reason, dry_run):
    h = _headers(key)
    existing = _get_existing(url, key, inst_id)
    inserted = 0
    skipped = 0
    for p in patterns:
        if p in existing:
            print(f'  SKIP (exists): {p}')
            skipped += 1
            continue
        if dry_run:
            print(f'  [DRY-RUN] INSERT: {p}')
            inserted += 1
            continue
        row = {'institution_id': inst_id, 'pattern': p, 'reason': reason, 'is_active': True}
        r = requests.post(f'{url}/rest/v1/crawler_exclusions', headers=h, json=row, timeout=15)
        if r.status_code in (200, 201):
            print(f'  INSERT: {p}')
            inserted += 1
        else:
            print(f'  FAIL: {p} ({r.status_code} {r.text[:100]})')
            skipped += 1
    return inserted, skipped


def _cleanup_staging(url, key, inst_id, patterns, dry_run):
    h = _headers(key)
    total = 0
    for p in patterns:
        clean = p.strip('/')
        r = requests.get(
            f'{url}/rest/v1/staging_raw?institution_id=eq.{inst_id}&url=ilike.*{clean}*&select=id',
            headers={**h, 'Prefer': 'count=exact'}, timeout=15)
        if r.status_code != 200:
            continue
        count = len(r.json())
        if count == 0:
            continue
        if dry_run:
            print(f'  [DRY-RUN] Would delete {count} staging_raw rows matching {p}')
            total += count
            continue
        rd = requests.delete(
            f'{url}/rest/v1/staging_raw?institution_id=eq.{inst_id}&url=ilike.*{clean}*&select=id',
            headers=h, timeout=15)
        if rd.status_code in (200, 204):
            print(f'  DELETED {count} staging_raw rows matching {p}')
            total += count
        else:
            print(f'  FAIL cleanup {p}: {rd.status_code}')
    return total


def apply_to_db(db_label, url, key, identifier, patterns, reason, dry_run, cleanup):
    if not url or not key:
        print(f'  SKIP {db_label}: missing URL or key env vars')
        return 0, 0

    inst = _find_institution(url, key, identifier)
    if not inst:
        print(f'  SKIP {db_label}: institution "{identifier}" not found')
        return 0, 0

    inst_id = inst['id']
    inst_name = inst['name']
    print(f'\n[{db_label}] {inst_name} (id={inst_id}):')

    inserted, skipped = _insert_exclusions(url, key, inst_id, patterns, reason, dry_run)
    print(f'  Result: {inserted} inserted, {skipped} skipped')

    if cleanup:
        _cleanup_staging(url, key, inst_id, patterns, dry_run)

    return inserted, skipped


def main():
    parser = argparse.ArgumentParser(
        description='Add crawler exclusion patterns to Supabase databases.',
        epilog='Example: python3 scripts/maintenance/add_exclusion.py --institution dmc --pattern /profesores/ /blog/')
    parser.add_argument('--institution', required=True, help='Institution slug or name (e.g. dmc, upc)')
    parser.add_argument('--pattern', required=True, nargs='+', help='One or more URL patterns to exclude (e.g. /profesores/ /blog/)')
    parser.add_argument('--reason', default='Manual exclusion', help='Reason for the exclusion (default: "Manual exclusion")')
    parser.add_argument('--db', choices=['both', 'free', 'pro'], default='both', help='Target database (default: both)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--cleanup', action='store_true', help='Also delete matching staging_raw records')
    args = parser.parse_args()

    if args.dry_run:
        print('>>> DRY-RUN MODE (no changes) <<<')

    total_ins = 0
    total_skip = 0

    if args.db in ('both', 'free'):
        ins, skip = apply_to_db('FREE', FREE_URL, FREE_KEY, args.institution, args.pattern, args.reason, args.dry_run, args.cleanup)
        total_ins += ins
        total_skip += skip

    if args.db in ('both', 'pro'):
        ins, skip = apply_to_db('PRO', PRO_URL, PRO_KEY, args.institution, args.pattern, args.reason, args.dry_run, args.cleanup)
        total_ins += ins
        total_skip += skip

    print(f'\nTotal: {total_ins} inserted, {total_skip} skipped')

    if not args.dry_run and total_ins > 0:
        print('Note: New patterns take effect on the next harvester run.')
        print('Tip: Also add patterns to SPECIFIC dict in seed_crawler_exclusions.py for persistence.')


if __name__ == '__main__':
    main()
