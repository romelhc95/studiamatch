"""Repository-only G5 v2 attribution over private, pre-materialized evidence."""

from __future__ import annotations

import copy
import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .f10_9_readonly_planner import canonical_json
from .url_identity import URL_IDENTITY_VERSION, build_url_identity


LEGACY_SCHEMA_V1 = "f10.9-g5-production-readonly-projection.v1"
LEGACY_ALGORITHM_VERSION_V1 = "f10.9-g5-production-readonly-v1"
SCHEMA_V1 = LEGACY_SCHEMA_V1
ALGORITHM_VERSION_V1 = LEGACY_ALGORITHM_VERSION_V1
SCHEMA = "f10.9-g5-production-readonly-projection.v2"
ALGORITHM_VERSION = "f10.9-g5-production-readonly-v2"
GATE = "APPROVE_F10_9_G5_PRODUCTION_READONLY_DIAGNOSTIC_V1"
GATE_CANDIDATE_STATUS = "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
DEFAULT_PAGE_SIZE = 1000
DEFAULT_MAX_ROWS_PER_TABLE = 50_000
DEFAULT_MAX_SNAPSHOT_BYTES = 32_000_000
STOP_SNAPSHOT_DRIFT = "STOP_G5_SNAPSHOT_DRIFT"
SNAPSHOT_DECLARATION = "DOUBLE_READ_STABILITY_NOT_SINGLE_POSTGRES_TRANSACTION"
EXCLUDED_SURFACES = frozenset(
    {
        "SYLLABUS",
        "OBJECTIVES",
        "METADATA",
        "PROVIDERS",
        "EDITORIAL_LINEAGE",
        "H2_CA2",
        "SQL",
        "DDL",
        "DML",
        "RPC",
        "WORKERS",
        "SCHEDULES",
    }
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_STALE_AFTER = timedelta(days=7)
_TABLES = {
    "institutions": "id,name,slug,website_url,last_harvest_at",
    "institution_site_profiles": (
        "id,institution_id,discovery_enabled,pipeline_enabled,pipeline_ready,"
        "discovery_mode,seed_urls,catalog_url_patterns,allowed_url_patterns,"
        "circuit_open,circuit_opened_at"
    ),
    "staging_raw": (
        "id,institution_id,url,status,content_hash,last_harvested_at,created_at"
    ),
    "cleansed_programs": "id,staging_id,institution_id,url",
    "enriched_programs": "id,cleansed_id,institution_id,url",
    "courses": "id,institution_id,url,is_active,last_404_at,start_date",
}
_TABLE_KEYS = {
    table: frozenset(columns.split(",")) for table, columns in _TABLES.items()
}
_STAGING_STATUSES = frozenset(
    {"discovered", "pending", "processing", "processed", "discarded", "skipped", "error"}
)
_DISCOVERY_MODES = frozenset(
    {"hardcoded_urls", "catalog_link_extraction", "paginated_catalog", "sitemap_bfs"}
)
_INVENTORY_CODES = frozenset(
    {"INVENTORY_OK", "INVENTORY_QUERY_FAILED", "INVENTORY_INCOMPLETE"}
)
_SOURCE_CODES = frozenset(
    {
        "SOURCE_ACCESSIBLE",
        "SOURCE_GET_403",
        "SOURCE_TIMEOUT",
        "SOURCE_DNS_FAILURE",
        "SOURCE_TLS_FAILURE",
        "SOURCE_TRANSPORT_FAILURE",
    }
)
_FG3_CLASSIFICATIONS = frozenset(
    {
        "HEALTHY",
        "GET_404",
        "GET_410",
        "GET_403",
        "TIMEOUT",
        "DNS_FAILURE",
        "TLS_FAILURE",
        "TRANSPORT_FAILURE",
    }
)
_FG3_INCONCLUSIVE = frozenset(
    {"GET_403", "TIMEOUT", "DNS_FAILURE", "TLS_FAILURE", "TRANSPORT_FAILURE"}
)
_LIFECYCLE_CLASSES = frozenset(
    {"STALE", "NOT_STALE", "AGE_UNKNOWN", "FUTURE_TIMESTAMP"}
)
_TIMESTAMP_ORIGINS = frozenset(
    {"LAST_HARVESTED_AT_PROXY", "CREATED_AT_PROXY", "NONE"}
)
_MUTATION_KINDS = frozenset(
    {
        "NONE",
        "FIRST_GET_404",
        "FIRST_GET_410",
        "DEACTIVATE_PERSISTENT_GONE",
        "RECOVER",
    }
)
_APPLY_OUTCOMES = frozenset({"NOT_APPLIED_READ_ONLY", "APPLIED_PRIOR_EXACT_ONE"})

# These definitions are the complete public vocabulary. Adding a public count
# requires adding a unit and denominator here first.
REASON_DEFINITIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "STOP_G5_SNAPSHOT_DRIFT": ("snapshot_pairs", "snapshot_pairs"),
        "INVENTORY_OK": ("profiles", "enabled_profiles"),
        "INVENTORY_QUERY_FAILED": ("profiles", "enabled_profiles"),
        "INVENTORY_INCOMPLETE": ("profiles", "enabled_profiles"),
        "SOURCE_ACCESSIBLE": ("source_observations", "enabled_profiles"),
        "SOURCE_GET_403": ("source_observations", "enabled_profiles"),
        "SOURCE_TIMEOUT": ("source_observations", "enabled_profiles"),
        "SOURCE_DNS_FAILURE": ("source_observations", "enabled_profiles"),
        "SOURCE_TLS_FAILURE": ("source_observations", "enabled_profiles"),
        "SOURCE_TRANSPORT_FAILURE": ("source_observations", "enabled_profiles"),
        "CONTENT_HASH_INVALID": ("staging_rows", "hash_evidence_targets"),
        "INVALID_URL_IDENTITY": ("staging_rows", "staging_rows"),
        "UNKNOWN_STAGING_STATUS": ("staging_rows", "staging_rows"),
        "INCOMPLETE_CONTENT_EVIDENCE": ("staging_rows", "hash_evidence_targets"),
        "PROCESSING_AGE_UNKNOWN": ("staging_rows", "processing_rows"),
        "PROCESSING_FUTURE_TIMESTAMP": ("staging_rows", "processing_rows"),
        "PROCESSING_STALE": ("staging_rows", "processing_rows"),
        "DUPLICATE_NORMALIZED_URL": ("groups", "normalized_url_groups"),
        "CONFLICTING_CONTENT_HASH": ("groups", "duplicate_groups"),
        "DOWNSTREAM_REFERENCE_CONFLICT": ("references", "downstream_references"),
        "INVALID_EMPTY_HARDCODED_PROFILE": ("profiles", "enabled_profiles"),
        "INVALID_ENABLED_DISCOVERY_PROFILE": ("profiles", "enabled_profiles"),
        "FG3_GET_403": ("courses", "fg3_evaluated_courses"),
        "FG3_TIMEOUT": ("courses", "fg3_evaluated_courses"),
        "FG3_DNS_FAILURE": ("courses", "fg3_evaluated_courses"),
        "FG3_TLS_FAILURE": ("courses", "fg3_evaluated_courses"),
        "FG3_TRANSPORT_FAILURE": ("courses", "fg3_evaluated_courses"),
    }
)
AGGREGATE_DEFINITIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "duplicate_groups": ("groups", "normalized_url_groups"),
        "duplicate_excess_rows": ("staging_rows", "staging_rows"),
        "conflicting_hash_groups": ("groups", "duplicate_groups"),
        "downstream_reference_conflicts": ("references", "downstream_references"),
        "processing_stale": ("staging_rows", "processing_rows"),
        "processing_not_stale": ("staging_rows", "processing_rows"),
        "processing_age_unknown": ("staging_rows", "processing_rows"),
        "processing_future_timestamp": ("staging_rows", "processing_rows"),
        "fg3_evaluated_courses": ("courses", "fg3_evaluated_courses"),
        "fg3_primary_cohort_courses": ("courses", "fg3_primary_cohort"),
        "fg3_prior_mutation_courses": ("courses", "fg3_prior_mutation_cohort"),
        "fg3_active_before": ("courses", "fg3_evaluated_courses"),
        "fg3_active_after": ("courses", "fg3_evaluated_courses"),
        "fg3_inconclusive_total": ("courses", "fg3_evaluated_courses"),
        "fg3_inconclusive_by_reason": ("courses_by_reason", "fg3_inconclusive_total"),
        "first_get_404_observations": ("courses", "fg3_evaluated_courses"),
        "first_get_410_observations": ("courses", "fg3_evaluated_courses"),
        "deactivations_persistent_gone": ("courses", "fg3_evaluated_courses"),
        "recoveries_required": ("courses", "fg3_evaluated_courses"),
        "prior_mutations_revalidated": (
            "courses",
            "fg3_attributable_prior_mutations",
        ),
    }
)
SNAPSHOT_PAIR_DEFINITIONS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "table_initial_count": ("rows", "snapshot_pairs"),
        "table_final_count": ("rows", "snapshot_pairs"),
        "table_pages": ("pages", "snapshot_pairs"),
        "global_initial_count": ("rows", "snapshot_pairs"),
        "global_final_count": ("rows", "snapshot_pairs"),
    }
)
_BLOCKING_CODES = frozenset(REASON_DEFINITIONS) - {
    "INVENTORY_OK",
    "SOURCE_ACCESSIBLE",
}


class G5Error(RuntimeError):
    """Sanitized failure containing only a closed reason code."""


class G5ReadOnlyFacade:
    """In-memory snapshot pair exposing only deterministic select and count."""

    __slots__ = ("__snapshots",)

    def __init__(
        self,
        first: Mapping[str, Sequence[Mapping[str, Any]]],
        second: Mapping[str, Sequence[Mapping[str, Any]]],
    ) -> None:
        snapshots = []
        for snapshot in (first, second):
            if set(snapshot) != set(_TABLES):
                raise G5Error("STOP_G5_FACADE_INVALID")
            normalized: dict[str, tuple[dict[str, Any], ...]] = {}
            total_bytes = 0
            for table in _TABLES:
                rows = snapshot[table]
                if len(rows) > DEFAULT_MAX_ROWS_PER_TABLE:
                    raise G5Error("STOP_G5_LIMIT_EXCEEDED")
                parsed_rows = []
                for row in rows:
                    parsed = dict(row)
                    if set(parsed) != _TABLE_KEYS[table]:
                        raise G5Error("STOP_G5_FACADE_SCOPE")
                    total_bytes += len(canonical_json(parsed).encode("utf-8"))
                    if total_bytes > DEFAULT_MAX_SNAPSHOT_BYTES:
                        raise G5Error("STOP_G5_LIMIT_EXCEEDED")
                    parsed_rows.append(copy.deepcopy(parsed))
                normalized[table] = tuple(parsed_rows)
            snapshots.append(normalized)
        self.__snapshots = tuple(snapshots)

    def select(
        self,
        snapshot: int,
        table: str,
        *,
        columns: str,
        limit: int,
        offset: int,
        order: str,
    ) -> Sequence[Mapping[str, Any]]:
        if (
            snapshot not in (0, 1)
            or table not in _TABLES
            or columns != _TABLES[table]
            or order != "id.asc"
            or isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 1000
            or isinstance(offset, bool)
            or not isinstance(offset, int)
            or offset < 0
        ):
            raise G5Error("STOP_G5_FACADE_SCOPE")
        rows = sorted(self.__snapshots[snapshot][table], key=lambda row: str(row["id"]))
        return copy.deepcopy(rows[offset : offset + limit])

    def count(self, snapshot: int, table: str) -> int:
        if snapshot not in (0, 1) or table not in _TABLES:
            raise G5Error("STOP_G5_FACADE_SCOPE")
        return len(self.__snapshots[snapshot][table])


@dataclass(frozen=True)
class InventoryObservation:
    institution_id: str
    profile_fingerprint: str
    source_fingerprint: str
    stage: str
    terminal_reason: str
    method_sequence: tuple[str, ...]
    attempts: int
    observed_at: datetime
    run_fingerprint: str
    cohort_fingerprint: str


@dataclass(frozen=True)
class SourceObservation:
    institution_id: str
    profile_fingerprint: str
    source_fingerprint: str
    stage: str
    terminal_reason: str
    method_sequence: tuple[str, ...]
    attempts: int
    observed_at: datetime
    run_fingerprint: str
    cohort_fingerprint: str


@dataclass(frozen=True)
class ProcessingLifecycleObservation:
    staging_id: str
    timestamp_used: str | None
    timestamp_origin: str
    calculated_age_seconds: int | None
    classification: str


@dataclass(frozen=True)
class FG3Observation:
    course_id: str
    run_fingerprint: str
    cohort_fingerprint: str
    observed_at: datetime
    pre_is_active: bool
    post_is_active: bool
    pre_last_404_at: str | None
    post_last_404_at: str | None
    classification: str
    method_sequence: tuple[str, ...]
    attempts: int
    mutation_kind: str
    apply_outcome: str
    exact_one_verified: bool
    antecedent_run_fingerprint: str | None
    antecedent_mutation_fingerprint: str | None
    antecedent_applied_at: datetime | None


@dataclass(frozen=True)
class HashObservation:
    staging_id: str
    content_hash_valid: bool


@dataclass(frozen=True)
class SnapshotPairEvidence:
    snapshot_pair_id: str
    snapshot_1_started_at: datetime
    snapshot_1_ended_at: datetime
    observations_started_at: datetime
    observations_ended_at: datetime
    snapshot_2_started_at: datetime
    snapshot_2_ended_at: datetime


@dataclass(frozen=True)
class HistoricalFG3Manifest:
    manifest_fingerprint: str
    complete: bool
    expected_observation_fingerprints: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalFG3Anchor:
    expected_manifest_fingerprint: str
    base_sha: str
    base_tree: str
    candidate_sha: str
    candidate_tree: str


@dataclass(frozen=True)
class CandidateBinding:
    base_sha: str
    base_tree: str
    candidate_sha: str
    candidate_tree: str
    observed_at: datetime


@dataclass(frozen=True)
class PrivateObservations:
    snapshot_fingerprint: str
    base_sha: str
    base_tree: str
    candidate_sha: str
    candidate_tree: str
    observed_at: datetime
    run_fingerprint: str
    source_cohort_fingerprint: str
    fg3_cohort_fingerprint: str
    fg3_historical_manifest: HistoricalFG3Manifest
    pair: SnapshotPairEvidence
    inventories: tuple[InventoryObservation, ...]
    sources: tuple[SourceObservation, ...]
    fg3: tuple[FG3Observation, ...]
    hashes: tuple[HashObservation, ...]
    lifecycle: tuple[ProcessingLifecycleObservation, ...]


@dataclass(frozen=True)
class ConnectedAuthorization:
    gate: str | None
    gate_status: str
    protected_merge_sha: str | None
    protected_merge_tree: str | None
    security_check_sha: str | None
    contract_check_sha: str | None
    payload_merge_sha: str | None
    payload_merge_tree: str | None
    production_target_digest: str | None


def _fingerprint(domain: str, value: object) -> str:
    material = f"studiamatch:f10.9:g5:{domain}:v2\0{canonical_json(value)}"
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _canonical_private(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical_private(asdict(value))
    if isinstance(value, datetime):
        return _timestamp_text(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical_private(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_private(item) for item in value]
    return value


def profile_fingerprint(profile: Mapping[str, Any]) -> str:
    """Fingerprint one exact private profile without publishing its fields."""
    return _fingerprint("profile", dict(profile))


def source_fingerprint(profile: Mapping[str, Any]) -> str:
    """Fingerprint only the source-defining private profile fields."""
    return _fingerprint(
        "source",
        {
            "institution_id": profile.get("institution_id"),
            "discovery_mode": profile.get("discovery_mode"),
            "seed_urls": profile.get("seed_urls"),
            "catalog_url_patterns": profile.get("catalog_url_patterns"),
            "allowed_url_patterns": profile.get("allowed_url_patterns"),
        },
    )


def snapshot_fingerprint(tables: Mapping[str, Sequence[Mapping[str, Any]]]) -> str:
    """Bind a private snapshot without publishing rows or identifiers."""
    canonical_tables = {
        table: sorted((dict(row) for row in tables[table]), key=lambda row: str(row["id"]))
        for table in sorted(_TABLES)
    }
    return _fingerprint(
        "snapshot",
        {"normalization": URL_IDENTITY_VERSION, "tables": canonical_tables},
    )


def _table_fingerprint(table: str, rows: Sequence[Mapping[str, Any]]) -> str:
    return _fingerprint(
        f"table:{table}",
        sorted((dict(row) for row in rows), key=lambda row: str(row["id"])),
    )


def source_cohort_fingerprint(profile_fingerprints: Sequence[str]) -> str:
    """Derive the enabled-profile cohort without institution-level collapsing."""
    return _fingerprint("source-cohort", sorted(str(value) for value in profile_fingerprints))


def fg3_cohort_fingerprint(
    active_course_ids: Sequence[str],
    prior_mutation_course_ids: Sequence[str],
) -> str:
    """Derive disjoint primary and attributable prior-mutation FG3 cohorts."""
    return _fingerprint(
        "fg3-cohort",
        {
            "active_snapshot_1": sorted(str(value) for value in active_course_ids),
            "inactive_prior_mutations": sorted(
                str(value) for value in prior_mutation_course_ids
            ),
        },
    )


def snapshot_pair_fingerprint(
    first: Mapping[str, Sequence[Mapping[str, Any]]],
    second: Mapping[str, Sequence[Mapping[str, Any]]],
    pair: SnapshotPairEvidence,
    binding: CandidateBinding,
) -> str:
    """Derive pair identity without including the identity itself."""
    return _fingerprint(
        "snapshot-pair",
        {
            "global": (snapshot_fingerprint(first), snapshot_fingerprint(second)),
            "tables": {
                table: (
                    _table_fingerprint(table, first[table]),
                    _table_fingerprint(table, second[table]),
                )
                for table in sorted(_TABLES)
            },
            "intervals": (
                _timestamp_text(pair.snapshot_1_started_at),
                _timestamp_text(pair.snapshot_1_ended_at),
                _timestamp_text(pair.observations_started_at),
                _timestamp_text(pair.observations_ended_at),
                _timestamp_text(pair.snapshot_2_started_at),
                _timestamp_text(pair.snapshot_2_ended_at),
            ),
            "binding": _canonical_private(binding),
        },
    )


def run_fingerprint(snapshot_pair_id: str, binding: CandidateBinding) -> str:
    """Derive one diagnostic run from its pair and immutable candidate binding."""
    return _fingerprint(
        "run",
        {"snapshot_pair_id": snapshot_pair_id, "binding": _canonical_private(binding)},
    )


def mutation_fingerprint(
    course_id: str,
    antecedent_run_fingerprint: str,
    antecedent_applied_at: datetime,
    mutation_kind: str,
    apply_outcome: str,
    exact_one_verified: bool,
) -> str:
    """Bind private evidence of a mutation that predates this read-only run."""
    return _fingerprint(
        "prior-mutation",
        {
            "course_id": course_id,
            "antecedent_run_fingerprint": antecedent_run_fingerprint,
            "antecedent_applied_at": _timestamp_text(antecedent_applied_at),
            "mutation_kind": mutation_kind,
            "apply_outcome": apply_outcome,
            "exact_one_verified": exact_one_verified,
        },
    )


def historical_observation_fingerprint(item: FG3Observation) -> str:
    """Bind one private historical FG3 result without publishing its fields."""
    return _fingerprint("historical-fg3-observation", _canonical_private(item))


def historical_manifest_fingerprint(
    complete: bool, expected_observation_fingerprints: Sequence[str]
) -> str:
    """Bind the independently materialized historical FG3 evidence inventory."""
    return _fingerprint(
        "historical-fg3-manifest",
        {
            "complete": complete,
            "expected_observation_fingerprints": sorted(
                str(value) for value in expected_observation_fingerprints
            ),
        },
    )


def _validate_binding(binding: CandidateBinding) -> None:
    if type(binding) is not CandidateBinding:
        raise G5Error("STOP_G5_BINDING_INVALID")


def _validate_historical_anchor(
    anchor: HistoricalFG3Anchor | None,
    manifest: HistoricalFG3Manifest,
    binding: CandidateBinding,
) -> None:
    if (
        type(anchor) is not HistoricalFG3Anchor
        or not _DIGEST_RE.fullmatch(anchor.expected_manifest_fingerprint)
        or anchor.expected_manifest_fingerprint != manifest.manifest_fingerprint
        or anchor.base_sha != binding.base_sha
        or anchor.base_tree != binding.base_tree
        or anchor.candidate_sha != binding.candidate_sha
        or anchor.candidate_tree != binding.candidate_tree
    ):
        raise G5Error("STOP_G5_FG3_HISTORICAL_EVIDENCE_ANCHOR_MISSING")
    identities = (
        binding.base_sha,
        binding.base_tree,
        binding.candidate_sha,
        binding.candidate_tree,
    )
    if (
        any(type(value) is not str for value in identities)
        or any(not _SHA_RE.fullmatch(value) for value in identities)
        or not _is_utc(binding.observed_at)
    ):
        raise G5Error("STOP_G5_BINDING_INVALID")


def _is_utc(value: object) -> bool:
    return type(value) is datetime and value.tzinfo is not None and value.utcoffset() == timedelta(0)


def _collect_table(
    facade: G5ReadOnlyFacade,
    snapshot: int,
    table: str,
    *,
    page_size: int,
    max_rows: int,
    max_bytes: int,
) -> tuple[tuple[dict[str, Any], ...], int, int]:
    try:
        expected = facade.count(snapshot, table)
    except Exception:
        raise G5Error("STOP_G5_COLLECTION_ERROR") from None
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
        raise G5Error("STOP_G5_COLLECTION_ERROR")
    if expected > max_rows:
        raise G5Error("STOP_G5_LIMIT_EXCEEDED")
    rows: list[dict[str, Any]] = []
    offset = pages = observed_bytes = 0
    while offset < expected:
        try:
            page = facade.select(
                snapshot,
                table,
                columns=_TABLES[table],
                limit=page_size,
                offset=offset,
                order="id.asc",
            )
        except Exception:
            raise G5Error("STOP_G5_COLLECTION_ERROR") from None
        if not page or len(page) > page_size:
            raise G5Error("STOP_G5_PAGINATION_INCOMPLETE")
        for row in page:
            if not isinstance(row, Mapping) or not row.get("id"):
                raise G5Error("STOP_G5_COLLECTION_ERROR")
            normalized = dict(row)
            observed_bytes += len(canonical_json(normalized).encode("utf-8"))
            if observed_bytes > max_bytes:
                raise G5Error("STOP_G5_LIMIT_EXCEEDED")
            rows.append(normalized)
        offset += len(page)
        pages += 1
    try:
        final_count = facade.count(snapshot, table)
    except Exception:
        raise G5Error("STOP_G5_COLLECTION_ERROR") from None
    if len(rows) != expected or final_count != expected:
        raise G5Error(STOP_SNAPSHOT_DRIFT)
    ids = [str(row["id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise G5Error("STOP_G5_DUPLICATE_ID")
    return tuple(sorted(rows, key=lambda row: str(row["id"]))), pages, observed_bytes


def _collect_snapshot(
    facade: G5ReadOnlyFacade,
    snapshot: int,
    *,
    page_size: int,
    max_rows: int,
    max_bytes: int,
) -> tuple[dict[str, tuple[dict[str, Any], ...]], dict[str, int], int]:
    tables: dict[str, tuple[dict[str, Any], ...]] = {}
    pages: dict[str, int] = {}
    total_bytes = 0
    for table in sorted(_TABLES):
        remaining = max_bytes - total_bytes
        if remaining <= 0:
            raise G5Error("STOP_G5_LIMIT_EXCEEDED")
        tables[table], pages[table], table_bytes = _collect_table(
            facade,
            snapshot,
            table,
            page_size=page_size,
            max_rows=max_rows,
            max_bytes=remaining,
        )
        total_bytes += table_bytes
    return tables, pages, total_bytes


def _parse_utc(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        return None
    return parsed.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _json_list(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise G5Error("STOP_G5_CLASSIFICATION_ERROR")
    return tuple(item for item in value if item.strip())


def _identity(value: object) -> tuple[str, bool]:
    identity = build_url_identity(str(value or ""))
    usable = bool(identity.canonical_url) and not identity.canonical_url.startswith("urn:")
    return identity.dedupe_key, usable


def _enabled(profile: Mapping[str, Any]) -> bool:
    pipeline = profile.get("pipeline_enabled")
    if pipeline is None:
        pipeline = profile.get("pipeline_ready")
    return bool(profile.get("discovery_enabled") and pipeline)


def _validate_pair(pair: SnapshotPairEvidence) -> None:
    if type(pair) is not SnapshotPairEvidence or not _DIGEST_RE.fullmatch(pair.snapshot_pair_id):
        raise G5Error("STOP_G5_SNAPSHOT_PAIR_INVALID")
    points = (
        pair.snapshot_1_started_at,
        pair.snapshot_1_ended_at,
        pair.observations_started_at,
        pair.observations_ended_at,
        pair.snapshot_2_started_at,
        pair.snapshot_2_ended_at,
    )
    if not all(_is_utc(point) for point in points) or list(points) != sorted(points):
        raise G5Error("STOP_G5_SNAPSHOT_PAIR_ORDER_INVALID")
    if (
        pair.snapshot_1_started_at == pair.snapshot_1_ended_at
        or pair.observations_started_at == pair.observations_ended_at
        or pair.snapshot_2_started_at == pair.snapshot_2_ended_at
    ):
        raise G5Error("STOP_G5_SNAPSHOT_PAIR_ORDER_INVALID")


def _validate_common_observation(
    item: InventoryObservation | SourceObservation,
    *,
    profile: Mapping[str, Any],
    reasons: frozenset[str],
    observations: PrivateObservations,
) -> None:
    if (
        item.institution_id != str(profile["institution_id"])
        or item.profile_fingerprint != profile_fingerprint(profile)
        or item.source_fingerprint != source_fingerprint(profile)
        or item.terminal_reason not in reasons
        or item.run_fingerprint != observations.run_fingerprint
        or item.cohort_fingerprint != observations.source_cohort_fingerprint
        or not _DIGEST_RE.fullmatch(item.run_fingerprint)
        or not _DIGEST_RE.fullmatch(item.cohort_fingerprint)
        or not _is_utc(item.observed_at)
        or not (
            observations.pair.observations_started_at
            <= item.observed_at
            <= observations.pair.observations_ended_at
        )
        or isinstance(item.attempts, bool)
        or not isinstance(item.attempts, int)
        or not 1 <= item.attempts <= 3
        or type(item.method_sequence) is not tuple
        or any(method not in {"HEAD", "GET"} for method in item.method_sequence)
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if type(item) is InventoryObservation and (
        item.stage != "INVENTORY_QUERY" or item.method_sequence or not 1 <= item.attempts <= 3
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if type(item) is SourceObservation and (
        not item.method_sequence
        or item.stage != item.method_sequence[-1]
        or item.attempts != len(item.method_sequence)
        or (
            item.terminal_reason == "SOURCE_GET_403"
            and item.method_sequence[-1] != "GET"
        )
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")


def _recompute_lifecycle(
    row: Mapping[str, Any], now: datetime
) -> tuple[str | None, str, int | None, str]:
    raw_last = row.get("last_harvested_at")
    raw_created = row.get("created_at")
    if raw_last is not None:
        raw = raw_last
        origin = "LAST_HARVESTED_AT_PROXY"
    elif raw_created is not None:
        raw = raw_created
        origin = "CREATED_AT_PROXY"
    else:
        return None, "NONE", None, "AGE_UNKNOWN"
    parsed = _parse_utc(raw)
    if parsed is None:
        return str(raw), origin, None, "AGE_UNKNOWN"
    timestamp_used = _timestamp_text(parsed)
    age = int((now - parsed).total_seconds())
    if age < 0:
        return timestamp_used, origin, age, "FUTURE_TIMESTAMP"
    if timedelta(seconds=age) > _STALE_AFTER:
        return timestamp_used, origin, age, "STALE"
    return timestamp_used, origin, age, "NOT_STALE"


def _validate_observations(
    tables: Mapping[str, tuple[dict[str, Any], ...]],
    observations: PrivateObservations,
    binding: CandidateBinding,
    expected_snapshot: str,
) -> tuple[Counter[str], dict[str, int], dict[str, int]]:
    _validate_private_types(observations)
    _validate_pair(observations.pair)
    if (
        observations.snapshot_fingerprint != expected_snapshot
        or observations.base_sha != binding.base_sha
        or observations.base_tree != binding.base_tree
        or observations.candidate_sha != binding.candidate_sha
        or observations.candidate_tree != binding.candidate_tree
        or observations.observed_at != binding.observed_at
        or not _DIGEST_RE.fullmatch(observations.run_fingerprint)
        or not _DIGEST_RE.fullmatch(observations.source_cohort_fingerprint)
        or not _DIGEST_RE.fullmatch(observations.fg3_cohort_fingerprint)
        or not (
            observations.pair.observations_started_at
            <= observations.observed_at
            <= observations.pair.observations_ended_at
        )
    ):
        raise G5Error("STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED")

    reasons: Counter[str] = Counter()
    enabled: dict[str, Mapping[str, Any]] = {}
    for profile in tables["institution_site_profiles"]:
        if not _enabled(profile):
            continue
        fingerprint = profile_fingerprint(profile)
        if fingerprint in enabled:
            raise G5Error("STOP_G5_PROFILE_FINGERPRINT_DUPLICATE")
        enabled[fingerprint] = profile
    expected_source_cohort = source_cohort_fingerprint(tuple(enabled))
    expected_run = run_fingerprint(observations.pair.snapshot_pair_id, binding)
    if (
        observations.source_cohort_fingerprint != expected_source_cohort
        or observations.run_fingerprint != expected_run
    ):
        raise G5Error("STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED")
    inventories: dict[str, InventoryObservation] = {}
    for item in observations.inventories:
        if (
            type(item) is not InventoryObservation
            or item.profile_fingerprint in inventories
        ):
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        profile = enabled.get(item.profile_fingerprint)
        if profile is None:
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        _validate_common_observation(
            item,
            profile=profile,
            reasons=_INVENTORY_CODES,
            observations=observations,
        )
        inventories[item.profile_fingerprint] = item
        reasons[item.terminal_reason] += 1
    sources: dict[str, SourceObservation] = {}
    for item in observations.sources:
        if type(item) is not SourceObservation or item.profile_fingerprint in sources:
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        profile = enabled.get(item.profile_fingerprint)
        if profile is None:
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        _validate_common_observation(
            item,
            profile=profile,
            reasons=_SOURCE_CODES,
            observations=observations,
        )
        sources[item.profile_fingerprint] = item
        reasons[item.terminal_reason] += 1
    if set(inventories) != set(enabled) or set(sources) != set(enabled):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INCOMPLETE")

    hash_targets = {
        str(row["id"])
        for row in tables["staging_raw"]
        if str(row.get("status") or "") in {"pending", "processing", "processed"}
    }
    hash_ids: set[str] = set()
    for item in observations.hashes:
        if (
            type(item) is not HashObservation
            or not item.staging_id
            or item.staging_id in hash_ids
            or type(item.content_hash_valid) is not bool
        ):
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        hash_ids.add(item.staging_id)
        if not item.content_hash_valid:
            reasons["CONTENT_HASH_INVALID"] += 1
    if hash_ids != hash_targets:
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INCOMPLETE")

    processing = {
        str(row["id"]): row
        for row in tables["staging_raw"]
        if str(row.get("status") or "") == "processing"
    }
    lifecycle_ids: set[str] = set()
    lifecycle_counts: Counter[str] = Counter()
    for item in observations.lifecycle:
        if (
            type(item) is not ProcessingLifecycleObservation
            or item.staging_id in lifecycle_ids
            or item.timestamp_origin not in _TIMESTAMP_ORIGINS
            or item.classification not in _LIFECYCLE_CLASSES
        ):
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        row = processing.get(item.staging_id)
        if row is None:
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        expected = _recompute_lifecycle(row, binding.observed_at)
        actual = (
            item.timestamp_used,
            item.timestamp_origin,
            item.calculated_age_seconds,
            item.classification,
        )
        if actual != expected:
            raise G5Error("STOP_G5_LIFECYCLE_EVIDENCE_MISMATCH")
        lifecycle_ids.add(item.staging_id)
        lifecycle_counts[item.classification] += 1
    if lifecycle_ids != set(processing):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INCOMPLETE")
    reasons["PROCESSING_STALE"] += lifecycle_counts["STALE"]
    reasons["PROCESSING_AGE_UNKNOWN"] += lifecycle_counts["AGE_UNKNOWN"]
    reasons["PROCESSING_FUTURE_TIMESTAMP"] += lifecycle_counts["FUTURE_TIMESTAMP"]
    for empty in ("PROCESSING_STALE", "PROCESSING_AGE_UNKNOWN", "PROCESSING_FUTURE_TIMESTAMP"):
        if not reasons[empty]:
            del reasons[empty]
    return (
        reasons,
        {
            "processing_stale": lifecycle_counts["STALE"],
            "processing_not_stale": lifecycle_counts["NOT_STALE"],
            "processing_age_unknown": lifecycle_counts["AGE_UNKNOWN"],
            "processing_future_timestamp": lifecycle_counts["FUTURE_TIMESTAMP"],
        },
        {
            "enabled_profiles": len(enabled),
            "processing_rows": len(processing),
            "staging_rows": len(tables["staging_raw"]),
            "hash_evidence_targets": len(hash_targets),
        },
    )


def _classify_fg2(
    tables: Mapping[str, tuple[dict[str, Any], ...]],
) -> tuple[Counter[str], dict[str, int], dict[str, int]]:
    reasons: Counter[str] = Counter()
    staging_by_identity: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    staging_by_id: dict[str, Mapping[str, Any]] = {}
    for row in tables["staging_raw"]:
        row_id = str(row["id"])
        staging_by_id[row_id] = row
        identity, usable = _identity(row.get("url"))
        if usable:
            staging_by_identity[identity].append(row)
        else:
            reasons["INVALID_URL_IDENTITY"] += 1
        status = str(row.get("status") or "")
        if status not in _STAGING_STATUSES:
            reasons["UNKNOWN_STAGING_STATUS"] += 1
        content_hash = row.get("content_hash")
        if status in {"pending", "processing", "processed"} and (
            not isinstance(content_hash, str) or not _HASH_RE.fullmatch(content_hash)
        ):
            reasons["INCOMPLETE_CONTENT_EVIDENCE"] += 1

    duplicate_groups = duplicate_excess_rows = conflicting_hash_groups = 0
    for rows in staging_by_identity.values():
        if len(rows) < 2:
            continue
        duplicate_groups += 1
        duplicate_excess_rows += len(rows) - 1
        reasons["DUPLICATE_NORMALIZED_URL"] += 1
        hashes = {str(row.get("content_hash")) for row in rows if row.get("content_hash")}
        if len(hashes) > 1:
            conflicting_hash_groups += 1
            reasons["CONFLICTING_CONTENT_HASH"] += 1

    cleansed_by_id: dict[str, Mapping[str, Any]] = {}
    downstream_counts: Counter[str] = Counter()
    downstream_conflicts = 0
    for row in tables["cleansed_programs"]:
        cleansed_by_id[str(row["id"])] = row
        staging_id = str(row.get("staging_id") or "")
        parent = staging_by_id.get(staging_id)
        downstream_counts[staging_id] += 1
        if parent is None or not _same_reference(parent, row):
            downstream_conflicts += 1
    downstream_conflicts += sum(
        count - 1 for count in downstream_counts.values() if count > 1
    )
    enriched_counts: Counter[str] = Counter()
    for row in tables["enriched_programs"]:
        cleansed_id = str(row.get("cleansed_id") or "")
        parent = cleansed_by_id.get(cleansed_id)
        enriched_counts[cleansed_id] += 1
        if parent is None or not _same_reference(parent, row):
            downstream_conflicts += 1
    downstream_conflicts += sum(
        count - 1 for count in enriched_counts.values() if count > 1
    )
    if downstream_conflicts:
        reasons["DOWNSTREAM_REFERENCE_CONFLICT"] = downstream_conflicts

    for profile in tables["institution_site_profiles"]:
        if not _enabled(profile):
            continue
        mode = str(profile.get("discovery_mode") or "")
        seeds = _json_list(profile.get("seed_urls"))
        catalogs = _json_list(profile.get("catalog_url_patterns"))
        allowed = _json_list(profile.get("allowed_url_patterns"))
        if mode == "hardcoded_urls" and not seeds:
            reasons["INVALID_EMPTY_HARDCODED_PROFILE"] += 1
        elif (
            mode not in _DISCOVERY_MODES
            or (mode == "catalog_link_extraction" and not seeds)
            or (mode == "paginated_catalog" and not catalogs)
            or (mode in {"hardcoded_urls", "sitemap_bfs"} and not allowed)
            or not all(_identity(seed)[1] for seed in seeds)
            or not all(_valid_catalog_template(item) for item in catalogs)
            or not all(_valid_pattern(pattern) for pattern in allowed)
        ):
            reasons["INVALID_ENABLED_DISCOVERY_PROFILE"] += 1
    return (
        reasons,
        {
            "duplicate_groups": duplicate_groups,
            "duplicate_excess_rows": duplicate_excess_rows,
            "conflicting_hash_groups": conflicting_hash_groups,
            "downstream_reference_conflicts": downstream_conflicts,
        },
        {
            "normalized_url_groups": len(staging_by_identity),
            "duplicate_groups": duplicate_groups,
            "downstream_references": (
                len(tables["cleansed_programs"]) + len(tables["enriched_programs"])
            ),
        },
    )


def _same_reference(parent: Mapping[str, Any], child: Mapping[str, Any]) -> bool:
    parent_identity, parent_usable = _identity(parent.get("url"))
    child_identity, child_usable = _identity(child.get("url"))
    return bool(
        parent_usable
        and child_usable
        and parent_identity == child_identity
        and str(parent.get("institution_id")) == str(child.get("institution_id"))
    )


def _valid_pattern(pattern: str) -> bool:
    if not pattern or len(pattern) > 200:
        return False
    if not pattern.startswith("re:"):
        return True
    expression = pattern[3:]
    if (
        not expression
        or "(?" in expression
        or re.search(r"\\[1-9]", expression)
        or re.search(r"(?:\*|\+|\{\d+,?\d*\})(?:\s*)(?:\*|\+|\{)", expression)
        or re.search(r"\([^)]*(?:\*|\+|\{\d+,?\d*\})[^)]*\)(?:\*|\+|\{)", expression)
    ):
        return False
    try:
        re.compile(expression)
    except re.error:
        return False
    return True


def _valid_catalog_template(pattern: str) -> bool:
    remainder = pattern.replace("{page}", "")
    return bool(
        len(pattern) <= 200
        and pattern.count("{page}") == 1
        and "{" not in remainder
        and "}" not in remainder
        and _identity(pattern.replace("{page}", "1"))[1]
    )


def _normalize_optional_timestamp(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = _parse_utc(value)
    if parsed is None:
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    return _timestamp_text(parsed)


def _has_prior_mutation(item: FG3Observation) -> bool:
    return item.mutation_kind != "NONE"


def _validate_private_types(observations: PrivateObservations) -> None:
    if (
        type(observations) is not PrivateObservations
        or type(observations.fg3_historical_manifest) is not HistoricalFG3Manifest
        or type(observations.fg3_historical_manifest.complete) is not bool
        or type(observations.fg3_historical_manifest.expected_observation_fingerprints)
        is not tuple
        or type(observations.pair) is not SnapshotPairEvidence
        or type(observations.inventories) is not tuple
        or type(observations.sources) is not tuple
        or type(observations.fg3) is not tuple
        or type(observations.hashes) is not tuple
        or type(observations.lifecycle) is not tuple
        or any(type(item) is not InventoryObservation for item in observations.inventories)
        or any(type(item) is not SourceObservation for item in observations.sources)
        or any(type(item) is not FG3Observation for item in observations.fg3)
        or any(type(item) is not HashObservation for item in observations.hashes)
        or any(
            type(item) is not ProcessingLifecycleObservation
            for item in observations.lifecycle
        )
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")


def _validate_fg3_item(
    item: FG3Observation,
    first_row: Mapping[str, Any],
    second_row: Mapping[str, Any],
    observations: PrivateObservations,
) -> None:
    prior = _has_prior_mutation(item)
    if (
        type(item) is not FG3Observation
        or item.run_fingerprint != observations.run_fingerprint
        or item.cohort_fingerprint != observations.fg3_cohort_fingerprint
        or not _is_utc(item.observed_at)
        or not (
            observations.pair.observations_started_at
            <= item.observed_at
            <= observations.pair.observations_ended_at
        )
        or type(item.pre_is_active) is not bool
        or type(item.post_is_active) is not bool
        or item.classification not in _FG3_CLASSIFICATIONS
        or not item.method_sequence
        or type(item.method_sequence) is not tuple
        or any(method not in {"HEAD", "GET"} for method in item.method_sequence)
        or isinstance(item.attempts, bool)
        or not isinstance(item.attempts, int)
        or not 1 <= item.attempts <= 3
        or item.attempts != len(item.method_sequence)
        or item.mutation_kind not in _MUTATION_KINDS
        or item.apply_outcome not in _APPLY_OUTCOMES
        or type(item.exact_one_verified) is not bool
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if item.classification in {"GET_404", "GET_410", "GET_403"} and (
        item.method_sequence[-1] != "GET"
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if item.classification in {"GET_404", "GET_410"} and not prior:
        raise G5Error("STOP_G5_FG3_HISTORICAL_EVIDENCE_MISSING")
    pre_last = _normalize_optional_timestamp(item.pre_last_404_at)
    post_last = _normalize_optional_timestamp(item.post_last_404_at)
    first_last = _normalize_optional_timestamp(first_row.get("last_404_at"))
    second_last = _normalize_optional_timestamp(second_row.get("last_404_at"))
    if (
        item.pre_is_active != first_row.get("is_active")
        or item.post_is_active != second_row.get("is_active")
        or pre_last != first_last
        or post_last != second_last
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if prior:
        if (
            item.apply_outcome != "APPLIED_PRIOR_EXACT_ONE"
            or not item.exact_one_verified
            or type(item.antecedent_run_fingerprint) is not str
            or not _DIGEST_RE.fullmatch(item.antecedent_run_fingerprint)
            or item.antecedent_run_fingerprint == observations.run_fingerprint
            or not _is_utc(item.antecedent_applied_at)
            or item.antecedent_applied_at >= observations.pair.snapshot_1_started_at
            or type(item.antecedent_mutation_fingerprint) is not str
            or item.antecedent_mutation_fingerprint
            != mutation_fingerprint(
                item.course_id,
                item.antecedent_run_fingerprint,
                item.antecedent_applied_at,
                item.mutation_kind,
                item.apply_outcome,
                item.exact_one_verified,
            )
        ):
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    elif (
        item.apply_outcome != "NOT_APPLIED_READ_ONLY"
        or item.exact_one_verified
        or item.antecedent_run_fingerprint is not None
        or item.antecedent_mutation_fingerprint is not None
        or item.antecedent_applied_at is not None
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if item.mutation_kind == "FIRST_GET_404" and pre_last is None:
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if item.mutation_kind == "FIRST_GET_410" and pre_last is None:
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
    if item.mutation_kind == "DEACTIVATE_PERSISTENT_GONE" and (
        item.pre_is_active or item.post_is_active or pre_last is None
    ):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")


def _classify_fg3(
    first: Mapping[str, tuple[dict[str, Any], ...]],
    second: Mapping[str, tuple[dict[str, Any], ...]],
    observations: PrivateObservations,
) -> tuple[Counter[str], dict[str, object], dict[str, int]]:
    manifest = observations.fg3_historical_manifest
    expected_historical = manifest.expected_observation_fingerprints
    if (
        not _DIGEST_RE.fullmatch(manifest.manifest_fingerprint)
        or any(
            type(value) is not str or not _DIGEST_RE.fullmatch(value)
            for value in expected_historical
        )
        or len(expected_historical) != len(set(expected_historical))
        or manifest.manifest_fingerprint
        != historical_manifest_fingerprint(manifest.complete, expected_historical)
    ):
        raise G5Error("STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED")
    if not manifest.complete:
        raise G5Error("STOP_G5_FG3_HISTORICAL_EVIDENCE_MISSING")
    reasons: Counter[str] = Counter()
    first_courses = {str(row["id"]): row for row in first["courses"]}
    second_courses = {str(row["id"]): row for row in second["courses"]}
    supplied: dict[str, FG3Observation] = {}
    for item in observations.fg3:
        if type(item) is not FG3Observation or item.course_id in supplied:
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        first_row = first_courses.get(item.course_id)
        second_row = second_courses.get(item.course_id)
        if first_row is None or second_row is None:
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        _validate_fg3_item(item, first_row, second_row, observations)
        if (
            not first_row.get("is_active")
            and item.mutation_kind != "DEACTIVATE_PERSISTENT_GONE"
        ):
            raise G5Error("STOP_G5_FG3_UNATTRIBUTED_INACTIVE")
        supplied[item.course_id] = item
    observed_historical = {
        historical_observation_fingerprint(item)
        for item in supplied.values()
        if _has_prior_mutation(item) or item.classification in _FG3_INCONCLUSIVE
    }
    if observed_historical != set(expected_historical):
        raise G5Error("STOP_G5_FG3_HISTORICAL_EVIDENCE_MISSING")
    required_active = {
        course_id
        for course_id, row in first_courses.items()
        if row.get("is_active") is True
    }
    if not required_active.issubset(supplied):
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INCOMPLETE")
    prior_inactive = {
        course_id
        for course_id, item in supplied.items()
        if course_id not in required_active and _has_prior_mutation(item)
    }
    if observations.fg3_cohort_fingerprint != fg3_cohort_fingerprint(
        tuple(required_active), tuple(prior_inactive)
    ):
        raise G5Error("STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED")

    inconclusive = Counter()
    first_404 = first_410 = persistent = recoveries = prior_count = 0
    active_before = active_after = 0
    for item in supplied.values():
        active_before += int(item.pre_is_active)
        active_after += int(item.post_is_active)
        prior = _has_prior_mutation(item)
        if item.classification in _FG3_INCONCLUSIVE:
            inconclusive[item.classification] += 1
            reasons[f"FG3_{item.classification}"] += 1
            continue
        if prior:
            prior_count += 1
        if item.classification == "HEALTHY":
            if (
                item.mutation_kind == "DEACTIVATE_PERSISTENT_GONE"
                or not item.post_is_active
                or item.post_last_404_at is not None
            ):
                recoveries += 1
            continue
        if item.mutation_kind == "DEACTIVATE_PERSISTENT_GONE":
            persistent += 1
        elif item.classification == "GET_404" and item.mutation_kind == "FIRST_GET_404":
            first_404 += 1
        elif item.classification == "GET_410" and item.mutation_kind == "FIRST_GET_410":
            first_410 += 1
    aggregates = {
        "fg3_evaluated_courses": len(supplied),
        "fg3_primary_cohort_courses": len(required_active),
        "fg3_prior_mutation_courses": len(prior_inactive),
        "fg3_active_before": active_before,
        "fg3_active_after": active_after,
        "fg3_inconclusive_total": sum(inconclusive.values()),
        "fg3_inconclusive_by_reason": dict(sorted(inconclusive.items())),
        "first_get_404_observations": first_404,
        "first_get_410_observations": first_410,
        "deactivations_persistent_gone": persistent,
        "recoveries_required": recoveries,
        "prior_mutations_revalidated": prior_count,
    }
    if (
        aggregates["fg3_evaluated_courses"]
        != aggregates["fg3_primary_cohort_courses"]
        + aggregates["fg3_prior_mutation_courses"]
        or aggregates["fg3_inconclusive_total"] != sum(inconclusive.values())
    ):
        raise G5Error("STOP_G5_CLASSIFICATION_ERROR")
    attributable_prior_mutations = sum(
        _has_prior_mutation(item) for item in supplied.values()
    )
    if prior_count > attributable_prior_mutations:
        raise G5Error("STOP_G5_CLASSIFICATION_ERROR")
    return reasons, aggregates, {
        "fg3_primary_cohort": len(required_active),
        "fg3_prior_mutation_cohort": len(prior_inactive),
        "fg3_evaluated_courses": len(supplied),
        "fg3_inconclusive_total": sum(inconclusive.values()),
        "fg3_attributable_prior_mutations": attributable_prior_mutations,
    }


def _definitions(
    reasons: Mapping[str, int],
    aggregates: Mapping[str, object],
    denominator_values: Mapping[str, int],
) -> dict[str, object]:
    if not set(reasons).issubset(REASON_DEFINITIONS) or set(aggregates) != set(AGGREGATE_DEFINITIONS):
        raise G5Error("STOP_G5_PUBLIC_VOCABULARY_INVALID")
    used_denominators = {
        definition[1]
        for key, definition in REASON_DEFINITIONS.items()
        if key in reasons
    } | {definition[1] for definition in AGGREGATE_DEFINITIONS.values()}
    if not used_denominators.issubset(denominator_values):
        raise G5Error("STOP_G5_PUBLIC_VOCABULARY_INVALID")
    return {
        "reason_codes": {
            key: {"unit": REASON_DEFINITIONS[key][0], "denominator": REASON_DEFINITIONS[key][1]}
            for key in sorted(reasons)
        },
        "aggregates": {
            key: {
                "unit": AGGREGATE_DEFINITIONS[key][0],
                "denominator": AGGREGATE_DEFINITIONS[key][1],
            }
            for key in sorted(aggregates)
        },
        "snapshot_pair_counts": {
            key: {"unit": value[0], "denominator": value[1]}
            for key, value in SNAPSHOT_PAIR_DEFINITIONS.items()
        },
    }


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _pair_projection(
    observations: PrivateObservations,
    first: Mapping[str, Sequence[Mapping[str, Any]]],
    second: Mapping[str, Sequence[Mapping[str, Any]]],
    first_pages: Mapping[str, int],
    second_pages: Mapping[str, int],
) -> dict[str, object]:
    pair = observations.pair
    tables = {
        table: {
            "initial_count": len(first[table]),
            "final_count": len(second[table]),
            "initial_fingerprint": _table_fingerprint(table, first[table]),
            "final_fingerprint": _table_fingerprint(table, second[table]),
            "pages": (first_pages[table], second_pages[table]),
        }
        for table in sorted(_TABLES)
    }
    return {
        "snapshot_pair_id": pair.snapshot_pair_id,
        "declaration": SNAPSHOT_DECLARATION,
        "sequence": ("snapshot_1", "observations", "snapshot_2"),
        "intervals": {
            "snapshot_1": (
                _timestamp_text(pair.snapshot_1_started_at),
                _timestamp_text(pair.snapshot_1_ended_at),
            ),
            "observations": (
                _timestamp_text(pair.observations_started_at),
                _timestamp_text(pair.observations_ended_at),
            ),
            "snapshot_2": (
                _timestamp_text(pair.snapshot_2_started_at),
                _timestamp_text(pair.snapshot_2_ended_at),
            ),
        },
        "global": {
            "initial_count": sum(len(rows) for rows in first.values()),
            "final_count": sum(len(rows) for rows in second.values()),
            "initial_fingerprint": snapshot_fingerprint(first),
            "final_fingerprint": snapshot_fingerprint(second),
        },
        "tables": tables,
    }


def _observation_fingerprint(observations: PrivateObservations) -> str:
    material = {
        "run": observations.run_fingerprint,
        "source_cohort": observations.source_cohort_fingerprint,
        "fg3_cohort": observations.fg3_cohort_fingerprint,
        "fg3_historical_manifest": observations.fg3_historical_manifest,
        "inventories": sorted(observations.inventories, key=lambda item: item.profile_fingerprint),
        "sources": sorted(observations.sources, key=lambda item: item.profile_fingerprint),
        "fg3": sorted(observations.fg3, key=lambda item: item.course_id),
        "hashes": sorted(observations.hashes, key=lambda item: item.staging_id),
        "lifecycle": sorted(observations.lifecycle, key=lambda item: item.staging_id),
    }
    return _fingerprint("observations", _canonical_private(material))


def collect_g5_projection(
    facade: G5ReadOnlyFacade,
    observations: PrivateObservations,
    binding: CandidateBinding,
    *,
    historical_anchor: HistoricalFG3Anchor | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_rows_per_table: int = DEFAULT_MAX_ROWS_PER_TABLE,
    max_snapshot_bytes: int = DEFAULT_MAX_SNAPSHOT_BYTES,
) -> Mapping[str, object]:
    """Read snapshot one, validate intervening evidence, then read snapshot two."""
    if type(facade) is not G5ReadOnlyFacade:
        raise G5Error("STOP_G5_FACADE_INVALID")
    if (
        isinstance(page_size, bool)
        or not isinstance(page_size, int)
        or not 1 <= page_size <= 1000
        or isinstance(max_rows_per_table, bool)
        or not isinstance(max_rows_per_table, int)
        or max_rows_per_table < page_size
        or isinstance(max_snapshot_bytes, bool)
        or not isinstance(max_snapshot_bytes, int)
        or max_snapshot_bytes < 1
    ):
        raise G5Error("STOP_G5_LIMIT_INVALID")
    _validate_binding(binding)
    _validate_historical_anchor(
        historical_anchor, observations.fg3_historical_manifest, binding
    )
    first, first_pages, _first_bytes = _collect_snapshot(
        facade,
        0,
        page_size=page_size,
        max_rows=max_rows_per_table,
        max_bytes=max_snapshot_bytes,
    )
    first_fingerprint = snapshot_fingerprint(first)
    observation_reasons, lifecycle_aggregates, observation_denominators = _validate_observations(
        first, observations, binding, first_fingerprint
    )
    fg2_reasons, fg2_aggregates, fg2_denominators = _classify_fg2(first)
    second, second_pages, _second_bytes = _collect_snapshot(
        facade,
        1,
        page_size=page_size,
        max_rows=max_rows_per_table,
        max_bytes=max_snapshot_bytes,
    )
    second_fingerprint = snapshot_fingerprint(second)
    stable = first == second and first_fingerprint == second_fingerprint
    if observations.pair.snapshot_pair_id != snapshot_pair_fingerprint(
        first, second, observations.pair, binding
    ):
        raise G5Error("STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED")
    pair_projection = _pair_projection(
        observations, first, second, first_pages, second_pages
    )
    if not stable:
        document = {
            "schema": SCHEMA,
            "algorithm_version": ALGORITHM_VERSION,
            "decision": "STOP",
            "reason_codes": {STOP_SNAPSHOT_DRIFT: 1},
            "aggregates": {},
            "denominator_values": {"snapshot_pairs": 1},
            "definitions": {
                "reason_codes": {
                    STOP_SNAPSHOT_DRIFT: {
                        "unit": REASON_DEFINITIONS[STOP_SNAPSHOT_DRIFT][0],
                        "denominator": REASON_DEFINITIONS[STOP_SNAPSHOT_DRIFT][1],
                    }
                },
                "aggregates": {},
                "snapshot_pair_counts": {
                    key: {"unit": value[0], "denominator": value[1]}
                    for key, value in SNAPSHOT_PAIR_DEFINITIONS.items()
                },
            },
            "snapshot_pair": pair_projection,
            "fingerprints": {"observations": _observation_fingerprint(observations)},
            "sha_tree": {
                "base_sha": binding.base_sha,
                "base_tree": binding.base_tree,
                "candidate_sha": binding.candidate_sha,
                "candidate_tree": binding.candidate_tree,
            },
        }
        document["digests"] = {"algorithm": _fingerprint("algorithm", ALGORITHM_VERSION)}
        document["digests"]["projection"] = _fingerprint("projection", document)
        return _freeze(document)  # type: ignore[return-value]
    fg3_reasons, fg3_aggregates, fg3_denominators = _classify_fg3(
        first, second, observations
    )
    reasons = observation_reasons + fg2_reasons + fg3_reasons
    aggregates = {**fg2_aggregates, **lifecycle_aggregates, **fg3_aggregates}
    denominator_values = {
        "snapshot_pairs": 1,
        **observation_denominators,
        **fg2_denominators,
        **fg3_denominators,
    }
    if sum(lifecycle_aggregates.values()) != denominator_values["processing_rows"]:
        raise G5Error("STOP_G5_CLASSIFICATION_ERROR")
    blocking = any(code in _BLOCKING_CODES and count for code, count in reasons.items())
    document: dict[str, object] = {
        "schema": SCHEMA,
        "algorithm_version": ALGORITHM_VERSION,
        "decision": "PASS" if stable and not blocking else "STOP",
        "reason_codes": dict(sorted(reasons.items())),
        "aggregates": aggregates,
        "denominator_values": dict(sorted(denominator_values.items())),
        "definitions": _definitions(reasons, aggregates, denominator_values),
        "snapshot_pair": pair_projection,
        "fingerprints": {
            "observations": _observation_fingerprint(observations),
        },
        "sha_tree": {
            "base_sha": binding.base_sha,
            "base_tree": binding.base_tree,
            "candidate_sha": binding.candidate_sha,
            "candidate_tree": binding.candidate_tree,
        },
    }
    document["digests"] = {"algorithm": _fingerprint("algorithm", ALGORITHM_VERSION)}
    document["digests"]["projection"] = _fingerprint("projection", document)
    return _freeze(document)  # type: ignore[return-value]


def collect_g5_connected(
    authorization: ConnectedAuthorization,
    *,
    facade_factory: object,
    observations: PrivateObservations,
    binding: CandidateBinding,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Mapping[str, object]:
    """Remain unconditionally blocked before inspecting adapters or credentials."""
    del authorization, facade_factory, observations, binding, page_size
    raise G5Error("STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED")


__all__ = [
    "AGGREGATE_DEFINITIONS",
    "ALGORITHM_VERSION",
    "ALGORITHM_VERSION_V1",
    "CandidateBinding",
    "ConnectedAuthorization",
    "EXCLUDED_SURFACES",
    "FG3Observation",
    "G5Error",
    "G5ReadOnlyFacade",
    "GATE",
    "GATE_CANDIDATE_STATUS",
    "HashObservation",
    "HistoricalFG3Anchor",
    "HistoricalFG3Manifest",
    "InventoryObservation",
    "LEGACY_ALGORITHM_VERSION_V1",
    "LEGACY_SCHEMA_V1",
    "PrivateObservations",
    "ProcessingLifecycleObservation",
    "REASON_DEFINITIONS",
    "SCHEMA",
    "SCHEMA_V1",
    "SNAPSHOT_PAIR_DEFINITIONS",
    "SNAPSHOT_DECLARATION",
    "STOP_SNAPSHOT_DRIFT",
    "SnapshotPairEvidence",
    "SourceObservation",
    "collect_g5_connected",
    "collect_g5_projection",
    "profile_fingerprint",
    "fg3_cohort_fingerprint",
    "historical_manifest_fingerprint",
    "historical_observation_fingerprint",
    "mutation_fingerprint",
    "run_fingerprint",
    "snapshot_fingerprint",
    "snapshot_pair_fingerprint",
    "source_cohort_fingerprint",
    "source_fingerprint",
]
