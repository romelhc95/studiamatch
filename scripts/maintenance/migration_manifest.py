#!/usr/bin/env python3
"""Validate and resolve closed migration manifests."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
import subprocess
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Sequence


def _freeze_policy(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _freeze_policy(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_policy(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_policy(item) for item in value)
    return value


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_ROOT = ROOT / "db" / "migrations"
ALLOWED_TARGETS = frozenset({"free", "pro"})
ALLOWED_PROVENANCE = frozenset({"new_forward_only"})
ALLOWED_STATUSES = frozenset({
    "reconciled_not_certified",
    "ready_for_free",
    "free_certified",
})
PACKAGE_STEM_PREFIXES = (
    "20260724_fase06_",
    "20260725_fase07_",
    "20260725_fase08_",
)
F9_5_PACKAGE_STEM_PREFIXES = PACKAGE_STEM_PREFIXES + (
    "20260726_fase09_5_",
)
F9_5_PACKAGE_ID = "F9.5-RLS-CANARY-RECONCILIATION-20260726"
F9_5_SUCCESSOR_PATH = (
    "db/migrations/20260726_fase09_5_rls_canary_reconciliation.sql"
)
F9_5_MANIFEST_SHA256 = (
    "27af06a3411f65786d5dfbda19814c24b187f13a055a0fa4733698843f1d3353"
)
MIGRATION_FILENAME_RE = re.compile(r"^[0-9]{8}_[a-z0-9_]+\.sql$")
_MANIFEST_CONTRACTS = {
    (1, "FASE-06", "F6-DB-AS-CODE-20260724"): {
        "component_order": ["g1b", "hito1", "g1b_closure"],
        "component_counts": {"g1b": 1, "hito1": 1, "g1b_closure": 1},
        "stem_prefixes": ("20260724_fase06_", "20260725_fase07_"),
        "component_prefixes": {
            "g1b": "20260724_fase06_",
            "hito1": "20260724_fase06_",
            "g1b_closure": "20260725_fase07_",
        },
        "blocked_targets_by_status": None,
    },
    (1, "FASE-08", "F8-HITO1-FUNCTIONAL-20260725"): {
        "component_order": [
            "g1b",
            "hito1",
            "g1b_closure",
            "hito1_functional_closure",
        ],
        "component_counts": {
            "g1b": 1,
            "hito1": 1,
            "g1b_closure": 1,
            "hito1_functional_closure": 1,
        },
        "stem_prefixes": PACKAGE_STEM_PREFIXES,
        "component_prefixes": {
            "g1b": "20260724_fase06_",
            "hito1": "20260724_fase06_",
            "g1b_closure": "20260725_fase07_",
            "hito1_functional_closure": "20260725_fase08_",
        },
        "blocked_targets_by_status": {
            "reconciled_not_certified": ["free", "pro"],
            "ready_for_free": ["pro"],
            "free_certified": [],
        },
        "excluded": {
            "H-00": "historical_free_only",
            "canary": "observed_effective_unledgered",
            "historical_snapshots": "superseded",
        },
    },
    (1, "FASE-09.5", "F9.5-RLS-CANARY-RECONCILIATION-20260726"): {
        "component_order": [
            "g1b",
            "hito1",
            "g1b_closure",
            "hito1_functional_closure",
            "rls_canary_reconciliation",
        ],
        "component_counts": {
            "g1b": 1,
            "hito1": 1,
            "g1b_closure": 1,
            "hito1_functional_closure": 1,
            "rls_canary_reconciliation": 1,
        },
        "stem_prefixes": F9_5_PACKAGE_STEM_PREFIXES,
        "component_prefixes": {
            "g1b": "20260724_fase06_",
            "hito1": "20260724_fase06_",
            "g1b_closure": "20260725_fase07_",
            "hito1_functional_closure": "20260725_fase08_",
            "rls_canary_reconciliation": "20260726_fase09_5_",
        },
        "blocked_targets_by_status": {
            "reconciled_not_certified": ["free", "pro"],
            "ready_for_free": ["pro"],
            "free_certified": [],
        },
        "excluded": {
            "H-00": "historical_free_only",
            "canary_operational_data": "observed_effective_unledgered",
            "historical_snapshots": "superseded",
        },
        "exact_entries": (
            (
                "F6-G1B-FORWARD", "g1b",
                "db/migrations/20260724_fase06_g1b_reconciliation.sql",
                "d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df",
                "new_forward_only", ("free", "pro"),
            ),
            (
                "F6-HITO1-FORWARD", "hito1",
                "db/migrations/20260724_fase06_hito1_editorial_contract.sql",
                "b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a",
                "new_forward_only", ("free", "pro"),
            ),
            (
                "F7-G1B-CLOSURE", "g1b_closure",
                "db/migrations/20260725_fase07_g1b_closure.sql",
                "9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120",
                "new_forward_only", ("free", "pro"),
            ),
            (
                "F8-HITO1-FUNCTIONAL-CLOSURE", "hito1_functional_closure",
                "db/migrations/20260725_fase08_hito1_functional_closure.sql",
                "7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527",
                "new_forward_only", ("free", "pro"),
            ),
            (
                "F9.5-RLS-CANARY-RECONCILIATION", "rls_canary_reconciliation",
                "db/migrations/20260726_fase09_5_rls_canary_reconciliation.sql",
                "4959b3f1ad60e2fe3a6e9a23161dd0467cfc549e10c1262ba8a0bb2aaf4c9a01",
                "new_forward_only", ("free", "pro"),
            ),
        ),
    },
}
MANIFEST_CONTRACTS = _freeze_policy(_MANIFEST_CONTRACTS)
_ALLOWED_TARGETS_SNAPSHOT = ALLOWED_TARGETS
_ALLOWED_PROVENANCE_SNAPSHOT = ALLOWED_PROVENANCE
_ALLOWED_STATUSES_SNAPSHOT = ALLOWED_STATUSES
_MANIFEST_CONTRACTS_SNAPSHOT = MANIFEST_CONTRACTS
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

F10_PACKAGE_ID = "F10-HITO1-PROMOTION-CONTRACT-20260725"
F10_SOURCE_MANIFEST_PATH = "db/manifests/fase08_candidate.json"
F10_SOURCE_PACKAGE_ID = "F8-HITO1-FUNCTIONAL-20260725"
F10_SOURCE_MANIFEST_SHA256 = (
    "db1c61e9baf8d3927669bf33c5a8f4a708c11d87b81a41c9454dd91b63ebe4cb"
)
F10_SOURCE_RAW_LF_SHA256 = (
    "6946570738aba234bb41273fc0839a50ece0617d464906a84736d1b2aafd4fee"
)
F10_INITIAL_STATE = "reconciled_not_certified"
F10_STATE_ORDER = (
    "reconciled_not_certified",
    "ready_for_free",
    "free_schema_certified",
    "free_backfill_certified",
    "free_certified",
)
F10_EXCLUSIONS = MappingProxyType({
    "H-00": "historical_free_only",
    "canary": "observed_effective_unledgered",
    "historical_snapshots": "superseded",
})
F10_STATES = MappingProxyType({
    "reconciled_not_certified": MappingProxyType({
        "schema_apply_blocked_targets": ("free", "pro"),
        "next_capabilities": ("REMOTE_READ_FREE", "ACCEPT_FREE_READINESS"),
    }),
    "ready_for_free": MappingProxyType({
        "schema_apply_blocked_targets": ("pro",),
        "next_capabilities": ("APPLY_SCHEMA_FREE",),
    }),
    "free_schema_certified": MappingProxyType({
        "schema_apply_blocked_targets": ("free", "pro"),
        "next_capabilities": ("BACKFILL_FREE",),
    }),
    "free_backfill_certified": MappingProxyType({
        "schema_apply_blocked_targets": ("free", "pro"),
        "next_capabilities": ("CERTIFY_FREE_READ_ONLY",),
    }),
    "free_certified": MappingProxyType({
        "schema_apply_blocked_targets": ("free",),
        "next_capabilities": ("PROMOTE_PRO",),
    }),
})
F10_PAYLOAD_ENTRIES = (
    MappingProxyType({
        "id": "F6-G1B-FORWARD",
        "component": "g1b",
        "path": "db/migrations/20260724_fase06_g1b_reconciliation.sql",
        "sha256": "d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df",
        "provenance": "new_forward_only",
        "targets": ("free", "pro"),
    }),
    MappingProxyType({
        "id": "F6-HITO1-FORWARD",
        "component": "hito1",
        "path": "db/migrations/20260724_fase06_hito1_editorial_contract.sql",
        "sha256": "b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a",
        "provenance": "new_forward_only",
        "targets": ("free", "pro"),
    }),
    MappingProxyType({
        "id": "F7-G1B-CLOSURE",
        "component": "g1b_closure",
        "path": "db/migrations/20260725_fase07_g1b_closure.sql",
        "sha256": "9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120",
        "provenance": "new_forward_only",
        "targets": ("free", "pro"),
    }),
    MappingProxyType({
        "id": "F8-HITO1-FUNCTIONAL-CLOSURE",
        "component": "hito1_functional_closure",
        "path": "db/migrations/20260725_fase08_hito1_functional_closure.sql",
        "sha256": "7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527",
        "provenance": "new_forward_only",
        "targets": ("free", "pro"),
    }),
)
F10_TRANSITIONS = (
    MappingProxyType({
        "id": "T01_FREE_READINESS",
        "from": "reconciled_not_certified",
        "to": "ready_for_free",
        "target": "free",
        "acceptance_capability": "ACCEPT_FREE_READINESS",
        "evidence_types": (
            "f9_completion",
            "free_preflight",
            "free_application_plan_approval",
        ),
    }),
    MappingProxyType({
        "id": "T02_FREE_SCHEMA",
        "from": "ready_for_free",
        "to": "free_schema_certified",
        "target": "free",
        "acceptance_capability": "ACCEPT_FREE_SCHEMA",
        "evidence_types": (
            "free_schema_application_approval",
            "free_backup_restore",
            "free_writers_pause",
            "free_schema_postconditions",
            "free_advisors",
        ),
    }),
    MappingProxyType({
        "id": "T03_FREE_BACKFILL",
        "from": "free_schema_certified",
        "to": "free_backfill_certified",
        "target": "free",
        "acceptance_capability": "ACCEPT_FREE_BACKFILL",
        "evidence_types": (
            "free_backfill_plan_approval",
            "free_backfill_execution_approval",
            "free_backfill_result",
        ),
    }),
    MappingProxyType({
        "id": "T04_FREE_FINAL",
        "from": "free_backfill_certified",
        "to": "free_certified",
        "target": "free",
        "acceptance_capability": "ACCEPT_FREE_FINAL",
        "evidence_types": (
            "free_final_certification_approval",
            "free_final_readonly",
            "free_advisors",
            "free_backfill_idempotency",
        ),
    }),
)
_F10_PACKAGE_ID_SNAPSHOT = F10_PACKAGE_ID
_F10_SOURCE_MANIFEST_PATH_SNAPSHOT = F10_SOURCE_MANIFEST_PATH
_F10_SOURCE_PACKAGE_ID_SNAPSHOT = F10_SOURCE_PACKAGE_ID
_F10_SOURCE_MANIFEST_SHA256_SNAPSHOT = F10_SOURCE_MANIFEST_SHA256
_F10_SOURCE_RAW_LF_SHA256_SNAPSHOT = F10_SOURCE_RAW_LF_SHA256
_F10_INITIAL_STATE_SNAPSHOT = F10_INITIAL_STATE
_F10_STATE_ORDER_SNAPSHOT = F10_STATE_ORDER
_F10_EXCLUSIONS_SNAPSHOT = F10_EXCLUSIONS
_F10_STATES_SNAPSHOT = F10_STATES
_F10_PAYLOAD_ENTRIES_SNAPSHOT = F10_PAYLOAD_ENTRIES
_F10_TRANSITIONS_SNAPSHOT = F10_TRANSITIONS

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RFC3339_SECONDS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ATTESTATION_ID_RE = re.compile(
    r"^ATT-(T0[1-4]_[A-Z_]+)-(\d{8}T\d{6}Z)-([0-9a-f]{12})$"
)
_TARGET_ORIGIN_RE = re.compile(
    r"^https://(?P<project_ref>[a-z0-9]{20})\.supabase\.co$"
)
_PUBLISHABLE_KEY_PREFIX = "sb_" + "publishable_"
_PUBLISHABLE_KEY_RE = re.compile(
    rf"^{re.escape(_PUBLISHABLE_KEY_PREFIX)}[A-Za-z0-9_-]+$"
)


class ManifestError(RuntimeError):
    """Raised when a migration package is not safe to execute."""


def _reject_json_float(value: str) -> None:
    raise ManifestError(f"project-JCS-v1 forbids floating-point value {value!r}")


def _reject_json_constant(value: str) -> None:
    raise ManifestError(f"project-JCS-v1 forbids non-finite value {value!r}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _validate_project_json(value: Any, *, location: str = "$") -> None:
    """Validate the deliberately small project-JCS-v1 data model."""

    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise ManifestError(f"project-JCS-v1 requires NFC text at {location}")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ManifestError(
                f"project-JCS-v1 requires valid Unicode at {location}"
            ) from exc
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_project_json(item, location=f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ManifestError(
                    f"project-JCS-v1 requires string object keys at {location}"
                )
            _validate_project_json(key, location=f"{location}.<key>")
            _validate_project_json(item, location=f"{location}.{key}")
        return
    raise ManifestError(
        f"project-JCS-v1 does not support {type(value).__name__} at {location}"
    )


def strict_json_loads(text: str | bytes) -> Any:
    """Parse project JSON without accepting lossy or ambiguous constructs."""

    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ManifestError("project JSON is not valid UTF-8") from exc
    if not isinstance(text, str):
        raise ManifestError("project JSON input must be text or UTF-8 bytes")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_constant,
        )
    except ManifestError:
        raise
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid project JSON: {exc}") from exc
    _validate_project_json(value)
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical project-JCS-v1 UTF-8 bytes for a complete object."""

    _validate_project_json(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ManifestError(f"cannot canonicalize project JSON: {exc}") from exc


def canonical_json_sha256(value: Any) -> str:
    """Hash the complete project-JCS-v1 representation."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def derive_target_fingerprint(canonical_origin: str, publishable_key: str) -> str:
    """Derive the sanitized Free target identity without environment access.

    Inputs are deliberately strict and errors never include either input.
    This helper accepts only the canonical F10 Free origin/key shapes; it has no
    generic target or Pro parameter.
    """

    if (
        not isinstance(canonical_origin, str)
        or _TARGET_ORIGIN_RE.fullmatch(canonical_origin) is None
    ):
        raise ManifestError("target origin is not canonical for F10 Free")
    if (
        not isinstance(publishable_key, str)
        or _PUBLISHABLE_KEY_RE.fullmatch(publishable_key) is None
    ):
        raise ManifestError("target publishable key has an invalid modern format")

    key_hash = hashlib.sha256(publishable_key.encode("utf-8")).hexdigest()
    material = (
        "studiamatch-target-v1\0free\0"
        f"{canonical_origin.lower()}\0{key_hash}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def target_fingerprints_match(expected: str, observed: str) -> bool:
    """Compare two sanitized target fingerprints in constant time."""

    if (
        not isinstance(expected, str)
        or not isinstance(observed, str)
        or _SHA256_RE.fullmatch(expected) is None
        or _SHA256_RE.fullmatch(observed) is None
    ):
        raise ManifestError("target fingerprint must be lowercase SHA-256")
    return hmac.compare_digest(expected, observed)


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
        os.path.abspath(right)
    )


def _canonical_directory(path: Path, *, label: str) -> Path:
    supplied = Path(os.path.abspath(path))
    try:
        metadata = supplied.lstat()
        resolved = supplied.resolve(strict=True)
    except OSError as exc:
        raise ManifestError(f"cannot inspect {label}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ManifestError(f"{label} must be a non-symlink directory")
    if not _same_path(supplied, resolved):
        raise ManifestError(f"{label} must be a canonical path")
    return supplied


def _assert_no_symlink_chain(path: Path, *, anchor: Path, label: str) -> None:
    anchor = Path(os.path.abspath(anchor))
    path = Path(os.path.abspath(path))
    try:
        relative = path.relative_to(anchor)
    except ValueError as exc:
        raise ManifestError(f"{label} escapes its anchored root") from exc
    current = anchor
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise ManifestError(f"cannot inspect {label}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ManifestError(f"{label} cannot use symlinks")


def _read_regular_file_bytes(path: Path, *, anchor: Path, label: str) -> bytes:
    """Read one anchored regular file with portable no-follow identity checks."""

    path = Path(os.path.abspath(path))
    _assert_no_symlink_chain(path, anchor=anchor, label=label)
    try:
        before = path.lstat()
    except OSError as exc:
        raise ManifestError(f"cannot inspect {label}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise ManifestError(f"{label} must be a regular file")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ManifestError(f"cannot open {label}") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (before.st_dev, before.st_ino):
            raise ManifestError(f"{label} identity changed before read")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read()
        after_open = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = path.lstat()
    except OSError as exc:
        raise ManifestError(f"{label} disappeared after read") from exc
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    if before_identity != (
        after_open.st_dev,
        after_open.st_ino,
        after_open.st_size,
        after_open.st_mtime_ns,
    ) or before_identity != (
        after_path.st_dev,
        after_path.st_ino,
        after_path.st_size,
        after_path.st_mtime_ns,
    ):
        raise ManifestError(f"{label} changed during read")
    if len(payload) != before.st_size:
        raise ManifestError(f"{label} read was incomplete")
    return payload


def _read_strict_json_with_bytes(
    path: Path, *, anchor: Path, label: str
) -> tuple[dict[str, Any], bytes]:
    try:
        payload = _read_regular_file_bytes(path, anchor=anchor, label=label)
        value = strict_json_loads(payload)
    except ManifestError:
        raise
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be a JSON object")
    return value, payload


def _read_strict_json(path: Path, *, anchor: Path, label: str) -> dict[str, Any]:
    return _read_strict_json_with_bytes(path, anchor=anchor, label=label)[0]


def _require_exact_keys(value: Any, expected: set[str], *, label: str) -> None:
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise ManifestError(
            f"{label} fields are not closed (missing={missing}, unknown={unknown})"
        )


def _mutable_policy_copy(value: Any) -> Any:
    """Return a fresh JSON-shaped copy of the immutable policy snapshot."""

    if isinstance(value, Mapping):
        return {key: _mutable_policy_copy(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_mutable_policy_copy(item) for item in value]
    return value


def _expected_f10_descriptor() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "phase": "FASE-10",
        "package_id": _F10_PACKAGE_ID_SNAPSHOT,
        "capability_class": "LOCAL_PROMOTION_CONTRACT",
        "approval_policy": {
            "owner": "romelhc95",
            "reviewer": "romelhc95-approver",
            "self_approval": False,
        },
        "source_manifest": {
            "path": _F10_SOURCE_MANIFEST_PATH_SNAPSHOT,
            "package_id": _F10_SOURCE_PACKAGE_ID_SNAPSHOT,
            "canonical_json_sha256": _F10_SOURCE_MANIFEST_SHA256_SNAPSHOT,
        },
        "initial_state": _F10_INITIAL_STATE_SNAPSHOT,
        "state_order": _mutable_policy_copy(_F10_STATE_ORDER_SNAPSHOT),
        "states": _mutable_policy_copy(_F10_STATES_SNAPSHOT),
        "payload_entries": _mutable_policy_copy(_F10_PAYLOAD_ENTRIES_SNAPSHOT),
        "transitions": _mutable_policy_copy(_F10_TRANSITIONS_SNAPSHOT),
        "excluded": _mutable_policy_copy(_F10_EXCLUSIONS_SNAPSHOT),
    }


def reject_v1_circular_prerequisites(manifest: Any) -> None:
    """Reject the historical v1 gate model for any future promotion decision.

    ``load_manifest`` intentionally remains compatible with v1 for historical
    package validation.  Promotion callers must use this stricter entry point.
    """

    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        return
    prerequisites = manifest.get("prerequisites")
    circular = {
        "editorial_backfill_certified",
        "free_postconditions_certified",
    }
    if isinstance(prerequisites, list) and circular.issubset(set(prerequisites)):
        raise ManifestError(
            "schema v1 circular prerequisites cannot authorize future promotion"
        )
    raise ManifestError("schema v1 cannot authorize future promotion")


def _validate_f10_descriptor_shape(descriptor: Any) -> dict[str, Any]:
    _validate_project_json(descriptor)
    if not isinstance(descriptor, dict):
        raise ManifestError("promotion descriptor must be a JSON object")
    if type(descriptor.get("schema_version")) is not int:
        raise ManifestError("promotion descriptor schema_version must be an integer")
    if descriptor.get("schema_version") == 1:
        reject_v1_circular_prerequisites(descriptor)

    expected = _expected_f10_descriptor()
    _require_exact_keys(descriptor, set(expected), label="promotion descriptor")
    _require_exact_keys(
        descriptor.get("approval_policy"),
        {"owner", "reviewer", "self_approval"},
        label="approval_policy",
    )
    _require_exact_keys(
        descriptor.get("source_manifest"),
        {"path", "package_id", "canonical_json_sha256"},
        label="source_manifest",
    )
    states = descriptor.get("states")
    _require_exact_keys(states, set(_F10_STATE_ORDER_SNAPSHOT), label="states")
    for state in _F10_STATE_ORDER_SNAPSHOT:
        _require_exact_keys(
            states[state],
            {"schema_apply_blocked_targets", "next_capabilities"},
            label=f"states.{state}",
        )
    payload_entries = descriptor.get("payload_entries")
    if not isinstance(payload_entries, list):
        raise ManifestError("payload_entries must be an array")
    for index, entry in enumerate(payload_entries):
        _require_exact_keys(
            entry,
            {"id", "component", "path", "sha256", "provenance", "targets"},
            label=f"payload_entries[{index}]",
        )
    transitions = descriptor.get("transitions")
    if not isinstance(transitions, list):
        raise ManifestError("transitions must be an array")
    for index, transition in enumerate(transitions):
        _require_exact_keys(
            transition,
            {
                "id",
                "from",
                "to",
                "target",
                "acceptance_capability",
                "evidence_types",
            },
            label=f"transitions[{index}]",
        )
    _require_exact_keys(
        descriptor.get("excluded"), set(_F10_EXCLUSIONS_SNAPSHOT), label="excluded"
    )

    source_hash = descriptor["source_manifest"]["canonical_json_sha256"]
    if not isinstance(source_hash, str) or not _SHA256_RE.fullmatch(source_hash):
        raise ManifestError("source manifest hash must be lowercase SHA-256")
    if descriptor != expected:
        raise ManifestError("promotion descriptor differs from the exact F10 contract")
    return descriptor


def validate_promotion_descriptor(
    descriptor: Any, *, root: Path = ROOT
) -> dict[str, Any]:
    """Validate the closed F10 descriptor and all inherited local bytes."""

    validated = _validate_f10_descriptor_shape(descriptor)
    root = _canonical_directory(Path(root), label="repository root")
    source_path = Path(
        os.path.abspath(root / _F10_SOURCE_MANIFEST_PATH_SNAPSHOT)
    )
    expected_source_path = Path(
        os.path.abspath(root / "db" / "manifests" / "fase08_candidate.json")
    )
    if not _same_path(source_path, expected_source_path):
        raise ManifestError("source manifest path is not the immutable F8 manifest")
    source, source_bytes = _read_strict_json_with_bytes(
        source_path, anchor=root, label="F8 source manifest"
    )
    raw_lf_hash = hashlib.sha256(source_bytes.replace(b"\r\n", b"\n")).hexdigest()
    if raw_lf_hash != _F10_SOURCE_RAW_LF_SHA256_SNAPSHOT:
        raise ManifestError("F8 source raw LF identity mismatch")
    if canonical_json_sha256(source) != _F10_SOURCE_MANIFEST_SHA256_SNAPSHOT:
        raise ManifestError("F8 source manifest canonical hash mismatch")
    if source.get("package_id") != _F10_SOURCE_PACKAGE_ID_SNAPSHOT:
        raise ManifestError("F8 source package identity mismatch")
    if source.get("status") != _F10_INITIAL_STATE_SNAPSHOT:
        raise ManifestError("F8 source status changed")
    if source.get("blocked_targets") != ["free", "pro"]:
        raise ManifestError("F8 source target blocks changed")
    if source.get("entries") != validated["payload_entries"]:
        raise ManifestError("F10 payload does not inherit F8 entries byte-for-byte")
    if source.get("excluded") != validated["excluded"]:
        raise ManifestError("F10 exclusions do not inherit F8 exactly")

    migration_root = Path(os.path.abspath(root / "db" / "migrations"))
    for entry in validated["payload_entries"]:
        migration = Path(os.path.abspath(root / entry["path"]))
        try:
            migration.relative_to(migration_root)
        except ValueError as exc:
            raise ManifestError("F10 payload path escapes db/migrations") from exc
        migration_bytes = _read_regular_file_bytes(
            migration, anchor=root, label=f"F10 payload migration {entry['id']}"
        )
        migration_hash = hashlib.sha256(
            migration_bytes.replace(b"\r\n", b"\n")
        ).hexdigest()
        if migration_hash != entry["sha256"]:
            raise ManifestError(f"F10 payload migration hash mismatch: {entry['path']}")
    return validated


def load_promotion_contract(
    descriptor_path: str | Path, *, root: Path = ROOT
) -> dict[str, Any]:
    """Load the one local/offline F10 promotion descriptor."""

    root = _canonical_directory(Path(root), label="repository root")
    expected = Path(
        os.path.abspath(root / "db" / "manifests" / "fase10_promotion_contract.json")
    )
    supplied = Path(descriptor_path)
    supplied = Path(os.path.abspath(root / supplied if not supplied.is_absolute() else supplied))
    if not _same_path(supplied, expected):
        raise ManifestError("promotion descriptor path is not canonical")
    descriptor = _read_strict_json(
        supplied, anchor=root, label="promotion descriptor"
    )
    return validate_promotion_descriptor(descriptor, root=root)


def schema_apply_is_blocked(descriptor: Any, state: str, target: str) -> bool:
    """Classify schema replay eligibility without environment or transport."""

    _validate_f10_descriptor_shape(descriptor)
    if state not in _F10_STATE_ORDER_SNAPSHOT:
        raise ManifestError(f"unknown promotion state: {state}")
    if target not in _ALLOWED_TARGETS_SNAPSHOT:
        raise ManifestError(f"unsupported schema target: {target}")
    return target in descriptor["states"][state]["schema_apply_blocked_targets"]


def require_schema_apply_allowed(descriptor: Any, state: str, target: str) -> None:
    if schema_apply_is_blocked(descriptor, state, target):
        raise ManifestError(f"schema apply to {target} is blocked in state {state}")


def _parse_utc_seconds(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not _RFC3339_SECONDS_RE.fullmatch(value):
        raise ManifestError(f"{label} must be UTC RFC3339 seconds with Z")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ManifestError(f"{label} is not a valid UTC timestamp") from exc


def _resolve_clock(
    clock: datetime | Callable[[], datetime] | None,
) -> datetime | None:
    if clock is None:
        return None
    value = clock() if callable(clock) else clock
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ManifestError("injected clock must return a timezone-aware datetime")
    if value.utcoffset() != timedelta(0):
        raise ManifestError("injected clock must be UTC")
    return value.astimezone(timezone.utc)


def _validate_attestation_fields(attestation: Any, *, label: str) -> None:
    _validate_project_json(attestation, location=label)
    _require_exact_keys(
        attestation,
        {
            "schema_version",
            "attestation_id",
            "transition_id",
            "from_state",
            "to_state",
            "target_environment",
            "target_fingerprint_sha256",
            "package_id",
            "descriptor_sha256",
            "source_manifest_sha256",
            "commit_sha",
            "tree_sha",
            "operation_owner",
            "previous_attestation_sha256",
            "created_at",
            "result",
            "approval",
            "evidence",
        },
        label=label,
    )
    _require_exact_keys(
        attestation.get("approval"),
        {"github_login", "review_id", "reviewed_commit_sha", "decision"},
        label=f"{label}.approval",
    )
    evidence = attestation.get("evidence")
    if not isinstance(evidence, list):
        raise ManifestError(f"{label}.evidence must be an array")
    for index, item in enumerate(evidence):
        _require_exact_keys(
            item,
            {"type", "sha256", "observed_at", "expires_at"},
            label=f"{label}.evidence[{index}]",
        )


_INVENTORY_TOKEN = object()


@dataclass(frozen=True)
class AttestationInventory:
    """Immutable, complete snapshot of one canonical attestation directory."""

    directory: str
    canonical_attestations: tuple[bytes, ...]
    file_names: tuple[str, ...]
    attestation_hashes: tuple[str, ...]
    inventory_sha256: str
    _loader_token: object

    def objects(self) -> tuple[dict[str, Any], ...]:
        if self._loader_token is not _INVENTORY_TOKEN:
            raise ManifestError("attestation inventory was not produced by the loader")
        return tuple(strict_json_loads(payload) for payload in self.canonical_attestations)


def load_attestation_inventory(
    directory: str | Path | None = None, *, root: Path = ROOT
) -> AttestationInventory:
    """Atomically load and globally validate the canonical Hito 1 inventory."""

    root = _canonical_directory(Path(root), label="repository root")
    expected = Path(os.path.abspath(root / "db" / "attestations" / "hito1"))
    supplied = expected if directory is None else Path(directory)
    supplied = Path(
        os.path.abspath(root / supplied if not supplied.is_absolute() else supplied)
    )
    if not _same_path(supplied, expected):
        raise ManifestError("attestation inventory path is not canonical")
    inventory_dir = _canonical_directory(supplied, label="attestation inventory")
    _assert_no_symlink_chain(
        inventory_dir, anchor=root, label="attestation inventory"
    )
    before_dir = inventory_dir.stat()

    try:
        with os.scandir(inventory_dir) as iterator:
            entries = sorted(iterator, key=lambda item: item.name)
    except OSError as exc:
        raise ManifestError("cannot list attestation inventory") from exc
    names = tuple(entry.name for entry in entries)
    objects_by_hash: dict[str, dict[str, Any]] = {}
    bytes_by_hash: dict[str, bytes] = {}
    names_by_hash: dict[str, str] = {}
    file_identities: dict[str, tuple[int, int, int, int]] = {}
    ids: set[str] = set()
    for entry in entries:
        if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
            raise ManifestError("attestation inventory contains a non-regular file")
        if not entry.name.endswith(".json"):
            raise ManifestError("attestation inventory contains an unexpected file")
        path = inventory_dir / entry.name
        attestation, _raw = _read_strict_json_with_bytes(
            path, anchor=inventory_dir, label="attestation inventory file"
        )
        metadata = path.lstat()
        file_identities[entry.name] = (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        )
        _validate_attestation_fields(attestation, label=f"inventory.{entry.name}")
        attestation_id = attestation.get("attestation_id")
        if (
            not isinstance(attestation_id, str)
            or _ATTESTATION_ID_RE.fullmatch(attestation_id) is None
            or entry.name != f"{attestation_id}.json"
        ):
            raise ManifestError("attestation inventory filename is not canonical")
        canonical = canonical_json_bytes(attestation)
        digest = hashlib.sha256(canonical).hexdigest()
        if digest in objects_by_hash or attestation_id in ids:
            raise ManifestError("attestation inventory contains a duplicate")
        objects_by_hash[digest] = attestation
        bytes_by_hash[digest] = canonical
        names_by_hash[digest] = entry.name
        ids.add(attestation_id)

    children: dict[str | None, list[str]] = {}
    for digest, attestation in objects_by_hash.items():
        predecessor = attestation["previous_attestation_sha256"]
        if predecessor is not None and (
            not isinstance(predecessor, str)
            or _SHA256_RE.fullmatch(predecessor) is None
        ):
            raise ManifestError("attestation inventory predecessor is malformed")
        if predecessor is not None and predecessor not in objects_by_hash:
            raise ManifestError("attestation inventory contains an orphan")
        children.setdefault(predecessor, []).append(digest)
    if any(len(child_hashes) > 1 for child_hashes in children.values()):
        raise ManifestError("attestation inventory contains a sibling fork")

    ordered_hashes: list[str] = []
    if objects_by_hash:
        roots = children.get(None, [])
        if len(roots) != 1:
            raise ManifestError("attestation inventory must have exactly one root")
        current: str | None = roots[0]
        while current is not None:
            if current in ordered_hashes:
                raise ManifestError("attestation inventory contains a cycle")
            ordered_hashes.append(current)
            descendants = children.get(current, [])
            current = descendants[0] if descendants else None
        if len(ordered_hashes) != len(objects_by_hash):
            raise ManifestError("attestation inventory is disconnected")
        transition_ids = [
            objects_by_hash[digest]["transition_id"] for digest in ordered_hashes
        ]
        expected_ids = [
            item["id"]
            for item in _F10_TRANSITIONS_SNAPSHOT[: len(ordered_hashes)]
        ]
        if transition_ids != expected_ids:
            raise ManifestError("attestation inventory contains a transition gap")

    try:
        with os.scandir(inventory_dir) as iterator:
            final_names = tuple(sorted(item.name for item in iterator))
        after_dir = inventory_dir.stat()
    except OSError as exc:
        raise ManifestError("attestation inventory changed during load") from exc
    if names != final_names or (
        before_dir.st_dev,
        before_dir.st_ino,
        before_dir.st_mtime_ns,
    ) != (
        after_dir.st_dev,
        after_dir.st_ino,
        after_dir.st_mtime_ns,
    ):
        raise ManifestError("attestation inventory changed during load")
    for name, identity in file_identities.items():
        try:
            metadata = (inventory_dir / name).lstat()
        except OSError as exc:
            raise ManifestError("attestation inventory changed during load") from exc
        if identity != (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        ):
            raise ManifestError("attestation inventory changed during load")

    inventory_payload = [
        {"file": names_by_hash[digest], "sha256": digest}
        for digest in sorted(objects_by_hash, key=lambda item: names_by_hash[item])
    ]
    return AttestationInventory(
        directory=str(inventory_dir),
        canonical_attestations=tuple(bytes_by_hash[item] for item in ordered_hashes),
        file_names=tuple(names_by_hash[item] for item in ordered_hashes),
        attestation_hashes=tuple(ordered_hashes),
        inventory_sha256=canonical_json_sha256(inventory_payload),
        _loader_token=_INVENTORY_TOKEN,
    )


def _run_local_git(repo_root: Path, argv: tuple[str, ...]) -> subprocess.CompletedProcess[bytes]:
    environment = {
        "PATH": os.defpath,
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1",
    }
    try:
        return subprocess.run(
            ["git", *argv],
            cwd=repo_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ManifestError("local Git binding command failed closed") from None


def validate_local_git_binding(
    attestation: dict[str, Any],
    *,
    repo_root: str | Path,
    attestation_commit_sha: str,
) -> bool:
    """Prove local commit/tree/review identity and candidate ancestry."""

    root = _canonical_directory(Path(repo_root), label="Git repository root")
    if not isinstance(attestation_commit_sha, str) or not _GIT_SHA_RE.fullmatch(
        attestation_commit_sha
    ):
        raise ManifestError("attestation commit must be a lowercase Git SHA")
    commit_sha = attestation.get("commit_sha")
    tree_sha = attestation.get("tree_sha")
    approval = attestation.get("approval")
    if (
        not isinstance(commit_sha, str)
        or _GIT_SHA_RE.fullmatch(commit_sha) is None
        or not isinstance(tree_sha, str)
        or _GIT_SHA_RE.fullmatch(tree_sha) is None
        or not isinstance(approval, dict)
        or approval.get("reviewed_commit_sha") != commit_sha
        or commit_sha == attestation_commit_sha
    ):
        raise ManifestError("attestation Git binding fields are invalid")

    top_level = _run_local_git(root, ("rev-parse", "--show-toplevel"))
    if top_level.returncode != 0:
        raise ManifestError("Git repository root cannot be verified")
    try:
        observed_root = Path(top_level.stdout.decode("utf-8").strip())
    except UnicodeDecodeError:
        raise ManifestError("Git repository root cannot be verified") from None
    if not _same_path(root, observed_root):
        raise ManifestError("Git repository root is not canonical")

    for candidate in (commit_sha, attestation_commit_sha):
        result = _run_local_git(root, ("cat-file", "-e", f"{candidate}^{{commit}}"))
        if result.returncode != 0:
            raise ManifestError("required Git commit object is missing")
    tree = _run_local_git(root, ("rev-parse", "--verify", f"{commit_sha}^{{tree}}"))
    if tree.returncode != 0:
        raise ManifestError("candidate Git tree cannot be verified")
    observed_tree = tree.stdout.decode("ascii", errors="ignore").strip()
    if not hmac.compare_digest(observed_tree, tree_sha):
        raise ManifestError("candidate Git tree does not match attestation")
    ancestry = _run_local_git(
        root,
        ("merge-base", "--is-ancestor", commit_sha, attestation_commit_sha),
    )
    if ancestry.returncode != 0:
        raise ManifestError("candidate commit ancestry is not proven")
    return True


def _git_tree_entries(
    repo_root: Path, commit_sha: str, pathspec: str
) -> dict[str, tuple[str, str]]:
    result = _run_local_git(
        repo_root, ("ls-tree", "-r", commit_sha, "--", pathspec)
    )
    if result.returncode != 0:
        raise ManifestError("attestation commit tree cannot be inspected")
    try:
        lines = result.stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        raise ManifestError("attestation commit tree is not canonical UTF-8") from None
    parsed: dict[str, tuple[str, str]] = {}
    for line in lines:
        match = re.fullmatch(
            r"(?P<mode>[0-9]{6}) blob [0-9a-f]+\t(?P<path>[^\r\n]+)", line
        )
        if match is None or match.group("path") in parsed:
            raise ManifestError("attestation commit tree contains an invalid entry")
        parsed[match.group("path")] = (match.group("mode"), "blob")
    return parsed


def validate_inventory_git_content(
    inventory: AttestationInventory,
    descriptor: dict[str, Any],
    *,
    repo_root: str | Path,
    attestation_commit_sha: str,
) -> bool:
    """Bind the complete inventory and F10 descriptor to one local Git commit."""

    if not isinstance(inventory, AttestationInventory):
        raise ManifestError("complete attestation inventory is required")
    inventory.objects()
    root = _canonical_directory(Path(repo_root), label="Git repository root")
    expected_directory = Path(
        os.path.abspath(root / "db" / "attestations" / "hito1")
    )
    if not _same_path(Path(inventory.directory), expected_directory):
        raise ManifestError("attestation inventory is not rooted in the Git repository")
    if not isinstance(attestation_commit_sha, str) or not _GIT_SHA_RE.fullmatch(
        attestation_commit_sha
    ):
        raise ManifestError("attestation commit must be a lowercase Git SHA")

    top_level = _run_local_git(root, ("rev-parse", "--show-toplevel"))
    if top_level.returncode != 0:
        raise ManifestError("Git repository root cannot be verified")
    try:
        observed_root = Path(top_level.stdout.decode("utf-8").strip())
    except UnicodeDecodeError:
        raise ManifestError("Git repository root cannot be verified") from None
    if not _same_path(root, observed_root):
        raise ManifestError("Git repository root is not canonical")
    exists = _run_local_git(
        root, ("cat-file", "-e", f"{attestation_commit_sha}^{{commit}}")
    )
    if exists.returncode != 0:
        raise ManifestError("attestation Git commit object is missing")

    descriptor_path = "db/manifests/fase10_promotion_contract.json"
    working_descriptor_path = Path(os.path.abspath(root / descriptor_path))
    working_descriptor, working_descriptor_bytes = _read_strict_json_with_bytes(
        working_descriptor_path,
        anchor=root,
        label="working F10 promotion descriptor",
    )
    _validate_f10_descriptor_shape(working_descriptor)
    if not hmac.compare_digest(
        canonical_json_bytes(working_descriptor), canonical_json_bytes(descriptor)
    ):
        raise ManifestError("working F10 descriptor does not match validation input")

    inventory_prefix = "db/attestations/hito1"
    expected_paths = {
        f"{inventory_prefix}/{name}" for name in inventory.file_names
    }
    observed_entries = _git_tree_entries(
        root, attestation_commit_sha, inventory_prefix
    )
    if set(observed_entries) != expected_paths:
        raise ManifestError("attestation commit inventory is incomplete or has extras")
    if any(mode != "100644" for mode, _kind in observed_entries.values()):
        raise ManifestError("attestation commit inventory contains a non-canonical mode")
    expected_objects = dict(zip(inventory.file_names, inventory.canonical_attestations))
    for name, canonical in expected_objects.items():
        path = f"{inventory_prefix}/{name}"
        blob = _run_local_git(root, ("show", f"{attestation_commit_sha}:{path}"))
        if blob.returncode != 0 or not hmac.compare_digest(blob.stdout, canonical):
            raise ManifestError("attestation commit inventory object drift detected")

    descriptor_entries = _git_tree_entries(
        root, attestation_commit_sha, descriptor_path
    )
    if descriptor_entries != {descriptor_path: ("100644", "blob")}:
        raise ManifestError("attestation commit lacks the canonical F10 descriptor")
    descriptor_blob = _run_local_git(
        root, ("show", f"{attestation_commit_sha}:{descriptor_path}")
    )
    if descriptor_blob.returncode != 0:
        raise ManifestError("attestation commit lacks the canonical F10 descriptor")
    if not hmac.compare_digest(descriptor_blob.stdout, working_descriptor_bytes):
        raise ManifestError("attestation commit raw F10 descriptor bytes drift detected")
    committed_descriptor = strict_json_loads(descriptor_blob.stdout)
    _validate_f10_descriptor_shape(committed_descriptor)
    if not hmac.compare_digest(
        canonical_json_bytes(committed_descriptor), canonical_json_bytes(descriptor)
    ):
        raise ManifestError("attestation commit F10 descriptor drift detected")
    return True


def validate_attestation_inventory_structure(
    descriptor: Any,
    attestations: AttestationInventory | Sequence[Any],
    *,
    clock: datetime | Callable[[], datetime] | None = None,
    expected_target_fingerprint: str | None = None,
    repo_root: str | Path | None = None,
    attestation_commit_sha: str | None = None,
) -> None:
    """Validate complete provenance without returning state or capability.

    Omitting ``clock`` performs durable historical replay: evidence is checked
    at attestation creation, never against wall-clock time.  Supplying a UTC
    clock additionally enforces the creation-time future check.  Every
    non-empty chain must come from ``load_attestation_inventory`` and requires
    an independently supplied target fingerprint plus concrete local Git
    commit/tree/review/ancestry proof.
    """

    validated_descriptor = _validate_f10_descriptor_shape(descriptor)
    if isinstance(attestations, AttestationInventory):
        if attestations._loader_token is not _INVENTORY_TOKEN:
            raise ManifestError("attestation inventory was not produced by the loader")
        attestation_sequence: Sequence[Any] = attestations.objects()
    elif isinstance(attestations, (list, tuple)) and len(attestations) == 0:
        attestation_sequence = ()
    else:
        raise ManifestError(
            "non-empty validation requires a complete loaded attestation inventory"
        )
    if len(attestation_sequence) > len(_F10_TRANSITIONS_SNAPSHOT):
        raise ManifestError("attestation chain is longer than the state machine")
    if attestation_sequence:
        if (
            not isinstance(expected_target_fingerprint, str)
            or _SHA256_RE.fullmatch(expected_target_fingerprint) is None
        ):
            raise ManifestError(
                "non-empty validation requires an expected target fingerprint"
            )
        if repo_root is None or attestation_commit_sha is None:
            raise ManifestError(
                "non-empty validation requires repository and attestation commit binding"
            )
        validate_inventory_git_content(
            attestations,
            validated_descriptor,
            repo_root=repo_root,
            attestation_commit_sha=attestation_commit_sha,
        )
    now = _resolve_clock(clock)
    descriptor_hash = canonical_json_sha256(validated_descriptor)
    source_hash = validated_descriptor["source_manifest"]["canonical_json_sha256"]
    policy = validated_descriptor["approval_policy"]

    attestation_ids: set[str] = set()
    attestation_hashes: set[str] = set()
    evidence_hashes: set[str] = set()
    review_ids: set[int] = set()
    stable_fingerprint: str | None = None
    previous: Any = None
    previous_hash: str | None = None
    previous_created: datetime | None = None
    for index, attestation in enumerate(attestation_sequence):
        label = f"attestations[{index}]"
        _validate_attestation_fields(attestation, label=label)
        transition = _F10_TRANSITIONS_SNAPSHOT[index]
        if type(attestation["schema_version"]) is not int or attestation["schema_version"] != 1:
            raise ManifestError(f"{label} has unsupported schema_version")
        if (
            attestation["transition_id"] != transition["id"]
            or attestation["from_state"] != transition["from"]
            or attestation["to_state"] != transition["to"]
            or attestation["target_environment"] != transition["target"]
        ):
            raise ManifestError(f"{label} does not match the consecutive transition")
        if attestation["target_environment"] != "free":
            raise ManifestError("F10 attestations cannot target Pro")

        attestation_id = attestation["attestation_id"]
        match = (
            _ATTESTATION_ID_RE.fullmatch(attestation_id)
            if isinstance(attestation_id, str)
            else None
        )
        if match is None or match.group(1) != transition["id"]:
            raise ManifestError(f"{label}.attestation_id is invalid")
        created = _parse_utc_seconds(attestation["created_at"], label=f"{label}.created_at")
        if match.group(2) != created.strftime("%Y%m%dT%H%M%SZ"):
            raise ManifestError(f"{label}.attestation_id timestamp does not bind created_at")
        if now is not None and created > now:
            raise ManifestError(f"{label}.created_at is in the future")
        if previous_created is not None and created <= previous_created:
            raise ManifestError("attestation created_at values are not strictly ordered")

        for field in (
            "target_fingerprint_sha256",
            "descriptor_sha256",
            "source_manifest_sha256",
        ):
            value = attestation[field]
            if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
                raise ManifestError(f"{label}.{field} must be lowercase SHA-256")
        if attestation["descriptor_sha256"] != descriptor_hash:
            raise ManifestError(f"{label} descriptor identity mismatch")
        if attestation["source_manifest_sha256"] != source_hash:
            raise ManifestError(f"{label} source manifest identity mismatch")
        if attestation["package_id"] != _F10_PACKAGE_ID_SNAPSHOT:
            raise ManifestError(f"{label} package identity mismatch")
        fingerprint = attestation["target_fingerprint_sha256"]
        if not target_fingerprints_match(
            fingerprint, expected_target_fingerprint  # type: ignore[arg-type]
        ):
            raise ManifestError(f"{label} target fingerprint does not match expected")
        if stable_fingerprint is None:
            stable_fingerprint = fingerprint
        elif not target_fingerprints_match(fingerprint, stable_fingerprint):
            raise ManifestError("target fingerprint changed across attestation chain")

        for field in ("commit_sha", "tree_sha"):
            value = attestation[field]
            if not isinstance(value, str) or not _GIT_SHA_RE.fullmatch(value):
                raise ManifestError(f"{label}.{field} must be a lowercase Git SHA")
        if attestation["operation_owner"] != policy["owner"]:
            raise ManifestError(f"{label} operation owner does not match policy")
        if policy["self_approval"] is not False or policy["owner"] == policy["reviewer"]:
            raise ManifestError("approval policy does not prohibit self approval")
        approval = attestation["approval"]
        review_id = approval["review_id"]
        if (
            approval["github_login"] != policy["reviewer"]
            or approval["reviewed_commit_sha"] != attestation["commit_sha"]
            or approval["decision"] != "APPROVED"
            or isinstance(review_id, bool)
            or not isinstance(review_id, int)
            or review_id <= 0
        ):
            raise ManifestError(f"{label} approval is not bound to policy and commit")
        validate_local_git_binding(
            attestation,
            repo_root=repo_root,  # type: ignore[arg-type]
            attestation_commit_sha=attestation_commit_sha,  # type: ignore[arg-type]
        )
        if attestation["result"] != "PASS":
            raise ManifestError(f"{label} result is not PASS")

        expected_previous = None if index == 0 else previous_hash
        if attestation["previous_attestation_sha256"] != expected_previous:
            raise ManifestError(f"{label} predecessor hash is invalid")

        expected_types = list(transition["evidence_types"])
        actual_types = [item["type"] for item in attestation["evidence"]]
        if actual_types != expected_types or len(actual_types) != len(set(actual_types)):
            raise ManifestError(f"{label} evidence types/cardinality are invalid")
        for evidence_index, evidence in enumerate(attestation["evidence"]):
            digest = evidence["sha256"]
            if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
                raise ManifestError(
                    f"{label}.evidence[{evidence_index}] digest is invalid"
                )
            observed = _parse_utc_seconds(
                evidence["observed_at"],
                label=f"{label}.evidence[{evidence_index}].observed_at",
            )
            expires = _parse_utc_seconds(
                evidence["expires_at"],
                label=f"{label}.evidence[{evidence_index}].expires_at",
            )
            interval = expires - observed
            if interval <= timedelta(0) or interval > timedelta(hours=24):
                raise ManifestError(f"{label} evidence interval is invalid")
            if not observed <= created <= expires:
                raise ManifestError(f"{label} evidence was not valid at created_at")
            if digest in evidence_hashes:
                raise ManifestError("evidence digest is reused across the chain")
            evidence_hashes.add(digest)

        attestation_hash = canonical_json_sha256(attestation)
        if attestation_id in attestation_ids or attestation_hash in attestation_hashes:
            raise ManifestError("attestation replay or duplicate detected")
        if review_id in review_ids:
            raise ManifestError("approval review_id is reused across the chain")
        attestation_ids.add(attestation_id)
        attestation_hashes.add(attestation_hash)
        review_ids.add(review_id)
        previous = attestation
        previous_hash = attestation_hash
        previous_created = created
    return None


def derive_effective_state(
    descriptor: Any,
    attestations: AttestationInventory | Sequence[Any],
    *,
    clock: datetime | Callable[[], datetime] | None = None,
    expected_target_fingerprint: str | None = None,
    repo_root: str | Path | None = None,
    attestation_commit_sha: str | None = None,
) -> str:
    """Public operational derivation, blocked pending review authenticity."""

    validate_attestation_inventory_structure(
        descriptor,
        attestations,
        clock=clock,
        expected_target_fingerprint=expected_target_fingerprint,
        repo_root=repo_root,
        attestation_commit_sha=attestation_commit_sha,
    )
    if isinstance(attestations, AttestationInventory) and attestations.canonical_attestations:
        raise ManifestError(
            "ACCEPT_FREE_READINESS/future acceptance gate must verify GitHub "
            "review authenticity"
        )
    return _F10_INITIAL_STATE_SNAPSHOT


def validate_attestation(
    descriptor: Any,
    attestation: Any,
    *,
    inventory: AttestationInventory | None = None,
    clock: datetime | Callable[[], datetime] | None = None,
    expected_target_fingerprint: str | None = None,
    repo_root: str | Path | None = None,
    attestation_commit_sha: str | None = None,
) -> str:
    """Validate one new attestation in the context of its immutable prefix."""

    if clock is None:
        raise ManifestError("new attestation validation requires an injected UTC clock")
    if not isinstance(inventory, AttestationInventory):
        raise ManifestError("new attestation validation requires complete inventory")
    objects = inventory.objects()
    if not objects or canonical_json_bytes(objects[-1]) != canonical_json_bytes(attestation):
        raise ManifestError("new attestation must be the final inventory entry")
    return derive_effective_state(
        descriptor,
        inventory,
        clock=clock,
        expected_target_fingerprint=expected_target_fingerprint,
        repo_root=repo_root,
        attestation_commit_sha=attestation_commit_sha,
    )


def canonical_sql_sha256(path: Path) -> str:
    """Hash SQL with CRLF normalized to the repository's canonical LF form."""

    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


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
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ManifestError(f"duplicate migration manifest key: {key}")
            result[key] = value
        return result

    try:
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
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
    required_status: str | tuple[str, ...] | None = None,
) -> list[Path]:
    """Return checksum-verified migration paths for one target."""

    target = target.lower()
    if target not in _ALLOWED_TARGETS_SNAPSHOT:
        raise ManifestError(f"unsupported migration target: {target}")

    manifest = _read_json(Path(manifest_path))
    entries = manifest.get("entries")
    has_f9_5_successor = isinstance(entries, list) and any(
        isinstance(entry, dict) and entry.get("path") == F9_5_SUCCESSOR_PATH
        for entry in entries
    )
    if manifest.get("package_id") == F9_5_PACKAGE_ID or has_f9_5_successor:
        canonical_manifest = json.dumps(
            manifest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if not hmac.compare_digest(
            hashlib.sha256(canonical_manifest).hexdigest(),
            F9_5_MANIFEST_SHA256,
        ):
            raise ManifestError(
                "F9.5 migration manifest does not match exact contract"
            )
    contract_key = (
        manifest.get("schema_version"),
        manifest.get("phase"),
        manifest.get("package_id"),
    )
    contract = _MANIFEST_CONTRACTS_SNAPSHOT.get(contract_key)
    if contract is None:
        raise ManifestError("unsupported migration manifest contract")
    status = manifest.get("status")
    if status not in _ALLOWED_STATUSES_SNAPSHOT:
        raise ManifestError("unsupported migration package status")
    if required_status is not None:
        required_statuses = (
            (required_status,) if isinstance(required_status, str) else required_status
        )
        if status not in required_statuses:
            expected = " or ".join(required_statuses)
            raise ManifestError(
                f"migration package status is {status}; required {expected}"
            )
    expected_exclusions = contract.get("excluded", {
        "H-00": "historical_free_only",
        "canary": "observed_effective_unledgered",
        "historical_snapshots": "superseded",
    })
    if manifest.get("excluded") != expected_exclusions:
        raise ManifestError("migration package exclusions are incomplete")
    blocked_targets_by_status = contract["blocked_targets_by_status"]
    if blocked_targets_by_status is None:
        if manifest.get("blocked_targets") is not None:
            raise ManifestError("migration package target blocks are unsupported")
    else:
        expected_blocks = blocked_targets_by_status[status]
        if manifest.get("blocked_targets") != list(expected_blocks):
            raise ManifestError(
                "migration package target blocks do not match its status"
            )
        if required_status is not None and target in expected_blocks:
            raise ManifestError(f"migration target {target} remains blocked")
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
    exact_entries = contract.get("exact_entries")
    if exact_entries is not None:
        actual_entries = tuple(
            (
                entry.get("id"), entry.get("component"), entry.get("path"),
                entry.get("sha256"), entry.get("provenance"),
                tuple(entry.get("targets", ())),
            )
            if isinstance(entry, dict) else None
            for entry in entries
        )
        if actual_entries != exact_entries:
            raise ManifestError("migration package entries do not match exact contract")

    migration_root = (root / "db" / "migrations").resolve()
    resolved: list[Path] = []
    stems: set[str] = set()
    ids: set[str] = set()
    components: set[str] = set()
    component_counts: dict[str, int] = {}
    component_order: list[str] = []

    for entry in entries:
        if not isinstance(entry, dict):
            raise ManifestError("migration manifest entry must be an object")
        entry_targets = entry.get("targets")
        if not isinstance(entry_targets, list) or not entry_targets:
            raise ManifestError("migration entry requires explicit targets")
        if any(item not in _ALLOWED_TARGETS_SNAPSHOT for item in entry_targets):
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
        if provenance not in _ALLOWED_PROVENANCE_SNAPSHOT:
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
        if not MIGRATION_FILENAME_RE.fullmatch(candidate.name):
            raise ManifestError("migration filename contains unsafe characters")
        if not candidate.stem.casefold().startswith(contract["stem_prefixes"]):
            raise ManifestError("historical or non-package migration stem is forbidden")
        component_prefix = contract["component_prefixes"].get(component)
        if component_prefix is None or not candidate.stem.casefold().startswith(
            component_prefix
        ):
            raise ManifestError("migration component uses the wrong phase prefix")

        stem = candidate.stem.casefold()
        if stem in stems or entry_id in ids:
            raise ManifestError("duplicate migration stem or ID")
        stems.add(stem)
        ids.add(entry_id)
        component_order.append(component)

        if canonical_sql_sha256(candidate) != expected_hash:
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
    expected_order = list(contract["component_order"])
    if target in _ALLOWED_TARGETS_SNAPSHOT and (
        component_order != expected_order
        or components != set(expected_order)
        or component_counts != contract["component_counts"]
    ):
        raise ManifestError(
            "migration package must contain its components exactly and in order"
        )
    return resolved
