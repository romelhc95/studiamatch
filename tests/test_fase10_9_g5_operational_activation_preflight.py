from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.shared.f10_9_g5_operational_activation_preflight import (
    CI_RETRY_RUN_ATTEMPT,
    CURRENT_CONNECTED,
    CURRENT_GATE,
    CURRENT_TRUST,
    EXPECTED_CONFIGURATION_NAMES,
    EXPECTED_GATES,
    EXPECTED_GITHUB_APP_PERMISSIONS,
    EXPECTED_WORKFLOW_PERMISSIONS,
    G5OperationalPreflightError,
    OPERATIONAL_RUN_ATTEMPT_REQUIRED,
    PREFLIGHT_VERSION,
    validate_manifest,
)


MANIFEST_PATH = Path(".context/operaciones/g5_operational_activation_manifest_2026_08_15.json")
RUNBOOK_PATH = Path(".context/operaciones/g5_operational_activation_runbook_2026_08_15.md")
ADR_PATH = Path(".context/decisiones/ADR-0016_g5_operational_activation_gates.md")
ADR18_PATH = Path(".context/decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md")
ADR19_PATH = Path(".context/decisiones/ADR-0019_github_runtime_schema_lifecycle.md")
ADR20_PATH = Path(".context/decisiones/ADR-0020_g5_runtime_binding_snapshot_cas.md")
ADR21_PATH = Path(".context/decisiones/ADR-0021_g5_terminal_confirmation_token_scope.md")
ADR22_PATH = Path(".context/decisiones/ADR-0022_g5_followup_security_remediation.md")
ADR23_PATH = Path(".context/decisiones/ADR-0023_g5_trusted_boundary_bootstrap.md")
ADR24_PATH = Path(".context/decisiones/ADR-0024_g5_link_header_hardening_closure.md")
ADR25_PATH = Path(".context/decisiones/ADR-0025_g5_default_branch_trusted_workflow_registration.md")
PRELIGHT_PATH = Path("scripts/shared/f10_9_g5_operational_activation_preflight.py")


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _walk(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_pr387_attempts_are_preserved_and_retry_is_ci_only() -> None:
    manifest = _manifest()
    evidence = manifest["pr_387_reconciliation"]
    assert evidence["candidate_sha"] == "d62c8969e7d229bb8d2a9e1f8c6db6a1c4ef4d1d"
    assert evidence["merge_sha"] == "bd0d82864c26755435e551b835d145b864383810"
    assert evidence["tree_sha"] == "135af5a95237a1d4d6e1b977e8bb9ab82ac95e16"
    assert evidence["status"] == "MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY"
    assert evidence["security_run_id"] == "31912540519"
    assert evidence["focused_job_id"] == "95079685172"
    assert evidence["m3_job_id"] == "95079685191"
    assert evidence["f9_7_run_id"] == "31912540528"
    assert evidence["ci_run_attempt"] == CI_RETRY_RUN_ATTEMPT
    assert evidence["operational_g5_run_attempt_required"] == OPERATIONAL_RUN_ATTEMPT_REQUIRED
    assert evidence["attempts"] == [
        {
            "attempt": 1,
            "job_id": "95079764790",
            "conclusion": "CANCELLED",
            "classification": "CI_INFRA_TIMEOUT_PLAYWRIGHT_APT",
            "scope": "CI_ONLY",
        },
        {
            "attempt": 2,
            "job_id": "95084155346",
            "conclusion": "PASS",
            "classification": "CI_RETRY_PASS",
            "scope": "CI_ONLY",
        },
    ]


def test_manifest_validates_name_only_package_and_current_stops() -> None:
    manifest = _manifest()
    result = validate_manifest(manifest)
    assert result.decision == "PASS"
    assert result.version == PREFLIGHT_VERSION
    assert result.checked_names == EXPECTED_CONFIGURATION_NAMES
    assert result.checked_gates == EXPECTED_GATES
    assert manifest["current_gate"] == CURRENT_GATE
    assert manifest["current_trust"] == CURRENT_TRUST
    assert manifest["current_connected"] == CURRENT_CONNECTED
    assert manifest["hito1_integral_status"] == {
        "ca1_original_technical": "PASS",
        "integral_state": "CA_ORIGINAL_PASS_CORRECTIVE_ACCEPTANCE_PENDING",
        "evidence_readiness": "75%",
        "formal_closure": "NOT_READY",
        "tracking_only": {"hito1": "60%", "f10_9": "38%", "g5": "50%"},
    }
    assert manifest["frozen_versions"]["wrangler"] == "4.44.0"
    assert manifest["status"] == "PREPARED_NOT_CONFIGURED_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED"
    assert all(item["state"] == "ABSENT_NOT_CONFIGURED" for item in manifest["required_configuration_names"])
    assert [item["name"] for item in manifest["required_configuration_names"]] == list(EXPECTED_CONFIGURATION_NAMES)


def test_pr390_and_e1_deployment_are_sanitized_and_reconciled() -> None:
    manifest = _manifest()
    pr390 = manifest["pr_390_reconciliation"]
    assert pr390 == {
        "candidate_sha": "c36cc9b6efb166f2f840615759793b7917142f38",
        "merge_sha": "9811b19e1527b39366e43907990c4b77d1394f75",
        "tree_sha": "edb7c827621fce1089d636b50494405115d348a6",
        "status": "MERGED_POST_MERGE_VERIFIED",
        "security_run_id": "31926378062",
        "security_conclusion": "PASS",
        "f9_7_run_id": "31926378069",
        "f9_7_conclusion": "PASS",
        "focused_job_id": "95114516929",
        "focused_conclusion": "PASS",
        "f9_7_job_id": "95114603279",
        "f9_7_job_conclusion": "PASS",
        "run_attempt": 1,
    }
    e1 = manifest["e1_deployment_reconciliation"]
    assert e1["status"] == "E1_DEPLOYMENT_PASS"
    assert e1["credential_state"] == "E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED"
    assert e1["version"] == "f10.9-g5-trust-broker.v2"
    assert e1["binding"] == "G5_ATOMIC_LEDGER"
    assert e1["class_name"] == "G5AtomicLedgerDurableObject"
    assert e1["migration_tag"] == "repository-only-v1"
    assert e1["worker_count_expected"] == 1
    assert e1["workers_dev_enabled"] is False
    assert e1["preview_urls_enabled"] is False
    assert e1["endpoint_public"] is False
    assert e1["routes_count"] == e1["custom_domains_count"] == 0
    assert e1["schedules_count"] == e1["vars_count"] == e1["secrets_count"] == 0
    assert len(e1["dry_run_bundle_sha256"]) == len(e1["deployed_payload_sha256"]) == 64
    assert "account" not in json.dumps(e1).lower()
    assert "token" not in json.dumps(e1).lower()


def test_pr392_and_e2_security_remediation_stop_are_registered() -> None:
    manifest = _manifest()
    assert manifest["pr_391_reconciliation"] == {
        "candidate_sha": "77f475af2e5900bc1338967676ebded71b672642",
        "merge_sha": "5a76abaae8760a9ce6a418511264e6742fa5c74c",
        "tree_sha": "9bd83392ade9e245f3fc4ab85bb85eb4f9031040",
        "status": "MERGED_POST_MERGE_VERIFIED",
        "security_run_id": "31951803908",
        "security_conclusion": "PASS",
        "f9_7_run_id": "31951803820",
        "f9_7_conclusion": "PASS",
        "focused_job_id": "95176303149",
        "focused_conclusion": "PASS",
        "f9_7_job_id": "95176398983",
        "f9_7_job_conclusion": "PASS",
        "run_attempt": 1,
    }
    assert manifest["pr_392_reconciliation"] == {
        "candidate_sha": "b3f9678e0df76ef8f9dfde8af9147a458a2e033b",
        "merge_sha": "0672156ae5ea13a3ba40ab5f4fd4fd184ec5811e",
        "tree_sha": "7fa8e5c26ddaa67450584b43d5b61c9f7b9edc98",
        "status": "MERGED_POST_MERGE_VERIFIED_SECURITY_REMEDIATION_REQUIRED",
        "security_run_id": "31958015767",
        "security_conclusion": "PASS",
        "f9_7_run_id": "31958015698",
        "f9_7_conclusion": "PASS",
        "focused_job_id": "95191560687",
        "focused_conclusion": "PASS",
        "f9_7_job_id": "95191665616",
        "f9_7_job_conclusion": "PASS",
        "run_attempt": 1,
        "previous_security_auditor_go_preserved": True,
        "post_merge_security_remediation_required": True,
    }
    assert manifest["e2_stop"] == "E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED"
    assert sorted(manifest["github_runtime_shapes"]) == sorted(
        [
            "approvals",
            "branch",
            "check_runs",
            "commit",
            "deployment_statuses",
            "deployments",
            "environment",
            "workflow_content_blob",
            "workflow_jobs",
            "workflow_run",
        ]
    )
    assert "ref_protected" in manifest["github_runtime_shapes"]["branch"]["forbidden_fields"]
    assert "environment_id" in manifest["github_runtime_shapes"]["deployments"]["forbidden_fields"]
    assert "check_run_id" in manifest["github_runtime_shapes"]["approvals"]["forbidden_fields"]
    assert manifest["github_runtime_shapes"]["check_runs"]["source"] == (
        "GET /repos/{owner}/{repo}/check-runs/{check_run_id}"
    )
    assert "commit_sha_name_array_search" in manifest["github_runtime_shapes"]["check_runs"]["forbidden_fields"]
    assert manifest["github_runtime_shapes"]["workflow_run"]["lifecycle"] == (
        "status=in_progress conclusion=null event=workflow_dispatch run_attempt=1"
    )
    assert manifest["github_runtime_shapes"]["deployment_statuses"]["source"].endswith(
        "/statuses?per_page=100"
    )
    assert "unique temporal maximum" in manifest["github_runtime_shapes"]["deployment_statuses"]["lifecycle"]
    assert manifest["github_runtime_shapes"]["workflow_content_blob"]["source"].endswith(
        "?ref={candidate_sha}"
    )


def test_pr393_and_residual_remediation_contract_are_registered() -> None:
    manifest = _manifest()
    assert manifest["pr_393_reconciliation"] == {
        "candidate_sha": "4d5d97bb37ffcd5126d467bde9152e705a895c85",
        "merge_sha": "51aaac5d289226b1f8f16de1daf69a16a084d585",
        "tree_sha": "7e7be8072cc416d76d2034a126d39393cdbcc968",
        "status": "MERGED_POST_MERGE_VERIFIED_RESIDUAL_REMEDIATION_REQUIRED",
        "security_run_id": "31962569422",
        "security_conclusion": "PASS",
        "security_aggregate_job_id": "95202769920",
        "security_aggregate_conclusion": "PASS",
        "branch_reconciliation_job_id": "95202690518",
        "branch_reconciliation_conclusion": "PASS",
        "f9_7_run_id": "31962569598",
        "f9_7_conclusion": "PASS",
        "focused_job_id": "95202690713",
        "focused_conclusion": "PASS",
        "f9_7_job_id": "95202805508",
        "f9_7_job_conclusion": "PASS",
        "run_attempt": 1,
        "merge_tree_reconciled": True,
        "post_merge_residual_remediation_required": True,
    }
    residual = manifest["post_merge_pr393_residual_findings"]
    assert len(residual) == 6
    assert [finding["severity"] for finding in residual].count("HIGH") == 1
    assert [finding["severity"] for finding in residual].count("MEDIUM") == 5
    assert all(finding["status"] == "REMEDIATED_REPOSITORY_ONLY" for finding in residual)
    assert manifest["terminal_confirmation"] == {
        "source": "requery_run_job_check_and_deployment_status_after_snapshot_b_immediately_before_cas",
        "covered_bindings": [
            "repositoryId",
            "runId",
            "runAttempt",
            "checkRunId",
            "checkSuiteId",
            "jobId",
            "deploymentId",
            "deploymentStatusId",
        ],
        "external_request_after_terminal_confirmation": "FORBIDDEN",
        "cas_retry": "FORBIDDEN",
    }
    assert manifest["github_actions_app_identity"] == {
        "slug": "github-actions",
        "name": "GitHub Actions",
        "id": 15368,
        "owner_id": 9919,
    }


def test_pr394_and_followup_security_remediation_are_registered() -> None:
    manifest = _manifest()
    assert manifest["pr_394_reconciliation"] == {
        "candidate_commits": [
            "7861af0cf94b726d6ce5fadad9ffb6c2274fdcaa",
            "03bab905901f62dba7631a9fe0a87290d70802d9",
            "82ef6e92c125040cededb4a648d1eedd6d519ecf",
        ],
        "head_sha": "82ef6e92c125040cededb4a648d1eedd6d519ecf",
        "merge_sha": "25be9caffe5674156c7515735a15ad45c5ad22e2",
        "tree_sha": "9f81f71bdabb2012ab593b1999cf4df92fa712eb",
        "status": "MERGED_POST_MERGE_VERIFIED_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED",
        "security_run_id": "31968991218",
        "security_conclusion": "PASS",
        "f9_7_run_id": "31968990202",
        "f9_7_conclusion": "PASS",
        "focused_job_id": "95218353795",
        "focused_conclusion": "PASS",
        "f9_7_job_id": "95218447778",
        "f9_7_job_conclusion": "PASS",
        "run_attempt": 1,
        "followup_security_remediation_required": True,
    }
    controls = manifest["followup_security_remediation"]
    assert controls["generic_followup_chain_support"] == "REMOVED"
    assert controls["pr_394_historical_identity"] == "EXACT_THREE_COMMITS_IMMUTABLE"
    assert controls["future_candidate_commits"] == "EXACT_ONE_DIRECT_COMMIT_REQUIRED"
    assert controls["link_headers"] == "REJECT_MALFORMED_AMBIGUOUS_DUPLICATED_UNEXPECTED"
    assert controls["installation_token_fixtures"] == "REQUEST_INDEPENDENT"
    assert controls["terminal_confirmation_mutation_tests"] == "COVER_EACH_TERMINAL_CALL"
    assert controls["residual_multi_endpoint_race"] == "DOCUMENTED_NO_FULL_ATOMICITY_CLAIM"
    assert controls["backlog"] == "BK-F10.9-G5-ATOMIC-AUTHORITY"
    backlog = manifest["atomic_authority_backlog"]
    assert backlog == {
        "id": "BK-F10.9-G5-ATOMIC-AUTHORITY",
        "state": "BACKLOG_NON_EXECUTABLE_QUOTABLE",
        "quotable": True,
        "included_in_hito_progress": False,
        "implementation_authorized": False,
    }
    assert [finding["id"] for finding in manifest["post_merge_pr394_followup_findings"]] == [
        f"PRL-{index:03d}" for index in range(1, 8)
    ]


def test_pr392_security_findings_and_runtime_binding_contract_are_explicit() -> None:
    manifest = _manifest()
    findings = manifest["post_merge_security_findings"]
    assert len(findings) == 6
    assert [finding["severity"] for finding in findings].count("HIGH") == 3
    assert [finding["severity"] for finding in findings].count("MEDIUM") == 3
    assert findings[-1]["status"] == "STOP_EXPLICIT_E2_PREFLIGHT_REQUIRED"
    assert all("REMEDIATED" in finding["status"] for finding in findings[:-1])
    assert manifest["runtime_binding_contract"] == {
        "check_run_source": "job.check_run_url_only",
        "deployment_status_source": "unique_temporal_maximum_after_validation",
        "binding_fields_added": ["jobId", "deploymentStatusId", "checkSuiteId"],
        "check_suite_id_policy": "included_because_check_run.check_suite.id_is_authoritative_and_stable_in_rest_shape",
        "caller_supplied_authority": "FORBIDDEN",
    }
    assert manifest["snapshot_cas"]["internal_retry"] == "FORBIDDEN"
    assert manifest["installation_token_scope"]["repository_ids_request"] == "exact_single_repository_id"
    assert manifest["installation_token_scope"]["repository_selection"] == "selected_required"
    assert manifest["installation_token_scope"]["token_schema"] == "exact_known_response_keys"
    assert manifest["installation_token_scope"]["token_promise_cache"] == "segmented_by_repository_id"
    assert manifest["installation_token_scope"]["permissions"] == EXPECTED_GITHUB_APP_PERMISSIONS
    assert manifest["future_e2_readonly_preflight"] == {
        "purpose": "confirm_whether_environment_endpoint_requires_additional_permission_before_e2",
        "state": "DOCUMENTED_NOT_EXECUTED",
        "permission_added_now": False,
        "stop": "E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED",
    }


def test_pr395_pr396_and_trusted_boundary_hardening_are_registered() -> None:
    manifest = _manifest()
    assert manifest["pr_395_reconciliation"] == {
        "candidate_sha": "444c674cf2ff2143bb4b511e88ff6cd30c1fb589",
        "merge_sha": "d04a174915910f50b8adf3d4d4b1216ffbc90b75",
        "tree_sha": "b30329f66ad8b8ba36e6cbd51303bd8e729036a0",
        "status": "MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED",
        "security_run_id": "31974315708",
        "security_conclusion": "PASS",
        "f9_7_run_id": "31974315810",
        "f9_7_conclusion": "PASS",
        "focused_job_id": "95231385472",
        "focused_conclusion": "PASS",
        "f9_7_job_id": "95231489296",
        "f9_7_job_conclusion": "PASS",
        "run_attempt": 1,
        "trusted_boundary_bootstrap_required": True,
        "link_hardening_closure_deferred_to_pr_n": True,
    }
    assert manifest["trusted_boundary_bootstrap"] == {
        "workflow": ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml",
        "check_name": "F10.9 Trusted Boundary Bootstrap",
        "event": "pull_request_target",
        "status": "BOOTSTRAP_HUMAN_NOT_SELF_ATTESTED",
        "permissions": {"contents": "read"},
        "secrets": "FORBIDDEN",
        "base_code_only": True,
        "candidate_execution": "FORBIDDEN",
        "candidate_actions": "FORBIDDEN",
        "candidate_tests": "FORBIDDEN",
        "candidate_inspection": "GIT_OBJECTS_AS_UNTRUSTED_DATA",
        "fork_policy": "REJECT",
        "shape_policy": "FAIL_CLOSED_EXACT_BASE_HEAD_DIRECT_COMMIT_ANCESTRY_PATH_STATUS_MODE",
        "actions_pinned_by_sha": True,
        "does_not_replace_pull_request_tests": True,
        "future_profile": "PR_N_LINK_HARDENING_CLOSURE_ONLY",
    }
    assert manifest["pr_396_reconciliation"] == {
        "candidate_sha": "063fb88b3b3dabda78ea641f46da69af09058ab7",
        "merge_sha": "0ec3da6c77b7819a38adcd2f38cd81699adc9283",
        "tree_sha": "ecbe760d50f06d0edce0f36ef84fabacb0a4037c",
        "status": "MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_HARDENING_REQUIRED",
        "security_run_id": "31979524771",
        "security_conclusion": "PASS",
        "f9_7_run_id": "31979524732",
        "f9_7_conclusion": "PASS",
        "focused_job_id": "95243979388",
        "focused_conclusion": "PASS",
        "f9_7_job_id": "95244079936",
        "f9_7_job_conclusion": "PASS",
        "run_attempt": 1,
        "trusted_boundary_hardening_required": True,
    }
    assert manifest["pr_397_reconciliation"] == {
        "candidate_sha": "8adede3ed10605f3af36e905d8f11e7489815d8a",
        "merge_sha": "9a5fcf539c69b635a41616e52716c0ee34837df4",
        "tree_sha": "b33228a031312062b165f8f612d27eacee2fea00",
        "status": "MERGED_POST_MERGE_VERIFIED",
        "security_run_id": "31984379751",
        "security_conclusion": "PASS",
        "security_audit_job_id": "95256753465",
        "security_audit_conclusion": "PASS",
        "f9_7_run_id": "31984379715",
        "f9_7_conclusion": "PASS",
        "f9_7_job_id": "95256780481",
        "f9_7_job_conclusion": "PASS",
        "focused_g5_job_id": "95256691723",
        "focused_g5_conclusion": "PASS",
        "m3_job_id": "95256691760",
        "m3_conclusion": "PASS",
        "run_attempt": 1,
    }
    assert manifest["pr_398_reconciliation"] == {
        "candidate_sha": "d03ee28ce90abcbf8efd7c4b37de99b72717207e",
        "base_sha": "9a5fcf539c69b635a41616e52716c0ee34837df4",
        "merge_sha": "85d7f647a37dc784fe16c11da0318956e255b698",
        "tree_sha": "91706dfcc3766fbf69b4fb8c893318786445a2a9",
        "status": "MERGED_POST_MERGE_VERIFIED_TRUSTED_ATTESTATION_MISSING_DEFAULT_BRANCH_REGISTRATION_REQUIRED",
        "security_run_id": "31992887172",
        "security_conclusion": "PASS",
        "security_run_attempt": 1,
        "security_audit_job_id": "95279485661",
        "security_audit_conclusion": "PASS",
        "f9_7_run_id": "31992887025",
        "f9_7_conclusion": "PASS",
        "f9_7_run_attempt": 1,
        "f9_7_job_id": "95279525942",
        "f9_7_job_conclusion": "PASS",
        "focused_g5_job_id": "95279414529",
        "focused_g5_conclusion": "PASS",
        "m3_job_id": "95279414473",
        "m3_conclusion": "PASS",
        "trusted_check": "NOT_EXECUTED",
        "retroactive_merge_gate_attestation": "FORBIDDEN",
    }
    assert manifest["trusted_boundary_hardening"] == {
        "workflow": ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml",
        "check_name": "F10.9 Trusted Boundary PR N v1",
        "status": "REPOSITORY_ONLY_HARDENED_NOT_REQUIRED_CHECK",
        "pull_request_target_types": ["opened", "synchronize", "reopened", "ready_for_review", "edited"],
        "pr_n_workflow_modifications": "FORBIDDEN",
        "trusted_validator_modifications": "FORBIDDEN",
        "oid_policy": "LOWERCASE_HEX_SHA_40_BEFORE_GIT",
        "git_policy": "ISOLATED_CONFIG_HOOKS_DISABLED_FETCH_NO_SUBMODULES",
        "persist_credentials": False,
        "candidate_execution": "FORBIDDEN",
        "candidate_actions": "FORBIDDEN",
        "candidate_tests": "FORBIDDEN",
        "candidate_scripts": "FORBIDDEN",
        "required_check_state": "NOT_REQUIRED_PENDING_SEPARATE_REMOTE_APPROVAL",
        "branch_protection_payload_path": ".context/operaciones/g5_trusted_required_check_payload_sanitized_2026_08_16.json",
    }
    branch_update = manifest["branch_protection_required_check_update"]
    assert branch_update["status"] == "PREPARED_NOT_EXECUTED_REQUIRES_EXPLICIT_REMOTE_APPROVAL"
    assert branch_update["prepared_from_live_state"] is True
    assert branch_update["required_check_to_add"] == {
        "context": "F10.9 Trusted Boundary PR N v1",
        "app_id": 15368,
    }
    assert branch_update["live_state_preserved"]["required_status_checks"]["strict"] is True
    assert branch_update["live_state_preserved"]["required_status_checks"]["checks"] == [
        {"context": "security-audit", "app_id": 15368},
    ]
    assert branch_update["request_body"]["required_status_checks"]["checks"] == [
        {"context": "security-audit", "app_id": 15368},
        {"context": "F10.9 Trusted Boundary PR N v1", "app_id": 15368},
    ]
    expected_reviews = {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": False,
        "require_last_push_approval": True,
        "required_approving_review_count": 1,
    }
    assert branch_update["live_state_preserved"]["required_pull_request_reviews"] == expected_reviews
    assert branch_update["request_body"]["required_pull_request_reviews"] == expected_reviews
    assert branch_update["request_body"]["required_pull_request_reviews"]["require_last_push_approval"] is True
    assert branch_update["request_body"]["enforce_admins"] is True
    assert branch_update["request_body"]["restrictions"] is None
    for flag in (
        "required_linear_history",
        "allow_force_pushes",
        "allow_deletions",
        "block_creations",
        "required_conversation_resolution",
        "lock_branch",
        "allow_fork_syncing",
    ):
        assert branch_update["live_state_preserved"][flag] is False
        assert branch_update["request_body"][flag] is False
    assert branch_update["execution_guard"] == "DO_NOT_EXECUTE_WITHOUT_EXPLICIT_ADDITIONAL_APPROVAL"
    assert manifest["link_hardening_closure"] == {
        "status": "CLOSED_BY_PR_N_TRUSTED_BOUNDARY",
        "trusted_boundary_required_first": True,
        "closed_by": "PR_N_LINK_HARDENING_CLOSURE",
        "link_header_contract": "CANONICAL_REL_ONLY_REJECT_NEXT_AND_UNEXPECTED",
        "pr_l_repository_only_changes": "REVALIDATED_AND_CLOSED_UNDER_TRUSTED_BOUNDARY_PR_N",
    }


def test_default_branch_registration_root_cause_and_pr_p_profile_are_registered() -> None:
    manifest = _manifest()
    assert manifest["default_branch_trusted_workflow_registration"] == {
        "default_branch": "main",
        "workflow_path": ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml",
        "workflow_exists_in_desarrollo": True,
        "workflow_exists_in_main": False,
        "pull_request_target_requires_default_branch_file": True,
        "edited_retry_api_enable_can_fix_absence": False,
        "pr_398_retroactive_merge_gate_attestation_allowed": False,
        "root_cause": "DEFAULT_BRANCH_TRUSTED_WORKFLOW_ABSENT",
        "stop": "E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED",
    }
    assert manifest["trusted_boundary_pr_p_profile"] == {
        "status": "PREPARED_HUMAN_BOOTSTRAP_NOT_SELF_ATTESTED",
        "check_name": "F10.9 Trusted Boundary PR P v1",
        "head_ref": "feat/f10-9-pr-p-trusted-boundary-registration-probe",
        "candidate_commits": "EXACTLY_ONE_DIRECT_COMMIT",
        "allowed_statuses": {
            ".context/operaciones/g5_trusted_boundary_pr_p_probe_2026_08_17.md": "M",
        },
        "forbidden_workflow_prefixes": [".github/workflows/"],
        "forbidden_validator_paths": ["scripts/security/f109_trusted_boundary_bootstrap.py"],
        "fork_policy": "REJECT",
        "permissions": {"contents": "read"},
        "persist_credentials": False,
        "git_policy": "ISOLATED_CONFIG_HOOKS_DISABLED_FETCH_NO_SUBMODULES",
        "secrets": "FORBIDDEN",
        "candidate_execution": "FORBIDDEN",
        "candidate_actions": "FORBIDDEN",
        "candidate_tests": "FORBIDDEN",
        "candidate_scripts": "FORBIDDEN",
    }


def test_selective_promotion_manifest_is_prepared_not_executed() -> None:
    manifest = _manifest()
    assert manifest["selective_promotion_manifest"] == {
        "status": "PREPARED_NOT_EXECUTED",
        "path": ".context/operaciones/g5_trusted_workflow_default_branch_promotion_sanitized_2026_08_17.json",
        "scope": "SELECTIVE_WORKFLOW_REGISTRATION_ONLY",
        "promotion_path": ["desarrollo", "certificacion", "main"],
        "execution_guard": "DO_NOT_EXECUTE_WITHOUT_EXPLICIT_PROMOTION_APPROVAL",
        "default_branch_change": "FORBIDDEN",
        "branch_protection_change": "FORBIDDEN",
        "workflow_dispatch": "FORBIDDEN",
        "required_check_preservation": "PRESERVE_EXISTING_REQUIRED_CHECKS_NO_REMOTE_MUTATION",
    }


def test_runtime_shapes_are_exact_and_fail_closed() -> None:
    manifest = _manifest()
    manifest["github_runtime_shapes"]["workflow_run"]["lifecycle"] = "completed success"
    with pytest.raises(G5OperationalPreflightError) as excinfo:
        validate_manifest(manifest)
    assert "STOP_G5_E_RUNTIME_SHAPE_LIFECYCLE" in str(excinfo.value)

    manifest = _manifest()
    manifest["github_runtime_shapes"]["deployment_statuses"]["required_fields"].remove("state")
    with pytest.raises(G5OperationalPreflightError) as excinfo:
        validate_manifest(manifest)
    assert "STOP_G5_E_RUNTIME_SHAPE_FIELDS" in str(excinfo.value)


def test_manifest_contains_no_configuration_values_or_remote_identifiers() -> None:
    manifest = _manifest()
    config_entries = manifest["required_configuration_names"]
    assert [item["name"] for item in config_entries] == list(EXPECTED_CONFIGURATION_NAMES)
    assert all(set(item) == {"name", "scope", "state"} for item in config_entries)
    serialized = json.dumps(manifest, sort_keys=True)
    for forbidden in (
        "https://",
        "http://",
        "sb_secret_",
        "sb_publishable_",
        "eyJhbG",
        "-----BEGIN",
        "installation_identifier",
        "project_ref",
        "account_id",
        "worker_id",
    ):
        assert forbidden not in serialized
    forbidden_keys = {"value", "secret", "token", "private_key", "current_value"}
    assert not forbidden_keys.intersection(str(item).lower() for item in _walk(manifest))


def test_permissions_are_exact_and_write_permissions_are_minimal() -> None:
    manifest = _manifest()
    assert manifest["github_app_permissions"] == EXPECTED_GITHUB_APP_PERMISSIONS
    assert manifest["workflow_permissions"] == EXPECTED_WORKFLOW_PERMISSIONS
    assert "write" not in manifest["github_app_permissions"].values()
    assert [
        permission
        for permission, access in manifest["workflow_permissions"].items()
        if access == "write"
    ] == ["id-token"]


def test_gates_e1_to_e6_are_reordered_and_non_executing() -> None:
    manifest = _manifest()
    gates = manifest["gates"]
    assert [gate["id"] for gate in gates] == list(EXPECTED_GATES)
    domains = [gate["domain"] for gate in gates]
    assert len(domains) == len(set(domains)) == 8
    for gate in gates:
        assert gate["future_authorization_required"] is True
        assert gate["preconditions"]
        assert gate["sanitized_outputs"]
        assert gate["rollback"]
        assert gate["stop_conditions"]
    gates_by_id = {gate["id"]: gate for gate in gates}
    assert gates_by_id["E4A"]["domain"] == "runtime_policy_exact_binding_and_redeploy"
    assert gates_by_id["E4B"]["domain"] == "trust_broker_endpoint_exposure_decision"
    assert "SUPERSEDED_NOT_EXECUTABLE" in RUNBOOK_PATH.read_text(encoding="utf-8")
    assert all(
        any(required in condition for condition in gates_by_id["E5"]["preconditions"])
        for required in ("E4", "E4A", "E4B")
    )
    assert manifest["superseded_sequence"] == "E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE"


def test_runbook_and_adr_preserve_operational_run_attempt_one() -> None:
    combined = (
        RUNBOOK_PATH.read_text(encoding="utf-8")
        + ADR_PATH.read_text(encoding="utf-8")
        + ADR18_PATH.read_text(encoding="utf-8")
        + ADR19_PATH.read_text(encoding="utf-8")
        + ADR20_PATH.read_text(encoding="utf-8")
        + ADR21_PATH.read_text(encoding="utf-8")
        + ADR22_PATH.read_text(encoding="utf-8")
        + ADR23_PATH.read_text(encoding="utf-8")
        + ADR24_PATH.read_text(encoding="utf-8")
        + ADR25_PATH.read_text(encoding="utf-8")
    )
    for marker in (
        "MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY",
        "attempt_1_job = 95079764790=CANCELLED",
        "attempt_1_classification = CI_INFRA_TIMEOUT_PLAYWRIGHT_APT",
        "attempt_2_job = 95084155346=PASS",
        "attempt_2_classification = CI_RETRY_PASS",
        "attempt_2_run_attempt = 2",
        "`run_attempt=1` obligatorio",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "E1_DEPLOYMENT_PASS",
        "E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED",
        "E2_STOP_GITHUB_RUNTIME_SCHEMA_INCOMPATIBLE",
        "status=in_progress",
        "conclusion=null",
        "GET /repos/{owner}/{repo}/branches/main",
        "G5_TRUST_RUNTIME_ENABLED",
        "SUPERSEDED_NOT_EXECUTABLE",
        "terminal confirmation",
        "51aaac5d289226b1f8f16de1daf69a16a084d585",
        "7e7be8072cc416d76d2034a126d39393cdbcc968",
        "25be9caffe5674156c7515735a15ad45c5ad22e2",
        "E2_STOP_TRUSTED_BOUNDARY_HARDENING_REQUIRED",
        "BK-F10.9-G5-ATOMIC-AUTHORITY",
        "DOCUMENTED_NO_FULL_ATOMICITY_CLAIM",
        "BOOTSTRAP_HUMAN_NOT_SELF_ATTESTED",
        "F10.9 Trusted Boundary Bootstrap",
        "F10.9 Trusted Boundary PR N v1",
        "CLOSED_BY_PR_N_TRUSTED_BOUNDARY",
        "CANONICAL_REL_ONLY_REJECT_NEXT_AND_UNEXPECTED",
        "NOT_REQUIRED_PENDING_SEPARATE_REMOTE_APPROVAL",
        "CA_ORIGINAL_PASS_CORRECTIVE_ACCEPTANCE_PENDING",
        "E2_STOP_TRUSTED_BOUNDARY_REQUIRED_CHECK_APPROVAL_PENDING",
        "MERGED_POST_MERGE_VERIFIED_TRUSTED_ATTESTATION_MISSING_DEFAULT_BRANCH_REGISTRATION_REQUIRED",
        "E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED",
        "default_branch=main",
        "workflow_exists_in_main=false",
        "F10.9 Trusted Boundary PR P v1",
        "PREPARED_NOT_EXECUTED",
    ):
        assert marker in combined
    assert "No se puede combinar" in combined


def test_preflight_is_completely_offline() -> None:
    source = PRELIGHT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    calls: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    assert imports <= {"__future__", "argparse", "dataclasses", "json", "pathlib", "re", "types", "typing"}
    assert not imports.intersection({"os", "socket", "subprocess", "requests", "httpx", "urllib", "supabase"})
    assert not calls.intersection({"getenv", "urlopen", "connect", "request", "run", "check_output"})
    assert not names.intersection({"environ", "workflow_dispatch", "wrangler"})


def test_preflight_rejects_values_writes_and_combined_gate_drift() -> None:
    manifest = _manifest()
    manifest["required_configuration_names"][0]["value"] = "redacted"
    with pytest.raises(G5OperationalPreflightError, match="STOP_G5_E_MANIFEST_CONTAINS_VALUE_KEY"):
        validate_manifest(manifest)

    manifest = _manifest()
    manifest["github_app_permissions"]["contents"] = "write"
    with pytest.raises(G5OperationalPreflightError, match="STOP_G5_E_GITHUB_APP_PERMISSIONS"):
        validate_manifest(manifest)

    manifest = _manifest()
    manifest["gates"][1]["domain"] = manifest["gates"][0]["domain"]
    with pytest.raises(G5OperationalPreflightError, match="STOP_G5_E_GATE_DOMAIN"):
        validate_manifest(manifest)

    manifest = _manifest()
    manifest["worker_numeric_id"] = 123
    with pytest.raises(G5OperationalPreflightError, match="STOP_G5_E_MANIFEST_KEYS"):
        validate_manifest(manifest)

    manifest = _manifest()
    manifest["required_configuration_names"][0]["remote_id"] = 123
    with pytest.raises(G5OperationalPreflightError, match="STOP_G5_E_CONFIGURATION_NAME_KEYS"):
        validate_manifest(manifest)
