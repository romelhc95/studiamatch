"""
db_migrate.py — Aplicador universal de migrations SQL para StudIAMatch.

Uso:
  python3 scripts/maintenance/db_migrate.py --env free [--dry-run]
  python3 scripts/maintenance/db_migrate.py --env pro --manifest PATH \
    --expected-manifest-sha256 SHA256 [--dry-run]

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
import hashlib
import argparse
import time
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client
from shared.supabase_credentials import get_secret_key


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "migrations"
)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUPABASE_MIGRATIONS_TABLE = "supabase_migrations"
EXPECTED_PROJECT_REFS = {
    "free": "aqrldlmlszjtgpqiegaa",
    "pro": "xwhtiqmboljkshrtviyw",
}


def _file_sha256(path):
    with open(path, "rb") as source:
        return hashlib.sha256(source.read()).hexdigest()


def migration_entries_from_manifest(
    manifest_path,
    target,
    expected_sha256=None,
    root_dir=ROOT_DIR,
    transactional=True,
):
    """Return the exact, ordered migration package authorized by a manifest."""
    path = Path(manifest_path).resolve()
    root = Path(root_dir).resolve()
    if path != root and root not in path.parents:
        raise RuntimeError("El manifest debe estar dentro del repositorio")
    if expected_sha256 and _file_sha256(path) != expected_sha256:
        raise RuntimeError("Checksum del manifest distinto al autorizado")
    with open(path, "r", encoding="utf-8") as source:
        manifest = json.load(source)

    entries = []
    seen = set()
    for item in manifest.get("migrations", []):
        if target not in item.get("targets", []):
            continue
        if item.get("transactional") is not transactional:
            continue
        relative_path = item.get("path", "")
        migration_path = (root / relative_path).resolve()
        migrations_root = (root / "db" / ("migrations" if transactional else "nontransactional")).resolve()
        if migrations_root not in migration_path.parents or migration_path.suffix != ".sql":
            raise RuntimeError(f"Path de migration invalido: {relative_path}")
        if relative_path in seen:
            raise RuntimeError(f"Migration duplicada en manifest: {relative_path}")
        seen.add(relative_path)
        if not migration_path.is_file():
            raise RuntimeError(f"Migration inexistente: {relative_path}")
        if _file_sha256(migration_path) != item.get("sha256"):
            raise RuntimeError(f"Checksum distinto para migration: {relative_path}")
        entries.append({**item, "absolute_path": str(migration_path)})
    return manifest, entries


def load_environment(target, root_dir=ROOT_DIR):
    env_file = ".env.gitprod" if target == "pro" else ".env.local"
    load_dotenv(os.path.join(root_dir, env_file), override=False)

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
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
    expected_host = f"{EXPECTED_PROJECT_REFS[target]}.supabase.co"
    if urlparse(url).hostname != expected_host:
        raise RuntimeError(f"URL de {target} no corresponde al project ref autorizado")


def get_applied_migrations(db):
    """Return ledger rows and fail closed on any API or shape error."""
    result = {}
    offset = 0
    while True:
        url = (
            f"{db.supabase_url}/rest/v1/{SUPABASE_MIGRATIONS_TABLE}"
            f"?select=name,statements&order=name.asc&limit=1000&offset={offset}"
        )
        response = requests.get(url, headers=db._get_headers(use_service_role=True), timeout=30)
        if response.status_code != 200:
            raise RuntimeError(
                f"No se pudo leer {SUPABASE_MIGRATIONS_TABLE}: HTTP {response.status_code}"
            )
        rows = response.json()
        if not isinstance(rows, list):
            raise RuntimeError("El ledger de migrations devolvio una forma invalida")
        for row in rows:
            name = row.get("name")
            if not name or name in result:
                raise RuntimeError("El ledger contiene nombres vacios o duplicados")
            result[name] = row.get("statements") or ""
        if len(rows) < 1000:
            return result
        offset += 1000


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


def _sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def apply_migration(db, entry, release_metadata=None, dry_run=False):
    """Aplica un archivo SQL como migration. Retorna True si éxito."""
    filepath = entry["absolute_path"]
    name = extract_name(filepath)
    content = Path(filepath).read_bytes()
    actual_sha256 = hashlib.sha256(content).hexdigest()
    expected_sha256 = entry["sha256"]
    if actual_sha256 != expected_sha256:
        print(f"  ❌ Checksum cambio antes de aplicar {name}")
        return False
    sql = content.decode("utf-8")
    executable_sql = "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )
    has_transaction_control = re.search(
        r"(?im)^\s*(BEGIN|COMMIT|ROLLBACK)\s*;\s*$", executable_sql
    )
    if has_transaction_control or re.search(r"\bCONCURRENTLY\b", executable_sql, re.IGNORECASE):
        print(f"  ❌ {name} contiene control transaccional o CONCURRENTLY no permitido")
        return False

    if not sql.strip():
        print(f"  ⚠️  {name} — archivo vacío, se salta")
        return False

    if dry_run:
        print(f"  ⏳ {name} — PENDIENTE (dry-run, no se ejecuta)")
        return True

    print(f"  ⏳ {name} — aplicando...")
    metadata = {
        "sha256": expected_sha256,
        **(release_metadata or {}),
    }
    ledger_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    atomic_sql = (
        f"{sql.rstrip()};\n"
        f"INSERT INTO public.{SUPABASE_MIGRATIONS_TABLE} "
        "(version, name, statements, applied_at) VALUES "
        f"(0, {_sql_literal(name)}, {_sql_literal(ledger_json)}, pg_catalog.now());"
    )
    result = _exec_sql_with_retry(db, atomic_sql)
    if result is None:
        return False
    applied = get_applied_migrations(db)
    try:
        recorded = json.loads(applied[name])
    except (KeyError, TypeError, json.JSONDecodeError):
        print(f"  ❌ El ledger no registro metadata valida para {name}")
        return False
    if recorded.get("sha256") != expected_sha256:
        print(f"  ❌ El ledger registro un checksum distinto para {name}")
        return False

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
    parser.add_argument("--manifest",
                        help="Manifest que fija orden, target y checksum de cada migration")
    parser.add_argument("--expected-manifest-sha256",
                        help="Checksum del manifest autorizado por el aprobador")
    parser.add_argument("--repo-root", default=ROOT_DIR,
                        help="Checkout candidato que contiene manifest y migrations")
    args = parser.parse_args()

    if args.only and args.manifest:
        parser.error("--only y --manifest son mutuamente excluyentes")
    if args.env == "pro" and not args.manifest:
        parser.error("Pro solo puede recibir un paquete fijado con --manifest")
    if args.env == "pro" and not args.expected_manifest_sha256:
        parser.error("Pro requiere --expected-manifest-sha256")

    print(f"\n{'='*60}")
    print(f"  db_migrate.py — Environment: {args.env.upper()}")
    if args.dry_run:
        print(f"  Modo: DRY-RUN (solo diagnóstico)")
    print(f"{'='*60}\n")

    root_dir = str(Path(args.repo_root).resolve())
    release_manifest = None
    if args.manifest:
        try:
            release_manifest, migration_entries = migration_entries_from_manifest(
                args.manifest, args.env, args.expected_manifest_sha256, root_dir
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            print(f"  🛑 Manifest rechazado: {exc}")
            sys.exit(1)
        if args.env == "pro" and not migration_entries:
            print("  No hay migrations transaccionales para Pro en este manifest")
            sys.exit(0)
    else:
        migration_entries = [
            {
                "absolute_path": path,
                "path": str(Path(path).relative_to(root_dir)).replace("\\", "/"),
                "sha256": _file_sha256(path),
            }
            for path in sorted(glob.glob(os.path.join(root_dir, "db", "migrations", "*.sql")))
        ]
    if args.only:
        wanted = set(args.only)
        migration_entries = [e for e in migration_entries if extract_name(e["absolute_path"]) in wanted]
        found = {extract_name(e["absolute_path"]) for e in migration_entries}
        missing = sorted(wanted - found)
        if missing:
            print(f"  🛑 Migrations solicitadas no existen: {missing}")
            sys.exit(1)
    if not migration_entries:
        print("  No se encontraron archivos SQL en db/migrations/")
        sys.exit(0)

    print(f"  Archivos encontrados: {len(migration_entries)}")
    print()

    load_environment(args.env, root_dir)
    assert_environment(args.env)
    db = get_db_client()

    applied = get_applied_migrations(db)
    print(f"  Migrations ya aplicadas: {len(applied)}")
    print()

    pending = []
    for entry in migration_entries:
        name = extract_name(entry["absolute_path"])
        if name not in applied:
            pending.append(entry)
            continue
        if args.manifest:
            try:
                ledger_metadata = json.loads(applied[name])
            except (TypeError, json.JSONDecodeError):
                print(f"  🛑 {name} existe sin metadata de checksum verificable")
                sys.exit(1)
            if ledger_metadata.get("sha256") != entry["sha256"]:
                print(f"  🛑 Drift detectado: {name} tiene otro checksum en el ledger")
                sys.exit(1)

    if not pending:
        print("  ✅ No hay migrations pendientes. Todo al día.")
        sys.exit(0)

    print(f"  Migrations pendientes: {len(pending)}")
    print()

    success_count = 0
    fail_count = 0

    release_metadata = None
    if release_manifest:
        release_metadata = {
            "release_id": release_manifest["release_id"],
            "revision": release_manifest["revision"],
            "candidate_commit": release_manifest["candidate_commit"],
            "manifest_sha256": args.expected_manifest_sha256,
        }
    for entry in pending:
        ok = apply_migration(db, entry, release_metadata, dry_run=args.dry_run)
        if ok:
            success_count += 1
        else:
            fail_count += 1
            if not args.dry_run:
                print(f"\n  🛑 Error aplicando {extract_name(entry['absolute_path'])}. Abortando.")
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
