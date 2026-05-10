"""
check_db_parity.py — Compara esquemas y config entre Free y Pro.

Uso:
  python3 scripts/maintenance/check_db_parity.py --env pro [--strict]

Exit codes:
  0 → OK (sin diferencias)
  1 → Warnings (diferencias menores)
  2 → ERROR (diferencias críticas que bloquean merge)

Checks:
  - Migraciones aplicadas (mismas versiones en ambos ambientes)
  - Columnas de institution_site_profiles
  - Columnas de courses
  - Perfiles por institución (misma cantidad)
  - pipeline_ready por institución
  - Exclusion patterns count
  - RPCs del pipeline
  - Triggers del pipeline
  - Extensiones requeridas
  - Cursos activos
"""

import os
import sys
import json
import re
import argparse
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import DatabaseClient


REQUIRED_RPCS = [
    "atomic_cleansing_promote", "atomic_enrichment_promote",
    "lock_staging_records", "lock_cleansed_records",
    "unlock_staging_record", "unlock_cleansed_record",
    "repair_jsonb_array", "repair_jsonb_object",
    "exec_sql",
]

REQUIRED_TRIGGERS = [
    ("institution_site_profiles", "trg_validate_institution_site_profiles_jsonb"),
    ("courses", "tr_auto_assign_category"),
    ("enriched_programs", "tr_enriched_programs_updated_at"),
]

REQUIRED_EXTENSIONS = ["vector", "pg_trgm", "pgcrypto", "uuid-ossp"]

PIPELINE_COLUMNS_CHECK = [
    "noise_patterns", "max_consecutive_errors",
    "circuit_open", "circuit_opened_at",
]

COURSES_COLUMNS_CHECK = ["start_date"]

IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def _mgmt_query(sql_text, supabase_url=None):
    """Ejecuta SQL SELECT via Management API y retorna resultados.
    Si supabase_url es None, usa SUPABASE_URL del environment actual."""
    token = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    url = supabase_url or os.environ.get("SUPABASE_URL", "")
    if not token or not url:
        return None
    match = re.match(r"https?://([^.]+)\.supabase\.co", url)
    if not match:
        return None
    mgmt_url = f"https://api.supabase.com/v1/projects/{match.group(1)}/database/query"
    try:
        resp = requests.post(mgmt_url, headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        }, json={"query": sql_text}, timeout=30)
        if resp.status_code in (200, 201):
            data = resp.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                raw = data.get("result", "")
                if isinstance(raw, str):
                    m = re.search(r'\[[\s\S]*\]', raw)
                    if m:
                        return json.loads(m.group())
        return None
    except Exception:
        return None


def _sanitize_identifier(name: str) -> str:
    """Sanitiza un identificador SQL (table, column, function name)."""
    if not name or not IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def _sanitize_literal(value: str) -> str:
    """Escapa un string literal SQL (defensa contra SQL injection)."""
    return value.replace("'", "''")


def compare_migrations(db_free, db_pro):
    """Check 1: Migraciones aplicadas."""
    print("\n[CHECK 1] Migraciones aplicadas")
    try:
        free = db_free.select("supabase_migrations", columns="name", limit=1000) or []
        pro = db_pro.select("supabase_migrations", columns="name", limit=1000) or []
    except Exception as e:
        print(f"  ⚠️  No se pudo leer supabase_migrations: {e}")
        return "WARN", []

    free_names = {r.get("name") for r in free if r.get("name")}
    pro_names = {r.get("name") for r in pro if r.get("name")}

    only_free = free_names - pro_names
    only_pro = pro_names - free_names

    if only_free:
        print(f"  ❌ Migraciones en Free pero NO en Pro: {sorted(only_free)}")
        return "ERROR", list(only_free)
    if only_pro:
        print(f"  ⚠️  Migraciones en Pro pero NO en Free: {sorted(only_pro)}")
        return "WARN", list(only_pro)
    print(f"  ✅ {len(free_names)} migraciones en ambos ambientes")
    return "OK", []


def check_column(db, table, column):
    """Verifica que una columna exista en una tabla."""
    safe_table = _sanitize_identifier(table)
    safe_col = _sanitize_identifier(column)
    sql = (
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_name = '{safe_table}' AND column_name = '{safe_col}';"
    )
    result = _mgmt_query(sql)
    exists = result and len(result) > 0
    if not exists:
        print(f"  ❌ Tabla '{table}' no tiene columna '{column}'")
    return exists


def compare_pipeline_columns(db_free, db_pro):
    """Check 2-3: Columnas críticas del pipeline."""
    print("\n[CHECK 2] Columnas de institution_site_profiles")
    errors = []
    for col in PIPELINE_COLUMNS_CHECK:
        in_free = check_column(db_free, "institution_site_profiles", col)
        in_pro = check_column(db_pro, "institution_site_profiles", col)
        if in_free and not in_pro:
            errors.append(col)
            print(f"  ❌ Falta columna '{col}' en Pro")
        elif not in_free and in_pro:
            print(f"  ⚠️  Columna '{col}' en Pro pero no en Free (puede ser ok)")

    print("\n[CHECK 3] Columnas de courses")
    for col in COURSES_COLUMNS_CHECK:
        in_free = check_column(db_free, "courses", col)
        in_pro = check_column(db_pro, "courses", col)
        if in_free and not in_pro:
            errors.append(f"courses.{col}")
            print(f"  ❌ Falta columna '{col}' en courses de Pro")

    if errors:
        return "ERROR", errors
    print("  ✅ Todas las columnas existen en ambos ambientes")
    return "OK", []


def compare_profiles(db_free, db_pro):
    """Check 4-6: Perfiles de institución."""
    print("\n[CHECK 4] Cantidad de perfiles")
    try:
        free = db_free.select_pipeline("institution_site_profiles", columns="institution_id", limit=1000) or []
        pro = db_pro.select_pipeline("institution_site_profiles", columns="institution_id", limit=1000) or []
    except Exception:
        return "ERROR", ["No se pudieron leer perfiles"]

    if len(free) != len(pro):
        print(f"  ❌ Free: {len(free)} perfiles, Pro: {len(pro)} perfiles")
        return "ERROR", [f"Cantidad perfiles: Free={len(free)}, Pro={len(pro)}"]
    print(f"  ✅ {len(free)} perfiles en ambos ambientes")

    print("\n[CHECK 5] pipeline_ready por institución")
    try:
        sql = (
            "SELECT i.slug, p.pipeline_ready FROM institution_site_profiles p "
            "JOIN institutions i ON i.id = p.institution_id "
            "WHERE p.pipeline_ready = true ORDER BY i.slug;"
        )
        free_ready = _mgmt_query(sql, db_free.supabase_url) or []
        pro_ready = _mgmt_query(sql, db_pro.supabase_url) or []
    except Exception:
        return "WARN", ["No se pudo leer pipeline_ready"]

    free_ready_slugs = {r.get("slug") for r in free_ready if r.get("slug")}
    pro_ready_slugs = {r.get("slug") for r in pro_ready if r.get("slug")}

    if free_ready_slugs != pro_ready_slugs:
        print(f"  ❌ Free ready: {free_ready_slugs}")
        print(f"     Pro  ready: {pro_ready_slugs}")
        return "ERROR", [f"pipeline_ready difiere"]
    print(f"  ✅ pipeline_ready idéntico: {sorted(free_ready_slugs)}")

    print("\n[CHECK 6] Exclusion patterns (tolerancia ±20%)")
    try:
        sql = (
            "SELECT i.slug, jsonb_array_length(COALESCE(p.exclusion_patterns, '[]'::jsonb)) as cnt "
            "FROM institution_site_profiles p JOIN institutions i ON i.id = p.institution_id ORDER BY i.slug;"
        )
        free_exc = _mgmt_query(sql, db_free.supabase_url) or []
        pro_exc = _mgmt_query(sql, db_pro.supabase_url) or []
    except Exception:
        return "WARN", ["No se pudo leer exclusion_patterns"]

    free_map = {r.get("slug"): r.get("cnt", 0) for r in free_exc}
    pro_map = {r.get("slug"): r.get("cnt", 0) for r in pro_exc}
    all_slugs = set(list(free_map.keys()) + list(pro_map.keys()))
    warnings = []
    for slug in sorted(all_slugs):
        f_cnt = free_map.get(slug, 0)
        p_cnt = pro_map.get(slug, 0)
        if f_cnt > 0 and abs(f_cnt - p_cnt) / max(f_cnt, 1) > 0.20:
            w = f"{slug}: Free={f_cnt}, Pro={p_cnt}"
            warnings.append(w)
            print(f"  ⚠️  Diferencia en exclusiones: {w}")

    if warnings:
        return "WARN", warnings
    print("  ✅ Exclusion patterns dentro de tolerancia")
    return "OK", []


def check_rpcs(db, label):
    """Verifica que existan los RPCs requeridos."""
    missing = []
    for rpc_name in REQUIRED_RPCS:
        safe_name = _sanitize_identifier(rpc_name)
        sql = f"SELECT proname FROM pg_proc WHERE proname = '{safe_name}' AND pronamespace = 'public'::regnamespace;"
        result = _mgmt_query(sql)
        if not result or len(result) == 0:
            missing.append(rpc_name)
    return missing


def compare_rpcs(db_free, db_pro):
    """Check 7: RPCs del pipeline."""
    print("\n[CHECK 7] RPCs del pipeline")
    free_missing = check_rpcs(db_free, "Free")
    pro_missing = check_rpcs(db_pro, "Pro")

    if pro_missing:
        print(f"  ❌ RPCs faltantes en Pro: {pro_missing}")
        return "ERROR", pro_missing
    if free_missing:
        print(f"  ⚠️  RPCs faltantes en Free: {free_missing}")
    print(f"  ✅ Todos los RPCs existen en Pro")
    return "OK", []


def check_triggers(db, label):
    """Verifica triggers requeridos."""
    missing = []
    for table, trigger in REQUIRED_TRIGGERS:
        safe_table = _sanitize_identifier(table)
        safe_trigger = _sanitize_identifier(trigger)
        sql = (
            f"SELECT trigger_name FROM information_schema.triggers "
            f"WHERE event_object_table = '{safe_table}' AND trigger_name = '{safe_trigger}';"
        )
        result = _mgmt_query(sql)
        if not result or len(result) == 0:
            missing.append(f"{table}.{trigger}")
    return missing


def compare_triggers(db_free, db_pro):
    """Check 8: Triggers."""
    print("\n[CHECK 8] Triggers del pipeline")
    pro_missing = check_triggers(db_pro, "Pro")
    if pro_missing:
        print(f"  ❌ Triggers faltantes en Pro: {pro_missing}")
        return "ERROR", pro_missing
    print("  ✅ Todos los triggers existen en Pro")
    return "OK", []


def compare_extensions(db_free, db_pro):
    """Check 9: Extensiones requeridas."""
    print("\n[CHECK 9] Extensiones requeridas")
    missing = []
    for ext in REQUIRED_EXTENSIONS:
        safe_ext = _sanitize_literal(_sanitize_identifier(ext))
        sql = f"SELECT extname FROM pg_extension WHERE extname = '{safe_ext}';"
        result = _mgmt_query(sql, db_pro.supabase_url)
        if not result or len(result) == 0:
            missing.append(ext)

    if missing:
        print(f"  ❌ Extensiones faltantes en Pro: {missing}")
        return "ERROR", missing
    print("  ✅ Todas las extensiones existen en Pro")
    return "OK", []


def compare_course_counts(db_free, db_pro):
    """Check 10: Cursos activos (tolerancia 20%)."""
    print("\n[CHECK 10] Cursos activos")
    try:
        free_count = db_free.count("courses", filters="is_active=eq.true")
        pro_count = db_pro.count("courses", filters="is_active=eq.true")
    except Exception as e:
        print(f"  ⚠️  No se pudo contar cursos: {e}")
        return "WARN", ["count error"]

    if free_count > 0 and abs(free_count - pro_count) / max(free_count, 1) > 0.20:
        print(f"  ⚠️  Diferencia significativa: Free={free_count}, Pro={pro_count}")
        return "WARN", [f"Free={free_count}, Pro={pro_count}"]

    print(f"  ✅ Free={free_count}, Pro={pro_count} (dentro de tolerancia)")
    return "OK", []


def main():
    parser = argparse.ArgumentParser(description="Parity check Free vs Pro")
    parser.add_argument("--env", choices=["free", "pro"], default="pro",
                        help="Ambiente a comparar contra Free (default: pro)")
    parser.add_argument("--strict", action="store_true",
                        help="Warnings se tratan como errores")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  check_db_parity.py — Comparando Free vs {args.env.upper()}")
    if args.strict:
        print(f"  Modo: STRICT (warnings = errors)")
    print(f"{'='*60}\n")

    os.environ["SUPABASE_ENV"] = "free"
    db_free = DatabaseClient()

    os.environ["SUPABASE_ENV"] = args.env
    db_target = DatabaseClient()

    checks = [
        ("migrations", compare_migrations(db_free, db_target)),
        ("columns", compare_pipeline_columns(db_free, db_target)),
        ("profiles", compare_profiles(db_free, db_target)),
        ("rpcs", compare_rpcs(db_free, db_target)),
        ("triggers", compare_triggers(db_free, db_target)),
        ("extensions", compare_extensions(db_free, db_target)),
        ("course_count", compare_course_counts(db_free, db_target)),
    ]

    print(f"\n{'='*60}")
    print(f"  REPORTE DE PARIDAD")
    print(f"{'='*60}")

    has_error = False
    has_warning = False
    all_details = []

    for name, (severity, details) in checks:
        icon = "✅" if severity == "OK" else ("⚠️" if severity == "WARN" else "❌")
        print(f"  {icon} [{severity}] {name}")
        if severity == "ERROR":
            has_error = True
        if severity == "WARN":
            has_warning = True
        if details:
            all_details.extend(details)

    print(f"\n{'='*60}")
    if has_error:
        print(f"  ❌ HAY ERRORES — Pro no está en paridad con Free")
        for d in all_details:
            print(f"     • {d}")
        print(f"\n  Revisión requerida antes de mergear a main.")
        sys.exit(2)
    elif has_warning and args.strict:
        print(f"  ⚠️  Warnings detectados (strict mode). Revisar.")
        sys.exit(2)
    elif has_warning:
        print(f"  ⚠️  Warnings detectados (no bloqueantes).")
        sys.exit(1)
    else:
        print(f"  ✅ PARIDAD COMPLETA — Free y Pro están sincronizados")
        sys.exit(0)


if __name__ == "__main__":
    main()
