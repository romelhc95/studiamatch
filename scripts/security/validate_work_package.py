#!/usr/bin/env python3
"""Validate Sprint 1 work package manifests and changed path scope."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / ".context" / "work_packages"
VALID_STATUS = {"PROPOSED", "APPROVED", "ACTIVE", "COMPLETED", "REVOKED", "EXPIRED"}
REQUIRED = {
    "id",
    "status",
    "hito",
    "risk_level",
    "baseline",
    "environment_scope",
    "allowed_paths",
    "denied_without_jit",
    "dependencies",
    "r3_operations",
    "expires_at",
    "candidate_digest",
    "approval_digest_source",
    "approver_required",
    "invalidated_by",
    "exit_criteria",
}
FORBIDDEN_PROPOSED_KEYS = {"approved_by", "approved_at", "approval_digest", "activated_at", "approval_reference", "approved_level", "approved_candidate_commit", "approval_evidence_sha256"}
APPROVAL_KEYS = {"approval_digest", "approved_by", "approved_at", "approval_reference", "approved_level", "approved_candidate_commit", "approval_evidence_sha256"}
ACTIVE_KEYS = APPROVAL_KEYS | {"activated_at"}
REQUIRED_DENY_TERMS = {"production", "writers", "schedules", "lead_capture", "egress"}
H2_REQUIRED_DENY_TERMS = REQUIRED_DENY_TERMS | {
    "certification",
    "main",
    "supabase-free",
    "supabase-pro",
    "ddl-execution",
    "dml-execution",
    "backfill-execution",
    "rls-grants-remote",
    "workflow_dispatch",
    "deploys",
    "secrets",
}
DIGEST_FIELD = "candidate_digest"
DIGEST_EXCLUDED_FIELDS = {
    DIGEST_FIELD,
    "status",
    "approval_digest",
    "approved_by",
    "approved_at",
    "approval_reference",
    "approved_level",
    "activated_at",
}
H2_DIGEST_SCHEMA = "h2-approval-target-v1"
H2_APPROVED_CANDIDATE_COMMIT = "c8e4596b153c10721ed335369863a07154eb2b43"
H2_ACTIVATION_BASE_COMMIT = "6ad2690239db361bf913fc9f14c22146d11e69a6"
H2_OBSIDIAN_BASE_COMMIT = "56c517140ede7bce6a0580035a456016da8571a5"
GOV_OBS_BASE_COMMIT = "486bf420cb0d8ad250bc7b3cceb21545184b4dd5"
PR424_BASE_COMMIT = "974f9d4bde6d79230afde5c5a86ba7a3894233c6"
GOV_OBS_TARGET_LEVEL = "R2"
H2_SIGNED_FIELDS = {
    "digest_schema",
    "id",
    "task_id",
    "hito",
    "phase_trace",
    "risk_level",
    "baseline",
    "environment_scope",
    "allowed_paths",
    "allowed_actions",
    "denied_operations",
    "denied_without_jit",
    "dependencies",
    "r3_operations",
    "approval_contract",
    "approval_target_lifecycle_stage",
    "approval_target_gate_status",
    "approval_target_level",
    "criteria_contract",
    "source_artifacts",
    "expires_at",
    "supersedes_digest",
    "approval_digest_source",
    "approver_required",
    "invalidated_by",
    "exit_criteria",
}
H2_MUTABLE_FIELDS = {
    "candidate_digest",
    "status",
    "lifecycle_stage",
    "gate_status",
    "implementation_status",
    "criteria_status",
    "acceptance_status",
    "metrics",
    "approval_digest",
    "approved_by",
    "approved_at",
    "approval_reference",
    "approved_level",
    "approved_candidate_commit",
    "approval_evidence_sha256",
    "activated_at",
}
H2_ALLOWED_FIELDS = H2_SIGNED_FIELDS | H2_MUTABLE_FIELDS
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
GOVERNANCE_ALLOWLIST = (
    "AGENTS.md",
    ".context/estado_del_proyecto.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/hitos/hito_002.md",
    ".context/backlog_tareas/req_est_001_sprint_1/_index.md",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md",
    ".context/matrices/matriz_hito_002.md",
    ".context/work_packages/WP-H2-001.json",
    ".context/decisiones/ADR-0027_work_packages_y_convergencia.md",
    ".context/decisiones/ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md",
    ".github/workflows/security-audit.yml",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "scripts/security/run_h2_r1_tests.sh",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "docker-compose.h2-test.yml",
)
ABSOLUTE_DENY = (
    ".env*",
    "**/.env*",
    "*.env",
    "**/*.env",
    "supabase/**",
)
GOVERNANCE_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "workers/**",
)
H2_ACTIVATION_TRANSITION_ALLOWLIST = (
    ".context/estado_del_proyecto.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/hitos/hito_002.md",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md",
    ".context/matrices/matriz_hito_002.md",
    ".context/work_packages/WP-H2-001.json",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
)
H2_ACTIVATION_TRANSITION_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "supabase/**",
    "workers/**",
)
H2_OBSIDIAN_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".context/**",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
H2_OBSIDIAN_TRANSITION_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "supabase/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "workers/**",
    ".github/workflows/**",
)
GOV_OBS_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".context/**",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
GOV_INFRA_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    "docker-compose.h2-test.yml",
    "scripts/security/run_h2_r1_tests.sh",
)
GOV_RELEASE_TRANSITION_ALLOWLIST = tuple(sorted(set(GOV_OBS_TRANSITION_ALLOWLIST + GOV_INFRA_TRANSITION_ALLOWLIST)))
GOV_RELEASE_TRANSITION_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "supabase/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "workers/**",
)
GOV_OBS_TRANSITION_DENY = GOV_RELEASE_TRANSITION_DENY
SOURCE_NAMES = {"Studiamatch_MVP_Requerimientos_v5.docx", "studiamatch_home.html", "studiamatch_resultados.html"}
SOURCE_EXTENSIONS = (".docx", ".pdf", ".zip", ".tar", ".tar.gz", ".html")


def canonical_payload(data: dict[str, Any]) -> bytes:
    if data.get("digest_schema") == H2_DIGEST_SCHEMA:
        payload = {key: data[key] for key in sorted(H2_SIGNED_FIELDS) if key in data}
    else:
        payload = {key: value for key, value in data.items() if key not in DIGEST_EXCLUDED_FIELDS}
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_digest(data: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload(data)).hexdigest()


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not UTC_TS.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def path_is_safe_pattern(pattern: str) -> bool:
    if not pattern or pattern in {"*", "**", "/", "/**"}:
        return False
    if "\\" in pattern or pattern.startswith("/"):
        return False
    parts = pattern.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def pattern_matches(patterns: tuple[str, ...] | list[str], path: str) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def validate_manifest(path: Path, *, now: datetime | None = None, root: Path | None = None) -> list[str]:
    errors: list[str] = []
    root = root or ROOT
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"WP_JSON_INVALID:{path.name}:{exc}"]
    if not isinstance(data, dict):
        return [f"WP_JSON_INVALID:{path.name}:root must be object"]

    missing = REQUIRED - data.keys()
    if missing:
        errors.append(f"WP_REQUIRED_MISSING:{path.name}:{sorted(missing)}")
    status = data.get("status")
    if status not in VALID_STATUS:
        errors.append(f"WP_STATUS_INVALID:{path.name}")
    if data.get("id") != path.stem:
        errors.append(f"WP_ID_MISMATCH:{path.name}")
    if data.get("approver_required") != "human":
        errors.append(f"WP_HUMAN_APPROVER_REQUIRED:{path.name}")
    if data.get("digest_schema") == H2_DIGEST_SCHEMA:
        unknown = set(data) - H2_ALLOWED_FIELDS
        if unknown:
            errors.append(f"WP_UNKNOWN_FIELDS:{path.name}:{sorted(unknown)}")
        missing_signed = H2_SIGNED_FIELDS - set(data)
        if missing_signed:
            errors.append(f"WP_SIGNED_FIELDS_MISSING:{path.name}:{sorted(missing_signed)}")

    for key in ("allowed_paths", "denied_without_jit", "dependencies", "r3_operations", "invalidated_by", "exit_criteria"):
        if not isinstance(data.get(key), list) or not data.get(key):
            errors.append(f"WP_LIST_REQUIRED:{path.name}:{key}")

    digest = data.get(DIGEST_FIELD)
    if not isinstance(digest, str) or not HEX64.match(digest):
        errors.append(f"WP_DIGEST_FORMAT:{path.name}")
    elif digest != compute_digest(data):
        errors.append(f"WP_DIGEST_MISMATCH:{path.name}:expected {compute_digest(data)}")

    baseline = data.get("baseline")
    required_baseline = {"main_commit", "main_tree", "desarrollo_commit", "desarrollo_tree", "certificacion_commit", "certificacion_tree"}
    if not isinstance(baseline, dict) or not required_baseline <= set(baseline):
        errors.append(f"WP_BASELINE_REQUIRED:{path.name}")
    elif any(not isinstance(baseline[key], str) or not HEX40.match(baseline[key]) for key in required_baseline):
        errors.append(f"WP_BASELINE_SHA_FORMAT:{path.name}")
    else:
        for branch in ("main", "desarrollo", "certificacion"):
            commit = baseline[f"{branch}_commit"]
            tree = baseline[f"{branch}_tree"]
            try:
                actual = subprocess.check_output(["git", "rev-parse", f"{commit}^{{tree}}"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
            except subprocess.CalledProcessError:
                continue
            if actual != tree:
                errors.append(f"COMMIT_TREE_MISMATCH:{path.name}:{branch}")

    expires_at = data.get("expires_at")
    if not isinstance(expires_at, str):
        errors.append(f"WP_EXPIRES_REQUIRED:{path.name}")
    else:
        expiry = parse_utc(expires_at)
        if expiry is None and data.get("id") != "WP-H2-001" and re.match(r"^\d{4}-\d{2}-\d{2}$", expires_at):
            expiry = datetime.strptime(expires_at, "%Y-%m-%d").replace(tzinfo=UTC)
        if expiry is None:
            errors.append(f"WP_EXPIRES_FORMAT:{path.name}")
        elif (now or datetime.now(UTC)) >= expiry:
            errors.append(f"WP_EXPIRED:{path.name}")

    allowed = [str(item) for item in data.get("allowed_paths", [])]
    denied = [str(item) for item in data.get("denied_without_jit", [])]
    for pattern in allowed:
        if not path_is_safe_pattern(pattern):
            errors.append(f"UNSAFE_PATH_PATTERN:{path.name}:{pattern}")
    if any(pattern in {"*", "**"} for pattern in allowed):
        errors.append(f"UNBOUNDED_ALLOWLIST:{path.name}")
    unsafe_allowed = (".env", ".env*", "**/.env", "**/.env*", "*.env", "**/*.env", "supabase/**")
    if any(pattern_matches(unsafe_allowed, pattern) for pattern in allowed):
        errors.append(f"ALLOW_DENY_OVERLAP:{path.name}")

    denied_terms = {item.lower() for item in denied}
    if data.get("id") == "WP-H2-001":
        required_denies = H2_REQUIRED_DENY_TERMS
        if data.get("task_id") != "TASK-H2-001" or data.get("hito") != "HITO-002":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("digest_schema") != H2_DIGEST_SCHEMA:
            errors.append(f"WP_DIGEST_SCHEMA_INVALID:{path.name}")
        expected_lifecycle = {"PROPOSED": "AWAITING_DIGEST", "APPROVED": "APPROVED_NOT_ACTIVE", "ACTIVE": "ACTIVE"}.get(status)
        expected_gate = "READY_FOR_DIGEST_APPROVAL" if status == "PROPOSED" else "APPROVED_R1"
        if expected_lifecycle and data.get("lifecycle_stage") != expected_lifecycle:
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:expected {expected_lifecycle}")
        if expected_gate and data.get("gate_status") != expected_gate:
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:gate")
        if data.get("approval_target_lifecycle_stage") != "APPROVED_NOT_ACTIVE":
            errors.append(f"APPROVAL_TARGET_INVALID:{path.name}:lifecycle")
        if data.get("approval_target_gate_status") != "APPROVED_R1":
            errors.append(f"APPROVAL_TARGET_INVALID:{path.name}:gate")
        if data.get("approval_target_level") != "R1":
            errors.append(f"APPROVAL_TARGET_INVALID:{path.name}:level")
        if data.get("criteria_contract") != ["H2-CA2", "H2-CA3"]:
            errors.append(f"CRITERIA_SET_MISMATCH:{path.name}:contract")
        expected_implementation = "BLOCKED_PENDING_OBSIDIAN_MAIN" if status == "ACTIVE" else "PLANNED_NOT_ACTIVE"
        if data.get("implementation_status") != expected_implementation:
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:implementation")
        if data.get("acceptance_status") != "NOT_STARTED":
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:acceptance")
        if data.get("criteria_status") != {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"}:
            errors.append(f"CRITERIA_SET_MISMATCH:{path.name}")
        if data.get("environment_scope") != ["local", "development"]:
            errors.append(f"WP_ENV_SCOPE_INVALID:{path.name}")
        if data.get("supersedes_digest") != "7a62121f8389192f8c0bab3a06b54b554ddd5a1e8fc05822e7429d96a1229066":
            errors.append(f"WP_REJECTED_DIGEST_TRACE_REQUIRED:{path.name}")
    elif data.get("id") == "WP-GOV-OBS-001":
        required_denies = H2_REQUIRED_DENY_TERMS
        if data.get("task_id") != "TASK-GOV-OBS-001" or data.get("hito") != "GOV-OBS":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_OBS_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_OBS_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_OBS_BASE_COMMIT:
            errors.append(f"GOV_OBS_BASELINE_INVALID:{path.name}:candidate_commit")
        if baseline.get("candidate_tree") != "bc521d7b030095fb1ef928923e333cb4721cda94":
            errors.append(f"GOV_OBS_BASELINE_INVALID:{path.name}:candidate_tree")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_OBS_R3_DENY_MISSING:{path.name}")
        if not any("certification" in str(item).lower() for item in data.get("r3_operations", [])) or not any("main" in str(item).lower() for item in data.get("r3_operations", [])):
            errors.append(f"GOV_OBS_R3_OPERATIONS_REQUIRED:{path.name}")
    elif data.get("id") == "WP-GOV-INFRA-001":
        required_denies = H2_REQUIRED_DENY_TERMS
        if data.get("task_id") != "TASK-GOV-INFRA-001" or data.get("hito") != "GOV-INFRA":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_INFRA_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_INFRA_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_INFRA_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_INFRA_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_OBS_BASE_COMMIT:
            errors.append(f"GOV_INFRA_BASELINE_INVALID:{path.name}:candidate_commit")
        if baseline.get("candidate_tree") != "bc521d7b030095fb1ef928923e333cb4721cda94":
            errors.append(f"GOV_INFRA_BASELINE_INVALID:{path.name}:candidate_tree")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_INFRA_R3_DENY_MISSING:{path.name}")
    else:
        required_denies = REQUIRED_DENY_TERMS
    if not required_denies <= denied_terms:
        errors.append(f"WP_DENY_TERMS_MISSING:{path.name}:{sorted(required_denies - denied_terms)}")

    if status == "PROPOSED" and any(key in data for key in FORBIDDEN_PROPOSED_KEYS):
        errors.append(f"WP_PROPOSED_APPROVAL_FIELDS:{path.name}")
    if status in {"APPROVED", "ACTIVE", "COMPLETED"}:
        missing_approval = [key for key in APPROVAL_KEYS if not data.get(key)]
        if missing_approval:
            errors.append(f"APPROVAL_METADATA_REQUIRED:{path.name}:{missing_approval}")
        if data.get("approval_digest") != digest:
            errors.append(f"APPROVAL_DIGEST_MISMATCH:{path.name}")
        if parse_utc(data.get("approved_at")) is None:
            errors.append(f"APPROVAL_TIMESTAMP_INVALID:{path.name}")
        if data.get("id") == "WP-H2-001" and data.get("approved_level") != "R1":
            errors.append(f"APPROVAL_LEVEL_INVALID:{path.name}:first H2 approval must be R1")
        if data.get("id") == "WP-H2-001":
            if not HEX40.match(str(data.get("approved_candidate_commit"))):
                errors.append(f"APPROVAL_CANDIDATE_COMMIT_INVALID:{path.name}")
            elif data.get("approved_candidate_commit") != H2_APPROVED_CANDIDATE_COMMIT:
                errors.append(f"APPROVAL_CANDIDATE_COMMIT_MISMATCH:{path.name}")
            if not HEX64.match(str(data.get("approval_evidence_sha256"))):
                errors.append(f"APPROVAL_EVIDENCE_INVALID:{path.name}")
            if status == "APPROVED" and "activated_at" in data:
                errors.append(f"ACTIVATION_PREMATURE:{path.name}:approved work package must not include activated_at")
    if status == "ACTIVE":
        if not data.get("activated_at") or parse_utc(data.get("activated_at")) is None:
            errors.append(f"ACTIVATION_METADATA_REQUIRED:{path.name}")
        approved_at = parse_utc(data.get("approved_at"))
        activated_at = parse_utc(data.get("activated_at"))
        if approved_at and activated_at and activated_at < approved_at:
            errors.append(f"ACTIVATION_TIMESTAMP_INVALID:{path.name}")

    return errors


def active_work_package_from_state(root: Path = ROOT) -> str:
    try:
        state = (root / ".context" / "estado_del_proyecto.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return "NONE"
    match = re.search(r"^- Work package activo:\s*`([^`]+)`", state, re.MULTILINE)
    return match.group(1) if match else "NONE"


def is_active_r1_manifest(manifest: dict[str, Any], *, active_work_package: str = "NONE") -> bool:
    if active_work_package != "WP-H2-001":
        return False
    if manifest.get("status") != "ACTIVE":
        return False
    if manifest.get("id") != "WP-H2-001":
        return False
    required = {
        "lifecycle_stage": "ACTIVE",
        "gate_status": "APPROVED_R1",
        "approval_target_level": "R1",
        "approved_level": "R1",
    }
    if any(manifest.get(key) != value for key, value in required.items()):
        return False
    if manifest.get("approval_digest") != manifest.get("candidate_digest"):
        return False
    if manifest.get("approved_candidate_commit") != H2_APPROVED_CANDIDATE_COMMIT:
        return False
    if not all(manifest.get(key) for key in APPROVAL_KEYS):
        return False
    if not HEX40.match(str(manifest.get("approved_candidate_commit"))):
        return False
    if not HEX64.match(str(manifest.get("approval_evidence_sha256"))):
        return False
    if parse_utc(manifest.get("approved_at")) is None or parse_utc(manifest.get("activated_at")) is None:
        return False
    if parse_utc(manifest["activated_at"]) < parse_utc(manifest["approved_at"]):
        return False
    expiry = parse_utc(manifest.get("expires_at"))
    if expiry is None or datetime.now(UTC) >= expiry:
        return False
    return compute_digest(manifest) == manifest.get("candidate_digest")


def parse_name_status(raw: bytes) -> list[tuple[str, str]]:
    fields = raw.split(b"\0")
    index = 0
    paths: list[tuple[str, str]] = []
    while index < len(fields) and fields[index]:
        status = fields[index].decode("ascii")
        index += 1
        if status.startswith(("R", "C")):
            paths.append((status, fields[index].decode("utf-8", "surrogateescape")))
            index += 1
        paths.append((status, fields[index].decode("utf-8", "surrogateescape")))
        index += 1
    return paths


def git_status_paths(root: Path = ROOT) -> list[tuple[str, str]]:
    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "-z"], cwd=root)
    fields = [field for field in raw.split(b"\0") if field]
    paths: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        entry = fields[index].decode("utf-8", "surrogateescape")
        status = entry[:2].strip() or "M"
        path = entry[3:]
        if status.startswith(("R", "C")):
            index += 1
            if index < len(fields):
                paths.append((status, fields[index].decode("utf-8", "surrogateescape")))
        paths.append((status, path))
        index += 1
    return paths


def git_changed_paths(base: str, root: Path = ROOT) -> list[tuple[str, str]]:
    status_paths = git_status_paths(root)
    for command in (
        ["git", "diff", "--name-status", "-z", base, "--"],
        ["git", "diff", "--name-status", "-z", base, "HEAD", "--"],
    ):
        try:
            paths = parse_name_status(subprocess.check_output(command, cwd=root, stderr=subprocess.DEVNULL))
            seen = {(status, path) for status, path in paths}
            for item in status_paths:
                if item not in seen:
                    paths.append(item)
            return paths
        except subprocess.CalledProcessError:
            continue
    paths = status_paths
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
        if head != base:
            paths.extend(parse_name_status(subprocess.check_output(["git", "show", "--name-status", "--format=", "-z", "HEAD"], cwd=root, stderr=subprocess.DEVNULL)))
    except subprocess.CalledProcessError:
        pass
    return paths


def resolve_git_ref(ref: str, root: Path = ROOT) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", ref], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ref


def validate_changed_paths(changed: list[tuple[str, str]], manifests: list[dict[str, Any]], *, active_work_package: str = "NONE", activation_transition: bool = False, obsidian_transition: bool = False, gov_obs_transition: bool = False) -> list[str]:
    errors: list[str] = []
    active = [manifest for manifest in manifests if is_active_r1_manifest(manifest, active_work_package=active_work_package)]
    if len(active) > 1:
        errors.append("MULTIPLE_ACTIVE_WORK_PACKAGES")
    if gov_obs_transition:
        allowed = GOV_RELEASE_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif obsidian_transition:
        allowed = H2_OBSIDIAN_TRANSITION_ALLOWLIST
        denied = H2_OBSIDIAN_TRANSITION_DENY
    elif active_work_package == "WP-GOV-OBS-001":
        allowed = GOV_OBS_TRANSITION_ALLOWLIST
        denied = GOV_OBS_TRANSITION_DENY
    elif activation_transition:
        allowed = H2_ACTIVATION_TRANSITION_ALLOWLIST
        denied = H2_ACTIVATION_TRANSITION_DENY
    elif active:
        allowed = tuple(str(item) for item in active[0].get("allowed_paths", []))
        denied = ABSOLUTE_DENY
    else:
        allowed = GOVERNANCE_ALLOWLIST
        denied = GOVERNANCE_DENY
    for status, path in changed:
        name = path.rsplit("/", 1)[-1]
        lower = path.lower()
        if name in SOURCE_NAMES or lower.endswith(SOURCE_EXTENSIONS):
            errors.append(f"SOURCE_ARTIFACT:{status}:{path}")
        if pattern_matches(denied, path):
            errors.append(f"DENIED_PATH:{status}:{path}")
        if not pattern_matches(allowed, path):
            errors.append(f"CHANGED_PATH_NOT_ALLOWED:{status}:{path}")
    return errors


def load_manifests(root: Path = ROOT) -> list[dict[str, Any]]:
    manifests = []
    for manifest_path in sorted((root / ".context" / "work_packages").glob("WP-*-001.json")):
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return manifests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-from", help="Validate changed paths from this git ref to HEAD")
    args = parser.parse_args(argv)
    manifests = sorted(MANIFEST_DIR.glob("WP-*-001.json"))
    errors: list[str] = []
    if len(manifests) != 6:
        errors.append("WP_MANIFEST_COUNT:expected four Sprint 1 manifests plus GOV OBS/INFRA manifests")
    for manifest in manifests:
        errors.extend(validate_manifest(manifest, root=ROOT))
    if args.changed_from:
        changed_from = resolve_git_ref(args.changed_from)
        errors.extend(validate_changed_paths(
            git_changed_paths(args.changed_from),
            load_manifests(),
            active_work_package=active_work_package_from_state(),
            activation_transition=changed_from == H2_ACTIVATION_BASE_COMMIT,
            obsidian_transition=changed_from == H2_OBSIDIAN_BASE_COMMIT,
            gov_obs_transition=changed_from in {GOV_OBS_BASE_COMMIT, PR424_BASE_COMMIT},
        ))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("work package manifests valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
