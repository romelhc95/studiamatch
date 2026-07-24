"""Diagnose schema differences between Free and Pro for all tables"""
import os, sys, requests, json
sys.path.insert(0, '/app')
from scripts.shared.db_client import DatabaseClient
from scripts.shared.supabase_credentials import (
    build_supabase_headers,
    get_environment_credentials,
    require_distinct_environments,
)

FREE = get_environment_credentials("FREE")
PRO = get_environment_credentials("PRO")
require_distinct_environments(FREE, PRO)
PRO_URL, PRO_KEY = PRO.url, PRO.secret_key
MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')
PRO_PROJECT_REF = PRO_URL.replace('https://', '').replace('.supabase.co', '') if PRO_URL else ''
if not MGMT_TOKEN:
    sys.exit('ERROR: Set SUPABASE_MGMT_TOKEN')

db = DatabaseClient(FREE.url, FREE.secret_key)

tables = ['institutions', 'courses', 'categories', 'crawler_exclusions',
          'staging_raw', 'cleansed_programs', 'enriched_programs',
          'market_salaries', 'category_rules', 'ratings', 'reviews', 'leads']

for table in tables:
    # Get Free columns from data
    free_data = db.select_service(table, limit=1)
    free_cols = set(free_data[0].keys()) if free_data else set()
    
    # Get Pro columns from sample
    r = requests.get(PRO_URL + "/rest/v1/" + table + "?limit=1",
                     headers=build_supabase_headers(PRO_KEY, kind="secret", content_type=False), timeout=10)
    pro_cols = set(r.json()[0].keys()) if r.status_code == 200 and r.json() else set()
    
    if not pro_cols:
        # Try schema via mgmt API
        r2 = requests.post(
            f'https://api.supabase.com/v1/projects/{PRO_PROJECT_REF}/database/query',
            json={'query': 'SELECT column_name FROM information_schema.columns WHERE table_schema = \'public\' AND table_name = \'' + table + '\' ORDER BY ordinal_position;'},
            headers={'Authorization': 'Bearer ' + MGMT_TOKEN, 'Content-Type': 'application/json'}, timeout=10)
        if r2.status_code == 201:
            pro_cols = {row['column_name'] for row in r2.json()}
    
    missing_in_pro = free_cols - pro_cols
    extra_in_pro = pro_cols - free_cols
    
    print(table + ":")
    print("  Free: " + str(len(free_cols)) + " cols, Pro: " + str(len(pro_cols)) + " cols")
    if missing_in_pro:
        print("  MISSING in Pro: " + str(sorted(missing_in_pro)))
    if extra_in_pro:
        print("  EXTRA in Pro: " + str(sorted(extra_in_pro)))
    if free_cols == pro_cols:
        print("  MATCH")
    print()
