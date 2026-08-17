"""Offline preflight for future G5 operational activation gates.

This module validates a repository-only, name-only manifest. It never reads
environment variables, never opens network transports, and never proves that any
remote Cloudflare, GitHub App, GitHub environment, OIDC, Supabase, or Production
configuration exists.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


PREFLIGHT_VERSION = "f10.9-g5-operational-activation-preflight.v1"
MANIFEST_SCHEMA = "f10.9-g5-operational-activation-manifest.v1"
MANIFEST_MODE = "REPOSITORY_ONLY_NAME_ONLY_NO_VALUES"
EXPECTED_STATUS = "PREPARED_NOT_CONFIGURED_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED"
PR387_STATUS = "MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY"
PR390_STATUS = "MERGED_POST_MERGE_VERIFIED"
PR391_STATUS = "MERGED_POST_MERGE_VERIFIED"
PR392_STATUS = "MERGED_POST_MERGE_VERIFIED_SECURITY_REMEDIATION_REQUIRED"
PR393_STATUS = "MERGED_POST_MERGE_VERIFIED_RESIDUAL_REMEDIATION_REQUIRED"
PR394_STATUS = "MERGED_POST_MERGE_VERIFIED_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED"
PR395_STATUS = "MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED"
PR396_STATUS = "MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_HARDENING_REQUIRED"
PR397_STATUS = "MERGED_POST_MERGE_VERIFIED"
PR398_STATUS = "MERGED_POST_MERGE_VERIFIED_TRUSTED_ATTESTATION_MISSING_DEFAULT_BRANCH_REGISTRATION_REQUIRED"
PR399_STATUS = "MERGED_POST_MERGE_VERIFIED"
E1_STATUS = "E1_DEPLOYMENT_PASS"
E2_STOP = "E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED"
LEGACY_LINK_HARDENING_E2_STOP = "E2_STOP_TRUSTED_BOUNDARY_REQUIRED_CHECK_APPROVAL_PENDING"
CURRENT_GATE = "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
CURRENT_TRUST = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED"
CURRENT_CONNECTED = "IMPLEMENTED_DISABLED_NOT_CONFIGURED"
EXPECTED_BRANCH = "main"
EXPECTED_REF = "refs/heads/main"
EXPECTED_ENVIRONMENT = "Production"
OPERATIONAL_RUN_ATTEMPT_REQUIRED = 1
CI_RETRY_RUN_ATTEMPT = 2

EXPECTED_CONFIGURATION_NAMES = (
    "G5_ALLOWED_CANDIDATE_SHA",
    "G5_ALLOWED_CANDIDATE_TREE",
    "G5_ALLOWED_WORKFLOW_BLOB_SHA",
    "G5_GITHUB_APP_PRIVATE_KEY",
    "G5_GITHUB_APP_ID",
    "G5_GITHUB_APP_INSTALLATION_ID",
    "G5_OIDC_AUDIENCE",
    "G5_TRUST_BROKER_ENDPOINT",
    "G5_TRUST_RUNTIME_ENABLED",
)
EXPECTED_MANIFEST_KEYS = frozenset(
    {
        "schema",
        "mode",
        "status",
        "current_gate",
        "current_trust",
        "current_connected",
        "hito1_integral_status",
        "pr_387_reconciliation",
        "pr_390_reconciliation",
        "pr_391_reconciliation",
        "pr_392_reconciliation",
        "pr_393_reconciliation",
        "pr_394_reconciliation",
        "pr_395_reconciliation",
        "pr_396_reconciliation",
        "pr_397_reconciliation",
        "pr_398_reconciliation",
        "pr_399_reconciliation",
        "default_branch_trusted_workflow_registration",
        "trusted_boundary_pr_p_profile",
        "permanent_trusted_check_hardening",
        "selective_promotion_manifest",
        "post_merge_security_findings",
        "post_merge_pr393_residual_findings",
        "post_merge_pr394_followup_findings",
        "followup_security_remediation",
        "atomic_authority_backlog",
        "trusted_boundary_bootstrap",
        "trusted_boundary_hardening",
        "branch_protection_required_check_update",
        "link_hardening_closure",
        "e1_deployment_reconciliation",
        "e2_stop",
        "github_runtime_shapes",
        "runtime_policy_resolution",
        "runtime_binding_contract",
        "snapshot_cas",
        "terminal_confirmation",
        "github_actions_app_identity",
        "installation_token_scope",
        "future_e2_readonly_preflight",
        "superseded_sequence",
        "required_configuration_names",
        "target",
        "github_app_permissions",
        "workflow_permissions",
        "frozen_versions",
        "gates",
        "forbidden_operations",
    }
)
EXPECTED_HITO1_INTEGRAL_STATUS_KEYS = frozenset(
    {
        "ca1_original_technical",
        "integral_state",
        "evidence_readiness",
        "formal_closure",
        "tracking_only",
    }
)
EXPECTED_HITO1_TRACKING_KEYS = frozenset({"hito1", "f10_9", "g5"})
EXPECTED_PR387_KEYS = frozenset(
    {
        "candidate_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "focused_job_id",
        "focused_conclusion",
        "m3_job_id",
        "m3_conclusion",
        "f9_7_run_id",
        "ci_run_attempt",
        "operational_g5_run_attempt_required",
        "attempts",
    }
)
EXPECTED_ATTEMPT_KEYS = frozenset(
    {"attempt", "job_id", "conclusion", "classification", "scope"}
)
EXPECTED_PR390_KEYS = frozenset(
    {
        "candidate_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "focused_job_id",
        "focused_conclusion",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "run_attempt",
    }
)
EXPECTED_PR391_KEYS = EXPECTED_PR390_KEYS
EXPECTED_PR392_KEYS = frozenset(
    {
        "candidate_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "focused_job_id",
        "focused_conclusion",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "run_attempt",
        "previous_security_auditor_go_preserved",
        "post_merge_security_remediation_required",
    }
)
EXPECTED_PR393_KEYS = frozenset(
    {
        "candidate_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "security_aggregate_job_id",
        "security_aggregate_conclusion",
        "branch_reconciliation_job_id",
        "branch_reconciliation_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "focused_job_id",
        "focused_conclusion",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "run_attempt",
        "merge_tree_reconciled",
        "post_merge_residual_remediation_required",
    }
)
EXPECTED_PR394_KEYS = frozenset(
    {
        "candidate_commits",
        "head_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "focused_job_id",
        "focused_conclusion",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "run_attempt",
        "followup_security_remediation_required",
    }
)
EXPECTED_PR395_KEYS = frozenset(
    {
        "candidate_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "focused_job_id",
        "focused_conclusion",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "run_attempt",
        "trusted_boundary_bootstrap_required",
        "link_hardening_closure_deferred_to_pr_n",
    }
)
EXPECTED_PR396_KEYS = frozenset(
    {
        "candidate_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "focused_job_id",
        "focused_conclusion",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "run_attempt",
        "trusted_boundary_hardening_required",
    }
)
EXPECTED_PR397_KEYS = frozenset(
    {
        "candidate_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "security_audit_job_id",
        "security_audit_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "focused_g5_job_id",
        "focused_g5_conclusion",
        "m3_job_id",
        "m3_conclusion",
        "run_attempt",
    }
)
EXPECTED_PR398_KEYS = frozenset(
    {
        "candidate_sha",
        "base_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "security_run_attempt",
        "security_audit_job_id",
        "security_audit_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "f9_7_run_attempt",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "focused_g5_job_id",
        "focused_g5_conclusion",
        "m3_job_id",
        "m3_conclusion",
        "trusted_check",
        "retroactive_merge_gate_attestation",
    }
)
EXPECTED_PR399_KEYS = frozenset(
    {
        "candidate_sha",
        "base_sha",
        "merge_sha",
        "tree_sha",
        "status",
        "security_run_id",
        "security_conclusion",
        "security_run_attempt",
        "security_audit_job_id",
        "security_audit_conclusion",
        "f9_7_run_id",
        "f9_7_conclusion",
        "f9_7_run_attempt",
        "f9_7_job_id",
        "f9_7_job_conclusion",
        "focused_g5_job_id",
        "focused_g5_conclusion",
        "m3_job_id",
        "m3_conclusion",
    }
)
EXPECTED_DEFAULT_BRANCH_REGISTRATION_KEYS = frozenset(
    {
        "default_branch",
        "workflow_path",
        "workflow_exists_in_desarrollo",
        "workflow_exists_in_main",
        "pull_request_target_requires_default_branch_file",
        "edited_retry_api_enable_can_fix_absence",
        "pr_398_retroactive_merge_gate_attestation_allowed",
        "root_cause",
        "stop",
    }
)
EXPECTED_PR_P_PROFILE_KEYS = frozenset(
    {
        "status",
        "check_name",
        "head_ref",
        "candidate_commits",
        "allowed_statuses",
        "forbidden_workflow_prefixes",
        "forbidden_validator_paths",
        "fork_policy",
        "permissions",
        "persist_credentials",
        "git_policy",
        "secrets",
        "candidate_execution",
        "candidate_actions",
        "candidate_tests",
        "candidate_scripts",
    }
)
EXPECTED_SELECTIVE_PROMOTION_KEYS = frozenset(
    {
        "status",
        "path",
        "scope",
        "promotion_path",
        "execution_guard",
        "default_branch_change",
        "branch_protection_change",
        "workflow_dispatch",
        "required_check_preservation",
    }
)
EXPECTED_PERMANENT_TRUSTED_CHECK_HARDENING_KEYS = frozenset(
    {
        "status",
        "stable_check_name",
        "legacy_one_shot_check_name",
        "pull_request_target_branches",
        "pull_request_target_types",
        "path_filters",
        "out_of_scope_classification",
        "protected_base_evaluation",
        "sensitive_surfaces_without_profile",
        "candidate_workflow_changes",
        "candidate_trusted_validator_changes",
        "candidate_execution",
        "candidate_actions",
        "candidate_tests",
        "candidate_scripts",
        "permissions",
        "persist_credentials",
        "submodules",
        "git_policy",
        "secrets",
        "github_actions_app_provenance",
    }
)
EXPECTED_FINDING_KEYS = frozenset(
    {"id", "severity", "finding", "required_remediation", "status"}
)
EXPECTED_FOLLOWUP_REMEDIATION_KEYS = frozenset(
    {
        "generic_followup_chain_support",
        "pr_394_historical_identity",
        "future_candidate_commits",
        "link_headers",
        "installation_token_fixtures",
        "terminal_confirmation_mutation_tests",
        "residual_multi_endpoint_race",
        "backlog",
    }
)
EXPECTED_ATOMIC_BACKLOG_KEYS = frozenset(
    {
        "id",
        "state",
        "quotable",
        "included_in_hito_progress",
        "implementation_authorized",
    }
)
EXPECTED_TRUSTED_BOUNDARY_BOOTSTRAP_KEYS = frozenset(
    {
        "workflow",
        "check_name",
        "event",
        "status",
        "permissions",
        "secrets",
        "base_code_only",
        "candidate_execution",
        "candidate_actions",
        "candidate_tests",
        "candidate_inspection",
        "fork_policy",
        "shape_policy",
        "actions_pinned_by_sha",
        "does_not_replace_pull_request_tests",
        "future_profile",
    }
)
EXPECTED_TRUSTED_BOUNDARY_HARDENING_KEYS = frozenset(
    {
        "workflow",
        "check_name",
        "status",
        "pull_request_target_types",
        "pr_n_workflow_modifications",
        "trusted_validator_modifications",
        "oid_policy",
        "git_policy",
        "persist_credentials",
        "candidate_execution",
        "candidate_actions",
        "candidate_tests",
        "candidate_scripts",
        "required_check_state",
        "branch_protection_payload_path",
    }
)
EXPECTED_BRANCH_PROTECTION_UPDATE_KEYS = frozenset(
    {
        "status",
        "prepared_from_live_state",
        "live_state_observed_at_utc",
        "target_branch",
        "required_check_to_add",
        "live_state_preserved",
        "request_body",
        "execution_guard",
    }
)
EXPECTED_BRANCH_PROTECTION_REVIEW_KEYS = frozenset(
    {
        "dismiss_stale_reviews",
        "require_code_owner_reviews",
        "require_last_push_approval",
        "required_approving_review_count",
    }
)
EXPECTED_BRANCH_PROTECTION_STATUS_CHECK_KEYS = frozenset({"strict", "checks"})
EXPECTED_BRANCH_PROTECTION_CONTAINER_KEYS = frozenset(
    {
        "required_status_checks",
        "required_pull_request_reviews",
        "enforce_admins",
        "restrictions",
        "required_linear_history",
        "allow_force_pushes",
        "allow_deletions",
        "block_creations",
        "required_conversation_resolution",
        "lock_branch",
        "allow_fork_syncing",
    }
)
BRANCH_PROTECTION_FALSE_FLAGS = (
    "required_linear_history",
    "allow_force_pushes",
    "allow_deletions",
    "block_creations",
    "required_conversation_resolution",
    "lock_branch",
    "allow_fork_syncing",
)
EXPECTED_LINK_HARDENING_CLOSURE_KEYS = frozenset(
    {
        "status",
        "trusted_boundary_required_first",
        "closed_by",
        "link_header_contract",
        "pr_l_repository_only_changes",
    }
)
EXPECTED_E1_KEYS = frozenset(
    {
        "status",
        "credential_state",
        "worker_count_expected",
        "version",
        "binding",
        "class_name",
        "migration_tag",
        "dry_run_bundle_sha256",
        "deployed_payload_sha256",
        "workers_dev_enabled",
        "preview_urls_enabled",
        "routes_count",
        "custom_domains_count",
        "schedules_count",
        "vars_count",
        "secrets_count",
        "endpoint_public",
    }
)
EXPECTED_RUNTIME_SHAPES = frozenset(
    {
        "workflow_run",
        "workflow_jobs",
        "check_runs",
        "branch",
        "environment",
        "approvals",
        "deployments",
        "deployment_statuses",
        "commit",
        "workflow_content_blob",
    }
)
EXPECTED_RUNTIME_SHAPE_ENTRY_KEYS = frozenset(
    {"source", "required_fields", "forbidden_fields", "lifecycle"}
)
EXPECTED_RUNTIME_SHAPE_ENTRIES = MappingProxyType(
    {
        "workflow_run": {
            "source": "GET /repos/{owner}/{repo}/actions/runs/{run_id}",
            "required_fields": (
                "id", "repository.id", "repository.full_name", "repository.owner.id",
                "head_branch", "run_attempt", "event", "status", "conclusion",
                "head_sha", "actor.id", "triggering_actor.id",
            ),
            "forbidden_fields": ("ref_protected", "caller_supplied_sha", "caller_supplied_tree"),
            "lifecycle": "status=in_progress conclusion=null event=workflow_dispatch run_attempt=1",
        },
        "workflow_jobs": {
            "source": "GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100",
            "required_fields": (
                "total_count", "jobs[].id", "jobs[].run_id", "jobs[].run_attempt", "jobs[].head_sha",
                "jobs[].check_run_url", "jobs[].name", "jobs[].status", "jobs[].conclusion",
            ),
            "forbidden_fields": ("caller_supplied_job_id", "independent_check_run_search"),
            "lifecycle": "total_count integer equals returned jobs length; exact-one run-scoped job name run_id exact run_attempt=1 head_sha exact check_run_url exact status=in_progress conclusion=null",
        },
        "check_runs": {
            "source": "GET /repos/{owner}/{repo}/check-runs/{check_run_id}",
            "required_fields": (
                "id", "check_suite.id", "head_sha", "name", "status", "conclusion", "app.id", "app.slug", "app.name", "app.owner.id",
            ),
            "forbidden_fields": ("caller_supplied_check_run_id", "commit_sha_name_array_search", "external_app"),
            "lifecycle": "check_run_id derives only from job.check_run_url; id/head_sha/name exact status=in_progress conclusion=null app=GitHub Actions id=15368 owner.id=9919",
        },
        "branch": {
            "source": "GET /repos/{owner}/{repo}/branches/main",
            "required_fields": ("name", "protected"),
            "forbidden_fields": ("ref_protected", "run.ref_protected"),
            "lifecycle": "name=main protected=true",
        },
        "environment": {
            "source": "GET /repos/{owner}/{repo}/environments/Production",
            "required_fields": ("id", "name", "protection_rules"),
            "forbidden_fields": ("caller_supplied_environment_id",),
            "lifecycle": "name=Production exact-one",
        },
        "approvals": {
            "source": "GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals",
            "required_fields": ("state", "user.id", "environments[].id", "environments[].name"),
            "forbidden_fields": ("check_run_id", "deployment_id", "sha", "workflow_sha"),
            "lifecycle": "exact-one state=approved for Production bound by run endpoint",
        },
        "deployments": {
            "source": "GET /repos/{owner}/{repo}/deployments",
            "required_fields": ("id", "sha", "environment", "statuses_url", "repository_url"),
            "forbidden_fields": ("environment_id", "caller_supplied_deployment_id"),
            "lifecycle": "filter by exact sha and Production before statuses",
        },
        "deployment_statuses": {
            "source": "GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses?per_page=100",
            "required_fields": (
                "id", "state", "created_at", "updated_at", "deployment_url", "log_url", "target_url", "environment", "repository_url",
            ),
            "forbidden_fields": (
                "redirect", "alternate_hostname", "link_rel_next", "malformed_link_header", "ambiguous_link_header",
                "duplicated_link_header", "unexpected_link_header", "duplicate_status_id", "timestamp_tie", "historical_in_progress",
            ),
            "lifecycle": "validate all timestamps ids and Link headers before ordering; reject malformed ambiguous duplicated or unexpected Link headers; select unique temporal maximum; state=in_progress; deployment_url exact; log_url and target_url bound to run_id and job_id; fail closed at 100 results; terminal confirmation repeats deployment status before CAS",
        },
        "commit": {
            "source": "GET /repos/{owner}/{repo}/commits/{sha}",
            "required_fields": ("sha", "commit.tree.sha"),
            "forbidden_fields": ("caller_supplied_tree",),
            "lifecycle": "candidate sha and tree derive from commit endpoint",
        },
        "workflow_content_blob": {
            "source": "GET /repos/{owner}/{repo}/contents/.github/workflows/g5-manual-trust-gate.yml?ref={candidate_sha}",
            "required_fields": ("sha",),
            "forbidden_fields": ("caller_supplied_workflow_blob_sha",),
            "lifecycle": "workflow blob derives from contents endpoint at candidate sha",
        },
    }
)
EXPECTED_RUNTIME_POLICY_KEYS = frozenset(
    {"source", "promotion_order", "caller_supplied", "legacy_fallback"}
)
EXPECTED_RUNTIME_BINDING_CONTRACT_KEYS = frozenset(
    {
        "check_run_source",
        "deployment_status_source",
        "binding_fields_added",
        "check_suite_id_policy",
        "caller_supplied_authority",
    }
)
EXPECTED_SNAPSHOT_CAS_KEYS = frozenset(
    {"snapshot_a", "snapshot_b", "required_match", "reject_on", "internal_retry"}
)
EXPECTED_TERMINAL_CONFIRMATION_KEYS = frozenset(
    {"source", "covered_bindings", "external_request_after_terminal_confirmation", "cas_retry"}
)
EXPECTED_GITHUB_ACTIONS_APP_IDENTITY_KEYS = frozenset(
    {"slug", "name", "id", "owner_id"}
)
EXPECTED_INSTALLATION_SCOPE_KEYS = frozenset(
    {
        "repository_id_source",
        "repository_ids_request",
        "response_repositories",
        "repository_selection",
        "token_schema",
        "token_promise_cache",
        "permissions",
        "additional_permissions",
        "write_permissions",
    }
)
EXPECTED_E2_PREFLIGHT_KEYS = frozenset(
    {"purpose", "state", "permission_added_now", "stop"}
)
EXPECTED_CONFIGURATION_ENTRY_KEYS = frozenset({"name", "scope", "state"})
EXPECTED_TARGET_KEYS = frozenset({"branch", "ref", "environment"})
EXPECTED_GATE_KEYS = frozenset(
    {
        "id",
        "name",
        "domain",
        "future_authorization_required",
        "preconditions",
        "sanitized_outputs",
        "rollback",
        "stop_conditions",
    }
)
EXPECTED_GATES = ("E1", "E2", "E3", "E4", "E4A", "E4B", "E5", "E6")
EXPECTED_GATE_DOMAINS = MappingProxyType(
    {
        "E1": "cloudflare_trust_plane_bootstrap_deployment",
        "E2": "github_app_read_only_configuration",
        "E3": "github_environment_production_disabled_configuration",
        "E4": "diagnostic_certification_main_promotion",
        "E4A": "runtime_policy_exact_binding_and_redeploy",
        "E4B": "trust_broker_endpoint_exposure_decision",
        "E5": "trust_only_smoke_without_data_plane",
        "E6": "g5_creation_approval_consumption",
    }
)
EXPECTED_GITHUB_APP_PERMISSIONS = MappingProxyType(
    {
        "actions": "read",
        "checks": "read",
        "contents": "read",
        "deployments": "read",
        "metadata": "read",
    }
)
EXPECTED_WORKFLOW_PERMISSIONS = MappingProxyType(
    {
        "actions": "read",
        "contents": "read",
        "deployments": "read",
        "id-token": "write",
    }
)
EXPECTED_FROZEN_VERSIONS = MappingProxyType(
    {
        "get_only_contract": "f10.9-g5-get-only-adapter-contract.v2.3",
        "trust_broker": "f10.9-g5-trust-broker.v2",
        "worker_config": "repository-only-v1",
        "wrangler": "4.44.0",
        "workflow_path": ".github/workflows/g5-manual-trust-gate.yml",
    }
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RUN_ID_RE = re.compile(r"^[1-9][0-9]*$")
_NAME_RE = re.compile(r"^G5_[A-Z0-9_]{3,80}$")
_SENSITIVE_VALUE_MARKERS = (
    "http://",
    "https://",
    "eyJhbG",
    "sb_publishable_",
    "sb_secret_",
    "sbp_",
    "ghp_",
    "gho_",
    "ghs_",
    "github_pat_",
    "-----BEGIN",
    "BEGIN PRIVATE KEY",
)
_FORBIDDEN_VALUE_KEYS = {
    "value",
    "secret",
    "token",
    "private_key",
    "current_value",
    "configured_value",
    "materialized_value",
    "installation_identifier",
    "installation_id",
    "remote_identifier",
    "remote_id",
    "project_reference",
    "project_ref",
    "account_identifier",
    "account_id",
    "worker_id",
}


class G5OperationalPreflightError(RuntimeError):
    """Fail-closed error containing only stable reason codes."""


@dataclass(frozen=True)
class PreflightResult:
    decision: str
    version: str
    reason_codes: tuple[str, ...]
    checked_names: tuple[str, ...]
    checked_gates: tuple[str, ...]


def load_manifest(path: str | Path) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_manifest(manifest: Mapping[str, Any]) -> PreflightResult:
    errors: list[str] = []
    _reject_values(manifest, errors)
    _validate_exact_keys(
        manifest, EXPECTED_MANIFEST_KEYS, "STOP_G5_E_MANIFEST_KEYS", errors
    )
    _expect(manifest.get("schema") == MANIFEST_SCHEMA, "STOP_G5_E_MANIFEST_SCHEMA", errors)
    _expect(manifest.get("mode") == MANIFEST_MODE, "STOP_G5_E_MANIFEST_MODE", errors)
    _expect(manifest.get("status") == EXPECTED_STATUS, "STOP_G5_E_STATUS", errors)
    _expect(manifest.get("current_gate") == CURRENT_GATE, "STOP_G5_E_GATE_STATE", errors)
    _expect(
        manifest.get("current_trust") == CURRENT_TRUST,
        "STOP_G5_E_TRUST_STATE",
        errors,
    )
    _expect(
        manifest.get("current_connected") == CURRENT_CONNECTED,
        "STOP_G5_E_CONNECTED_STATE",
        errors,
    )
    _validate_hito1_integral_status(manifest.get("hito1_integral_status"), errors)
    _validate_pr387(manifest.get("pr_387_reconciliation"), errors)
    _validate_pr390(manifest.get("pr_390_reconciliation"), errors)
    _validate_pr391(manifest.get("pr_391_reconciliation"), errors)
    _validate_pr392(manifest.get("pr_392_reconciliation"), errors)
    _validate_pr393(manifest.get("pr_393_reconciliation"), errors)
    _validate_pr394(manifest.get("pr_394_reconciliation"), errors)
    _validate_pr395(manifest.get("pr_395_reconciliation"), errors)
    _validate_pr396(manifest.get("pr_396_reconciliation"), errors)
    _validate_pr397(manifest.get("pr_397_reconciliation"), errors)
    _validate_pr398(manifest.get("pr_398_reconciliation"), errors)
    _validate_pr399(manifest.get("pr_399_reconciliation"), errors)
    _validate_default_branch_registration(manifest.get("default_branch_trusted_workflow_registration"), errors)
    _validate_pr_p_profile(manifest.get("trusted_boundary_pr_p_profile"), errors)
    _validate_permanent_trusted_check_hardening(manifest.get("permanent_trusted_check_hardening"), errors)
    _validate_selective_promotion(manifest.get("selective_promotion_manifest"), errors)
    _validate_findings(manifest.get("post_merge_security_findings"), errors)
    _validate_residual_findings(manifest.get("post_merge_pr393_residual_findings"), errors)
    _validate_followup_findings(manifest.get("post_merge_pr394_followup_findings"), errors)
    _validate_followup_remediation(manifest.get("followup_security_remediation"), errors)
    _validate_atomic_backlog(manifest.get("atomic_authority_backlog"), errors)
    _validate_trusted_boundary_bootstrap(manifest.get("trusted_boundary_bootstrap"), errors)
    _validate_trusted_boundary_hardening(manifest.get("trusted_boundary_hardening"), errors)
    _validate_branch_protection_update(manifest.get("branch_protection_required_check_update"), errors)
    _validate_link_hardening_closure(manifest.get("link_hardening_closure"), errors)
    _validate_e1(manifest.get("e1_deployment_reconciliation"), errors)
    _expect(manifest.get("e2_stop") == E2_STOP, "STOP_G5_E_E2_STOP", errors)
    _validate_runtime_shapes(manifest.get("github_runtime_shapes"), errors)
    _validate_runtime_policy(manifest.get("runtime_policy_resolution"), errors)
    _validate_runtime_binding_contract(manifest.get("runtime_binding_contract"), errors)
    _validate_snapshot_cas(manifest.get("snapshot_cas"), errors)
    _validate_terminal_confirmation(manifest.get("terminal_confirmation"), errors)
    _validate_github_actions_app_identity(manifest.get("github_actions_app_identity"), errors)
    _validate_installation_scope(manifest.get("installation_token_scope"), errors)
    _validate_future_e2_preflight(manifest.get("future_e2_readonly_preflight"), errors)
    checked_names = _validate_required_names(manifest.get("required_configuration_names"), errors)
    checked_gates = _validate_gates(manifest.get("gates"), errors)
    _validate_target(manifest.get("target"), errors)
    _validate_permissions(
        manifest.get("github_app_permissions"),
        EXPECTED_GITHUB_APP_PERMISSIONS,
        allow_write=(),
        reason="STOP_G5_E_GITHUB_APP_PERMISSIONS",
        errors=errors,
    )
    _validate_permissions(
        manifest.get("workflow_permissions"),
        EXPECTED_WORKFLOW_PERMISSIONS,
        allow_write=("id-token",),
        reason="STOP_G5_E_WORKFLOW_PERMISSIONS",
        errors=errors,
    )
    _expect(
        manifest.get("frozen_versions") == EXPECTED_FROZEN_VERSIONS,
        "STOP_G5_E_FROZEN_VERSION_DRIFT",
        errors,
    )
    _validate_absence_of_writes(manifest, errors)
    _expect(
        manifest.get("superseded_sequence") == "E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE",
        "STOP_G5_E_SUPERSEDED_SEQUENCE",
        errors,
    )
    if errors:
        raise G5OperationalPreflightError(",".join(sorted(set(errors))))
    return PreflightResult(
        decision="PASS",
        version=PREFLIGHT_VERSION,
        reason_codes=(),
        checked_names=checked_names,
        checked_gates=checked_gates,
    )


def _expect(condition: bool, reason: str, errors: list[str]) -> None:
    if not condition:
        errors.append(reason)


def _validate_exact_keys(
    value: Mapping[str, Any], expected: frozenset[str], reason: str, errors: list[str]
) -> None:
    if set(value) != expected:
        errors.append(reason)


def _validate_hito1_integral_status(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_HITO1_INTEGRAL_STATUS")
        return
    _validate_exact_keys(value, EXPECTED_HITO1_INTEGRAL_STATUS_KEYS, "STOP_G5_E_HITO1_INTEGRAL_KEYS", errors)
    _expect(value.get("ca1_original_technical") == "PASS", "STOP_G5_E_HITO1_CA1_ORIGINAL", errors)
    _expect(
        value.get("integral_state") == "CA_ORIGINAL_PASS_CORRECTIVE_ACCEPTANCE_PENDING",
        "STOP_G5_E_HITO1_INTEGRAL_STATE",
        errors,
    )
    _expect(value.get("evidence_readiness") == "75%", "STOP_G5_E_HITO1_EVIDENCE_READINESS", errors)
    _expect(value.get("formal_closure") == "NOT_READY", "STOP_G5_E_HITO1_FORMAL_CLOSURE", errors)
    tracking = value.get("tracking_only")
    if not isinstance(tracking, Mapping):
        errors.append("STOP_G5_E_HITO1_TRACKING")
        return
    _validate_exact_keys(tracking, EXPECTED_HITO1_TRACKING_KEYS, "STOP_G5_E_HITO1_TRACKING_KEYS", errors)
    _expect(tracking == {"hito1": "60%", "f10_9": "38%", "g5": "50%"}, "STOP_G5_E_HITO1_TRACKING", errors)


def _reject_values(value: Any, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _FORBIDDEN_VALUE_KEYS:
                errors.append("STOP_G5_E_MANIFEST_CONTAINS_VALUE_KEY")
            _reject_values(item, errors)
        return
    if isinstance(value, list):
        for item in value:
            _reject_values(item, errors)
        return
    if isinstance(value, str) and any(marker in value for marker in _SENSITIVE_VALUE_MARKERS):
        errors.append("STOP_G5_E_MANIFEST_CONTAINS_SENSITIVE_VALUE")


def _validate_pr387(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR387_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR387_KEYS, "STOP_G5_E_PR387_KEYS", errors)
    expected_shas = {
        "candidate_sha": "d62c8969e7d229bb8d2a9e1f8c6db6a1c4ef4d1d",
        "merge_sha": "bd0d82864c26755435e551b835d145b864383810",
        "tree_sha": "135af5a95237a1d4d6e1b977e8bb9ab82ac95e16",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR387_SHA", errors)
    _expect(value.get("status") == PR387_STATUS, "STOP_G5_E_PR387_STATUS", errors)
    _expect(value.get("ci_run_attempt") == CI_RETRY_RUN_ATTEMPT, "STOP_G5_E_CI_ATTEMPT", errors)
    _expect(
        value.get("operational_g5_run_attempt_required") == OPERATIONAL_RUN_ATTEMPT_REQUIRED,
        "STOP_G5_E_OPERATIONAL_ATTEMPT",
        errors,
    )
    for key in ("security_run_id", "focused_job_id", "m3_job_id", "f9_7_run_id"):
        _expect(bool(_RUN_ID_RE.fullmatch(str(value.get(key, "")))), "STOP_G5_E_PR387_RUN_ID", errors)
    attempts = value.get("attempts")
    if not isinstance(attempts, list) or len(attempts) != 2:
        errors.append("STOP_G5_E_PR387_ATTEMPTS")
        return
    expected_attempts = (
        (1, "95079764790", "CANCELLED", "CI_INFRA_TIMEOUT_PLAYWRIGHT_APT"),
        (2, "95084155346", "PASS", "CI_RETRY_PASS"),
    )
    for attempt, expected in zip(attempts, expected_attempts, strict=True):
        if not isinstance(attempt, Mapping):
            errors.append("STOP_G5_E_PR387_ATTEMPTS")
            continue
        _validate_exact_keys(attempt, EXPECTED_ATTEMPT_KEYS, "STOP_G5_E_PR387_ATTEMPT_KEYS", errors)
        number, job_id, conclusion, classification = expected
        _expect(attempt.get("attempt") == number, "STOP_G5_E_PR387_ATTEMPTS", errors)
        _expect(attempt.get("job_id") == job_id, "STOP_G5_E_PR387_ATTEMPTS", errors)
        _expect(attempt.get("conclusion") == conclusion, "STOP_G5_E_PR387_ATTEMPTS", errors)
        _expect(attempt.get("classification") == classification, "STOP_G5_E_PR387_ATTEMPTS", errors)
        _expect(attempt.get("scope") == "CI_ONLY", "STOP_G5_E_PR387_ATTEMPTS", errors)


def _validate_pr390(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR390_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR390_KEYS, "STOP_G5_E_PR390_KEYS", errors)
    expected_shas = {
        "candidate_sha": "c36cc9b6efb166f2f840615759793b7917142f38",
        "merge_sha": "9811b19e1527b39366e43907990c4b77d1394f75",
        "tree_sha": "edb7c827621fce1089d636b50494405115d348a6",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR390_SHA", errors)
    _expect(value.get("status") == PR390_STATUS, "STOP_G5_E_PR390_STATUS", errors)
    _expect(value.get("security_run_id") == "31926378062", "STOP_G5_E_PR390_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR390_SECURITY", errors)
    _expect(value.get("f9_7_run_id") == "31926378069", "STOP_G5_E_PR390_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR390_F97", errors)
    _expect(value.get("focused_job_id") == "95114516929", "STOP_G5_E_PR390_FOCUSED", errors)
    _expect(value.get("focused_conclusion") == "PASS", "STOP_G5_E_PR390_FOCUSED", errors)
    _expect(value.get("f9_7_job_id") == "95114603279", "STOP_G5_E_PR390_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR390_F97_JOB", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR390_ATTEMPT", errors)


def _validate_pr391(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR391_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR391_KEYS, "STOP_G5_E_PR391_KEYS", errors)
    expected_shas = {
        "candidate_sha": "77f475af2e5900bc1338967676ebded71b672642",
        "merge_sha": "5a76abaae8760a9ce6a418511264e6742fa5c74c",
        "tree_sha": "9bd83392ade9e245f3fc4ab85bb85eb4f9031040",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR391_SHA", errors)
    _expect(value.get("status") == PR391_STATUS, "STOP_G5_E_PR391_STATUS", errors)
    _expect(value.get("security_run_id") == "31951803908", "STOP_G5_E_PR391_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR391_SECURITY", errors)
    _expect(value.get("f9_7_run_id") == "31951803820", "STOP_G5_E_PR391_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR391_F97", errors)
    _expect(value.get("focused_job_id") == "95176303149", "STOP_G5_E_PR391_FOCUSED", errors)
    _expect(value.get("focused_conclusion") == "PASS", "STOP_G5_E_PR391_FOCUSED", errors)
    _expect(value.get("f9_7_job_id") == "95176398983", "STOP_G5_E_PR391_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR391_F97_JOB", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR391_ATTEMPT", errors)


def _validate_pr392(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR392_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR392_KEYS, "STOP_G5_E_PR392_KEYS", errors)
    expected_shas = {
        "candidate_sha": "b3f9678e0df76ef8f9dfde8af9147a458a2e033b",
        "merge_sha": "0672156ae5ea13a3ba40ab5f4fd4fd184ec5811e",
        "tree_sha": "7fa8e5c26ddaa67450584b43d5b61c9f7b9edc98",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR392_SHA", errors)
    _expect(value.get("status") == PR392_STATUS, "STOP_G5_E_PR392_STATUS", errors)
    _expect(value.get("security_run_id") == "31958015767", "STOP_G5_E_PR392_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR392_SECURITY", errors)
    _expect(value.get("f9_7_run_id") == "31958015698", "STOP_G5_E_PR392_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR392_F97", errors)
    _expect(value.get("focused_job_id") == "95191560687", "STOP_G5_E_PR392_FOCUSED", errors)
    _expect(value.get("focused_conclusion") == "PASS", "STOP_G5_E_PR392_FOCUSED", errors)
    _expect(value.get("f9_7_job_id") == "95191665616", "STOP_G5_E_PR392_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR392_F97_JOB", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR392_ATTEMPT", errors)
    _expect(value.get("previous_security_auditor_go_preserved") is True, "STOP_G5_E_PR392_PRIOR_GO", errors)
    _expect(value.get("post_merge_security_remediation_required") is True, "STOP_G5_E_PR392_REMEDIATION", errors)


def _validate_pr393(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR393_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR393_KEYS, "STOP_G5_E_PR393_KEYS", errors)
    expected_shas = {
        "candidate_sha": "4d5d97bb37ffcd5126d467bde9152e705a895c85",
        "merge_sha": "51aaac5d289226b1f8f16de1daf69a16a084d585",
        "tree_sha": "7e7be8072cc416d76d2034a126d39393cdbcc968",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR393_SHA", errors)
    _expect(value.get("status") == PR393_STATUS, "STOP_G5_E_PR393_STATUS", errors)
    _expect(value.get("security_run_id") == "31962569422", "STOP_G5_E_PR393_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR393_SECURITY", errors)
    _expect(value.get("security_aggregate_job_id") == "95202769920", "STOP_G5_E_PR393_SECURITY_JOB", errors)
    _expect(value.get("security_aggregate_conclusion") == "PASS", "STOP_G5_E_PR393_SECURITY_JOB", errors)
    _expect(value.get("branch_reconciliation_job_id") == "95202690518", "STOP_G5_E_PR393_BOUNDARY", errors)
    _expect(value.get("branch_reconciliation_conclusion") == "PASS", "STOP_G5_E_PR393_BOUNDARY", errors)
    _expect(value.get("f9_7_run_id") == "31962569598", "STOP_G5_E_PR393_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR393_F97", errors)
    _expect(value.get("focused_job_id") == "95202690713", "STOP_G5_E_PR393_FOCUSED", errors)
    _expect(value.get("focused_conclusion") == "PASS", "STOP_G5_E_PR393_FOCUSED", errors)
    _expect(value.get("f9_7_job_id") == "95202805508", "STOP_G5_E_PR393_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR393_F97_JOB", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR393_ATTEMPT", errors)
    _expect(value.get("merge_tree_reconciled") is True, "STOP_G5_E_PR393_TREE", errors)
    _expect(value.get("post_merge_residual_remediation_required") is True, "STOP_G5_E_PR393_REMEDIATION", errors)


def _validate_pr394(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR394_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR394_KEYS, "STOP_G5_E_PR394_KEYS", errors)
    expected_commits = [
        "7861af0cf94b726d6ce5fadad9ffb6c2274fdcaa",
        "03bab905901f62dba7631a9fe0a87290d70802d9",
        "82ef6e92c125040cededb4a648d1eedd6d519ecf",
    ]
    _expect(value.get("candidate_commits") == expected_commits, "STOP_G5_E_PR394_COMMITS", errors)
    expected_shas = {
        "head_sha": expected_commits[-1],
        "merge_sha": "25be9caffe5674156c7515735a15ad45c5ad22e2",
        "tree_sha": "9f81f71bdabb2012ab593b1999cf4df92fa712eb",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR394_SHA", errors)
    _expect(value.get("status") == PR394_STATUS, "STOP_G5_E_PR394_STATUS", errors)
    _expect(value.get("security_run_id") == "31968991218", "STOP_G5_E_PR394_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR394_SECURITY", errors)
    _expect(value.get("f9_7_run_id") == "31968990202", "STOP_G5_E_PR394_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR394_F97", errors)
    _expect(value.get("focused_job_id") == "95218353795", "STOP_G5_E_PR394_FOCUSED", errors)
    _expect(value.get("focused_conclusion") == "PASS", "STOP_G5_E_PR394_FOCUSED", errors)
    _expect(value.get("f9_7_job_id") == "95218447778", "STOP_G5_E_PR394_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR394_F97_JOB", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR394_ATTEMPT", errors)
    _expect(value.get("followup_security_remediation_required") is True, "STOP_G5_E_PR394_REMEDIATION", errors)


def _validate_pr395(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR395_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR395_KEYS, "STOP_G5_E_PR395_KEYS", errors)
    expected_shas = {
        "candidate_sha": "444c674cf2ff2143bb4b511e88ff6cd30c1fb589",
        "merge_sha": "d04a174915910f50b8adf3d4d4b1216ffbc90b75",
        "tree_sha": "b30329f66ad8b8ba36e6cbd51303bd8e729036a0",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR395_SHA", errors)
    _expect(value.get("status") == PR395_STATUS, "STOP_G5_E_PR395_STATUS", errors)
    _expect(value.get("security_run_id") == "31974315708", "STOP_G5_E_PR395_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR395_SECURITY", errors)
    _expect(value.get("f9_7_run_id") == "31974315810", "STOP_G5_E_PR395_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR395_F97", errors)
    _expect(value.get("focused_job_id") == "95231385472", "STOP_G5_E_PR395_FOCUSED", errors)
    _expect(value.get("focused_conclusion") == "PASS", "STOP_G5_E_PR395_FOCUSED", errors)
    _expect(value.get("f9_7_job_id") == "95231489296", "STOP_G5_E_PR395_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR395_F97_JOB", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR395_ATTEMPT", errors)
    _expect(value.get("trusted_boundary_bootstrap_required") is True, "STOP_G5_E_PR395_BOOTSTRAP", errors)
    _expect(value.get("link_hardening_closure_deferred_to_pr_n") is True, "STOP_G5_E_PR395_LINK_DEFERRED", errors)


def _validate_pr396(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR396_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR396_KEYS, "STOP_G5_E_PR396_KEYS", errors)
    expected_shas = {
        "candidate_sha": "063fb88b3b3dabda78ea641f46da69af09058ab7",
        "merge_sha": "0ec3da6c77b7819a38adcd2f38cd81699adc9283",
        "tree_sha": "ecbe760d50f06d0edce0f36ef84fabacb0a4037c",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR396_SHA", errors)
    _expect(value.get("status") == PR396_STATUS, "STOP_G5_E_PR396_STATUS", errors)
    _expect(value.get("security_run_id") == "31979524771", "STOP_G5_E_PR396_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR396_SECURITY", errors)
    _expect(value.get("f9_7_run_id") == "31979524732", "STOP_G5_E_PR396_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR396_F97", errors)
    _expect(value.get("focused_job_id") == "95243979388", "STOP_G5_E_PR396_FOCUSED", errors)
    _expect(value.get("focused_conclusion") == "PASS", "STOP_G5_E_PR396_FOCUSED", errors)
    _expect(value.get("f9_7_job_id") == "95244079936", "STOP_G5_E_PR396_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR396_F97_JOB", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR396_ATTEMPT", errors)
    _expect(value.get("trusted_boundary_hardening_required") is True, "STOP_G5_E_PR396_HARDENING", errors)


def _validate_pr397(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR397_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR397_KEYS, "STOP_G5_E_PR397_KEYS", errors)
    expected_shas = {
        "candidate_sha": "8adede3ed10605f3af36e905d8f11e7489815d8a",
        "merge_sha": "9a5fcf539c69b635a41616e52716c0ee34837df4",
        "tree_sha": "b33228a031312062b165f8f612d27eacee2fea00",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR397_SHA", errors)
    _expect(value.get("status") == PR397_STATUS, "STOP_G5_E_PR397_STATUS", errors)
    _expect(value.get("security_run_id") == "31984379751", "STOP_G5_E_PR397_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR397_SECURITY", errors)
    _expect(value.get("security_audit_job_id") == "95256753465", "STOP_G5_E_PR397_SECURITY_AUDIT", errors)
    _expect(value.get("security_audit_conclusion") == "PASS", "STOP_G5_E_PR397_SECURITY_AUDIT", errors)
    _expect(value.get("f9_7_run_id") == "31984379715", "STOP_G5_E_PR397_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR397_F97", errors)
    _expect(value.get("f9_7_job_id") == "95256780481", "STOP_G5_E_PR397_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR397_F97_JOB", errors)
    _expect(value.get("focused_g5_job_id") == "95256691723", "STOP_G5_E_PR397_FOCUSED", errors)
    _expect(value.get("focused_g5_conclusion") == "PASS", "STOP_G5_E_PR397_FOCUSED", errors)
    _expect(value.get("m3_job_id") == "95256691760", "STOP_G5_E_PR397_M3", errors)
    _expect(value.get("m3_conclusion") == "PASS", "STOP_G5_E_PR397_M3", errors)
    _expect(value.get("run_attempt") == 1, "STOP_G5_E_PR397_ATTEMPT", errors)


def _validate_pr398(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR398_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR398_KEYS, "STOP_G5_E_PR398_KEYS", errors)
    expected_shas = {
        "candidate_sha": "d03ee28ce90abcbf8efd7c4b37de99b72717207e",
        "base_sha": "9a5fcf539c69b635a41616e52716c0ee34837df4",
        "merge_sha": "85d7f647a37dc784fe16c11da0318956e255b698",
        "tree_sha": "91706dfcc3766fbf69b4fb8c893318786445a2a9",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR398_SHA", errors)
    _expect(value.get("status") == PR398_STATUS, "STOP_G5_E_PR398_STATUS", errors)
    _expect(value.get("security_run_id") == "31992887172", "STOP_G5_E_PR398_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR398_SECURITY", errors)
    _expect(value.get("security_run_attempt") == 1, "STOP_G5_E_PR398_SECURITY_ATTEMPT", errors)
    _expect(value.get("security_audit_job_id") == "95279485661", "STOP_G5_E_PR398_SECURITY_AUDIT", errors)
    _expect(value.get("security_audit_conclusion") == "PASS", "STOP_G5_E_PR398_SECURITY_AUDIT", errors)
    _expect(value.get("f9_7_run_id") == "31992887025", "STOP_G5_E_PR398_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR398_F97", errors)
    _expect(value.get("f9_7_run_attempt") == 1, "STOP_G5_E_PR398_F97_ATTEMPT", errors)
    _expect(value.get("f9_7_job_id") == "95279525942", "STOP_G5_E_PR398_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR398_F97_JOB", errors)
    _expect(value.get("focused_g5_job_id") == "95279414529", "STOP_G5_E_PR398_FOCUSED", errors)
    _expect(value.get("focused_g5_conclusion") == "PASS", "STOP_G5_E_PR398_FOCUSED", errors)
    _expect(value.get("m3_job_id") == "95279414473", "STOP_G5_E_PR398_M3", errors)
    _expect(value.get("m3_conclusion") == "PASS", "STOP_G5_E_PR398_M3", errors)
    _expect(value.get("trusted_check") == "NOT_EXECUTED", "STOP_G5_E_PR398_TRUSTED_CHECK", errors)
    _expect(value.get("retroactive_merge_gate_attestation") == "FORBIDDEN", "STOP_G5_E_PR398_RETROACTIVE", errors)


def _validate_pr399(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR399_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_PR399_KEYS, "STOP_G5_E_PR399_KEYS", errors)
    expected_shas = {
        "candidate_sha": "2e7422e9f67e91ee6b02b4b44fccc060248c13a3",
        "base_sha": "85d7f647a37dc784fe16c11da0318956e255b698",
        "merge_sha": "ab5b0dffe8fe7d677c083e258e86f590d393b731",
        "tree_sha": "fb0b0166b67a58cab14dd0c20e89f034a8adab6e",
    }
    for key, expected in expected_shas.items():
        current = value.get(key)
        _expect(current == expected and bool(_SHA_RE.fullmatch(str(current))), "STOP_G5_E_PR399_SHA", errors)
    _expect(value.get("status") == PR399_STATUS, "STOP_G5_E_PR399_STATUS", errors)
    _expect(value.get("security_run_id") == "31998458176", "STOP_G5_E_PR399_SECURITY", errors)
    _expect(value.get("security_conclusion") == "PASS", "STOP_G5_E_PR399_SECURITY", errors)
    _expect(value.get("security_run_attempt") == 1, "STOP_G5_E_PR399_SECURITY_ATTEMPT", errors)
    _expect(value.get("security_audit_job_id") == "95294350579", "STOP_G5_E_PR399_SECURITY_AUDIT", errors)
    _expect(value.get("security_audit_conclusion") == "PASS", "STOP_G5_E_PR399_SECURITY_AUDIT", errors)
    _expect(value.get("f9_7_run_id") == "31998458172", "STOP_G5_E_PR399_F97", errors)
    _expect(value.get("f9_7_conclusion") == "PASS", "STOP_G5_E_PR399_F97", errors)
    _expect(value.get("f9_7_run_attempt") == 1, "STOP_G5_E_PR399_F97_ATTEMPT", errors)
    _expect(value.get("f9_7_job_id") == "95294383627", "STOP_G5_E_PR399_F97_JOB", errors)
    _expect(value.get("f9_7_job_conclusion") == "PASS", "STOP_G5_E_PR399_F97_JOB", errors)
    _expect(value.get("focused_g5_job_id") == "95294259790", "STOP_G5_E_PR399_FOCUSED", errors)
    _expect(value.get("focused_g5_conclusion") == "PASS", "STOP_G5_E_PR399_FOCUSED", errors)
    _expect(value.get("m3_job_id") == "95294259769", "STOP_G5_E_PR399_M3", errors)
    _expect(value.get("m3_conclusion") == "PASS", "STOP_G5_E_PR399_M3", errors)


def _validate_default_branch_registration(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_DEFAULT_BRANCH_REGISTRATION")
        return
    _validate_exact_keys(value, EXPECTED_DEFAULT_BRANCH_REGISTRATION_KEYS, "STOP_G5_E_DEFAULT_BRANCH_REGISTRATION_KEYS", errors)
    _expect(value.get("default_branch") == "main", "STOP_G5_E_DEFAULT_BRANCH", errors)
    _expect(value.get("workflow_path") == ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml", "STOP_G5_E_DEFAULT_BRANCH_WORKFLOW", errors)
    _expect(value.get("workflow_exists_in_desarrollo") is True, "STOP_G5_E_WORKFLOW_DESARROLLO", errors)
    _expect(value.get("workflow_exists_in_main") is False, "STOP_G5_E_WORKFLOW_MAIN", errors)
    _expect(value.get("pull_request_target_requires_default_branch_file") is True, "STOP_G5_E_PULL_REQUEST_TARGET_DEFAULT", errors)
    _expect(value.get("edited_retry_api_enable_can_fix_absence") is False, "STOP_G5_E_EDITED_RETRY_API", errors)
    _expect(value.get("pr_398_retroactive_merge_gate_attestation_allowed") is False, "STOP_G5_E_RETROACTIVE_PR398", errors)
    _expect(value.get("root_cause") == "DEFAULT_BRANCH_TRUSTED_WORKFLOW_ABSENT", "STOP_G5_E_ROOT_CAUSE", errors)
    _expect(value.get("stop") == E2_STOP, "STOP_G5_E_DEFAULT_BRANCH_STOP", errors)


def _validate_pr_p_profile(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PR_P_PROFILE")
        return
    _validate_exact_keys(value, EXPECTED_PR_P_PROFILE_KEYS, "STOP_G5_E_PR_P_PROFILE_KEYS", errors)
    _expect(value.get("status") == "PREPARED_HUMAN_BOOTSTRAP_NOT_SELF_ATTESTED", "STOP_G5_E_PR_P_PROFILE_STATUS", errors)
    _expect(value.get("check_name") == "F10.9 Trusted Boundary v1", "STOP_G5_E_PR_P_CHECK", errors)
    _expect(value.get("head_ref") == "feat/f10-9-pr-p-trusted-boundary-registration-probe", "STOP_G5_E_PR_P_HEAD", errors)
    _expect(value.get("candidate_commits") == "EXACTLY_ONE_DIRECT_COMMIT", "STOP_G5_E_PR_P_COMMITS", errors)
    _expect(value.get("allowed_statuses") == {".context/operaciones/g5_trusted_boundary_pr_p_probe_2026_08_17.md": "M"}, "STOP_G5_E_PR_P_DELTA", errors)
    _expect(value.get("forbidden_workflow_prefixes") == [".github/workflows/"], "STOP_G5_E_PR_P_WORKFLOW_FORBIDDEN", errors)
    _expect(value.get("forbidden_validator_paths") == ["scripts/security/f109_trusted_boundary_bootstrap.py"], "STOP_G5_E_PR_P_VALIDATOR_FORBIDDEN", errors)
    _expect(value.get("fork_policy") == "REJECT", "STOP_G5_E_PR_P_FORK", errors)
    _expect(value.get("permissions") == {"contents": "read"}, "STOP_G5_E_PR_P_PERMISSIONS", errors)
    _expect(value.get("persist_credentials") is False, "STOP_G5_E_PR_P_CREDENTIALS", errors)
    _expect(value.get("git_policy") == "ISOLATED_CONFIG_HOOKS_DISABLED_FETCH_NO_SUBMODULES", "STOP_G5_E_PR_P_GIT", errors)
    _expect(value.get("secrets") == "FORBIDDEN", "STOP_G5_E_PR_P_SECRETS", errors)
    for key in ("candidate_execution", "candidate_actions", "candidate_tests", "candidate_scripts"):
        _expect(value.get(key) == "FORBIDDEN", "STOP_G5_E_PR_P_CANDIDATE", errors)


def _validate_permanent_trusted_check_hardening(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_PERMANENT_TRUSTED_CHECK_HARDENING")
        return
    _validate_exact_keys(
        value,
        EXPECTED_PERMANENT_TRUSTED_CHECK_HARDENING_KEYS,
        "STOP_G5_E_PERMANENT_TRUSTED_CHECK_HARDENING_KEYS",
        errors,
    )
    _expect(value.get("status") == "PREPARED_REPOSITORY_ONLY_REQUIRED_CHECK_HARDENING", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_STATUS", errors)
    _expect(value.get("stable_check_name") == "F10.9 Trusted Boundary v1", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_NAME", errors)
    _expect(value.get("legacy_one_shot_check_name") == "F10.9 Trusted Boundary PR P v1", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_LEGACY", errors)
    _expect(value.get("pull_request_target_branches") == ["desarrollo"], "STOP_G5_E_PERMANENT_TRUSTED_CHECK_BRANCHES", errors)
    _expect(value.get("pull_request_target_types") == ["opened", "synchronize", "reopened", "ready_for_review", "edited"], "STOP_G5_E_PERMANENT_TRUSTED_CHECK_EVENTS", errors)
    _expect(value.get("path_filters") == "NONE_ALWAYS_REPORT_STATUS", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_PATHS", errors)
    _expect(value.get("out_of_scope_classification") == "OUT_OF_SCOPE_SAFE", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_OUT_OF_SCOPE", errors)
    _expect(value.get("protected_base_evaluation") == "REQUIRED", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_BASE", errors)
    _expect(value.get("sensitive_surfaces_without_profile") == "FAIL", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_SENSITIVE", errors)
    _expect(value.get("candidate_workflow_changes") == "FAIL", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_WORKFLOW", errors)
    _expect(value.get("candidate_trusted_validator_changes") == "FAIL", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_VALIDATOR", errors)
    for key in ("candidate_execution", "candidate_actions", "candidate_tests", "candidate_scripts"):
        _expect(value.get(key) == "FORBIDDEN", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_CANDIDATE", errors)
    _expect(value.get("permissions") == {"contents": "read"}, "STOP_G5_E_PERMANENT_TRUSTED_CHECK_PERMISSIONS", errors)
    _expect(value.get("persist_credentials") is False, "STOP_G5_E_PERMANENT_TRUSTED_CHECK_CREDENTIALS", errors)
    _expect(value.get("submodules") is False, "STOP_G5_E_PERMANENT_TRUSTED_CHECK_SUBMODULES", errors)
    _expect(value.get("git_policy") == "ISOLATED_CONFIG_HOOKS_DISABLED_FETCH_NO_SUBMODULES", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_GIT", errors)
    _expect(value.get("secrets") == "FORBIDDEN", "STOP_G5_E_PERMANENT_TRUSTED_CHECK_SECRETS", errors)
    _expect(value.get("github_actions_app_provenance") == {"name": "GitHub Actions", "app_id": 15368}, "STOP_G5_E_PERMANENT_TRUSTED_CHECK_APP", errors)


def _validate_selective_promotion(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_SELECTIVE_PROMOTION")
        return
    _validate_exact_keys(value, EXPECTED_SELECTIVE_PROMOTION_KEYS, "STOP_G5_E_SELECTIVE_PROMOTION_KEYS", errors)
    _expect(value.get("status") == "PREPARED_NOT_EXECUTED", "STOP_G5_E_SELECTIVE_PROMOTION_STATUS", errors)
    _expect(value.get("path") == ".context/operaciones/g5_trusted_check_definitive_promotion_sanitized_2026_08_17.json", "STOP_G5_E_SELECTIVE_PROMOTION_PATH", errors)
    _expect(value.get("scope") == "SELECTIVE_WORKFLOW_REGISTRATION_ONLY", "STOP_G5_E_SELECTIVE_PROMOTION_SCOPE", errors)
    _expect(value.get("promotion_path") == ["desarrollo", "certificacion", "main"], "STOP_G5_E_SELECTIVE_PROMOTION_PATHS", errors)
    _expect(value.get("execution_guard") == "DO_NOT_EXECUTE_WITHOUT_EXPLICIT_PROMOTION_APPROVAL", "STOP_G5_E_SELECTIVE_PROMOTION_GUARD", errors)
    _expect(value.get("default_branch_change") == "FORBIDDEN", "STOP_G5_E_SELECTIVE_PROMOTION_DEFAULT", errors)
    _expect(value.get("branch_protection_change") == "FORBIDDEN", "STOP_G5_E_SELECTIVE_PROMOTION_PROTECTION", errors)
    _expect(value.get("workflow_dispatch") == "FORBIDDEN", "STOP_G5_E_SELECTIVE_PROMOTION_DISPATCH", errors)
    _expect(value.get("required_check_preservation") == "PRESERVE_EXISTING_REQUIRED_CHECKS_NO_REMOTE_MUTATION", "STOP_G5_E_SELECTIVE_PROMOTION_REQUIRED", errors)


def _validate_findings(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 6:
        errors.append("STOP_G5_E_SECURITY_FINDINGS")
        return
    severities = []
    statuses = []
    ids = []
    for item in value:
        if not isinstance(item, Mapping):
            errors.append("STOP_G5_E_SECURITY_FINDINGS")
            continue
        _validate_exact_keys(item, EXPECTED_FINDING_KEYS, "STOP_G5_E_SECURITY_FINDING_KEYS", errors)
        ids.append(str(item.get("id", "")))
        severities.append(item.get("severity"))
        statuses.append(item.get("status"))
    _expect(len(set(ids)) == 6, "STOP_G5_E_SECURITY_FINDING_IDS", errors)
    _expect(severities.count("HIGH") == 3, "STOP_G5_E_SECURITY_FINDING_SEVERITY", errors)
    _expect(severities.count("MEDIUM") == 3, "STOP_G5_E_SECURITY_FINDING_SEVERITY", errors)
    _expect(statuses.count("REMEDIATED_REPOSITORY_ONLY") == 5, "STOP_G5_E_SECURITY_FINDING_STATUS", errors)
    _expect("STOP_EXPLICIT_E2_PREFLIGHT_REQUIRED" in statuses, "STOP_G5_E_SECURITY_FINDING_STATUS", errors)


def _validate_residual_findings(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 6:
        errors.append("STOP_G5_E_RESIDUAL_FINDINGS")
        return
    ids: list[str] = []
    severities: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            errors.append("STOP_G5_E_RESIDUAL_FINDINGS")
            continue
        _validate_exact_keys(item, EXPECTED_FINDING_KEYS, "STOP_G5_E_RESIDUAL_FINDING_KEYS", errors)
        ids.append(str(item.get("id", "")))
        severities.append(str(item.get("severity", "")))
        _expect(item.get("status") == "REMEDIATED_REPOSITORY_ONLY", "STOP_G5_E_RESIDUAL_FINDING_STATUS", errors)
    _expect(tuple(ids) == tuple(f"PRK-{severity}-{index:03d}" for index, severity in [(1, "HIGH"), (1, "MEDIUM"), (2, "MEDIUM"), (3, "MEDIUM"), (4, "MEDIUM"), (5, "MEDIUM")]), "STOP_G5_E_RESIDUAL_FINDING_IDS", errors)
    _expect(severities.count("HIGH") == 1 and severities.count("MEDIUM") == 5, "STOP_G5_E_RESIDUAL_FINDING_SEVERITY", errors)


def _validate_followup_findings(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 7:
        errors.append("STOP_G5_E_FOLLOWUP_FINDINGS")
        return
    ids: list[str] = []
    statuses: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            errors.append("STOP_G5_E_FOLLOWUP_FINDINGS")
            continue
        _validate_exact_keys(item, EXPECTED_FINDING_KEYS, "STOP_G5_E_FOLLOWUP_FINDING_KEYS", errors)
        ids.append(str(item.get("id", "")))
        statuses.append(str(item.get("status", "")))
    _expect(tuple(ids) == tuple(f"PRL-{index:03d}" for index in range(1, 8)), "STOP_G5_E_FOLLOWUP_FINDING_IDS", errors)
    _expect(set(statuses) == {"REMEDIATED_REPOSITORY_ONLY", "DOCUMENTED_BACKLOG_NOT_EXECUTED"}, "STOP_G5_E_FOLLOWUP_FINDING_STATUS", errors)
    _expect(statuses.count("DOCUMENTED_BACKLOG_NOT_EXECUTED") == 1, "STOP_G5_E_FOLLOWUP_FINDING_STATUS", errors)


def _validate_followup_remediation(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_FOLLOWUP_REMEDIATION")
        return
    _validate_exact_keys(value, EXPECTED_FOLLOWUP_REMEDIATION_KEYS, "STOP_G5_E_FOLLOWUP_REMEDIATION_KEYS", errors)
    expected = {
        "generic_followup_chain_support": "REMOVED",
        "pr_394_historical_identity": "EXACT_THREE_COMMITS_IMMUTABLE",
        "future_candidate_commits": "EXACT_ONE_DIRECT_COMMIT_REQUIRED",
        "link_headers": "REJECT_MALFORMED_AMBIGUOUS_DUPLICATED_UNEXPECTED",
        "installation_token_fixtures": "REQUEST_INDEPENDENT",
        "terminal_confirmation_mutation_tests": "COVER_EACH_TERMINAL_CALL",
        "residual_multi_endpoint_race": "DOCUMENTED_NO_FULL_ATOMICITY_CLAIM",
        "backlog": "BK-F10.9-G5-ATOMIC-AUTHORITY",
    }
    _expect(value == expected, "STOP_G5_E_FOLLOWUP_REMEDIATION", errors)


def _validate_atomic_backlog(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_ATOMIC_BACKLOG")
        return
    _validate_exact_keys(value, EXPECTED_ATOMIC_BACKLOG_KEYS, "STOP_G5_E_ATOMIC_BACKLOG_KEYS", errors)
    _expect(value.get("id") == "BK-F10.9-G5-ATOMIC-AUTHORITY", "STOP_G5_E_ATOMIC_BACKLOG_ID", errors)
    _expect(value.get("state") == "BACKLOG_NON_EXECUTABLE_QUOTABLE", "STOP_G5_E_ATOMIC_BACKLOG_STATE", errors)
    _expect(value.get("quotable") is True, "STOP_G5_E_ATOMIC_BACKLOG_QUOTABLE", errors)
    _expect(value.get("included_in_hito_progress") is False, "STOP_G5_E_ATOMIC_BACKLOG_PROGRESS", errors)
    _expect(value.get("implementation_authorized") is False, "STOP_G5_E_ATOMIC_BACKLOG_AUTH", errors)


def _validate_trusted_boundary_bootstrap(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_TRUSTED_BOUNDARY_BOOTSTRAP")
        return
    _validate_exact_keys(value, EXPECTED_TRUSTED_BOUNDARY_BOOTSTRAP_KEYS, "STOP_G5_E_TRUSTED_BOUNDARY_KEYS", errors)
    _expect(value.get("workflow") == ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml", "STOP_G5_E_TRUSTED_BOUNDARY_WORKFLOW", errors)
    _expect(value.get("check_name") == "F10.9 Trusted Boundary Bootstrap", "STOP_G5_E_TRUSTED_BOUNDARY_CHECK", errors)
    _expect(value.get("event") == "pull_request_target", "STOP_G5_E_TRUSTED_BOUNDARY_EVENT", errors)
    _expect(value.get("status") == "BOOTSTRAP_HUMAN_NOT_SELF_ATTESTED", "STOP_G5_E_TRUSTED_BOUNDARY_STATUS", errors)
    _expect(value.get("permissions") == {"contents": "read"}, "STOP_G5_E_TRUSTED_BOUNDARY_PERMISSIONS", errors)
    _expect(value.get("secrets") == "FORBIDDEN", "STOP_G5_E_TRUSTED_BOUNDARY_SECRETS", errors)
    _expect(value.get("base_code_only") is True, "STOP_G5_E_TRUSTED_BOUNDARY_BASE_CODE", errors)
    for key in ("candidate_execution", "candidate_actions", "candidate_tests"):
        _expect(value.get(key) == "FORBIDDEN", "STOP_G5_E_TRUSTED_BOUNDARY_CANDIDATE", errors)
    _expect(value.get("candidate_inspection") == "GIT_OBJECTS_AS_UNTRUSTED_DATA", "STOP_G5_E_TRUSTED_BOUNDARY_INSPECTION", errors)
    _expect(value.get("fork_policy") == "REJECT", "STOP_G5_E_TRUSTED_BOUNDARY_FORK", errors)
    _expect(value.get("shape_policy") == "FAIL_CLOSED_EXACT_BASE_HEAD_DIRECT_COMMIT_ANCESTRY_PATH_STATUS_MODE", "STOP_G5_E_TRUSTED_BOUNDARY_SHAPE", errors)
    _expect(value.get("actions_pinned_by_sha") is True, "STOP_G5_E_TRUSTED_BOUNDARY_PIN", errors)
    _expect(value.get("does_not_replace_pull_request_tests") is True, "STOP_G5_E_TRUSTED_BOUNDARY_REPLACEMENT", errors)
    _expect(value.get("future_profile") == "PR_N_LINK_HARDENING_CLOSURE_ONLY", "STOP_G5_E_TRUSTED_BOUNDARY_PROFILE", errors)


def _validate_trusted_boundary_hardening(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_TRUSTED_BOUNDARY_HARDENING")
        return
    _validate_exact_keys(
        value,
        EXPECTED_TRUSTED_BOUNDARY_HARDENING_KEYS,
        "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_KEYS",
        errors,
    )
    _expect(value.get("workflow") == ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_WORKFLOW", errors)
    _expect(value.get("check_name") == "F10.9 Trusted Boundary PR N v1", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_CHECK", errors)
    _expect(value.get("status") == "REPOSITORY_ONLY_HARDENED_NOT_REQUIRED_CHECK", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_STATUS", errors)
    _expect(
        value.get("pull_request_target_types") == ["opened", "synchronize", "reopened", "ready_for_review", "edited"],
        "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_EVENTS",
        errors,
    )
    _expect(value.get("pr_n_workflow_modifications") == "FORBIDDEN", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_WORKFLOWS", errors)
    _expect(value.get("trusted_validator_modifications") == "FORBIDDEN", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_VALIDATOR", errors)
    _expect(value.get("oid_policy") == "LOWERCASE_HEX_SHA_40_BEFORE_GIT", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_OID", errors)
    _expect(value.get("git_policy") == "ISOLATED_CONFIG_HOOKS_DISABLED_FETCH_NO_SUBMODULES", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_GIT", errors)
    _expect(value.get("persist_credentials") is False, "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_CREDENTIALS", errors)
    for key in ("candidate_execution", "candidate_actions", "candidate_tests", "candidate_scripts"):
        _expect(value.get(key) == "FORBIDDEN", "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_CANDIDATE", errors)
    _expect(
        value.get("required_check_state") == "NOT_REQUIRED_PENDING_SEPARATE_REMOTE_APPROVAL",
        "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_REQUIRED_CHECK",
        errors,
    )
    _expect(
        value.get("branch_protection_payload_path") == ".context/operaciones/g5_trusted_required_check_payload_sanitized_2026_08_16.json",
        "STOP_G5_E_TRUSTED_BOUNDARY_HARDENING_PAYLOAD",
        errors,
    )


def _validate_branch_protection_update(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_BRANCH_PROTECTION_UPDATE")
        return
    _validate_exact_keys(value, EXPECTED_BRANCH_PROTECTION_UPDATE_KEYS, "STOP_G5_E_BRANCH_PROTECTION_UPDATE_KEYS", errors)
    _expect(value.get("status") == "PREPARED_NOT_EXECUTED_REQUIRES_EXPLICIT_REMOTE_APPROVAL", "STOP_G5_E_BRANCH_PROTECTION_UPDATE_STATUS", errors)
    _expect(value.get("prepared_from_live_state") is True, "STOP_G5_E_BRANCH_PROTECTION_LIVE_STATE", errors)
    _expect(value.get("target_branch") == "desarrollo", "STOP_G5_E_BRANCH_PROTECTION_BRANCH", errors)
    _expect(value.get("execution_guard") == "DO_NOT_EXECUTE_WITHOUT_EXPLICIT_ADDITIONAL_APPROVAL", "STOP_G5_E_BRANCH_PROTECTION_GUARD", errors)
    required = value.get("required_check_to_add")
    _expect(required == {"context": "F10.9 Trusted Boundary v1", "app_id": 15368}, "STOP_G5_E_BRANCH_PROTECTION_REQUIRED_CHECK", errors)
    live = value.get("live_state_preserved")
    body = value.get("request_body")
    if not isinstance(live, Mapping) or not isinstance(body, Mapping):
        errors.append("STOP_G5_E_BRANCH_PROTECTION_BODY")
        return
    _validate_exact_keys(live, EXPECTED_BRANCH_PROTECTION_CONTAINER_KEYS, "STOP_G5_E_BRANCH_PROTECTION_CONTAINER_KEYS", errors)
    _validate_exact_keys(body, EXPECTED_BRANCH_PROTECTION_CONTAINER_KEYS, "STOP_G5_E_BRANCH_PROTECTION_CONTAINER_KEYS", errors)
    live_checks = live.get("required_status_checks", {})
    body_checks = body.get("required_status_checks", {})
    if not isinstance(live_checks, Mapping) or not isinstance(body_checks, Mapping):
        errors.append("STOP_G5_E_BRANCH_PROTECTION_CHECKS")
        return
    _validate_exact_keys(live_checks, EXPECTED_BRANCH_PROTECTION_STATUS_CHECK_KEYS, "STOP_G5_E_BRANCH_PROTECTION_STATUS_CHECK_KEYS", errors)
    _validate_exact_keys(body_checks, EXPECTED_BRANCH_PROTECTION_STATUS_CHECK_KEYS, "STOP_G5_E_BRANCH_PROTECTION_STATUS_CHECK_KEYS", errors)
    _expect(live_checks.get("strict") is True and body_checks.get("strict") is True, "STOP_G5_E_BRANCH_PROTECTION_STRICT", errors)
    _expect(live_checks.get("checks") == [{"context": "security-audit", "app_id": 15368}], "STOP_G5_E_BRANCH_PROTECTION_SECURITY_AUDIT", errors)
    _expect(
        body_checks.get("checks") == [
            {"context": "security-audit", "app_id": 15368},
            {"context": "F10.9 Trusted Boundary v1", "app_id": 15368},
        ],
        "STOP_G5_E_BRANCH_PROTECTION_CHECKS",
        errors,
    )
    for container in (live, body):
        reviews = container.get("required_pull_request_reviews", {})
        if not isinstance(reviews, Mapping):
            errors.append("STOP_G5_E_BRANCH_PROTECTION_REVIEWS")
            continue
        _validate_exact_keys(reviews, EXPECTED_BRANCH_PROTECTION_REVIEW_KEYS, "STOP_G5_E_BRANCH_PROTECTION_REVIEW_KEYS", errors)
        _expect(reviews.get("dismiss_stale_reviews") is True, "STOP_G5_E_BRANCH_PROTECTION_STALE", errors)
        _expect(reviews.get("require_code_owner_reviews") is False, "STOP_G5_E_BRANCH_PROTECTION_CODEOWNERS", errors)
        _expect(reviews.get("require_last_push_approval") is True, "STOP_G5_E_BRANCH_PROTECTION_LAST_PUSH", errors)
        _expect(reviews.get("required_approving_review_count") == 1, "STOP_G5_E_BRANCH_PROTECTION_REVIEW_COUNT", errors)
        _expect(container.get("enforce_admins") is True, "STOP_G5_E_BRANCH_PROTECTION_ADMIN", errors)
        _expect(container.get("restrictions") is None, "STOP_G5_E_BRANCH_PROTECTION_RESTRICTIONS", errors)
        for flag in BRANCH_PROTECTION_FALSE_FLAGS:
            _expect(container.get(flag) is False, "STOP_G5_E_BRANCH_PROTECTION_FLAGS", errors)


def _validate_link_hardening_closure(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_LINK_HARDENING_CLOSURE")
        return
    _validate_exact_keys(value, EXPECTED_LINK_HARDENING_CLOSURE_KEYS, "STOP_G5_E_LINK_CLOSURE_KEYS", errors)
    _expect(value.get("status") == "CLOSED_BY_PR_N_TRUSTED_BOUNDARY", "STOP_G5_E_LINK_CLOSURE_STATUS", errors)
    _expect(value.get("trusted_boundary_required_first") is True, "STOP_G5_E_LINK_CLOSURE_BOUNDARY", errors)
    _expect(value.get("closed_by") == "PR_N_LINK_HARDENING_CLOSURE", "STOP_G5_E_LINK_CLOSURE_PRN", errors)
    _expect(
        value.get("link_header_contract") == "CANONICAL_REL_ONLY_REJECT_NEXT_AND_UNEXPECTED",
        "STOP_G5_E_LINK_CLOSURE_CONTRACT",
        errors,
    )
    _expect(
        value.get("pr_l_repository_only_changes") == "REVALIDATED_AND_CLOSED_UNDER_TRUSTED_BOUNDARY_PR_N",
        "STOP_G5_E_LINK_CLOSURE_PRL",
        errors,
    )


def _validate_runtime_shapes(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_RUNTIME_SHAPES")
        return
    _validate_exact_keys(value, EXPECTED_RUNTIME_SHAPES, "STOP_G5_E_RUNTIME_SHAPE_KEYS", errors)
    for name, shape in value.items():
        if not isinstance(shape, Mapping):
            errors.append("STOP_G5_E_RUNTIME_SHAPES")
            continue
        _validate_exact_keys(shape, EXPECTED_RUNTIME_SHAPE_ENTRY_KEYS, "STOP_G5_E_RUNTIME_SHAPE_ENTRY_KEYS", errors)
        expected = EXPECTED_RUNTIME_SHAPE_ENTRIES.get(str(name))
        if expected is None:
            errors.append("STOP_G5_E_RUNTIME_SHAPE_KEYS")
            continue
        _expect(shape.get("source") == expected["source"], "STOP_G5_E_RUNTIME_SHAPE_SOURCE", errors)
        _expect(shape.get("lifecycle") == expected["lifecycle"], "STOP_G5_E_RUNTIME_SHAPE_LIFECYCLE", errors)
        for key in ("required_fields", "forbidden_fields"):
            fields = shape.get(key)
            _expect(
                isinstance(fields, list)
                and tuple(fields) == expected[key],
                "STOP_G5_E_RUNTIME_SHAPE_FIELDS",
                errors,
            )


def _validate_e1(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_E1_EVIDENCE")
        return
    _validate_exact_keys(value, EXPECTED_E1_KEYS, "STOP_G5_E_E1_KEYS", errors)
    _expect(value.get("status") == E1_STATUS, "STOP_G5_E_E1_STATUS", errors)
    _expect(
        value.get("credential_state") == "E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED",
        "STOP_G5_E_E1_CREDENTIAL",
        errors,
    )
    _expect(value.get("worker_count_expected") == 1, "STOP_G5_E_E1_WORKER_COUNT", errors)
    _expect(value.get("version") == "f10.9-g5-trust-broker.v2", "STOP_G5_E_E1_VERSION", errors)
    _expect(value.get("binding") == "G5_ATOMIC_LEDGER", "STOP_G5_E_E1_BINDING", errors)
    _expect(value.get("class_name") == "G5AtomicLedgerDurableObject", "STOP_G5_E_E1_CLASS", errors)
    _expect(value.get("migration_tag") == "repository-only-v1", "STOP_G5_E_E1_MIGRATION", errors)
    for key in ("dry_run_bundle_sha256", "deployed_payload_sha256"):
        _expect(bool(re.fullmatch(r"[0-9a-f]{64}", str(value.get(key, "")))), "STOP_G5_E_E1_DIGEST", errors)
    for key in ("workers_dev_enabled", "preview_urls_enabled", "endpoint_public"):
        _expect(value.get(key) is False, "STOP_G5_E_E1_EXPOSURE", errors)
    for key in ("routes_count", "custom_domains_count", "schedules_count", "vars_count", "secrets_count"):
        _expect(value.get(key) == 0, "STOP_G5_E_E1_ZERO_SURFACE", errors)


def _validate_runtime_policy(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_RUNTIME_POLICY")
        return
    _validate_exact_keys(value, EXPECTED_RUNTIME_POLICY_KEYS, "STOP_G5_E_RUNTIME_POLICY_KEYS", errors)
    _expect(value.get("source") == "FUTURE_RUNTIME_BINDINGS_NAME_ONLY", "STOP_G5_E_RUNTIME_POLICY", errors)
    _expect(
        value.get("promotion_order")
        == "MAIN_PROMOTION_FIRST_THEN_CONFIGURE_SHA_TREE_BLOB_THEN_BROKER_CONSUMES_IMMUTABLE_POLICY",
        "STOP_G5_E_RUNTIME_POLICY_ORDER",
        errors,
    )
    _expect(value.get("caller_supplied") == "FORBIDDEN", "STOP_G5_E_RUNTIME_POLICY_CALLER", errors)
    _expect(value.get("legacy_fallback") == "FORBIDDEN", "STOP_G5_E_RUNTIME_POLICY_LEGACY", errors)


def _validate_runtime_binding_contract(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_RUNTIME_BINDING_CONTRACT")
        return
    _validate_exact_keys(value, EXPECTED_RUNTIME_BINDING_CONTRACT_KEYS, "STOP_G5_E_RUNTIME_BINDING_KEYS", errors)
    _expect(value.get("check_run_source") == "job.check_run_url_only", "STOP_G5_E_RUNTIME_BINDING_CHECK", errors)
    _expect(
        value.get("deployment_status_source") == "unique_temporal_maximum_after_validation",
        "STOP_G5_E_RUNTIME_BINDING_STATUS",
        errors,
    )
    _expect(
        value.get("binding_fields_added") == ["jobId", "deploymentStatusId", "checkSuiteId"],
        "STOP_G5_E_RUNTIME_BINDING_FIELDS",
        errors,
    )
    _expect(
        value.get("check_suite_id_policy")
        == "included_because_check_run.check_suite.id_is_authoritative_and_stable_in_rest_shape",
        "STOP_G5_E_RUNTIME_BINDING_CHECK_SUITE",
        errors,
    )
    _expect(value.get("caller_supplied_authority") == "FORBIDDEN", "STOP_G5_E_RUNTIME_BINDING_CALLER", errors)


def _validate_snapshot_cas(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_SNAPSHOT_CAS")
        return
    _validate_exact_keys(value, EXPECTED_SNAPSHOT_CAS_KEYS, "STOP_G5_E_SNAPSHOT_CAS_KEYS", errors)
    _expect(str(value.get("snapshot_a", "")).startswith("collect_run_job_check"), "STOP_G5_E_SNAPSHOT_A", errors)
    _expect(str(value.get("snapshot_b", "")).startswith("requery_same_evidence"), "STOP_G5_E_SNAPSHOT_B", errors)
    _expect(value.get("required_match") == "stable_binding_identity_exact", "STOP_G5_E_SNAPSHOT_MATCH", errors)
    reject_on = value.get("reject_on")
    _expect(isinstance(reject_on, list) and len(reject_on) == 6, "STOP_G5_E_SNAPSHOT_REJECT_ON", errors)
    _expect(value.get("internal_retry") == "FORBIDDEN", "STOP_G5_E_SNAPSHOT_RETRY", errors)


def _validate_terminal_confirmation(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_TERMINAL_CONFIRMATION")
        return
    _validate_exact_keys(
        value,
        EXPECTED_TERMINAL_CONFIRMATION_KEYS,
        "STOP_G5_E_TERMINAL_CONFIRMATION_KEYS",
        errors,
    )
    _expect(
        value.get("source") == "requery_run_job_check_and_deployment_status_after_snapshot_b_immediately_before_cas",
        "STOP_G5_E_TERMINAL_CONFIRMATION_SOURCE",
        errors,
    )
    _expect(
        value.get("covered_bindings")
        == [
            "repositoryId", "runId", "runAttempt", "checkRunId", "checkSuiteId",
            "jobId", "deploymentId", "deploymentStatusId",
        ],
        "STOP_G5_E_TERMINAL_CONFIRMATION_BINDINGS",
        errors,
    )
    _expect(
        value.get("external_request_after_terminal_confirmation") == "FORBIDDEN",
        "STOP_G5_E_TERMINAL_CONFIRMATION_ORDER",
        errors,
    )
    _expect(value.get("cas_retry") == "FORBIDDEN", "STOP_G5_E_TERMINAL_CONFIRMATION_RETRY", errors)


def _validate_github_actions_app_identity(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_GITHUB_ACTIONS_APP_IDENTITY")
        return
    _validate_exact_keys(
        value,
        EXPECTED_GITHUB_ACTIONS_APP_IDENTITY_KEYS,
        "STOP_G5_E_GITHUB_ACTIONS_APP_IDENTITY_KEYS",
        errors,
    )
    _expect(value.get("slug") == "github-actions", "STOP_G5_E_GITHUB_ACTIONS_APP_SLUG", errors)
    _expect(value.get("name") == "GitHub Actions", "STOP_G5_E_GITHUB_ACTIONS_APP_NAME", errors)
    _expect(value.get("id") == 15368, "STOP_G5_E_GITHUB_ACTIONS_APP_ID", errors)
    _expect(value.get("owner_id") == 9919, "STOP_G5_E_GITHUB_ACTIONS_APP_OWNER", errors)


def _validate_installation_scope(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_INSTALLATION_SCOPE")
        return
    _validate_exact_keys(value, EXPECTED_INSTALLATION_SCOPE_KEYS, "STOP_G5_E_INSTALLATION_SCOPE_KEYS", errors)
    _expect(
        value.get("repository_id_source") == "oidc_repository_id_verified_against_run_repository",
        "STOP_G5_E_INSTALLATION_REPOSITORY_SOURCE",
        errors,
    )
    _expect(value.get("repository_ids_request") == "exact_single_repository_id", "STOP_G5_E_INSTALLATION_REPOSITORY_IDS", errors)
    _expect(value.get("response_repositories") == "exact_single_expected_repository", "STOP_G5_E_INSTALLATION_RESPONSE_REPO", errors)
    _expect(value.get("repository_selection") == "selected_required", "STOP_G5_E_INSTALLATION_SELECTION", errors)
    _expect(value.get("token_schema") == "exact_known_response_keys", "STOP_G5_E_INSTALLATION_TOKEN_SCHEMA", errors)
    _expect(value.get("token_promise_cache") == "segmented_by_repository_id", "STOP_G5_E_INSTALLATION_TOKEN_PROMISE", errors)
    _validate_permissions(
        value.get("permissions"),
        EXPECTED_GITHUB_APP_PERMISSIONS,
        allow_write=(),
        reason="STOP_G5_E_INSTALLATION_PERMISSIONS",
        errors=errors,
    )
    _expect(value.get("additional_permissions") == "FORBIDDEN", "STOP_G5_E_INSTALLATION_ADDITIONAL", errors)
    _expect(value.get("write_permissions") == "FORBIDDEN", "STOP_G5_E_INSTALLATION_WRITE", errors)


def _validate_future_e2_preflight(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("STOP_G5_E_E2_PREFLIGHT")
        return
    _validate_exact_keys(value, EXPECTED_E2_PREFLIGHT_KEYS, "STOP_G5_E_E2_PREFLIGHT_KEYS", errors)
    _expect(
        value.get("purpose") == "confirm_whether_environment_endpoint_requires_additional_permission_before_e2",
        "STOP_G5_E_E2_PREFLIGHT_PURPOSE",
        errors,
    )
    _expect(value.get("state") == "DOCUMENTED_NOT_EXECUTED", "STOP_G5_E_E2_PREFLIGHT_STATE", errors)
    _expect(value.get("permission_added_now") is False, "STOP_G5_E_E2_PREFLIGHT_PERMISSION", errors)
    _expect(value.get("stop") == E2_STOP, "STOP_G5_E_E2_PREFLIGHT_STOP", errors)


def _validate_required_names(value: Any, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        errors.append("STOP_G5_E_CONFIGURATION_NAMES")
        return ()
    names: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            errors.append("STOP_G5_E_CONFIGURATION_NAMES")
            continue
        _validate_exact_keys(
            item,
            EXPECTED_CONFIGURATION_ENTRY_KEYS,
            "STOP_G5_E_CONFIGURATION_NAME_KEYS",
            errors,
        )
        name = str(item.get("name", ""))
        names.append(name)
        _expect(bool(_NAME_RE.fullmatch(name)), "STOP_G5_E_CONFIGURATION_NAME_FORMAT", errors)
        _expect(
            item.get("state") in {"NAME_ONLY_NOT_CONFIGURED", "ABSENT_NOT_CONFIGURED"},
            "STOP_G5_E_CONFIGURATION_NAME_STATE",
            errors,
        )
        if name in EXPECTED_CONFIGURATION_NAMES:
            _expect(item.get("state") == "ABSENT_NOT_CONFIGURED", "STOP_G5_E_RUNTIME_NAME_PRESENT", errors)
    _expect(tuple(names) == EXPECTED_CONFIGURATION_NAMES, "STOP_G5_E_CONFIGURATION_NAMES", errors)
    return tuple(names)


def _validate_gates(value: Any, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        errors.append("STOP_G5_E_GATES")
        return ()
    ids: list[str] = []
    domains: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping):
            errors.append("STOP_G5_E_GATES")
            continue
        _validate_exact_keys(item, EXPECTED_GATE_KEYS, "STOP_G5_E_GATE_KEYS", errors)
        gate_id = str(item.get("id", ""))
        ids.append(gate_id)
        domain = str(item.get("domain", ""))
        domains.add(domain)
        _expect(EXPECTED_GATE_DOMAINS.get(gate_id) == domain, "STOP_G5_E_GATE_DOMAIN", errors)
        _expect(item.get("future_authorization_required") is True, "STOP_G5_E_GATE_AUTHORIZATION", errors)
        for field in ("preconditions", "sanitized_outputs", "rollback", "stop_conditions"):
            _expect(isinstance(item.get(field), list) and len(item[field]) > 0, "STOP_G5_E_GATE_RUNBOOK", errors)
    _expect(tuple(ids) == EXPECTED_GATES, "STOP_G5_E_GATES", errors)
    _expect(len(domains) == len(EXPECTED_GATES), "STOP_G5_E_GATE_COMBINATION", errors)
    if isinstance(value, list):
        gates_by_id = {
            str(item.get("id", "")): item
            for item in value
            if isinstance(item, Mapping)
        }
        e5 = gates_by_id.get("E5", {})
        e5_text = " ".join(
            map(str, (*e5.get("preconditions", ()), *e5.get("stop_conditions", ())))
        ) if isinstance(e5, Mapping) else ""
        for required in ("E4", "E4A", "E4B"):
            _expect(required in e5_text, "STOP_G5_E_E5_NOT_BLOCKED_BY_PRIOR_GATES", errors)
    return tuple(ids)


def _validate_target(value: Any, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        _validate_exact_keys(value, EXPECTED_TARGET_KEYS, "STOP_G5_E_TARGET_KEYS", errors)
    _expect(
        isinstance(value, Mapping)
        and value.get("branch") == EXPECTED_BRANCH
        and value.get("ref") == EXPECTED_REF
        and value.get("environment") == EXPECTED_ENVIRONMENT,
        "STOP_G5_E_TARGET",
        errors,
    )


def _validate_permissions(
    value: Any,
    expected: Mapping[str, str],
    *,
    allow_write: tuple[str, ...],
    reason: str,
    errors: list[str],
) -> None:
    _expect(value == expected, reason, errors)
    if isinstance(value, Mapping):
        for permission, access in value.items():
            if access == "write" and permission not in allow_write:
                errors.append("STOP_G5_E_UNAUTHORIZED_WRITE_PERMISSION")


def _validate_absence_of_writes(manifest: Mapping[str, Any], errors: list[str]) -> None:
    forbidden = manifest.get("forbidden_operations")
    _expect(isinstance(forbidden, list) and "writes" in forbidden, "STOP_G5_E_WRITE_GUARD", errors)
    text = json.dumps(manifest, sort_keys=True)
    for marker in ("deploy_now", "configure_remote", "sql_apply"):
        _expect(marker not in text, "STOP_G5_E_REMOTE_OPERATION_MARKER", errors)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = validate_manifest(load_manifest(args.manifest))
    except G5OperationalPreflightError as exc:
        print(f"STOP {exc}")
        return 1
    print(f"{result.decision} {result.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
