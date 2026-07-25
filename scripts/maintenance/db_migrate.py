"""
db_migrate.py — Aplicador universal de migrations SQL para StudIAMatch.

Uso:
  python3 scripts/maintenance/db_migrate.py --env free --manifest <path> [--dry-run]
  python3 scripts/maintenance/db_migrate.py --env pro --manifest <path> [--dry-run]

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
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client, _request_with_retry, DNS_RETRY_DELAYS
from shared.supabase_credentials import get_secret_key
from maintenance.migration_manifest import (
    ManifestError,
    canonical_sql_sha256,
    load_manifest,
)


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "migrations"
)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUPABASE_MIGRATIONS_TABLE = "supabase_migrations"
PACKAGE_POSTCONDITIONS = {
    "20260724_fase06_g1b_reconciliation": "public.verify_fase06_g1b_reconciliation()",
    "20260724_fase06_hito1_editorial_contract": "public.verify_fase06_hito1_contract()",
    "20260725_fase07_g1b_closure": "public.verify_fase07_g1b_closure()",
}
MANIFEST_ONLY_PREFIXES = ("20260724_fase06_", "20260725_fase07_")


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
    """Return the complete auxiliary ledger and fail closed on API errors."""
    rows = []
    offset = 0
    page_size = 1000
    while True:
        url = (
            f"{db.supabase_url}/rest/v1/{SUPABASE_MIGRATIONS_TABLE}"
            f"?select=name,statements&order=name.asc&limit={page_size}&offset={offset}"
        )
        try:
            response = requests.get(
                url,
                headers=db._get_headers(use_service_role=True),
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"No se pudo leer supabase_migrations: {exc}") from exc
        if response.status_code not in (200, 206):
            raise RuntimeError(
                "No se pudo leer supabase_migrations: "
                f"HTTP {response.status_code}"
            )
        try:
            page = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "supabase_migrations no devolvio JSON valido"
            ) from exc
        if not isinstance(page, list):
            raise RuntimeError("supabase_migrations no devolvio una lista valida")
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += len(page)

    ledger = {}
    for row in rows:
        name = row.get("name") if isinstance(row, dict) else None
        statements = row.get("statements") if isinstance(row, dict) else None
        if not isinstance(name, str) or not name:
            raise RuntimeError("supabase_migrations contiene una fila invalida")
        if name in ledger:
            raise RuntimeError(f"supabase_migrations duplica el nombre {name}")
        ledger[name] = statements if isinstance(statements, str) else ""
    return ledger


def extract_name(filepath):
    """Extrae nombre de migration del path: 20260510_descripcion"""
    basename = os.path.basename(filepath)
    return os.path.splitext(basename)[0]


def select_legacy_migrations(only=None):
    """Resolve non-F6 migrations while keeping F6 behind its manifest."""
    migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    wanted = set(only or [])
    if wanted:
        migration_files = [f for f in migration_files if extract_name(f) in wanted]
        found = {extract_name(f) for f in migration_files}
        missing = sorted(wanted - found)
        if missing:
            raise ValueError(f"Migrations solicitadas no existen: {missing}")
    if any(
        extract_name(path).casefold().startswith(MANIFEST_ONLY_PREFIXES)
        for path in migration_files
    ):
        raise ManifestError("Las migrations FASE-06/07 requieren --manifest")
    return migration_files


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
    last_error = None
    for attempt in range(2):
        try:
            db.rpc_raise("exec_sql", {
                "sql_text": f"CREATE TABLE IF NOT EXISTS public.{SUPABASE_MIGRATIONS_TABLE} (version BIGINT NOT NULL, name TEXT PRIMARY KEY, statements TEXT DEFAULT '', applied_at TIMESTAMPTZ DEFAULT now());"
            })
            return
        except Exception as e:
            last_error = e
            if attempt == 0:
                time.sleep(3)
    raise RuntimeError("No se pudo asegurar supabase_migrations") from last_error


def _sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def _file_sha256(filepath):
    return canonical_sql_sha256(Path(filepath))


def verify_applied_postcondition(db, migration_name):
    verifier = PACKAGE_POSTCONDITIONS.get(migration_name)
    if verifier is None:
        raise RuntimeError(f"Falta verificador para {migration_name}")
    rpc_name = verifier.removeprefix("public.").removesuffix("()")
    if db.rpc_raise(rpc_name, {}) is not True:
        raise RuntimeError(f"Postcondicion fallida: {migration_name}")


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

    _ensure_migration_table(db)
    version = int(datetime.utcnow().strftime("%Y%m%d%H%M%S"))
    checksum_marker = f"sha256:{_file_sha256(filepath)}"
    verifier = PACKAGE_POSTCONDITIONS.get(name)
    if name.casefold().startswith(MANIFEST_ONLY_PREFIXES) and verifier is None:
        raise RuntimeError(f"Falta verificador transaccional para {name}")
    verification = ""
    if verifier:
        verification = (
            "\nDO $fase06_verify$ BEGIN "
            f"IF NOT {verifier} THEN "
            f"RAISE EXCEPTION {_sql_literal(f'Postcondicion fallida: {name}')}; "
            "END IF; END; $fase06_verify$;"
        )
    registration = (
        f"\nINSERT INTO public.{SUPABASE_MIGRATIONS_TABLE} "
        "(version, name, statements, applied_at) VALUES ("
        f"{version}, {_sql_literal(name)}, {_sql_literal(checksum_marker)}, "
        "pg_catalog.now()) "
        "ON CONFLICT (name) DO NOTHING;"
    )
    result = _exec_sql_with_retry(db, sql + verification + registration)
    if result is None:
        return False

    if get_applied_migrations(db).get(name) != checksum_marker:
        raise RuntimeError(f"La migration {name} no quedo registrada")

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
    parser.add_argument(
        "--manifest",
        help="Manifest cerrado con paths y checksums de migrations autorizadas.",
    )
    args = parser.parse_args()

    if args.env == "pro" and not args.manifest:
        parser.error("--manifest es obligatorio para Pro")
    if args.manifest and args.only:
        parser.error("--manifest y --only no se pueden combinar")

    print(f"\n{'='*60}")
    print(f"  db_migrate.py — Environment: {args.env.upper()}")
    if args.dry_run:
        print(f"  Modo: DRY-RUN (solo diagnóstico)")
    print(f"{'='*60}\n")

    if args.manifest:
        try:
            migration_files = [
                str(path)
                for path in load_manifest(
                    Path(args.manifest),
                    args.env,
                    required_status=(
                        "free_certified"
                        if args.env == "pro"
                        else ("ready_for_free", "free_certified")
                    ),
                )
            ]
        except ManifestError as exc:
            print(f"  🛑 Manifest invalido: {exc}")
            sys.exit(2)
    else:
        try:
            migration_files = select_legacy_migrations(args.only)
        except ValueError as exc:
            print(f"  🛑 {exc}")
            sys.exit(1)
        except ManifestError as exc:
            print(f"  🛑 {exc}")
            sys.exit(2)
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
        if name in applied and args.manifest:
            expected_marker = f"sha256:{_file_sha256(f)}"
            if applied[name] != expected_marker:
                print(f"  🛑 Ledger/checksum mismatch para {name}")
                sys.exit(2)
            try:
                verify_applied_postcondition(db, name)
            except RuntimeError as exc:
                print(f"  🛑 {exc}")
                sys.exit(2)
        elif name not in applied:
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
