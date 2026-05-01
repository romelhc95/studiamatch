"""
Migrate ALL data from Supabase Free (Dev) to Supabase Pro (Production).
"""

import os, sys, json, time
sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client

MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')
PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
PRO_PROJECT_REF = PRO_URL.replace('https://', '').replace('.supabase.co', '') if PRO_URL else ''
if not all([MGMT_TOKEN, PRO_URL, PRO_KEY]):
    sys.exit('ERROR: Set SUPABASE_MGMT_TOKEN, SUPABASE_PRO_URL, SUPABASE_SERVICE_ROLE_KEY env vars')

import requests
PRO_REST_HEADERS = {
    'apikey': PRO_KEY,
    'Authorization': f'Bearer {PRO_KEY}',
    'Content-Type': 'application/json',
}

def run_mgmt_sql(sql):
    resp = requests.post(
        f'https://api.supabase.com/v1/projects/{PRO_PROJECT_REF}/database/query',
        json={'query': sql},
        headers={'Authorization': f'Bearer {MGMT_TOKEN}', 'Content-Type': 'application/json'}
    )
    return resp

def upsert_pro(table, data, batch_size=200):
    if not data:
        return 0
    inserted = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        clean_batch = []
        for row in batch:
            clean = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    clean[k] = json.dumps(v) if v is not None else None
                else:
                    clean[k] = v
            clean_batch.append(clean)
        
        headers = {**PRO_REST_HEADERS, 'Prefer': 'resolution=merge-duplicates'}
        resp = requests.post(f'{PRO_URL}/rest/v1/{table}', headers=headers, json=clean_batch, timeout=120)
        if resp.status_code in (200, 201):
            inserted += len(batch)
            print(f'  +{inserted}/{len(data)}', end='\r')
        else:
            # Fall back to row-by-row
            for row in clean_batch:
                r = requests.post(f'{PRO_URL}/rest/v1/{table}', headers=headers, json=[row], timeout=60)
                if r.status_code in (200, 201):
                    inserted += 1
                else:
                    print(f'\n  ROW FAIL: {r.status_code} {r.text[:120]}')
        time.sleep(0.3)
    return inserted

def main():
    print('=== DATA MIGRATION: Free -> Pro ===')
    
    PRO_TABLES = [
        'ratings', 'reviews', 'enriched_programs', 'cleansed_programs',
        'staging_raw', 'crawler_exclusions', 'courses',
        'category_rules', 'market_salaries', 'categories', 'institutions'
    ]
    
    # Step 1: DELETE all existing Pro data (cascade-safe order)
    print('\n1. DELETE existing Pro data...')
    for table in PRO_TABLES:
        r = run_mgmt_sql(f'DELETE FROM public."{table}" WHERE 1=1;')
        status = 'OK' if r.status_code == 201 else f'FAIL {r.status_code}'
        print(f'  {status}: {table}')
    
    # Step 2: Load from Free and insert into Pro
    ORDER = [
        'institutions', 'categories', 'market_salaries', 'category_rules',
        'courses', 'crawler_exclusions', 'staging_raw',
        'cleansed_programs', 'enriched_programs', 'ratings', 'reviews'
    ]
    
    print('\n2. Migrate data...')
    db = get_db_client()
    total = 0
    for table in ORDER:
        print(f'\n-- {table} --')
        try:
            data = db.select_all(table)
            print(f'  Loaded {len(data)} records from Free')
        except Exception as e:
            print(f'  SELECT FAIL: {e}')
            continue
        if not data:
            print(f'  Empty (skipping)')
            continue
        ok = upsert_pro(table, data)
        total += ok
        print(f'  Migrated: {ok}/{len(data)}')
    
    # Step 3: Re-enable triggers
    print('\n3. Re-enable triggers...')
    run_mgmt_sql('ALTER TABLE courses ENABLE TRIGGER tr_auto_assign_category;')
    run_mgmt_sql('ALTER TABLE enriched_programs ENABLE TRIGGER tr_enriched_programs_updated_at;')
    print('  Triggers re-enabled')
    
    print(f'\n=== Migration complete: {total} total records ===')

if __name__ == '__main__':
    main()
