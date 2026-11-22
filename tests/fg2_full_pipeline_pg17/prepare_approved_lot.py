"""Build a synthetic approved lot from the fixture's current processed rows."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.fg2_bounded_run import (  # noqa: E402
    FG2_LIMITS,
    FG2ApprovedLotManifest,
    approved_url_alias_filter,
    course_url_alias_filter,
    stable_json_sha256,
    url_sha256,
    validate_controlled_profile,
)
from scripts.shared.db_client import get_db_client  # noqa: E402


INSTITUTION_ID = "20000000-0000-0000-0000-000000000001"
REFRESH_URL = "https://ssr.fg2.example/programas/analitica-aplicada"
REFERENCE = "fixture-processed-refresh-existing-course"
SOURCE_SHA = os.environ["GITHUB_SHA"]
TARGET = Path("/run/fg2-approved-lot.json")


def select(client, table: str, filters: str, columns: str, *, pipeline: bool):
    method = client.select_pipeline_raise if pipeline else client.select_service_raise
    rows = method(table, filters=filters, columns=columns, order="id.asc", limit=2)
    if not isinstance(rows, list):
        raise SystemExit(f"phase=approved_lot_fixture|result=FAIL|code=malformed_{table}")
    return rows


def merge_by_id(*groups: list[dict]) -> list[dict]:
    records = {}
    for group in groups:
        for row in group:
            row_id = str(row["id"]).lower()
            if row_id in records and records[row_id] != row:
                raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=snapshot_reference_conflict")
            records[row_id] = row
    return sorted(records.values(), key=lambda row: str(row["id"]).lower())


def main() -> None:
    if len(SOURCE_SHA) != 40 or any(character not in "0123456789abcdef" for character in SOURCE_SHA):
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=invalid_source_sha")

    client = get_db_client()
    institutions = select(
        client,
        "institutions",
        f"id=eq.{INSTITUTION_ID}",
        "id,slug,website_url",
        pipeline=False,
    )
    profiles = select(
        client,
        "institution_site_profiles",
        f"institution_id=eq.{INSTITUTION_ID}",
        "*",
        pipeline=True,
    )
    if len(institutions) != 1 or len(profiles) != 1:
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=fixture_binding_not_unique")
    institution = institutions[0]
    profile = profiles[0]
    preflight = validate_controlled_profile(
        institution,
        profile,
        selected_seed_urls=[REFRESH_URL],
    )

    staging_columns = "id,institution_id,url,status,content_hash"
    course_columns = "id,institution_id,url,is_active,is_verified,last_404_at"
    cleansed_columns = "id,staging_id,institution_id,url,status"
    enriched_columns = "id,cleansed_id,institution_id,url,status"
    staging_rows = select(
        client,
        "staging_raw",
        f"institution_id=eq.{INSTITUTION_ID}&{approved_url_alias_filter([REFRESH_URL])}",
        staging_columns,
        pipeline=True,
    )
    course_rows = select(
        client,
        "courses",
        f"institution_id=eq.{INSTITUTION_ID}&{course_url_alias_filter([REFRESH_URL])}",
        course_columns,
        pipeline=False,
    )
    if len(staging_rows) != 1 or len(course_rows) != 1:
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=refresh_identity_not_unique")
    if staging_rows[0].get("status") != "processed":
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=staging_not_processed")
    prior_hash = staging_rows[0].get("content_hash")
    if not isinstance(prior_hash, str) or len(prior_hash) != 64:
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=prior_hash_invalid")
    try:
        int(prior_hash, 16)
    except ValueError:
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=prior_hash_invalid") from None

    cleansed_by_url = select(
        client,
        "cleansed_programs",
        approved_url_alias_filter([REFRESH_URL]),
        cleansed_columns,
        pipeline=True,
    )
    cleansed_by_staging = select(
        client,
        "cleansed_programs",
        f"staging_id=in.({staging_rows[0]['id']})",
        cleansed_columns,
        pipeline=True,
    )
    cleansed_rows = merge_by_id(cleansed_by_url, cleansed_by_staging)
    if len(cleansed_rows) != 1:
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=cleansed_identity_not_unique")
    enriched_by_url = select(
        client,
        "enriched_programs",
        approved_url_alias_filter([REFRESH_URL]),
        enriched_columns,
        pipeline=True,
    )
    enriched_by_cleansed = select(
        client,
        "enriched_programs",
        f"cleansed_id=in.({cleansed_rows[0]['id']})",
        enriched_columns,
        pipeline=True,
    )
    enriched_rows = merge_by_id(enriched_by_url, enriched_by_cleansed)
    if len(enriched_rows) != 1:
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=enriched_identity_not_unique")

    profile_binding = {
        "institution_id": INSTITUTION_ID,
        "institution_sha256": stable_json_sha256(
            {
                "id": str(institution["id"]).lower(),
                "slug": institution.get("slug"),
                "website_url": institution.get("website_url"),
            }
        ),
        "profile_sha256": preflight["profile_sha256"],
        "seed_sha256": preflight["seed_sha256"],
        "seed_urls": preflight["seed_urls"],
    }
    payload = {
        "schema_version": 1,
        "reference": REFERENCE,
        "source_sha": SOURCE_SHA,
        "limits": dict(FG2_LIMITS),
        "institutions": [profile_binding],
        "scope": [
            {
                "institution_id": INSTITUTION_ID,
                "url": REFRESH_URL,
                "url_sha256": url_sha256(REFRESH_URL),
                "kind": "refresh_existing",
                "snapshot": {
                    "staging_rows": staging_rows,
                    "course_rows": course_rows,
                    "cleansed_rows": cleansed_rows,
                    "enriched_rows": enriched_rows,
                },
            }
        ],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        FG2ApprovedLotManifest.from_bytes(
            raw,
            payload,
            expected_sha256=digest,
            expected_reference=REFERENCE,
            expected_source_sha=SOURCE_SHA,
        )
    except Exception as exc:
        raise SystemExit("phase=approved_lot_fixture|result=FAIL|code=manifest_rejected") from exc
    TARGET.write_bytes(raw)
    TARGET.chmod(0o644)
    print(
        f"phase=approved_lot_fixture|result=PASS|reference={REFERENCE}|"
        f"sha256={digest}|scope_urls=1|staging=1|courses=1|cleansed=1|enriched=1"
    )


if __name__ == "__main__":
    main()
