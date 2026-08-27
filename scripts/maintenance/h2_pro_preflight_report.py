"""Read-only H2 Pro preflight report for JIT preparation.

Produces the expected cohort count and ordered ID digest required by
db-sync-to-pro before applying the h2-expand-compat manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from scripts.shared.db_client import DatabaseClient  # noqa: E402
from scripts.shared.supabase_credentials import get_secret_key  # noqa: E402

PRO_PROJECT_REF = "xwhtiqmboljkshrtviyw"


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
    )


def public_get(db: DatabaseClient, path: str) -> requests.Response:
    return requests.get(
        f"{db.supabase_url}/rest/v1/{path}",
        headers=db._get_headers(use_service_role=False),
        timeout=30,
    )


def select_all(db: DatabaseClient, table: str, columns: str, *, use_service_role: bool) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    page_size = 1000
    while True:
        path = f"{table}?select={columns}&limit={page_size}&offset={offset}"
        res = service_get(db, path) if use_service_role else public_get(db, path)
        if res.status_code != 200:
            raise RuntimeError(
                f"No se pudo leer {table}: {res.status_code} {(res.text or '')[:200]}"
            )
        page = res.json() if res.content else []
        rows.extend(page)
        if len(page) < page_size:
            return rows
        offset += page_size


def select_service_all(db: DatabaseClient, table: str, columns: str) -> list[dict]:
    return select_all(db, table, columns, use_service_role=True)


def select_public_all(db: DatabaseClient, table: str, columns: str) -> list[dict]:
    return select_all(db, table, columns, use_service_role=False)


def table_exists(db: DatabaseClient, table: str) -> bool:
    res = service_get(db, f"{table}?select=*&limit=0")
    return res.status_code == 200


def table_has_rows(db: DatabaseClient, table: str) -> bool:
    res = service_get(db, f"{table}?select=*&limit=1")
    if res.status_code != 200:
        raise RuntimeError(
            f"No se pudo verificar si {table} tiene filas: {res.status_code} {(res.text or '')[:200]}"
        )
    rows = res.json() if res.content else []
    return bool(rows)


def rpc_exists(db: DatabaseClient, name: str) -> bool:
    res = service_get(db, f"rpc/{name}")
    return res.status_code != 404


def main() -> None:
    load_pro_environment()
    if not (os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")):
        raise RuntimeError("SUPABASE_URL/NEXT_PUBLIC_SUPABASE_URL requerido para Pro preflight")
    if not os.environ.get("NEXT_SUPABASE_PUBLISHABLE_KEY"):
        raise RuntimeError("NEXT_SUPABASE_PUBLISHABLE_KEY requerido para Pro preflight publico")
    active_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
    expected_host = f"{PRO_PROJECT_REF}.supabase.co"
    parsed = urlparse(active_url)
    if parsed.scheme != "https" or parsed.hostname != expected_host or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise RuntimeError(f"Pro preflight target must be pinned to {expected_host}")
    get_secret_key()
    db = DatabaseClient()

    public_ids = sorted(row["id"] for row in select_public_all(db, "courses", "id") if row.get("id"))
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
    duplicate_pairs = {}
    for row in courses:
        key = (row.get("institution_id"), row.get("slug"))
        if not key[0] or not key[1]:
            continue
        duplicate_pairs[key] = duplicate_pairs.get(key, 0) + 1
    duplicate_pair_count = sum(1 for count in duplicate_pairs.values() if count > 1)
    if duplicate_pair_count:
        raise RuntimeError(
            f"Duplicados institution_id+slug bloquean h2-expand-compat: {duplicate_pair_count} grupos"
        )

    missing_from_public = sorted(set(eligible_ids) - set(public_ids))
    unexpected_public = sorted(set(public_ids) - set(eligible_ids))
    if missing_from_public or unexpected_public:
        raise RuntimeError(
            "Visibilidad publica Pro difiere del contrato elegible: "
            f"missing={len(missing_from_public)}, unexpected={len(unexpected_public)}"
        )

    joined = ",".join(public_ids).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(joined).hexdigest()
    crawler_exclusions_present = table_exists(db, "crawler_exclusions")
    crawler_exclusions_empty = (
        not table_has_rows(db, "crawler_exclusions") if crawler_exclusions_present else True
    )
    h2_objects_present = {
        "course_editorial_state": table_exists(db, "course_editorial_state"),
        "courses_public_effective": table_exists(db, "courses_public_effective"),
        "h2_legacy_public_course_cohort": table_exists(db, "h2_legacy_public_course_cohort"),
        "h2_verify_expand_compat": rpc_exists(db, "h2_verify_expand_compat"),
        "crawler_exclusions": crawler_exclusions_present,
    }
    stale_h2_objects = [
        name
        for name, present in h2_objects_present.items()
        if present and name not in {"crawler_exclusions"}
    ]
    if stale_h2_objects:
        raise RuntimeError(
            "Objetos H2 Pro ya existen antes de h2-expand-compat; revisar drift parcial: "
            + ", ".join(stale_h2_objects)
        )
    if crawler_exclusions_present and not crawler_exclusions_empty and os.environ.get(
        "H2_ALLOW_CRAWLER_EXCLUSIONS_DRIFT"
    ) != "true":
        raise RuntimeError(
            "public.crawler_exclusions tiene filas en Pro; corregir drift o versionar waiver JIT antes de h2-expand-compat"
        )

    report = {
        "schema": "h2-pro-preflight-report-v1",
        "environment": "pro",
        "manifest": "h2-expand-compat",
        "total_courses": len(courses),
        "eligible_count": len(eligible_ids),
        "public_visible_count": len(public_ids),
        "ordered_eligible_ids_digest": digest,
        "missing_from_public_count": len(missing_from_public),
        "unexpected_public_count": len(unexpected_public),
        "duplicate_institution_slug_groups": duplicate_pair_count,
        "crawler_exclusions_empty": crawler_exclusions_empty,
        "h2_objects_present": h2_objects_present,
        "jit_lines": [
            "H2 expected eligible count: " + str(len(eligible_ids)),
            "H2 expected cohort digest: " + digest,
        ],
    }
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
