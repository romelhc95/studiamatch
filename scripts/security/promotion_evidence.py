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


ENVELOPE_SCHEMA_V3 = "promotion-jit-envelope-v3"
APPROVAL_EVIDENCE_SCHEMA = "promotion-approval-evidence-v3"
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


def redacted_envelope_summary(envelope: dict[str, Any]) -> dict[str, Any]:
    redacted = {key: value for key, value in envelope.items() if key not in {"approval_id", "nonce"}}
    redacted["approval_id_sha256"] = hashlib.sha256(str(envelope.get("approval_id") or "").encode("utf-8")).hexdigest()
    return redacted


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


def _comment_fingerprint(comment: Any) -> tuple[bool, str | None]:
    if comment is None:
        return False, None
    if not isinstance(comment, str):
        raise ValueError("APPROVAL_COMMENT_INVALID")
    return True, hashlib.sha256(comment.encode("utf-8")).hexdigest()


def validate_envelope_v2(envelope: dict[str, Any], *, now: datetime | None = None, snapshot: dict[str, Any] | None = None) -> list[str]:
    now = now or datetime.now(UTC)
    errors: list[str] = []
    unknown = set(envelope) - ENVELOPE_FIELDS
    missing = ENVELOPE_FIELDS - set(envelope)
    if unknown:
        errors.append("ENVELOPE_UNKNOWN_FIELDS")
    if missing:
        errors.append("ENVELOPE_MISSING_FIELDS")
    if envelope.get("schema") != ENVELOPE_SCHEMA_V3:
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


def validate_workflow_gate_binding(binding: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema",
        "source_commit",
        "workflow_path",
        "workflow_name",
        "job_key",
        "api_job_name",
        "environment_name",
        "artifact_producer_in_same_job",
        "extraction_method",
        "remote_request",
        "historical_binding_only",
        "candidate_workflow_must_produce_artifact_in_same_job",
        "source_blob_sha256",
    }
    if set(binding) != required:
        errors.append("WORKFLOW_GATE_SCHEMA_INVALID")
    if binding.get("schema") != "github-workflow-environment-gate-binding-v1":
        errors.append("WORKFLOW_GATE_SCHEMA_INVALID")
    if binding.get("job_key") != "promotion-boundary" or binding.get("api_job_name") != "Promotion Boundary":
        errors.append("WORKFLOW_GATE_JOB_INVALID")
    if binding.get("environment_name") != REQUIRED_ENVIRONMENT:
        errors.append("WORKFLOW_GATE_ENVIRONMENT_INVALID")
    if binding.get("workflow_path") != ".github/workflows/security-audit.yml" or binding.get("workflow_name") != "Security Audit Gate":
        errors.append("WORKFLOW_GATE_WORKFLOW_INVALID")
    if binding.get("artifact_producer_in_same_job") is not True or binding.get("candidate_workflow_must_produce_artifact_in_same_job") is not True:
        errors.append("WORKFLOW_GATE_ARTIFACT_PRODUCER_INVALID")
    if binding.get("remote_request") is not False or binding.get("historical_binding_only") is not False:
        errors.append("WORKFLOW_GATE_PROVENANCE_INVALID")
    if binding.get("extraction_method") not in {"local_workflow_structural_parser_v1", "local_worktree_candidate"}:
        errors.append("WORKFLOW_GATE_EXTRACTION_INVALID")
    digest = binding.get("source_blob_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        errors.append("WORKFLOW_GATE_SOURCE_DIGEST_INVALID")
    return errors


def normalize_environment_approval_history(history: Any, envelope: dict[str, Any], *, run_id: int, run_attempt: int, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    if not isinstance(history, list):
        raise ValueError("APPROVAL_HISTORY_SCHEMA_INVALID")
    if len(history) != 1:
        raise ValueError("APPROVAL_HISTORY_COUNT_INVALID")
    record = history[0]
    if not isinstance(record, dict):
        raise ValueError("APPROVAL_HISTORY_RECORD_INVALID")
    if record.get("state") != "approved":
        raise ValueError("APPROVAL_STATE_INVALID")
    user = record.get("user") or {}
    if not isinstance(user, dict) or user.get("login") != envelope.get("required_reviewer") or user.get("id") != envelope.get("required_reviewer_id"):
        raise ValueError("APPROVAL_REVIEWER_INVALID")
    environments = record.get("environments")
    if not isinstance(environments, list) or len(environments) != 1 or not isinstance(environments[0], dict):
        raise ValueError("APPROVAL_ENVIRONMENT_COUNT_INVALID")
    environment = environments[0]
    if environment.get("name") != REQUIRED_ENVIRONMENT or environment.get("id") != envelope.get("environment_id"):
        raise ValueError("APPROVAL_ENVIRONMENT_INVALID")
    for forbidden in ("run_id", "run_attempt", "created_at", "submitted_at", "approved_at", "deployment_approval_id", "environment_name"):
        if forbidden in record:
            raise ValueError("APPROVAL_OBSERVED_FORBIDDEN_FIELD")
    comment_present, comment_sha256 = _comment_fingerprint(record.get("comment"))
    normalized = {
        "state": "approved",
        "reviewer": {"login": user.get("login"), "id": user.get("id")},
        "environment": {"id": environment.get("id"), "name": environment.get("name"), "can_admins_bypass": environment.get("can_admins_bypass")},
        "comment_present": comment_present,
    }
    if comment_sha256:
        normalized["comment_sha256"] = comment_sha256
    return normalized


def normalize_run_payload(run_payload: dict[str, Any], envelope: dict[str, Any], *, run_id: int) -> dict[str, Any]:
    if not isinstance(run_payload, dict):
        raise ValueError("RUN_SCHEMA_INVALID")
    if run_payload.get("id") != run_id or run_payload.get("id") != envelope.get("premerge_run_id"):
        raise ValueError("RUN_ID_MISMATCH")
    if run_payload.get("run_attempt") != envelope.get("premerge_run_attempt"):
        raise ValueError("RUN_ATTEMPT_INVALID")
    if run_payload.get("event") != "pull_request":
        raise ValueError("RUN_EVENT_INVALID")
    if run_payload.get("head_sha") != envelope.get("candidate_sha"):
        raise ValueError("RUN_HEAD_SHA_INVALID")
    if run_payload.get("head_branch") != envelope.get("candidate_ref"):
        raise ValueError("RUN_HEAD_BRANCH_INVALID")
    if run_payload.get("path") != ".github/workflows/security-audit.yml":
        raise ValueError("RUN_WORKFLOW_PATH_INVALID")
    if parse_utc(run_payload.get("created_at")) is None or parse_utc(run_payload.get("run_started_at")) is None:
        raise ValueError("RUN_TIMESTAMP_INVALID")
    repository = run_payload.get("repository") or {}
    head_repository = run_payload.get("head_repository") or {}
    if repository.get("full_name", "").lower() != str(envelope.get("repository", "")).lower():
        raise ValueError("RUN_REPOSITORY_INVALID")
    if head_repository.get("full_name", "").lower() != str(envelope.get("repository", "")).lower():
        raise ValueError("RUN_HEAD_REPOSITORY_INVALID")
    return {
        "id": run_payload.get("id"),
        "name": run_payload.get("name"),
        "head_branch": run_payload.get("head_branch"),
        "head_sha": run_payload.get("head_sha"),
        "path": run_payload.get("path"),
        "event": run_payload.get("event"),
        "status": run_payload.get("status"),
        "conclusion": run_payload.get("conclusion"),
        "run_attempt": run_payload.get("run_attempt"),
        "created_at": run_payload.get("created_at"),
        "updated_at": run_payload.get("updated_at"),
        "run_started_at": run_payload.get("run_started_at"),
        "repository": {"id": repository.get("id"), "full_name": repository.get("full_name")},
        "head_repository": {"id": head_repository.get("id"), "full_name": head_repository.get("full_name")},
    }


def normalize_promotion_boundary_job(jobs_payload: dict[str, Any], envelope: dict[str, Any], *, run_id: int, premerge: bool = True) -> dict[str, Any]:
    if not isinstance(jobs_payload, dict) or not isinstance(jobs_payload.get("jobs"), list):
        raise ValueError("JOBS_SCHEMA_INVALID")
    jobs = jobs_payload["jobs"]
    if jobs_payload.get("total_count") != len(jobs):
        raise ValueError("JOBS_TOTAL_COUNT_MISMATCH")
    matches = [job for job in jobs if isinstance(job, dict) and job.get("name") == "Promotion Boundary" and job.get("run_id") == run_id and job.get("run_attempt") == envelope.get("premerge_run_attempt") and job.get("head_sha") == envelope.get("candidate_sha")]
    if len(matches) != 1:
        raise ValueError("JOB_COUNT_INVALID")
    job = matches[0]
    if not isinstance(job.get("id"), int) or job.get("id") <= 0:
        raise ValueError("JOB_ID_INVALID")
    if job.get("head_branch") != envelope.get("candidate_ref"):
        raise ValueError("JOB_HEAD_BRANCH_INVALID")
    if job.get("workflow_name") != "Security Audit Gate":
        raise ValueError("JOB_WORKFLOW_INVALID")
    started = parse_utc(job.get("started_at"))
    issued = parse_utc(envelope.get("issued_at"))
    if started is None:
        raise ValueError("JOB_STARTED_AT_INVALID")
    if issued is not None and started < issued:
        raise ValueError("JOB_ENVELOPE_ORDER_INVALID")
    if premerge:
        if job.get("status") != "in_progress" or job.get("conclusion") is not None or job.get("completed_at") is not None:
            raise ValueError("JOB_PREMERGE_STATE_INVALID")
    else:
        completed = parse_utc(job.get("completed_at"))
        if job.get("status") != "completed" or job.get("conclusion") != "success":
            raise ValueError("JOB_POSTMERGE_STATE_INVALID")
        if completed is None:
            raise ValueError("JOB_COMPLETED_AT_INVALID")
        if completed < started:
            raise ValueError("JOB_TIMESTAMP_ORDER_INVALID")
    return {key: job.get(key) for key in ("id", "run_id", "workflow_name", "head_branch", "run_attempt", "head_sha", "status", "conclusion", "created_at", "started_at", "completed_at", "name")}


def validate_environment_approval(approval: dict[str, Any], envelope: dict[str, Any], *, run_id: int, run_attempt: int = 1) -> list[str]:
    user = (approval.get("environment_review") or {}).get("reviewer") or {}
    environment = (approval.get("environment_review") or {}).get("environment") or {}
    errors: list[str] = []
    if approval.get("deployment_approval_id") is not None or approval.get("approved_at") is not None or approval.get("environment_name") is not None:
        errors.append("APPROVAL_LEGACY_FIELDS_INVALID")
    if environment.get("name") != REQUIRED_ENVIRONMENT or environment.get("id") != envelope.get("environment_id"):
        errors.append("APPROVAL_ENVIRONMENT_INVALID")
    if approval.get("run_id") != run_id or approval.get("run_attempt") != run_attempt:
        errors.append("APPROVAL_RUN_ID_INVALID")
    if user.get("login") != envelope.get("required_reviewer") or user.get("id") != envelope.get("required_reviewer_id"):
        errors.append("APPROVAL_REVIEWER_INVALID")
    if approval.get("state") != "approved":
        errors.append("APPROVAL_STATE_INVALID")
    if parse_utc(approval.get("created_at")) is None:
        errors.append("APPROVAL_TIMESTAMP_INVALID")
    if approval.get("environment_review_digest") != digest_json(approval.get("environment_review") or {}):
        errors.append("APPROVAL_REVIEW_DIGEST_INVALID")
    return errors


def approval_evidence(envelope: dict[str, Any], *, run_id: int, job_id: int, deployment_approval: Any, snapshot: dict[str, Any] | None = None, run_payload: dict[str, Any] | None = None, jobs_payload: dict[str, Any] | None = None, workflow_gate_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    errors = validate_envelope_v2(envelope, snapshot=snapshot)
    if errors:
        raise ValueError(",".join(errors))
    if envelope.get("premerge_run_id") != run_id:
        raise ValueError("ENVELOPE_RUN_ID_MISMATCH")
    if snapshot is None:
        raise ValueError("READINESS_SNAPSHOT_REQUIRED")
    if run_payload is None or jobs_payload is None or workflow_gate_binding is None:
        raise ValueError("EVIDENCE_MISSING_FIELDS")
    observed_approval = normalize_environment_approval_history(deployment_approval, envelope, run_id=run_id, run_attempt=envelope["premerge_run_attempt"])
    observed_run = normalize_run_payload(run_payload, envelope, run_id=run_id)
    observed_job = normalize_promotion_boundary_job(jobs_payload, envelope, run_id=run_id, premerge=True)
    if observed_job["id"] != job_id:
        raise ValueError("JOB_ID_INVALID")
    binding_errors = validate_workflow_gate_binding(workflow_gate_binding)
    if binding_errors:
        raise ValueError(",".join(binding_errors))
    snapshot_digest = digest_json(snapshot)
    binding_digest = digest_json(workflow_gate_binding)
    envelope_digest = digest_json(envelope)
    envelope_summary = redacted_envelope_summary(envelope)
    derived = {
        "source_run_id": run_id,
        "source_run_attempt": envelope["premerge_run_attempt"],
        "approvals_endpoint_run_id": run_id,
        "run_endpoint_run_id": run_id,
        "jobs_endpoint_run_id": run_id,
        "jit_approval_reference_sha256": envelope_summary["approval_id_sha256"],
        "envelope_digest": envelope_digest,
        "approval_record_digest": digest_json(observed_approval),
        "run_record_digest": digest_json(observed_run),
        "job_record_digest": digest_json(observed_job),
        "readiness_snapshot_digest": snapshot_digest,
        "workflow_gate_binding_digest": binding_digest,
        "evidence_created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifact_name": f"promotion-approval-evidence-pr-{envelope['pr_number']}-run-{run_id}.json",
    }
    payload = {
        "schema": APPROVAL_EVIDENCE_SCHEMA,
        "envelope_summary": envelope_summary,
        "observed_premerge_approval": observed_approval,
        "observed_premerge_run": observed_run,
        "observed_premerge_job": observed_job,
        "observed_readiness": snapshot,
        "workflow_gate_binding": workflow_gate_binding,
        "derived_context": derived,
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


def exact_completed_check(checks: list[dict[str, Any]], *, name: str, head_sha: str, app_id: int | None = None) -> tuple[dict[str, Any] | None, str | None]:
    matches = []
    terminal_bad = {"failure", "cancelled", "timed_out", "action_required", "stale", "startup_failure", "skipped"}
    for check in checks:
        if check.get("name") != name or check.get("head_sha") != head_sha:
            continue
        if app_id is not None and (check.get("app") or {}).get("id") != app_id:
            return None, "O3_CHECK_APP_INVALID"
        if check.get("conclusion") in terminal_bad:
            return None, "O3_CHECK_TERMINAL_FAILURE"
        matches.append(check)
    if len(matches) != 1:
        return None, "O3_CHECK_COUNT_INVALID"
    check = matches[0]
    if check.get("status") != "completed" or check.get("conclusion") != "success":
        return None, "O3_CHECK_NOT_CLOSED"
    return check, None


def produce_o3_closure(premerge_evidence: dict[str, Any], checks: list[dict[str, Any]], db_artifacts: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    envelope = premerge_evidence.get("envelope_summary") or {}
    main_merge_sha = premerge_evidence.get("main_merge_sha") or envelope.get("candidate_sha")
    cf, cf_error = exact_completed_check(checks, name="Cloudflare Pages", head_sha=main_merge_sha, app_id=CLOUDFLARE_PAGES_APP_ID)
    db, db_error = exact_completed_check(checks, name="DB Sync Detect Only", head_sha=main_merge_sha, app_id=15368)
    if cf_error:
        errors.append(cf_error if cf_error != "O3_CHECK_NOT_CLOSED" else "O3_CLOUDFLARE_NOT_CLOSED")
    if db_error:
        errors.append(db_error if db_error != "O3_CHECK_NOT_CLOSED" else "O3_DB_SYNC_NOT_CLOSED")
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
    parser.add_argument("--approval-history")
    parser.add_argument("--readiness-snapshot")
    parser.add_argument("--run-payload")
    parser.add_argument("--jobs-payload")
    parser.add_argument("--workflow-gate-binding")
    parser.add_argument("--job-id", type=int)
    args = parser.parse_args(argv)
    if args.validate_envelope:
        data = json.loads(Path(args.validate_envelope).read_text(encoding="utf-8"))
        errors = validate_envelope_v2(data)
        if errors:
            print("\n".join(errors))
            return 1
        print("promotion envelope valid")
    if args.write_approval_evidence:
        envelope = json.loads(os.environ.get("R3_JIT_APPROVAL_ENVELOPE", "{}"))
        approval_path = args.approval_history or os.environ.get("PROMOTION_ENVIRONMENT_APPROVAL_HISTORY", "")
        approval = json.loads(Path(approval_path).read_text(encoding="utf-8")) if approval_path else json.loads(os.environ.get("PROMOTION_ENVIRONMENT_APPROVAL", "[]"))
        snapshot_raw = args.readiness_snapshot or os.environ.get("PROMOTION_READINESS_SNAPSHOT", "")
        snapshot = json.loads(Path(snapshot_raw).read_text(encoding="utf-8")) if snapshot_raw else None
        run_raw = args.run_payload or os.environ.get("PROMOTION_RUN_PAYLOAD", "")
        jobs_raw = args.jobs_payload or os.environ.get("PROMOTION_JOBS_PAYLOAD", "")
        binding_raw = args.workflow_gate_binding or os.environ.get("PROMOTION_WORKFLOW_GATE_BINDING", "")
        run_payload = json.loads(Path(run_raw).read_text(encoding="utf-8")) if run_raw else None
        jobs_payload = json.loads(Path(jobs_raw).read_text(encoding="utf-8")) if jobs_raw else None
        workflow_gate_binding = json.loads(Path(binding_raw).read_text(encoding="utf-8")) if binding_raw else None
        run_id = int(os.environ.get("GITHUB_RUN_ID", "0"))
        job_id = args.job_id if args.job_id is not None else int(os.environ.get("PROMOTION_BOUNDARY_JOB_ID", "0"))
        evidence = approval_evidence(
            envelope,
            run_id=run_id,
            job_id=job_id,
            deployment_approval=approval,
            snapshot=snapshot,
            run_payload=run_payload,
            jobs_payload=jobs_payload,
            workflow_gate_binding=workflow_gate_binding,
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
