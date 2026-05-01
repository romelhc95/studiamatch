"""Diagnose schema differences between Free and Pro for all tables"""
import sys, requests, json
sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client

PRO_URL = 'https://zogdcvlqxanzqbvkkdar.supabase.co'
PRO_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZ2RjdmxxeGFuenFidmtrZGFyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjE4OTM4NSwiZXhwIjoyMDkxNzY1Mzg1fQ.A2PcyM_AgHPE9GvTgZo1tacENC5FW8uEFUIBbx4gjlI'
MGMT_TOKEN = 'sbp_dd5873314717846f1a47c44dce2b1b36bb3487bb'

db = get_db_client()

tables = ['institutions', 'courses', 'categories', 'crawler_exclusions',
          'staging_raw', 'cleansed_programs', 'enriched_programs',
          'market_salaries', 'category_rules', 'ratings', 'reviews', 'leads']

for table in tables:
    # Get Free columns from data
    free_data = db.select(table, limit=1)
    free_cols = set(free_data[0].keys()) if free_data else set()
    
    # Get Pro columns from sample
    r = requests.get(PRO_URL + "/rest/v1/" + table + "?limit=1",
                     headers={"apikey": PRO_KEY, "Authorization": "Bearer " + PRO_KEY}, timeout=10)
    pro_cols = set(r.json()[0].keys()) if r.status_code == 200 and r.json() else set()
    
    if not pro_cols:
        # Try schema via mgmt API
        r2 = requests.post(
            'https://api.supabase.com/v1/projects/zogdcvlqxanzqbvkkdar/database/query',
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
