import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFINITION_PATH = ROOT / "db/manifests/fase09_7_remediation_definition.json"
PACKAGE_PATH = ROOT / "db/manifests/fase09_7_free_schema_rls.json"
BACKUP_PATH = ROOT / "db/runbooks/fase09_7_backup_restore.json"
WRITERS_PATH = ROOT / "db/runbooks/fase09_7_writer_pause.json"
CLOSURE_PATH = ROOT / "db/migrations/20260727_fase09_7_public_access_closure.sql"

DEFINITION_CANONICAL_SHA256 = "dcfe1e49892f78719036013adce73871e1aa4d91a8d100abdd8b5898edbfdc62"
PACKAGE_CANONICAL_SHA256 = "5d32ed2c977c59c38d56948e687ba2b05ecd9ad8b2d3f5752cce3a9836889de3"
BACKUP_SHA256 = "15a8a4522c3c19491cecc9a8ee1355596b656f4039065d52f67aa1d8b3d57e0f"
WRITERS_SHA256 = "aa4583b919838cf14bc8e107e46cda7fc068326ccc4e40a6088f38082e89c525"


def _load_json(path: Path) -> dict:
    def reject_duplicates(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate key in {path}: {key}")
            value[key] = item
        return value

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
    )


def _canonical_sha256(value: dict) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_definition_is_closed_local_only_and_not_authorized():
    definition = _load_json(DEFINITION_PATH)
    assert _canonical_sha256(definition) == DEFINITION_CANONICAL_SHA256
    assert definition["artifact_type"] == "LOCAL_ONLY_REMEDIATION_DEFINITION"
    assert definition["status"] == "REMEDIATION_DEFINED_BLOCKED_PENDING_ACL_SOURCE_ATTRIBUTION"
    assert definition["status_scope"] == "HISTORICAL_AS_DEFINED_BEFORE_ACL_ATTESTATION"
    assert definition["superseded_for_live_state_by"] == {
        "path": "db/manifests/fase09_7_acl_source_attestation.json",
        "status": "CONSUMED_READ_ONLY_PACKAGE_SOURCE_COVERAGE_COMPLETE_BLOCKED",
        "result": "FREE_ACL_SOURCE_ATTESTED_PACKAGE_COVERAGE_COMPLETE_STOPPED_READ_ONLY",
    }
    assert definition["capabilities"] == []
    assert definition["blocked_targets"] == ["free", "pro"]
    assert definition["parent_evidence"]["result"] == (
        "FREE_GATE_B_FAIL_STOPPED_READ_ONLY"
    )
    assert definition["parent_evidence"]["gate_b_authorization"] == (
        "consumed_non_reusable"
    )
    assert definition["definition_binding"]["definition_commit"] == (
        "external_required_after_merge"
    )
    assert definition["definition_binding"]["definition_tree"] == (
        "external_required_after_merge"
    )
    assert "remote_transport" in definition["explicitly_forbidden"]
    assert "schema_or_migration_execution" in definition["explicitly_forbidden"]
    assert "new_free_or_pro_read_attempt_in_definition_phase" in definition["stop_conditions"]


def test_frozen_package_is_exact_five_entry_prefix_without_migration_changes():
    definition = _load_json(DEFINITION_PATH)
    package = _load_json(PACKAGE_PATH)
    assert _canonical_sha256(package) == PACKAGE_CANONICAL_SHA256

    frozen = definition["frozen_package"]
    assert frozen["manifest_canonical_sha256"] == PACKAGE_CANONICAL_SHA256
    assert frozen["package_id"] == package["package_id"]
    assert frozen["migration_changes_in_this_definition"] == 0
    assert frozen["accepted_ledger_boundaries"] == [0, 3, 4, 5]
    assert frozen["transaction_mode"] == "single_atomic_transaction"
    assert frozen["ledger_rule"] == "append_only_after_all_postconditions"
    assert frozen["entries"] == [
        [entry["id"], entry["sha256"]] for entry in package["entries"]
    ]
    assert len(frozen["entries"]) == 5
    assert all(
        not path.startswith("db/migrations/")
        for path in definition["implementation_allowlist"]
    )


def test_coverage_claim_is_complete_for_direct_drift_and_honest_about_gap():
    coverage = _load_json(DEFINITION_PATH)["coverage"]
    for control in (
        "protected_public_read",
        "lead_capture_insert_columns",
        "additional_public_table_capabilities",
    ):
        assert coverage[control]["evidence"] == "FAIL_REDUCED"
        assert coverage[control]["direct_drift_repair"] == "LOCAL_PROVEN"
    assert coverage["unmanaged_public_policies"] == {
        "evidence": "PASS_ABSENT",
        "unexpected_drift_behavior": "ATOMIC_ROLLBACK_PROVEN",
    }
    assert coverage["delegation_and_indirect_access"]["ordinary_inherited_acl_source"] == (
        "NOT_MEASURED_BY_CONSUMED_GATE"
    )
    assert coverage["complete_remote_coverage"] == {
        "status": "NOT_PROVEN_WITHOUT_NEW_SOURCE_ATTRIBUTION",
        "reason": "effective_acl_origin_was_not_preserved_in_sanitized_gate_evidence",
        "application_effect": "BLOCK",
    }
    assert "attribute_effective_acl_sources_for_public_anon_authenticated" in (
        _load_json(DEFINITION_PATH)["future_precondition_allowlist"]
    )


def test_closure_contains_each_direct_repair_and_final_fail_closed_verifier():
    closure = CLOSURE_PATH.read_text(encoding="utf-8")
    for required in (
        "DROP POLICY IF EXISTS leads_select_public ON public.leads",
        "DROP POLICY IF EXISTS email_log_select_authenticated ON public.email_log",
        "REVOKE ALL PRIVILEGES ON TABLE public.leads",
        "REVOKE ALL PRIVILEGES ON TABLE public.email_log",
        "GRANT INSERT (",
        ") ON TABLE public.leads TO anon, authenticated;",
        "CREATE OR REPLACE FUNCTION public.verify_fase09_7_public_access_closure()",
        "SECURITY INVOKER",
        "SET search_path = ''",
        "expected_insert_columns constant text[] := ARRAY[",
    ):
        assert required in closure
    assert _file_sha256(CLOSURE_PATH) == (
        "040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b"
    )


def test_runbooks_are_digest_bound_data_without_execution_capabilities():
    definition = _load_json(DEFINITION_PATH)
    backup = _load_json(BACKUP_PATH)
    writers = _load_json(WRITERS_PATH)
    assert _file_sha256(BACKUP_PATH) == BACKUP_SHA256
    assert _file_sha256(WRITERS_PATH) == WRITERS_SHA256
    assert definition["runbooks"] == [
        {
            "path": "db/runbooks/fase09_7_backup_restore.json",
            "sha256": BACKUP_SHA256,
            "current_state": "PLANNED",
            "approval": "required_not_granted",
        },
        {
            "path": "db/runbooks/fase09_7_writer_pause.json",
            "sha256": WRITERS_SHA256,
            "current_state": "INVENTORIED",
            "approval": "required_not_granted",
        },
    ]
    for runbook in (backup, writers):
        assert runbook["capabilities"] == []
        assert runbook["commands"] == []
        assert runbook["status"] == "DEFINED_NOT_APPROVED_NOT_EXECUTABLE"
        assert runbook["blocked_targets"] == ["free", "pro"]
        assert "free_connection" in runbook["explicitly_forbidden"]
        assert "pro_connection" in runbook["explicitly_forbidden"]


def test_backup_restore_states_and_recovery_decisions_are_separate():
    backup = _load_json(BACKUP_PATH)
    assert backup["state_machine"]["states"] == [
        "PLANNED",
        "APPROVED",
        "CREATED",
        "INTEGRITY_ATTESTED",
        "RESTORE_PROVEN",
    ]
    assert backup["state_machine"]["current_state"] == "PLANNED"
    assert [item["decision"] for item in backup["approval_classes"]] == [
        "backup_custody_approval",
        "restore_evidence_approval",
    ]
    assert len({item["actor_class"] for item in backup["approval_classes"]}) == 2
    assert backup["failure_matrix"][0]["ledger_action"] == "no_append"
    assert backup["failure_matrix"][1]["approval"] == (
        "separate_emergency_human_gate_required"
    )
    assert backup["failure_matrix"][1]["allowed_recovery"] == [
        "forward_fix",
        "restore",
    ]


def test_writer_pause_inventory_and_resume_boundary_are_complete():
    writers = _load_json(WRITERS_PATH)
    assert writers["state_machine"]["states"] == [
        "INVENTORIED",
        "PAUSE_APPROVED",
        "PAUSE_CONFIRMED",
        "DRAIN_CONFIRMED",
        "HELD",
    ]
    assert writers["state_machine"]["current_state"] == "INVENTORIED"
    inventory_sources = {
        item["source"] for item in writers["writer_inventory"]
        if not item["source"].startswith("private_")
    }
    for source in inventory_sources:
        assert (ROOT / source).is_file()
    assert "do_not_resume_before_f9_10_qa_and_separate_approval" in (
        writers["pause_contract"]
    )
    decisions = writers["approval_classes"]
    assert decisions[-1] == {
        "decision": "writer_resume_approval",
        "actor_class": "f9_10_independent_human_reviewer",
        "status": "out_of_scope_blocked",
    }


def test_public_artifacts_avoid_people_requests_secrets_and_remote_primitives():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (DEFINITION_PATH, BACKUP_PATH, WRITERS_PATH)
    ).lower()
    for forbidden in (
        "romelhc95",
        "approval_request_id",
        "publishable_key",
        "secret_key",
        "execute_sql",
        "requests.",
        "subprocess",
        "pg_dump",
        "pg_restore",
    ):
        assert forbidden not in combined


def test_f9_7_is_blocking_in_independent_and_required_ci():
    independent = (ROOT / ".github/workflows/f9-7-contract.yml").read_text(
        encoding="utf-8"
    )
    required = (ROOT / ".github/workflows/security-audit.yml").read_text(
        encoding="utf-8"
    )
    for path in (
        "db/manifests/fase09_7_remediation_definition.json",
        "db/runbooks/fase09_7_backup_restore.json",
        "db/runbooks/fase09_7_writer_pause.json",
        "tests/test_fase09_7_remediation_definition.py",
        "tests/sql/fase08_minimal_baseline.sql",
        "tests/sql/fase09_exec_sql_fixture.sql",
        "requirements-db-migrate.txt",
        "requirements-test.txt",
    ):
        assert path in independent
    assert "fase09-7-remediation:" in required
    assert "fase09-7-remediation" in required.split("needs:", 1)[1]
    assert "F97: ${{ needs.fase09-7-remediation.result }}" in required
    assert 'if [ "$F97" != "success" ]; then' in required


def test_shell_command_substitution_propagates_partial_producer_failure():
    producer_failure = subprocess.run(
        [
            "bash",
            "-c",
            'set -e; output="$(printf partial; exit 42)"; printf "%s" "$output"',
        ],
        capture_output=True,
        check=False,
    )
    assert producer_failure.returncode == 42
    assert producer_failure.stdout == b""
