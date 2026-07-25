"""
check_db_parity.py - Configuration-oriented parity check Free vs target.

Exit codes:
  0 = OK
  1 = non-blocking warnings
  2 = blocking parity error

Fase 103: operational FG2 tables are allowed to diverge between Free and Pro.
This script blocks on schema/configuration drift, not on ETL row counts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import DatabaseClient
from shared.supabase_credentials import (
    get_environment_credentials,
    get_secret_key,
    require_distinct_environments,
)
from maintenance.migration_manifest import canonical_sql_sha256, load_manifest


CONFIG_COLUMNS = {
    "institution_site_profiles": {
        "pipeline_ready",
        "allowed_url_patterns",
        "noise_patterns",
        "max_consecutive_errors",
        "circuit_open",
        "circuit_opened_at",
        "discovery_enabled",
        "pipeline_enabled",
        "production_enabled",
    },
    "courses": {
        "start_date",
        "publication_status",
        "data_quality_status",
        "missing_fields",
        "field_sources",
        "manual_updated_at",
        "is_sponsored",
        "sponsorship_priority",
        "sponsorship_label",
    },
    "leads": {"lead_source_type"},
    "ratings": {"moderation_status", "moderated_at"},
    "reviews": {"moderation_status", "moderated_at"},
}

CONFIG_TABLES = {
    "institutions",
    "institution_site_profiles",
    "categories",
    "category_rules",
    "market_salaries",
}

REQUIRED_MIGRATIONS = {
    "fase112_pro_fk_courses_category",
    "fase113_pro_rls_and_rpc_sync",
    "fase114_security_contract_hardening",
    "fase115_authenticated_profile_hardening",
    "fase116_public_grant_defense_in_depth",
    "20260724_fase06_g1b_reconciliation",
    "20260724_fase06_hito1_editorial_contract",
    "20260725_fase07_g1b_closure",
    "20260725_fase08_hito1_functional_closure",
}

OPERATIONAL_TABLES = {
    "staging_raw",
    "cleansed_programs",
    "enriched_programs",
    "courses",
}

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F8_MANIFEST = Path(ROOT_DIR) / "db" / "manifests" / "fase08_candidate.json"


def migration_is_applied(applied: set[str], required_name: str) -> bool:
    """Accept exact migration names or versioned filenames like 20260525_<name>."""
    versioned_pattern = re.compile(rf"^\d{{8,14}}_{re.escape(required_name)}$")
    return required_name in applied or any(versioned_pattern.match(name) for name in applied)


def load_environment(target: str) -> None:
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


def assert_environment(target: str) -> None:
    required = ["NEXT_SUPABASE_SECRET_KEY"]
    missing = [name for name in required if not os.environ.get(name)]
    if not (os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")):
        missing.append("SUPABASE_URL/NEXT_PUBLIC_SUPABASE_URL")
    if missing:
        raise RuntimeError(f"Faltan credenciales para {target}: {', '.join(missing)}")
    get_secret_key()


def try_rpc(db: DatabaseClient, sql: str) -> list[dict[str, Any]] | None:
    try:
        result = db.rpc("exec_sql", {"sql_text": sql})
        return result if isinstance(result, list) else None
    except Exception:
        return None


def service_select(db: DatabaseClient, table: str, columns: str, limit: int = 1000):
    url = f"{db.supabase_url}/rest/v1/{table}?select={columns}&limit={limit}"
    res = requests.get(url, headers=db._get_headers(use_service_role=True), timeout=30)
    if res.status_code == 200:
        return res.json()
    raise RuntimeError(f"REST select failed for {table}.{columns}: {res.status_code} {(res.text or '')[:160]}")


def _select_all(db: DatabaseClient, table: str, columns: str) -> list[dict[str, Any]]:
    return db.select_service(table, columns=columns, limit=1000) or []


def compare_migrations(db_free: DatabaseClient, db_target: DatabaseClient):
    print("\n[CHECK 1] Package contractual aplicado")
    try:
        free = service_select(
            db_free, "supabase_migrations", "name,statements"
        ) or []
        target = service_select(
            db_target, "supabase_migrations", "name,statements"
        ) or []
        package = load_manifest(
            F8_MANIFEST, "pro", required_status="free_certified"
        )
    except Exception as e:
        return "ERROR", [f"No se pudo validar el package contractual: {e}"]

    free_ledger = {
        row.get("name"): row.get("statements")
        for row in free
        if row.get("name")
    }
    target_ledger = {
        row.get("name"): row.get("statements")
        for row in target
        if row.get("name")
    }
    errors = []
    for migration in package:
        marker = f"sha256:{canonical_sql_sha256(migration)}"
        for environment, ledger in (
            ("Free", free_ledger),
            ("target", target_ledger),
        ):
            if ledger.get(migration.stem) != marker:
                errors.append(
                    f"{environment}: ledger/checksum invalido para {migration.stem}"
                )

    if errors:
        return "ERROR", errors

    print(f"  OK: {len(package)} migrations contractuales con checksum exacto")
    return "OK", []


def check_column_exists(db: DatabaseClient, table: str, column: str) -> bool:
    if table not in CONFIG_COLUMNS or column not in CONFIG_COLUMNS[table]:
        raise ValueError(f"Tabla/columna no permitida: {table}.{column}")
    url = f"{db.supabase_url}/rest/v1/{table}?select={column}&limit=1"
    res = requests.get(url, headers=db._get_headers(use_service_role=True), timeout=30)
    if res.status_code == 200:
        return True
    if res.status_code in (400, 404):
        return False
    raise RuntimeError(f"No se pudo verificar columna {table}.{column}: {res.status_code}")


def compare_columns(db_free: DatabaseClient, db_target: DatabaseClient):
    print("\n[CHECK 2] Columnas criticas de configuracion/schema")
    errors: list[str] = []
    for table, columns in sorted(CONFIG_COLUMNS.items()):
        for column in sorted(columns):
            in_free = check_column_exists(db_free, table, column)
            in_target = check_column_exists(db_target, table, column)
            if in_free and not in_target:
                errors.append(f"{table}.{column}")
                print(f"  ERROR: falta {table}.{column} en target")
    if errors:
        return "ERROR", errors
    print("  OK: columnas criticas presentes")
    return "OK", []


def check_target_columns(db_target: DatabaseClient):
    print("\n[CHECK 1] Columnas criticas de configuracion/schema en target")
    errors: list[str] = []
    for table, columns in sorted(CONFIG_COLUMNS.items()):
        for column in sorted(columns):
            if not check_column_exists(db_target, table, column):
                errors.append(f"{table}.{column}")
                print(f"  ERROR: falta {table}.{column} en target")
    if errors:
        return "ERROR", errors
    print("  OK: columnas criticas presentes en target")
    return "OK", []


def check_schema_contracts(db_target: DatabaseClient, *, check_public: bool = True):
    print("\n[CHECK 3] Schema contracts requeridos por PostgREST/pipeline")
    errors: list[str] = []

    try:
        target_migrations = service_select(
            db_target, "supabase_migrations", "name,statements"
        ) or []
        applied = {row.get("name") for row in target_migrations if row.get("name")}
        missing_migrations = sorted(
            required_name
            for required_name in REQUIRED_MIGRATIONS
            if not migration_is_applied(applied, required_name)
        )
        if missing_migrations:
            errors.append(f"Migraciones contractuales faltantes en target: {missing_migrations}")

        ledger = {
            row.get("name"): row.get("statements")
            for row in target_migrations
            if row.get("name")
        }
        for migration in load_manifest(
            F8_MANIFEST, "pro", required_status="free_certified"
        ):
            expected_marker = f"sha256:{canonical_sql_sha256(migration)}"
            if ledger.get(migration.stem) != expected_marker:
                errors.append(
                    f"Ledger/checksum contractual invalido: {migration.stem}"
                )
    except Exception as e:
        errors.append(f"No se pudo verificar supabase_migrations: {e}")

    for verifier in (
        "verify_fase06_g1b_reconciliation",
        "verify_fase06_hito1_contract",
        "verify_fase07_g1b_closure",
        "verify_fase08_hito1_contract",
    ):
        try:
            result = db_target.rpc_raise(verifier, {})
            if result is not True:
                errors.append(f"El verificador {verifier} no retorno true")
        except Exception as e:
            errors.append(f"No se pudo ejecutar {verifier}: {e}")

    embedded_url = (
        f"{db_target.supabase_url}/rest/v1/courses"
        "?is_active=eq.true&is_verified=eq.true"
        "&select=id,categories(name),institutions(name,slug)&limit=1"
    )
    service_res = requests.get(embedded_url, headers=db_target._get_headers(use_service_role=True), timeout=30)
    if service_res.status_code != 200:
        errors.append(
            "PostgREST embedded query falla con service role. "
            f"Esto suele indicar FK faltante courses->categories/institutions: {service_res.status_code} {(service_res.text or '')[:200]}"
        )

    if check_public:
        service_has_active_courses = (
            service_res.status_code == 200 and bool(service_res.json())
        )
        public_headers = db_target._get_headers(use_service_role=False)
        public_res = requests.get(
            embedded_url,
            headers=public_headers,
            timeout=30,
        )
        if public_res.status_code != 200:
            errors.append(
                "PostgREST embedded query falla con publishable key. "
                f"Esto bloquea el frontend: {public_res.status_code} {(public_res.text or '')[:200]}"
            )
        elif service_has_active_courses and not public_res.json():
            errors.append(
                "La API publica devuelve 0 cursos aunque existen cursos activos/verificados. "
                "Revisar RLS de courses/institution_site_profiles y production_enabled."
            )

        public_profile_safe_url = (
            f"{db_target.supabase_url}/rest/v1/institution_site_profiles"
            "?select=institution_id,production_enabled&production_enabled=eq.true&limit=1"
        )
        safe_profile_res = requests.get(
            public_profile_safe_url,
            headers=public_headers,
            timeout=30,
        )
        if safe_profile_res.status_code != 200:
            errors.append(
                "La policy publica minima de institution_site_profiles no permite leer "
                f"institution_id/production_enabled: {safe_profile_res.status_code} {(safe_profile_res.text or '')[:200]}"
            )

        public_profile_sensitive_url = (
            f"{db_target.supabase_url}/rest/v1/institution_site_profiles"
            "?select=exclusion_patterns&limit=1"
        )
        sensitive_profile_res = requests.get(
            public_profile_sensitive_url,
            headers=public_headers,
            timeout=30,
        )
        if sensitive_profile_res.status_code == 200:
            errors.append(
                "institution_site_profiles.exclusion_patterns esta expuesto publicamente"
            )

        social_public_fields = {
            "ratings": "id,course_id,rating_value,user_nickname,created_at",
            "reviews": "id,course_id,content,user_nickname,created_at",
        }
        for table, columns in social_public_fields.items():
            social_url = (
                f"{db_target.supabase_url}/rest/v1/{table}"
                f"?select={columns}&limit=1"
            )
            social_res = requests.get(
                social_url, headers=public_headers, timeout=30
            )
            if social_res.status_code != 200:
                errors.append(
                    f"Lectura publica minima de {table} fallo: "
                    f"HTTP {social_res.status_code}"
                )

            private_url = (
                f"{db_target.supabase_url}/rest/v1/{table}"
                "?select=moderation_status&limit=1"
            )
            private_res = requests.get(
                private_url, headers=public_headers, timeout=30
            )
            if private_res.status_code not in (401, 403):
                errors.append(
                    f"{table}.moderation_status no produjo una denegacion explicita: "
                    f"HTTP {private_res.status_code}"
                )

        rpc_checks = [
            (
                "atomic_enrichment_promote",
                {
                    "p_enriched_data": [],
                    "p_cleansed_id": "00000000-0000-0000-0000-000000000000",
                },
            ),
            ("exec_sql", {"sql_text": "select 1"}),
        ]
        for function_name, payload in rpc_checks:
            rpc_url = f"{db_target.supabase_url}/rest/v1/rpc/{function_name}"
            rpc_res = requests.post(
                rpc_url,
                headers=public_headers,
                json=payload,
                timeout=30,
            )
            if rpc_res.status_code not in (401, 403, 404):
                errors.append(
                    f"RPC {function_name} no produjo una denegacion explicita: "
                    f"HTTP {rpc_res.status_code}"
                )

    if errors:
        return "ERROR", errors
    print("  OK: schema contracts requeridos presentes")
    return "OK", []


def compare_institutions(db_free: DatabaseClient, db_target: DatabaseClient):
    print("\n[CHECK 3] Catalogo institutions por slug")
    free_rows = _select_all(db_free, "institutions", "slug,name,website_url")
    target_rows = _select_all(db_target, "institutions", "slug,name,website_url")
    free = {r.get("slug"): r for r in free_rows if r.get("slug")}
    target = {r.get("slug"): r for r in target_rows if r.get("slug")}

    missing = sorted(set(free) - set(target))
    if missing:
        return "ERROR", [f"Institutions faltantes en target: {missing}"]
    extra = sorted(set(target) - set(free))
    if extra:
        print(f"  WARN: institutions extra en target: {extra}")
        return "WARN", [f"Institutions extra en target: {extra}"]
    print(f"  OK: {len(free)} institutions en paridad por slug")
    return "OK", []


def compare_profiles(db_free: DatabaseClient, db_target: DatabaseClient):
    print("\n[CHECK 4] Perfiles por institution slug")
    free_insts = {r.get("id"): r.get("slug") for r in service_select(db_free, "institutions", "id,slug") if r.get("id") and r.get("slug")}
    target_insts = {r.get("id"): r.get("slug") for r in service_select(db_target, "institutions", "id,slug") if r.get("id") and r.get("slug")}
    free_profile_ids = {r.get("institution_id") for r in service_select(db_free, "institution_site_profiles", "institution_id") if r.get("institution_id")}
    target_profile_ids = {r.get("institution_id") for r in service_select(db_target, "institution_site_profiles", "institution_id") if r.get("institution_id")}

    free = {free_insts[iid] for iid in free_profile_ids if iid in free_insts}
    target = {target_insts[iid] for iid in target_profile_ids if iid in target_insts}
    missing = sorted(free - target)
    if missing:
        return "ERROR", [f"Perfiles faltantes en target: {missing}"]
    extra = sorted(target - free)
    if extra:
        return "WARN", [f"Perfiles extra en target: {extra}"]
    print(f"  OK: {len(free)} perfiles en paridad por slug")
    return "OK", []


def normalize_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return value


def normalize_row(row: dict[str, Any], exclude: set[str]) -> dict[str, Any]:
    return {
        key: normalize_value(value)
        for key, value in sorted(row.items())
        if key not in exclude and not key.endswith("_id")
    }


def compare_catalog_values(db_free: DatabaseClient, db_target: DatabaseClient):
    print("\n[CHECK 5] Valores de catalogos/configuracion")
    checks = [
        ("institutions", "slug", {"id", "created_at", "updated_at", "last_harvest_at", "last_harvest_duration_sec"}),
        ("categories", "slug", {"id", "created_at", "updated_at"}),
        ("market_salaries", "category", {"id", "created_at", "updated_at"}),
        ("category_rules", "keyword", {"id", "created_at", "updated_at"}),
    ]
    errors: list[str] = []
    warnings: list[str] = []

    for table, preferred_key, exclude in checks:
        try:
            free_rows = service_select(db_free, table, "*")
            target_rows = service_select(db_target, table, "*")
        except Exception as e:
            warnings.append(f"{table}: no se pudo comparar valores ({e})")
            continue

        def key_for(row: dict[str, Any]) -> str:
            for candidate in (preferred_key, "slug", "name", "keyword"):
                if row.get(candidate):
                    return str(row[candidate])
            return json.dumps(normalize_row(row, exclude), sort_keys=True, ensure_ascii=False)

        free = {key_for(row): normalize_row(row, exclude) for row in free_rows}
        target = {key_for(row): normalize_row(row, exclude) for row in target_rows}
        missing = sorted(set(free) - set(target))
        extra = sorted(set(target) - set(free))
        changed = sorted(key for key in set(free) & set(target) if free[key] != target[key])
        if missing or changed:
            errors.append(f"{table}: missing={missing}, changed={changed[:20]}")
        if extra:
            warnings.append(f"{table}: extra en target={extra}")

    profile_errors = compare_profile_values(db_free, db_target)
    errors.extend(profile_errors)

    if errors:
        return "ERROR", errors + warnings
    if warnings:
        return "WARN", warnings
    print("  OK: catalogos/configuracion sin drift material")
    return "OK", []


def compare_profile_values(db_free: DatabaseClient, db_target: DatabaseClient) -> list[str]:
    profile_fields = [
        "pipeline_ready",
        "discovery_enabled",
        "pipeline_enabled",
        "production_enabled",
        "site_type",
        "discovery_mode",
        "requires_stealth",
        "requires_cloudflare_bypass",
        "warmup_url",
        "detail_wait_ms",
        "catalog_max_pages",
        "catalog_scroll_iterations",
        "catalog_link_selector",
        "catalog_url_patterns",
        "allowed_url_patterns",
        "exclusion_patterns",
        "noise_patterns",
        "seed_urls",
        "popup_close_selectors",
        "title_prefix_removals",
        "title_split_separators",
        "price_regex",
        "field_defaults",
        "section_keywords",
        "section_mode_map",
        "section_course_type_map",
        "max_consecutive_errors",
        "circuit_open",
        "circuit_opened_at",
    ]
    columns = "institution_id," + ",".join(profile_fields)
    free_insts = {r.get("id"): r.get("slug") for r in service_select(db_free, "institutions", "id,slug") if r.get("id") and r.get("slug")}
    target_insts = {r.get("id"): r.get("slug") for r in service_select(db_target, "institutions", "id,slug") if r.get("id") and r.get("slug")}
    try:
        free_rows = service_select(db_free, "institution_site_profiles", columns)
        target_rows = service_select(db_target, "institution_site_profiles", columns)
    except Exception as e:
        return [f"institution_site_profiles: no se pudieron comparar valores ({e})"]
    free = {free_insts.get(r.get("institution_id")): normalize_row(r, {"institution_id"}) for r in free_rows if free_insts.get(r.get("institution_id"))}
    target = {target_insts.get(r.get("institution_id")): normalize_row(r, {"institution_id"}) for r in target_rows if target_insts.get(r.get("institution_id"))}
    changed = sorted(slug for slug in set(free) & set(target) if free[slug] != target[slug])
    missing = sorted(set(free) - set(target))
    errors = []
    if missing or changed:
        errors.append(f"institution_site_profiles: missing={missing}, changed={changed[:20]}")
    return errors


def report_operational_counts(db_free: DatabaseClient, db_target: DatabaseClient):
    print("\n[CHECK 6] Conteos operativos (informativo, no bloqueante)")
    messages: list[str] = []
    for table in sorted(OPERATIONAL_TABLES):
        try:
            free_count = db_free.count_service(table)
            target_count = db_target.count_service(table)
            msg = f"{table}: Free={free_count}, target={target_count}"
            print(f"  INFO: {msg}")
            messages.append(msg)
        except Exception as e:
            msg = f"{table}: no se pudo contar ({e})"
            print(f"  WARN: {msg}")
            messages.append(msg)
    return "OK", messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["free", "pro"], default="pro")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--target-only",
        action="store_true",
        help="Valida solo el target con las credenciales del environment actual. Uso CI cuando GitHub no expone secrets de dos environments en un job.",
    )
    args = parser.parse_args()

    if args.target_only:
        load_environment(args.env)
        assert_environment(args.env)
        db_target = DatabaseClient()
        results = [
            ("target_columns", check_target_columns(db_target)),
            ("schema_contracts", check_schema_contracts(db_target)),
        ]
        has_error = any(status == "ERROR" for _, (status, _) in results)
        print(f"\n{'=' * 60}")
        print("  TARGET CONFIG CHECK REPORT")
        print(f"{'=' * 60}")
        for name, (status, details) in results:
            print(f"  [{status}] {name}")
            for detail in details:
                print(f"    - {detail}")
        if has_error:
            print("  ERROR: schema/configuracion target incompleta")
            sys.exit(2)
        print("  OK: schema/configuracion target minima completa")
        sys.exit(0)

    if args.env != "pro":
        raise RuntimeError("El modo cross-environment requiere --env pro")
    free = get_environment_credentials("FREE")
    pro = get_environment_credentials("PRO")
    require_distinct_environments(free, pro)
    db_free = DatabaseClient(free.url, free.secret_key)
    db_target = DatabaseClient(pro.url, pro.secret_key)

    results = [
        ("migrations", compare_migrations(db_free, db_target)),
        ("columns", compare_columns(db_free, db_target)),
        ("schema_contracts", check_schema_contracts(db_target, check_public=False)),
        ("institutions", compare_institutions(db_free, db_target)),
        ("profiles", compare_profiles(db_free, db_target)),
        ("catalog_values", compare_catalog_values(db_free, db_target)),
        ("operational_counts", report_operational_counts(db_free, db_target)),
    ]

    has_error = any(status == "ERROR" for _, (status, _) in results)
    has_warning = any(status == "WARN" for _, (status, _) in results)

    print(f"\n{'=' * 60}")
    print("  PARITY CHECK REPORT")
    print(f"{'=' * 60}")
    for name, (status, details) in results:
        icon = {"OK": "OK", "WARN": "WARN", "ERROR": "ERROR"}[status]
        print(f"  [{icon}] {name}")
        for detail in details:
            if detail:
                print(f"    - {detail}")

    if has_error:
        print("  ERROR: paridad de configuracion/schema incompleta")
        sys.exit(2)
    if has_warning and args.strict:
        print("  ERROR: warnings en strict mode")
        sys.exit(2)
    if has_warning:
        print("  WARN: warnings no bloqueantes")
        sys.exit(1)
    print("  OK: paridad de configuracion/schema completa")
    sys.exit(0)


if __name__ == "__main__":
    main()
