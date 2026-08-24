from datetime import UTC, datetime

from scripts.security.promotion_evidence import approval_evidence, db_detect_only_artifact, produce_o3_closure, validate_envelope_v2, validate_o4_consumes_o3, wait_for_o3_closure


def deployment_approval(**updates):
    payload = {
        "approval_id": "human-jit-o3",
        "run_id": 1000,
        "environment_name": "Promotion",
        "approved_at": "2026-08-24T00:05:00Z",
        "user": {"login": "romelhc95-approver", "id": 306979205},
    }
    payload.update(updates)
    return payload


def envelope(**updates):
    payload = {
        "schema": "promotion-jit-envelope-v2",
        "transaction_id": "tx-hom012-o3-0001",
        "approval_id": "human-jit-o3",
        "grant_id": "R3-GOV-HOM-012-O3-REQ1",
        "repository_id": 1,
        "repository": "romelhc95/studiamatch",
        "operation": "O3 certificacion -> main",
        "pr_number": 501,
        "pr_node_id": "PR_kw_fixture",
        "premerge_run_id": 1000,
        "premerge_run_attempt": 1,
        "event_name": "pull_request",
        "event_action": "opened",
        "base_ref": "main",
        "base_sha": "a" * 40,
        "source_ref": "certificacion",
        "source_sha": "b" * 40,
        "candidate_ref": "promote/gov-hom-012-o3-req1",
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
        "environment_id": 10,
        "ruleset_id": 21255108,
        "ruleset_digest": "sha256:" + "1" * 64,
        "issued_at": "2026-08-23T00:00:00Z",
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
    bad = deployment_approval(user={"login": "romelhc95", "id": 18040405})
    try:
        approval_evidence(envelope(), run_id=1000, job_id=2000, deployment_approval=bad)
    except ValueError as exc:
        assert "APPROVAL_REVIEWER_INVALID" in str(exc)
    else:
        raise AssertionError("approval should fail")


def test_o3_produces_closure_and_o4_consumes_loader_output():
    approved = approval_evidence(envelope(candidate_sha="f" * 40), run_id=1000, job_id=2000, deployment_approval=deployment_approval())
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
    approved = approval_evidence(envelope(), run_id=1000, job_id=2000, deployment_approval=deployment_approval())
    checks = [
        {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 85455}},
        {"id": 2, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 15368}},
    ]
    _, errors = produce_o3_closure(approved, checks, [db_detect_only_artifact(head_sha="c" * 40, result="NO_DB_CHANGES", db_changed=True, apply_executed=True)])
    assert "O3_DB_NO_CHANGE_CONTRACT_INVALID" in errors


def test_o3_polling_uses_fake_sleeper_until_checks_close():
    approved = approval_evidence(envelope(), run_id=1000, job_id=2000, deployment_approval=deployment_approval())
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
    approved = approval_evidence(envelope(), run_id=1000, job_id=2000, deployment_approval=deployment_approval())
    checks = [
        {"id": 1, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 85455}},
        {"id": 2, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": "c" * 40, "app": {"id": 15368}},
    ]
    _, errors = produce_o3_closure(approved, checks, [db_detect_only_artifact(head_sha="b" * 40, result="NO_DB_CHANGES", db_changed=False, apply_executed=False)])
    assert "O3_DB_ARTIFACT_SHA_INVALID" in errors
