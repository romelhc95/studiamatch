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
    assert manifest["frozen_versions"]["wrangler"] == "4.44.0"
    assert any(
        item["name"] == "G5_TRUST_OPERATIONAL_ENABLED"
        and item["state"] == "ABSENT_NOT_CONFIGURED"
        for item in manifest["required_configuration_names"]
    )


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
        "installation_id",
        "project_ref",
        "account_id",
        "workers_dev",
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


def test_gates_e1_to_e6_and_e3a_are_separate_and_non_executing() -> None:
    manifest = _manifest()
    gates = manifest["gates"]
    assert [gate["id"] for gate in gates] == list(EXPECTED_GATES)
    domains = [gate["domain"] for gate in gates]
    assert len(domains) == len(set(domains)) == 7
    for gate in gates:
        assert gate["future_authorization_required"] is True
        assert gate["preconditions"]
        assert gate["sanitized_outputs"]
        assert gate["rollback"]
        assert gate["stop_conditions"]
    gates_by_id = {gate["id"]: gate for gate in gates}
    assert gates_by_id["E3A"]["domain"] == "trust_broker_endpoint_exposure_decision"
    assert "DEFINED_NOT_EXECUTED" in RUNBOOK_PATH.read_text(encoding="utf-8")
    assert any("E3A" in condition for condition in gates_by_id["E4"]["preconditions"])
    assert any("E3A" in condition for condition in gates_by_id["E4"]["stop_conditions"])


def test_runbook_and_adr_preserve_operational_run_attempt_one() -> None:
    combined = RUNBOOK_PATH.read_text(encoding="utf-8") + ADR_PATH.read_text(encoding="utf-8")
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
