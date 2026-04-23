import os
import requests
from dotenv import load_dotenv

# Configuración
load_dotenv(".env.local")
url = os.getenv("SUPABASE_URL") or "https://fmcxwoqvxatbrawwtqke.supabase.co"
# Necesitamos el Service Role Key para cambios de esquema si hay una RPC, 
# pero intentaremos ver si podemos enviar un PATCH que falle con un error descriptivo 
# o simplemente informar la sentencia SQL.
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"--- Diagnóstico de Base de Datos ---")
print(f"URL: {url}")

sql_query = "ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_late_enrollment_request BOOLEAN DEFAULT false;"

print(f"\nSentencia SQL para ejecutar en el panel de Supabase (SQL Editor):")
print("-" * 50)
print(sql_query)
print("-" * 50)

# Intentar verificar si la columna ya existe consultando un registro
headers = {
    "apikey": os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY"),
    "Authorization": f"Bearer {os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')}"
}

res = requests.get(f"{url}/rest/v1/leads?limit=1", headers=headers)
if res.status_code == 200:
    data = res.json()
    if data and "is_late_enrollment_request" in data[0]:
        print("\n✅ La columna 'is_late_enrollment_request' YA EXISTE.")
    else:
        print("\n❌ La columna 'is_late_enrollment_request' NO EXISTE aún.")
else:
    print(f"\n⚠️ No se pudo verificar la existencia de la columna: {res.status_code}")
