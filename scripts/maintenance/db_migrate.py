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
import json
import glob
import re
import argparse
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client, _request_with_retry, DNS_RETRY_DELAYS
from shared.supabase_credentials import get_secret_key


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "migrations"
)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUPABASE_MIGRATIONS_TABLE = "supabase_migrations"


def load_environment(target):
    env_file = ".env.gitprod" if target == "pro" else ".env.local"
    load_dotenv(os.path.join(ROOT_DIR, env_file), override=True)

    prefix = "PRO" if target == "pro" else "FREE"
    mappings = {
        "SUPABASE_URL": [f"{prefix}_SUPABASE_URL"],
        "NEXT_PUBLIC_SUPABASE_URL": [f"{prefix}_NEXT_PUBLIC_SUPABASE_URL", f"{prefix}_SUPABASE_URL"],
        "NEXT_SUPABASE_SECRET_KEY": [f"{prefix}_NEXT_SUPABASE_SECRET_KEY"],
        "NEXT_SUPABASE_PUBLISHABLE_KEY": [f"{prefix}_NEXT_SUPABASE_PUBLISHABLE_KEY", f"{prefix}_NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"],
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY": [f"{prefix}_NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", f"{prefix}_NEXT_SUPABASE_PUBLISHABLE_KEY"],
    }
    for canonical, candidates in mappings.items():
        for candidate in candidates:
            value = os.environ.get(candidate)
            if value:
                os.environ[canonical] = value
                break

    if os.environ.get("NEXT_PUBLIC_SUPABASE_URL"):
        os.environ["SUPABASE_URL"] = os.environ["NEXT_PUBLIC_SUPABASE_URL"]

    os.environ["SUPABASE_ENV"] = target


def assert_environment(target):
    required = ["NEXT_SUPABASE_SECRET_KEY"]
    missing = [name for name in required if not os.environ.get(name)]
    if not (os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")):
        missing.append("SUPABASE_URL/NEXT_PUBLIC_SUPABASE_URL")
    if missing:
        raise RuntimeError(f"Faltan credenciales para {target}: {', '.join(missing)}")
    get_secret_key()


def get_applied_migrations(db):
    """Retorna set de nombres de migrations ya aplicadas via PostgREST service key."""
    try:
        result = db._select_api(
            SUPABASE_MIGRATIONS_TABLE,
            filters=None,
            columns="name",
            limit=1000,
            order=None,
            use_service_role=True,
        )
        if result and isinstance(result, list):
            return {row.get("name") for row in result if row.get("name")}
    except Exception as e:
        print(f"  ⚠️  No se pudo leer supabase_migrations: {e}")
    return set()


def extract_name(filepath):
    """Extrae nombre de migration del path: 20260510_descripcion"""
    basename = os.path.basename(filepath)
    return os.path.splitext(basename)[0]


def _exec_sql_with_retry(db, sql, max_retries=2):
    """Ejecuta SQL via RPC exec_sql con reintento."""
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

    print("  ❌ No se pudo ejecutar SQL via exec_sql. No se registra la migration.")
    return None


def _ensure_migration_table(db):
    """Crea supabase_migrations si no existe usando exec_sql."""
    for attempt in range(2):
        try:
            db.rpc_raise("exec_sql", {
                "sql_text": f"CREATE TABLE IF NOT EXISTS public.{SUPABASE_MIGRATIONS_TABLE} (version BIGINT NOT NULL, name TEXT PRIMARY KEY, statements TEXT DEFAULT '', applied_at TIMESTAMPTZ DEFAULT now());"
            })
            return
        except Exception:
            if attempt == 0:
                time.sleep(3)


def _try_register_migration(db, name):
    """Registra migration como aplicada en supabase_migrations.
    Si PostgREST falla, se reporta y la siguiente corrida la volvera a listar."""
    now = datetime.utcnow().isoformat()
    try:
        _ensure_migration_table(db)
        try:
            db.insert(SUPABASE_MIGRATIONS_TABLE, [{
                "version": 0, "name": name, "statements": "", "applied_at": now
            }])
        except Exception as e:
            print(f"  ⚠️  No se pudo registrar migration {name}: {e}")
    except Exception as e:
        print(f"  ⚠️  No se pudo asegurar supabase_migrations: {e}")


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

    _try_register_migration(db, name)

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
    parser.add_argument("--only", action="append", default=[],
                        help="Aplicar/listar solo migrations cuyo nombre coincida exactamente. Repetible.")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  db_migrate.py — Environment: {args.env.upper()}")
    if args.dry_run:
        print(f"  Modo: DRY-RUN (solo diagnóstico)")
    print(f"{'='*60}\n")

    migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    if args.only:
        wanted = set(args.only)
        migration_files = [f for f in migration_files if extract_name(f) in wanted]
        found = {extract_name(f) for f in migration_files}
        missing = sorted(wanted - found)
        if missing:
            print(f"  🛑 Migrations solicitadas no existen: {missing}")
            sys.exit(1)
    if not migration_files:
        print("  No se encontraron archivos SQL en db/migrations/")
        sys.exit(0)

    print(f"  Archivos encontrados: {len(migration_files)}")
    print()

    load_environment(args.env)
    assert_environment(args.env)
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
    if args.dry_run:
        print(f"    Pendientes listadas: {success_count}/{len(pending)}")
        print(f"    Aplicadas:           0 (dry-run)")
    else:
        print(f"    Aplicadas:  {success_count}/{len(pending)}")
    print(f"    Errores:    {fail_count}")
    print(f"    Previas:    {len(applied)}")
    print(f"{'='*60}\n")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
