import os
import json
import pathlib
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client

load_dotenv()

db = get_db_client()

def load_sources():
    """Load institution sources from the versioned JSON config, fail-closed."""
    config_path = pathlib.Path(__file__).parent.parent.parent / "config" / "institution_sources.json"
    if not config_path.exists():
        raise RuntimeError("config/institution_sources.json is required")
    with open(config_path, 'r', encoding='utf-8') as f:
        sources = json.load(f)
    if not isinstance(sources, list) or not sources:
        raise RuntimeError("config/institution_sources.json must be a non-empty list")
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise RuntimeError(f"institution source #{index} must be an object")
        name = str(source.get('name') or '').strip()
        url = str(source.get('url') or '').strip()
        parsed = urlparse(url)
        if not name or parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise RuntimeError(f"institution source #{index} must include name and http(s) url")
    print(f"INFO: Loaded {len(sources)} institutions from config/institution_sources.json")
    return sources

def run_discovery():
    print("INFO: Iniciando Descubrimiento de Instituciones Nivel 1...")

    sources = load_sources()

    found = 0
    for inst in sources:
        # 1. Verificar si ya existe por dominio
        domain = inst['url'].replace('https://', '').replace('http://', '').split('/')[0]
        res_check_data = db.select_service_raise(
            'institutions', filters=f"website_url=ilike.*{domain}*"
        )

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
    return 0

if __name__ == "__main__":
    try:
        sys.exit(run_discovery())
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
