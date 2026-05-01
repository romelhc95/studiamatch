import os, requests, json, sys

token = os.environ.get('SUPABASE_MGMT_TOKEN', '')
PRO_PROJECT_REF = os.environ.get('SUPABASE_PRO_PROJECT_REF', '')
url = f'https://api.supabase.com/v1/projects/{PRO_PROJECT_REF}/database/query'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
if not all([token, PRO_PROJECT_REF]):
    sys.exit('ERROR: Set SUPABASE_MGMT_TOKEN and SUPABASE_PRO_PROJECT_REF env vars')

with open('/app/db/migrations/20260501_production_full_replace.sql', 'r') as f:
    sql = f.read()

start = sql.index('DROP FUNCTION IF EXISTS lock_staging_records')
end = sql.index('-- ============================================================', start + 300)
rpc_sql = sql[start:end].strip()

fns = rpc_sql.replace('CREATE OR REPLACE FUNCTION', '|||CREATE OR REPLACE FUNCTION').split('|||')

success = 0
for i, fn in enumerate(fns):
    fn = fn.strip()
    if not fn:
        continue
    resp = requests.post(url, json={'query': fn}, headers=headers)
    if resp.status_code in (200, 201):
        success += 1
        name = fn[fn.index('FUNCTION') + 9:fn.index('(')]
        print(f'OK [{i+1}]: {name.strip()}')
    else:
        print(f'FAIL [{i+1}] (HTTP {resp.status_code}): {resp.text[:150]}')

total = len([f for f in fns if f.strip()])
print(f'\nCreated {success}/{total} RPC functions')
sys.exit(0 if success == total else 1)
