"""Build a synthetic approved lot from the fixture's current processed rows."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.fg2_bounded_run import (  # noqa: E402
    FG2_LIMITS,
    FG2ApprovedLotManifest,
    FG2CohortManifest,
    InvalidControlledRun,
    approved_url_alias_filter,
    append_manifest_discovery_row,
    append_manifest_entry,
    course_url_alias_filter,
    initialize_manifest,
    stable_json_sha256,
    url_sha256,
    validate_controlled_profile,
)
from scripts.core.master_orchestrator import get_institutions  # noqa: E402
from scripts.shared.db_client import get_db_client  # noqa: E402


INSTITUTION_ID = "20000000-0000-0000-0000-000000000001"
REFRESH_URL = "https://ssr.fg2.example/programas/analitica-aplicada"
REFERENCE = "fixture-processed-refresh-existing-course"
SOURCE_SHA = os.environ["GITHUB_SHA"]
TARGET = Path("/run/fg2-approved-lot.json")
UTEC_INSTITUTION_ID = "50d8779c-54fd-437e-b941-e817e202e60c"
UTEC_TARGET_URL = "https://posgrado.utec.edu.pe/maestrias/ciencia-de-datos-inteligencia-artificial"
UTEC_STAGING_ID = "a1d10e6a-0058-4798-82ba-9cf86e0b5077"
UTEC_PRIOR_CONTENT_SHA256 = "4ffc587dc49a2789acde46fdba984b698508f82ef49b49ba4580b75bd984427c"
UTEC_REFERENCE = "fixture-utec-reviewed-exact-new-discovery"
UTEC_ROTATION_TARGET = Path("/run/fg2-approved-lot-rotation.json")
UTEC_ZERO_PROGRESS_URL = "https://posgrado.utec.edu.pe/utec-only/zero-progress"
UTEC_ZERO_PROGRESS_STAGING_ID = "a1d10e6a-0058-4798-82ba-9cf86e0b5088"
UTEC_ZERO_PROGRESS_CONTENT_SHA256 = "5932ff8e8c9f5710b12a885f404ec13f147e122a6e4e1d0409a0cbc6e807b004"
UTEC_ZERO_PROGRESS_REFERENCE = "fixture-utec-reviewed-exact-zero-progress"
UTEC_ZERO_PROGRESS_LOT_TARGET = Path("/run/fg2-zero-progress-approved-lot.json")
UTEC_ZERO_PROGRESS_COHORT_TARGET = Path("/run/fg2-zero-progress-cohort.json")


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


def prepare_utec_reviewed_exact() -> None:
    if len(SOURCE_SHA) != 40 or any(character not in "0123456789abcdef" for character in SOURCE_SHA):
        raise SystemExit("phase=utec_exact_lot_fixture|result=FAIL|code=invalid_source_sha")

    client = get_db_client()
    institutions = select(
        client, "institutions", f"id=eq.{UTEC_INSTITUTION_ID}", "id,slug,website_url", pipeline=False
    )
    profiles = select(
        client, "institution_site_profiles", f"institution_id=eq.{UTEC_INSTITUTION_ID}", "*", pipeline=True
    )
    if len(institutions) != 1:
        raise SystemExit(
            f"phase=utec_exact_lot_fixture|result=FAIL|code=institution_binding_count_{len(institutions)}"
        )
    if len(profiles) != 1:
        raise SystemExit(
            f"phase=utec_exact_lot_fixture|result=FAIL|code=profile_binding_count_{len(profiles)}"
        )
    institution, profile = institutions[0], profiles[0]
    selected_seeds = profile.get("seed_urls")
    if isinstance(selected_seeds, str):
        selected_seeds = json.loads(selected_seeds)
    preflight = validate_controlled_profile(institution, profile, selected_seed_urls=selected_seeds)

    staging_rows = select(
        client,
        "staging_raw",
        f"institution_id=eq.{UTEC_INSTITUTION_ID}&{approved_url_alias_filter([UTEC_TARGET_URL])}",
        "id,institution_id,url,status,content_hash",
        pipeline=True,
    )
    if (
        len(staging_rows) != 1
        or str(staging_rows[0].get("id", "")).lower() != UTEC_STAGING_ID
        or staging_rows[0].get("status") != "discovered"
        or staging_rows[0].get("content_hash") != UTEC_PRIOR_CONTENT_SHA256
    ):
        raise SystemExit("phase=utec_exact_lot_fixture|result=FAIL|code=staging_snapshot_mismatch")

    course_rows = select(
        client,
        "courses",
        f"institution_id=eq.{UTEC_INSTITUTION_ID}&{course_url_alias_filter([UTEC_TARGET_URL])}",
        "id,institution_id,url,is_active,is_verified,last_404_at",
        pipeline=False,
    )
    cleansed_by_url = select(
        client, "cleansed_programs", approved_url_alias_filter([UTEC_TARGET_URL]),
        "id,staging_id,institution_id,url,status,modality", pipeline=True,
    )
    cleansed_by_staging = select(
        client, "cleansed_programs", f"staging_id=in.({UTEC_STAGING_ID})",
        "id,staging_id,institution_id,url,status,modality", pipeline=True,
    )
    cleansed_rows = merge_by_id(cleansed_by_url, cleansed_by_staging)
    enriched_by_url = select(
        client, "enriched_programs", approved_url_alias_filter([UTEC_TARGET_URL]),
        "id,cleansed_id,institution_id,url,status", pipeline=True,
    )
    enriched_by_cleansed = select(
        client,
        "enriched_programs",
        "cleansed_id=in.({})".format(",".join(str(row["id"]) for row in cleansed_rows))
        if cleansed_rows else "id=eq.00000000-0000-0000-0000-000000000000",
        "id,cleansed_id,institution_id,url,status",
        pipeline=True,
    )
    enriched_rows = merge_by_id(enriched_by_url, enriched_by_cleansed)
    if course_rows or cleansed_rows or enriched_rows:
        raise SystemExit("phase=utec_exact_lot_fixture|result=FAIL|code=unexpected_downstream_identity")

    payload = {
        "schema_version": 1,
        "reference": UTEC_REFERENCE,
        "source_sha": SOURCE_SHA,
        "selection_mode": "reviewed_exact",
        "limits": dict(FG2_LIMITS),
        "institutions": [{
            "institution_id": UTEC_INSTITUTION_ID,
            "institution_sha256": stable_json_sha256({
                "id": str(institution["id"]).lower(),
                "slug": institution.get("slug"),
                "website_url": institution.get("website_url"),
            }),
            "profile_sha256": preflight["profile_sha256"],
            "seed_sha256": preflight["seed_sha256"],
            "seed_urls": preflight["seed_urls"],
        }],
        "scope": [{
            "institution_id": UTEC_INSTITUTION_ID,
            "url": UTEC_TARGET_URL,
            "url_sha256": url_sha256(UTEC_TARGET_URL),
            "kind": "new_discovery",
            "snapshot": {
                "staging_rows": staging_rows,
                "course_rows": course_rows,
                "cleansed_rows": cleansed_rows,
                "enriched_rows": enriched_rows,
            },
        }],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    FG2ApprovedLotManifest.from_bytes(
        raw, payload, expected_sha256=digest, expected_reference=UTEC_REFERENCE,
        expected_source_sha=SOURCE_SHA, expected_selection_mode="reviewed_exact",
    )
    TARGET.write_bytes(raw)
    TARGET.chmod(0o644)

    rotation_payload = {**payload, "selection_mode": "rotation_prefix"}
    rotation_raw = json.dumps(
        rotation_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    rotation_digest = hashlib.sha256(rotation_raw).hexdigest()
    FG2ApprovedLotManifest.from_bytes(
        rotation_raw, rotation_payload, expected_sha256=rotation_digest,
        expected_reference=UTEC_REFERENCE, expected_source_sha=SOURCE_SHA,
        expected_selection_mode="rotation_prefix",
    )
    UTEC_ROTATION_TARGET.write_bytes(rotation_raw)
    UTEC_ROTATION_TARGET.chmod(0o644)
    print(
        "phase=utec_exact_lot_fixture|result=PASS|selection=reviewed_exact|"
        f"sha256={digest}|rotation_sha256={rotation_digest}|source_sha={SOURCE_SHA}|scope_urls=1|staging_discovered=1|"
        "courses=0|cleansed=0|enriched=0"
    )


def prepare_utec_zero_progress() -> None:
    """Build a real reviewed_exact cohort whose only row is discarded by UTEC's own rule."""
    if len(SOURCE_SHA) != 40 or any(character not in "0123456789abcdef" for character in SOURCE_SHA):
        raise SystemExit("phase=utec_zero_progress_manifest|result=FAIL|code=invalid_source_sha")

    client = get_db_client()
    institutions = select(
        client, "institutions", f"id=eq.{UTEC_INSTITUTION_ID}", "id,slug,website_url", pipeline=False
    )
    profiles = select(
        client, "institution_site_profiles", f"institution_id=eq.{UTEC_INSTITUTION_ID}", "*", pipeline=True
    )
    staging_rows = select(
        client,
        "staging_raw",
        f"id=eq.{UTEC_ZERO_PROGRESS_STAGING_ID}",
        "id,institution_id,url,status,content_hash",
        pipeline=True,
    )
    if len(institutions) != 1 or len(profiles) != 1 or len(staging_rows) != 1:
        raise SystemExit("phase=utec_zero_progress_manifest|result=FAIL|code=fixture_binding_not_unique")
    institution, profile, staging = institutions[0], profiles[0], staging_rows[0]
    if (
        str(staging.get("institution_id", "")).lower() != UTEC_INSTITUTION_ID
        or staging.get("url") != UTEC_ZERO_PROGRESS_URL
        or staging.get("status") != "discovered"
        or staging.get("content_hash") != UTEC_ZERO_PROGRESS_CONTENT_SHA256
    ):
        raise SystemExit("phase=utec_zero_progress_manifest|result=FAIL|code=staging_snapshot_mismatch")

    selected_seeds = profile.get("seed_urls")
    if isinstance(selected_seeds, str):
        selected_seeds = json.loads(selected_seeds)
    preflight = validate_controlled_profile(
        institution, profile, selected_seed_urls=selected_seeds
    )
    snapshot = {
        "staging_rows": [staging],
        "course_rows": [],
        "cleansed_rows": [],
        "enriched_rows": [],
    }
    lot_payload = {
        "schema_version": 1,
        "reference": UTEC_ZERO_PROGRESS_REFERENCE,
        "source_sha": SOURCE_SHA,
        "selection_mode": "reviewed_exact",
        "limits": dict(FG2_LIMITS),
        "institutions": [{
            "institution_id": UTEC_INSTITUTION_ID,
            "institution_sha256": stable_json_sha256({
                "id": str(institution["id"]).lower(),
                "slug": institution.get("slug"),
                "website_url": institution.get("website_url"),
            }),
            "profile_sha256": preflight["profile_sha256"],
            "seed_sha256": preflight["seed_sha256"],
            "seed_urls": preflight["seed_urls"],
        }],
        "scope": [{
            "institution_id": UTEC_INSTITUTION_ID,
            "url": UTEC_ZERO_PROGRESS_URL,
            "url_sha256": url_sha256(UTEC_ZERO_PROGRESS_URL),
            "kind": "new_discovery",
            "snapshot": snapshot,
        }],
    }
    lot_raw = json.dumps(
        lot_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    lot_digest = hashlib.sha256(lot_raw).hexdigest()
    approved_lot = FG2ApprovedLotManifest.from_bytes(
        lot_raw, lot_payload, expected_sha256=lot_digest,
        expected_reference=UTEC_ZERO_PROGRESS_REFERENCE,
        expected_source_sha=SOURCE_SHA,
        expected_selection_mode="reviewed_exact",
    )
    UTEC_ZERO_PROGRESS_LOT_TARGET.write_bytes(lot_raw)
    UTEC_ZERO_PROGRESS_LOT_TARGET.chmod(0o644)

    manifest_institution = {
        "institution_id": UTEC_INSTITUTION_ID,
        "profile_sha256": preflight["profile_sha256"],
        "seed_sha256": preflight["seed_sha256"],
        "http_requests": 1,
        "unique_urls": 1,
        "result": "complete",
    }
    initialize_manifest(
        UTEC_ZERO_PROGRESS_COHORT_TARGET,
        run_id=os.getenv("GITHUB_RUN_ID", "9000007"),
        run_attempt=int(os.getenv("GITHUB_RUN_ATTEMPT", "1")),
        source_sha=SOURCE_SHA,
        institutions=[manifest_institution],
        approved_lot_reference=approved_lot.reference,
        approved_lot_sha256=approved_lot.sha256,
        approved_lot_selection="reviewed_exact",
    )
    append_manifest_discovery_row(UTEC_ZERO_PROGRESS_COHORT_TARGET, {
        "institution_id": UTEC_INSTITUTION_ID,
        "staging_id": UTEC_ZERO_PROGRESS_STAGING_ID,
        "url_sha256": url_sha256(UTEC_ZERO_PROGRESS_URL),
        "initial_status": "discovered",
        "kind": "new_discovery",
    })
    append_manifest_entry(UTEC_ZERO_PROGRESS_COHORT_TARGET, {
        "institution_id": UTEC_INSTITUTION_ID,
        "staging_id": UTEC_ZERO_PROGRESS_STAGING_ID,
        "url_sha256": url_sha256(UTEC_ZERO_PROGRESS_URL),
        "cleansed_url_sha256": url_sha256(UTEC_ZERO_PROGRESS_URL),
        "content_sha256": UTEC_ZERO_PROGRESS_CONTENT_SHA256,
        "kind": "new_discovery",
    })
    digest_before_export = hashlib.sha256(UTEC_ZERO_PROGRESS_COHORT_TARGET.read_bytes()).hexdigest()
    try:
        # write_manifest_atomic replaces the inode with a mkstemp file (0600).
        # This synthetic artifact is copied by the host runner after the final append.
        UTEC_ZERO_PROGRESS_COHORT_TARGET.chmod(0o644)
    except OSError:
        raise SystemExit("phase=utec_zero_progress_manifest|result=FAIL|code=cohort_export_chmod_failed") from None
    raw_manifest = UTEC_ZERO_PROGRESS_COHORT_TARGET.read_bytes()
    digest_after_export = hashlib.sha256(raw_manifest).hexdigest()
    if digest_after_export != digest_before_export or (UTEC_ZERO_PROGRESS_COHORT_TARGET.stat().st_mode & 0o777) != 0o644:
        raise SystemExit("phase=utec_zero_progress_manifest|result=FAIL|code=cohort_export_integrity_failed")
    cohort = FG2CohortManifest.from_payload(
        json.loads(raw_manifest),
        expected_run_id=os.getenv("GITHUB_RUN_ID", "9000007"),
        expected_run_attempt=int(os.getenv("GITHUB_RUN_ATTEMPT", "1")),
        expected_source_sha=SOURCE_SHA,
        expected_approved_lot_selection="reviewed_exact",
        allow_empty=False,
    )
    if cohort.staging_ids != (UTEC_ZERO_PROGRESS_STAGING_ID,):
        raise SystemExit("phase=utec_zero_progress_manifest|result=FAIL|code=cohort_identity_mismatch")
    print(
        "phase=utec_zero_progress_manifest|result=PASS|selection=reviewed_exact|"
        f"lot_sha256={approved_lot.sha256}|cohort_sha256={digest_after_export}|"
        "scope=1|stage=pending_after_discovery|provider=not_started|export_mode=0644|digest_preserved=true"
    )


def verify_utec_rotation_rejected() -> None:
    raw = UTEC_ROTATION_TARGET.read_bytes()
    payload = json.loads(raw)
    lot = FG2ApprovedLotManifest.from_bytes(
        raw, payload, expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_reference=payload["reference"], expected_source_sha=payload["source_sha"],
        expected_selection_mode="rotation_prefix",
    )
    try:
        get_institutions(
            limit=10, controlled=True, approved_lot=lot,
            approved_lot_selection="rotation_prefix", now=datetime.now(timezone.utc),
        )
    except InvalidControlledRun as exc:
        if "eligible rotation prefix" not in str(exc):
            raise SystemExit("phase=utec_default_rotation|result=FAIL|code=unexpected_rejection") from None
        print("phase=utec_default_rotation|result=PASS|utec=rejected|reason=outside_eligible_rotation_prefix")
        return
    raise SystemExit("phase=utec_default_rotation|result=FAIL|code=utec_was_not_rejected")


def main() -> None:
    if "--utec-reviewed-exact" in sys.argv[1:]:
        prepare_utec_reviewed_exact()
        return
    if "--utec-zero-progress" in sys.argv[1:]:
        prepare_utec_zero_progress()
        return
    if "--verify-utec-rotation-rejected" in sys.argv[1:]:
        verify_utec_rotation_rejected()
        return
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
