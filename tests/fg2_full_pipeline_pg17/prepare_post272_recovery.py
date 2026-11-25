"""Exercise the production recovery manifest builder with a synthetic DB."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core import fg2_bounded_run as fg2  # noqa: E402
from scripts.shared.db_client import get_db_client  # noqa: E402


INSTITUTION_ID = "20000000-0000-0000-0000-000000000001"
BASE_URL = "https://ssr.fg2.example/programas/post272-refresh-"
RUN_ID = os.environ.get("GITHUB_RUN_ID", "9000005")
RUN_ATTEMPT = int(os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
SOURCE_SHA = os.environ["GITHUB_SHA"].lower()
OLD_RUN_ID = "9000004"
OLD_SOURCE_SHA = "9" * 40
OLD_REFERENCE = "synthetic-source-272"
OLD_LOT_SHA256 = "a" * 64
NEW_REFERENCE = "synthetic-post272-recovery"
TARGET = Path(os.environ.get("FG2_FIXTURE_EXPORT_MANIFEST", "/run/fg2-cohort-manifest.json"))
SOURCE_TARGET = Path("/run/post272-source-manifest.json")
COURSE_IDS = {
    n: f"53000000-0000-0000-0000-{n:012d}" for n in range(1, 9)
}
STAGING_IDS = {
    n: f"52000000-0000-0000-0000-{n:012d}" for n in range(1, 7)
}
CLEANSED_IDS = {
    n: f"54000000-0000-0000-0000-{n:012d}" for n in range(1, 9)
}
ENRICHED_IDS = {
    n: f"55000000-0000-0000-0000-{n:012d}" for n in range(1, 9)
}


def select(client, table: str, filters: str, columns: str, *, pipeline: bool):
    method = client.select_pipeline_raise if pipeline else client.select_service_raise
    rows = method(table, filters=filters, columns=columns, limit=2, order="id.asc")
    if not isinstance(rows, list) or len(rows) != 1:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=identity_not_unique")
    return rows[0]


def encode_payload(payload: dict) -> tuple[bytes, str]:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return raw, hashlib.sha256(raw).hexdigest()


def main() -> None:
    if len(SOURCE_SHA) != 40 or any(character not in "0123456789abcdef" for character in SOURCE_SHA):
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=invalid_current_source_sha")
    if SOURCE_SHA == OLD_SOURCE_SHA or RUN_ID == OLD_RUN_ID:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=run_identity_alias")

    client = get_db_client()
    institution = select(
        client, "institutions", f"id=eq.{INSTITUTION_ID}", "id,slug,website_url", pipeline=False
    )
    profiles = client.select_pipeline_raise(
        "institution_site_profiles",
        filters=f"institution_id=eq.{INSTITUTION_ID}", columns="*", limit=2,
    )
    if not isinstance(profiles, list) or len(profiles) != 1:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=profile_not_unique")
    profile = profiles[0]
    seeds = profile.get("seed_urls") or []
    if isinstance(seeds, str):
        seeds = json.loads(seeds)
    preflight = fg2.validate_controlled_profile(
        institution, profile, selected_seed_urls=seeds,
    )
    institution_sha = fg2.stable_json_sha256({
        "id": str(institution["id"]).lower(),
        "slug": institution.get("slug"),
        "website_url": institution.get("website_url"),
    })
    institution_binding = {
        "institution_id": INSTITUTION_ID,
        "institution_sha256": institution_sha,
        "profile_sha256": preflight["profile_sha256"],
        "seed_sha256": preflight["seed_sha256"],
        "seed_urls": preflight["seed_urls"],
    }

    source_institution = {
        "institution_id": INSTITUTION_ID,
        "profile_sha256": preflight["profile_sha256"],
        "seed_sha256": preflight["seed_sha256"],
        "http_requests": 7,
        "unique_urls": 7,
        "result": "deferred",
    }
    fg2.initialize_manifest(
        SOURCE_TARGET,
        run_id=OLD_RUN_ID,
        run_attempt=1,
        source_sha=OLD_SOURCE_SHA,
        institutions=[source_institution],
        approved_lot_reference=OLD_REFERENCE,
        approved_lot_sha256=OLD_LOT_SHA256,
    )

    url_alias_hash_differences = 0
    for ordinal in range(1, 9):
        url = f"{BASE_URL}{ordinal:02d}"
        staging_id = STAGING_IDS[ordinal] if ordinal <= 6 else f"52000000-0000-0000-0000-{ordinal:012d}"
        staging = select(
            client, "staging_raw", f"id=eq.{staging_id}",
            "id,institution_id,url,status,content_hash", pipeline=True,
        )
        course_id = COURSE_IDS[ordinal]
        # A processed refresh discovery row records the previous content hash;
        # the later manifest entry binds the stored post-harvest content. The
        # requested discovery URL and stored raw URL can also hash differently
        # when their slash aliases differ, while resolving to one course identity.
        discovery_url = url
        previous_hash = hashlib.sha256(
            f"pre-harvest-approved-content-{ordinal}".encode("utf-8")
        ).hexdigest()
        discovery = {
            "institution_id": INSTITUTION_ID,
            "staging_id": staging_id,
            "course_id": course_id,
            "url_sha256": fg2.url_sha256(discovery_url),
            "initial_status": "processed",
            "kind": "refresh_existing",
            "content_sha256": previous_hash if ordinal <= 6 else staging["content_hash"],
        }
        fg2.append_manifest_discovery_row(SOURCE_TARGET, discovery)
        if ordinal <= 6:
            cleansed = select(
                client, "cleansed_programs", f"id=eq.{CLEANSED_IDS[ordinal]}",
                "id,staging_id,institution_id,url,status", pipeline=True,
            )
            entry = {
                "institution_id": INSTITUTION_ID,
                "staging_id": staging_id,
                "course_id": course_id,
                "url_sha256": fg2.url_sha256(staging["url"]),
                "cleansed_url_sha256": fg2.url_sha256(cleansed["url"]),
                "content_sha256": staging["content_hash"],
                "kind": "refresh_existing",
            }
            if discovery["url_sha256"] != entry["url_sha256"]:
                url_alias_hash_differences += 1
            fg2.append_manifest_entry(SOURCE_TARGET, entry)
    if url_alias_hash_differences != 6:
        raise SystemExit(
            "phase=post272_recovery_manifest|result=FAIL|code=url_alias_digest_semantics_not_exercised"
        )
    source_digest = fg2.manifest_file_sha256(SOURCE_TARGET)

    source_contract = {
        "run_id": OLD_RUN_ID,
        "run_attempt": 1,
        "source_sha": OLD_SOURCE_SHA,
        "workflow_id": 261386590,
        "artifact_id": "9000004001",
        "artifact_sha256": "b" * 64,
        "manifest_sha256": source_digest,
        "approved_lot_reference": OLD_REFERENCE,
        "approved_lot_sha256": OLD_LOT_SHA256,
    }
    # Test fixture provenance is synthetic. Production keeps these constants
    # pinned to the immutable GitHub #272 run and artifact.
    original_source = fg2.FG2_POST272_RECOVERY_SOURCE
    original_institution_id = fg2.FG2_POST272_RECOVERY_INSTITUTION_ID
    original_course_staging = fg2.FG2_POST272_RECOVERY_COURSE_STAGING_IDS
    original_excluded_course = fg2.FG2_POST272_RECOVERY_EXCLUDED_COURSE_ID
    fg2.FG2_POST272_RECOVERY_SOURCE = source_contract
    fg2.FG2_POST272_RECOVERY_INSTITUTION_ID = INSTITUTION_ID
    fg2.FG2_POST272_RECOVERY_COURSE_STAGING_IDS = {
        COURSE_IDS[n]: STAGING_IDS[n] for n in range(1, 7)
    }
    fg2.FG2_POST272_RECOVERY_EXCLUDED_COURSE_ID = COURSE_IDS[6]

    scope = []
    for ordinal in range(1, 6):
        url = f"{BASE_URL}{ordinal:02d}"
        snapshot = {
            "staging_rows": [select(
                client, "staging_raw", f"id=eq.{STAGING_IDS[ordinal]}",
                "id,institution_id,url,status,content_hash", pipeline=True,
            )],
            "course_rows": [select(
                client, "courses", f"id=eq.{COURSE_IDS[ordinal]}",
                "id,institution_id,url,is_active,is_verified,last_404_at", pipeline=False,
            )],
            "cleansed_rows": [select(
                client, "cleansed_programs", f"id=eq.{CLEANSED_IDS[ordinal]}",
                "id,staging_id,institution_id,url,status,modality", pipeline=True,
            )],
            "enriched_rows": [select(
                client, "enriched_programs", f"id=eq.{ENRICHED_IDS[ordinal]}",
                "id,cleansed_id,institution_id,url,status", pipeline=True,
            )],
        }
        scope.append({
            "institution_id": INSTITUTION_ID,
            "url": url,
            "url_sha256": fg2.url_sha256(url),
            "kind": "refresh_existing",
            "snapshot": snapshot,
        })
    lot_payload = {
        "schema_version": 1,
        "reference": NEW_REFERENCE,
        "source_sha": SOURCE_SHA,
        "limits": dict(fg2.FG2_LIMITS),
        "institutions": [institution_binding],
        "scope": scope,
    }
    lot_raw, lot_digest = encode_payload(lot_payload)
    approved_lot = fg2.FG2ApprovedLotManifest.from_bytes(
        lot_raw, lot_payload, expected_sha256=lot_digest,
        expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
    )
    fg2.verify_approved_lot_scope(client, approved_lot)

    def assert_source_rejected(source_payload: dict, label: str) -> None:
        mutated_source = Path(f"/run/post272-source-{label}.json")
        raw, source_digest = encode_payload(source_payload)
        mutated_source.write_bytes(raw)
        pinned_source = fg2.FG2_POST272_RECOVERY_SOURCE
        fg2.FG2_POST272_RECOVERY_SOURCE = {
            **pinned_source,
            "manifest_sha256": source_digest,
        }
        try:
            fg2.build_post272_enrichment_recovery_manifest(
                TARGET, source_manifest_path=mutated_source, approved_lot=approved_lot,
                run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
                profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
            )
        except fg2.InvalidControlledRun:
            pass
        else:
            raise SystemExit(
                f"phase=post272_recovery_manifest|result=FAIL|code={label}_source_accepted"
            )
        finally:
            fg2.FG2_POST272_RECOVERY_SOURCE = pinned_source
            mutated_source.unlink(missing_ok=True)

    # A deferred institution is a valid partial outcome only when the rows
    # selected for recovery have their own linked entry/discovery/snapshot and
    # current cleansing evidence. The old cohort may not be relabeled complete.
    complete_source = json.loads(SOURCE_TARGET.read_text(encoding="utf-8"))
    complete_source["institutions"][0].update({
        "result": "complete", "http_requests": 8, "unique_urls": 8,
    })
    assert_source_rejected(complete_source, "complete_8_of_8")

    unchanged_content_source = json.loads(SOURCE_TARGET.read_text(encoding="utf-8"))
    first_entry = unchanged_content_source["entries"][0]
    first_discovery = next(
        row for row in unchanged_content_source["discovery_rows"]
        if row["staging_id"] == first_entry["staging_id"]
    )
    first_discovery["content_sha256"] = first_entry["content_sha256"]
    assert_source_rejected(unchanged_content_source, "missing_harvest_delta")

    wrong_source_identity = json.loads(SOURCE_TARGET.read_text(encoding="utf-8"))
    wrong_source_identity["discovery_rows"][0]["institution_id"] = COURSE_IDS[1]
    assert_source_rejected(wrong_source_identity, "wrong_discovery_identity")

    # Wrong byte digest, wrong course ID and changed prior content hash must
    # all fail before worker selection or writes.
    try:
        fg2.FG2ApprovedLotManifest.from_bytes(
            lot_raw, lot_payload, expected_sha256="0" * 64,
            expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=wrong_lot_digest_accepted")

    wrong_identity = copy.deepcopy(lot_payload)
    wrong_identity["scope"][0]["snapshot"]["course_rows"][0]["id"] = COURSE_IDS[7]
    wrong_identity_raw, wrong_identity_digest = encode_payload(wrong_identity)
    wrong_identity_lot = fg2.FG2ApprovedLotManifest.from_bytes(
        wrong_identity_raw, wrong_identity, expected_sha256=wrong_identity_digest,
        expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
    )
    try:
        fg2.build_post272_enrichment_recovery_manifest(
            TARGET, source_manifest_path=SOURCE_TARGET, approved_lot=wrong_identity_lot,
            run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
            profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=wrong_course_id_accepted")

    wrong_hash = copy.deepcopy(lot_payload)
    wrong_hash["scope"][0]["snapshot"]["staging_rows"][0]["content_hash"] = "c" * 64
    wrong_hash_raw, wrong_hash_digest = encode_payload(wrong_hash)
    wrong_hash_lot = fg2.FG2ApprovedLotManifest.from_bytes(
        wrong_hash_raw, wrong_hash, expected_sha256=wrong_hash_digest,
        expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
    )
    try:
        fg2.build_post272_enrichment_recovery_manifest(
            TARGET, source_manifest_path=SOURCE_TARGET, approved_lot=wrong_hash_lot,
            run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
            profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=wrong_prior_hash_accepted")

    wrong_cleanse_status = copy.deepcopy(lot_payload)
    wrong_cleanse_status["scope"][0]["snapshot"]["cleansed_rows"][0]["status"] = "synced"
    wrong_cleanse_status_raw, wrong_cleanse_status_digest = encode_payload(wrong_cleanse_status)
    wrong_cleanse_status_lot = fg2.FG2ApprovedLotManifest.from_bytes(
        wrong_cleanse_status_raw, wrong_cleanse_status,
        expected_sha256=wrong_cleanse_status_digest,
        expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
    )
    try:
        fg2.build_post272_enrichment_recovery_manifest(
            TARGET, source_manifest_path=SOURCE_TARGET, approved_lot=wrong_cleanse_status_lot,
            run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
            profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=cleansing_status_drift_accepted")

    wrong_raw_status = copy.deepcopy(lot_payload)
    wrong_raw_status["scope"][0]["snapshot"]["staging_rows"][0]["status"] = "pending"
    wrong_raw_status_bytes, wrong_raw_status_digest = encode_payload(wrong_raw_status)
    try:
        wrong_raw_status_lot = fg2.FG2ApprovedLotManifest.from_bytes(
            wrong_raw_status_bytes, wrong_raw_status,
            expected_sha256=wrong_raw_status_digest,
            expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
        )
        fg2.build_post272_enrichment_recovery_manifest(
            TARGET, source_manifest_path=SOURCE_TARGET, approved_lot=wrong_raw_status_lot,
            run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
            profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=raw_status_drift_accepted")

    wrong_downstream_reference = copy.deepcopy(lot_payload)
    wrong_downstream_reference["scope"][0]["snapshot"]["cleansed_rows"][0]["staging_id"] = STAGING_IDS[6]
    wrong_reference_bytes, wrong_reference_digest = encode_payload(wrong_downstream_reference)
    try:
        wrong_reference_lot = fg2.FG2ApprovedLotManifest.from_bytes(
            wrong_reference_bytes, wrong_downstream_reference,
            expected_sha256=wrong_reference_digest,
            expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
        )
        fg2.build_post272_enrichment_recovery_manifest(
            TARGET, source_manifest_path=SOURCE_TARGET, approved_lot=wrong_reference_lot,
            run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
            profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=downstream_reference_drift_accepted")

    wrong_staging = copy.deepcopy(lot_payload)
    wrong_staging["scope"][0]["snapshot"]["staging_rows"][0]["id"] = STAGING_IDS[6]
    wrong_staging_raw, wrong_staging_digest = encode_payload(wrong_staging)
    try:
        wrong_staging_lot = fg2.FG2ApprovedLotManifest.from_bytes(
            wrong_staging_raw, wrong_staging, expected_sha256=wrong_staging_digest,
            expected_reference=NEW_REFERENCE, expected_source_sha=SOURCE_SHA,
        )
        fg2.build_post272_enrichment_recovery_manifest(
            TARGET, source_manifest_path=SOURCE_TARGET, approved_lot=wrong_staging_lot,
            run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
            profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=wrong_staging_id_accepted")

    damaged_source = Path("/run/post272-source-damaged.json")
    damaged_source.write_bytes(SOURCE_TARGET.read_bytes() + b" ")
    try:
        fg2.build_post272_enrichment_recovery_manifest(
            TARGET, source_manifest_path=damaged_source, approved_lot=approved_lot,
            run_id=RUN_ID, run_attempt=RUN_ATTEMPT, source_sha=SOURCE_SHA,
            profile_sha256=preflight["profile_sha256"], seed_sha256=preflight["seed_sha256"],
        )
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=wrong_source_artifact_accepted")
    finally:
        damaged_source.unlink(missing_ok=True)

    digest = fg2.build_post272_enrichment_recovery_manifest(
        TARGET,
        source_manifest_path=SOURCE_TARGET,
        approved_lot=approved_lot,
        run_id=RUN_ID,
        run_attempt=RUN_ATTEMPT,
        source_sha=SOURCE_SHA,
        profile_sha256=preflight["profile_sha256"],
        seed_sha256=preflight["seed_sha256"],
    )
    manifest = fg2.FG2CohortManifest.load(
        TARGET,
        expected_sha256=digest,
        expected_run_id=RUN_ID,
        expected_run_attempt=RUN_ATTEMPT,
        expected_source_sha=SOURCE_SHA,
        expected_approved_lot_reference=NEW_REFERENCE,
        expected_approved_lot_sha256=lot_digest,
    )
    wrong_provenance = copy.deepcopy(manifest.payload)
    wrong_provenance["recovery_source"]["artifact_sha256"] = "0" * 64
    try:
        fg2.FG2CohortManifest.from_payload(wrong_provenance)
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=wrong_source_artifact_hash_accepted")

    fabricated_discovery = copy.deepcopy(manifest.payload)
    first_evidence = fabricated_discovery["recovery_source"]["row_evidence"][0]
    fabricated_discovery["discovery_rows"] = [{
        "institution_id": INSTITUTION_ID,
        "staging_id": first_evidence["staging_id"],
        "course_id": first_evidence["course_id"],
        "url_sha256": first_evidence["source_discovery_url_sha256"],
        "initial_status": "processed",
        "kind": "refresh_existing",
        # This is the post-harvest hash, not a new run's pre-harvest value.
        "content_sha256": first_evidence["current_content_sha256"],
    }]
    try:
        fg2.FG2CohortManifest.from_payload(fabricated_discovery)
    except fg2.InvalidControlledRun:
        pass
    else:
        raise SystemExit(
            "phase=post272_recovery_manifest|result=FAIL|code=synthetic_new_run_discovery_accepted"
        )
    if (
        len(manifest.payload["entries"]) != 5
        or manifest.payload["discovery_rows"]
        or manifest.payload["institutions"][0]["result"] != "resumed"
        or manifest.payload["recovery_source"]["run_id"] != OLD_RUN_ID
        or manifest.payload["recovery_source"]["source_sha"] != OLD_SOURCE_SHA
        or manifest.payload["run_id"] == OLD_RUN_ID
        or manifest.payload["source_sha"] == OLD_SOURCE_SHA
        or manifest.payload["blocked_staging_rows"]
        or manifest.payload["recovery_source"]["source_summary"] != {
            "result": "deferred", "http_requests": 7, "unique_urls": 7,
            "entry_count": 6, "discovery_row_count": 8,
        }
        or len(manifest.payload["recovery_source"]["row_evidence"]) != 5
        or any(
            item["cleansed_modality_snapshot"] is None
            or item["cleansed_modality_snapshot"]["authorization_basis"] != "approved_lot_exact_digest"
            or item["cleansed_modality_snapshot"]["approved_lot_sha256"] != approved_lot.sha256
            for item in manifest.payload["recovery_source"]["row_evidence"]
        )
    ):
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=new_run_binding_or_scope_mismatch")

    print(
        "phase=post272_recovery_manifest|result=PASS|mode=enrichment_sync_only|"
        "entries=5|authorized_modality_snapshots=5|out_of_scope_excluded=1|discovery_only_excluded=2|"
        f"source_run={OLD_RUN_ID}|current_run={RUN_ID}|current_sha={SOURCE_SHA}|"
        f"artifact_digest_checked=true|lot_digest_checked=true|manifest_sha256={digest}|"
        "source_result=deferred|source_http_requests=7|source_unique_urls=7|"
        "source_entries=6|source_discovery_rows=8|prior_hashes_distinct=6|"
        f"url_alias_hashes_differ={url_alias_hash_differences}|new_run_discovery_rows=0|"
        "invalid_bindings_rejected=12|"
        "hash_semantics=source_discovery_prior_vs_entry_stored_vs_current_snapshot"
    )
    for name, value in (
        ("FG2_POST272_RECOVERY_SOURCE", original_source),
        ("FG2_POST272_RECOVERY_INSTITUTION_ID", original_institution_id),
        ("FG2_POST272_RECOVERY_COURSE_STAGING_IDS", original_course_staging),
        ("FG2_POST272_RECOVERY_EXCLUDED_COURSE_ID", original_excluded_course),
    ):
        setattr(fg2, name, value)


if __name__ == "__main__":
    main()
