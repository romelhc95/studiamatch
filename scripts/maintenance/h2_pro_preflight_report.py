"""Read-only H2 Pro preflight report for JIT preparation.

Produces read-only cohort aggregates for review before any later
h2-expand-compat migration decision. The report never authorizes application.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

with redirect_stdout(sys.stderr):
    from scripts.shared.db_client import DatabaseClient  # noqa: E402
    from scripts.maintenance.db_migrate import PRO_MIGRATION_MANIFESTS  # noqa: E402
from scripts.shared.supabase_credentials import get_secret_key  # noqa: E402

PRO_PROJECT_REF = "xwhtiqmboljkshrtviyw"
H2_EXPAND_MIGRATIONS = PRO_MIGRATION_MANIFESTS["h2-expand-compat"]
H2_PUBLIC_TABLES = (
    "editorial_field_definitions",
    "course_editorial_state",
    "course_editorial_audit",
)
H2_PUBLIC_VIEW = "courses_public_effective"


class PreflightReadError(RuntimeError):
    """Sanitized marker for a failed read; response bodies are never retained."""

    def __init__(self, resource: str, category: str):
        http_status = category.startswith("HTTP ") and category[5:].isdigit() and len(category[5:]) == 3
        self.category = category if category in {"invalid_json", "invalid_shape", "network_error"} or http_status else "unknown"
        self.resource = resource
        super().__init__(f"read failed: {resource} ({self.category})")


def assert_pro_target(active_url: str) -> None:
    """Pin the report to the Pro origin; never accept a path or URL modifiers."""
    expected_host = f"{PRO_PROJECT_REF}.supabase.co"
    try:
        parsed = urlparse(active_url)
        port = parsed.port
    except ValueError:
        raise RuntimeError(f"Pro preflight target must be pinned to {expected_host}") from None
    if (
        parsed.scheme != "https"
        or parsed.hostname != expected_host
        or parsed.username
        or parsed.password
        or port not in (None, 443)
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or "?" in active_url
        or "#" in active_url
    ):
        raise RuntimeError(f"Pro preflight target must be pinned to {expected_host}")


def load_pro_environment() -> None:
    load_dotenv(ROOT_DIR / ".env.gitprod", override=True)
    mappings = {
        "SUPABASE_URL": ["PRO_SUPABASE_URL", "PRO_NEXT_PUBLIC_SUPABASE_URL"],
        "NEXT_PUBLIC_SUPABASE_URL": ["PRO_NEXT_PUBLIC_SUPABASE_URL", "PRO_SUPABASE_URL"],
        "NEXT_SUPABASE_SECRET_KEY": ["PRO_NEXT_SUPABASE_SECRET_KEY"],
        "NEXT_SUPABASE_PUBLISHABLE_KEY": ["PRO_NEXT_SUPABASE_PUBLISHABLE_KEY", "PRO_NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"],
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY": ["PRO_NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "PRO_NEXT_SUPABASE_PUBLISHABLE_KEY"],
    }
    for canonical, candidates in mappings.items():
        for candidate in candidates:
            value = os.environ.get(candidate)
            if value:
                os.environ[canonical] = value
                break
    if os.environ.get("NEXT_PUBLIC_SUPABASE_URL"):
        os.environ["SUPABASE_URL"] = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    os.environ["SUPABASE_ENV"] = "pro"


def service_get(db: DatabaseClient, path: str) -> requests.Response:
    return requests.get(
        f"{db.supabase_url}/rest/v1/{path}",
        headers=db._get_headers(use_service_role=True),
        timeout=30,
        allow_redirects=False,
    )


def public_get(db: DatabaseClient, path: str) -> requests.Response:
    return requests.get(
        f"{db.supabase_url}/rest/v1/{path}",
        headers=db._get_headers(use_service_role=False),
        timeout=30,
        allow_redirects=False,
    )


def select_all(db: DatabaseClient, table: str, columns: str, *, use_service_role: bool) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    page_size = 1000
    while True:
        path = f"{table}?select={columns}&limit={page_size}&offset={offset}"
        try:
            res = service_get(db, path) if use_service_role else public_get(db, path)
        except requests.RequestException:
            raise PreflightReadError(table, "network_error") from None
        if res.status_code != 200:
            raise PreflightReadError(table, f"HTTP {res.status_code}")
        try:
            page = res.json() if res.content else []
        except ValueError:
            raise PreflightReadError(table, "invalid_json") from None
        if not isinstance(page, list) or any(not isinstance(row, dict) for row in page):
            raise PreflightReadError(table, "invalid_shape")
        rows.extend(page)
        if len(page) < page_size:
            return rows
        offset += page_size


def select_service_all(db: DatabaseClient, table: str, columns: str) -> list[dict]:
    return select_all(db, table, columns, use_service_role=True)


def select_public_all(db: DatabaseClient, table: str, columns: str) -> list[dict]:
    return select_all(db, table, columns, use_service_role=False)


def table_exists(db: DatabaseClient, table: str) -> bool:
    try:
        res = service_get(db, f"{table}?select=*&limit=0")
    except requests.RequestException:
        raise PreflightReadError(table, "network_error") from None
    if res.status_code == 200:
        return True
    if res.status_code == 404:
        return False
    raise PreflightReadError(table, f"HTTP {res.status_code}")


def table_has_rows(db: DatabaseClient, table: str) -> bool:
    try:
        res = service_get(db, f"{table}?select=id&limit=1")
    except requests.RequestException:
        raise PreflightReadError(table, "network_error") from None
    if res.status_code != 200:
        raise PreflightReadError(table, f"HTTP {res.status_code}")
    try:
        rows = res.json() if res.content else []
    except ValueError:
        raise PreflightReadError(table, "invalid_json") from None
    if not isinstance(rows, list):
        raise PreflightReadError(table, "invalid_shape")
    return bool(rows)


def classify_h2_state(
    migration_names: list[str],
    h2_objects_present: dict[str, bool],
    *,
    crawler_exclusions_present: bool,
) -> tuple[str, list[str]]:
    """Classify the Data-API-visible contract; never grants apply permission."""
    expected_migrations = set(H2_EXPAND_MIGRATIONS)
    applied = set(migration_names) & expected_migrations
    visible_objects = set(H2_PUBLIC_TABLES) | {H2_PUBLIC_VIEW}
    observed_objects = {name for name in visible_objects if h2_objects_present.get(name) is True}
    missing_objects = sorted(visible_objects - observed_objects)
    blockers: list[str] = []

    if not applied and not observed_objects:
        return "BASELINE", blockers
    if not applied and observed_objects:
        blockers.append("public H2 objects exist outside the h2-expand-compat ledger")
        return "PARTIAL_UNLEDGERED", blockers
    if applied != expected_migrations:
        missing_migrations = [name for name in H2_EXPAND_MIGRATIONS if name not in applied]
        blockers.append("H2 migration ledger is partial")
        blockers.extend(f"ledger missing: {name}" for name in missing_migrations)
        return "INCONSISTENT", blockers
    if missing_objects:
        blockers.append("ledger is complete but public H2 objects are missing")
        blockers.extend(f"object missing: {name}" for name in missing_objects)
        return "INCONSISTENT", blockers
    if crawler_exclusions_present:
        blockers.append("legacy crawler_exclusions remains after h2-expand-compat")
        return "INCONSISTENT", blockers
    return "H2_COMPATIBLE_OBSERVED_SURFACE", blockers


def _read_error_report(error: PreflightReadError) -> dict:
    return {
        "schema": "h2-pro-preflight-report-v2",
        "environment": "pro",
        "manifest": "h2-expand-compat",
        "report_status": "READ_ERROR",
        "error": {"resource": error.resource, "category": error.category},
        "h2_state": "UNDETERMINED",
        "private_h2_schema_observed": None,
        "private_h2_schema_probe": "not_performed",
        "verification_rpc_probe": "not_performed",
        "eligible_count": None,
        "public_visible_count": None,
        "ordered_eligible_ids_digest": None,
        "apply_authorized": False,
        "application_decision": "NOT_AUTHORIZED",
        "jit_fields_available": False,
        "jit_lines": [],
    }


def build_report(db: DatabaseClient) -> dict:
    """Read bounded fields and emit aggregates only; this never invokes RPCs or writes."""
    try:
        public_ids = sorted(
            row["id"] for row in select_public_all(db, "courses", "id") if row.get("id")
        )
        courses = select_service_all(
            db,
            "courses",
            columns="id,institution_id,slug,is_active,is_verified,url",
        )
        profiles = select_service_all(
            db,
            "institution_site_profiles",
            columns="institution_id,production_enabled,notes",
        )
        ledger_rows = select_service_all(db, "supabase_migrations", "name")
        migration_names = [row["name"] for row in ledger_rows if row.get("name")]

        production_institutions = {
            row["institution_id"]
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

        duplicate_pairs: dict[tuple[str, str], int] = {}
        for row in courses:
            key = (row.get("institution_id"), row.get("slug"))
            if not key[0] or not key[1]:
                continue
            duplicate_pairs[key] = duplicate_pairs.get(key, 0) + 1
        duplicate_pair_count = sum(1 for count in duplicate_pairs.values() if count > 1)

        missing_from_public = sorted(set(eligible_ids) - set(public_ids))
        unexpected_public = sorted(set(public_ids) - set(eligible_ids))
        crawler_exclusions_present = table_exists(db, "crawler_exclusions")
        crawler_exclusions_empty = (
            not table_has_rows(db, "crawler_exclusions") if crawler_exclusions_present else True
        )
        h2_objects_present = {table: table_exists(db, table) for table in H2_PUBLIC_TABLES}
        h2_objects_present[H2_PUBLIC_VIEW] = table_exists(db, H2_PUBLIC_VIEW)
    except PreflightReadError as error:
        return _read_error_report(error)

    h2_state, h2_blockers = classify_h2_state(
        migration_names,
        h2_objects_present,
        crawler_exclusions_present=crawler_exclusions_present,
    )
    data_blockers = []
    if duplicate_pair_count:
        data_blockers.append(f"duplicate institution_id+slug groups: {duplicate_pair_count}")
    if missing_from_public or unexpected_public:
        data_blockers.append(
            "public visibility differs from eligible cohort: "
            f"missing={len(missing_from_public)}, unexpected={len(unexpected_public)}"
        )
    if not crawler_exclusions_empty:
        data_blockers.append("public.crawler_exclusions contains rows")

    digest = "sha256:" + hashlib.sha256(",".join(eligible_ids).encode("utf-8")).hexdigest()
    jit_fields_available = h2_state == "BASELINE" and not data_blockers
    if data_blockers:
        report_status = "INCOMPLETE"
    elif h2_state == "INCONSISTENT":
        report_status = "INCOMPLETE"
    elif h2_state == "PARTIAL_UNLEDGERED":
        report_status = "REVIEW_REQUIRED"
    else:
        report_status = "REPORT_ONLY"

    jit_lines = []
    if jit_fields_available:
        jit_lines = [
            "H2 expected eligible count: " + str(len(eligible_ids)),
            "H2 expected cohort digest: " + digest,
        ]

    return {
        "schema": "h2-pro-preflight-report-v2",
        "environment": "pro",
        "manifest": "h2-expand-compat",
        "report_status": report_status,
        "h2_state": h2_state,
        "h2_ledger_migrations": [name for name in H2_EXPAND_MIGRATIONS if name in migration_names],
        "h2_objects_present": h2_objects_present,
        "h2_blockers": h2_blockers,
        "private_h2_schema_observed": None,
        "private_h2_schema_probe": "not_performed",
        "private_h2_schema_note": "private schema is not queried through this Data API report",
        "verification_rpc_probe": "not_performed",
        "total_courses": len(courses),
        "eligible_count": len(eligible_ids),
        "public_visible_count": len(public_ids),
        "ordered_eligible_ids_digest": digest,
        "missing_from_public_count": len(missing_from_public),
        "unexpected_public_count": len(unexpected_public),
        "duplicate_institution_slug_groups": duplicate_pair_count,
        "data_blockers": data_blockers,
        "crawler_exclusions_present": crawler_exclusions_present,
        "crawler_exclusions_empty": crawler_exclusions_empty,
        "apply_authorized": False,
        "application_decision": "NOT_AUTHORIZED",
        "jit_fields_available": jit_fields_available,
        "jit_lines": jit_lines,
    }


def main() -> None:
    load_pro_environment()
    if not (os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")):
        raise RuntimeError("SUPABASE_URL/NEXT_PUBLIC_SUPABASE_URL requerido para Pro preflight")
    if not os.environ.get("NEXT_SUPABASE_PUBLISHABLE_KEY"):
        raise RuntimeError("NEXT_SUPABASE_PUBLISHABLE_KEY requerido para Pro preflight publico")
    active_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
    assert_pro_target(active_url)
    get_secret_key()
    db = DatabaseClient()
    report = build_report(db)
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    if report["report_status"] in {"INCOMPLETE", "READ_ERROR"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
