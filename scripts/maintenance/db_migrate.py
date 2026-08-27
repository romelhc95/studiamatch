"""
db_migrate.py — Aplicador universal de migrations SQL para StudIAMatch.

Uso:
  python3 scripts/maintenance/db_migrate.py --env free [--dry-run]
  python3 scripts/maintenance/db_migrate.py --env pro --manifest <name> [--dry-run]

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
import hashlib
import argparse
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client, _request_with_retry, DNS_RETRY_DELAYS
from shared.supabase_credentials import get_secret_key


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "migrations"
)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRO_MIGRATION_MANIFESTS = {
    "f10-8-atomic-cleansing-provenance": (
        "20260808_fase10_8_atomic_cleansing_provenance",
    ),
    "h2-expand-compat": (
        "20260827_h2_pro_expand_schema_compat",
        "20260827_h2_pro_seed_editorial_field_definitions",
        "20260827_h2_pro_backfill_editorial_state",
        "20260827_h2_pro_capture_legacy_cohort",
        "20260827_h2_pro_enable_legacy_cohort_rls",
    ),
    "h2-contract-public-reader": (
        "20260827_h2_pro_contract_public_reader",
    ),
    "h2-contract-legacy-cohort": (
        "20260827_h2_pro_contract_legacy_cohort",
    ),
    "h2-rollback-public-reader-contract": (
        "20260827_h2_pro_rollback_public_reader_contract",
    ),
}
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SUPABASE_MIGRATIONS_TABLE = "supabase_migrations"
PRO_PROJECT_REF = "xwhtiqmboljkshrtviyw"


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
    if target == "pro":
        active_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
        expected_host = f"{PRO_PROJECT_REF}.supabase.co"
        parsed = urlparse(active_url)
        if parsed.scheme != "https" or parsed.hostname != expected_host or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise RuntimeError(f"Pro target must be pinned to {expected_host}")
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
        if isinstance(result, list):
            return {row.get("name") for row in result if row.get("name")}
    except Exception as e:
        raise RuntimeError(f"No se pudo leer supabase_migrations: {e}") from e

    raise RuntimeError("No se pudo leer supabase_migrations: respuesta vacia o invalida")


def extract_name(filepath):
    """Extrae nombre de migration del path: 20260510_descripcion"""
    basename = os.path.basename(filepath)
    return os.path.splitext(basename)[0]


def resolve_requested_migrations(args, parser):
    if args.env != "pro":
        if args.manifest:
            parser.error("--manifest solo esta permitido con --env pro")
        return tuple(args.only)

    if args.only:
        parser.error("--only no esta permitido con --env pro; usa --manifest")
    if not args.manifest:
        parser.error("--manifest es obligatorio para Pro")
    if args.manifest not in PRO_MIGRATION_MANIFESTS:
        allowed = ", ".join(sorted(PRO_MIGRATION_MANIFESTS))
        parser.error(f"manifest Pro no permitido: {args.manifest}. Permitidos: {allowed}")

    return PRO_MIGRATION_MANIFESTS[args.manifest]


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
            return True
        except Exception as e:
            raise RuntimeError(f"No se pudo registrar migration {name}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"No se pudo asegurar supabase_migrations: {e}") from e


def _sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def render_migration_sql(name, sql):
    replacements = {
        "__H2_EXPECTED_ELIGIBLE_COUNT__": os.environ.get("H2_EXPECTED_ELIGIBLE_COUNT", ""),
        "__H2_EXPECTED_COHORT_DIGEST__": os.environ.get("H2_EXPECTED_COHORT_DIGEST", ""),
        "__H2_PAYLOAD_SHA__": os.environ.get("H2_PAYLOAD_SHA", "unknown"),
        "__H2_AUTHORIZATION_ID__": os.environ.get("H2_AUTHORIZATION_ID", os.environ.get("DDL_AUTHORIZATION_ID", "unknown")),
    }
    rendered = sql
    for token, value in replacements.items():
        if token in rendered:
            if not value:
                raise RuntimeError(f"{token} requerido para aplicar {name}")
            rendered = rendered.replace(token, str(value))
    return rendered


def build_atomic_migration_sql(name, sql):
    settings = []
    setting_map = {
        "app.h2_expected_eligible_count": os.environ.get("H2_EXPECTED_ELIGIBLE_COUNT"),
        "app.h2_expected_cohort_digest": os.environ.get("H2_EXPECTED_COHORT_DIGEST"),
        "app.h2_payload_sha": os.environ.get("H2_PAYLOAD_SHA", "unknown"),
        "app.h2_authorization_id": os.environ.get("H2_AUTHORIZATION_ID", os.environ.get("DDL_AUTHORIZATION_ID", "unknown")),
    }
    if name.startswith("20260827_h2_pro_"):
        for key, value in setting_map.items():
            if value:
                settings.append(f"SELECT set_config({_sql_literal(key)}, {_sql_literal(value)}, true);")
    return "\n".join([
        f"CREATE TABLE IF NOT EXISTS public.{SUPABASE_MIGRATIONS_TABLE} (version BIGINT NOT NULL, name TEXT PRIMARY KEY, statements TEXT DEFAULT '', applied_at TIMESTAMPTZ DEFAULT now());",
        *settings,
        sql,
        (
            f"INSERT INTO public.{SUPABASE_MIGRATIONS_TABLE} (version, name, statements, applied_at) "
            f"VALUES (0, {_sql_literal(name)}, '', now()) "
            "ON CONFLICT (name) DO NOTHING;"
        ),
    ])


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

    sql = render_migration_sql(name, sql)
    result = _exec_sql_with_retry(db, build_atomic_migration_sql(name, sql))
    if result is None:
        return False

    try:
        db.rpc("exec_sql", {"sql_text": "NOTIFY pgrst, 'reload schema';"})
    except Exception:
        pass

    return True


def resolve_migration_files(requested_migrations):
    if not requested_migrations:
        return sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))

    migration_files = []
    missing = []
    for name in requested_migrations:
        filepath = os.path.join(MIGRATIONS_DIR, f"{name}.sql")
        if os.path.exists(filepath):
            migration_files.append(filepath)
        else:
            missing.append(name)
    if missing:
        print(f"  🛑 Migrations solicitadas no existen: {missing}")
        sys.exit(1)
    return migration_files


def _select_all_with_role(db, table, columns, *, use_service_role):
    rows = []
    offset = 0
    limit = 1000
    while True:
        url = f"{db.supabase_url}/rest/v1/{table}?select={columns}&limit={limit}&offset={offset}"
        res = _request_with_retry(
            requests.get,
            url,
            headers=db._get_headers(use_service_role=use_service_role),
            timeout=30,
        )
        if res.status_code != 200:
            raise RuntimeError(
                f"No se pudo leer {table} para preflight H2: {res.status_code} {(res.text or '')[:200]}"
            )
        page = res.json() if res.content else []
        rows.extend(page)
        if len(page) < limit:
            return rows
        offset += limit


def _select_service_all(db, table, columns):
    return _select_all_with_role(db, table, columns, use_service_role=True)


def _select_public_all(db, table, columns):
    return _select_all_with_role(db, table, columns, use_service_role=False)


def assert_h2_expand_preapply_guard(db):
    expected_count_raw = os.environ.get("H2_EXPECTED_ELIGIBLE_COUNT")
    expected_digest = os.environ.get("H2_EXPECTED_COHORT_DIGEST")
    if not expected_count_raw or not expected_digest:
        raise RuntimeError(
            "H2_EXPECTED_ELIGIBLE_COUNT y H2_EXPECTED_COHORT_DIGEST son obligatorios "
            "antes de aplicar h2-expand-compat"
        )
    try:
        expected_count = int(expected_count_raw)
    except ValueError as exc:
        raise RuntimeError(f"H2_EXPECTED_ELIGIBLE_COUNT invalido: {expected_count_raw}") from exc
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_digest):
        raise RuntimeError("H2_EXPECTED_COHORT_DIGEST debe tener formato sha256:<64 hex chars>")

    public_ids = sorted(row["id"] for row in _select_public_all(db, "courses", "id") if row.get("id"))
    courses = _select_service_all(db, "courses", "id,institution_id,is_active,is_verified,url")
    profiles = _select_service_all(db, "institution_site_profiles", "institution_id,production_enabled,notes")
    production_institutions = {
        row.get("institution_id")
        for row in profiles
        if row.get("institution_id")
        and row.get("production_enabled") is True
        and (row.get("notes") or "") != "DB_AS_CODE_RELEASE_CANARY"
    }
    eligible_ids = sorted(
        row["id"]
        for row in courses
        if row.get("id")
        and row.get("institution_id") in production_institutions
        and row.get("is_active") is True
        and row.get("is_verified") is True
        and not (row.get("url") or "").startswith("https://canary.invalid/")
    )
    if public_ids != eligible_ids:
        raise RuntimeError(
            "H2 Pro pre-apply public visibility drift: "
            f"public={len(public_ids)} eligible={len(eligible_ids)}"
        )
    actual_digest = "sha256:" + hashlib.sha256(",".join(public_ids).encode("utf-8")).hexdigest()
    if len(public_ids) != expected_count or actual_digest != expected_digest:
        raise RuntimeError(
            "H2 Pro pre-apply cohort drift: "
            f"expected count/digest {expected_count}/{expected_digest}, "
            f"got {len(public_ids)}/{actual_digest}"
        )


def main():
    parser = argparse.ArgumentParser(description="Aplicador de migrations SQL")
    parser.add_argument("--env", choices=["free", "pro"], default="free",
                        help="Ambiente target: free (desarrollo) o pro (producción)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo listar migrations pendientes sin ejecutar")
    parser.add_argument("--only", action="append", default=[],
                        help="Aplicar/listar solo migrations cuyo nombre coincida exactamente. Repetible.")
    parser.add_argument("--manifest", choices=sorted(PRO_MIGRATION_MANIFESTS),
                        help="Manifiesto cerrado de migrations Pro. Obligatorio con --env pro.")
    args = parser.parse_args()
    requested_migrations = resolve_requested_migrations(args, parser)

    print(f"\n{'='*60}")
    print(f"  db_migrate.py — Environment: {args.env.upper()}")
    if args.manifest:
        print(f"  Manifest: {args.manifest}")
    if args.dry_run:
        print(f"  Modo: DRY-RUN (solo diagnóstico)")
    print(f"{'='*60}\n")

    migration_files = resolve_migration_files(requested_migrations)
    if not migration_files:
        print("  No se encontraron archivos SQL en db/migrations/")
        sys.exit(0)

    print(f"  Archivos encontrados: {len(migration_files)}")
    print()

    load_environment(args.env)
    db = None
    applied = set()
    try:
        assert_environment(args.env)
        db = get_db_client()
        applied = get_applied_migrations(db)
    except Exception as e:
        if not args.dry_run:
            raise
        if args.env == "pro" and os.environ.get("GITHUB_ACTIONS") == "true":
            raise RuntimeError(f"Dry-run Pro en CI requiere ledger remoto accesible: {e}") from e
        print(f"  ⚠️  Dry-run offline: no se pudo consultar ledger remoto ({e})")
        print("  ⚠️  Se listan todas las migrations solicitadas como pendientes offline")
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

    if args.env == "pro" and args.manifest == "h2-expand-compat" and not args.dry_run:
        assert_h2_expand_preapply_guard(db)

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
