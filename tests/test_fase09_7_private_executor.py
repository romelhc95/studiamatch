from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from scripts.maintenance import fase09_7_private_executor as executor


ROOT = Path(__file__).resolve().parents[1]
VALID_COMMIT = "a" * 40
VALID_TREE = "b" * 40


def _contract() -> executor.PrivateExecutorContract:
    return executor.load_contract(ROOT)


def _clean_drift_snapshot() -> dict[str, object]:
    return {key: "clean" for key in executor.DRIFT_GUARDS}


def test_private_executor_manifest_is_closed_local_only_and_digest_bound():
    contract = _contract()

    assert contract.manifest_sha256 == executor.MANIFEST_SHA256
    assert contract.runbook_sha256 == executor.RUNBOOK_SHA256
    assert contract.boundary7_sql_sha256 == executor.BOUNDARY7_SQL_SHA256
    assert contract.payload_sha256 == executor.PAYLOAD_SHA256

    manifest = contract.manifest
    assert manifest["package_id"] == executor.PACKAGE_ID
    assert manifest["status"] == "GO_WP_LOCAL"
    assert manifest["application_authorized"] is False
    assert manifest["capabilities"] == []
    assert manifest["target"] == "free"
    assert manifest["blocked_targets"] == ["pro", "production", "certification"]
    assert manifest["atomic_sequence"] == list(executor.ATOMIC_SEQUENCE)
    assert manifest["depends_on"]["manifest_sha256"] == executor.V3_MANIFEST_SHA256
    assert len(manifest["depends_on"]["entries"]) == 6
    assert manifest["executor"]["final_state_excludes"] == ["public.exec_sql(text)"]


def test_private_executor_surface_is_not_data_api_or_role_invocable():
    manifest = _contract().manifest
    executor.validate_private_surface(manifest)

    surface = manifest["executor"]
    assert surface["schema"] != "public"
    assert surface["schema_exposed_by_data_api"] is False
    assert surface["postgrest_rpc_endpoint"] is False
    assert surface["accepts_arbitrary_sql"] is False
    assert surface["accepts_text_sql"] is False
    assert surface["descriptor_only"] is True
    assert all(value is False for value in surface["execute_grants"].values())

    for role in executor.APPLICATION_ROLES:
        mutated = json.loads(json.dumps(manifest))
        mutated["executor"]["execute_grants"][role] = True
        with pytest.raises(executor.PrivateExecutorError, match=role):
            executor.validate_private_surface(mutated)


def test_descriptor_accepts_only_exact_candidate_manifest_sql_runbook_and_payload():
    contract = _contract()
    descriptor = executor.build_descriptor(
        contract,
        candidate_commit=VALID_COMMIT,
        candidate_tree=VALID_TREE,
    )
    executor.validate_descriptor(
        contract,
        descriptor,
        expected_candidate_commit=VALID_COMMIT,
        expected_candidate_tree=VALID_TREE,
    )

    mutations = {
        "candidate_commit": "c" * 40,
        "candidate_tree": "d" * 40,
        "manifest_sha256": "0" * 64,
        "runbook_sha256": "1" * 64,
        "boundary7_sql_sha256": "2" * 64,
        "payload_sha256": "3" * 64,
        "target": "pro",
        "target_fingerprint_sha256": "4" * 64,
    }
    for key, value in mutations.items():
        candidate = dict(descriptor)
        candidate[key] = value
        with pytest.raises(executor.PrivateExecutorError, match=key):
            executor.validate_descriptor(
                contract,
                candidate,
                expected_candidate_commit=VALID_COMMIT,
                expected_candidate_tree=VALID_TREE,
            )

    with_extra_key = dict(descriptor)
    with_extra_key["sql_text"] = "DROP TABLE public.leads;"
    with pytest.raises(executor.PrivateExecutorError, match="unexpected keys"):
        executor.validate_descriptor(
            contract,
            with_extra_key,
            expected_candidate_commit=VALID_COMMIT,
            expected_candidate_tree=VALID_TREE,
        )

    payload = executor.expected_payload(contract.manifest)
    payload["final_expected_state"] = "changed"
    mutated = executor.build_descriptor(
        contract,
        candidate_commit=VALID_COMMIT,
        candidate_tree=VALID_TREE,
        payload=payload,
    )
    with pytest.raises(executor.PrivateExecutorError, match="payload_sha256"):
        executor.validate_descriptor(
            contract,
            mutated,
            expected_candidate_commit=VALID_COMMIT,
            expected_candidate_tree=VALID_TREE,
        )


def test_target_binding_accepts_only_synthetic_free_fingerprint():
    manifest = _contract().manifest
    executor.validate_target_binding(
        manifest,
        "free",
        executor.SYNTHETIC_FREE_FINGERPRINT_SHA256,
    )
    with pytest.raises(executor.PrivateExecutorError, match="target binding"):
        executor.validate_target_binding(
            manifest,
            "pro",
            executor.SYNTHETIC_FREE_FINGERPRINT_SHA256,
        )
    with pytest.raises(executor.PrivateExecutorError, match="target binding"):
        executor.validate_target_binding(
            manifest,
            "ambiguous",
            executor.SYNTHETIC_FREE_FINGERPRINT_SHA256,
        )
    with pytest.raises(executor.PrivateExecutorError, match="fingerprint"):
        executor.validate_target_binding(manifest, "free", "0" * 64)


def test_single_use_approval_accepts_one_nonce_and_invalidates_every_terminal_state():
    now = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)
    state = executor.create_approval(
        nonce="private-nonce",
        not_before=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=5),
        now=now,
    )
    assert state.consumed is False
    assert len(state.nonce_digest) == 64

    consumed = executor.consume_approval(state, "success")
    assert consumed.consumed is True
    assert consumed.terminal_result == "success"
    with pytest.raises(executor.PrivateExecutorError, match="already consumed"):
        executor.consume_approval(consumed, "success")

    for terminal in ("failure", "timeout", "ambiguous_response"):
        state = executor.create_approval(
            nonce=terminal,
            not_before=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=5),
            now=now,
        )
        consumed = executor.consume_approval(state, terminal)
        assert consumed.consumed is True
        assert consumed.terminal_result == terminal

    with pytest.raises(executor.PrivateExecutorError, match="window closed"):
        executor.create_approval(
            nonce="expired",
            not_before=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=1),
            now=now,
        )
    with pytest.raises(executor.PrivateExecutorError, match="ambiguous"):
        executor.consume_approval(state, "unknown")


@pytest.mark.parametrize("drift", sorted(executor.DRIFT_GUARDS))
def test_all_declared_drift_guards_fail_closed(drift: str):
    snapshot = _clean_drift_snapshot()
    snapshot[drift] = "dirty"
    with pytest.raises(executor.PrivateExecutorError, match="drift detected"):
        executor.validate_no_drift(snapshot)


def test_drift_snapshot_requires_every_guard():
    snapshot = _clean_drift_snapshot()
    snapshot.pop("ledger")
    with pytest.raises(executor.PrivateExecutorError, match="incomplete"):
        executor.validate_no_drift(snapshot)


def test_arbitrary_sql_is_rejected_and_exact_boundary_sql_is_accepted():
    contract = _contract()
    executor.reject_arbitrary_sql(contract, contract.boundary7_sql)
    with pytest.raises(executor.PrivateExecutorError):
        executor.reject_arbitrary_sql(contract, contract.boundary7_sql.replace("\n", "\r\n"))
    for sql in (
        "DROP TABLE public.leads;",
        "SELECT * FROM public.email_log;",
        "LOCK TABLE public.supabase_migrations;",
        "SELECT pg_advisory_lock(1);",
    ):
        with pytest.raises(executor.PrivateExecutorError):
            executor.reject_arbitrary_sql(contract, sql)


def test_boundary7_sql_is_strictly_read_only_and_sanitized():
    sql = _contract().boundary7_sql
    executor.validate_boundary7_sql(sql)
    lowered = sql.lower()
    for forbidden in (
        "lock",
        "for update",
        "pg_advisory",
        "insert",
        "update",
        "delete",
        "alter",
        "create",
        "drop",
        "grant",
        "revoke",
        "call",
        "public.leads",
        "public.email_log",
    ):
        assert forbidden not in lowered


def test_public_evidence_excludes_secrets_pii_urls_project_refs_and_rows():
    contract = _contract()
    evidence = executor.public_evidence(
        contract,
        verdict="GO_WP_LOCAL",
        timestamp="2026-07-31T12:00:00Z",
    )
    assert set(evidence) == {
        "aggregate_state",
        "timestamp",
        "artifact_digest",
        "verdict",
    }
    serialized = json.dumps(evidence, sort_keys=True)
    for forbidden in (
        "https://",
        "http://",
        "sb_publishable_",
        "sb_secret_",
        "project_ref",
        "row",
        "email@",
    ):
        assert forbidden not in serialized.lower()

    unsafe = dict(evidence)
    unsafe["target_url"] = "https://example.invalid"
    with pytest.raises(executor.PrivateExecutorError, match="non-public keys"):
        executor.assert_public_evidence_sanitized(unsafe)
