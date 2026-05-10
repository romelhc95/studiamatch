"""
db_migrate.py — Aplicador universal de migrations SQL para StudIAMatch.

Uso:
  python3 scripts/maintenance/db_migrate.py --env free [--dry-run]
  python3 scripts/maintenance/db_migrate.py --env pro  [--dry-run]

Flujo:
  1. Lee archivos db/migrations/*.sql ordenados por nombre
  2. Consulta supabase_migrations para saber cuáles ya están aplicadas
  3. Para cada archivo NO aplicado:
     a. Lee contenido SQL
     b. Ejecuta via RPC exec_sql()
     c. Si éxito → registra en supabase_migrations
     d. Si falla → aborta (no aplicar parcial)
  4. Reporta resumen

Requisito: La BD debe tener el RPC exec_sql(text) creado (Fase 95).
"""

import os
import sys
import glob
import re
import argparse
import time
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client, _request_with_retry, DNS_RETRY_DELAYS


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "migrations"
)

SUPABASE_MIGRATIONS_TABLE = "supabase_migrations"


def get_applied_migrations(db):
    """Retorna set de nombres de migrations ya aplicadas."""
    try:
        result = db.select(
            SUPABASE_MIGRATIONS_TABLE,
            columns="name",
            limit=1000
        )
        if result and isinstance(result, list):
            return {row.get("name") for row in result if row.get("name")}
    except Exception as e:
        print(f"  [INFO] No se pudo leer {SUPABASE_MIGRATIONS_TABLE}: {e}")
        print(f"  [INFO] Se asumirá que ninguna migration está aplicada.")
    return set()


def extract_name(filepath):
    """Extrae nombre de migration del path: 20260510_descripcion"""
    basename = os.path.basename(filepath)
    return os.path.splitext(basename)[0]


def _exec_sql_direct(db, sql_text):
    """Ejecuta SQL directamente contra la BD usando conexión psycopg2 vía URL.",
    Fallback cuando exec_sql RPC no está disponible (PGRST202 schema cache miss).
    """
    supabase_url = os.environ.get("SUPABASE_URL", "")
    secret_key = os.environ.get("NEXT_SUPABASE_SECRET_KEY", "")
    match = re.match(r"https?://([^.]+)\.supabase\.co", supabase_url)
    if not match or not secret_key:
        return False

    project_ref = match.group(1)
    region = os.environ.get("SUPABASE_REGION", "us-west-1")

    dsn_list = [
        # Pooler (port 6543) — different region variants
        f"postgresql://postgres.{project_ref}:{secret_key}@aws-0-{region}.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{secret_key}@aws-0-us-west-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{secret_key}@aws-0-us-west-2.pooler.supabase.com:6543/postgres",
        # Direct (port 5432)
        f"postgresql://postgres:{secret_key}@db.{project_ref}.supabase.co:5432/postgres",
    ]

    try:
        import psycopg2
        last_err = None
        for dsn in dsn_list:
            try:
                conn = psycopg2.connect(dsn, connect_timeout=8)
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(sql_text)
                cur.close()
                conn.close()
                return True
            except Exception as e:
                last_err = e
                print(f"  ⚠️  DSN {dsn[:60]}... falló: {type(e).__name__}")
                continue
        raise last_err or Exception("All connections failed")
    except ImportError:
        print("  ⚠️  psycopg2 no instalado — no se puede conectar directamente")
    except Exception as e:
        print(f"  ⚠️  Todas las conexiones directas fallaron: {e}")

    return False


def _exec_sql_via_mgmt_api(sql_text):
    """Ejecuta SQL usando la Management API de Supabase (NO necesita PostgREST)."""
    access_token = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    supabase_url = os.environ.get("SUPABASE_URL", "")
    if not access_token or not supabase_url:
        return False

    match = re.match(r"https?://([^.]+)\.supabase\.co", supabase_url)
    if not match:
        return False
    project_ref = match.group(1)

    mgmt_url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(mgmt_url, headers=headers, json={"query": sql_text}, timeout=30)
        if resp.status_code in (200, 201, 204):
            print("  ✅ Ejecutado via Management API")
            return True
        print(f"  ⚠️  Management API: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"  ⚠️  Management API falló: {e}")
    return False


def _exec_sql_with_retry(db, sql, max_retries=2):
    """Ejecuta SQL via RPC exec_sql con reintento y fallback a Management API.
    Si la Management API no está disponible, intenta conexión directa vía psycopg2."""
    for attempt in range(1, max_retries + 1):
        try:
            result = db.rpc_raise("exec_sql", {"sql_text": sql})
            return result
        except Exception as e:
            estr = str(e)
            if 'PGRST202' in estr:
                if attempt < max_retries:
                    print(f"  ⏳ Schema cache no actualizado (PGRST202). Reintento {attempt}/{max_retries}...")
                    time.sleep(3)
                    continue
            print(f"  ❌ ERROR: {e}")
            break

    print("  ⏳ Intentando Management API...")
    if _exec_sql_via_mgmt_api(sql):
        return {"status": "success"}

    print("  ⏳ Intentando conexión directa a la base de datos...")
    if _exec_sql_direct(db, sql):
        print("  ✅ Ejecutado via conexión directa")
        return {"status": "success"}
    print("  ❌ Falló también la conexión directa")
    return None


def apply_migration(db, filepath, dry_run=False):
    """Aplica un archivo SQL como migration. Retorna True si éxito."""
    name = extract_name(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()

    if not sql.strip():
        print(f"  ⚠️  {name} — archivo vacío, se salta")
        return False

    if dry_run:
        print(f"  ⏳ {name} — PENDIENTE (dry-run, no se ejecuta)")
        return True

    print(f"  ⏳ {name} — aplicando...")

    result = _exec_sql_with_retry(db, sql)
    if result is None:
        return False
    print(f"  ✅ {name} — OK")

    try:
        now = datetime.utcnow().isoformat()
        db.insert(SUPABASE_MIGRATIONS_TABLE, [{
            "version": 0,
            "name": name,
            "statements": "",
            "applied_at": now
        }])
    except Exception as e:
        print(f"  ⚠️  {name} — aplicada pero no se pudo registrar: {e}")

    try:
        db.rpc("exec_sql", {"sql_text": "NOTIFY pgrst, 'reload schema';"})
    except Exception:
        pass

    return True


def main():
    parser = argparse.ArgumentParser(description="Aplicador de migrations SQL")
    parser.add_argument("--env", choices=["free", "pro"], default="free",
                        help="Ambiente target: free (desarrollo) o pro (producción)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo listar migrations pendientes sin ejecutar")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  db_migrate.py — Environment: {args.env.upper()}")
    if args.dry_run:
        print(f"  Modo: DRY-RUN (solo diagnóstico)")
    print(f"{'='*60}\n")

    migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    if not migration_files:
        print("  No se encontraron archivos SQL en db/migrations/")
        sys.exit(0)

    print(f"  Archivos encontrados: {len(migration_files)}")
    print()

    os.environ["SUPABASE_ENV"] = args.env
    db = get_db_client()

    applied = get_applied_migrations(db)
    print(f"  Migrations ya aplicadas: {len(applied)}")
    print()

    pending = []
    for f in migration_files:
        name = extract_name(f)
        if name not in applied:
            pending.append(f)

    if not pending:
        print("  ✅ No hay migrations pendientes. Todo al día.")
        sys.exit(0)

    print(f"  Migrations pendientes: {len(pending)}")
    print()

    success_count = 0
    fail_count = 0

    for f in pending:
        ok = apply_migration(db, f, dry_run=args.dry_run)
        if ok:
            success_count += 1
        else:
            fail_count += 1
            if not args.dry_run:
                print(f"\n  🛑 Error aplicando {extract_name(f)}. Abortando.")
                break

    print(f"\n{'='*60}")
    print(f"  RESUMEN:")
    print(f"    Aplicadas:  {success_count}/{len(pending)}")
    print(f"    Errores:    {fail_count}")
    print(f"    Previas:    {len(applied)}")
    print(f"{'='*60}\n")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
