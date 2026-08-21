#!/usr/bin/env python3
"""Validate Sprint 1 work package manifests."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / ".context" / "work_packages"
VALID_STATUS = {"PROPOSED", "APPROVED", "ACTIVE", "COMPLETED", "REVOKED", "EXPIRED"}
REQUIRED = {"id", "status", "hito", "risk_level", "allowed_paths", "denied_without_jit", "exit_criteria"}
FORBIDDEN_PROPOSED_KEYS = {"approved_by", "approved_at", "approval_digest", "activated_at"}
REQUIRED_DENY_TERMS = {"production", "writers"}


def validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED - data.keys()
    if missing:
        errors.append(f"{path.name}: missing {sorted(missing)}")
    if data.get("status") not in VALID_STATUS:
        errors.append(f"{path.name}: invalid status")
    for key in ("allowed_paths", "denied_without_jit", "exit_criteria"):
        if not isinstance(data.get(key), list) or not data.get(key):
            errors.append(f"{path.name}: {key} must be a non-empty list")
    if data.get("id") != path.stem:
        errors.append(f"{path.name}: id must match file name")
    if data.get("status") == "PROPOSED" and any(key in data for key in FORBIDDEN_PROPOSED_KEYS):
        errors.append(f"{path.name}: proposed manifests cannot carry approval or activation fields")
    if data.get("status") in {"APPROVED", "ACTIVE"} and "approval_digest" not in data:
        errors.append(f"{path.name}: approved or active manifests require approval_digest")
    denied = {str(item).lower() for item in data.get("denied_without_jit", [])}
    if not REQUIRED_DENY_TERMS <= denied:
        errors.append(f"{path.name}: denied_without_jit must include production and writers")
    allowed = [str(item) for item in data.get("allowed_paths", [])]
    if "**" in allowed or "*" in allowed:
        errors.append(f"{path.name}: unbounded wildcard is not allowed")
    return errors


def main() -> int:
    manifests = sorted(MANIFEST_DIR.glob("WP-H*-001.json"))
    errors: list[str] = []
    if len(manifests) != 4:
        errors.append("expected exactly four Sprint 1 manifests")
    for manifest in manifests:
        errors.extend(validate_manifest(manifest))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("work package manifests valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
