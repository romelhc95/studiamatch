#!/usr/bin/env python3
"""Promotion approval and O3 closure evidence helpers for HOM-012."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ENVELOPE_SCHEMA = "promotion-jit-envelope-v2"
APPROVAL_EVIDENCE_SCHEMA = "promotion-approval-evidence-v1"
O3_CLOSURE_SCHEMA = "o3-closure-evidence-v1"
CLOUDFLARE_PAGES_APP_ID = 85455
DB_SYNC_RESULT = "NO_DB_CHANGES"
REQUIRED_ENVIRONMENT = "Promotion"

ENVELOPE_FIELDS = {
    "schema", "transaction_id", "approval_id", "grant_id", "repository_id", "repository", "operation",
    "pr_number", "pr_node_id", "premerge_run_id", "premerge_run_attempt", "event_name", "event_action",
    "base_ref", "base_sha", "source_ref", "source_sha", "candidate_ref", "candidate_sha", "candidate_tree",
    "final_wp", "final_digest", "final_tree", "required_reviewer", "required_reviewer_id", "required_merger",
    "required_merger_id", "allowed_side_effects", "environment", "environment_id", "ruleset_id", "ruleset_digest",
    "issued_at", "expires_at", "nonce",
}


def digest_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def attach_payload_digest(payload: dict[str, Any]) -> dict[str, Any]:
    signed = {key: value for key, value in payload.items() if key != "payload_sha256"}
    payload["payload_sha256"] = digest_json(signed)
    return payload


def payload_digest_valid(payload: dict[str, Any]) -> bool:
    digest = payload.get("payload_sha256")
    if not isinstance(digest, str):
        return False
    signed = {key: value for key, value in payload.items() if key != "payload_sha256"}
    return digest_json(signed) == digest


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        if not value.endswith("Z"):
            return None
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return None


def validate_envelope_v2(envelope: dict[str, Any], *, now: datetime | None = None, snapshot: dict[str, Any] | None = None) -> list[str]:
    now = now or datetime.now(UTC)
    errors: list[str] = []
    unknown = set(envelope) - ENVELOPE_FIELDS
    missing = ENVELOPE_FIELDS - set(envelope)
    if unknown:
        errors.append("ENVELOPE_UNKNOWN_FIELDS")
    if missing:
        errors.append("ENVELOPE_MISSING_FIELDS")
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        errors.append("ENVELOPE_SCHEMA_INVALID")
    if envelope.get("event_name") != "pull_request" or envelope.get("event_action") != "opened" or envelope.get("premerge_run_attempt") != 1:
        errors.append("ENVELOPE_EVENT_BINDING_INVALID")
    if envelope.get("environment") != REQUIRED_ENVIRONMENT:
        errors.append("ENVELOPE_ENVIRONMENT_INVALID")
    if envelope.get("required_reviewer") != "romelhc95-approver" or envelope.get("required_reviewer_id") != 306979205:
        errors.append("ENVELOPE_REVIEWER_INVALID")
    if envelope.get("required_merger") != "romelhc95" or envelope.get("required_merger_id") != 18040405:
        errors.append("ENVELOPE_MERGER_INVALID")
    issued = parse_utc(envelope.get("issued_at"))
    expires = parse_utc(envelope.get("expires_at"))
    if issued is None or expires is None or issued >= expires or now >= expires or issued > now:
        errors.append("ENVELOPE_EXPIRY_INVALID")
    ruleset_digest = str(envelope.get("ruleset_digest") or "")
    expected_ruleset_digest = os.environ.get("PROMOTION_RULESET_DIGEST", "")
    if not ruleset_digest.startswith("sha256:"):
        errors.append("ENVELOPE_RULESET_DIGEST_INVALID")
    if expected_ruleset_digest and ruleset_digest != expected_ruleset_digest:
        errors.append("ENVELOPE_RULESET_DIGEST_MISMATCH")
    for key in ("transaction_id", "nonce"):
        if not isinstance(envelope.get(key), str) or len(envelope[key]) < 12:
            errors.append(f"ENVELOPE_{key.upper()}_INVALID")
    if not isinstance(envelope.get("allowed_side_effects"), list) or any(not isinstance(item, str) for item in envelope.get("allowed_side_effects", [])):
        errors.append("ENVELOPE_ALLOWED_SIDE_EFFECTS_INVALID")
    for key in ("repository_id", "environment_id", "ruleset_id", "premerge_run_id", "pr_number", "required_reviewer_id", "required_merger_id"):
        if not isinstance(envelope.get(key), int) or envelope[key] <= 0:
            errors.append(f"ENVELOPE_{key.upper()}_INVALID")
    for key in ("pr_node_id", "approval_id", "grant_id", "repository", "operation"):
        if not isinstance(envelope.get(key), str) or not envelope[key].strip():
            errors.append(f"ENVELOPE_{key.upper()}_INVALID")
    if snapshot:
        environment = snapshot.get("environment") or {}
        ruleset = snapshot.get("ruleset") or {}
        if environment.get("id") is not None and envelope.get("environment_id") != environment.get("id"):
            errors.append("ENVELOPE_ENVIRONMENT_ID_MISMATCH")
        if ruleset.get("id") is not None and envelope.get("ruleset_id") != ruleset.get("id"):
            errors.append("ENVELOPE_RULESET_ID_MISMATCH")
        if ruleset.get("canonical_digest") and envelope.get("ruleset_digest") != ruleset.get("canonical_digest"):
            errors.append("ENVELOPE_RULESET_DIGEST_MISMATCH")
    return errors


def validate_environment_approval(approval: dict[str, Any], envelope: dict[str, Any]) -> list[str]:
    user = approval.get("user") or approval.get("reviewer") or {}
    errors: list[str] = []
    if approval.get("environment_name") not in {None, REQUIRED_ENVIRONMENT}:
        errors.append("APPROVAL_ENVIRONMENT_INVALID")
    if approval.get("run_id") not in {None, envelope.get("premerge_run_id")}:
        errors.append("APPROVAL_RUN_ID_INVALID")
    if user.get("login") != envelope.get("required_reviewer") or user.get("id") != envelope.get("required_reviewer_id"):
        errors.append("APPROVAL_REVIEWER_INVALID")
    if str(approval.get("approval_id") or approval.get("id") or "") != str(envelope.get("approval_id")):
        errors.append("APPROVAL_ID_MISMATCH")
    if not approval.get("approved_at"):
        errors.append("APPROVAL_TIMESTAMP_INVALID")
    return errors


def approval_evidence(envelope: dict[str, Any], *, run_id: int, job_id: int, deployment_approval: dict[str, Any], snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    errors = validate_envelope_v2(envelope, snapshot=snapshot)
    if errors:
        raise ValueError(",".join(errors))
    if envelope.get("premerge_run_id") != run_id:
        raise ValueError("ENVELOPE_RUN_ID_MISMATCH")
    approval_errors = validate_environment_approval(deployment_approval, envelope)
    if approval_errors:
        raise ValueError(",".join(approval_errors))
    approval_id = str(deployment_approval.get("approval_id") or deployment_approval.get("id"))
    payload = {
        "schema": APPROVAL_EVIDENCE_SCHEMA,
        "envelope": envelope,
        "premerge_run_id": run_id,
        "premerge_run_attempt": envelope["premerge_run_attempt"],
        "promotion_boundary_job_id": job_id,
        "deployment_approval_id": approval_id,
        "deployment_approval": {
            "approval_id": approval_id,
            "environment_name": deployment_approval.get("environment_name", REQUIRED_ENVIRONMENT),
            "approved_at": deployment_approval.get("approved_at"),
            "reviewer": {
                "login": (deployment_approval.get("user") or deployment_approval.get("reviewer") or {}).get("login"),
                "id": (deployment_approval.get("user") or deployment_approval.get("reviewer") or {}).get("id"),
            },
        },
        "artifact_name": f"promotion-approval-evidence-pr-{envelope['pr_number']}-run-{run_id}.json",
    }
    return attach_payload_digest(payload)


def db_detect_only_artifact(*, head_sha: str, db_changed: bool, apply_executed: bool, result: str) -> dict[str, Any]:
    payload = {
        "schema": "db-sync-detect-only-v1",
        "head_sha": head_sha,
        "result": result,
        "db_changed": db_changed,
        "apply_executed": apply_executed,
    }
    return attach_payload_digest(payload)


def latest_check(checks: list[dict[str, Any]], *, name: str, head_sha: str, app_id: int | None = None) -> dict[str, Any] | None:
    matches = []
    for check in checks:
        if check.get("name") != name or check.get("head_sha") != head_sha:
            continue
        if app_id is not None and (check.get("app") or {}).get("id") != app_id:
            continue
        matches.append(check)
    if not matches:
        return None
    return max(matches, key=lambda item: (str(item.get("completed_at") or item.get("updated_at") or ""), int(item.get("id") or 0)))


def produce_o3_closure(premerge_evidence: dict[str, Any], checks: list[dict[str, Any]], db_artifacts: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    envelope = premerge_evidence.get("envelope") or {}
    main_merge_sha = premerge_evidence.get("main_merge_sha") or envelope.get("candidate_sha")
    cf = latest_check(checks, name="Cloudflare Pages", head_sha=main_merge_sha, app_id=CLOUDFLARE_PAGES_APP_ID)
    db = latest_check(checks, name="DB Sync Detect Only", head_sha=main_merge_sha, app_id=15368)
    if not cf or cf.get("status") != "completed" or cf.get("conclusion") != "success":
        errors.append("O3_CLOUDFLARE_NOT_CLOSED")
    if not db or db.get("status") != "completed" or db.get("conclusion") != "success":
        errors.append("O3_DB_SYNC_NOT_CLOSED")
    if len(db_artifacts) != 1 or db_artifacts[0].get("result") != DB_SYNC_RESULT:
        errors.append("O3_DB_ARTIFACT_INVALID")
    if db_artifacts and not payload_digest_valid(db_artifacts[0]):
        errors.append("O3_DB_ARTIFACT_DIGEST_INVALID")
    if db_artifacts and (db_artifacts[0].get("apply_executed") is not False or db_artifacts[0].get("db_changed") is not False):
        errors.append("O3_DB_NO_CHANGE_CONTRACT_INVALID")
    if db_artifacts and db_artifacts[0].get("head_sha") != main_merge_sha:
        errors.append("O3_DB_ARTIFACT_SHA_INVALID")
    if errors:
        return None, errors
    closure = {
        "schema": O3_CLOSURE_SCHEMA,
        "status": "CLOSED",
        "repository": envelope.get("repository"),
        "o3_pr_number": envelope.get("pr_number"),
        "candidate_sha": envelope.get("candidate_sha"),
        "main_merge_sha": main_merge_sha,
        "final_tree": envelope.get("final_tree"),
        "premerge_evidence_digest": premerge_evidence.get("payload_sha256"),
        "cloudflare_check_id": cf.get("id"),
        "cloudflare_pages_app_id": CLOUDFLARE_PAGES_APP_ID,
        "db_sync_check_id": db.get("id"),
        "db_sync_app_id": 15368,
        "db_sync_artifact_head_sha": db_artifacts[0].get("head_sha"),
        "db_sync_result": DB_SYNC_RESULT,
        "db_changed": False,
        "apply_executed": False,
    }
    return attach_payload_digest(closure), []


def wait_for_o3_closure(
    premerge_evidence: dict[str, Any],
    checks_provider,
    db_artifacts_provider,
    *,
    attempts: int = 20,
    interval_seconds: float = 30.0,
    sleeper=time.sleep,
) -> tuple[dict[str, Any] | None, list[str]]:
    last_errors: list[str] = []
    for attempt in range(attempts):
        checks = checks_provider()
        db_artifacts = db_artifacts_provider()
        closure, errors = produce_o3_closure(premerge_evidence, checks, db_artifacts)
        if closure is not None:
            return closure, []
        last_errors = errors
        if attempt < attempts - 1:
            sleeper(interval_seconds)
    return None, ["O3_CLOSURE_TIMEOUT", *last_errors]


def validate_o4_consumes_o3(closure: dict[str, Any], *, expected_main_sha: str) -> list[str]:
    errors: list[str] = []
    if closure.get("schema") != O3_CLOSURE_SCHEMA or closure.get("status") != "CLOSED":
        errors.append("O4_O3_CLOSURE_INVALID")
    if closure.get("main_merge_sha") != expected_main_sha:
        errors.append("O4_O3_CLOSURE_SHA_MISMATCH")
    if closure.get("cloudflare_pages_app_id") != CLOUDFLARE_PAGES_APP_ID or closure.get("db_sync_result") != DB_SYNC_RESULT:
        errors.append("O4_O3_CLOSURE_RESULT_INVALID")
    if closure.get("db_changed") is not False or closure.get("apply_executed") is not False:
        errors.append("O4_O3_DB_CONTRACT_INVALID")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-envelope")
    parser.add_argument("--write-approval-evidence")
    parser.add_argument("--write-db-detect-only")
    args = parser.parse_args(argv)
    if args.validate_envelope:
        data = json.loads(Path(args.validate_envelope).read_text(encoding="utf-8"))
        errors = validate_envelope_v2(data)
        if errors:
            print("\n".join(errors))
            return 1
        print("promotion envelope v2 valid")
    if args.write_approval_evidence:
        envelope = json.loads(os.environ.get("R3_JIT_APPROVAL_ENVELOPE", "{}"))
        approval = json.loads(os.environ.get("PROMOTION_ENVIRONMENT_APPROVAL", "{}"))
        snapshot_raw = os.environ.get("PROMOTION_READINESS_SNAPSHOT", "")
        snapshot = json.loads(Path(snapshot_raw).read_text(encoding="utf-8")) if snapshot_raw else None
        run_id = int(os.environ.get("GITHUB_RUN_ID", "0"))
        job_id = int(os.environ.get("PROMOTION_BOUNDARY_JOB_ID", "0"))
        evidence = approval_evidence(
            envelope,
            run_id=run_id,
            job_id=job_id,
            deployment_approval=approval,
            snapshot=snapshot,
        )
        Path(args.write_approval_evidence).write_text(json.dumps(evidence, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("promotion approval evidence written")
    if args.write_db_detect_only:
        artifact = db_detect_only_artifact(
            head_sha=os.environ.get("GITHUB_SHA", ""),
            db_changed=os.environ.get("DB_CHANGED", "") == "true",
            apply_executed=False,
            result=DB_SYNC_RESULT if os.environ.get("DB_CHANGED", "") == "false" else "DB_CHANGES_DETECTED",
        )
        Path(args.write_db_detect_only).write_text(json.dumps(artifact, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("db detect-only artifact written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
