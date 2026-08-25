import json
import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.security.promotion_evidence import approval_evidence, db_detect_only_artifact, normalize_environment_approval_history, produce_o3_closure, validate_envelope_v2, validate_o4_consumes_o3, wait_for_o3_closure


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "governance" / "gov-ci12"


def approval_history(name="v2/run_32659961454_approvals_raw.json"):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def run_payload():
    data = json.loads((FIXTURES / "v2" / "run_32659961454_raw.json").read_text(encoding="utf-8"))
    data.update({"head_branch": "promote/gov-hom-012-o2-req1", "head_sha": "c" * 40, "status": "in_progress", "conclusion": None})
    return data


def jobs_payload():
    return json.loads((FIXTURES / "v2" / "premerge_jobs_in_progress_valid.json").read_text(encoding="utf-8"))["jobs_payload"]


def readiness_snapshot():
    return json.loads((FIXTURES / "v2" / "readiness_valid.json").read_text(encoding="utf-8"))


def workflow_binding():
    return json.loads((FIXTURES / "v2" / "candidate_5dc1bedd_workflow_gate_binding.json").read_text(encoding="utf-8"))


def load_validator():
    path = ROOT / "scripts" / "security" / "validate_work_package.py"
    spec = importlib.util.spec_from_file_location("validate_work_package_for_promotion_evidence_tests", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def envelope(**updates):
    payload = {
        "schema": "promotion-jit-envelope-v3",
        "transaction_id": "tx-hom012-o3-0001",
        "approval_id": "human-jit-o3",
        "grant_id": "R3-GOV-HOM-012-O3-REQ1",
        "repository_id": 1211718813,
        "repository": "romelhc95/studiamatch",
        "operation": "O3 certificacion -> main",
        "pr_number": 501,
        "pr_node_id": "PR_kw_fixture",
        "premerge_run_id": 32659961454,
        "premerge_run_attempt": 1,
        "event_name": "pull_request",
        "event_action": "opened",
        "base_ref": "main",
        "base_sha": "a" * 40,
        "source_ref": "certificacion",
        "source_sha": "b" * 40,
        "candidate_ref": "promote/gov-hom-012-o2-req1",
        "candidate_sha": "c" * 40,
        "candidate_tree": "d" * 40,
        "final_wp": "WP-GOV-CI-012",
        "final_digest": "e" * 64,
        "final_tree": "d" * 40,
        "required_reviewer": "romelhc95-approver",
        "required_reviewer_id": 306979205,
        "required_merger": "romelhc95",
        "required_merger_id": 18040405,
        "allowed_side_effects": ["main_branch_update", "cloudflare_pages_production_rebuild", "db_sync_detect_only"],
        "environment": "Promotion",
        "environment_id": 20409543239,
        "ruleset_id": 21255108,
        "ruleset_digest": "sha256:fixture",
        "issued_at": "2026-08-23T19:40:00Z",
        "expires_at": "2026-09-06T23:59:59Z",
        "nonce": "nonce-hom012-o3",
    }
    payload.update(updates)
    return payload


def test_envelope_v2_accepts_exact_payload():
    assert validate_envelope_v2(envelope(), now=datetime(2026, 8, 24, tzinfo=UTC)) == []


def test_envelope_v2_rejects_attempt_2_and_unknown_fields():
    bad = envelope(premerge_run_attempt=2)
    bad["extra"] = True
    errors = validate_envelope_v2(bad, now=datetime(2026, 8, 24, tzinfo=UTC))
    assert "ENVELOPE_EVENT_BINDING_INVALID" in errors
    assert "ENVELOPE_UNKNOWN_FIELDS" in errors


def test_envelope_v2_rejects_stale_ruleset_digest(monkeypatch):
    monkeypatch.setenv("PROMOTION_RULESET_DIGEST", "sha256:" + "2" * 64)
    errors = validate_envelope_v2(envelope(), now=datetime(2026, 8, 24, tzinfo=UTC))
    assert "ENVELOPE_RULESET_DIGEST_MISMATCH" in errors


def test_envelope_v2_rejects_future_issued_at():
    errors = validate_envelope_v2(envelope(issued_at="2026-08-25T00:00:00Z"), now=datetime(2026, 8, 24, tzinfo=UTC))
    assert "ENVELOPE_EXPIRY_INVALID" in errors


def test_approval_evidence_requires_real_reviewer():
    bad = approval_history("approval_history_wrong_reviewer.json")
    try:
        approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=bad, snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    except ValueError as exc:
        assert "APPROVAL_REVIEWER_INVALID" in str(exc)
    else:
        raise AssertionError("approval should fail")


def test_approval_history_normalizes_raw_rest_shape_and_hashes_comment():
    normalized = normalize_environment_approval_history(approval_history(), envelope(), run_id=32659961454, run_attempt=1, now=datetime(2026, 8, 24, 1, tzinfo=UTC))
    assert normalized["state"] == "approved"
    assert normalized["reviewer"] == {"login": "romelhc95-approver", "id": 306979205}
    assert normalized["environment"] == {"id": 20409543239, "name": "Promotion", "can_admins_bypass": False}
    assert normalized["comment_present"] is True
    assert "comment_sha256" in normalized
    assert "sanitized approval fixture" not in json.dumps(normalized)


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("approval_history_rejected.json", "APPROVAL_STATE_INVALID"),
        ("approval_history_wrong_environment.json", "APPROVAL_ENVIRONMENT_INVALID"),
        ("approval_history_wrong_reviewer.json", "APPROVAL_REVIEWER_INVALID"),
        ("approval_history_extra_reviewer.json", "APPROVAL_HISTORY_COUNT_INVALID"),
        ("approval_history_multiple_records.json", "APPROVAL_HISTORY_COUNT_INVALID"),
        ("approval_history_missing_environment.json", "APPROVAL_ENVIRONMENT_COUNT_INVALID"),
        ("approval_history_invalid_state.json", "APPROVAL_STATE_INVALID"),
    ],
)
def test_approval_history_negative_fixtures_fail_closed(fixture, expected):
    with pytest.raises(ValueError) as exc:
        normalize_environment_approval_history(approval_history(fixture), envelope(), run_id=32659961454, run_attempt=1, now=datetime(2026, 8, 24, 1, tzinfo=UTC))
    assert expected in str(exc.value)


@pytest.mark.parametrize("payload", [{}, [], ["bad"], [{"environments": None, "user": {}, "state": "approved", "created_at": "2026-08-24T00:05:00Z"}]])
def test_approval_history_schema_negatives_fail_closed(payload):
    with pytest.raises(ValueError):
        normalize_environment_approval_history(payload, envelope(), run_id=32659961454, run_attempt=1, now=datetime(2026, 8, 24, 1, tzinfo=UTC))


def test_approval_evidence_separates_jit_reference_from_environment_review():
    evidence = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    assert evidence["derived_context"]["jit_approval_reference_sha256"]
    assert evidence["derived_context"]["envelope_digest"]
    assert "envelope" not in evidence
    assert "nonce" not in evidence["envelope_summary"]
    assert "approval_id" not in evidence["envelope_summary"]
    assert "deployment_approval_id" not in evidence
    assert "approved_at" not in json.dumps(evidence)
    assert evidence["derived_context"]["approval_record_digest"]
    assert "created_at" not in evidence["observed_premerge_approval"]


def test_postmerge_loader_rejects_rejected_v1_artifact(monkeypatch):
    validator = load_validator()
    legacy = {
        "schema": "promotion-approval-evidence-v1",
        "artifact_name": "promotion-approval-evidence-pr-500-run-32659961454.json",
        "envelope": envelope(),
    }
    legacy["payload_sha256"] = validator.digest_json(legacy)
    monkeypatch.setattr(validator, "load_workflow_artifact_json", lambda *args, **kwargs: legacy)
    with pytest.raises(validator.GitHubEvidenceError, match="identity invalid"):
        validator.load_promotion_approval_evidence(32659961454, 500)


def test_postmerge_loader_revalidates_v2_semantics(monkeypatch):
    validator = load_validator()
    evidence = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    evidence["observed_premerge_approval"]["state"] = "rejected"
    evidence["derived_context"]["approval_record_digest"] = validator.digest_json(evidence["observed_premerge_approval"])
    evidence["payload_sha256"] = validator.digest_json({key: value for key, value in evidence.items() if key != "payload_sha256"})
    monkeypatch.setattr(validator, "load_workflow_artifact_json", lambda *args, **kwargs: evidence)
    with pytest.raises(validator.GitHubEvidenceError, match="state invalid"):
        validator.load_promotion_approval_evidence(32659961454, 501)


def test_o3_produces_closure_and_o4_consumes_loader_output():
    approved = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    approved["main_merge_sha"] = "m" * 40
    checks = [
        {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "m" * 40, "app": {"id": 85455}, "completed_at": "2026-08-23T00:10:00Z"},
        {"id": 2, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "m" * 40, "app": {"id": 15368}, "completed_at": "2026-08-23T00:11:00Z"},
    ]
    closure, errors = produce_o3_closure(approved, checks, [db_detect_only_artifact(head_sha="m" * 40, result="NO_DB_CHANGES", db_changed=False, apply_executed=False)])
    assert errors == []
    assert closure is not None
    assert validate_o4_consumes_o3(closure, expected_main_sha="m" * 40) == []


def test_o3_rejects_db_apply_or_delta():
    approved = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    checks = [
        {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 85455}},
        {"id": 2, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 15368}},
    ]
    _, errors = produce_o3_closure(approved, checks, [db_detect_only_artifact(head_sha="c" * 40, result="NO_DB_CHANGES", db_changed=True, apply_executed=True)])
    assert "O3_DB_NO_CHANGE_CONTRACT_INVALID" in errors


def test_o3_polling_uses_fake_sleeper_until_checks_close():
    approved = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    db_artifact = db_detect_only_artifact(head_sha="c" * 40, result="NO_DB_CHANGES", db_changed=False, apply_executed=False)
    calls = {"count": 0, "sleep": []}

    def checks_provider():
        calls["count"] += 1
        if calls["count"] < 3:
            return []
        return [
            {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 85455}},
            {"id": 2, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 15368}},
        ]

    closure, errors = wait_for_o3_closure(approved, checks_provider, lambda: [db_artifact], attempts=3, interval_seconds=30, sleeper=lambda seconds: calls["sleep"].append(seconds))
    assert errors == []
    assert closure["status"] == "CLOSED"
    assert calls["sleep"] == [30, 30]


def test_o3_rejects_db_artifact_sha_mismatch():
    approved = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    checks = [
        {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 85455}},
        {"id": 2, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 15368}},
    ]
    _, errors = produce_o3_closure(approved, checks, [db_detect_only_artifact(head_sha="b" * 40, result="NO_DB_CHANGES", db_changed=False, apply_executed=False)])
    assert "O3_DB_ARTIFACT_SHA_INVALID" in errors


def test_o3_rejects_duplicate_checks():
    approved = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    checks = [
        {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 85455}},
        {"id": 2, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 85455}},
        {"id": 3, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 15368}},
    ]
    _, errors = produce_o3_closure(approved, checks, [db_detect_only_artifact(head_sha="c" * 40, result="NO_DB_CHANGES", db_changed=False, apply_executed=False)])
    assert "O3_CHECK_COUNT_INVALID" in errors


def test_o3_rejects_terminal_failed_check():
    approved = approval_evidence(envelope(), run_id=32659961454, job_id=97244495190, deployment_approval=approval_history(), snapshot=readiness_snapshot(), run_payload=run_payload(), jobs_payload=jobs_payload(), workflow_gate_binding=workflow_binding())
    checks = [
        {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "failure", "head_sha": "c" * 40, "app": {"id": 85455}},
        {"id": 2, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 15368}},
    ]
    _, errors = produce_o3_closure(approved, checks, [db_detect_only_artifact(head_sha="c" * 40, result="NO_DB_CHANGES", db_changed=False, apply_executed=False)])
    assert "O3_CHECK_TERMINAL_FAILURE" in errors
