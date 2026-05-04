"""Fase 71: Sincronizar Pro → Free — migración de datos del pipeline con mapeo de UUIDs
   Las credenciales se leen de variables de entorno (NUNCA hardcodear).
   Pro: SUPABASE_URL + NEXT_SUPABASE_SECRET_KEY desde .env.gitprod (AGENTS.md §102-107)
   Free: db_client.py lee de .env.local"""
import sys, os, json, requests, argparse

sys.path.insert(0, '/app')


def _read_env_file(filepath, var_name, default=''):
    """Lee una variable de un archivo .env sin contaminar os.environ."""
    if not os.path.exists(filepath):
        return os.environ.get(var_name, default)
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue
            k, _, v = line.partition('=')
            if k.strip() == var_name:
                return v.strip().strip('"').strip("'")
    return os.environ.get(var_name, default)


root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_gitprod = os.path.join(root_dir, '.env.gitprod')

PRO_URL = _read_env_file(env_gitprod, 'SUPABASE_URL', '')
PRO_KEY = _read_env_file(env_gitprod, 'NEXT_SUPABASE_SECRET_KEY', '')

if not PRO_URL or not PRO_KEY:
    print("ERROR: Credenciales Pro no encontradas.")
    print("Opción 1: Tener .env.gitprod (gitignored) en la raíz del proyecto con:")
    print("  SUPABASE_URL='https://xxx.supabase.co'")
    print("  NEXT_SUPABASE_SECRET_KEY='sb_secret_xxx'")
    print("Opción 2: Exportar variables antes de ejecutar:")
    print("  export SUPABASE_URL='https://xxx.supabase.co'")
    print("  export NEXT_SUPABASE_SECRET_KEY='sb_secret_xxx'")
    sys.exit(1)

# Remove Pro vars from env so db_client can load Free creds from .env.local
for _v in ('SUPABASE_URL', 'NEXT_PUBLIC_SUPABASE_URL', 'NEXT_SUPABASE_SECRET_KEY', 'NEXT_SUPABASE_PUBLISHABLE_KEY'):
    os.environ.pop(_v, None)

PRO_HEADERS = {
    'apikey': PRO_KEY,
    'Authorization': f'Bearer {PRO_KEY}',
    'Content-Type': 'application/json',
}

from scripts.shared.db_client import get_db_client
db = get_db_client()

PAGE_SIZE = 1000
BATCH_SIZE = 200
EXCLUDE_KEYS = ('id', 'created_at', 'updated_at')
TABLES = ['staging_raw', 'cleansed_programs', 'enriched_programs', 'courses']


def _paginate_get(url):
    all_rows = []
    offset = 0
    while True:
        h = {**PRO_HEADERS, 'Range': f'{offset}-{offset + PAGE_SIZE - 1}', 'Prefer': 'count=exact'}
        r = requests.get(url, headers=h, timeout=30)
        if r.status_code in (200, 206):
            rows = r.json()
            if rows:
                all_rows.extend(rows)
                offset += PAGE_SIZE
            else:
                break
        elif r.status_code == 416:
            break
        else:
            print(f"  HTTP {r.status_code} at offset {offset}: {r.text[:100]}")
            break
    return all_rows


def _build_uuid_map(source_list, key_field='slug'):
    return {r[key_field]: r['id'] for r in (source_list or [])}


def _pro_to_free_map(pro_list, free_map, key_field='slug'):
    m = {}
    for r in (pro_list or []):
        k = r.get(key_field)
        if k and k in free_map:
            m[r['id']] = free_map[k]
    return m


def _translate_field(row, field, uuid_map):
    old = row.get(field)
    if old and old in uuid_map:
        row[field] = uuid_map[old]
    return row


def _clean_row(row):
    return {k: v for k, v in row.items() if k not in EXCLUDE_KEYS}


def count_free(table):
    try:
        if table in ('staging_raw', 'cleansed_programs', 'enriched_programs'):
            url = f"{db.supabase_url}/rest/v1/{table}?select=count"
            h = db._get_headers(use_service_role=True)
            h["Prefer"] = "count=exact"
            r = requests.get(url, headers=h, timeout=15)
            if r.status_code == 200:
                cr = r.headers.get("content-range", "")
                if "/" in cr:
                    return int(cr.split("/")[-1])
            return '?'
        return db.count(table)
    except Exception:
        return '?'


def sync_table(name, pro_data, on_conflict, uuid_map=None, cat_map=None, zero_cleansed=False, use_insert=False):
    if not pro_data:
        print(f"  SKIP: {name} — 0 rows from Pro")
        return 0

    total = len(pro_data)
    ok = 0
    for i in range(0, total, BATCH_SIZE):
        batch = pro_data[i:i + BATCH_SIZE]
        cleaned = []
        for row in batch:
            r = _clean_row(row)
            if uuid_map:
                _translate_field(r, 'institution_id', uuid_map)
            if cat_map:
                _translate_field(r, 'category_id', cat_map)
            if zero_cleansed:
                r['cleansed_id'] = None
            cleaned.append(r)

        if use_insert:
            for row in cleaned:
                r2 = db.insert(name, row)
                if r2:
                    ok += 1
        else:
            r2 = db.upsert(name, cleaned, on_conflict=on_conflict)
            if r2:
                ok += len(cleaned)
        suffix = '\n' if ok >= total else ''
        print(f"  {name}: {ok}/{total}", end=suffix)
    return ok


def dry_run_table(name, pro_data, free_count):
    n_pro = len(pro_data)
    print(f"  {name}: Pro={n_pro} Free={free_count} → sync {n_pro} rows")
    return n_pro


def main():
    parser = argparse.ArgumentParser(description='Sync Pro → Free: migration pipeline data with UUID mapping')
    parser.add_argument('--dry-run', action='store_true', help='Preview counts and mapping without writing')
    parser.add_argument('--table', choices=TABLES + ['all'], default='all', help='Table to sync (default: all)')
    parser.add_argument('--truncate-staging', action='store_true', help='Truncate staging_raw in Free before inserting')
    args = parser.parse_args()

    # ============ Phase 1: Build UUID maps ============
    print("=== 1. Construyendo mapas de UUIDs ===")
    free_insts = db.select('institutions', columns='id,slug')
    pro_insts = _paginate_get(f"{PRO_URL}/rest/v1/institutions?select=id,slug")
    if not pro_insts:
        print("ERROR: No institutions found in Pro (¿SUPABASE_URL correcta?)")
        sys.exit(1)
    print(f"  Free institutions: {len(free_insts)} | Pro institutions: {len(pro_insts)}")

    free_inst_by_slug = _build_uuid_map(free_insts, 'slug')
    inst_uuid_map = _pro_to_free_map(pro_insts, free_inst_by_slug, 'slug')
    print(f"  Institution UUID mapping: {len(inst_uuid_map)}/{len(pro_insts)} matched")

    free_cats = db.select('categories', columns='id,name')
    pro_cats = _paginate_get(f"{PRO_URL}/rest/v1/categories?select=id,name")
    if free_cats:
        free_cat_by_name = _build_uuid_map(free_cats, 'name')
        cat_uuid_map = _pro_to_free_map(pro_cats, free_cat_by_name, 'name')
        print(f"  Category UUID mapping: {len(cat_uuid_map)}/{len(pro_cats) if pro_cats else 0} matched")
    else:
        cat_uuid_map = {}
        print(f"  Category UUID mapping: 0 (no categories in Free)")

    if args.dry_run:
        for slug, free_id in sorted(free_inst_by_slug.items()):
            pro_id = None
            for p in (pro_insts or []):
                if p['slug'] == slug:
                    pro_id = p['id']
                    break
            match = "OK" if pro_id and pro_id in inst_uuid_map else "MISS"
            print(f"  {match} {slug}: Free={free_id[:8]}... Pro={pro_id[:8] if pro_id else 'N/A'}...")

    # ============ Phase 2: Read & Sync ============
    if args.table == 'all':
        targets = TABLES
        print(f"\n=== 2. Sincronizando todas las tablas ===")
    else:
        targets = [args.table]
        print(f"\n=== 2. Sincronizando {args.table} ===")

    for table in targets:
        print(f"\n--- {table} ---")
        free_count = count_free(table)
        pro_data = _paginate_get(f"{PRO_URL}/rest/v1/{table}?select=*")

        if not pro_data:
            print(f"  SKIP: 0 rows in Pro")
            continue

        if args.dry_run:
            dry_run_table(table, pro_data, free_count)
            continue

        if table == 'staging_raw' and args.truncate_staging:
            print(f"  Truncando staging_raw en Free...")
            try:
                db.delete('staging_raw', '1=eq.1')
                print(f"  Truncado OK")
            except Exception as e:
                print(f"  WARN: truncate falló: {e}")

        if table == 'courses':
            ok = sync_table(table, pro_data, 'url', inst_uuid_map, cat_uuid_map)
        elif table == 'enriched_programs':
            ok = sync_table(table, pro_data, 'url', inst_uuid_map, zero_cleansed=True, use_insert=True)
        else:
            ok = sync_table(table, pro_data, 'url', inst_uuid_map)

        print(f"  DONE: {table} — {ok}/{len(pro_data)}")

    # ============ Summary ============
    if not args.dry_run and args.table == 'all':
        print(f"\n=== 3. Verificación post-sync ===")
        for table in TABLES:
            after = count_free(table)
            print(f"  {table}: {after} filas en Free")


if __name__ == '__main__':
    main()
