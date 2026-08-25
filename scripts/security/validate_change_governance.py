#!/usr/bin/env python3
"""Validate PR governance attestation and architecture co-change policy."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.security.attestation_parser import parse_attestation_section
except ModuleNotFoundError:
    from attestation_parser import parse_attestation_section


ROOT = Path(__file__).resolve().parents[2]
LEVELS = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R3+": 4}
REQUIRED_FIELDS = (
    "Base-SHA",
    "Candidate-SHA",
    "Estado-Snapshot",
    "Requerimiento",
    "Hito",
    "TASK",
    "WP",
    "WP-Digest",
    "Approval-Level",
    "Approval-Expiry",
    "Architecture-Snapshot",
    "Data-Architecture-Snapshot",
    "Adoption-Matrix-Snapshot",
    "Architecture-Impact",
    "Architecture-Impact-Reason",
    "Data-Impact",
    "Data-Impact-Reason",
    "Security-Auditor",
)
PROMOTION_FIELDS = ("Operation", "Grant-ID", "Base-Ref", "Base-SHA", "Source-Ref", "Source-SHA", "Candidate-SHA", "Candidate-Tree", "Final-WP", "D_FINAL", "T_FINAL", "Approval-Level", "Approval-Reference", "Approval-Expiry")
BRANCH_PATTERNS = ("feat/", "fix/", "docs/", "governance/", "chore/")
PLACEHOLDER_VALUES = {"", "todo", "tbd", "n/a", "na", "none", "null", "<todo>", "<commit>", "<digest>"}
UTC_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def parse_attestation(body: str) -> dict[str, str]:
    return parse_attestation_section(body, "Governance Attestation", REQUIRED_FIELDS).fields


def is_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES or value.strip().startswith("<")


def promotion_section_populated(body: str) -> bool:
    section = parse_attestation_section(body, "Promotion Attestation", PROMOTION_FIELDS)
    return any(not is_placeholder(value) and value.strip().lower() != "nuevo-unico-no-consumido" for value in section.nonempty_fields().values())


def load_manifest(wp_id: str, root: Path = ROOT) -> dict[str, Any] | None:
    path = root / ".context" / "work_packages" / f"{wp_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def parse_expiry(value: str) -> datetime | None:
    if not UTC_TS.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def changed_paths(base: str, head: str, root: Path = ROOT) -> list[str]:
    raw = subprocess.check_output(["git", "diff", "--name-only", base, head, "--"], cwd=root, text=True, stderr=subprocess.DEVNULL)
    return [line.strip() for line in raw.splitlines() if line.strip()]


def git_is_ancestor(base: str, head: str, root: Path = ROOT) -> bool | None:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def git_sha(args: list[str], root: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


def path_requires_architecture(path: str) -> bool:
    return (
        path == "Dockerfile"
        or path.startswith("web/")
        or path.startswith("scripts/core/")
        or path.startswith("scripts/shared/")
        or path.startswith(".github/workflows/")
        or re.match(r"^docker-compose.*\.ya?ml$", path) is not None
    )


def path_requires_data_docs(path: str) -> bool:
    return path.startswith("db/") or path.startswith("supabase/")


def path_requires_matrix(path: str) -> bool:
    return path.startswith("db/") or path.startswith("supabase/") or path.startswith(".github/workflows/")


def validate(
    *,
    body: str,
    base_ref: str,
    head_ref: str,
    base_sha: str,
    base_for_diff: str,
    pr_head_sha: str = "",
    root: Path = ROOT,
    now: datetime | None = None,
    event_path: str = "",
) -> list[str]:
    errors: list[str] = []
    section = parse_attestation_section(body, "Governance Attestation", REQUIRED_FIELDS)
    fields = section.fields
    now = now or datetime.now(UTC)

    if not section.present:
        errors.append("GOVERNANCE_ATTESTATION_SECTION_MISSING")
    if section.duplicate_section:
        errors.append("GOVERNANCE_ATTESTATION_SECTION_DUPLICATE")
    for duplicate in section.duplicates:
        errors.append(f"GOVERNANCE_ATTESTATION_DUPLICATE:{duplicate}")
    if promotion_section_populated(body):
        errors.append("GOVERNANCE_PROMOTION_SECTION_POPULATED")

    for field in REQUIRED_FIELDS:
        value = fields.get(field, "")
        if field in {"Architecture-Impact", "Data-Impact"}:
            if value not in {"updated", "none"}:
                errors.append(f"GOVERNANCE_PREFLIGHT_FIELD_REQUIRED:{field}")
            continue
        if is_placeholder(value):
            errors.append(f"GOVERNANCE_PREFLIGHT_FIELD_REQUIRED:{field}")

    if "Ejecuta las tareas pendientes de la Fase" in body:
        errors.append("GOVERNANCE_LEGACY_PHASE_AUTHORIZATION")

    if base_ref != "desarrollo":
        errors.append(f"GOVERNANCE_BASE_REF_INVALID:{base_ref}")
    if not any(head_ref.startswith(prefix) for prefix in BRANCH_PATTERNS):
        errors.append(f"GOVERNANCE_BRANCH_INVALID:{head_ref}")

    wp_id = fields.get("WP", "")
    manifest = load_manifest(wp_id, root=root)
    if manifest is None:
        errors.append(f"GOVERNANCE_WP_NOT_FOUND:{wp_id}")
    else:
        if manifest.get("task_id") != fields.get("TASK"):
            errors.append("GOVERNANCE_TASK_WP_MISMATCH")
        digest = fields.get("WP-Digest", "")
        if not HEX64.match(digest) or digest != manifest.get("candidate_digest"):
            errors.append("GOVERNANCE_WP_DIGEST_MISMATCH")
        requested_level = fields.get("Approval-Level", "")
        target_level = str(manifest.get("target_level") or manifest.get("approval_target_level") or "R0")
        if requested_level != target_level:
            errors.append("GOVERNANCE_APPROVAL_LEVEL_MISMATCH")
        if LEVELS.get(requested_level, 99) > LEVELS.get(target_level, -1):
            errors.append("GOVERNANCE_APPROVAL_LEVEL_EXCEEDS_TARGET")

    expiry = parse_expiry(fields.get("Approval-Expiry", ""))
    if expiry is None:
        errors.append("GOVERNANCE_APPROVAL_EXPIRY_INVALID")
    elif now >= expiry:
        errors.append("GOVERNANCE_APPROVAL_EXPIRED")

    if not HEX40.match(base_sha):
        errors.append("GOVERNANCE_BASE_SHA_INVALID")
    if not HEX40.match(pr_head_sha):
        errors.append("GOVERNANCE_HEAD_SHA_INVALID")
    if base_for_diff != base_sha:
        errors.append("GOVERNANCE_DIFF_BASE_MISMATCH")

    if not HEX40.match(fields.get("Base-SHA", "")) or fields.get("Base-SHA") != base_sha:
        errors.append("GOVERNANCE_BASE_SHA_MISMATCH")
    candidate_sha = fields.get("Candidate-SHA", "")
    if not HEX40.match(candidate_sha):
        errors.append("GOVERNANCE_CANDIDATE_SHA_INVALID")
    elif candidate_sha != pr_head_sha:
        errors.append("GOVERNANCE_CANDIDATE_SHA_MISMATCH")

    if fields.get("Architecture-Impact") not in {"updated", "none"}:
        errors.append("GOVERNANCE_ARCHITECTURE_IMPACT_INVALID")
    if fields.get("Data-Impact") not in {"updated", "none"}:
        errors.append("GOVERNANCE_DATA_IMPACT_INVALID")
    paths = changed_paths(base_sha, pr_head_sha, root=root) if HEX40.match(base_sha) and HEX40.match(pr_head_sha) else []
    changed = set(paths)
    needs_arch = any(path_requires_architecture(path) for path in paths)
    needs_data = any(path_requires_data_docs(path) for path in paths)
    needs_matrix = any(path_requires_matrix(path) for path in paths)
    arch_doc_changed = ".context/arquitectura_pipeline.md" in changed
    db_doc_changed = ".context/sistema_db_supabase.md" in changed
    matrix_changed = ".context/operaciones/matriz_adopcion_db.md" in changed

    if needs_arch and not arch_doc_changed:
        errors.append("GOVERNANCE_ARCHITECTURE_COCHANGE_REQUIRED")
    if needs_data and not db_doc_changed:
        errors.append("GOVERNANCE_DATA_COCHANGE_REQUIRED")
    if needs_matrix and not matrix_changed:
        errors.append("GOVERNANCE_ADOPTION_MATRIX_COCHANGE_REQUIRED")

    head_sha = git_sha(["rev-parse", "HEAD"], root=root)
    if HEX40.match(pr_head_sha) and head_sha != pr_head_sha:
        errors.append("GOVERNANCE_HEAD_SHA_MISMATCH")
    ancestry = git_is_ancestor(base_sha, pr_head_sha, root=root) if HEX40.match(base_sha) and HEX40.match(pr_head_sha) else None
    if ancestry is False:
        errors.append("GOVERNANCE_BRANCH_NOT_BASED_ON_DECLARED_BASE")
    elif ancestry is None:
        errors.append("GOVERNANCE_GIT_VALIDATION_FAILED")
    if fields.get("Security-Auditor") not in {"clean", "findings-remediated"}:
        errors.append("GOVERNANCE_SECURITY_AUDITOR_INVALID")
    if fields.get("Approval-Level") in {"R3", "R3+"}:
        errors.append("GOVERNANCE_R3_JIT_NOT_SUPPORTED_BY_PREFLIGHT")
    print(f"governance-preflight base_ref={base_ref} head_ref={head_ref} base_sha={base_sha} head_sha={head_sha} pr_head_sha={pr_head_sha} wp={wp_id}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH", ""))
    parser.add_argument("--base-ref", default=os.getenv("GITHUB_BASE_REF", ""))
    parser.add_argument("--head-ref", default=os.getenv("GITHUB_HEAD_REF", ""))
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha", default="")
    parser.add_argument("--changed-from")
    parser.add_argument("--body-file")
    args = parser.parse_args(argv)

    body = ""
    base_sha = args.base_sha or ""
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    elif args.event_path:
        event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
        pull_request = event.get("pull_request") or {}
        body = pull_request.get("body") or ""
        base_sha = base_sha or (pull_request.get("base") or {}).get("sha", "")

    if not args.base_ref:
        print("governance-preflight skipped: not a pull_request event")
        return 0

    base_for_diff = args.changed_from or base_sha
    errors = validate(
        body=body,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        base_sha=base_sha,
        pr_head_sha=args.head_sha,
        base_for_diff=base_for_diff,
        event_path=args.event_path,
    )
    if errors:
        for error in errors:
            print(error)
        return 1
    print("governance preflight valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
