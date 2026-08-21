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
FORBIDDEN_PROPOSED_KEYS = {"approved_by", "approved_at", "approval_digest", "activated_at", "approval_reference", "approved_level"}
APPROVAL_KEYS = {"approval_digest", "approved_by", "approved_at", "approval_reference", "approved_level"}
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
SOURCE_NAMES = {"Studiamatch_MVP_Requerimientos_v5.docx", "studiamatch_home.html", "studiamatch_resultados.html"}
SOURCE_EXTENSIONS = (".docx", ".pdf", ".zip", ".tar", ".tar.gz", ".html")


def canonical_payload(data: dict[str, Any]) -> bytes:
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
        if data.get("lifecycle_stage") != "AWAITING_DIGEST":
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:expected AWAITING_DIGEST")
        if data.get("gate_status") != "READY_FOR_DIGEST_APPROVAL":
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:gate")
        if data.get("implementation_status") != "PLANNED_NOT_ACTIVE":
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:implementation")
        if data.get("acceptance_status") != "NOT_STARTED":
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:acceptance")
        if data.get("criteria_status") != {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"}:
            errors.append(f"CRITERIA_SET_MISMATCH:{path.name}")
        if data.get("environment_scope") != ["local", "development"]:
            errors.append(f"WP_ENV_SCOPE_INVALID:{path.name}")
        if data.get("supersedes_digest") != "7a62121f8389192f8c0bab3a06b54b554ddd5a1e8fc05822e7429d96a1229066":
            errors.append(f"WP_REJECTED_DIGEST_TRACE_REQUIRED:{path.name}")
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
    if status == "ACTIVE":
        if not data.get("activated_at") or parse_utc(data.get("activated_at")) is None:
            errors.append(f"ACTIVATION_METADATA_REQUIRED:{path.name}")

    return errors


def git_changed_paths(base: str, root: Path = ROOT) -> list[tuple[str, str]]:
    raw = subprocess.check_output(["git", "diff", "--name-status", "-z", base, "HEAD", "--"], cwd=root)
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


def validate_changed_paths(changed: list[tuple[str, str]], manifests: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    active = [manifest for manifest in manifests if manifest.get("status") == "ACTIVE"]
    if active:
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
    for manifest_path in sorted((root / ".context" / "work_packages").glob("WP-H*-001.json")):
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return manifests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-from", help="Validate changed paths from this git ref to HEAD")
    args = parser.parse_args(argv)
    manifests = sorted(MANIFEST_DIR.glob("WP-H*-001.json"))
    errors: list[str] = []
    if len(manifests) != 4:
        errors.append("WP_MANIFEST_COUNT:expected exactly four Sprint 1 manifests")
    for manifest in manifests:
        errors.extend(validate_manifest(manifest, root=ROOT))
    if args.changed_from:
        errors.extend(validate_changed_paths(git_changed_paths(args.changed_from), load_manifests()))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("work package manifests valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
