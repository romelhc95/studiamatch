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
GOV_ARCH_BASE_COMMIT = "96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9"
GOV_HOM_BASE_COMMIT = "4cce43a743de5860c4da86eecf1782efab91d26b"
GOV_CI_BASE_COMMIT = "fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1"
GOV_CI2_BASE_COMMIT = "b878c5764e55cb2646b60c4777e363489fe48e8b"
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
    "README.md",
    ".context/00_INDICE.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
    ".context/work_packages/WP-GOV-ARCH-001.json",
    "docs/architecture/Documento_Detallado_workflow.md",
    "docs/architecture/core_data_flow.md",
    "docs/orquestador-sdlc/PRODUCTION_ARCHITECTURE.md",
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
GOV_ARCH_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    "README.md",
    ".github/pull_request_template.md",
    ".github/workflows/security-audit.yml",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
    ".context/work_packages/WP-GOV-ARCH-001.json",
    "docs/architecture/Documento_Detallado_workflow.md",
    "docs/architecture/core_data_flow.md",
    "docs/orquestador-sdlc/PRODUCTION_ARCHITECTURE.md",
    "scripts/security/validate_change_governance.py",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_change_governance.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
GOV_HOM_TRANSITION_ALLOWLIST = (
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md",
    ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
    ".context/backlog_tareas/governance/TASK-GOV-HOM-001.md",
    ".context/work_packages/WP-GOV-HOM-001.json",
    ".context/decisiones/ADR-0029_homologacion_no_recursiva.md",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
GOV_CI_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    ".github/pull_request_template.md",
    "scripts/security/validate_change_governance.py",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-001.md",
    ".context/work_packages/WP-GOV-CI-001.json",
    ".context/decisiones/ADR-0030_separacion_ci_y_review_gate.md",
)
GOV_CI2_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    ".github/pull_request_template.md",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-002.md",
    ".context/work_packages/WP-GOV-CI-002.json",
    ".context/decisiones/ADR-0031_boundary_homologacion_estructural.md",
)
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
PROMOTION_PAIRS = {
    "O2 desarrollo -> certificacion": ("certificacion", "desarrollo"),
    "O3 certificacion -> main": ("main", "certificacion"),
    "O4 main -> certificacion": ("certificacion", "main"),
    "O5 certificacion -> desarrollo": ("desarrollo", "certificacion"),
}
PROMOTION_FIELDS = ("Operation", "Grant-ID", "Base-SHA", "Candidate-SHA", "Final-WP", "D_FINAL", "T_FINAL", "Approval-Level", "Approval-Reference", "Approval-Expiry")
PROMOTION_FINAL_WP = "WP-GOV-CI-002"
PROMOTION_ALLOWED_ACTION = "opened"
PROMOTION_BLOCKED_PR_NUMBERS = {428}
PROMOTION_CONSUMED_GRANTS = {"R3-GOV-HOM-001-O2"}
PROMOTION_GRANT_ID_PATTERN = re.compile(r"^R3-GOV-HOM-\d{3}-O[2-5]-[A-Za-z0-9][A-Za-z0-9_.-]{3,}$")


def canonical_payload(data: dict[str, Any]) -> bytes:
    if data.get("digest_schema") == H2_DIGEST_SCHEMA:
        payload = {key: data[key] for key in sorted(H2_SIGNED_FIELDS) if key in data}
    else:
        payload = {key: value for key, value in data.items() if key not in DIGEST_EXCLUDED_FIELDS}
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_digest(data: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload(data)).hexdigest()


def parse_attestation_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in body.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in PROMOTION_FIELDS:
            fields[key] = value.strip()
    return fields


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
    elif data.get("id") == "WP-GOV-ARCH-001":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-ARCH-001" or data.get("hito") != "GOV-ARCH":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_ARCH_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_ARCH_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_ARCH_BASE_COMMIT:
            errors.append(f"GOV_ARCH_BASELINE_INVALID:{path.name}:candidate_commit")
        if baseline.get("candidate_tree") != "530b0a95dda9f81f408ebcb8c177a1ed73afe3e3":
            errors.append(f"GOV_ARCH_BASELINE_INVALID:{path.name}:candidate_tree")
        required_paths = {
            ".context/arquitectura_pipeline.md",
            ".context/sistema_db_supabase.md",
            ".context/operaciones/matriz_adopcion_db.md",
            ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
            ".context/work_packages/WP-GOV-ARCH-001.json",
        }
        if data.get("allowed_paths") != list(GOV_ARCH_TRANSITION_ALLOWLIST) or not required_paths <= set(data.get("allowed_paths", [])):
            errors.append(f"GOV_ARCH_ALLOWLIST_INVALID:{path.name}")
        control_paths = {".github/workflows/security-audit.yml", "scripts/security/validate_change_governance.py", "scripts/security/validate_context_graph.py", "scripts/security/validate_work_package.py"}
        if control_paths & set(data.get("allowed_paths", [])) and not data.get("governance_controls_scope"):
            errors.append(f"GOV_ARCH_CONTROLS_SCOPE_REQUIRED:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_ARCH_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-HOM-001":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-HOM-001" or data.get("hito") != "GOV-HOM":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_HOM_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_HOM_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_HOM_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_HOM_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_HOM_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_HOM_BASE_COMMIT:
            errors.append(f"GOV_HOM_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "ac16b545b74a03b149aac538062def20101187fb" or baseline.get("desarrollo_tree") != "ac16b545b74a03b149aac538062def20101187fb":
            errors.append(f"GOV_HOM_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        grants = data.get("homologation_grants")
        if not isinstance(grants, list) or len(grants) != 4:
            errors.append(f"GOV_HOM_GRANTS_INVALID:{path.name}:expected four separate templates")
        else:
            expected_ids = {"R3-GOV-HOM-001-O2", "R3-GOV-HOM-001-O3", "R3-GOV-HOM-001-O4", "R3-GOV-HOM-001-O5"}
            actual_ids = {str(grant.get("id")) for grant in grants if isinstance(grant, dict)}
            if actual_ids != expected_ids or any(grant.get("single_use") is not True for grant in grants if isinstance(grant, dict)):
                errors.append(f"GOV_HOM_GRANTS_INVALID:{path.name}:ids/single_use")
            if any(str(grant.get("status")) != "TEMPLATE_ONLY_NOT_GRANTED" for grant in grants if isinstance(grant, dict)):
                errors.append(f"GOV_HOM_GRANTS_INVALID:{path.name}:must not grant R3")
        predicate = data.get("closure_predicate")
        if not isinstance(predicate, list) or not any("tree(main) == tree(certificacion) == tree(desarrollo) == T_HOM" in str(item) for item in predicate):
            errors.append(f"GOV_HOM_CLOSURE_PREDICATE_REQUIRED:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_HOM_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-001":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-001" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI_BASE_COMMIT:
            errors.append(f"GOV_CI_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "5e7d087ac45457264ea29dfc1aa7373efd909290" or baseline.get("desarrollo_tree") != "5e7d087ac45457264ea29dfc1aa7373efd909290":
            errors.append(f"GOV_CI_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        decoupling = data.get("ci_review_decoupling")
        if not isinstance(decoupling, dict) or decoupling.get("reviews_trigger_ci") is not False or decoupling.get("reviews_api_used") is not False or decoupling.get("manual_rerun_required_for_review") is not False:
            errors.append(f"GOV_CI_DECOUPLING_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-002":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-002" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI2_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI2_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI2_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI2_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI2_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI2_BASE_COMMIT:
            errors.append(f"GOV_CI2_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "174c18efd840fff6ce27fce9fe1dc4edcd65abe8" or baseline.get("desarrollo_tree") != "174c18efd840fff6ce27fce9fe1dc4edcd65abe8":
            errors.append(f"GOV_CI2_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        promotion = data.get("promotion_boundary")
        if not isinstance(promotion, dict) or promotion.get("structural_pairs") != sorted(PROMOTION_PAIRS) or promotion.get("incremental_boundary_preserved") is not True:
            errors.append(f"GOV_CI2_PROMOTION_BOUNDARY_INVALID:{path.name}")
        elif promotion.get("blocked_pr_numbers") != sorted(PROMOTION_BLOCKED_PR_NUMBERS) or promotion.get("consumed_grants_blocked") != sorted(PROMOTION_CONSUMED_GRANTS) or promotion.get("accepted_event_action") != PROMOTION_ALLOWED_ACTION or promotion.get("accepted_run_attempt") != 1:
            errors.append(f"GOV_CI2_PROMOTION_REPLAY_GUARDS_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI2_R3_DENY_MISSING:{path.name}")
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


def git_sha(args: list[str], root: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


def git_is_ancestor(base: str, head: str, root: Path = ROOT) -> bool | None:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def load_manifest_by_id(wp_id: str, root: Path = ROOT) -> dict[str, Any] | None:
    path = root / ".context" / "work_packages" / f"{wp_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_promotion_grant(grant_id: str, root: Path = ROOT) -> dict[str, Any] | None:
    path = root / ".context" / "r3_grants" / f"{grant_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def validate_promotion_event(event_path: str, *, event_name: str = "", run_attempt: str = "", now: datetime | None = None, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    now = now or datetime.now(UTC)
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["PROMOTION_EVENT_INVALID"]

    pr = event.get("pull_request") or {}
    if event_name and event_name != "pull_request":
        errors.append("PROMOTION_EVENT_INVALID")
    if not pr:
        errors.append("PROMOTION_EVENT_INVALID")
        return errors
    if event.get("action") != PROMOTION_ALLOWED_ACTION:
        errors.append("PROMOTION_ACTION_INVALID")
    try:
        attempt = int(run_attempt)
    except (TypeError, ValueError):
        attempt = 0
    if attempt != 1:
        errors.append("PROMOTION_RUN_ATTEMPT_INVALID")
    try:
        pr_number = int(pr.get("number") or event.get("number") or 0)
    except (TypeError, ValueError):
        pr_number = 0
    if pr_number in PROMOTION_BLOCKED_PR_NUMBERS:
        errors.append("PROMOTION_PR_BLOCKED:428")

    fields = parse_attestation_fields(pr.get("body") or "")
    operation = fields.get("Operation", "")
    expected_pair = PROMOTION_PAIRS.get(operation)
    if expected_pair is None:
        errors.append("PROMOTION_OPERATION_MISMATCH")

    base = pr.get("base") or {}
    head = pr.get("head") or {}
    repo = event.get("repository") or {}
    base_repo = base.get("repo") or {}
    head_repo = head.get("repo") or {}
    repo_name = str(repo.get("full_name") or "")
    if not repo_name or str(base_repo.get("full_name") or "") != repo_name or str(head_repo.get("full_name") or "") != repo_name:
        errors.append("PROMOTION_REPOSITORY_INVALID")
    base_ref = str(base.get("ref") or "")
    head_ref = str(head.get("ref") or "")
    base_sha = str(base.get("sha") or "")
    head_sha = str(head.get("sha") or "")
    if expected_pair and (base_ref, head_ref) != expected_pair:
        errors.append("PROMOTION_PAIR_INVALID")
    grant_id = fields.get("Grant-ID", "")
    operation_code = operation.split(" ", 1)[0] if operation else ""
    if not PROMOTION_GRANT_ID_PATTERN.match(grant_id):
        errors.append("PROMOTION_GRANT_ID_INVALID")
    if grant_id in PROMOTION_CONSUMED_GRANTS:
        errors.append("PROMOTION_GRANT_CONSUMED")
    if not grant_id or not operation_code or f"-{operation_code}-" not in grant_id:
        errors.append("PROMOTION_GRANT_ID_MISMATCH")
    grant = load_promotion_grant(grant_id, root=root) if grant_id else None
    if grant is None:
        errors.append("PROMOTION_GRANT_NOT_FOUND")

    attested_base = fields.get("Base-SHA", "")
    if not HEX40.match(base_sha) or not HEX40.match(attested_base):
        errors.append("PROMOTION_BASE_SHA_INVALID")
    elif base_sha != attested_base:
        errors.append("PROMOTION_BASE_SHA_MISMATCH")

    attested_head = fields.get("Candidate-SHA", "")
    if not HEX40.match(head_sha) or not HEX40.match(attested_head):
        errors.append("PROMOTION_CANDIDATE_SHA_INVALID")
    elif head_sha != attested_head:
        errors.append("PROMOTION_CANDIDATE_SHA_MISMATCH")

    final_wp_id = fields.get("Final-WP", "")
    if final_wp_id != PROMOTION_FINAL_WP:
        errors.append("PROMOTION_FINAL_WP_INVALID")
    final_wp = load_manifest_by_id(final_wp_id, root=root)
    if final_wp is None:
        errors.append("PROMOTION_FINAL_WP_NOT_FOUND")

    d_final = fields.get("D_FINAL", "")
    if not HEX64.match(d_final):
        errors.append("PROMOTION_FINAL_DIGEST_INVALID")
    elif final_wp is not None and (final_wp.get("candidate_digest") != d_final or compute_digest(final_wp) != d_final):
        errors.append("PROMOTION_FINAL_DIGEST_MISMATCH")

    t_final = fields.get("T_FINAL", "")
    if not HEX40.match(t_final):
        errors.append("PROMOTION_FINAL_TREE_INVALID")
    elif HEX40.match(head_sha):
        try:
            if git_sha(["rev-parse", f"{head_sha}^{{tree}}"], root=root) != t_final:
                errors.append("PROMOTION_FINAL_TREE_MISMATCH")
        except subprocess.CalledProcessError:
            errors.append("PROMOTION_FINAL_TREE_MISMATCH")

    if HEX40.match(base_sha) and HEX40.match(head_sha) and git_is_ancestor(base_sha, head_sha, root=root) is not True:
        errors.append("PROMOTION_ANCESTRY_INVALID")

    if HEX40.match(head_sha):
        try:
            if git_sha(["rev-parse", "HEAD^{tree}"], root=root) != git_sha(["rev-parse", f"{head_sha}^{{tree}}"], root=root):
                errors.append("PROMOTION_SYNTHETIC_TREE_MISMATCH")
        except subprocess.CalledProcessError:
            errors.append("PROMOTION_SYNTHETIC_TREE_MISMATCH")

    if fields.get("Approval-Level") != "R3 JIT single-use":
        errors.append("PROMOTION_OPERATION_MISMATCH")
    approval_ref = fields.get("Approval-Reference", "")
    if not approval_ref or approval_ref in {"TODO", "N/A", "none", "<approval-reference>"}:
        errors.append("PROMOTION_APPROVAL_REFERENCE_REQUIRED")
    expiry = parse_utc(fields.get("Approval-Expiry", ""))
    if expiry is None or now >= expiry:
        errors.append("PROMOTION_APPROVAL_EXPIRED")

    if grant is not None:
        expected_grant = {
            "id": grant_id,
            "status": "APPROVED_JIT_SINGLE_USE",
            "operation": operation,
            "repository": repo_name,
            "base_ref": base_ref,
            "head_ref": head_ref,
            "base_sha": base_sha,
            "candidate_sha": head_sha,
            "final_wp": final_wp_id,
            "d_final": d_final,
            "t_final": t_final,
            "approval_level": "R3 JIT single-use",
            "approval_reference": approval_ref,
            "approval_expiry": fields.get("Approval-Expiry", ""),
            "event_action": PROMOTION_ALLOWED_ACTION,
            "run_attempt": 1,
            "consumed": False,
        }
        for key, expected_value in expected_grant.items():
            if grant.get(key) != expected_value:
                errors.append(f"PROMOTION_GRANT_MISMATCH:{key}")
        if grant.get("single_use") is not True:
            errors.append("PROMOTION_GRANT_MISMATCH:single_use")

    return errors


def resolve_git_ref(ref: str, root: Path = ROOT) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", ref], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        for known_ref in (H2_ACTIVATION_BASE_COMMIT, H2_OBSIDIAN_BASE_COMMIT, GOV_OBS_BASE_COMMIT, PR424_BASE_COMMIT, GOV_ARCH_BASE_COMMIT, GOV_HOM_BASE_COMMIT, GOV_CI_BASE_COMMIT, GOV_CI2_BASE_COMMIT):
            if known_ref.startswith(ref):
                return known_ref
        return ref


def validate_changed_paths(changed: list[tuple[str, str]], manifests: list[dict[str, Any]], *, active_work_package: str = "NONE", activation_transition: bool = False, obsidian_transition: bool = False, gov_obs_transition: bool = False, gov_arch_transition: bool = False, gov_hom_transition: bool = False, gov_ci_transition: bool = False, gov_ci2_transition: bool = False) -> list[str]:
    errors: list[str] = []
    active = [manifest for manifest in manifests if is_active_r1_manifest(manifest, active_work_package=active_work_package)]
    if len(active) > 1:
        errors.append("MULTIPLE_ACTIVE_WORK_PACKAGES")
    if gov_ci2_transition:
        allowed = GOV_CI2_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci_transition:
        allowed = GOV_CI_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_obs_transition:
        allowed = GOV_RELEASE_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_hom_transition:
        allowed = GOV_HOM_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_arch_transition:
        allowed = GOV_ARCH_TRANSITION_ALLOWLIST
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
    for manifest_path in sorted((root / ".context" / "work_packages").glob("WP-*.json")):
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return manifests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-from", help="Validate changed paths from this git ref to HEAD")
    parser.add_argument("--promotion-event", help="Validate a protected branch promotion event")
    parser.add_argument("--event-name", default="")
    parser.add_argument("--run-attempt", default="", help="GitHub Actions run attempt for promotion replay protection")
    args = parser.parse_args(argv)
    manifests = sorted(MANIFEST_DIR.glob("WP-*.json"))
    errors: list[str] = []
    if len(manifests) != 10:
        errors.append("WP_MANIFEST_COUNT:expected four Sprint 1 manifests plus GOV OBS/INFRA/ARCH/HOM/CI/CI2 manifests")
    for manifest in manifests:
        errors.extend(validate_manifest(manifest, root=ROOT))
    if args.promotion_event:
        errors.extend(validate_promotion_event(args.promotion_event, event_name=args.event_name, run_attempt=args.run_attempt, root=ROOT))
    elif args.changed_from:
        changed_from = resolve_git_ref(args.changed_from)
        errors.extend(validate_changed_paths(
            git_changed_paths(args.changed_from),
            load_manifests(),
            active_work_package=active_work_package_from_state(),
            activation_transition=changed_from == H2_ACTIVATION_BASE_COMMIT,
            obsidian_transition=changed_from == H2_OBSIDIAN_BASE_COMMIT,
            gov_obs_transition=changed_from in {GOV_OBS_BASE_COMMIT, PR424_BASE_COMMIT},
            gov_arch_transition=changed_from == GOV_ARCH_BASE_COMMIT,
            gov_hom_transition=changed_from == GOV_HOM_BASE_COMMIT,
            gov_ci_transition=changed_from == GOV_CI_BASE_COMMIT,
            gov_ci2_transition=changed_from == GOV_CI2_BASE_COMMIT,
        ))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("work package manifests valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
