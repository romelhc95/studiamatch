import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN ---
# Desarrollo (Free)
DEV_URL = os.getenv("SUPABASE_URL") 
DEV_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") 

# Producción (Pro)
PROD_URL = "https://zogdcvlqxanzqbvkkdar.supabase.co"
PROD_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") 

headers_dev = {"apikey": DEV_KEY, "Authorization": f"Bearer {DEV_KEY}"}
headers_prod = {"apikey": PROD_KEY, "Authorization": f"Bearer {PROD_KEY}", "Content-Type": "application/json"}

def migrate_institutions():
    print("[MIGRATION] Obteniendo instituciones de Desarrollo...")
    res = requests.get(f"{DEV_URL}/rest/v1/institutions?select=*", headers=headers_dev)
    if res.status_code != 200:
        print(f"[ERROR] leyendo Dev: {res.text}")
        return
    
    institutions = res.json()
    print(f"[INFO] Encontradas {len(institutions)} instituciones.")

    print("[INFO] Migrando a Producción...")
    for inst in institutions:
        res_push = requests.post(f"{PROD_URL}/rest/v1/institutions", headers=headers_prod, json=inst)
        if res_push.status_code in [201, 204, 409]: 
            print(f"[OK] {inst['name']} sincronizada.")
        else:
            print(f"[WARNING] Error con {inst['name']}: {res_push.text}")

if __name__ == "__main__":
    migrate_institutions()
