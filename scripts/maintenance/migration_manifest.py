#!/usr/bin/env python3
"""Validate and resolve closed migration manifests."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_ROOT = ROOT / "db" / "migrations"
ALLOWED_TARGETS = {"free", "pro"}
ALLOWED_PROVENANCE = {"new_forward_only"}
ALLOWED_STATUSES = {
    "reconciled_not_certified",
    "ready_for_free",
    "free_certified",
}
F6_STEM_PREFIX = "20260724_fase06_"
FORBIDDEN_DML_RE = re.compile(
    r"(?im)^\s*(insert\s+into|update\s+[^\s]+\s+set|delete\s+from|"
    r"merge\s+into|truncate(?:\s+table)?|copy\s+|call\s+)"
)
FORBIDDEN_STATEMENT_RE = re.compile(
    r"(?is)^\s*(insert\s+into|update\s+[^\s]+\s+set|delete\s+from|"
    r"merge\s+into|truncate(?:\s+table)?|copy\s+|call\s+|with\b|perform\b|"
    r"select\b|explain\b)"
)
DOLLAR_BLOCK_RE = re.compile(
    r"(?P<tag>\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$)(?P<body>.*?)(?P=tag)",
    re.DOTALL,
)


class ManifestError(RuntimeError):
    """Raised when a migration package is not safe to execute."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _without_comments_and_strings(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return re.sub(r"'(?:''|[^'])*'", "''", sql)


def validate_promotable_sql(sql: str, *, label: str = "migration") -> None:
    """Reject DML that executes while a migration is installed.

    Function bodies are definitions and may contain runtime DML. Anonymous DO
    blocks execute during installation, so their direct and dynamic SQL is
    inspected.
    """

    cursor = 0
    top_level_parts: list[str] = []
    for match in DOLLAR_BLOCK_RE.finditer(sql):
        prefix = sql[cursor : match.start()]
        top_level_parts.append(prefix)
        statement_prefix = prefix.rsplit(";", 1)[-1]
        normalized_prefix = _without_comments_and_strings(statement_prefix).lower()
        body = match.group("body")

        if re.search(r"\bdo\s*$", normalized_prefix):
            raise ManifestError(f"{label}: DO blocks are forbidden")

        top_level_parts.append(" ")
        cursor = match.end()

    top_level_parts.append(sql[cursor:])
    top_level = _without_comments_and_strings("".join(top_level_parts))
    for statement in top_level.split(";"):
        if FORBIDDEN_STATEMENT_RE.match(statement):
            raise ManifestError(f"{label}: top-level migration DML is forbidden")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read migration manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("migration manifest must be a JSON object")
    return data


def load_manifest(
    manifest_path: str | Path,
    target: str,
    *,
    root: Path = ROOT,
    required_status: str | None = None,
) -> list[Path]:
    """Return checksum-verified migration paths for one target."""

    target = target.lower()
    if target not in ALLOWED_TARGETS:
        raise ManifestError(f"unsupported migration target: {target}")

    manifest = _read_json(Path(manifest_path))
    if manifest.get("schema_version") != 1 or manifest.get("phase") != "FASE-06":
        raise ManifestError("unsupported migration manifest contract")
    if manifest.get("package_id") != "F6-DB-AS-CODE-20260724":
        raise ManifestError("unexpected FASE-06 package ID")
    status = manifest.get("status")
    if status not in ALLOWED_STATUSES:
        raise ManifestError("unsupported migration package status")
    if required_status is not None and status != required_status:
        raise ManifestError(
            f"migration package status is {status}; required {required_status}"
        )
    if manifest.get("excluded") != {
        "H-00": "historical_free_only",
        "canary": "observed_effective_unledgered",
        "historical_snapshots": "superseded",
    }:
        raise ManifestError("FASE-06 exclusions are incomplete")
    prerequisites = manifest.get("prerequisites")
    if not isinstance(prerequisites, list) or set(prerequisites) != {
        "g1b_frontend_compatible",
        "editorial_backfill_certified",
        "free_postconditions_certified",
    }:
        raise ManifestError("FASE-06 prerequisites are incomplete")

    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ManifestError("migration manifest entries must be non-empty")

    migration_root = (root / "db" / "migrations").resolve()
    resolved: list[Path] = []
    stems: set[str] = set()
    ids: set[str] = set()
    components: set[str] = set()
    component_counts: dict[str, int] = {}

    for entry in entries:
        if not isinstance(entry, dict):
            raise ManifestError("migration manifest entry must be an object")
        entry_targets = entry.get("targets")
        if not isinstance(entry_targets, list) or not entry_targets:
            raise ManifestError("migration entry requires explicit targets")
        if any(item not in ALLOWED_TARGETS for item in entry_targets):
            raise ManifestError("migration entry contains an unsupported target")
        if len(entry_targets) != len(set(entry_targets)):
            raise ManifestError("migration entry contains duplicate targets")

        entry_id = entry.get("id")
        component = entry.get("component")
        provenance = entry.get("provenance")
        relative = entry.get("path")
        expected_hash = entry.get("sha256")
        if not all(isinstance(value, str) and value for value in (
            entry_id,
            component,
            provenance,
            relative,
            expected_hash,
        )):
            raise ManifestError("migration entry has missing string fields")
        normalized_identity = re.sub(
            r"[^a-z0-9]", "", f"{entry_id}{component}{relative}".lower()
        )
        if "h00" in normalized_identity:
            raise ManifestError("H-00 is forbidden in promotable manifests")
        if provenance not in ALLOWED_PROVENANCE:
            raise ManifestError(f"non-promotable provenance: {provenance}")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise ManifestError("migration checksum must be lowercase SHA-256")

        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ManifestError("migration path must remain inside the repository")
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(migration_root)
        except ValueError as exc:
            raise ManifestError("migration path is outside db/migrations") from exc
        if candidate.suffix.lower() != ".sql" or candidate.is_symlink():
            raise ManifestError("migration path must be a regular SQL file")
        if not candidate.is_file():
            raise ManifestError(f"migration file is missing: {relative}")
        if not candidate.stem.casefold().startswith(F6_STEM_PREFIX):
            raise ManifestError("historical or non-F6 migration stem is forbidden")

        stem = candidate.stem.casefold()
        if stem in stems or entry_id in ids:
            raise ManifestError("duplicate migration stem or ID")
        stems.add(stem)
        ids.add(entry_id)

        if _sha256(candidate) != expected_hash:
            raise ManifestError(f"migration checksum mismatch: {relative}")
        sql = candidate.read_text(encoding="utf-8")
        if not re.search(r"(?im)^\s*set\s+search_path\s*=\s*''\s*;", sql):
            raise ManifestError(
                f"{relative}: migration must set an empty search_path"
            )
        validate_promotable_sql(sql, label=relative)
        if target in entry_targets:
            resolved.append(candidate)
            component_counts[component] = component_counts.get(component, 0) + 1
            components.add(component)

    if not resolved:
        raise ManifestError(f"manifest has no migrations for target {target}")
    if target in ALLOWED_TARGETS and (
        components != {"g1b", "hito1"}
        or component_counts != {"g1b": 1, "hito1": 1}
    ):
        raise ManifestError("FASE-06 package must contain g1b and hito1 exactly")
    return resolved
