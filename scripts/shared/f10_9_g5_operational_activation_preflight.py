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
EXPECTED_STATUS = "PREPARED_NOT_CONFIGURED"
PR387_STATUS = "MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY"
PR390_STATUS = "MERGED_POST_MERGE_VERIFIED"
PR391_STATUS = "MERGED_POST_MERGE_VERIFIED"
E1_STATUS = "E1_DEPLOYMENT_PASS"
E2_STOP = "E2_STOP_GITHUB_RUNTIME_SCHEMA_INCOMPATIBLE"
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
        "pr_387_reconciliation",
        "pr_390_reconciliation",
        "pr_391_reconciliation",
        "e1_deployment_reconciliation",
        "e2_stop",
        "github_runtime_shapes",
        "runtime_policy_resolution",
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
            "source": "GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            "required_fields": ("jobs[].id", "jobs[].name", "jobs[].status", "jobs[].conclusion"),
            "forbidden_fields": ("caller_supplied_job_id",),
            "lifecycle": "exact job name status=in_progress conclusion=null",
        },
        "check_runs": {
            "source": "GET /repos/{owner}/{repo}/commits/{sha}/check-runs",
            "required_fields": ("check_runs[].id", "check_runs[].name", "check_runs[].status", "check_runs[].conclusion"),
            "forbidden_fields": ("caller_supplied_check_run_id",),
            "lifecycle": "exact check name status=in_progress conclusion=null",
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
            "required_fields": ("environment", "state", "log_url", "target_url", "repository_url"),
            "forbidden_fields": ("redirect", "alternate_hostname"),
            "lifecycle": "current-first state=in_progress deployment linked to same run_id and job_id through GitHub job URLs",
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
    _validate_pr387(manifest.get("pr_387_reconciliation"), errors)
    _validate_pr390(manifest.get("pr_390_reconciliation"), errors)
    _validate_pr391(manifest.get("pr_391_reconciliation"), errors)
    _validate_e1(manifest.get("e1_deployment_reconciliation"), errors)
    _expect(manifest.get("e2_stop") == E2_STOP, "STOP_G5_E_E2_STOP", errors)
    _validate_runtime_shapes(manifest.get("github_runtime_shapes"), errors)
    _validate_runtime_policy(manifest.get("runtime_policy_resolution"), errors)
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
