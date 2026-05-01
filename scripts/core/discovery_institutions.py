import os
import json
import pathlib
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client

load_dotenv()

db = get_db_client()

# Legacy fallback list (kept for backward compatibility)
LEGACY_SOURCES = [
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

def load_sources():
    """Load institution sources from JSON config file, falling back to legacy list."""
    config_path = pathlib.Path(__file__).parent.parent.parent / "config" / "institution_sources.json"
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                sources = json.load(f)
            if isinstance(sources, list) and len(sources) > 0:
                print(f"INFO: Loaded {len(sources)} institutions from config/institution_sources.json")
                return sources
    except Exception as e:
        print(f"WARN: Failed to load config/institution_sources.json: {e}")

    # Fallback: try loading from institutions table
    try:
        existing = db.select_all('institutions', columns="name,website_url", order="name.asc")
        if existing and len(existing) > 0:
            sources = [{"name": r.get("name"), "url": r.get("website_url")}
                       for r in existing if r.get("website_url")]
            if len(sources) > 0:
                print(f"INFO: Loaded {len(sources)} institutions from database")
                return sources
    except Exception as e:
        print(f"WARN: Failed to load from institutions table: {e}")

    print("WARN: Using legacy hardcoded source list.")
    return LEGACY_SOURCES

def run_discovery():
    print("INFO: Iniciando Descubrimiento de Instituciones Nivel 1...")
    
    sources = load_sources()
    
    found = 0
    for inst in sources:
        # 1. Verificar si ya existe por dominio
        domain = inst['url'].replace('https://', '').replace('http://', '').split('/')[0]
        res_check_data = db.select('institutions', filters=f"website_url=ilike.*{domain}*")
        
        if isinstance(res_check_data, list):
            if len(res_check_data) == 0:
                # 2. Es una institución nueva: Insertar
                slug = inst['name'].lower().replace(' ', '-').replace('.', '')
                data = {
                    "name": inst['name'],
                    "slug": slug,
                    "website_url": inst['url']
                }
                res_insert = db.insert('institutions', data)
                
                if res_insert:
                    print(f"NEW: {inst['name']} añadida al catálogo maestro.")
                    found += 1
                else:
                    print(f"ERROR: Error al insertar {inst['name']}")
            else:
                print(f"SKIP: {inst['name']} ya existe en el catálogo.")
        else:
            print(f"ERROR: Error al verificar {inst['name']}")

    print(f"\nSUCCESS: Descubrimiento finalizado. {found} nuevas instituciones encontradas.")

if __name__ == "__main__":
    run_discovery()
