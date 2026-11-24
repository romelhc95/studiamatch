"""Create an Actions-style downstream handoff for a synthetic #272 recovery."""

from __future__ import annotations

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.fg2_bounded_run import (  # noqa: E402
    FG2CohortManifest,
    append_manifest_discovery_row,
    append_manifest_entry,
    initialize_manifest,
    manifest_file_sha256,
    url_sha256,
    validate_controlled_profile,
)
from scripts.shared.db_client import get_db_client  # noqa: E402


INSTITUTION_ID = "20000000-0000-0000-0000-000000000001"
BASE_URL = "https://ssr.fg2.example/programas/post272-refresh-"
SOURCE_SHA = os.environ["GITHUB_SHA"]
RUN_ID = "9000005"
TARGET = Path("/run/fg2-cohort-manifest.json")


def select(client, table: str, filters: str, columns: str, *, pipeline: bool):
    method = client.select_pipeline_raise if pipeline else client.select_service_raise
    rows = method(table, filters=filters, columns=columns, limit=2)
    if not isinstance(rows, list) or len(rows) != 1:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=identity_not_unique")
    return rows[0]


def main() -> None:
    if len(SOURCE_SHA) != 40 or any(character not in "0123456789abcdef" for character in SOURCE_SHA):
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=invalid_source_sha")

    client = get_db_client()
    institution = select(
        client, "institutions", f"id=eq.{INSTITUTION_ID}", "id,slug,website_url", pipeline=False
    )
    profiles = client.select_pipeline_raise(
        "institution_site_profiles", filters=f"institution_id=eq.{INSTITUTION_ID}", columns="*", limit=2
    )
    if not isinstance(profiles, list) or len(profiles) != 1:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=profile_not_unique")
    profile = profiles[0]
    seeds = profile.get("seed_urls") or []
    if isinstance(seeds, str):
        import json

        seeds = json.loads(seeds)
    preflight = validate_controlled_profile(institution, profile, selected_seed_urls=seeds)
    institution_binding = {
        "institution_id": INSTITUTION_ID,
        "profile_sha256": preflight["profile_sha256"],
        "seed_sha256": preflight["seed_sha256"],
        "http_requests": 0,
        "unique_urls": 8,
        "result": "complete",
    }

    records = []
    for ordinal in range(1, 9):
        url = f"{BASE_URL}{ordinal:02d}"
        staging_id = f"52000000-0000-0000-0000-{ordinal:012d}"
        course_id = f"53000000-0000-0000-0000-{ordinal:012d}"
        cleansed_id = f"54000000-0000-0000-0000-{ordinal:012d}"
        enriched_id = f"55000000-0000-0000-0000-{ordinal:012d}"
        staging = select(
            client, "staging_raw", f"id=eq.{staging_id}",
            "id,institution_id,url,status,content_hash", pipeline=True,
        )
        course = select(
            client, "courses", f"id=eq.{course_id}",
            "id,institution_id,url,is_active,is_verified,last_404_at", pipeline=False,
        )
        cleansed = select(
            client, "cleansed_programs", f"id=eq.{cleansed_id}",
            "id,staging_id,institution_id,url,status", pipeline=True,
        )
        enriched = select(
            client, "enriched_programs", f"id=eq.{enriched_id}",
            "id,cleansed_id,institution_id,url,status", pipeline=True,
        )
        expected_cleanse_state = "pending" if ordinal <= 6 else "synced"
        if (
            staging.get("status") != "processed"
            or staging.get("url") != url
            or staging.get("institution_id") != INSTITUTION_ID
            or cleansed.get("staging_id") != staging_id
            or cleansed.get("status") != expected_cleanse_state
            or enriched.get("cleansed_id") != cleansed_id
            or enriched.get("status") != "synced"
            or course.get("url") != url
            or course.get("institution_id") != INSTITUTION_ID
        ):
            raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=postflight_state_mismatch")
        records.append({
            "ordinal": ordinal,
            "url": url,
            "staging": staging,
            "course": course,
            "cleansed": cleansed,
            "enriched": enriched,
        })

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    initialize_manifest(
        TARGET,
        run_id=RUN_ID,
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[institution_binding],
    )
    for record in records:
        staging = record["staging"]
        course = record["course"]
        entry = {
            "institution_id": INSTITUTION_ID,
            "staging_id": staging["id"],
            "course_id": course["id"],
            "url_sha256": url_sha256(record["url"]),
            "initial_status": "processed",
            "kind": "refresh_existing",
            "content_sha256": staging["content_hash"],
        }
        append_manifest_discovery_row(TARGET, entry)
        if record["ordinal"] <= 6:
            append_manifest_entry(TARGET, {
                "institution_id": INSTITUTION_ID,
                "staging_id": staging["id"],
                "course_id": course["id"],
                "url_sha256": url_sha256(record["url"]),
                "cleansed_url_sha256": url_sha256(record["cleansed"]["url"]),
                "content_sha256": staging["content_hash"],
                "kind": "refresh_existing",
            })

    digest = manifest_file_sha256(TARGET)
    FG2CohortManifest.load(
        TARGET,
        expected_sha256=digest,
        expected_run_id=RUN_ID,
        expected_run_attempt=1,
        expected_source_sha=SOURCE_SHA,
    )
    TARGET.chmod(0o644)
    print("phase=post272_recovery_manifest|result=PASS|refresh_pending=6|unchanged_excluded=2|digest_checked=true")


if __name__ == "__main__":
    main()
