import os
import json
import pathlib
import re
import sys
import unicodedata
from urllib.parse import quote, urlparse

from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client

load_dotenv()

db = get_db_client()


def source_slug(name):
    normalized = unicodedata.normalize('NFKD', str(name or ''))
    ascii_name = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+', '-', ascii_name.lower()).strip('-')


def load_sources(only_source_slug=None):
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
    if only_source_slug:
        sources = [source for source in sources if source_slug(source.get('name')) == only_source_slug]
        if not sources:
            raise RuntimeError(f"source_slug not found in config/institution_sources.json: {only_source_slug}")
    print(f"INFO: Loaded {len(sources)} institutions from config/institution_sources.json")
    return sources

def run_discovery(source_slug_filter=None, allow_insert=True):
    print("INFO: Iniciando Descubrimiento de Instituciones Nivel 1...")

    sources = load_sources(source_slug_filter)

    found = 0
    failed = 0
    for inst in sources:
        # 1. Verificar si ya existe por dominio
        parsed = urlparse(inst['url'])
        domain = (parsed.hostname or '').lower()
        if not re.fullmatch(r"[a-z0-9.-]+", domain):
            raise RuntimeError(f"invalid institution source domain for {inst['name']}")
        res_check_data = db.select_service_raise(
            'institutions', filters=f"website_url=ilike.*{quote(domain, safe='')}*"
        )

        if isinstance(res_check_data, list):
            if len(res_check_data) == 0:
                if not allow_insert:
                    print(f"ERROR: {inst['name']} no existe en el catálogo y --no-insert está activo")
                    failed += 1
                    continue
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
                    failed += 1
            else:
                print(f"SKIP: {inst['name']} ya existe en el catálogo.")
        else:
            print(f"ERROR: Error al verificar {inst['name']}")
            failed += 1

    print(f"\nSUCCESS: Descubrimiento finalizado. {found} nuevas instituciones encontradas.")
    return 1 if failed else 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run FG1 institution discovery")
    parser.add_argument("--source-slug", help="Optional source slug for a one-source canary run")
    parser.add_argument("--no-insert", action="store_true", help="Fail instead of inserting missing institutions")
    args = parser.parse_args()
    try:
        sys.exit(run_discovery(args.source_slug, allow_insert=not args.no_insert))
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
