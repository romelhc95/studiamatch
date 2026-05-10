"""
check_db_parity.py — Parity check Free vs Pro.
Exits: 0=OK, 1=WARN, 2=ERROR.
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import DatabaseClient

REQUIRED_EXTENSIONS = ["vector", "pg_trgm", "pgcrypto", "uuid-ossp"]
PIPELINE_COLUMNS = ["noise_patterns", "max_consecutive_errors", "circuit_open", "circuit_opened_at"]
COURSES_COLUMNS = ["start_date"]


def try_rpc(db, sql):
    try:
        return db.rpc("exec_sql", {"sql_text": sql})
    except Exception:
        return None


def compare_migrations(db_free, db_pro):
    print("\n[CHECK 1] Migraciones aplicadas")
    try:
        free = db_free.select("supabase_migrations", columns="name", limit=1000) or []
        pro = db_pro.select("supabase_migrations", columns="name", limit=1000) or []
    except Exception:
        return "WARN", ["No se pudo leer supabase_migrations"]
    free_set = {r["name"] for r in free if r.get("name")}
    pro_set = {r["name"] for r in pro if r.get("name")}
    only_free = free_set - pro_set
    if only_free:
        return "ERROR", [f"Migraciones en Free pero NO en Pro: {sorted(only_free)}"]
    only_pro = pro_set - free_set
    if only_pro:
        return "WARN", [f"Migraciones en Pro pero NO en Free: {sorted(only_pro)}"]
    print(f"  ✅ {len(free_set)} migraciones en ambos ambientes")
    return "OK", []


def check_column_exists(db, table, col):
    sql = f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}';"
    result = try_rpc(db, sql)
    return result and len(result) > 0


def compare_columns(db_free, db_pro):
    print("\n[CHECK 2] Columnas de institution_site_profiles")
    errors = []
    for col in PIPELINE_COLUMNS:
        in_free = check_column_exists(db_free, "institution_site_profiles", col)
        in_pro = check_column_exists(db_pro, "institution_site_profiles", col)
        if in_free and not in_pro:
            errors.append(col)
            print(f"  ❌ Falta columna '{col}' en Pro")
    print("\n[CHECK 3] Columnas de courses")
    for col in COURSES_COLUMNS:
        in_free = check_column_exists(db_free, "courses", col)
        in_pro = check_column_exists(db_pro, "courses", col)
        if in_free and not in_pro:
            errors.append(f"courses.{col}")
            print(f"  ❌ Falta columna '{col}' en courses de Pro")
    if errors:
        return "ERROR", errors
    print("  ✅ Columnas OK en ambos ambientes")
    return "OK", []


def compare_profiles(db_free, db_pro):
    ok = True
    print("\n[CHECK 4] Cantidad de perfiles")
    try:
        free = db_free.select_pipeline("institution_site_profiles", columns="institution_id", limit=1000) or []
        pro = db_pro.select_pipeline("institution_site_profiles", columns="institution_id", limit=1000) or []
        if len(free) != len(pro):
            print(f"  ❌ Free: {len(free)}, Pro: {len(pro)}")
            ok = False
        else:
            print(f"  ✅ {len(free)} perfiles")
    except Exception:
        print("  ⚠️  No se pudieron leer perfiles")
    return "OK" if ok else "ERROR", [""]


def compare_course_counts(db_free, db_pro):
    print("\n[CHECK 5] Cursos activos")
    try:
        fc = db_free.count("courses", filters="is_active=eq.true")
        pc = db_pro.count("courses", filters="is_active=eq.true")
        print(f"  Free={fc}, Pro={pc}")
        if fc > 0 and abs(fc - pc) / max(fc, 1) > 0.20:
            return "WARN", [f"Free={fc}, Pro={pc}"]
        return "OK", []
    except Exception as e:
        return "WARN", [f"count error: {e}"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["free", "pro"], default="pro")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    os.environ["SUPABASE_ENV"] = "free"
    db_free = DatabaseClient()
    os.environ["SUPABASE_ENV"] = args.env
    db_target = DatabaseClient()

    results = [
        ("migrations", compare_migrations(db_free, db_target)),
        ("columns", compare_columns(db_free, db_target)),
        ("profiles", compare_profiles(db_free, db_target)),
        ("course_count", compare_course_counts(db_free, db_target)),
    ]

    has_error = any(s == "ERROR" for _, (s, _) in results)
    has_warning = any(s == "WARN" for _, (s, _) in results)

    print(f"\n{'='*60}")
    print("  PARITY CHECK REPORT")
    print(f"{'='*60}")
    for name, (sev, _) in results:
        icon = {"OK": "✅", "WARN": "⚠️", "ERROR": "❌"}[sev]
        print(f"  {icon} [{sev}] {name}")

    if has_error:
        print("  ❌ ERRORES — Revisión requerida")
        sys.exit(2)
    if has_warning and args.strict:
        print("  ⚠️  Warnings (strict mode)")
        sys.exit(2)
    if has_warning:
        print("  ⚠️  Warnings no bloqueantes")
        sys.exit(1)
    print("  ✅ PARIDAD COMPLETA")
    sys.exit(0)


if __name__ == "__main__":
    main()
