"""Repository-only G5 diagnostic over two pre-materialized private snapshots."""

from __future__ import annotations

import copy
import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .f10_9_readonly_planner import canonical_json
from .url_identity import URL_IDENTITY_VERSION, build_url_identity


SCHEMA = "f10.9-g5-production-readonly-projection.v1"
ALGORITHM_VERSION = "f10.9-g5-production-readonly-v1"
GATE = "APPROVE_F10_9_G5_PRODUCTION_READONLY_DIAGNOSTIC_V1"
GATE_CANDIDATE_STATUS = "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
DEFAULT_PAGE_SIZE = 1000
DEFAULT_MAX_ROWS_PER_TABLE = 50_000
DEFAULT_MAX_SNAPSHOT_BYTES = 32_000_000
STOP_SNAPSHOT_DRIFT = "STOP_G5_SNAPSHOT_DRIFT"
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
_SOURCE_OUTCOMES = frozenset(
    {"ACCESSIBLE", "SOURCE_ACCESS_403", "SOURCE_TIMEOUT", "SOURCE_FAILURE"}
)
_FG3_OUTCOMES = frozenset({"HEALTHY", "GONE", "INCONCLUSIVE"})


class G5Error(RuntimeError):
    """Sanitized G5 failure containing only a closed reason code."""


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
                normalized_rows: list[dict[str, Any]] = []
                for row in rows:
                    parsed = dict(row)
                    if set(parsed) != _TABLE_KEYS[table]:
                        raise G5Error("STOP_G5_FACADE_SCOPE")
                    total_bytes += len(canonical_json(parsed).encode("utf-8"))
                    if total_bytes > DEFAULT_MAX_SNAPSHOT_BYTES:
                        raise G5Error("STOP_G5_LIMIT_EXCEEDED")
                    normalized_rows.append(copy.deepcopy(parsed))
                normalized[table] = tuple(normalized_rows)
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
            or not 1 <= limit <= 1000
            or offset < 0
        ):
            raise G5Error("STOP_G5_FACADE_SCOPE")
        rows = sorted(self.__snapshots[snapshot][table], key=lambda row: str(row.get("id")))
        return copy.deepcopy(rows[offset : offset + limit])

    def count(self, snapshot: int, table: str) -> int:
        if snapshot not in (0, 1) or table not in _TABLES:
            raise G5Error("STOP_G5_FACADE_SCOPE")
        return len(self.__snapshots[snapshot][table])


@dataclass(frozen=True)
class SourceObservation:
    institution_id: str
    inventory_loaded: bool
    outcome: str


@dataclass(frozen=True)
class FG3Observation:
    course_id: str
    outcome: str


@dataclass(frozen=True)
class HashObservation:
    staging_id: str
    content_hash_valid: bool


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
    sources: tuple[SourceObservation, ...]
    fg3: tuple[FG3Observation, ...]
    hashes: tuple[HashObservation, ...]


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
    material = f"studiamatch:f10.9:g5:{domain}:v1\0{canonical_json(value)}"
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def snapshot_fingerprint(
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
) -> str:
    """Bind a private snapshot without publishing its rows or identifiers."""
    canonical_tables = {
        table: sorted(
            (dict(row) for row in tables[table]),
            key=lambda row: str(row.get("id")),
        )
        for table in sorted(_TABLES)
    }
    return _fingerprint(
        "snapshot",
        {"normalization": URL_IDENTITY_VERSION, "tables": canonical_tables},
    )


def _validate_binding(binding: CandidateBinding) -> None:
    if any(
        not _SHA_RE.fullmatch(value)
        for value in (
            binding.base_sha,
            binding.base_tree,
            binding.candidate_sha,
            binding.candidate_tree,
        )
    ) or binding.observed_at.tzinfo is None:
        raise G5Error("STOP_G5_BINDING_INVALID")


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
    offset = 0
    pages = 0
    observed_bytes = 0
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


def _parse_timestamp(value: object, reason: str) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise G5Error(reason) from None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


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


def _validate_observations(
    tables: Mapping[str, tuple[dict[str, Any], ...]],
    observations: PrivateObservations,
    binding: CandidateBinding,
    expected_snapshot: str,
) -> tuple[Counter[str], dict[str, int]]:
    if (
        observations.snapshot_fingerprint != expected_snapshot
        or observations.base_sha != binding.base_sha
        or observations.base_tree != binding.base_tree
        or observations.candidate_sha != binding.candidate_sha
        or observations.candidate_tree != binding.candidate_tree
        or observations.observed_at != binding.observed_at
    ):
        raise G5Error("STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED")

    reasons: Counter[str] = Counter()
    source_ids: set[str] = set()
    for item in observations.sources:
        if (
            not item.institution_id
            or item.institution_id in source_ids
            or item.outcome not in _SOURCE_OUTCOMES
            or not isinstance(item.inventory_loaded, bool)
        ):
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        source_ids.add(item.institution_id)
        if not item.inventory_loaded:
            reasons["INSTITUTION_INVENTORY_LOAD_FAILED"] += 1
        if item.outcome != "ACCESSIBLE":
            reasons[item.outcome] += 1
    enabled_ids = {
        str(profile.get("institution_id"))
        for profile in tables["institution_site_profiles"]
        if _enabled(profile)
    }
    if source_ids != enabled_ids:
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INCOMPLETE")

    fg3_ids: set[str] = set()
    course_ids = {str(row["id"]) for row in tables["courses"]}
    for item in observations.fg3:
        if (
            not item.course_id
            or item.course_id in fg3_ids
            or item.outcome not in _FG3_OUTCOMES
        ):
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        fg3_ids.add(item.course_id)
        if item.outcome == "INCONCLUSIVE":
            reasons["FG3_INCONCLUSIVE"] += 1
    if fg3_ids != course_ids:
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INCOMPLETE")

    hash_ids: set[str] = set()
    hash_targets = {
        str(row["id"])
        for row in tables["staging_raw"]
        if str(row.get("status") or "") in {"pending", "processing", "processed"}
    }
    for item in observations.hashes:
        if (
            not item.staging_id
            or item.staging_id in hash_ids
            or not isinstance(item.content_hash_valid, bool)
        ):
            raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INVALID")
        hash_ids.add(item.staging_id)
        if not item.content_hash_valid:
            reasons["CONTENT_HASH_INVALID"] += 1
    if hash_ids != hash_targets:
        raise G5Error("STOP_G5_PRIVATE_OBSERVATION_INCOMPLETE")
    return reasons, {
        "source_observations": len(source_ids),
        "fg3_observations": len(fg3_ids),
        "hash_observations": len(hash_ids),
    }


def _classify_fg2(
    tables: Mapping[str, tuple[dict[str, Any], ...]],
    *,
    now: datetime,
) -> tuple[Counter[str], dict[str, int]]:
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
        if status == "processing":
            started = _parse_timestamp(
                row.get("last_harvested_at") or row.get("created_at"),
                "STOP_G5_CLASSIFICATION_ERROR",
            )
            if started is None or started > now:
                reasons["PROCESSING_TIME_INVALID"] += 1
            elif now - started > _STALE_AFTER:
                reasons["STALE_PROCESSING"] += 1

    duplicate_groups = 0
    duplicate_excess_rows = 0
    for rows in staging_by_identity.values():
        if len(rows) < 2:
            continue
        duplicate_groups += 1
        duplicate_excess_rows += len(rows) - 1
        reasons["DUPLICATE_NORMALIZED_URL"] += 1
        hashes = {str(row.get("content_hash")) for row in rows if row.get("content_hash")}
        if len(hashes) > 1:
            reasons["CONFLICTING_CONTENT_HASH"] += 1

    cleansed_by_id: dict[str, Mapping[str, Any]] = {}
    downstream_counts: Counter[str] = Counter()
    for row in tables["cleansed_programs"]:
        cleansed_by_id[str(row["id"])] = row
        staging_id = str(row.get("staging_id") or "")
        parent = staging_by_id.get(staging_id)
        downstream_counts[staging_id] += 1
        if parent is None or not _same_reference(parent, row):
            reasons["DOWNSTREAM_REFERENCE_CONFLICT"] += 1
    reasons["DOWNSTREAM_REFERENCE_CONFLICT"] += sum(
        count - 1 for count in downstream_counts.values() if count > 1
    )
    enriched_counts: Counter[str] = Counter()
    for row in tables["enriched_programs"]:
        cleansed_id = str(row.get("cleansed_id") or "")
        parent = cleansed_by_id.get(cleansed_id)
        enriched_counts[cleansed_id] += 1
        if parent is None or not _same_reference(parent, row):
            reasons["DOWNSTREAM_REFERENCE_CONFLICT"] += 1
    reasons["DOWNSTREAM_REFERENCE_CONFLICT"] += sum(
        count - 1 for count in enriched_counts.values() if count > 1
    )

    for profile in tables["institution_site_profiles"]:
        if not _enabled(profile):
            continue
        mode = str(profile.get("discovery_mode") or "")
        seeds = _json_list(profile.get("seed_urls"))
        catalogs = _json_list(profile.get("catalog_url_patterns"))
        allowed = _json_list(profile.get("allowed_url_patterns"))
        seeds_valid = all(_identity(seed)[1] for seed in seeds)
        catalogs_valid = all(_valid_catalog_template(item) for item in catalogs)
        patterns_valid = all(_valid_pattern(pattern) for pattern in allowed)
        if mode == "hardcoded_urls" and not seeds:
            reasons["INVALID_EMPTY_HARDCODED_PROFILE"] += 1
        elif (
            mode not in _DISCOVERY_MODES
            or (mode == "catalog_link_extraction" and not seeds)
            or (mode == "paginated_catalog" and not catalogs)
            or (mode in {"hardcoded_urls", "sitemap_bfs"} and not allowed)
            or not seeds_valid
            or not catalogs_valid
            or not patterns_valid
        ):
            reasons["INVALID_ENABLED_DISCOVERY_PROFILE"] += 1
    if not reasons["DOWNSTREAM_REFERENCE_CONFLICT"]:
        del reasons["DOWNSTREAM_REFERENCE_CONFLICT"]
    return reasons, {
        "duplicate_groups": duplicate_groups,
        "duplicate_excess_rows": duplicate_excess_rows,
    }


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
        or re.search(
            r"\([^)]*(?:\*|\+|\{\d+,?\d*\})[^)]*\)(?:\*|\+|\{)",
            expression,
        )
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


def _classify_fg3(
    tables: Mapping[str, tuple[dict[str, Any], ...]],
    observations: PrivateObservations,
    *,
    now: datetime,
) -> tuple[Counter[str], dict[str, int]]:
    reasons: Counter[str] = Counter()
    outcomes = {item.course_id: item.outcome for item in observations.fg3}
    already_deactivated = 0
    for row in tables["courses"]:
        try:
            course_id = str(row["id"])
            url = str(row["url"])
            is_active = row["is_active"]
        except (KeyError, TypeError):
            raise G5Error("STOP_G5_CLASSIFICATION_ERROR") from None
        if not course_id or not url or not isinstance(is_active, bool):
            raise G5Error("STOP_G5_CLASSIFICATION_ERROR")
        last_gone = _parse_timestamp(
            row.get("last_404_at"), "FG3_LAST_GONE_STATE_INVALID"
        )
        outcome = outcomes[course_id]
        if outcome == "INCONCLUSIVE":
            continue
        if outcome == "HEALTHY":
            if not is_active:
                reasons["FG3_INACTIVE_RECOVERY_REQUIRES_REBASELINE"] += 1
            elif last_gone is not None:
                reasons["FG3_RECOVERY_REQUIRED"] += 1
            continue
        if not is_active:
            already_deactivated += 1
        elif last_gone is None or now <= last_gone + timedelta(days=3):
            reasons["FIRST_404_410_OBSERVATION"] += 1
        else:
            reasons["DEACTIVATION_REVALIDATION_REQUIRED"] += 1
    return reasons, {"deactivation_already_observed": already_deactivated}


def _stop_projection(
    reason: str,
    binding: CandidateBinding,
    counts: Mapping[str, object],
) -> Mapping[str, object]:
    document = _projection_base(binding, "STOP", {reason: 1}, counts)
    document["fingerprints"] = {"snapshot": None, "observations": None}
    document["digests"] = {"algorithm": _fingerprint("algorithm", ALGORITHM_VERSION)}
    document["digests"]["projection"] = _fingerprint("projection", document)
    return MappingProxyType(document)


def _projection_base(
    binding: CandidateBinding,
    decision: str,
    reasons: Mapping[str, int],
    counts: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "decision": decision,
        "reason_codes": dict(sorted(reasons.items())),
        "counts": dict(counts),
        "timestamps": {
            "observed_at": binding.observed_at.astimezone(timezone.utc).isoformat()
        },
        "sha_tree": {
            "base_sha": binding.base_sha,
            "base_tree": binding.base_tree,
            "candidate_sha": binding.candidate_sha,
            "candidate_tree": binding.candidate_tree,
        },
    }


def collect_g5_projection(
    facade: G5ReadOnlyFacade,
    observations: PrivateObservations,
    binding: CandidateBinding,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_rows_per_table: int = DEFAULT_MAX_ROWS_PER_TABLE,
    max_snapshot_bytes: int = DEFAULT_MAX_SNAPSHOT_BYTES,
) -> Mapping[str, object]:
    """Compare two private snapshots and emit only a sanitized projection."""
    if type(facade) is not G5ReadOnlyFacade:
        raise G5Error("STOP_G5_FACADE_INVALID")
    if (
        not 1 <= page_size <= 1000
        or max_rows_per_table < page_size
        or max_snapshot_bytes < 1
    ):
        raise G5Error("STOP_G5_LIMIT_INVALID")
    _validate_binding(binding)
    first, first_pages, first_bytes = _collect_snapshot(
        facade,
        0,
        page_size=page_size,
        max_rows=max_rows_per_table,
        max_bytes=max_snapshot_bytes,
    )
    second, second_pages, second_bytes = _collect_snapshot(
        facade,
        1,
        page_size=page_size,
        max_rows=max_rows_per_table,
        max_bytes=max_snapshot_bytes,
    )
    first_fingerprint = snapshot_fingerprint(first)
    second_fingerprint = snapshot_fingerprint(second)
    table_counts = {
        table: {
            "rows": len(first[table]),
            "pages_per_snapshot": [first_pages[table], second_pages[table]],
        }
        for table in sorted(first)
    }
    if first_fingerprint != second_fingerprint or first != second:
        return _stop_projection(
            STOP_SNAPSHOT_DRIFT,
            binding,
            {
                "tables": table_counts,
                "snapshots": 2,
                "bytes_per_snapshot": [first_bytes, second_bytes],
            },
        )

    observation_reasons, observation_counts = _validate_observations(
        first, observations, binding, first_fingerprint
    )
    fg2_reasons, fg2_counts = _classify_fg2(first, now=binding.observed_at)
    fg3_reasons, fg3_counts = _classify_fg3(
        first, observations, now=binding.observed_at
    )
    reasons = observation_reasons + fg2_reasons + fg3_reasons
    observations_material = {
        "sources": sorted(
            (
                item.institution_id,
                item.inventory_loaded,
                item.outcome,
            )
            for item in observations.sources
        ),
        "fg3": sorted((item.course_id, item.outcome) for item in observations.fg3),
        "hashes": sorted(
            (item.staging_id, item.content_hash_valid) for item in observations.hashes
        ),
        "snapshot": observations.snapshot_fingerprint,
        "observed_at": observations.observed_at.astimezone(timezone.utc).isoformat(),
    }
    document = _projection_base(
        binding,
        "STOP" if reasons else "PASS",
        reasons,
        {
            "tables": table_counts,
            "snapshots": 2,
            "bytes_per_snapshot": [first_bytes, second_bytes],
            **fg2_counts,
            **fg3_counts,
            **observation_counts,
        },
    )
    document["fingerprints"] = {
        "snapshot": first_fingerprint,
        "observations": _fingerprint("observations", observations_material),
    }
    document["digests"] = {"algorithm": _fingerprint("algorithm", ALGORITHM_VERSION)}
    document["digests"]["projection"] = _fingerprint("projection", document)
    return MappingProxyType(document)


def collect_g5_connected(
    authorization: ConnectedAuthorization,
    *,
    facade_factory: object,
    observations: PrivateObservations,
    binding: CandidateBinding,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Mapping[str, object]:
    """Keep connected mode fail-closed until a post-merge implementation exists."""
    del facade_factory, observations, page_size
    if authorization.gate != GATE:
        raise G5Error("STOP_G5_GATE_MISSING")
    if authorization.gate_status != "APPROVED_NOT_CONSUMED":
        raise G5Error("STOP_G5_GATE_NOT_APPROVED")
    merge_sha = authorization.protected_merge_sha
    merge_tree = authorization.protected_merge_tree
    if (
        merge_sha != binding.candidate_sha
        or merge_tree != binding.candidate_tree
        or authorization.security_check_sha != merge_sha
        or authorization.contract_check_sha != merge_sha
    ):
        raise G5Error("STOP_G5_PROTECTED_MERGE_REQUIRED")
    if (
        authorization.payload_merge_sha != merge_sha
        or authorization.payload_merge_tree != merge_tree
    ):
        raise G5Error("STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED")
    if not authorization.production_target_digest or not _DIGEST_RE.fullmatch(
        authorization.production_target_digest
    ):
        raise G5Error("STOP_G5_PRODUCTION_TARGET_REQUIRED")
    raise G5Error("STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED")


__all__ = [
    "ALGORITHM_VERSION",
    "CandidateBinding",
    "ConnectedAuthorization",
    "FG3Observation",
    "G5Error",
    "G5ReadOnlyFacade",
    "GATE",
    "GATE_CANDIDATE_STATUS",
    "HashObservation",
    "PrivateObservations",
    "SCHEMA",
    "STOP_SNAPSHOT_DRIFT",
    "SourceObservation",
    "collect_g5_connected",
    "collect_g5_projection",
    "snapshot_fingerprint",
]
