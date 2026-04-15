import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def run_discovery():
    print("INFO: Iniciando Descubrimiento de Instituciones Nivel 1...")
    
    # Fuente de verdad: Registro de Universidades SUNEDU (Simulación de crawling sobre fuente confiable)
    # En un entorno de producción real, este script navegaría el portal oficial.
    # Aquí implementamos la lógica de conexión y mapeo institucional.
    
    sources = [
        {"name": "Universidad de Lima", "url": "https://www.ulima.edu.pe/"},
        {"name": "Universidad del Pacífico", "url": "https://www.up.edu.pe/"},
        {"name": "IDAT", "url": "https://www.idat.edu.pe/"},
        {"name": "SENATI", "url": "https://www.senati.edu.pe/"},
        {"name": "UPC", "url": "https://www.upc.edu.pe/"},
        {"name": "USIL", "url": "https://www.usil.edu.pe/"},
        {"name": "Universidad Continental", "url": "https://ucontinental.edu.pe/"},
        {"name": "UTP", "url": "https://www.utp.edu.pe/"},
        {"name": "UNMSM", "url": "https://unmsm.edu.pe/"},
        {"name": "UNI", "url": "https://www.uni.edu.pe/"}
    ]
    
    found = 0
    for inst in sources:
        # 1. Verificar si ya existe por dominio
        domain = inst['url'].replace('https://', '').replace('http://', '').split('/')[0]
        check_url = f"{SUPABASE_URL}/rest/v1/institutions?website_url=ilike.*{domain}*"
        res_check = requests.get(check_url, headers=headers)
        
        if res_check.status_code == 200:
            if len(res_check.json()) == 0:
                # 2. Es una institución nueva: Insertar
                slug = inst['name'].lower().replace(' ', '-').replace('.', '')
                data = {
                    "name": inst['name'],
                    "slug": slug,
                    "website_url": inst['url']
                }
                res_insert = requests.post(f"{SUPABASE_URL}/rest/v1/institutions", headers=headers, json=data)
                
                if res_insert.status_code in [201, 204, 200]:
                    print(f"NEW: {inst['name']} añadida al catálogo maestro.")
                    found += 1
                else:
                    print(f"ERROR: Error al insertar {inst['name']}: {res_insert.text}")
            else:
                print(f"SKIP: {inst['name']} ya existe en el catálogo.")
        else:
            print(f"ERROR: Error al verificar {inst['name']}: {res_check.status_code} - {res_check.text}")

    print(f"\nSUCCESS: Descubrimiento finalizado. {found} nuevas instituciones encontradas.")

if __name__ == "__main__":
    run_discovery()
