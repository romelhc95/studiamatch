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
AMBIGUOUS_ALIAS_IDS = {
    "staging": "52000000-0000-0000-0000-000000000066",
    "cleansed": "54000000-0000-0000-0000-000000000066",
    "enriched": "55000000-0000-0000-0000-000000000066",
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
        "http_requests": 8,
        "unique_urls": 8,
        "result": "complete",
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

    for ordinal in range(1, 9):
        url = f"{BASE_URL}{ordinal:02d}"
        staging_id = STAGING_IDS[ordinal] if ordinal <= 6 else f"52000000-0000-0000-0000-{ordinal:012d}"
        staging = select(
            client, "staging_raw", f"id=eq.{staging_id}",
            "id,institution_id,url,status,content_hash", pipeline=True,
        )
        course_id = COURSE_IDS[ordinal]
        # The source artifact's approved-lot entry is pre-harvest evidence;
        # its discovery row is the post-harvest staging evidence. Keep the
        # stable identity equal while making their hashes independently
        # representative of the real #272 artifact.
        discovery_url = f"{url}?page=1"
        discovery = {
            "institution_id": INSTITUTION_ID,
            "staging_id": staging_id,
            "course_id": course_id,
            "url_sha256": fg2.url_sha256(discovery_url),
            "initial_status": "processed",
            "kind": "refresh_existing",
            "content_sha256": staging["content_hash"],
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
                "url_sha256": fg2.url_sha256(url),
                "cleansed_url_sha256": fg2.url_sha256(cleansed["url"]),
                "content_sha256": hashlib.sha256(
                    f"pre-harvest-approved-content-{ordinal}".encode("utf-8")
                ).hexdigest(),
                "kind": "refresh_existing",
            }
            fg2.append_manifest_entry(SOURCE_TARGET, entry)
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
    original_excluded_url = fg2.FG2_POST272_RECOVERY_EXCLUDED_URL
    fg2.FG2_POST272_RECOVERY_SOURCE = source_contract
    fg2.FG2_POST272_RECOVERY_INSTITUTION_ID = INSTITUTION_ID
    fg2.FG2_POST272_RECOVERY_COURSE_STAGING_IDS = {
        COURSE_IDS[n]: STAGING_IDS[n] for n in range(1, 7)
    }
    fg2.FG2_POST272_RECOVERY_EXCLUDED_COURSE_ID = COURSE_IDS[6]
    fg2.FG2_POST272_RECOVERY_EXCLUDED_URL = f"{BASE_URL}06"

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
                "id,staging_id,institution_id,url,status", pipeline=True,
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
    ambiguous_aliases = fg2.verify_post272_recovery_excluded_identity(client)
    if ambiguous_aliases < 2:
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=sixth_identity_not_ambiguous")

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
    if (
        len(manifest.payload["entries"]) != 5
        or len(manifest.payload["discovery_rows"]) != 5
        or manifest.payload["institutions"][0]["result"] != "resumed"
        or manifest.payload["recovery_source"]["run_id"] != OLD_RUN_ID
        or manifest.payload["recovery_source"]["source_sha"] != OLD_SOURCE_SHA
        or manifest.payload["run_id"] == OLD_RUN_ID
        or manifest.payload["source_sha"] == OLD_SOURCE_SHA
        or len(manifest.payload["blocked_staging_rows"]) != 1
    ):
        raise SystemExit("phase=post272_recovery_manifest|result=FAIL|code=new_run_binding_or_scope_mismatch")

    print(
        "phase=post272_recovery_manifest|result=PASS|mode=enrichment_sync_only|"
        "entries=5|ambiguous_excluded=1|unchanged_excluded=2|"
        f"source_run={OLD_RUN_ID}|current_run={RUN_ID}|current_sha={SOURCE_SHA}|"
        f"artifact_digest_checked=true|lot_digest_checked=true|manifest_sha256={digest}|"
        f"excluded_alias_rows={ambiguous_aliases}|invalid_bindings_rejected=6|"
        "historical_hash_semantics=approved_preharvest_vs_processed_discovery"
    )
    for name, value in (
        ("FG2_POST272_RECOVERY_SOURCE", original_source),
        ("FG2_POST272_RECOVERY_INSTITUTION_ID", original_institution_id),
        ("FG2_POST272_RECOVERY_COURSE_STAGING_IDS", original_course_staging),
        ("FG2_POST272_RECOVERY_EXCLUDED_COURSE_ID", original_excluded_course),
        ("FG2_POST272_RECOVERY_EXCLUDED_URL", original_excluded_url),
    ):
        setattr(fg2, name, value)


if __name__ == "__main__":
    main()
