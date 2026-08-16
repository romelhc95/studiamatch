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
CURRENT_GATE = "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
CURRENT_TRUST = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED"
CURRENT_CONNECTED = "IMPLEMENTED_DISABLED_NOT_CONFIGURED"
EXPECTED_BRANCH = "main"
EXPECTED_REF = "refs/heads/main"
EXPECTED_ENVIRONMENT = "Production"
OPERATIONAL_RUN_ATTEMPT_REQUIRED = 1
CI_RETRY_RUN_ATTEMPT = 2

EXPECTED_CONFIGURATION_NAMES = (
    "G5_GITHUB_APP_PRIVATE_KEY",
    "G5_GITHUB_APP_ID",
    "G5_OIDC_AUDIENCE",
    "G5_TRUST_BROKER_ENDPOINT",
    "G5_TRUST_OPERATIONAL_ENABLED",
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
EXPECTED_GATES = ("E1", "E2", "E3", "E4", "E5", "E6")
EXPECTED_GATE_DOMAINS = MappingProxyType(
    {
        "E1": "cloudflare_trust_plane_deployment",
        "E2": "github_app_read_only_configuration",
        "E3": "github_environment_production_configuration",
        "E4": "trust_only_smoke_without_production",
        "E5": "diagnostic_certification_main_promotion",
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
        if name == "G5_TRUST_OPERATIONAL_ENABLED":
            _expect(item.get("state") == "ABSENT_NOT_CONFIGURED", "STOP_G5_E_OPERATIONAL_VAR_PRESENT", errors)
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
    for marker in ("deploy_now", "configure_remote", "workflow_dispatch", "sql_apply"):
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
