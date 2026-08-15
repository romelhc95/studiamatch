"""Pure repository-only contract for a future G5 GET-only adapter.

The contract consumes exact frozen dataclasses containing deeply immutable data.
It validates structure and integrity only. It cannot establish operational trust,
approve or consume a gate, inspect credentials, execute caller code, or create a
transport.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Mapping


CONTRACT_VERSION = "f10.9-g5-get-only-adapter-contract.v2.2"
SCHEMA_VERSION = "f10.9-g5-get-only-adapter-schema.v2.2"
ALGORITHM_VERSION = "f10.9-g5-get-only-adapter-v2.2"
HISTORICAL_CONTRACT_VERSION = "f10.9-g5-get-only-adapter-contract.v2.1"
HISTORICAL_V2_STATUS = "HISTORICAL_ANTECEDENT_NOT_FIT_FOR_CONNECTED_MODE"
EXPECTED_ENVIRONMENT = "Production"
EXPECTED_WORKFLOW = "F10.9 G5 Production Read-Only Diagnostic"
PROTECTED_SOURCE_SHA = "c998b0293b364b1c59d9c52824178927977f0b56"
PROTECTED_SOURCE_TREE = "d93843d4e08dfd9c45571b72040994926dffc221"
CURRENT_GATE_STATUS = "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
CONNECTED_STOP = "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"
TRUST_STOP = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED"
TRUST_MODEL_FUTURE_REQUIREMENTS = (
    "TRUSTED_AUTHORITY_VERIFIER",
    "ATOMIC_SINGLE_USE_GATE_CONSUMPTION",
    "NONCE_REPLAY_LEDGER",
    "ENVIRONMENT_AND_RUN_IDENTITY",
    "NON_FORGEABLE_SIGNATURE_OR_PROOF",
)

STOP_TARGET_BINDING_INVALID = "STOP_G5_TARGET_BINDING_INVALID"
STOP_PROTECTED_SOURCE_INVALID = "STOP_G5_PROTECTED_SOURCE_SHA_TREE_INVALID"
STOP_CAPABILITY_INVALID = "STOP_G5_ADAPTER_CAPABILITY_INVALID"
STOP_PAGINATION_INCOMPLETE = "STOP_G5_PAGINATION_INCOMPLETE"
STOP_COUNT_DRIFT = "STOP_G5_COUNT_DRIFT"
STOP_SNAPSHOT_CONTENT_DRIFT = "STOP_G5_SNAPSHOT_CONTENT_DRIFT"
STOP_CLOCK_TIMING_INVALID = "STOP_G5_CLOCK_TIMING_INVALID"
STOP_ANCHOR_NOT_INDEPENDENT = "STOP_G5_HISTORICAL_ANCHOR_NOT_INDEPENDENT"
STOP_MANIFEST_ANCHOR_MISMATCH = "STOP_G5_MANIFEST_ANCHOR_MISMATCH"

AUTHORIZATION_ORDER = (
    "PROTECTED_SOURCE_SHA_TREE",
    "WORKFLOW_ENVIRONMENT",
    "TARGET_BINDING",
    "ADAPTER_CAPABILITY",
    "PAGINATION_AND_SNAPSHOT_STRUCTURE",
    "SOURCE_OBSERVATION_STRUCTURE",
    "LIFECYCLE_STRUCTURE",
    "MANIFEST_ANCHOR_STRUCTURE",
    "FG3_COHORT_STRUCTURE",
    "TRUST_VERIFICATION",
)
COMPLETED_STRUCTURAL_STEPS = AUTHORIZATION_ORDER[:-1]
READ_CLOCK_SOURCE = "SYSTEM_UTC_PLUS_MONOTONIC"
READ_CAPTURE_SEQUENCE = ("IMMEDIATELY_BEFORE_READ", "IMMEDIATELY_AFTER_READ")
CLOCK_DURATION_TOLERANCE_NS = 250_000_000
SOURCE_ATTEMPT_BUDGET_NS = 15_000_000_000
MAX_SOURCES_PER_PROFILE = 64
MAX_PROFILE_SOURCE_PAIRS = 50_000
SOURCE_ATTEMPT_GRAMMAR = (
    ("HEAD", "GET"),
    ("HEAD", "HEAD", "GET"),
    ("HEAD", "GET", "GET"),
)
MAX_IMMUTABLE_DEPTH = 8
MAX_IMMUTABLE_NODES = 256
MAX_IMMUTABLE_STRING_BYTES = 8_192
MAX_IMMUTABLE_INTEGER_ABS = 2**63 - 1
LIFECYCLE_PROXY_ORDER = ("last_harvested_at", "created_at")
LIFECYCLE_TIMESTAMP_ORIGINS = (
    "LAST_HARVESTED_AT_PROXY",
    "CREATED_AT_PROXY",
    "NONE",
)
LIFECYCLE_CLASSIFICATIONS = (
    "STALE",
    "NOT_STALE",
    "AGE_UNKNOWN",
    "FUTURE_TIMESTAMP",
)
FG3_PRIMARY_COHORT = "ACTIVE_AT_SNAPSHOT_1"
FG3_INACTIVE_ADMISSION = "ATTRIBUTABLE_PRIOR_MUTATION_ONLY"
FG3_HISTORICAL_REQUIREMENT = "COMPLETE_PREMATERIALIZED_MANIFEST_REQUIRED_FOR_24_2_1"
FG3_HISTORICAL_CATEGORY_COUNTS = MappingProxyType(
    {"INCONCLUSIVE": 24, "FIRST_GET_404": 2, "DEACTIVATION": 1}
)
FINGERPRINT_DECLARATION = "INTEGRITY_NOT_AUTHORITY_OR_ANONYMIZATION"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_STALE_AFTER = timedelta(days=7)

TABLE_COLUMNS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "institutions": ("id", "name", "slug", "website_url", "last_harvest_at"),
        "institution_site_profiles": (
            "id",
            "institution_id",
            "discovery_enabled",
            "pipeline_enabled",
            "pipeline_ready",
            "discovery_mode",
            "seed_urls",
            "catalog_url_patterns",
            "allowed_url_patterns",
            "circuit_open",
            "circuit_opened_at",
        ),
        "staging_raw": (
            "id",
            "institution_id",
            "url",
            "status",
            "content_hash",
            "last_harvested_at",
            "created_at",
        ),
        "cleansed_programs": ("id", "staging_id", "institution_id", "url"),
        "enriched_programs": ("id", "cleansed_id", "institution_id", "url"),
        "courses": (
            "id",
            "institution_id",
            "url",
            "is_active",
            "last_404_at",
            "start_date",
        ),
    }
)
FORBIDDEN_METHODS = frozenset(
    {"insert", "update", "upsert", "patch", "delete", "rpc", "execute", "mutate"}
)
PUBLIC_PROJECTION_FORBIDDEN_FIELDS = frozenset(
    {
        "url",
        "host",
        "uuid",
        "institution_id",
        "rows",
        "project_ref",
        "payload",
        "individual_results",
        "response_body",
        "secrets",
    }
)


class G5AdapterContractError(RuntimeError):
    """Fail-closed error containing only a stable reason code."""


ImmutableValue = None | str | bool | int | tuple["ImmutableValue", ...]


@dataclass(frozen=True)
class FrozenRow:
    values: tuple[tuple[str, ImmutableValue], ...]


@dataclass(frozen=True)
class QueryCapability:
    table: str
    columns: tuple[str, ...]
    filters: tuple[tuple[str, str, str], ...]
    order: tuple[str, ...]
    stable_tie_breaker: str
    pagination_mode: str
    page_size: int
    max_rows: int
    max_pages: int
    timeout_seconds: int
    retry_budget: int


@dataclass(frozen=True)
class AdapterCapability:
    methods: tuple[str, ...]
    queries: tuple[QueryCapability, ...]
    max_snapshot_bytes: int


def _query(table: str) -> QueryCapability:
    return QueryCapability(
        table=table,
        columns=TABLE_COLUMNS[table],
        filters=(),
        order=("id.asc",),
        stable_tie_breaker="id",
        pagination_mode="KEYSET_ID_ASC",
        page_size=1000,
        max_rows=50_000,
        max_pages=50,
        timeout_seconds=15,
        retry_budget=2,
    )


GET_ONLY_CAPABILITY = AdapterCapability(
    methods=("select", "count"),
    queries=tuple(_query(table) for table in sorted(TABLE_COLUMNS)),
    max_snapshot_bytes=32_000_000,
)


@dataclass(frozen=True)
class TargetBinding:
    environment: str
    protected_source_sha: str
    protected_source_tree: str
    contract_version: str
    schema_version: str
    algorithm_version: str
    workflow: str
    run_id: str
    issued_at: datetime
    expires_at: datetime
    snapshot_pair_id: str
    payload_digest: str
    manifest_digest: str
    anchor_digest: str


@dataclass(frozen=True)
class ReadTiming:
    snapshot_pair_id: str
    operation: str
    clock_source: str
    capture_sequence: tuple[str, str]
    started_at_utc: datetime
    ended_at_utc: datetime
    monotonic_started_ns: int
    monotonic_ended_ns: int


@dataclass(frozen=True)
class RowCursor:
    order_value: str
    tie_breaker: str
    row_fingerprint: str
    row: FrozenRow


@dataclass(frozen=True)
class PageEvidence:
    after_id: str | None
    requested_limit: int
    rows: tuple[RowCursor, ...]
    page_digest: str
    timing: ReadTiming


@dataclass(frozen=True)
class PaginationEvidence:
    target_binding_digest: str
    snapshot_pair_id: str
    table: str
    initial_count: int
    initial_count_timing: ReadTiming
    final_count: int
    final_count_timing: ReadTiming
    pages: tuple[PageEvidence, ...]
    inventory_digest: str


@dataclass(frozen=True)
class SnapshotPairPayloadEvidence:
    snapshot_pair_id: str
    snapshot_1: tuple[PaginationEvidence, ...]
    snapshot_2: tuple[PaginationEvidence, ...]
    payload_digest: str


@dataclass(frozen=True)
class HistoricalFG3Manifest:
    manifest_digest: str
    builder_identity: str
    builder_instance_identity: str
    candidate_sha: str
    candidate_tree: str
    run_id: str
    issued_at: datetime
    complete: bool
    expected_observation_fingerprints: tuple[str, ...]
    observation_categories: tuple[tuple[str, str], ...]
    category_counts: tuple[tuple[str, int], ...]
    published_count_tuple: tuple[int, int, int]


@dataclass(frozen=True)
class HistoricalFG3Anchor:
    anchor_digest: str
    manifest_digest: str
    provider_identity: str
    provider_instance_identity: str
    provenance: str
    candidate_sha: str
    candidate_tree: str
    run_id: str
    issued_at: datetime


@dataclass(frozen=True)
class ManifestBuilderEvidenceReceipt:
    builder_identity: str
    builder_instance_identity: str
    manifest_digest: str
    evidence_digest: str


@dataclass(frozen=True)
class AnchorProviderEvidenceReceipt:
    provider_identity: str
    provider_instance_identity: str
    manifest_digest: str
    anchor_digest: str
    evidence_digest: str


@dataclass(frozen=True)
class SourceObservationRequest:
    target_binding_digest: str
    snapshot_pair_id: str
    profile_fingerprint: str
    source_fingerprint: str
    run_fingerprint: str
    cohort_fingerprint: str
    method_sequence: tuple[str, ...]
    max_attempts: int


@dataclass(frozen=True)
class SourceAttemptTiming:
    method: str
    started_at_utc: datetime
    ended_at_utc: datetime
    monotonic_started_ns: int
    monotonic_ended_ns: int


@dataclass(frozen=True)
class SourceObservationEvidence:
    target_binding_digest: str
    snapshot_pair_id: str
    profile_fingerprint: str
    source_fingerprint: str
    run_fingerprint: str
    cohort_fingerprint: str
    method_sequence: tuple[str, ...]
    attempt_timings: tuple[SourceAttemptTiming, ...]
    attempts: int
    terminal_reason: str
    observed_at: datetime


@dataclass(frozen=True)
class SourceObservationBundle:
    request: SourceObservationRequest
    evidence: SourceObservationEvidence


@dataclass(frozen=True)
class LifecycleProxy:
    last_harvested_at: str | None
    created_at: str | None
    observed_at: datetime
    timestamp_used: str | None
    timestamp_origin: str
    calculated_age_seconds: int | None
    classification: str


@dataclass(frozen=True)
class LifecycleEvidence:
    staging_row_fingerprint: str
    proxy: LifecycleProxy


@dataclass(frozen=True)
class FG3CourseCohortEvidence:
    course_fingerprint: str
    active_at_snapshot_1: bool
    related_to_current_run: bool


@dataclass(frozen=True)
class FG3PriorMutationEvidence:
    course_fingerprint: str
    antecedent_run_fingerprint: str
    antecedent_observed_at: datetime
    mutation_kind: str
    mutation_fingerprint: str
    historical_observation_fingerprint: str


@dataclass(frozen=True)
class FG3HistoricalObservationEvidence:
    observation_fingerprint: str
    target_binding_digest: str
    snapshot_pair_id: str
    course_fingerprint: str
    run_id: str
    category: str
    active_at_snapshot_1: bool
    observed_at: datetime


@dataclass(frozen=True)
class FG3CohortEvidence:
    target_binding_digest: str
    snapshot_pair_id: str
    run_id: str
    courses: tuple[FG3CourseCohortEvidence, ...]
    prior_mutations: tuple[FG3PriorMutationEvidence, ...]
    historical_observations: tuple[FG3HistoricalObservationEvidence, ...]


@dataclass(frozen=True)
class AuthorizationRequest:
    execution_sha: str
    execution_tree: str
    workflow: str
    environment: str
    target: TargetBinding
    capability: AdapterCapability
    historical_manifest: HistoricalFG3Manifest
    historical_anchor: HistoricalFG3Anchor
    manifest_builder_receipt: ManifestBuilderEvidenceReceipt
    anchor_provider_receipt: AnchorProviderEvidenceReceipt
    fg3_cohort: FG3CohortEvidence
    snapshot_payload: SnapshotPairPayloadEvidence
    source_observations: tuple[SourceObservationBundle, ...]
    lifecycle_evidence: tuple[LifecycleEvidence, ...]
    evaluated_at: datetime


@dataclass(frozen=True)
class AuthorizedAdapterPlan:
    target_binding_digest: str
    completed_steps: tuple[str, ...]
    next_step: str
    reason: str
    transport_created: bool
    authorization_complete: bool
    trust_verification_implemented: bool


_DATACLASS_FIELDS: Mapping[type[object], tuple[str, ...]] = MappingProxyType(
    {
        FrozenRow: ("values",),
        QueryCapability: (
            "table", "columns", "filters", "order", "stable_tie_breaker",
            "pagination_mode", "page_size", "max_rows", "max_pages",
            "timeout_seconds", "retry_budget",
        ),
        AdapterCapability: ("methods", "queries", "max_snapshot_bytes"),
        TargetBinding: (
            "environment", "protected_source_sha", "protected_source_tree",
            "contract_version", "schema_version", "algorithm_version", "workflow",
            "run_id", "issued_at", "expires_at", "snapshot_pair_id",
            "payload_digest", "manifest_digest", "anchor_digest",
        ),
        ReadTiming: (
            "snapshot_pair_id", "operation", "clock_source", "capture_sequence",
            "started_at_utc", "ended_at_utc", "monotonic_started_ns",
            "monotonic_ended_ns",
        ),
        RowCursor: ("order_value", "tie_breaker", "row_fingerprint", "row"),
        PageEvidence: ("after_id", "requested_limit", "rows", "page_digest", "timing"),
        PaginationEvidence: (
            "target_binding_digest", "snapshot_pair_id", "table", "initial_count",
            "initial_count_timing", "final_count", "final_count_timing", "pages",
            "inventory_digest",
        ),
        SnapshotPairPayloadEvidence: ("snapshot_pair_id", "snapshot_1", "snapshot_2", "payload_digest"),
        HistoricalFG3Manifest: (
            "manifest_digest", "builder_identity", "builder_instance_identity",
            "candidate_sha", "candidate_tree", "run_id", "issued_at", "complete",
            "expected_observation_fingerprints", "observation_categories",
            "category_counts", "published_count_tuple",
        ),
        HistoricalFG3Anchor: (
            "anchor_digest", "manifest_digest", "provider_identity",
            "provider_instance_identity", "provenance", "candidate_sha",
            "candidate_tree", "run_id", "issued_at",
        ),
        ManifestBuilderEvidenceReceipt: (
            "builder_identity", "builder_instance_identity", "manifest_digest", "evidence_digest",
        ),
        AnchorProviderEvidenceReceipt: (
            "provider_identity", "provider_instance_identity", "manifest_digest",
            "anchor_digest", "evidence_digest",
        ),
        SourceObservationRequest: (
            "target_binding_digest", "snapshot_pair_id", "profile_fingerprint",
            "source_fingerprint", "run_fingerprint", "cohort_fingerprint",
            "method_sequence", "max_attempts",
        ),
        SourceAttemptTiming: (
            "method", "started_at_utc", "ended_at_utc", "monotonic_started_ns",
            "monotonic_ended_ns",
        ),
        SourceObservationEvidence: (
            "target_binding_digest", "snapshot_pair_id", "profile_fingerprint",
            "source_fingerprint", "run_fingerprint", "cohort_fingerprint",
            "method_sequence", "attempt_timings", "attempts", "terminal_reason",
            "observed_at",
        ),
        SourceObservationBundle: ("request", "evidence"),
        LifecycleProxy: (
            "last_harvested_at", "created_at", "observed_at", "timestamp_used",
            "timestamp_origin", "calculated_age_seconds", "classification",
        ),
        LifecycleEvidence: ("staging_row_fingerprint", "proxy"),
        FG3CourseCohortEvidence: (
            "course_fingerprint", "active_at_snapshot_1", "related_to_current_run",
        ),
        FG3PriorMutationEvidence: (
            "course_fingerprint", "antecedent_run_fingerprint",
            "antecedent_observed_at", "mutation_kind", "mutation_fingerprint",
            "historical_observation_fingerprint",
        ),
        FG3HistoricalObservationEvidence: (
            "observation_fingerprint", "target_binding_digest", "snapshot_pair_id",
            "course_fingerprint", "run_id", "category", "active_at_snapshot_1",
            "observed_at",
        ),
        FG3CohortEvidence: (
            "target_binding_digest", "snapshot_pair_id", "run_id", "courses",
            "prior_mutations", "historical_observations",
        ),
        AuthorizationRequest: (
            "execution_sha", "execution_tree", "workflow", "environment", "target",
            "capability", "historical_manifest", "historical_anchor",
            "manifest_builder_receipt", "anchor_provider_receipt", "fg3_cohort",
            "snapshot_payload", "source_observations", "lifecycle_evidence", "evaluated_at",
        ),
        AuthorizedAdapterPlan: (
            "target_binding_digest", "completed_steps", "next_step", "reason",
            "transport_created", "authorization_complete", "trust_verification_implemented",
        ),
    }
)


def _raise(reason: str) -> None:
    raise G5AdapterContractError(reason)


def _require_complete(value: object, expected_type: type[object], reason: str) -> None:
    if type(value) is not expected_type:
        _raise(reason)
    state = value.__dict__
    names = _DATACLASS_FIELDS[expected_type]
    if (
        type(state) is not dict
        or len(state) != len(names)
        or any(type(name) is not str for name in state)
        or tuple(sorted(state)) != tuple(sorted(names))
    ):
        _raise(reason)


def _is_utc(value: object) -> bool:
    return type(value) is datetime and value.tzinfo is timezone.utc


def _timestamp_text(value: datetime) -> str:
    if not _is_utc(value):
        _raise(STOP_CLOCK_TIMING_INVALID)
    return value.isoformat()


def _valid_digest(value: object) -> bool:
    return type(value) is str and bool(_DIGEST_RE.fullmatch(value))


def _valid_identity(value: object) -> bool:
    return type(value) is str and bool(_IDENTITY_RE.fullmatch(value))


def _strict_int(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def _duration_ns(started_at: datetime, ended_at: datetime) -> int:
    delta = ended_at - started_at
    return (
        delta.days * 86_400_000_000_000
        + delta.seconds * 1_000_000_000
        + delta.microseconds * 1_000
    )


def _valid_immutable(value: object) -> bool:
    remaining = [MAX_IMMUTABLE_NODES]

    def valid_string(item: str) -> bool:
        size = 0
        for character in item:
            codepoint = ord(character)
            if 0xD800 <= codepoint <= 0xDFFF:
                return False
            size += 1 if codepoint <= 0x7F else 2 if codepoint <= 0x7FF else 3 if codepoint <= 0xFFFF else 4
            if size > MAX_IMMUTABLE_STRING_BYTES:
                return False
        return True

    def visit(item: object, depth: int) -> bool:
        remaining[0] -= 1
        if remaining[0] < 0 or depth > MAX_IMMUTABLE_DEPTH:
            return False
        if item is None or type(item) is bool:
            return True
        if type(item) is int:
            return abs(item) <= MAX_IMMUTABLE_INTEGER_ABS
        if type(item) is str:
            return valid_string(item)
        if type(item) is not tuple:
            return False
        return all(visit(child, depth + 1) for child in item)

    return visit(value, 0)


def _validate_frozen_row(row: object, columns: tuple[str, ...], reason: str) -> FrozenRow:
    _require_complete(row, FrozenRow, reason)
    if type(row.values) is not tuple:
        _raise(reason)
    keys: list[str] = []
    for pair in row.values:
        if type(pair) is not tuple or len(pair) != 2:
            _raise(reason)
        key, value = pair
        if type(key) is not str or not _valid_immutable(value):
            _raise(reason)
        keys.append(key)
    if tuple(keys) != columns or len(keys) != len(set(keys)):
        _raise(reason)
    return row


def _row_value(row: FrozenRow, key: str) -> ImmutableValue:
    for name, value in row.values:
        if name == key:
            return value
    _raise(STOP_PAGINATION_INCOMPLETE)


def _json_size(value: object) -> int:
    return len(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
    )


def _digest(domain: str, value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    material = (
        b"studiamatch:f10.9:g5:get-only:"
        + domain.encode("ascii")
        + b":v2.2\0"
        + encoded
    )
    return "sha256:" + hashlib.sha256(material).hexdigest()


def _target_material(binding: TargetBinding, *, evidence: bool) -> tuple[object, ...]:
    material: tuple[object, ...] = (
        binding.environment,
        binding.protected_source_sha,
        binding.protected_source_tree,
        binding.contract_version,
        binding.schema_version,
        binding.algorithm_version,
        binding.workflow,
        binding.run_id,
        _timestamp_text(binding.issued_at),
        _timestamp_text(binding.expires_at),
        binding.snapshot_pair_id,
    )
    if evidence:
        return material
    return material + (
        binding.payload_digest,
        binding.manifest_digest,
        binding.anchor_digest,
    )


def _validate_target_binding(binding: object) -> TargetBinding:
    _require_complete(binding, TargetBinding, STOP_TARGET_BINDING_INVALID)
    if (
        type(binding.environment) is not str
        or binding.environment != EXPECTED_ENVIRONMENT
        or type(binding.protected_source_sha) is not str
        or binding.protected_source_sha != PROTECTED_SOURCE_SHA
        or type(binding.protected_source_tree) is not str
        or binding.protected_source_tree != PROTECTED_SOURCE_TREE
        or type(binding.contract_version) is not str
        or binding.contract_version != CONTRACT_VERSION
        or type(binding.schema_version) is not str
        or binding.schema_version != SCHEMA_VERSION
        or type(binding.algorithm_version) is not str
        or binding.algorithm_version != ALGORITHM_VERSION
        or type(binding.workflow) is not str
        or binding.workflow != EXPECTED_WORKFLOW
        or not _valid_digest(binding.run_id)
        or not _is_utc(binding.issued_at)
        or not _is_utc(binding.expires_at)
        or binding.expires_at <= binding.issued_at
        or not _valid_digest(binding.snapshot_pair_id)
        or not _valid_digest(binding.payload_digest)
        or not _valid_digest(binding.manifest_digest)
        or not _valid_digest(binding.anchor_digest)
    ):
        _raise(STOP_TARGET_BINDING_INVALID)
    return binding


def target_binding_digest(binding: TargetBinding) -> str:
    validated = _validate_target_binding(binding)
    return _digest("target-binding", _target_material(validated, evidence=False))


def evidence_binding_digest(binding: TargetBinding) -> str:
    validated = _validate_target_binding(binding)
    return _digest("evidence-binding", _target_material(validated, evidence=True))


def validate_capability(capability: AdapterCapability) -> None:
    _require_complete(capability, AdapterCapability, STOP_CAPABILITY_INVALID)
    if (
        type(capability.methods) is not tuple
        or any(type(method) is not str for method in capability.methods)
        or capability.methods != ("select", "count")
        or type(capability.queries) is not tuple
        or not _strict_int(capability.max_snapshot_bytes, 1, 32_000_000)
    ):
        _raise(STOP_CAPABILITY_INVALID)
    seen: set[str] = set()
    for query in capability.queries:
        _require_complete(query, QueryCapability, STOP_CAPABILITY_INVALID)
        if (
            type(query.table) is not str
            or query.table not in TABLE_COLUMNS
            or query.table in seen
            or type(query.columns) is not tuple
            or any(type(item) is not str for item in query.columns)
            or query.columns != TABLE_COLUMNS[query.table]
            or type(query.filters) is not tuple
            or query.filters != ()
            or type(query.order) is not tuple
            or any(type(item) is not str for item in query.order)
            or query.order != ("id.asc",)
            or type(query.stable_tie_breaker) is not str
            or query.stable_tie_breaker != "id"
            or type(query.pagination_mode) is not str
            or query.pagination_mode != "KEYSET_ID_ASC"
            or not _strict_int(query.page_size, 1, 1000)
            or not _strict_int(query.max_rows, 1, 50_000)
            or not _strict_int(query.max_pages, 1, 50)
            or not _strict_int(query.timeout_seconds, 1, 15)
            or not _strict_int(query.retry_budget, 0, 2)
        ):
            _raise(STOP_CAPABILITY_INVALID)
        seen.add(query.table)
    if seen != set(TABLE_COLUMNS):
        _raise(STOP_CAPABILITY_INVALID)


def validate_read_timing(timing: ReadTiming, snapshot_pair_id: str) -> None:
    if type(snapshot_pair_id) is not str:
        _raise(STOP_CLOCK_TIMING_INVALID)
    _require_complete(timing, ReadTiming, STOP_CLOCK_TIMING_INVALID)
    if (
        type(timing.snapshot_pair_id) is not str
        or timing.snapshot_pair_id != snapshot_pair_id
        or type(timing.operation) is not str
        or timing.operation not in {"COUNT_INITIAL", "SELECT_PAGE", "COUNT_FINAL"}
        or type(timing.clock_source) is not str
        or timing.clock_source != READ_CLOCK_SOURCE
        or type(timing.capture_sequence) is not tuple
        or len(timing.capture_sequence) != 2
        or any(type(item) is not str for item in timing.capture_sequence)
        or timing.capture_sequence != READ_CAPTURE_SEQUENCE
        or not _is_utc(timing.started_at_utc)
        or not _is_utc(timing.ended_at_utc)
        or timing.started_at_utc >= timing.ended_at_utc
        or not _strict_int(timing.monotonic_started_ns, 0, 2**63 - 1)
        or not _strict_int(timing.monotonic_ended_ns, 1, 2**63 - 1)
        or timing.monotonic_started_ns >= timing.monotonic_ended_ns
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    utc_duration_ns = _duration_ns(timing.started_at_utc, timing.ended_at_utc)
    monotonic_duration_ns = timing.monotonic_ended_ns - timing.monotonic_started_ns
    if (
        utc_duration_ns > 15_000_000_000
        or monotonic_duration_ns > 15_000_000_000
        or abs(utc_duration_ns - monotonic_duration_ns) > CLOCK_DURATION_TOLERANCE_NS
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)


def _timing_within_target(timing: ReadTiming, target: TargetBinding) -> bool:
    return target.issued_at <= timing.started_at_utc and timing.ended_at_utc < target.expires_at


def row_fingerprint(
    table: str,
    target_digest: str,
    snapshot_pair_id: str,
    row: FrozenRow,
) -> str:
    if (
        type(table) is not str
        or table not in TABLE_COLUMNS
        or not _valid_digest(target_digest)
        or not _valid_digest(snapshot_pair_id)
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    validated = _validate_frozen_row(row, TABLE_COLUMNS[table], STOP_PAGINATION_INCOMPLETE)
    return _digest(
        "row",
        (table, target_digest, snapshot_pair_id, validated.values),
    )


def _validate_row_cursor(row: object, table: str, target_digest: str, pair_id: str) -> RowCursor:
    _require_complete(row, RowCursor, STOP_PAGINATION_INCOMPLETE)
    validated_row = _validate_frozen_row(
        row.row, TABLE_COLUMNS[table], STOP_PAGINATION_INCOMPLETE
    )
    row_id = _row_value(validated_row, "id")
    if (
        type(row.order_value) is not str
        or not row.order_value
        or type(row.tie_breaker) is not str
        or not row.tie_breaker
        or type(row_id) is not str
        or row_id != row.order_value
        or row.tie_breaker != row.order_value
        or not _valid_digest(row.row_fingerprint)
        or row.row_fingerprint
        != row_fingerprint(table, target_digest, pair_id, validated_row)
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    return row


def page_evidence_digest(
    table: str,
    target_digest: str,
    snapshot_pair_id: str,
    page: PageEvidence,
) -> str:
    if (
        type(table) is not str
        or table not in TABLE_COLUMNS
        or not _valid_digest(target_digest)
        or not _valid_digest(snapshot_pair_id)
        or type(page) is not PageEvidence
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    _require_complete(page, PageEvidence, STOP_PAGINATION_INCOMPLETE)
    if (
        type(page.after_id) not in {str, type(None)}
        or not _strict_int(page.requested_limit, 1, 1000)
        or type(page.rows) is not tuple
        or type(page.page_digest) is not str
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    row_fingerprints: list[str] = []
    for row in page.rows:
        validated = _validate_row_cursor(row, table, target_digest, snapshot_pair_id)
        row_fingerprints.append(validated.row_fingerprint)
    validate_read_timing(page.timing, snapshot_pair_id)
    return _digest(
        "page",
        (
            table,
            target_digest,
            snapshot_pair_id,
            page.after_id,
            page.requested_limit,
            tuple(row_fingerprints),
            _timing_material(page.timing),
        ),
    )


def _timing_material(timing: ReadTiming) -> tuple[object, ...]:
    return (
        timing.snapshot_pair_id,
        timing.operation,
        timing.clock_source,
        timing.capture_sequence,
        _timestamp_text(timing.started_at_utc),
        _timestamp_text(timing.ended_at_utc),
        timing.monotonic_started_ns,
        timing.monotonic_ended_ns,
    )


def _validate_pagination_shape(evidence: object) -> PaginationEvidence:
    _require_complete(evidence, PaginationEvidence, STOP_PAGINATION_INCOMPLETE)
    if (
        type(evidence.target_binding_digest) is not str
        or type(evidence.snapshot_pair_id) is not str
        or type(evidence.table) is not str
        or type(evidence.pages) is not tuple
        or type(evidence.inventory_digest) is not str
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    return evidence


def inventory_digest(evidence: PaginationEvidence) -> str:
    validated = _validate_pagination_shape(evidence)
    if validated.table not in TABLE_COLUMNS:
        _raise(STOP_PAGINATION_INCOMPLETE)
    if type(validated.initial_count) is not int or type(validated.final_count) is not int:
        _raise(STOP_COUNT_DRIFT)
    validate_read_timing(validated.initial_count_timing, validated.snapshot_pair_id)
    validate_read_timing(validated.final_count_timing, validated.snapshot_pair_id)
    row_fingerprints: list[str] = []
    page_timings: list[tuple[object, ...]] = []
    for page in validated.pages:
        _require_complete(page, PageEvidence, STOP_PAGINATION_INCOMPLETE)
        if type(page.rows) is not tuple:
            _raise(STOP_PAGINATION_INCOMPLETE)
        page_evidence_digest(
            validated.table,
            validated.target_binding_digest,
            validated.snapshot_pair_id,
            page,
        )
        for row in page.rows:
            cursor = _validate_row_cursor(
                row,
                validated.table,
                validated.target_binding_digest,
                validated.snapshot_pair_id,
            )
            row_fingerprints.append(cursor.row_fingerprint)
        validate_read_timing(page.timing, validated.snapshot_pair_id)
        page_timings.append(_timing_material(page.timing))
    return _digest(
        "inventory",
        (
            validated.target_binding_digest,
            validated.snapshot_pair_id,
            validated.table,
            validated.initial_count,
            validated.final_count,
            tuple(row_fingerprints),
            _timing_material(validated.initial_count_timing),
            tuple(page_timings),
            _timing_material(validated.final_count_timing),
        ),
    )


def validate_pagination(
    evidence: PaginationEvidence,
    target: TargetBinding,
    capability: AdapterCapability = GET_ONLY_CAPABILITY,
) -> tuple[str, ...]:
    validate_capability(capability)
    validated_target = _validate_target_binding(target)
    validated = _validate_pagination_shape(evidence)
    queries = {query.table: query for query in capability.queries}
    if (
        validated.table not in queries
        or validated.target_binding_digest != evidence_binding_digest(validated_target)
        or validated.snapshot_pair_id != validated_target.snapshot_pair_id
        or not _valid_digest(validated.snapshot_pair_id)
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    if (
        type(validated.initial_count) is not int
        or type(validated.final_count) is not int
        or validated.initial_count < 0
        or validated.final_count < 0
        or validated.initial_count != validated.final_count
    ):
        _raise(STOP_COUNT_DRIFT)
    query = queries[validated.table]
    if validated.initial_count > query.max_rows or len(validated.pages) > query.max_pages:
        _raise(STOP_PAGINATION_INCOMPLETE)
    validate_read_timing(validated.initial_count_timing, validated.snapshot_pair_id)
    validate_read_timing(validated.final_count_timing, validated.snapshot_pair_id)
    if (
        validated.initial_count_timing.operation != "COUNT_INITIAL"
        or validated.final_count_timing.operation != "COUNT_FINAL"
        or validated.initial_count_timing.monotonic_ended_ns
        >= validated.final_count_timing.monotonic_started_ns
        or validated.initial_count_timing.ended_at_utc
        >= validated.final_count_timing.started_at_utc
        or not _timing_within_target(validated.initial_count_timing, validated_target)
        or not _timing_within_target(validated.final_count_timing, validated_target)
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    if validated.initial_count == 0:
        if validated.pages or validated.inventory_digest != inventory_digest(validated):
            _raise(STOP_PAGINATION_INCOMPLETE)
        return ()

    expected_after_id: str | None = None
    page_digests: set[str] = set()
    row_fingerprints: set[str] = set()
    ordered: list[tuple[str, str]] = []
    observed_bytes = 0
    previous_timing = validated.initial_count_timing
    for page in validated.pages:
        _require_complete(page, PageEvidence, STOP_PAGINATION_INCOMPLETE)
        if (
            type(page.after_id) not in {str, type(None)}
            or page.after_id != expected_after_id
            or page.requested_limit != query.page_size
            or type(page.rows) is not tuple
            or not page.rows
            or len(page.rows) > page.requested_limit
            or not _valid_digest(page.page_digest)
            or page.page_digest in page_digests
        ):
            _raise(STOP_PAGINATION_INCOMPLETE)
        validate_read_timing(page.timing, validated.snapshot_pair_id)
        if (
            page.timing.operation != "SELECT_PAGE"
            or previous_timing.monotonic_ended_ns >= page.timing.monotonic_started_ns
            or previous_timing.ended_at_utc >= page.timing.started_at_utc
            or not _timing_within_target(page.timing, validated_target)
        ):
            _raise(STOP_CLOCK_TIMING_INVALID)
        if page.page_digest != page_evidence_digest(
            validated.table,
            validated.target_binding_digest,
            validated.snapshot_pair_id,
            page,
        ):
            _raise(STOP_PAGINATION_INCOMPLETE)
        page_digests.add(page.page_digest)
        for row in page.rows:
            cursor = _validate_row_cursor(
                row,
                validated.table,
                validated.target_binding_digest,
                validated.snapshot_pair_id,
            )
            if cursor.row_fingerprint in row_fingerprints:
                _raise(STOP_PAGINATION_INCOMPLETE)
            observed_bytes += _json_size(cursor.row.values)
            ordered.append((cursor.order_value, cursor.tie_breaker))
            row_fingerprints.add(cursor.row_fingerprint)
        expected_after_id = page.rows[-1].tie_breaker
        previous_timing = page.timing
    if (
        len(ordered) != validated.initial_count
        or ordered != sorted(ordered)
        or len(ordered) != len(set(ordered))
        or observed_bytes > capability.max_snapshot_bytes
        or validated.inventory_digest != inventory_digest(validated)
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    if (
        previous_timing.monotonic_ended_ns
        >= validated.final_count_timing.monotonic_started_ns
        or previous_timing.ended_at_utc
        >= validated.final_count_timing.started_at_utc
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    return tuple(
        row.row_fingerprint for page in validated.pages for row in page.rows
    )


def _pagination_bytes(evidence: PaginationEvidence) -> int:
    total = 0
    for page in evidence.pages:
        for row in page.rows:
            total += _json_size(row.row.values)
    return total


def _all_timings(items: tuple[PaginationEvidence, ...], reason: str) -> tuple[ReadTiming, ...]:
    if type(items) is not tuple or not items:
        _raise(reason)
    timings: list[ReadTiming] = []
    for item in items:
        _require_complete(item, PaginationEvidence, reason)
        if type(item.pages) is not tuple:
            _raise(reason)
        timings.append(item.initial_count_timing)
        for page in item.pages:
            _require_complete(page, PageEvidence, reason)
            timings.append(page.timing)
        timings.append(item.final_count_timing)
    return tuple(timings)


def _validate_course_booleans(payload: SnapshotPairPayloadEvidence) -> None:
    for snapshot in (1, 2):
        rows = _inventory_rows(
            payload, snapshot, "courses", STOP_MANIFEST_ANCHOR_MISMATCH
        )
        for row in rows:
            if type(_row_value(row, "is_active")) is not bool:
                _raise(STOP_MANIFEST_ANCHOR_MISMATCH)


def snapshot_payload_digest(evidence: SnapshotPairPayloadEvidence) -> str:
    _require_complete(evidence, SnapshotPairPayloadEvidence, STOP_PAGINATION_INCOMPLETE)
    if (
        not _valid_digest(evidence.snapshot_pair_id)
        or type(evidence.snapshot_1) is not tuple
        or type(evidence.snapshot_2) is not tuple
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    snapshots: list[tuple[tuple[str, str], ...]] = []
    for items in (evidence.snapshot_1, evidence.snapshot_2):
        material: list[tuple[str, str]] = []
        for item in items:
            validated = _validate_pagination_shape(item)
            if validated.table not in TABLE_COLUMNS or not _valid_digest(validated.inventory_digest):
                _raise(STOP_PAGINATION_INCOMPLETE)
            inventory_digest(validated)
            material.append((validated.table, validated.inventory_digest))
        material.sort()
        snapshots.append(tuple(material))
    return _digest(
        "snapshot-payload",
        (evidence.snapshot_pair_id, snapshots[0], snapshots[1]),
    )


def validate_snapshot_pair_payload(
    evidence: SnapshotPairPayloadEvidence,
    target: TargetBinding,
    *,
    max_snapshot_bytes: int = GET_ONLY_CAPABILITY.max_snapshot_bytes,
) -> None:
    validated_target = _validate_target_binding(target)
    _require_complete(evidence, SnapshotPairPayloadEvidence, STOP_PAGINATION_INCOMPLETE)
    if (
        not _valid_digest(evidence.snapshot_pair_id)
        or type(evidence.snapshot_1) is not tuple
        or type(evidence.snapshot_2) is not tuple
        or not _strict_int(max_snapshot_bytes, 1, GET_ONLY_CAPABILITY.max_snapshot_bytes)
    ):
        _raise(STOP_PAGINATION_INCOMPLETE)
    if evidence.snapshot_pair_id != validated_target.snapshot_pair_id:
        _raise(STOP_PAGINATION_INCOMPLETE)
    first: dict[str, PaginationEvidence] = {}
    second: dict[str, PaginationEvidence] = {}
    for source, destination in ((evidence.snapshot_1, first), (evidence.snapshot_2, second)):
        for item in source:
            validated = _validate_pagination_shape(item)
            if validated.table in destination:
                _raise(STOP_PAGINATION_INCOMPLETE)
            destination[validated.table] = validated
    if set(first) != set(TABLE_COLUMNS) or set(second) != set(TABLE_COLUMNS):
        _raise(STOP_PAGINATION_INCOMPLETE)
    _validate_course_booleans(evidence)
    total_bytes = 0
    for table in sorted(TABLE_COLUMNS):
        first_rows = validate_pagination(first[table], validated_target)
        second_rows = validate_pagination(second[table], validated_target)
        total_bytes += _pagination_bytes(first[table]) + _pagination_bytes(second[table])
        if first[table].initial_count != second[table].initial_count:
            _raise(STOP_COUNT_DRIFT)
        if first_rows != second_rows:
            _raise(STOP_SNAPSHOT_CONTENT_DRIFT)
    first_timings = _all_timings(evidence.snapshot_1, STOP_PAGINATION_INCOMPLETE)
    second_timings = _all_timings(evidence.snapshot_2, STOP_PAGINATION_INCOMPLETE)
    if (
        max(item.ended_at_utc for item in first_timings)
        >= min(item.started_at_utc for item in second_timings)
        or max(item.monotonic_ended_ns for item in first_timings)
        >= min(item.monotonic_started_ns for item in second_timings)
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    if total_bytes > max_snapshot_bytes * 2:
        _raise(STOP_PAGINATION_INCOMPLETE)
    expected_payload = snapshot_payload_digest(evidence)
    if evidence.payload_digest != expected_payload or validated_target.payload_digest != expected_payload:
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)


def _manifest_material(manifest: HistoricalFG3Manifest) -> tuple[object, ...]:
    return (
        manifest.builder_identity,
        manifest.builder_instance_identity,
        manifest.candidate_sha,
        manifest.candidate_tree,
        manifest.run_id,
        _timestamp_text(manifest.issued_at),
        manifest.complete,
        manifest.expected_observation_fingerprints,
        manifest.observation_categories,
        manifest.category_counts,
        manifest.published_count_tuple,
    )


def _validate_manifest_shape(manifest: object) -> HistoricalFG3Manifest:
    _require_complete(manifest, HistoricalFG3Manifest, STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        type(manifest.manifest_digest) is not str
        or type(manifest.builder_identity) is not str
        or type(manifest.builder_instance_identity) is not str
        or type(manifest.candidate_sha) is not str
        or type(manifest.candidate_tree) is not str
        or type(manifest.run_id) is not str
        or not _is_utc(manifest.issued_at)
        or type(manifest.complete) is not bool
        or type(manifest.expected_observation_fingerprints) is not tuple
        or any(type(item) is not str for item in manifest.expected_observation_fingerprints)
        or type(manifest.observation_categories) is not tuple
        or type(manifest.category_counts) is not tuple
        or type(manifest.published_count_tuple) is not tuple
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    for pair in manifest.observation_categories:
        if type(pair) is not tuple or len(pair) != 2 or any(type(item) is not str for item in pair):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    for pair in manifest.category_counts:
        if (
            type(pair) is not tuple
            or len(pair) != 2
            or type(pair[0]) is not str
            or type(pair[1]) is not int
        ):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    if len(manifest.published_count_tuple) != 3 or any(
        type(item) is not int for item in manifest.published_count_tuple
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    return manifest


def historical_manifest_digest(manifest: HistoricalFG3Manifest) -> str:
    validated = _validate_manifest_shape(manifest)
    return _digest("historical-manifest", _manifest_material(validated))


def historical_anchor_digest(anchor: HistoricalFG3Anchor) -> str:
    _require_complete(anchor, HistoricalFG3Anchor, STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        type(anchor.anchor_digest) is not str
        or type(anchor.manifest_digest) is not str
        or type(anchor.provider_identity) is not str
        or type(anchor.provider_instance_identity) is not str
        or type(anchor.provenance) is not str
        or type(anchor.candidate_sha) is not str
        or type(anchor.candidate_tree) is not str
        or type(anchor.run_id) is not str
        or not _is_utc(anchor.issued_at)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    return _digest(
        "historical-anchor",
        (
            anchor.manifest_digest,
            anchor.provider_identity,
            anchor.provider_instance_identity,
            anchor.provenance,
            anchor.candidate_sha,
            anchor.candidate_tree,
            anchor.run_id,
            _timestamp_text(anchor.issued_at),
        ),
    )


def manifest_builder_receipt_digest(receipt: ManifestBuilderEvidenceReceipt) -> str:
    _require_complete(receipt, ManifestBuilderEvidenceReceipt, STOP_ANCHOR_NOT_INDEPENDENT)
    if any(
        type(value) is not str
        for value in (
            receipt.builder_identity,
            receipt.builder_instance_identity,
            receipt.manifest_digest,
            receipt.evidence_digest,
        )
    ):
        _raise(STOP_ANCHOR_NOT_INDEPENDENT)
    return _digest(
        "manifest-builder-receipt",
        (
            receipt.builder_identity,
            receipt.builder_instance_identity,
            receipt.manifest_digest,
        ),
    )


def anchor_provider_receipt_digest(receipt: AnchorProviderEvidenceReceipt) -> str:
    _require_complete(receipt, AnchorProviderEvidenceReceipt, STOP_ANCHOR_NOT_INDEPENDENT)
    if any(
        type(value) is not str
        for value in (
            receipt.provider_identity,
            receipt.provider_instance_identity,
            receipt.manifest_digest,
            receipt.anchor_digest,
            receipt.evidence_digest,
        )
    ):
        _raise(STOP_ANCHOR_NOT_INDEPENDENT)
    return _digest(
        "anchor-provider-receipt",
        (
            receipt.provider_identity,
            receipt.provider_instance_identity,
            receipt.manifest_digest,
            receipt.anchor_digest,
        ),
    )


def historical_observation_fingerprint(item: FG3HistoricalObservationEvidence) -> str:
    _require_complete(item, FG3HistoricalObservationEvidence, STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        type(item.observation_fingerprint) is not str
        or not _valid_digest(item.target_binding_digest)
        or not _valid_digest(item.snapshot_pair_id)
        or not _valid_digest(item.course_fingerprint)
        or not _valid_digest(item.run_id)
        or type(item.category) is not str
        or type(item.active_at_snapshot_1) is not bool
        or not _is_utc(item.observed_at)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    return _digest(
        "historical-observation",
        (
            item.target_binding_digest,
            item.snapshot_pair_id,
            item.course_fingerprint,
            item.run_id,
            item.category,
            item.active_at_snapshot_1,
            _timestamp_text(item.observed_at),
        ),
    )


def prior_mutation_fingerprint(
    course_fingerprint: str,
    antecedent_run_fingerprint: str,
    antecedent_observed_at: datetime,
    mutation_kind: str,
    historical_observation_fingerprint: str,
) -> str:
    if (
        not _valid_digest(course_fingerprint)
        or not _valid_digest(antecedent_run_fingerprint)
        or not _is_utc(antecedent_observed_at)
        or type(mutation_kind) is not str
        or mutation_kind not in {"DEACTIVATION"}
        or not _valid_digest(historical_observation_fingerprint)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    return _digest(
        "prior-mutation",
        (
            course_fingerprint,
            antecedent_run_fingerprint,
            _timestamp_text(antecedent_observed_at),
            mutation_kind,
            historical_observation_fingerprint,
        ),
    )


def _snapshot_bounds(payload: object, reason: str) -> tuple[datetime, datetime, datetime, datetime]:
    _require_complete(payload, SnapshotPairPayloadEvidence, reason)
    if (
        not _valid_digest(payload.snapshot_pair_id)
        or type(payload.snapshot_1) is not tuple
        or type(payload.snapshot_2) is not tuple
    ):
        _raise(reason)
    first = _all_timings(payload.snapshot_1, reason)
    second = _all_timings(payload.snapshot_2, reason)
    for timing in (*first, *second):
        validate_read_timing(timing, payload.snapshot_pair_id)
    return (
        min(item.started_at_utc for item in first),
        max(item.ended_at_utc for item in first),
        min(item.started_at_utc for item in second),
        max(item.ended_at_utc for item in second),
    )


def _snapshot_monotonic_bounds(payload: object, reason: str) -> tuple[int, int]:
    _require_complete(payload, SnapshotPairPayloadEvidence, reason)
    first = _all_timings(payload.snapshot_1, reason)
    second = _all_timings(payload.snapshot_2, reason)
    for timing in (*first, *second):
        validate_read_timing(timing, payload.snapshot_pair_id)
    return (
        max(item.monotonic_ended_ns for item in first),
        min(item.monotonic_started_ns for item in second),
    )


def validate_historical_anchor(
    manifest: HistoricalFG3Manifest,
    anchor: HistoricalFG3Anchor,
    builder_receipt: ManifestBuilderEvidenceReceipt,
    provider_receipt: AnchorProviderEvidenceReceipt,
    target: TargetBinding,
    snapshot_payload: SnapshotPairPayloadEvidence,
    historical_observations: tuple[FG3HistoricalObservationEvidence, ...],
    evaluated_at: datetime,
) -> None:
    validated_target = _validate_target_binding(target)
    validated_manifest = _validate_manifest_shape(manifest)
    if (
        type(anchor) is not HistoricalFG3Anchor
        or type(builder_receipt) is not ManifestBuilderEvidenceReceipt
        or type(provider_receipt) is not AnchorProviderEvidenceReceipt
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    _require_complete(anchor, HistoricalFG3Anchor, STOP_MANIFEST_ANCHOR_MISMATCH)
    _require_complete(
        builder_receipt,
        ManifestBuilderEvidenceReceipt,
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )
    _require_complete(
        provider_receipt,
        AnchorProviderEvidenceReceipt,
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )
    _require_complete(
        snapshot_payload,
        SnapshotPairPayloadEvidence,
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )
    if type(historical_observations) is not tuple or not historical_observations:
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    if not _is_utc(evaluated_at):
        _raise(STOP_CLOCK_TIMING_INVALID)
    observation_times: list[datetime] = []
    for observation in historical_observations:
        _require_complete(
            observation,
            FG3HistoricalObservationEvidence,
            STOP_MANIFEST_ANCHOR_MISMATCH,
        )
        if not _is_utc(observation.observed_at):
            _raise(STOP_CLOCK_TIMING_INVALID)
        observation_times.append(observation.observed_at)
    snapshot_1_started, _, _, _ = _snapshot_bounds(
        snapshot_payload, STOP_MANIFEST_ANCHOR_MISMATCH
    )
    if (
        not _is_utc(anchor.issued_at)
        or not (
            validated_target.issued_at
            <= min(observation_times)
            <= max(observation_times)
            <= validated_manifest.issued_at
            <= anchor.issued_at
            < snapshot_1_started
            <= evaluated_at
            < validated_target.expires_at
        )
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    anchor_digest_value = historical_anchor_digest(anchor)
    builder_digest_value = manifest_builder_receipt_digest(builder_receipt)
    provider_digest_value = anchor_provider_receipt_digest(provider_receipt)
    if (
        not _valid_identity(validated_manifest.builder_identity)
        or not _valid_identity(validated_manifest.builder_instance_identity)
        or not _valid_identity(anchor.provider_identity)
        or not _valid_identity(anchor.provider_instance_identity)
        or validated_manifest.builder_identity == anchor.provider_identity
        or validated_manifest.builder_instance_identity == anchor.provider_instance_identity
    ):
        _raise(STOP_ANCHOR_NOT_INDEPENDENT)
    fingerprints = validated_manifest.expected_observation_fingerprints
    categories_pairs = validated_manifest.observation_categories
    counts_pairs = validated_manifest.category_counts
    if (
        not validated_manifest.complete
        or not fingerprints
        or any(not _valid_digest(item) for item in fingerprints)
        or len(fingerprints) != len(set(fingerprints))
        or len(categories_pairs) != len(set(categories_pairs))
        or len(counts_pairs) != len(set(counts_pairs))
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    category_keys = tuple(pair[0] for pair in categories_pairs)
    count_keys = tuple(pair[0] for pair in counts_pairs)
    if len(category_keys) != len(set(category_keys)) or len(count_keys) != len(set(count_keys)):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    categories = {key: value for key, value in categories_pairs}
    counts = {key: value for key, value in counts_pairs}
    observed_counts = {
        category: sum(value == category for value in categories.values())
        for category in set(categories.values())
    }
    if (
        set(categories) != set(fingerprints)
        or counts != observed_counts
        or counts != dict(FG3_HISTORICAL_CATEGORY_COUNTS)
        or validated_manifest.published_count_tuple != (24, 2, 1)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        validated_manifest.manifest_digest != historical_manifest_digest(validated_manifest)
        or anchor.anchor_digest != anchor_digest_value
        or anchor.provenance != "INDEPENDENT_HISTORICAL_FG3_SOURCE"
        or anchor.manifest_digest != validated_manifest.manifest_digest
        or anchor.candidate_sha != validated_manifest.candidate_sha
        or anchor.candidate_tree != validated_manifest.candidate_tree
        or anchor.run_id != validated_manifest.run_id
        or validated_manifest.candidate_sha != validated_target.protected_source_sha
        or validated_manifest.candidate_tree != validated_target.protected_source_tree
        or validated_manifest.run_id != validated_target.run_id
        or validated_manifest.manifest_digest != validated_target.manifest_digest
        or anchor.anchor_digest != validated_target.anchor_digest
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        builder_receipt.builder_identity != validated_manifest.builder_identity
        or builder_receipt.builder_instance_identity
        != validated_manifest.builder_instance_identity
        or builder_receipt.manifest_digest != validated_manifest.manifest_digest
        or builder_receipt.evidence_digest != builder_digest_value
        or provider_receipt.provider_identity != anchor.provider_identity
        or provider_receipt.provider_instance_identity
        != anchor.provider_instance_identity
        or provider_receipt.manifest_digest != validated_manifest.manifest_digest
        or provider_receipt.anchor_digest != anchor.anchor_digest
        or provider_receipt.evidence_digest != provider_digest_value
    ):
        _raise(STOP_ANCHOR_NOT_INDEPENDENT)


def _inventory(
    payload: SnapshotPairPayloadEvidence,
    snapshot: int,
    table: str,
    reason: str = STOP_PAGINATION_INCOMPLETE,
) -> PaginationEvidence:
    _require_complete(payload, SnapshotPairPayloadEvidence, reason)
    if type(snapshot) is not int or snapshot not in {1, 2} or type(table) is not str:
        _raise(reason)
    items = payload.snapshot_1 if snapshot == 1 else payload.snapshot_2
    if type(items) is not tuple:
        _raise(reason)
    for item in items:
        _require_complete(item, PaginationEvidence, reason)
        if type(item.table) is not str:
            _raise(reason)
        if item.table == table:
            return item
    _raise(reason)


def _inventory_rows(
    payload: SnapshotPairPayloadEvidence,
    snapshot: int,
    table: str,
    reason: str = STOP_PAGINATION_INCOMPLETE,
) -> tuple[FrozenRow, ...]:
    inventory = _inventory(payload, snapshot, table, reason)
    if type(inventory.pages) is not tuple:
        _raise(reason)
    rows: list[FrozenRow] = []
    for page in inventory.pages:
        _require_complete(page, PageEvidence, reason)
        if type(page.rows) is not tuple:
            _raise(reason)
        for cursor in page.rows:
            validated = _validate_row_cursor(
                cursor,
                table,
                inventory.target_binding_digest,
                inventory.snapshot_pair_id,
            )
            rows.append(validated.row)
    return tuple(rows)


def validate_fg3_cohort(
    evidence: FG3CohortEvidence,
    manifest: HistoricalFG3Manifest,
    target: TargetBinding,
    snapshot_payload: SnapshotPairPayloadEvidence,
) -> tuple[frozenset[str], frozenset[str]]:
    validated_target = _validate_target_binding(target)
    validated_manifest = _validate_manifest_shape(manifest)
    _require_complete(evidence, FG3CohortEvidence, STOP_MANIFEST_ANCHOR_MISMATCH)
    _require_complete(
        snapshot_payload,
        SnapshotPairPayloadEvidence,
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )
    if (
        type(evidence.courses) is not tuple
        or type(evidence.prior_mutations) is not tuple
        or type(evidence.historical_observations) is not tuple
        or len(evidence.historical_observations) != 27
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        not _valid_digest(evidence.target_binding_digest)
        or not _valid_digest(evidence.snapshot_pair_id)
        or not _valid_digest(evidence.run_id)
        or not _valid_digest(snapshot_payload.snapshot_pair_id)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    target_digest = evidence_binding_digest(validated_target)
    if (
        evidence.target_binding_digest != target_digest
        or evidence.snapshot_pair_id != validated_target.snapshot_pair_id
        or evidence.run_id != validated_target.run_id
        or validated_manifest.run_id != evidence.run_id
        or validated_manifest.manifest_digest != validated_target.manifest_digest
        or evidence.snapshot_pair_id != snapshot_payload.snapshot_pair_id
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    snapshot_1_started, _, _, _ = _snapshot_bounds(
        snapshot_payload, STOP_MANIFEST_ANCHOR_MISMATCH
    )
    first_rows = _inventory_rows(
        snapshot_payload, 1, "courses", STOP_MANIFEST_ANCHOR_MISMATCH
    )
    second_rows = _inventory_rows(
        snapshot_payload, 2, "courses", STOP_MANIFEST_ANCHOR_MISMATCH
    )
    for row in (*first_rows, *second_rows):
        if type(_row_value(row, "is_active")) is not bool:
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    first_by_fingerprint = {
        row_fingerprint("courses", target_digest, evidence.snapshot_pair_id, row): row
        for row in first_rows
    }
    manifest_categories = {key: value for key, value in validated_manifest.observation_categories}
    historical: set[str] = set()
    observations_by_fingerprint: dict[str, FG3HistoricalObservationEvidence] = {}
    for item in evidence.historical_observations:
        _require_complete(
            item,
            FG3HistoricalObservationEvidence,
            STOP_MANIFEST_ANCHOR_MISMATCH,
        )
        computed_fingerprint = historical_observation_fingerprint(item)
        if not (
            validated_target.issued_at
            <= item.observed_at
            <= validated_manifest.issued_at
            < snapshot_1_started
        ):
            _raise(STOP_CLOCK_TIMING_INVALID)
        if (
            item.observation_fingerprint in historical
            or item.observation_fingerprint != computed_fingerprint
            or item.target_binding_digest != target_digest
            or item.snapshot_pair_id != evidence.snapshot_pair_id
            or item.course_fingerprint not in first_by_fingerprint
            or item.category != manifest_categories.get(item.observation_fingerprint)
        ):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
        row_active = _row_value(first_by_fingerprint[item.course_fingerprint], "is_active")
        if type(row_active) is not bool or item.active_at_snapshot_1 != row_active:
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
        historical.add(item.observation_fingerprint)
        observations_by_fingerprint[item.observation_fingerprint] = item
    primary: set[str] = set()
    seen_courses: set[str] = set()
    for course in evidence.courses:
        _require_complete(
            course,
            FG3CourseCohortEvidence,
            STOP_MANIFEST_ANCHOR_MISMATCH,
        )
        if (
            not _valid_digest(course.course_fingerprint)
            or course.course_fingerprint in seen_courses
            or type(course.active_at_snapshot_1) is not bool
            or type(course.related_to_current_run) is not bool
            or not course.related_to_current_run
        ):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
        seen_courses.add(course.course_fingerprint)
        row = first_by_fingerprint.get(course.course_fingerprint)
        if row is None or course.active_at_snapshot_1 != _row_value(row, "is_active"):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
        if course.active_at_snapshot_1:
            primary.add(course.course_fingerprint)
    required_active = {
        fingerprint
        for fingerprint, row in first_by_fingerprint.items()
        if _row_value(row, "is_active") is True
    }
    required_inactive = set(first_by_fingerprint) - required_active
    mutations_by_course: dict[str, list[FG3PriorMutationEvidence]] = {}
    seen_mutation_fingerprints: set[str] = set()
    for mutation in evidence.prior_mutations:
        _require_complete(
            mutation,
            FG3PriorMutationEvidence,
            STOP_MANIFEST_ANCHOR_MISMATCH,
        )
        observation = observations_by_fingerprint.get(
            mutation.historical_observation_fingerprint
        )
        if (
            not _valid_digest(mutation.course_fingerprint)
            or not _valid_digest(mutation.antecedent_run_fingerprint)
            or not _valid_digest(mutation.mutation_fingerprint)
            or not _valid_digest(mutation.historical_observation_fingerprint)
            or mutation.mutation_fingerprint in seen_mutation_fingerprints
            or mutation.course_fingerprint not in required_inactive
            or mutation.antecedent_run_fingerprint == evidence.run_id
            or mutation.mutation_kind != "DEACTIVATION"
            or observation is None
        ):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
        if (
            not _is_utc(mutation.antecedent_observed_at)
            or mutation.antecedent_observed_at >= snapshot_1_started
            or mutation.antecedent_observed_at < validated_target.issued_at
        ):
            _raise(STOP_CLOCK_TIMING_INVALID)
        if (
            observation.course_fingerprint != mutation.course_fingerprint
            or observation.category != "DEACTIVATION"
            or observation.active_at_snapshot_1 is not False
            or observation.run_id != mutation.antecedent_run_fingerprint
            or observation.observed_at != mutation.antecedent_observed_at
        ):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
        if mutation.mutation_fingerprint != prior_mutation_fingerprint(
            mutation.course_fingerprint,
            mutation.antecedent_run_fingerprint,
            mutation.antecedent_observed_at,
            mutation.mutation_kind,
            mutation.historical_observation_fingerprint,
        ):
            _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
        seen_mutation_fingerprints.add(mutation.mutation_fingerprint)
        mutations_by_course.setdefault(mutation.course_fingerprint, []).append(mutation)
    if (
        primary != required_active
        or seen_courses != set(first_by_fingerprint)
        or set(mutations_by_course) != required_inactive
        or any(len(items) != 1 for items in mutations_by_course.values())
        or historical != set(validated_manifest.expected_observation_fingerprints)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    return frozenset(primary), frozenset(mutations_by_course)


def profile_source_fingerprints(
    profile_fingerprint: str,
    row: FrozenRow,
) -> frozenset[str]:
    if not _valid_digest(profile_fingerprint):
        _raise(STOP_TARGET_BINDING_INVALID)
    validated = _validate_frozen_row(
        row, TABLE_COLUMNS["institution_site_profiles"], STOP_TARGET_BINDING_INVALID
    )
    discovery_mode = _row_value(validated, "discovery_mode")
    configured = tuple(
        (name, _row_value(validated, name))
        for name in ("seed_urls", "catalog_url_patterns", "allowed_url_patterns")
    )
    if type(discovery_mode) is not str or not discovery_mode:
        _raise(STOP_TARGET_BINDING_INVALID)
    for _, values in configured:
        if (
            type(values) is not tuple
            or any(type(value) is not str or not value for value in values)
            or len(values) != len(set(values))
        ):
            _raise(STOP_TARGET_BINDING_INVALID)
    if sum(len(values) for _, values in configured) > MAX_SOURCES_PER_PROFILE:
        _raise(STOP_TARGET_BINDING_INVALID)
    full_configuration = (discovery_mode, *tuple(values for _, values in configured))
    fingerprints = frozenset(
        _digest(
            "profile-source",
            (profile_fingerprint, full_configuration, source_kind, source_value),
        )
        for source_kind, values in configured
        for source_value in values
    )
    if not fingerprints:
        _raise(STOP_TARGET_BINDING_INVALID)
    return fingerprints


def _eligible_profile_sources(
    target: TargetBinding, payload: SnapshotPairPayloadEvidence
) -> frozenset[tuple[str, str]]:
    rows = _inventory_rows(
        payload, 1, "institution_site_profiles", STOP_TARGET_BINDING_INVALID
    )
    target_digest = evidence_binding_digest(target)
    eligible: set[tuple[str, str]] = set()
    for row in rows:
        discovery_enabled = _row_value(row, "discovery_enabled")
        pipeline_enabled = _row_value(row, "pipeline_enabled")
        pipeline_ready = _row_value(row, "pipeline_ready")
        circuit_open = _row_value(row, "circuit_open")
        if (
            type(discovery_enabled) is not bool
            or type(pipeline_enabled) not in {bool, type(None)}
            or type(pipeline_ready) is not bool
            or type(circuit_open) is not bool
        ):
            _raise(STOP_TARGET_BINDING_INVALID)
        pipeline_gate = pipeline_ready if pipeline_enabled is None else pipeline_enabled
        if discovery_enabled and pipeline_gate and not circuit_open:
            profile_fingerprint = row_fingerprint(
                "institution_site_profiles",
                target_digest,
                target.snapshot_pair_id,
                row,
            )
            profile_sources = profile_source_fingerprints(profile_fingerprint, row)
            if len(eligible) + len(profile_sources) > MAX_PROFILE_SOURCE_PAIRS:
                _raise(STOP_TARGET_BINDING_INVALID)
            eligible.update(
                (profile_fingerprint, source_fingerprint)
                for source_fingerprint in profile_sources
            )
    return frozenset(eligible)


def validate_source_observation(
    request: SourceObservationRequest,
    evidence: SourceObservationEvidence,
    target: TargetBinding,
    snapshot_payload: SnapshotPairPayloadEvidence,
    evaluated_at: datetime,
) -> None:
    _require_complete(request, SourceObservationRequest, STOP_TARGET_BINDING_INVALID)
    _require_complete(evidence, SourceObservationEvidence, STOP_TARGET_BINDING_INVALID)
    validated_target = _validate_target_binding(target)
    _require_complete(
        snapshot_payload,
        SnapshotPairPayloadEvidence,
        STOP_TARGET_BINDING_INVALID,
    )
    if not _is_utc(evaluated_at):
        _raise(STOP_CLOCK_TIMING_INVALID)
    request_strings = (
        request.target_binding_digest,
        request.snapshot_pair_id,
        request.profile_fingerprint,
        request.source_fingerprint,
        request.run_fingerprint,
        request.cohort_fingerprint,
    )
    evidence_strings = (
        evidence.target_binding_digest,
        evidence.snapshot_pair_id,
        evidence.profile_fingerprint,
        evidence.source_fingerprint,
        evidence.run_fingerprint,
        evidence.cohort_fingerprint,
        evidence.terminal_reason,
    )
    if any(type(value) is not str for value in (*request_strings, *evidence_strings)):
        _raise(STOP_TARGET_BINDING_INVALID)
    methods = request.method_sequence
    if (
        type(evidence.attempt_timings) is not tuple
        or type(methods) is not tuple
        or len(evidence.attempt_timings) != len(methods)
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    if any(type(method) is not str for method in methods):
        _raise(STOP_TARGET_BINDING_INVALID)
    if (
        request.target_binding_digest != evidence_binding_digest(validated_target)
        or evidence.target_binding_digest != request.target_binding_digest
        or request.snapshot_pair_id != validated_target.snapshot_pair_id
        or request.run_fingerprint != validated_target.run_id
        or methods not in SOURCE_ATTEMPT_GRAMMAR
        or not _strict_int(request.max_attempts, 1, 3)
        or request.max_attempts != len(methods)
        or evidence.snapshot_pair_id != request.snapshot_pair_id
        or evidence.profile_fingerprint != request.profile_fingerprint
        or evidence.source_fingerprint != request.source_fingerprint
        or evidence.run_fingerprint != request.run_fingerprint
        or evidence.cohort_fingerprint != request.cohort_fingerprint
        or type(evidence.method_sequence) is not tuple
        or any(type(method) is not str for method in evidence.method_sequence)
        or evidence.method_sequence != methods
        or not _strict_int(evidence.attempts, 1, 3)
        or evidence.attempts != len(methods)
        or evidence.terminal_reason
        not in {
            "SOURCE_ACCESSIBLE",
            "SOURCE_GET_403",
            "SOURCE_TIMEOUT",
            "SOURCE_DNS_FAILURE",
            "SOURCE_TLS_FAILURE",
            "SOURCE_TRANSPORT_FAILURE",
        }
        or any(
            not _valid_digest(value)
            for value in (
                request.snapshot_pair_id,
                request.profile_fingerprint,
                request.source_fingerprint,
                request.run_fingerprint,
                request.cohort_fingerprint,
            )
        )
    ):
        _raise(STOP_TARGET_BINDING_INVALID)
    snapshot_1_started, snapshot_1_closed, snapshot_2_started, snapshot_2_closed = (
        _snapshot_bounds(snapshot_payload, STOP_TARGET_BINDING_INVALID)
    )
    snapshot_1_monotonic_closed, snapshot_2_monotonic_started = (
        _snapshot_monotonic_bounds(snapshot_payload, STOP_TARGET_BINDING_INVALID)
    )
    if (
        not (
            validated_target.issued_at <= snapshot_1_started <= snapshot_1_closed
            < snapshot_2_started <= snapshot_2_closed <= evaluated_at
            < validated_target.expires_at
        )
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    previous: SourceAttemptTiming | None = None
    for index, timing in enumerate(evidence.attempt_timings):
        _require_complete(timing, SourceAttemptTiming, STOP_CLOCK_TIMING_INVALID)
        if (
            type(timing.method) is not str
            or timing.method != methods[index]
            or not _is_utc(timing.started_at_utc)
            or not _is_utc(timing.ended_at_utc)
            or not _strict_int(timing.monotonic_started_ns, 0, 2**63 - 1)
            or not _strict_int(timing.monotonic_ended_ns, 1, 2**63 - 1)
        ):
            _raise(STOP_CLOCK_TIMING_INVALID)
        utc_duration_ns = _duration_ns(timing.started_at_utc, timing.ended_at_utc)
        monotonic_duration_ns = timing.monotonic_ended_ns - timing.monotonic_started_ns
        if (
            utc_duration_ns <= 0
            or monotonic_duration_ns <= 0
            or utc_duration_ns > SOURCE_ATTEMPT_BUDGET_NS
            or monotonic_duration_ns > SOURCE_ATTEMPT_BUDGET_NS
            or abs(utc_duration_ns - monotonic_duration_ns)
            > CLOCK_DURATION_TOLERANCE_NS
            or timing.started_at_utc <= snapshot_1_closed
            or timing.ended_at_utc >= snapshot_2_started
            or timing.started_at_utc < validated_target.issued_at
            or timing.ended_at_utc >= validated_target.expires_at
            or timing.ended_at_utc > evaluated_at
            or timing.monotonic_started_ns <= snapshot_1_monotonic_closed
            or timing.monotonic_ended_ns >= snapshot_2_monotonic_started
        ):
            _raise(STOP_CLOCK_TIMING_INVALID)
        if previous is not None and (
            previous.ended_at_utc > timing.started_at_utc
            or previous.monotonic_ended_ns > timing.monotonic_started_ns
        ):
            _raise(STOP_CLOCK_TIMING_INVALID)
        previous = timing
    if (
        previous is None
        or not _is_utc(evidence.observed_at)
        or evidence.observed_at != previous.ended_at_utc
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)


def validate_source_coverage(
    bundles: tuple[SourceObservationBundle, ...],
    target: TargetBinding,
    snapshot_payload: SnapshotPairPayloadEvidence,
    evaluated_at: datetime,
) -> None:
    validated_target = _validate_target_binding(target)
    if type(bundles) is not tuple or type(snapshot_payload) is not SnapshotPairPayloadEvidence:
        _raise(STOP_TARGET_BINDING_INVALID)
    _require_complete(
        snapshot_payload,
        SnapshotPairPayloadEvidence,
        STOP_TARGET_BINDING_INVALID,
    )
    eligible = _eligible_profile_sources(validated_target, snapshot_payload)
    observed_pairs: set[tuple[str, str]] = set()
    for bundle in bundles:
        _require_complete(bundle, SourceObservationBundle, STOP_TARGET_BINDING_INVALID)
        _require_complete(
            bundle.request,
            SourceObservationRequest,
            STOP_TARGET_BINDING_INVALID,
        )
        fingerprint = bundle.request.profile_fingerprint
        source_fingerprint = bundle.request.source_fingerprint
        if type(fingerprint) is not str or type(source_fingerprint) is not str:
            _raise(STOP_TARGET_BINDING_INVALID)
        unit = (fingerprint, source_fingerprint)
        if unit in observed_pairs or unit not in eligible:
            _raise(STOP_TARGET_BINDING_INVALID)
        validate_source_observation(
            bundle.request,
            bundle.evidence,
            validated_target,
            snapshot_payload,
            evaluated_at,
        )
        observed_pairs.add(unit)
    if observed_pairs != set(eligible):
        _raise(STOP_TARGET_BINDING_INVALID)


def classify_lifecycle_proxy(
    *,
    last_harvested_at: str | None,
    created_at: str | None,
    observed_at: datetime,
) -> LifecycleProxy:
    if type(last_harvested_at) not in {str, type(None)} or type(created_at) not in {
        str,
        type(None),
    }:
        _raise(STOP_TARGET_BINDING_INVALID)
    if not _is_utc(observed_at):
        _raise(STOP_CLOCK_TIMING_INVALID)
    if last_harvested_at is not None:
        raw = last_harvested_at
        origin = "LAST_HARVESTED_AT_PROXY"
    elif created_at is not None:
        raw = created_at
        origin = "CREATED_AT_PROXY"
    else:
        return LifecycleProxy(
            last_harvested_at,
            created_at,
            observed_at,
            None,
            "NONE",
            None,
            "AGE_UNKNOWN",
        )
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if not _is_utc(parsed):
        return LifecycleProxy(
            last_harvested_at,
            created_at,
            observed_at,
            raw,
            origin,
            None,
            "AGE_UNKNOWN",
        )
    parsed = parsed.astimezone(timezone.utc)
    delta = observed_at - parsed
    age = int(delta.total_seconds())
    classification = (
        "FUTURE_TIMESTAMP"
        if parsed > observed_at
        else "STALE"
        if delta > _STALE_AFTER
        else "NOT_STALE"
    )
    return LifecycleProxy(
        last_harvested_at,
        created_at,
        observed_at,
        _timestamp_text(parsed),
        origin,
        age,
        classification,
    )


def lifecycle_allows_pass(observations: tuple[LifecycleProxy, ...]) -> bool:
    if type(observations) is not tuple:
        _raise(STOP_TARGET_BINDING_INVALID)
    if not observations:
        return False
    for item in observations:
        if type(item) is not LifecycleProxy or not _valid_lifecycle_proxy_shape(item):
            _raise(STOP_TARGET_BINDING_INVALID)
        expected = classify_lifecycle_proxy(
            last_harvested_at=item.last_harvested_at,
            created_at=item.created_at,
            observed_at=item.observed_at,
        )
        if item != expected or item.classification != "NOT_STALE":
            return False
    return True


def _valid_lifecycle_proxy_shape(proxy: LifecycleProxy) -> bool:
    _require_complete(proxy, LifecycleProxy, STOP_TARGET_BINDING_INVALID)
    return (
        type(proxy.last_harvested_at) in {str, type(None)}
        and type(proxy.created_at) in {str, type(None)}
        and _is_utc(proxy.observed_at)
        and type(proxy.timestamp_used) in {str, type(None)}
        and type(proxy.timestamp_origin) is str
        and type(proxy.calculated_age_seconds) in {int, type(None)}
        and type(proxy.classification) is str
    )


def validate_lifecycle_evidence(
    evidence: tuple[LifecycleEvidence, ...],
    target: TargetBinding,
    snapshot_payload: SnapshotPairPayloadEvidence,
    evaluated_at: datetime,
) -> None:
    validated_target = _validate_target_binding(target)
    if type(evidence) is not tuple or type(snapshot_payload) is not SnapshotPairPayloadEvidence:
        _raise(STOP_TARGET_BINDING_INVALID)
    _require_complete(
        snapshot_payload,
        SnapshotPairPayloadEvidence,
        STOP_TARGET_BINDING_INVALID,
    )
    if not _is_utc(evaluated_at):
        _raise(STOP_CLOCK_TIMING_INVALID)
    rows = _inventory_rows(
        snapshot_payload, 1, "staging_raw", STOP_TARGET_BINDING_INVALID
    )
    target_digest = evidence_binding_digest(validated_target)
    expected: dict[str, FrozenRow] = {}
    for row in rows:
        if _row_value(row, "status") == "processing":
            fingerprint = row_fingerprint(
                "staging_raw", target_digest, validated_target.snapshot_pair_id, row
            )
            expected[fingerprint] = row
    observed: set[str] = set()
    for item in evidence:
        if type(item) is LifecycleEvidence:
            _require_complete(item, LifecycleEvidence, STOP_TARGET_BINDING_INVALID)
        if (
            type(item) is not LifecycleEvidence
            or not _valid_digest(item.staging_row_fingerprint)
            or item.staging_row_fingerprint in observed
            or type(item.proxy) is not LifecycleProxy
            or not _valid_lifecycle_proxy_shape(item.proxy)
        ):
            _raise(STOP_TARGET_BINDING_INVALID)
        row = expected.get(item.staging_row_fingerprint)
        if row is None:
            _raise(STOP_TARGET_BINDING_INVALID)
        last_harvested = _row_value(row, "last_harvested_at")
        created = _row_value(row, "created_at")
        if type(last_harvested) not in {str, type(None)} or type(created) not in {
            str,
            type(None),
        }:
            _raise(STOP_TARGET_BINDING_INVALID)
        expected_proxy = classify_lifecycle_proxy(
            last_harvested_at=last_harvested,
            created_at=created,
            observed_at=evaluated_at,
        )
        if item.proxy != expected_proxy:
            _raise(STOP_TARGET_BINDING_INVALID)
        observed.add(item.staging_row_fingerprint)
    if observed != set(expected):
        _raise(STOP_TARGET_BINDING_INVALID)


def authorize_future_adapter(request: AuthorizationRequest) -> AuthorizedAdapterPlan:
    """Validate all pure evidence, then stop because trusted authority is absent."""
    _require_complete(request, AuthorizationRequest, STOP_TARGET_BINDING_INVALID)
    if (
        type(request.execution_sha) is not str
        or type(request.execution_tree) is not str
        or request.execution_sha != PROTECTED_SOURCE_SHA
        or request.execution_tree != PROTECTED_SOURCE_TREE
        or not _SHA_RE.fullmatch(request.execution_sha)
        or not _SHA_RE.fullmatch(request.execution_tree)
    ):
        _raise(STOP_PROTECTED_SOURCE_INVALID)
    if (
        type(request.workflow) is not str
        or type(request.environment) is not str
        or request.workflow != EXPECTED_WORKFLOW
        or request.environment != EXPECTED_ENVIRONMENT
    ):
        _raise(STOP_TARGET_BINDING_INVALID)
    target = _validate_target_binding(request.target)
    if not _is_utc(request.evaluated_at) or not (
        target.issued_at <= request.evaluated_at < target.expires_at
    ):
        _raise(STOP_CLOCK_TIMING_INVALID)
    validate_capability(request.capability)
    validate_snapshot_pair_payload(request.snapshot_payload, target)
    _, _, _, snapshot_2_closed = _snapshot_bounds(
        request.snapshot_payload, STOP_PAGINATION_INCOMPLETE
    )
    if request.evaluated_at < snapshot_2_closed:
        _raise(STOP_CLOCK_TIMING_INVALID)
    validate_source_coverage(
        request.source_observations,
        target,
        request.snapshot_payload,
        request.evaluated_at,
    )
    validate_lifecycle_evidence(
        request.lifecycle_evidence,
        target,
        request.snapshot_payload,
        request.evaluated_at,
    )
    _require_complete(
        request.fg3_cohort,
        FG3CohortEvidence,
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )
    if type(request.fg3_cohort.historical_observations) is not tuple:
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    validate_historical_anchor(
        request.historical_manifest,
        request.historical_anchor,
        request.manifest_builder_receipt,
        request.anchor_provider_receipt,
        target,
        request.snapshot_payload,
        request.fg3_cohort.historical_observations,
        request.evaluated_at,
    )
    validate_fg3_cohort(
        request.fg3_cohort,
        request.historical_manifest,
        target,
        request.snapshot_payload,
    )
    return AuthorizedAdapterPlan(
        target_binding_digest=target_binding_digest(target),
        completed_steps=COMPLETED_STRUCTURAL_STEPS,
        next_step=TRUST_STOP,
        reason=TRUST_STOP,
        transport_created=False,
        authorization_complete=False,
        trust_verification_implemented=False,
    )


def public_contract_projection(plan: AuthorizedAdapterPlan) -> Mapping[str, object]:
    _require_complete(plan, AuthorizedAdapterPlan, STOP_TARGET_BINDING_INVALID)
    if (
        not _valid_digest(plan.target_binding_digest)
        or type(plan.completed_steps) is not tuple
        or any(type(step) is not str for step in plan.completed_steps)
        or plan.completed_steps != COMPLETED_STRUCTURAL_STEPS
        or type(plan.next_step) is not str
        or plan.next_step != TRUST_STOP
        or type(plan.reason) is not str
        or plan.reason != TRUST_STOP
        or type(plan.transport_created) is not bool
        or plan.transport_created
        or type(plan.authorization_complete) is not bool
        or plan.authorization_complete
        or type(plan.trust_verification_implemented) is not bool
        or plan.trust_verification_implemented
    ):
        _raise(STOP_TARGET_BINDING_INVALID)
    return MappingProxyType(
        {
            "contract_version": CONTRACT_VERSION,
            "decision": "STOP",
            "reason_code": TRUST_STOP,
            "authorization_complete": False,
            "transport_created": False,
        }
    )


__all__ = [
    "ALGORITHM_VERSION",
    "AUTHORIZATION_ORDER",
    "AdapterCapability",
    "AnchorProviderEvidenceReceipt",
    "AuthorizationRequest",
    "AuthorizedAdapterPlan",
    "CLOCK_DURATION_TOLERANCE_NS",
    "MAX_IMMUTABLE_DEPTH",
    "MAX_IMMUTABLE_INTEGER_ABS",
    "MAX_IMMUTABLE_NODES",
    "MAX_IMMUTABLE_STRING_BYTES",
    "MAX_PROFILE_SOURCE_PAIRS",
    "MAX_SOURCES_PER_PROFILE",
    "COMPLETED_STRUCTURAL_STEPS",
    "CONNECTED_STOP",
    "CONTRACT_VERSION",
    "CURRENT_GATE_STATUS",
    "EXPECTED_ENVIRONMENT",
    "EXPECTED_WORKFLOW",
    "FG3CohortEvidence",
    "FG3CourseCohortEvidence",
    "FG3HistoricalObservationEvidence",
    "FG3PriorMutationEvidence",
    "FG3_HISTORICAL_CATEGORY_COUNTS",
    "FG3_HISTORICAL_REQUIREMENT",
    "FG3_INACTIVE_ADMISSION",
    "FG3_PRIMARY_COHORT",
    "FINGERPRINT_DECLARATION",
    "FORBIDDEN_METHODS",
    "FrozenRow",
    "G5AdapterContractError",
    "GET_ONLY_CAPABILITY",
    "HISTORICAL_CONTRACT_VERSION",
    "HISTORICAL_V2_STATUS",
    "HistoricalFG3Anchor",
    "HistoricalFG3Manifest",
    "LIFECYCLE_CLASSIFICATIONS",
    "LIFECYCLE_PROXY_ORDER",
    "LIFECYCLE_TIMESTAMP_ORIGINS",
    "LifecycleEvidence",
    "LifecycleProxy",
    "ManifestBuilderEvidenceReceipt",
    "PUBLIC_PROJECTION_FORBIDDEN_FIELDS",
    "PROTECTED_SOURCE_SHA",
    "PROTECTED_SOURCE_TREE",
    "PageEvidence",
    "PaginationEvidence",
    "QueryCapability",
    "READ_CAPTURE_SEQUENCE",
    "READ_CLOCK_SOURCE",
    "ReadTiming",
    "RowCursor",
    "SCHEMA_VERSION",
    "SOURCE_ATTEMPT_BUDGET_NS",
    "SOURCE_ATTEMPT_GRAMMAR",
    "STOP_ANCHOR_NOT_INDEPENDENT",
    "STOP_CAPABILITY_INVALID",
    "STOP_CLOCK_TIMING_INVALID",
    "STOP_COUNT_DRIFT",
    "STOP_MANIFEST_ANCHOR_MISMATCH",
    "STOP_PAGINATION_INCOMPLETE",
    "STOP_PROTECTED_SOURCE_INVALID",
    "STOP_SNAPSHOT_CONTENT_DRIFT",
    "STOP_TARGET_BINDING_INVALID",
    "SourceObservationBundle",
    "SourceObservationEvidence",
    "SourceObservationRequest",
    "SourceAttemptTiming",
    "SnapshotPairPayloadEvidence",
    "TABLE_COLUMNS",
    "TRUST_MODEL_FUTURE_REQUIREMENTS",
    "TRUST_STOP",
    "TargetBinding",
    "anchor_provider_receipt_digest",
    "authorize_future_adapter",
    "classify_lifecycle_proxy",
    "evidence_binding_digest",
    "historical_anchor_digest",
    "historical_manifest_digest",
    "historical_observation_fingerprint",
    "inventory_digest",
    "lifecycle_allows_pass",
    "manifest_builder_receipt_digest",
    "page_evidence_digest",
    "prior_mutation_fingerprint",
    "profile_source_fingerprints",
    "public_contract_projection",
    "row_fingerprint",
    "snapshot_payload_digest",
    "target_binding_digest",
    "validate_capability",
    "validate_fg3_cohort",
    "validate_historical_anchor",
    "validate_lifecycle_evidence",
    "validate_pagination",
    "validate_read_timing",
    "validate_snapshot_pair_payload",
    "validate_source_coverage",
    "validate_source_observation",
]
