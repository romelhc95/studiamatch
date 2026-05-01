import os, requests, sys, json

token = os.environ.get('SUPABASE_MGMT_TOKEN', '')
PRO_PROJECT_REF = os.environ.get('SUPABASE_PRO_PROJECT_REF', '')
url = f'https://api.supabase.com/v1/projects/{PRO_PROJECT_REF}/database/query'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
if not all([token, PRO_PROJECT_REF]):
    sys.exit('ERROR: Set SUPABASE_MGMT_TOKEN and SUPABASE_PRO_PROJECT_REF env vars')

def run_sql(query, label):
    resp = requests.post(url, json={'query': query}, headers=headers)
    try:
        data = resp.json()
        print(f'{label}: {data}')
    except Exception as e:
        print(f'{label}: HTTP {resp.status_code} - {e}')

run_sql("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename", 'Tables')
run_sql("SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='public' AND routine_type='FUNCTION'", 'RPC count')
run_sql("SELECT extname, extversion FROM pg_extension WHERE extname IN ('pg_trgm','vector','uuid-ossp','pgcrypto')", 'Extensions')
run_sql("SELECT COUNT(*) FROM pg_policy WHERE polrelid IN (SELECT oid FROM pg_class WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public'))", 'RLS policies')
