#!/usr/bin/env python3
"""Apply the cleansing loop fix to the real Supabase Pro project."""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

MIGRATION_FILE = os.path.join(os.path.dirname(__file__), '20260501_fix_cleansing_loop.sql')
PRO_URL = os.environ.get('SUPABASE_PRO_URL', '')
PRO_REF = os.environ.get('SUPABASE_PRO_PROJECT_REF', '')
MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')

if not MGMT_TOKEN or not PRO_REF:
    print("=" * 60)
    print("  ERROR: Credenciales Pro no disponibles en variables de entorno.")
    print()
    print("  Aplica la migracion manualmente en Supabase Dashboard:")
    print(f" 1. Ir a https://supabase.com/dashboard/project/{PRO_REF or 'YOUR_PRO_PROJECT_REF'}/sql/new")
    print("  2. Copiar el contenido de:")
    print(f"     {MIGRATION_FILE}")
    print("  3. Ejecutar el SQL")
    print("=" * 60)
    sys.exit(1)

if not os.path.exists(MIGRATION_FILE):
    print(f"ERROR: No se encuentra {MIGRATION_FILE}")
    sys.exit(1)

with open(MIGRATION_FILE, 'r') as f:
    sql = f.read()

# Remove BEGIN/COMMIT for single-statement execution via API
sql_clean = sql.replace('BEGIN;', '').replace('COMMIT;', '').strip()

print(f"Aplicando migracion a proyecto Pro: {PRO_REF}")
resp = requests.post(
    f"https://api.supabase.com/v1/projects/{PRO_REF}/sql",
    headers={
        "Authorization": f"Bearer {MGMT_TOKEN}",
        "Content-Type": "application/json",
    },
    json={"query": sql_clean},
)

if resp.status_code == 200:
    print("OK: Migracion aplicada correctamente en Pro.")
else:
    print(f"ERROR: {resp.status_code} - {resp.text}")
    print()
    print("Alternativa: aplica manualmente via Supabase Dashboard > SQL Editor.")
    sys.exit(1)
