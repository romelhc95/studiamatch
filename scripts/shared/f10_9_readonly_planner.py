from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import stat
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.shared.url_identity import URL_IDENTITY_VERSION, build_url_identity


INPUT_SCHEMA = "f10.9-p2-readonly-input.v1"
MANIFEST_SCHEMA = "f10.9-p2-readonly-manifest.v1"
MAX_INPUT_BYTES = 2_000_000
MAX_ROWS = 20_000
MAX_NODES = 200_000
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_STAGING_STATUSES = frozenset(
    {"discovered", "pending", "processing", "processed", "discarded", "skipped", "error"}
)
_DISCOVERY_MODES = frozenset(
    {"hardcoded_urls", "sitemap_bfs", "paginated_catalog", "catalog_link_extraction"}
)
_SOURCE_OUTCOMES = frozenset({"ACCESSIBLE", "SOURCE_ACCESS_403", "SOURCE_TIMEOUT"})
_MUTATION_KINDS = frozenset({"FIRST_404_FLAG", "DEACTIVATE"})
_MUTATION_OUTCOMES = frozenset({"HTTP_2XX", "HTTP_404", "HTTP_410", "INCONCLUSIVE"})
_TOP_LEVEL_KEYS = frozenset(
    {
        "schema",
        "observed_at",
        "normalization_version",
        "stale_after_seconds",
        "page_size",
        "metadata_placeholders",
        "provenance",
        "staging_raw",
        "downstream_references",
        "profiles",
        "source_access",
        "courses",
        "prior_mutation_checks",
    }
)
_PROVENANCE_KEYS = frozenset(
    {
        "source_kind",
        "environment",
        "run_id",
        "base_sha",
        "base_tree",
        "expires_at",
        "required_approver",
    }
)
_P2_PATHS = (
    "scripts/maintenance/f10_9_readonly_audit.py",
    "scripts/shared/f10_9_readonly_planner.py",
    "tests/fixtures/f10_9_p2_synthetic.json",
    "tests/test_fase10_9_p2_readonly_planners.py",
)
_ROW_CONTRACTS = {
    "staging_raw": {
        "id": "opaque_id",
        "institution_id": "opaque_id",
        "url": "string",
        "status": "staging_status_enum",
        "payload": "nullable_string",
        "content_hash": "nullable_sha256",
        "processing_since": "nullable_utc_timestamp",
        "created_at": "nullable_utc_timestamp",
    },
    "downstream_references": {
        "id": "opaque_id",
        "staging_id": "staging_reference",
        "institution_id": "opaque_id",
        "url": "string",
        "lineage_id": "opaque_id",
        "valid": "boolean",
    },
    "profiles": {
        "institution_id": "opaque_id",
        "discovery_enabled": "boolean",
        "pipeline_enabled": "boolean",
        "discovery_mode": "discovery_mode_enum",
        "seed_urls": "string_list",
        "catalog_url_patterns": "pattern_list",
        "allowed_url_patterns": "pattern_list",
    },
    "source_access": {
        "id": "opaque_id",
        "institution_id": "profile_reference",
        "outcome": "source_outcome_enum",
    },
    "courses": {
        "id": "opaque_id",
        "institution_id": "opaque_id",
        "url": "string",
        "is_active": "boolean",
        "syllabus": "nullable_string",
        "objectives": "nullable_string",
        "last_404_at": "nullable_utc_timestamp",
    },
    "prior_mutation_checks": {
        "id": "opaque_id",
        "course_id": "course_reference",
        "run_id": "provenance_run_reference",
        "mutation_kind": "mutation_kind_enum",
        "observed_outcome": "mutation_outcome_enum",
    },
}
_FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


class PlannerInputError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID") from exc


def fingerprint(value: object, *, domain: str = "manifest") -> str:
    payload = f"studiamatch:f10.9:p2:{domain}:v1\0{canonical_json(value)}"
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _reject_constant(_value: str) -> None:
    raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")


def _object_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PlannerInputError("P2_INPUT_DUPLICATE_KEY")
        result[key] = value
    return result


def _preflight_limits(value: object) -> None:
    stack = [value]
    nodes = 0
    characters = 0
    while stack:
        current = stack.pop()
        nodes += 1
        if nodes > MAX_NODES:
            raise PlannerInputError("P2_INPUT_LIMIT_EXCEEDED")
        if isinstance(current, str):
            characters += len(current)
            if characters > MAX_INPUT_BYTES:
                raise PlannerInputError("P2_INPUT_LIMIT_EXCEEDED")
        elif isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def _safe_fixture_path(path: Path) -> Path:
    raw = str(path)
    if (
        not raw
        or "\x00" in raw
        or "://" in raw
        or raw.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\"))
    ):
        raise PlannerInputError("P2_INPUT_FILE_UNAVAILABLE")
    fixture_root = _FIXTURE_ROOT.absolute()
    candidate = path if path.is_absolute() else Path.cwd() / path
    candidate = candidate.absolute()
    if candidate.parent != fixture_root or candidate.name in {"", ".", ".."}:
        raise PlannerInputError("P2_INPUT_FILE_UNAVAILABLE")
    return candidate


def _read_bounded_regular_file(path: Path) -> bytes:
    if not getattr(os, "O_NOFOLLOW", 0):
        raise PlannerInputError("P2_INPUT_PLATFORM_UNSUPPORTED")
    candidate = _safe_fixture_path(path)
    try:
        link_metadata = os.lstat(candidate)
    except OSError as exc:
        raise PlannerInputError("P2_INPUT_FILE_UNAVAILABLE") from exc
    if stat.S_ISLNK(link_metadata.st_mode) or not stat.S_ISREG(link_metadata.st_mode):
        raise PlannerInputError("P2_INPUT_FILE_UNAVAILABLE")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise PlannerInputError("P2_INPUT_FILE_UNAVAILABLE") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_INPUT_BYTES:
            raise PlannerInputError("P2_INPUT_LIMIT_EXCEEDED")
        chunks: list[bytes] = []
        remaining = MAX_INPUT_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > MAX_INPUT_BYTES:
            raise PlannerInputError("P2_INPUT_LIMIT_EXCEEDED")
        return raw
    finally:
        os.close(descriptor)


def load_snapshot(path: Path, *, now: datetime | None = None) -> dict[str, object]:
    raw = _read_bounded_regular_file(path)
    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except PlannerInputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlannerInputError("P2_INPUT_JSON_INVALID") from exc
    validated = _validate_snapshot(parsed)
    if now is not None:
        if now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
            raise PlannerInputError("P2_INPUT_TIMESTAMP_INVALID")
        expires_at = _parse_timestamp(validated["provenance"]["expires_at"])
        assert expires_at is not None
        if expires_at <= now:
            raise PlannerInputError("P2_INPUT_EXPIRED")
    return validated


def _require_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    return value


def _require_exact_keys(row: Mapping[str, object], expected: set[str] | frozenset[str]) -> None:
    if set(row) != set(expected):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")


def _require_string(value: object, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    if len(value) > MAX_INPUT_BYTES:
        raise PlannerInputError("P2_INPUT_LIMIT_EXCEEDED")
    return value


def _require_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    return value


def _require_int(value: object, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    if not minimum <= value <= maximum:
        raise PlannerInputError("P2_INPUT_LIMIT_EXCEEDED")
    return value


def _require_id(value: object) -> str:
    candidate = _require_string(value)
    if not candidate or not _ID_RE.fullmatch(candidate):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    return candidate


def _parse_timestamp(value: object, *, nullable: bool = False) -> datetime | None:
    candidate = _require_string(value, nullable=nullable)
    if candidate is None:
        return None
    if not candidate.endswith("Z"):
        raise PlannerInputError("P2_INPUT_TIMESTAMP_INVALID")
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00")
    except ValueError as exc:
        raise PlannerInputError("P2_INPUT_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise PlannerInputError("P2_INPUT_TIMESTAMP_INVALID")
    return parsed


def _require_string_list(value: object) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    return list(value)


def _validate_rows(
    value: object,
    *,
    keys: set[str],
    id_key: str,
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in value:
        row = _require_object(item)
        _require_exact_keys(row, keys)
        row_id = _require_id(row[id_key])
        if row_id in seen:
            raise PlannerInputError("P2_INPUT_DUPLICATE_ID")
        seen.add(row_id)
        rows.append(copy.deepcopy(row))
    return sorted(rows, key=lambda row: str(row[id_key]))


def _validate_snapshot(value: object) -> dict[str, object]:
    _preflight_limits(value)
    root = _require_object(value)
    _require_exact_keys(root, _TOP_LEVEL_KEYS)
    if root["schema"] != INPUT_SCHEMA or root["normalization_version"] != URL_IDENTITY_VERSION:
        raise PlannerInputError("P2_INPUT_VERSION_UNSUPPORTED")
    _parse_timestamp(root["observed_at"])
    _require_int(root["stale_after_seconds"], minimum=1, maximum=31_536_000)
    _require_int(root["page_size"], minimum=1, maximum=1000)

    placeholders = _require_string_list(root["metadata_placeholders"])
    normalized_placeholders = [_normalize_text(item) for item in placeholders]
    if any(not item for item in normalized_placeholders) or len(set(normalized_placeholders)) != len(placeholders):
        raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")

    provenance = _require_object(root["provenance"])
    _require_exact_keys(provenance, _PROVENANCE_KEYS)
    for key in ("source_kind", "environment", "run_id", "required_approver"):
        if not _require_string(provenance[key]) or not str(provenance[key]).strip():
            raise PlannerInputError("P2_INPUT_SCHEMA_INVALID")
    if (
        provenance["source_kind"] != "SYNTHETIC_FIXTURE"
        or provenance["environment"] != "LOCAL_OFFLINE"
        or provenance["required_approver"] != "HUMAN_REVIEW_REQUIRED"
        or not _ID_RE.fullmatch(str(provenance["run_id"]))
    ):
        raise PlannerInputError("P2_INPUT_PROVENANCE_INVALID")
    for key in ("base_sha", "base_tree"):
        if not _GIT_SHA_RE.fullmatch(str(_require_string(provenance[key]))):
            raise PlannerInputError("P2_INPUT_HASH_INVALID")
    expires_at = _parse_timestamp(provenance["expires_at"])
    observed_at = _parse_timestamp(root["observed_at"])
    assert expires_at is not None and observed_at is not None
    if expires_at <= observed_at:
        raise PlannerInputError("P2_INPUT_TIMESTAMP_INVALID")

    staging = _validate_rows(
        root["staging_raw"],
        keys={
            "id",
            "institution_id",
            "url",
            "status",
            "payload",
            "content_hash",
            "processing_since",
            "created_at",
        },
        id_key="id",
    )
    if not staging:
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")
    for row in staging:
        _require_id(row["institution_id"])
        _require_string(row["url"])
        if row["status"] not in _STAGING_STATUSES:
            raise PlannerInputError("P2_INPUT_STATUS_INVALID")
        _require_string(row["payload"], nullable=True)
        content_hash = _require_string(row["content_hash"], nullable=True)
        if content_hash is not None and not _HASH_RE.fullmatch(content_hash):
            raise PlannerInputError("P2_INPUT_HASH_INVALID")
        _parse_timestamp(row["processing_since"], nullable=True)
        created_at = _parse_timestamp(row["created_at"], nullable=True)
        if created_at is not None and created_at > observed_at:
            raise PlannerInputError("P2_INPUT_TIMESTAMP_INVALID")

    downstream = _validate_rows(
        root["downstream_references"],
        keys={"id", "staging_id", "institution_id", "url", "lineage_id", "valid"},
        id_key="id",
    )
    staging_ids = {str(row["id"]) for row in staging}
    for row in downstream:
        if _require_id(row["staging_id"]) not in staging_ids:
            raise PlannerInputError("P2_INPUT_REFERENCE_INVALID")
        _require_id(row["institution_id"])
        _require_id(row["lineage_id"])
        _require_string(row["url"])
        _require_bool(row["valid"])

    profiles = _validate_rows(
        root["profiles"],
        keys={
            "institution_id",
            "discovery_enabled",
            "pipeline_enabled",
            "discovery_mode",
            "seed_urls",
            "catalog_url_patterns",
            "allowed_url_patterns",
        },
        id_key="institution_id",
    )
    if not profiles:
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")
    for row in profiles:
        _require_bool(row["discovery_enabled"])
        _require_bool(row["pipeline_enabled"])
        if row["discovery_mode"] not in _DISCOVERY_MODES:
            raise PlannerInputError("P2_INPUT_PROFILE_INVALID")
        seed_urls = _require_string_list(row["seed_urls"])
        catalog_patterns = _require_string_list(row["catalog_url_patterns"])
        allowed_patterns = _require_string_list(row["allowed_url_patterns"])
        if any(not _usable_identity(seed)[1] for seed in seed_urls):
            raise PlannerInputError("P2_INPUT_PROFILE_INVALID")
        _validate_catalog_templates(catalog_patterns)
        _validate_patterns(allowed_patterns)

    source_access = _validate_rows(
        root["source_access"],
        keys={"id", "institution_id", "outcome"},
        id_key="id",
    )
    if not source_access:
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")
    for row in source_access:
        _require_id(row["institution_id"])
        if row["outcome"] not in _SOURCE_OUTCOMES:
            raise PlannerInputError("P2_INPUT_SOURCE_OUTCOME_INVALID")

    courses = _validate_rows(
        root["courses"],
        keys={"id", "institution_id", "url", "is_active", "syllabus", "objectives", "last_404_at"},
        id_key="id",
    )
    if not courses:
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")
    for row in courses:
        _require_id(row["institution_id"])
        _require_string(row["url"])
        _require_bool(row["is_active"])
        _require_string(row["syllabus"], nullable=True)
        _require_string(row["objectives"], nullable=True)
        last_404_at = _parse_timestamp(row["last_404_at"], nullable=True)
        if last_404_at is not None and last_404_at > observed_at:
            raise PlannerInputError("P2_INPUT_TIMESTAMP_INVALID")

    prior = _validate_rows(
        root["prior_mutation_checks"],
        keys={"id", "course_id", "run_id", "mutation_kind", "observed_outcome"},
        id_key="id",
    )
    if not prior:
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")
    course_ids = {str(row["id"]) for row in courses}
    for row in prior:
        if _require_id(row["course_id"]) not in course_ids:
            raise PlannerInputError("P2_INPUT_REFERENCE_INVALID")
        if row["run_id"] != provenance["run_id"]:
            raise PlannerInputError("P2_INPUT_PROVENANCE_INVALID")
        if row["mutation_kind"] not in _MUTATION_KINDS or row["observed_outcome"] not in _MUTATION_OUTCOMES:
            raise PlannerInputError("P2_INPUT_MUTATION_OUTCOME_INVALID")

    total_rows = sum(len(rows) for rows in (staging, downstream, profiles, source_access, courses, prior))
    if total_rows > MAX_ROWS:
        raise PlannerInputError("P2_INPUT_LIMIT_EXCEEDED")
    enabled_institutions = {
        str(row["institution_id"])
        for row in profiles
        if row["discovery_enabled"] or row["pipeline_enabled"]
    }
    source_institution_counts = Counter(str(row["institution_id"]) for row in source_access)
    source_institutions = set(source_institution_counts)
    if any(source_institution_counts[institution_id] != 1 for institution_id in enabled_institutions):
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")
    if not source_institutions.issubset({str(row["institution_id"]) for row in profiles}):
        raise PlannerInputError("P2_INPUT_REFERENCE_INVALID")
    profile_institutions = {str(row["institution_id"]) for row in profiles}
    referenced_institutions = {
        str(row["institution_id"])
        for rows in (staging, downstream, courses)
        for row in rows
    }
    if not referenced_institutions.issubset(profile_institutions):
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")

    mutation_keys: set[tuple[str, str]] = set()
    mutation_kinds = Counter(str(row["mutation_kind"]) for row in prior)
    for row in prior:
        key = (str(row["course_id"]), str(row["mutation_kind"]))
        if key in mutation_keys:
            raise PlannerInputError("P2_INPUT_DUPLICATE_ID")
        mutation_keys.add(key)
    if mutation_kinds != Counter({"FIRST_404_FLAG": 2, "DEACTIVATE": 1}):
        raise PlannerInputError("P2_INPUT_COVERAGE_INCOMPLETE")

    return {
        "schema": INPUT_SCHEMA,
        "observed_at": root["observed_at"],
        "normalization_version": URL_IDENTITY_VERSION,
        "stale_after_seconds": root["stale_after_seconds"],
        "page_size": root["page_size"],
        "metadata_placeholders": placeholders,
        "provenance": copy.deepcopy(provenance),
        "staging_raw": staging,
        "downstream_references": downstream,
        "profiles": profiles,
        "source_access": source_access,
        "courses": courses,
        "prior_mutation_checks": prior,
    }


def _normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


def _validate_patterns(patterns: list[str]) -> None:
    for pattern in patterns:
        if len(pattern) > 200:
            raise PlannerInputError("P2_INPUT_PROFILE_INVALID")
        if not pattern.startswith("re:"):
            continue
        expression = pattern[3:]
        if (
            not expression
            or "(?" in expression
            or re.search(r"\\[1-9]", expression)
            or re.search(r"(?:\*|\+|\{\d+,?\d*\})(?:\s*)(?:\*|\+|\{)", expression)
            or re.search(r"\([^)]*(?:\*|\+|\{\d+,?\d*\})[^)]*\)(?:\*|\+|\{)", expression)
        ):
            raise PlannerInputError("P2_INPUT_PROFILE_INVALID")
        try:
            re.compile(expression)
        except re.error as exc:
            raise PlannerInputError("P2_INPUT_PROFILE_INVALID") from exc


def _validate_catalog_templates(patterns: list[str]) -> None:
    for pattern in patterns:
        if (
            len(pattern) > 200
            or pattern.count("{page}") != 1
            or "{" in pattern.replace("{page}", "")
            or "}" in pattern.replace("{page}", "")
            or not _usable_identity(pattern.replace("{page}", "1"))[1]
        ):
            raise PlannerInputError("P2_INPUT_PROFILE_INVALID")


def _payload_state(row: Mapping[str, object]) -> tuple[bool, bool]:
    payload = row["payload"]
    content_hash = row["content_hash"]
    if payload is None and content_hash is None:
        return False, False
    if not isinstance(payload, str) or not payload.strip() or not isinstance(content_hash, str):
        return False, True
    calculated = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return calculated == content_hash, calculated != content_hash


def _usable_identity(url: object) -> tuple[str, bool]:
    identity = build_url_identity(str(url))
    usable = bool(identity.canonical_url) and not identity.canonical_url.startswith("urn:")
    return identity.dedupe_key, usable


def _dependency_state(
    row: Mapping[str, object],
    references: list[Mapping[str, object]],
) -> tuple[bool, bool]:
    if not references:
        return False, False
    row_identity, row_usable = _usable_identity(row["url"])
    lineages: set[str] = set()
    for reference in references:
        reference_identity, reference_usable = _usable_identity(reference["url"])
        if (
            not bool(reference["valid"])
            or not row_usable
            or not reference_usable
            or reference_identity != row_identity
            or reference["institution_id"] != row["institution_id"]
        ):
            return True, False
        lineages.add(str(reference["lineage_id"]))
    return len(references) != 1 or len(lineages) != 1, len(references) == 1 and len(lineages) == 1


def _opaque_entity(kind: str, row_id: object, cohort_context: str) -> str:
    return fingerprint(
        {"cohort_context": cohort_context, "kind": kind, "id": str(row_id)},
        domain="entity",
    )


def _iter_pages(rows: list[dict[str, object]], page_size: int):
    for offset in range(0, len(rows), page_size):
        yield rows[offset : offset + page_size]


def _pagination_manifest(rows: list[dict[str, object]], page_size: int) -> dict[str, object]:
    page_count = 0
    processed_rows = 0
    for page in _iter_pages(rows, page_size):
        page_count += 1
        processed_rows += len(page)
    if processed_rows != len(rows):
        raise PlannerInputError("P2_PAGINATION_INCOMPLETE")
    return {
        "rows": len(rows),
        "pages_processed": page_count,
        "cohort_fingerprint": fingerprint(rows, domain="cohort"),
    }


def build_readonly_manifest(
    snapshot: Mapping[str, object],
    *,
    page_size: int | None = None,
) -> dict[str, object]:
    normalized = _validate_snapshot(dict(snapshot))
    effective_page_size = normalized["page_size"] if page_size is None else page_size
    effective_page_size = _require_int(effective_page_size, minimum=1, maximum=1000)
    observed_at = _parse_timestamp(normalized["observed_at"])
    assert observed_at is not None
    stale_after = int(normalized["stale_after_seconds"])
    staging = list(normalized["staging_raw"])
    downstream = list(normalized["downstream_references"])
    profiles = list(normalized["profiles"])
    source_access = list(normalized["source_access"])
    courses = list(normalized["courses"])
    prior = list(normalized["prior_mutation_checks"])
    input_cohort_fingerprint = fingerprint(normalized, domain="input")

    references_by_staging: dict[str, list[dict[str, object]]] = defaultdict(list)
    for page in _iter_pages(downstream, effective_page_size):
        for reference in page:
            references_by_staging[str(reference["staging_id"])].append(reference)

    reason_counts: Counter[str] = Counter()
    evidence_holds: Counter[str] = Counter()
    lifecycle_counts: Counter[str] = Counter()
    lifecycle_stale = 0
    identities: dict[str, list[dict[str, object]]] = defaultdict(list)
    row_evidence: dict[str, dict[str, object]] = {}

    for page in _iter_pages(staging, effective_page_size):
        for row in page:
            row_id = str(row["id"])
            identity, usable = _usable_identity(row["url"])
            payload_valid, contradictory_payload = _payload_state(row)
            dependency_conflict, coherent_downstream = _dependency_state(
                row,
                references_by_staging[row_id],
            )
            row_evidence[row_id] = {
                "payload_valid": payload_valid,
                "contradictory_payload": contradictory_payload,
                "dependency_conflict": dependency_conflict,
                "coherent_downstream": coherent_downstream,
            }
            if usable:
                identities[identity].append(row)
            else:
                reason_counts["INVALID_URL_IDENTITY"] += 1
            if contradictory_payload:
                reason_counts["CONFLICTING_CONTENT_HASH"] += 1
                evidence_holds["PAYLOAD_HASH_CONTRADICTION"] += 1
                evidence_holds["HOLD_MANUAL"] += 1
            if dependency_conflict:
                reason_counts["DOWNSTREAM_REFERENCE_CONFLICT"] += 1

            if row["status"] in {"discarded", "error", "skipped"}:
                reason_counts["UNRESOLVED_STAGING_STATUS"] += 1
                evidence_holds["HOLD_MANUAL"] += 1
                continue
            if row["status"] != "processing":
                continue
            processing_since = _parse_timestamp(row["processing_since"], nullable=True)
            if processing_since is None:
                reason_counts["PROCESSING_AGE_UNKNOWN"] += 1
                lifecycle_counts["HOLD_MANUAL"] += 1
                evidence_holds["HOLD_MANUAL"] += 1
                continue
            age_seconds = (observed_at - processing_since).total_seconds()
            if age_seconds < 0:
                reason_counts["PROCESSING_TIME_IN_FUTURE"] += 1
                lifecycle_counts["HOLD_MANUAL"] += 1
                evidence_holds["HOLD_MANUAL"] += 1
                continue
            if age_seconds <= stale_after:
                reason_counts["ACTIVE_PROCESSING"] += 1
                evidence_holds["HOLD_MANUAL"] += 1
                continue
            lifecycle_stale += 1
            reason_counts["STALE_PROCESSING"] += 1
            if dependency_conflict:
                lifecycle_counts["HOLD_DEPENDENCY_CONFLICT"] += 1
            elif contradictory_payload:
                lifecycle_counts["HOLD_MANUAL"] += 1
            elif coherent_downstream:
                lifecycle_counts["CANDIDATE_PROCESSED"] += 1
            elif payload_valid:
                lifecycle_counts["CANDIDATE_PENDING"] += 1
            else:
                lifecycle_counts["CANDIDATE_DISCOVERED"] += 1

    duplicate_results: list[dict[str, object]] = []
    dedupe_counts: Counter[str] = Counter()
    for identity, rows in sorted(identities.items()):
        if len(rows) < 2:
            continue
        reason_counts["DUPLICATE_NORMALIZED_URL"] += 1
        dedupe_counts["duplicate_groups"] += 1
        dedupe_counts["excess_rows"] += len(rows) - 1
        valid_hashes = {
            str(row["content_hash"])
            for row in rows
            if bool(row_evidence[str(row["id"])]["payload_valid"])
        }
        referenced_members = sum(
            bool(row_evidence[str(row["id"])]["coherent_downstream"])
            for row in rows
        )
        dependency_hold = referenced_members > 1 or any(
            bool(row_evidence[str(row["id"])]["dependency_conflict"])
            for row in rows
        )
        contradiction_hold = any(
            bool(row_evidence[str(row["id"])]["contradictory_payload"])
            for row in rows
        )
        institution_hold = len({str(row["institution_id"]) for row in rows}) > 1
        ineligible_status_hold = any(
            str(row["status"]) not in {"processed", "pending", "discovered"}
            for row in rows
        )
        group_fingerprint = fingerprint(
            {
                "cohort_context": input_cohort_fingerprint,
                "members": sorted(str(row["id"]) for row in rows),
                "normalization_version": URL_IDENTITY_VERSION,
            },
            domain="dedupe-group",
        )
        result: dict[str, object] = {
            "group_fingerprint": group_fingerprint,
            "member_count": len(rows),
            "loser_count": 0,
            "decision": "HOLD_MANUAL",
            "survivor_fingerprint": None,
        }
        if contradiction_hold or len(valid_hashes) > 1 or ineligible_status_hold:
            if len(valid_hashes) > 1:
                reason_counts["CONFLICTING_CONTENT_HASH"] += 1
            if ineligible_status_hold:
                reason_counts["INELIGIBLE_SURVIVOR_STATUS"] += 1
            dedupe_counts["hold_manual_groups"] += 1
        elif dependency_hold or institution_hold:
            reason_counts["DOWNSTREAM_REFERENCE_CONFLICT"] += 1
            dedupe_counts["hold_dependency_groups"] += 1
            result["decision"] = "HOLD_DEPENDENCY_CONFLICT"
        else:
            status_rank = {
                "processed": 0,
                "pending": 1,
                "discovered": 2,
                "processing": 3,
                "skipped": 4,
                "error": 5,
                "discarded": 6,
            }

            def rank(row: Mapping[str, object]) -> tuple[object, ...]:
                evidence = row_evidence[str(row["id"])]
                timestamp = _parse_timestamp(row["created_at"], nullable=True)
                return (
                    not bool(evidence["coherent_downstream"]),
                    not bool(evidence["payload_valid"]),
                    status_rank[str(row["status"])],
                    timestamp is None,
                    timestamp or datetime.max.replace(tzinfo=timezone.utc),
                    str(row["id"]),
                )

            survivor = min(rows, key=rank)
            result.update(
                {
                    "decision": "SURVIVOR_IDENTIFIED_READ_ONLY",
                    "loser_count": len(rows) - 1,
                    "survivor_fingerprint": _opaque_entity(
                        "staging",
                        survivor["id"],
                        input_cohort_fingerprint,
                    ),
                }
            )
            dedupe_counts["survivors_identified"] += 1
        duplicate_results.append(result)

    profile_counts: Counter[str] = Counter()
    for page in _iter_pages(profiles, effective_page_size):
        for profile in page:
            enabled = bool(profile["discovery_enabled"] or profile["pipeline_enabled"])
            if not enabled:
                continue
            mode = str(profile["discovery_mode"])
            invalid_hardcoded = mode == "hardcoded_urls" and not profile["seed_urls"]
            invalid_catalog_link = mode == "catalog_link_extraction" and not profile["seed_urls"]
            invalid_paginated = mode == "paginated_catalog" and not profile["catalog_url_patterns"]
            invalid_allowed = mode in {"hardcoded_urls", "sitemap_bfs"} and not profile["allowed_url_patterns"]
            if invalid_hardcoded:
                reason_counts["INVALID_EMPTY_HARDCODED_PROFILE"] += 1
                profile_counts["invalid_enabled_profiles"] += 1
            elif invalid_catalog_link or invalid_paginated or invalid_allowed:
                reason_counts["INVALID_ENABLED_DISCOVERY_PROFILE"] += 1
                profile_counts["invalid_enabled_profiles"] += 1
            else:
                profile_counts["valid_enabled_profiles"] += 1

    source_counts: Counter[str] = Counter()
    for page in _iter_pages(source_access, effective_page_size):
        for observation in page:
            outcome = str(observation["outcome"])
            source_counts[outcome] += 1
            if outcome in {"SOURCE_ACCESS_403", "SOURCE_TIMEOUT"}:
                reason_counts[outcome] += 1

    placeholders = {_normalize_text(item) for item in normalized["metadata_placeholders"]}
    metadata_counts: Counter[str] = Counter()
    for page in _iter_pages(courses, effective_page_size):
        for course in page:
            if not course["is_active"]:
                continue
            metadata_counts["active_courses"] += 1
            syllabus_missing = course["syllabus"] is None or _normalize_text(str(course["syllabus"])) in placeholders | {""}
            objectives_missing = course["objectives"] is None or _normalize_text(str(course["objectives"])) in placeholders | {""}
            if syllabus_missing:
                metadata_counts["missing_syllabus"] += 1
            if objectives_missing:
                metadata_counts["missing_objectives"] += 1
            if syllabus_missing and objectives_missing:
                metadata_counts["missing_both"] += 1
            if syllabus_missing or objectives_missing:
                metadata_counts["incomplete_active_courses"] += 1
    if metadata_counts["incomplete_active_courses"]:
        reason_counts["MISSING_ACTIVE_COURSE_METADATA"] += metadata_counts["incomplete_active_courses"]

    mutation_counts: Counter[str] = Counter()
    courses_by_id = {str(course["id"]): course for course in courses}
    for page in _iter_pages(prior, effective_page_size):
        for check in page:
            outcome = str(check["observed_outcome"])
            course = courses_by_id[str(check["course_id"])]
            state_consistent = (
                check["mutation_kind"] == "FIRST_404_FLAG"
                and bool(course["is_active"])
                and course["last_404_at"] is not None
            ) or (
                check["mutation_kind"] == "DEACTIVATE"
                and not bool(course["is_active"])
                and course["last_404_at"] is not None
            )
            if outcome == "HTTP_2XX":
                mutation_counts["STOP_REQUIRES_REBASELINE"] += 1
                reason_counts["PRIOR_MUTATION_RECOVERY_REQUIRED"] += 1
                if not state_consistent:
                    mutation_counts["HOLD_MANUAL"] += 1
                    reason_counts["PRIOR_MUTATION_STATE_CONFLICT"] += 1
            elif not state_consistent:
                mutation_counts["HOLD_MANUAL"] += 1
                reason_counts["PRIOR_MUTATION_STATE_CONFLICT"] += 1
            elif outcome in {"HTTP_404", "HTTP_410"}:
                mutation_counts["PRESERVE_CONFIRMED_STATE"] += 1
            else:
                mutation_counts["HOLD_MANUAL"] += 1
                reason_counts["PRIOR_MUTATION_INCONCLUSIVE"] += 1

    pagination = {
        name: _pagination_manifest(rows, effective_page_size)
        for name, rows in (
            ("courses", courses),
            ("downstream_references", downstream),
            ("prior_mutation_checks", prior),
            ("profiles", profiles),
            ("source_access", source_access),
            ("staging_raw", staging),
        )
    }
    stop_required = bool(
        mutation_counts["STOP_REQUIRES_REBASELINE"]
        or metadata_counts["incomplete_active_courses"]
    )
    decision = "STOP_REQUIRES_REBASELINE" if stop_required else (
        "FINDINGS_PRESENT" if reason_counts else "PASS_READ_ONLY"
    )
    provenance = dict(normalized["provenance"])
    collection_counts = {
        "courses": len(courses),
        "downstream_references": len(downstream),
        "prior_mutation_checks": len(prior),
        "profiles": len(profiles),
        "source_access": len(source_access),
        "staging_raw": len(staging),
    }
    manifest: dict[str, object] = {
        "schema": MANIFEST_SCHEMA,
        "plan_id": "PLAN-REM-F10.9-001",
        "gate": "G1",
        "package": "P2",
        "mode": "LOCAL_OFFLINE_READ_ONLY",
        "observed_at": normalized["observed_at"],
        "normalization_version": URL_IDENTITY_VERSION,
        "algorithm_version": "f10.9-p2-planner-v1",
        "provenance": {
            "source_kind": provenance["source_kind"],
            "environment": provenance["environment"],
            "run_id": provenance["run_id"],
            "base_sha": provenance["base_sha"],
            "base_tree": provenance["base_tree"],
            "expires_at": provenance["expires_at"],
            "required_approver": provenance["required_approver"],
            "candidate_binding": "UNBOUND_LOCAL_IMPLEMENTATION",
            "candidate_contract": {
                "branch": "feat/f10-9-p2-readonly-planners",
                "direct_parent": provenance["base_sha"],
                "expected_paths": list(_P2_PATHS),
                "expected_status": "A",
                "expected_mode": "100644",
                "candidate_sha": None,
                "candidate_tree": None,
                "diff_digest": None,
            },
        },
        "capabilities": {"apply": False, "database": False, "http": False, "providers": False},
        "input": {
            "schema": INPUT_SCHEMA,
            "cohort_fingerprint": input_cohort_fingerprint,
            "schema_fingerprint": fingerprint(
                {
                    "input": INPUT_SCHEMA,
                    "manifest": MANIFEST_SCHEMA,
                    "normalization": URL_IDENTITY_VERSION,
                    "top_level_keys": sorted(_TOP_LEVEL_KEYS),
                    "provenance_keys": sorted(_PROVENANCE_KEYS),
                    "staging_statuses": sorted(_STAGING_STATUSES),
                    "discovery_modes": sorted(_DISCOVERY_MODES),
                    "source_outcomes": sorted(_SOURCE_OUTCOMES),
                    "mutation_kinds": sorted(_MUTATION_KINDS),
                    "mutation_outcomes": sorted(_MUTATION_OUTCOMES),
                    "row_contracts": _ROW_CONTRACTS,
                    "strict_unknown_keys": True,
                    "strict_scalar_types": True,
                },
                domain="schema",
            ),
            "placeholder_policy_fingerprint": fingerprint(
                sorted(placeholders),
                domain="metadata-placeholders",
            ),
            "profile_dependency_fingerprint": fingerprint(
                {"profiles": profiles, "downstream_references": downstream},
                domain="profile-dependencies",
            ),
        },
        "before_after": {
            name: {"before": count, "after": count, "delta": 0}
            for name, count in sorted(collection_counts.items())
        },
        "pagination": pagination,
        "reason_counts": dict(sorted(reason_counts.items())),
        "evidence_holds": dict(sorted(evidence_holds.items())),
        "lifecycle": {
            "stale_processing": lifecycle_stale,
            "classifications": dict(sorted(lifecycle_counts.items())),
            "planned_transitions": 0,
        },
        "deduplication": {
            **dict(sorted(dedupe_counts.items())),
            "groups": sorted(duplicate_results, key=lambda item: str(item["group_fingerprint"])),
            "planned_mutations": 0,
        },
        "profiles": dict(sorted(profile_counts.items())),
        "source_access": dict(sorted(source_counts.items())),
        "metadata": {
            **dict(sorted(metadata_counts.items())),
            "cohort_fingerprint": fingerprint(
                [
                    _opaque_entity("course", course["id"], input_cohort_fingerprint)
                    for course in courses
                    if course["is_active"]
                    and (
                        course["syllabus"] is None
                        or _normalize_text(str(course["syllabus"])) in placeholders | {""}
                        or course["objectives"] is None
                        or _normalize_text(str(course["objectives"])) in placeholders | {""}
                    )
                ],
                domain="metadata-cohort",
            ),
            "planned_enrichment_calls": 0,
        },
        "prior_mutations": {
            **dict(sorted(mutation_counts.items())),
            "planned_restorations": 0,
        },
        "writes": {"actual": 0, "expected": 0, "planned": 0},
        "decision": {
            "result": decision,
            "next_gate_eligible": False,
            "repeat_semantics": "IDENTICAL_INPUT_NOOP",
        },
    }
    manifest["manifest_fingerprint"] = fingerprint(manifest, domain="result")
    return manifest


__all__ = [
    "INPUT_SCHEMA",
    "MANIFEST_SCHEMA",
    "PlannerInputError",
    "build_readonly_manifest",
    "canonical_json",
    "fingerprint",
    "load_snapshot",
]
