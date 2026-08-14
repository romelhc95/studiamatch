"""Offline contract for a future G5 GET-only adapter.

This module validates synthetic, pre-materialized evidence only. It deliberately
has no transport implementation, environment access, credential lookup, or
secret-manager integration.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Mapping, Protocol, Sequence, runtime_checkable


CONTRACT_VERSION = "f10.9-g5-get-only-adapter-contract.v1"
SCHEMA_VERSION = "f10.9-g5-get-only-adapter-schema.v1"
ALGORITHM_VERSION = "f10.9-g5-get-only-adapter-v1"
EXPECTED_ENVIRONMENT = "Production"
EXPECTED_WORKFLOW = "F10.9 G5 Production Read-Only Diagnostic"
PROTECTED_SOURCE_SHA = "bfdeb34c82d3e2fc4545b36f384436ff96ef1cb3"
PROTECTED_SOURCE_TREE = "dabf61ced4012419c4cd9f688506b4fe77e613dd"
GATE_NAME = "APPROVE_F10_9_G5_PRODUCTION_READONLY_DIAGNOSTIC_V1"
CURRENT_GATE_STATUS = "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
APPROVED_GATE_STATUS = "APPROVED_NOT_CONSUMED"
TRUSTED_GATE_AUTHORITY = "sha256:" + "6" * 64
TRUSTED_CREDENTIAL_AUTHORITY = "sha256:" + "7" * 64
TRUSTED_HISTORICAL_ANCHOR_AUTHORITY = "sha256:" + "8" * 64
CONNECTED_STOP = "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"

STOP_TARGET_BINDING_INVALID = "STOP_G5_TARGET_BINDING_INVALID"
STOP_PROTECTED_SOURCE_INVALID = "STOP_G5_PROTECTED_SOURCE_SHA_TREE_INVALID"
STOP_GATE_NOT_APPROVED = "STOP_G5_GATE_ABSENT_OR_NOT_APPROVED"
STOP_PAYLOAD_EXPIRED = "STOP_G5_PAYLOAD_EXPIRED"
STOP_CAPABILITY_INVALID = "STOP_G5_ADAPTER_CAPABILITY_INVALID"
STOP_PAGINATION_INCOMPLETE = "STOP_G5_PAGINATION_INCOMPLETE"
STOP_COUNT_DRIFT = "STOP_G5_COUNT_DRIFT"
STOP_CLOCK_TIMING_INVALID = "STOP_G5_CLOCK_TIMING_INVALID"
STOP_ANCHOR_NOT_INDEPENDENT = "STOP_G5_HISTORICAL_ANCHOR_NOT_INDEPENDENT"
STOP_MANIFEST_ANCHOR_MISMATCH = "STOP_G5_MANIFEST_ANCHOR_MISMATCH"

AUTHORIZATION_ORDER = (
    "GATE_EXACT_APPROVED",
    "PROTECTED_SOURCE_SHA_TREE",
    "WORKFLOW_ENVIRONMENT",
    "TARGET_BINDING",
    "PAYLOAD_MANIFEST_DIGEST",
    "EXPIRATION",
    "ADAPTER_CAPABILITY",
    "CREDENTIAL_AVAILABILITY_ATTESTATION",
    "TRANSPORT_CREATION",
)
COMPLETED_AUTHORIZATION_STEPS = AUTHORIZATION_ORDER[:-1]
READ_CLOCK_SOURCE = "SYSTEM_UTC_PLUS_MONOTONIC"
READ_CAPTURE_SEQUENCE = ("IMMEDIATELY_BEFORE_READ", "IMMEDIATELY_AFTER_READ")
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
FG3_HISTORICAL_REQUIREMENT = "COMPLETE_INDEPENDENT_MANIFEST_REQUIRED_FOR_24_2_1"
FG3_HISTORICAL_CATEGORY_COUNTS = MappingProxyType(
    {"INCONCLUSIVE": 24, "FIRST_GET_404": 2, "DEACTIVATION": 1}
)
FINGERPRINT_DECLARATION = "INTEGRITY_NOT_ANONYMIZATION"

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
class GateAttestation:
    name: str
    status: str
    authority_identity: str
    target_binding_digest: str
    run_id: str
    approval_nonce: str
    issued_at: datetime
    expires_at: datetime
    consumed: bool
    approval_digest: str


@dataclass(frozen=True)
class CredentialAvailabilityAttestation:
    available: bool
    source: str
    secret_values_inspected: bool = False
    authority_identity: str = ""
    target_binding_digest: str = ""
    run_id: str = ""
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    attestation_digest: str = ""


@dataclass(frozen=True)
class AuthorizationRequest:
    gate: GateAttestation
    execution_sha: str
    execution_tree: str
    workflow: str
    environment: str
    target: TargetBinding
    capability: AdapterCapability
    payload_digest: str
    manifest_digest: str
    anchor_digest: str
    historical_manifest: HistoricalFG3ManifestAttestation
    historical_anchor: HistoricalFG3AnchorAttestation
    manifest_builder: HistoricalFG3ManifestBuilder
    anchor_provider: HistoricalFG3AnchorProvider
    fg3_cohort: FG3CohortEvidence
    snapshot_payload: SnapshotPairPayloadEvidence
    evaluated_at: datetime
    credential_availability: CredentialAvailabilityAttestation


@dataclass(frozen=True)
class AuthorizedAdapterPlan:
    target_binding_digest: str
    completed_steps: tuple[str, ...]
    next_step: str
    transport_created: bool
    authorization_complete: bool
    independent_execution_verification_required: bool


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
    row: Mapping[str, object]


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
class HistoricalFG3ManifestAttestation:
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
class HistoricalFG3AnchorAttestation:
    anchor_digest: str
    manifest_digest: str
    provider_identity: str
    provider_instance_identity: str
    provenance: str
    candidate_sha: str
    candidate_tree: str
    run_id: str
    authority_identity: str
    issued_at: datetime


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
class SourceObservationEvidence:
    target_binding_digest: str
    snapshot_pair_id: str
    profile_fingerprint: str
    source_fingerprint: str
    run_fingerprint: str
    cohort_fingerprint: str
    method_sequence: tuple[str, ...]
    attempts: int
    terminal_reason: str
    observed_at: datetime


@dataclass(frozen=True)
class LifecycleProxy:
    last_harvested_at: object
    created_at: object
    observed_at: datetime
    timestamp_used: str | None
    timestamp_origin: str
    calculated_age_seconds: int | None
    classification: str


@dataclass(frozen=True)
class FG3CourseCohortEvidence:
    course_fingerprint: str
    active_at_snapshot_1: bool
    attributable_prior_mutation: bool
    exact_one_verified: bool
    antecedent_run_fingerprint: str | None
    historical_observation_fingerprint: str | None
    historical_category: str | None
    related_to_current_run: bool


@dataclass(frozen=True)
class FG3HistoricalObservationEvidence:
    observation_fingerprint: str
    course_fingerprint: str
    run_id: str
    category: str
    active_at_snapshot_1: bool


@dataclass(frozen=True)
class FG3CohortEvidence:
    target_binding_digest: str
    snapshot_pair_id: str
    run_id: str
    snapshot_1_courses: tuple[Mapping[str, object], ...]
    snapshot_2_courses: tuple[Mapping[str, object], ...]
    courses: tuple[FG3CourseCohortEvidence, ...]
    additional_historical_observations: tuple[FG3HistoricalObservationEvidence, ...]


@dataclass(frozen=True)
class SnapshotPairPayloadEvidence:
    snapshot_pair_id: str
    snapshot_1: tuple[PaginationEvidence, ...]
    snapshot_2: tuple[PaginationEvidence, ...]
    payload_digest: str


@runtime_checkable
class HistoricalFG3AnchorProvider(Protocol):
    """Independent offline source for a pre-materialized historical anchor."""

    provider_identity: str
    provider_instance_identity: str
    provenance: str

    def provide_anchor(
        self,
        *,
        candidate_sha: str,
        candidate_tree: str,
        run_id: str,
        manifest_digest: str,
    ) -> HistoricalFG3AnchorAttestation: ...


@runtime_checkable
class HistoricalFG3ManifestBuilder(Protocol):
    """Identity of the offline actor that materialized the historical manifest."""

    builder_identity: str
    builder_instance_identity: str


@runtime_checkable
class SourceObservationProvider(Protocol):
    """Offline interface only; this candidate supplies no probe implementation."""

    provider_identity: str

    def observe(self, request: SourceObservationRequest) -> SourceObservationEvidence: ...


def _canonical(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical(asdict(value))
    if isinstance(value, datetime):
        return _timestamp_text(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


def _digest(domain: str, value: object) -> str:
    encoded = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    material = b"studiamatch:f10.9:g5:get-only:" + domain.encode("ascii") + b":v1\0" + encoded
    return "sha256:" + hashlib.sha256(material).hexdigest()


def _is_utc(value: object) -> bool:
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() == timedelta(0)
    )


def _timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _valid_digest(value: object) -> bool:
    return type(value) is str and bool(_DIGEST_RE.fullmatch(value))


def _valid_identity(value: object) -> bool:
    return type(value) is str and bool(_IDENTITY_RE.fullmatch(value))


def validate_capability(capability: AdapterCapability) -> None:
    if type(capability) is not AdapterCapability or capability != GET_ONLY_CAPABILITY:
        raise G5AdapterContractError(STOP_CAPABILITY_INVALID)
    if set(capability.methods) != {"select", "count"}:
        raise G5AdapterContractError(STOP_CAPABILITY_INVALID)
    if set(capability.methods) & FORBIDDEN_METHODS:
        raise G5AdapterContractError(STOP_CAPABILITY_INVALID)
    for query in capability.queries:
        if (
            query.table not in TABLE_COLUMNS
            or query.columns != TABLE_COLUMNS[query.table]
            or query.filters != ()
            or query.order != ("id.asc",)
            or query.stable_tie_breaker != "id"
            or query.pagination_mode != "KEYSET_ID_ASC"
            or not 1 <= query.page_size <= 1000
            or query.max_rows > 50_000
            or query.max_pages > 50
            or not 1 <= query.timeout_seconds <= 15
            or not 0 <= query.retry_budget <= 2
        ):
            raise G5AdapterContractError(STOP_CAPABILITY_INVALID)


def target_binding_digest(binding: TargetBinding) -> str:
    return _digest("target-binding", binding)


def evidence_binding_digest(binding: TargetBinding) -> str:
    material = asdict(binding)
    material.pop("payload_digest")
    material.pop("manifest_digest")
    material.pop("anchor_digest")
    return _digest("evidence-binding", material)


def gate_approval_digest(gate: GateAttestation) -> str:
    material = {key: value for key, value in asdict(gate).items() if key != "approval_digest"}
    return _digest("gate-approval", material)


def credential_attestation_digest(
    attestation: CredentialAvailabilityAttestation,
) -> str:
    material = {
        key: value
        for key, value in asdict(attestation).items()
        if key != "attestation_digest"
    }
    return _digest("credential-availability", material)


def _validate_target_binding(binding: TargetBinding) -> None:
    if (
        type(binding) is not TargetBinding
        or binding.environment != EXPECTED_ENVIRONMENT
        or binding.protected_source_sha != PROTECTED_SOURCE_SHA
        or binding.protected_source_tree != PROTECTED_SOURCE_TREE
        or binding.contract_version != CONTRACT_VERSION
        or binding.schema_version != SCHEMA_VERSION
        or binding.algorithm_version != ALGORITHM_VERSION
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
        raise G5AdapterContractError(STOP_TARGET_BINDING_INVALID)


def authorize_future_adapter(request: AuthorizationRequest) -> AuthorizedAdapterPlan:
    """Validate authorization offline and stop before transport creation.

    The function accepts no factory, environment reader, secret value, credential
    object, or transport. Credential availability is an opaque boolean attestation.
    """
    if type(request) is not AuthorizationRequest or type(request.gate) is not GateAttestation:
        raise G5AdapterContractError(STOP_GATE_NOT_APPROVED)
    gate = request.gate
    if (
        gate.name != GATE_NAME
        or gate.status != APPROVED_GATE_STATUS
        or gate.authority_identity != TRUSTED_GATE_AUTHORITY
        or not _valid_digest(gate.target_binding_digest)
        or not _valid_digest(gate.run_id)
        or not _valid_digest(gate.approval_nonce)
        or not _is_utc(gate.issued_at)
        or not _is_utc(gate.expires_at)
        or gate.expires_at <= gate.issued_at
        or type(gate.consumed) is not bool
        or gate.consumed
        or gate.approval_digest != gate_approval_digest(gate)
    ):
        raise G5AdapterContractError(STOP_GATE_NOT_APPROVED)
    if (
        request.execution_sha != PROTECTED_SOURCE_SHA
        or request.execution_tree != PROTECTED_SOURCE_TREE
        or not _SHA_RE.fullmatch(request.execution_sha)
        or not _SHA_RE.fullmatch(request.execution_tree)
    ):
        raise G5AdapterContractError(STOP_PROTECTED_SOURCE_INVALID)
    if (
        request.workflow != EXPECTED_WORKFLOW
        or request.environment != EXPECTED_ENVIRONMENT
    ):
        raise G5AdapterContractError(STOP_TARGET_BINDING_INVALID)
    _validate_target_binding(request.target)
    binding_digest = target_binding_digest(request.target)
    if (
        gate.target_binding_digest != binding_digest
        or gate.run_id != request.target.run_id
    ):
        raise G5AdapterContractError(STOP_TARGET_BINDING_INVALID)
    if (
        request.target.payload_digest != request.payload_digest
        or request.target.manifest_digest != request.manifest_digest
        or request.target.anchor_digest != request.anchor_digest
        or any(
            not _valid_digest(value)
            for value in (
                request.payload_digest,
                request.manifest_digest,
                request.anchor_digest,
            )
        )
    ):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    validate_snapshot_pair_payload(request.snapshot_payload, request.target)
    independent_anchor = obtain_independent_historical_anchor(
        request.manifest_builder,
        request.anchor_provider,
        request.historical_manifest,
        request.target,
    )
    if independent_anchor != request.historical_anchor:
        raise G5AdapterContractError(STOP_ANCHOR_NOT_INDEPENDENT)
    validate_fg3_cohort(
        request.fg3_cohort,
        request.historical_manifest,
        request.target,
        request.snapshot_payload,
    )
    if not _is_utc(request.evaluated_at):
        raise G5AdapterContractError(STOP_CLOCK_TIMING_INVALID)
    if (
        request.evaluated_at < request.target.issued_at
        or request.evaluated_at >= request.target.expires_at
        or request.evaluated_at < gate.issued_at
        or request.evaluated_at >= gate.expires_at
    ):
        raise G5AdapterContractError(STOP_PAYLOAD_EXPIRED)
    validate_capability(request.capability)
    credential = request.credential_availability
    if (
        type(credential) is not CredentialAvailabilityAttestation
        or type(credential.available) is not bool
        or not credential.available
        or credential.secret_values_inspected
        or credential.source != "ENVIRONMENT_AVAILABILITY_ATTESTATION"
        or credential.authority_identity != TRUSTED_CREDENTIAL_AUTHORITY
        or credential.target_binding_digest != binding_digest
        or credential.run_id != request.target.run_id
        or not _is_utc(credential.issued_at)
        or not _is_utc(credential.expires_at)
        or credential.expires_at <= credential.issued_at
        or request.evaluated_at < credential.issued_at
        or request.evaluated_at >= credential.expires_at
        or credential.attestation_digest != credential_attestation_digest(credential)
    ):
        raise G5AdapterContractError(STOP_TARGET_BINDING_INVALID)
    return AuthorizedAdapterPlan(
        target_binding_digest=target_binding_digest(request.target),
        completed_steps=COMPLETED_AUTHORIZATION_STEPS,
        next_step=CONNECTED_STOP,
        transport_created=False,
        authorization_complete=False,
        independent_execution_verification_required=True,
    )


def validate_read_timing(timing: ReadTiming, snapshot_pair_id: str) -> None:
    if (
        type(timing) is not ReadTiming
        or timing.snapshot_pair_id != snapshot_pair_id
        or timing.operation not in {"COUNT_INITIAL", "SELECT_PAGE", "COUNT_FINAL"}
        or timing.clock_source != READ_CLOCK_SOURCE
        or timing.capture_sequence != READ_CAPTURE_SEQUENCE
        or not _is_utc(timing.started_at_utc)
        or not _is_utc(timing.ended_at_utc)
        or timing.started_at_utc >= timing.ended_at_utc
        or isinstance(timing.monotonic_started_ns, bool)
        or isinstance(timing.monotonic_ended_ns, bool)
        or not isinstance(timing.monotonic_started_ns, int)
        or not isinstance(timing.monotonic_ended_ns, int)
        or timing.monotonic_started_ns < 0
        or timing.monotonic_started_ns >= timing.monotonic_ended_ns
        or (timing.ended_at_utc - timing.started_at_utc).total_seconds() > 15
        or (timing.monotonic_ended_ns - timing.monotonic_started_ns) > 15_000_000_000
    ):
        raise G5AdapterContractError(STOP_CLOCK_TIMING_INVALID)


def _timing_within_target(timing: ReadTiming, target: TargetBinding) -> bool:
    return (
        target.issued_at <= timing.started_at_utc
        and timing.ended_at_utc < target.expires_at
    )


def row_fingerprint(
    table: str,
    target_digest: str,
    snapshot_pair_id: str,
    row: Mapping[str, object],
) -> str:
    return _digest(
        "row",
        {
            "table": table,
            "target_binding_digest": target_digest,
            "snapshot_pair_id": snapshot_pair_id,
            "row": dict(row),
        },
    )


def page_evidence_digest(
    table: str,
    target_digest: str,
    snapshot_pair_id: str,
    page: PageEvidence,
) -> str:
    return _digest(
        "page",
        {
            "table": table,
            "target_binding_digest": target_digest,
            "snapshot_pair_id": snapshot_pair_id,
            "after_id": page.after_id,
            "requested_limit": page.requested_limit,
            "row_fingerprints": tuple(row.row_fingerprint for row in page.rows),
            "timing": page.timing,
        },
    )


def inventory_digest(evidence: PaginationEvidence) -> str:
    return _digest(
        "inventory",
        {
            "target_binding_digest": evidence.target_binding_digest,
            "snapshot_pair_id": evidence.snapshot_pair_id,
            "table": evidence.table,
            "initial_count": evidence.initial_count,
            "final_count": evidence.final_count,
            "rows": tuple(
                row.row_fingerprint for page in evidence.pages for row in page.rows
            ),
            "initial_count_timing": evidence.initial_count_timing,
            "page_timings": tuple(page.timing for page in evidence.pages),
            "final_count_timing": evidence.final_count_timing,
        },
    )


def validate_pagination(
    evidence: PaginationEvidence,
    target: TargetBinding,
    capability: AdapterCapability = GET_ONLY_CAPABILITY,
) -> tuple[str, ...]:
    validate_capability(capability)
    _validate_target_binding(target)
    queries = {query.table: query for query in capability.queries}
    binding_digest = evidence_binding_digest(target)
    if (
        type(evidence) is not PaginationEvidence
        or evidence.table not in queries
        or evidence.target_binding_digest != binding_digest
        or evidence.snapshot_pair_id != target.snapshot_pair_id
        or not _valid_digest(evidence.snapshot_pair_id)
    ):
        raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
    if (
        isinstance(evidence.initial_count, bool)
        or isinstance(evidence.final_count, bool)
        or not isinstance(evidence.initial_count, int)
        or not isinstance(evidence.final_count, int)
        or evidence.initial_count < 0
        or evidence.final_count < 0
    ):
        raise G5AdapterContractError(STOP_COUNT_DRIFT)
    if evidence.initial_count != evidence.final_count:
        raise G5AdapterContractError(STOP_COUNT_DRIFT)
    query = queries[evidence.table]
    if evidence.initial_count > query.max_rows or len(evidence.pages) > query.max_pages:
        raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
    validate_read_timing(evidence.initial_count_timing, evidence.snapshot_pair_id)
    validate_read_timing(evidence.final_count_timing, evidence.snapshot_pair_id)
    if (
        evidence.initial_count_timing.operation != "COUNT_INITIAL"
        or evidence.final_count_timing.operation != "COUNT_FINAL"
        or evidence.initial_count_timing.monotonic_ended_ns
        >= evidence.final_count_timing.monotonic_started_ns
        or evidence.initial_count_timing.ended_at_utc
        >= evidence.final_count_timing.started_at_utc
        or not _timing_within_target(evidence.initial_count_timing, target)
        or not _timing_within_target(evidence.final_count_timing, target)
    ):
        raise G5AdapterContractError(STOP_CLOCK_TIMING_INVALID)
    if evidence.initial_count == 0:
        if evidence.pages or evidence.inventory_digest != inventory_digest(evidence):
            raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
        return ()

    expected_after_id: str | None = None
    page_digests: set[str] = set()
    row_fingerprints: set[str] = set()
    ordered: list[tuple[str, str]] = []
    observed_bytes = 0
    previous_timing = evidence.initial_count_timing
    for page in evidence.pages:
        if (
            type(page) is not PageEvidence
            or page.after_id != expected_after_id
            or page.requested_limit != query.page_size
            or not page.rows
            or len(page.rows) > page.requested_limit
            or not _valid_digest(page.page_digest)
            or page.page_digest in page_digests
        ):
            raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
        validate_read_timing(page.timing, evidence.snapshot_pair_id)
        if (
            page.timing.operation != "SELECT_PAGE"
            or previous_timing.monotonic_ended_ns >= page.timing.monotonic_started_ns
            or previous_timing.ended_at_utc >= page.timing.started_at_utc
            or not _timing_within_target(page.timing, target)
            or page.page_digest
            != page_evidence_digest(
                evidence.table,
                evidence.target_binding_digest,
                evidence.snapshot_pair_id,
                page,
            )
        ):
            raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
        page_digests.add(page.page_digest)
        for row in page.rows:
            if (
                type(row) is not RowCursor
                or not row.order_value
                or not row.tie_breaker
                or not isinstance(row.row, Mapping)
                or set(row.row) != set(TABLE_COLUMNS[evidence.table])
                or str(row.row.get("id")) != row.order_value
                or row.tie_breaker != row.order_value
                or not _valid_digest(row.row_fingerprint)
                or row.row_fingerprint in row_fingerprints
                or row.row_fingerprint
                != row_fingerprint(
                    evidence.table,
                    evidence.target_binding_digest,
                    evidence.snapshot_pair_id,
                    row.row,
                )
            ):
                raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
            observed_bytes += len(
                json.dumps(
                    _canonical(dict(row.row)),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            )
            ordered.append((row.order_value, row.tie_breaker))
            row_fingerprints.add(row.row_fingerprint)
        expected_after_id = page.rows[-1].tie_breaker
        previous_timing = page.timing
    if (
        len(ordered) != evidence.initial_count
        or ordered != sorted(ordered)
        or len(ordered) != len(set(ordered))
        or observed_bytes > capability.max_snapshot_bytes
        or previous_timing.monotonic_ended_ns
        >= evidence.final_count_timing.monotonic_started_ns
        or previous_timing.ended_at_utc
        >= evidence.final_count_timing.started_at_utc
        or evidence.inventory_digest != inventory_digest(evidence)
    ):
        raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
    return tuple(row.row_fingerprint for page in evidence.pages for row in page.rows)


def _pagination_bytes(evidence: PaginationEvidence) -> int:
    return sum(
        len(
            json.dumps(
                _canonical(dict(row.row)),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
        )
        for page in evidence.pages
        for row in page.rows
    )


def snapshot_payload_digest(evidence: SnapshotPairPayloadEvidence) -> str:
    return _digest(
        "snapshot-payload",
        {
            "snapshot_pair_id": evidence.snapshot_pair_id,
            "snapshot_1": tuple(
                (item.table, item.inventory_digest)
                for item in sorted(evidence.snapshot_1, key=lambda item: item.table)
            ),
            "snapshot_2": tuple(
                (item.table, item.inventory_digest)
                for item in sorted(evidence.snapshot_2, key=lambda item: item.table)
            ),
        },
    )


def validate_snapshot_pair_payload(
    evidence: SnapshotPairPayloadEvidence,
    target: TargetBinding,
    *,
    max_snapshot_bytes: int = GET_ONLY_CAPABILITY.max_snapshot_bytes,
) -> None:
    if (
        type(evidence) is not SnapshotPairPayloadEvidence
        or evidence.snapshot_pair_id != target.snapshot_pair_id
        or type(evidence.snapshot_1) is not tuple
        or type(evidence.snapshot_2) is not tuple
        or isinstance(max_snapshot_bytes, bool)
        or not isinstance(max_snapshot_bytes, int)
        or not 1 <= max_snapshot_bytes <= GET_ONLY_CAPABILITY.max_snapshot_bytes
    ):
        raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
    first = {item.table: item for item in evidence.snapshot_1}
    second = {item.table: item for item in evidence.snapshot_2}
    if (
        len(first) != len(evidence.snapshot_1)
        or len(second) != len(evidence.snapshot_2)
        or set(first) != set(TABLE_COLUMNS)
        or set(second) != set(TABLE_COLUMNS)
    ):
        raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
    total_bytes = 0
    first_timings: list[ReadTiming] = []
    second_timings: list[ReadTiming] = []
    for table in sorted(TABLE_COLUMNS):
        first_rows = validate_pagination(first[table], target)
        second_rows = validate_pagination(second[table], target)
        total_bytes += _pagination_bytes(first[table]) + _pagination_bytes(second[table])
        first_timings.extend(
            [
                first[table].initial_count_timing,
                *(page.timing for page in first[table].pages),
                first[table].final_count_timing,
            ]
        )
        second_timings.extend(
            [
                second[table].initial_count_timing,
                *(page.timing for page in second[table].pages),
                second[table].final_count_timing,
            ]
        )
        if first_rows != second_rows:
            raise G5AdapterContractError(STOP_COUNT_DRIFT)
    if (
        max(item.ended_at_utc for item in first_timings)
        >= min(item.started_at_utc for item in second_timings)
        or max(item.monotonic_ended_ns for item in first_timings)
        >= min(item.monotonic_started_ns for item in second_timings)
    ):
        raise G5AdapterContractError(STOP_CLOCK_TIMING_INVALID)
    if total_bytes > max_snapshot_bytes * 2:
        raise G5AdapterContractError(STOP_PAGINATION_INCOMPLETE)
    expected_payload = snapshot_payload_digest(evidence)
    if evidence.payload_digest != expected_payload or target.payload_digest != expected_payload:
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)


def historical_anchor_digest(anchor: HistoricalFG3AnchorAttestation) -> str:
    material = {
        key: value
        for key, value in asdict(anchor).items()
        if key != "anchor_digest"
    }
    return _digest("historical-anchor", material)


def historical_manifest_digest(
    manifest: HistoricalFG3ManifestAttestation,
) -> str:
    material = {
        key: value
        for key, value in asdict(manifest).items()
        if key != "manifest_digest"
    }
    return _digest("historical-manifest", material)


def validate_historical_anchor(
    manifest: HistoricalFG3ManifestAttestation,
    anchor: HistoricalFG3AnchorAttestation,
    target: TargetBinding,
) -> None:
    if (
        type(manifest) is not HistoricalFG3ManifestAttestation
        or type(anchor) is not HistoricalFG3AnchorAttestation
        or type(manifest.observation_categories) is not tuple
        or type(manifest.category_counts) is not tuple
    ):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    try:
        categories = dict(manifest.category_counts)
        categorized = dict(manifest.observation_categories)
    except (TypeError, ValueError):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH) from None
    observed_category_counts = {
        category: sum(value == category for value in categorized.values())
        for category in set(categorized.values())
    }
    if (
        not _valid_identity(manifest.builder_identity)
        or not _valid_identity(manifest.builder_instance_identity)
        or not _valid_identity(anchor.provider_identity)
        or not _valid_identity(anchor.provider_instance_identity)
        or manifest.builder_identity == anchor.provider_identity
        or manifest.builder_instance_identity == anchor.provider_instance_identity
    ):
        raise G5AdapterContractError(STOP_ANCHOR_NOT_INDEPENDENT)
    if (
        type(manifest.complete) is not bool
        or not manifest.complete
        or not _valid_digest(manifest.manifest_digest)
        or type(manifest.expected_observation_fingerprints) is not tuple
        or not manifest.expected_observation_fingerprints
        or len(manifest.expected_observation_fingerprints)
        != len(set(manifest.expected_observation_fingerprints))
        or any(
            not _valid_digest(value)
            for value in manifest.expected_observation_fingerprints
        )
        or len(categorized) != len(manifest.observation_categories)
        or set(categorized) != set(manifest.expected_observation_fingerprints)
        or any(type(value) is not str or not value for value in categorized.values())
        or len(categories) != len(manifest.category_counts)
        or not categories
        or any(
            type(name) is not str
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            for name, count in manifest.category_counts
        )
        or sum(categories.values()) != len(manifest.expected_observation_fingerprints)
        or categories != observed_category_counts
        or categories != dict(FG3_HISTORICAL_CATEGORY_COUNTS)
        or manifest.published_count_tuple != (24, 2, 1)
    ):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        manifest.manifest_digest != historical_manifest_digest(manifest)
        or anchor.provenance != "INDEPENDENT_HISTORICAL_FG3_SOURCE"
        or anchor.manifest_digest != manifest.manifest_digest
        or anchor.candidate_sha != manifest.candidate_sha
        or anchor.candidate_tree != manifest.candidate_tree
        or anchor.run_id != manifest.run_id
        or anchor.authority_identity != TRUSTED_HISTORICAL_ANCHOR_AUTHORITY
        or manifest.candidate_sha != target.protected_source_sha
        or manifest.candidate_tree != target.protected_source_tree
        or manifest.run_id != target.run_id
        or manifest.manifest_digest != target.manifest_digest
        or anchor.anchor_digest != target.anchor_digest
        or not _SHA_RE.fullmatch(anchor.candidate_sha)
        or not _SHA_RE.fullmatch(anchor.candidate_tree)
        or not _valid_digest(anchor.run_id)
        or not _is_utc(manifest.issued_at)
        or not _is_utc(anchor.issued_at)
        or anchor.issued_at < manifest.issued_at
        or anchor.anchor_digest != historical_anchor_digest(anchor)
    ):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)


def obtain_independent_historical_anchor(
    manifest_builder: HistoricalFG3ManifestBuilder,
    anchor_provider: HistoricalFG3AnchorProvider,
    manifest: HistoricalFG3ManifestAttestation,
    target: TargetBinding,
) -> HistoricalFG3AnchorAttestation:
    if (
        manifest_builder is anchor_provider
        or not isinstance(manifest_builder, HistoricalFG3ManifestBuilder)
        or not isinstance(anchor_provider, HistoricalFG3AnchorProvider)
        or manifest_builder.builder_identity != manifest.builder_identity
        or manifest_builder.builder_instance_identity
        != manifest.builder_instance_identity
        or anchor_provider.provider_identity == manifest.builder_identity
        or anchor_provider.provider_instance_identity
        == manifest.builder_instance_identity
    ):
        raise G5AdapterContractError(STOP_ANCHOR_NOT_INDEPENDENT)
    anchor = anchor_provider.provide_anchor(
        candidate_sha=target.protected_source_sha,
        candidate_tree=target.protected_source_tree,
        run_id=target.run_id,
        manifest_digest=manifest.manifest_digest,
    )
    if (
        type(anchor) is not HistoricalFG3AnchorAttestation
        or anchor.provider_identity != anchor_provider.provider_identity
        or anchor.provider_instance_identity
        != anchor_provider.provider_instance_identity
        or anchor.provenance != anchor_provider.provenance
    ):
        raise G5AdapterContractError(STOP_ANCHOR_NOT_INDEPENDENT)
    validate_historical_anchor(manifest, anchor, target)
    return anchor


def validate_fg3_cohort(
    evidence: FG3CohortEvidence,
    manifest: HistoricalFG3ManifestAttestation,
    target: TargetBinding,
    snapshot_payload: SnapshotPairPayloadEvidence,
) -> tuple[frozenset[str], frozenset[str]]:
    target_digest = evidence_binding_digest(target)
    if (
        type(evidence) is not FG3CohortEvidence
        or evidence.target_binding_digest != target_digest
        or evidence.snapshot_pair_id != target.snapshot_pair_id
        or evidence.run_id != target.run_id
        or manifest.run_id != evidence.run_id
        or manifest.manifest_digest != historical_manifest_digest(manifest)
        or manifest.manifest_digest != target.manifest_digest
        or evidence.snapshot_pair_id != snapshot_payload.snapshot_pair_id
    ):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    first_courses_inventory = next(
        (item for item in snapshot_payload.snapshot_1 if item.table == "courses"),
        None,
    )
    second_courses_inventory = next(
        (item for item in snapshot_payload.snapshot_2 if item.table == "courses"),
        None,
    )
    if first_courses_inventory is None or second_courses_inventory is None:
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    first_rows = tuple(
        dict(row.row)
        for page in first_courses_inventory.pages
        for row in page.rows
    )
    second_rows = tuple(
        dict(row.row)
        for page in second_courses_inventory.pages
        for row in page.rows
    )
    if evidence.snapshot_1_courses != first_rows or evidence.snapshot_2_courses != second_rows:
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    if any(type(row.get("is_active")) is not bool for row in (*first_rows, *second_rows)):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    first_by_fingerprint = {
        row_fingerprint(
            "courses",
            target_digest,
            evidence.snapshot_pair_id,
            row,
        ): row
        for row in first_rows
    }
    primary: set[str] = set()
    prior: set[str] = set()
    manifest_categories = dict(manifest.observation_categories)
    if (
        type(evidence.additional_historical_observations) is not tuple
        or any(
            type(item) is not FG3HistoricalObservationEvidence
            for item in evidence.additional_historical_observations
        )
    ):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    historical: set[str] = set()
    additional_courses: set[str] = set()
    for item in evidence.additional_historical_observations:
        row = first_by_fingerprint.get(item.course_fingerprint)
        if (
            not _valid_digest(item.observation_fingerprint)
            or item.observation_fingerprint in historical
            or item.course_fingerprint in additional_courses
            or row is None
            or row.get("is_active") is not True
            or item.run_id != evidence.run_id
            or item.category != manifest_categories.get(item.observation_fingerprint)
            or type(item.active_at_snapshot_1) is not bool
            or not item.active_at_snapshot_1
        ):
            raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
        historical.add(item.observation_fingerprint)
        additional_courses.add(item.course_fingerprint)
    seen: set[str] = set()
    for course in evidence.courses:
        if (
            type(course) is not FG3CourseCohortEvidence
            or not _valid_digest(course.course_fingerprint)
            or course.course_fingerprint in seen
            or type(course.active_at_snapshot_1) is not bool
            or type(course.attributable_prior_mutation) is not bool
            or type(course.exact_one_verified) is not bool
            or type(course.related_to_current_run) is not bool
            or not course.related_to_current_run
        ):
            raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
        seen.add(course.course_fingerprint)
        snapshot_row = first_by_fingerprint.get(course.course_fingerprint)
        if (
            snapshot_row is None
            or type(snapshot_row.get("is_active")) is not bool
            or course.active_at_snapshot_1 != snapshot_row.get("is_active")
        ):
            raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
        if course.active_at_snapshot_1:
            if (
                course.attributable_prior_mutation
                or course.exact_one_verified
                or course.antecedent_run_fingerprint is not None
                or course.historical_observation_fingerprint is not None
                or course.historical_category is not None
            ):
                raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
            primary.add(course.course_fingerprint)
            continue
        if (
            not course.attributable_prior_mutation
            or not course.exact_one_verified
            or not _valid_digest(course.antecedent_run_fingerprint)
            or course.antecedent_run_fingerprint == evidence.run_id
            or not _valid_digest(course.historical_observation_fingerprint)
            or course.historical_category != "DEACTIVATION"
            or manifest_categories.get(
                str(course.historical_observation_fingerprint)
            )
            != course.historical_category
        ):
            raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
        prior.add(course.course_fingerprint)
        if str(course.historical_observation_fingerprint) in historical:
            raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
        historical.add(str(course.historical_observation_fingerprint))
    required_active = {
        fingerprint
        for fingerprint, row in first_by_fingerprint.items()
        if row.get("is_active") is True
    }
    if primary != required_active:
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    if historical != set(manifest.expected_observation_fingerprints):
        raise G5AdapterContractError(STOP_MANIFEST_ANCHOR_MISMATCH)
    return frozenset(primary), frozenset(prior)


def validate_source_observation(
    request: SourceObservationRequest,
    evidence: SourceObservationEvidence,
    target: TargetBinding,
) -> None:
    methods = request.method_sequence
    if (
        type(request) is not SourceObservationRequest
        or type(evidence) is not SourceObservationEvidence
        or request.target_binding_digest != evidence_binding_digest(target)
        or evidence.target_binding_digest != request.target_binding_digest
        or request.snapshot_pair_id != target.snapshot_pair_id
        or request.run_fingerprint != target.run_id
        or not methods
        or any(method not in {"HEAD", "GET"} for method in methods)
        or methods[-1] != "GET"
        or request.max_attempts != len(methods)
        or not 1 <= request.max_attempts <= 3
        or evidence.snapshot_pair_id != request.snapshot_pair_id
        or evidence.profile_fingerprint != request.profile_fingerprint
        or evidence.source_fingerprint != request.source_fingerprint
        or evidence.run_fingerprint != request.run_fingerprint
        or evidence.cohort_fingerprint != request.cohort_fingerprint
        or evidence.method_sequence != methods
        or evidence.attempts != len(methods)
        or evidence.terminal_reason not in {
            "SOURCE_ACCESSIBLE",
            "SOURCE_GET_403",
            "SOURCE_TIMEOUT",
            "SOURCE_DNS_FAILURE",
            "SOURCE_TLS_FAILURE",
            "SOURCE_TRANSPORT_FAILURE",
        }
        or not _is_utc(evidence.observed_at)
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
        raise G5AdapterContractError(STOP_TARGET_BINDING_INVALID)


def classify_lifecycle_proxy(
    *,
    last_harvested_at: object,
    created_at: object,
    observed_at: datetime,
) -> LifecycleProxy:
    if not _is_utc(observed_at):
        raise G5AdapterContractError(STOP_CLOCK_TIMING_INVALID)
    if last_harvested_at is not None:
        raw = last_harvested_at
        origin = "LAST_HARVESTED_AT_PROXY"
    elif created_at is not None:
        raw = created_at
        origin = "CREATED_AT_PROXY"
    else:
        return LifecycleProxy(
            last_harvested_at, created_at, observed_at, None, "NONE", None, "AGE_UNKNOWN"
        )
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        parsed = None
    if not _is_utc(parsed):
        return LifecycleProxy(
            last_harvested_at,
            created_at,
            observed_at,
            str(raw),
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
        if timedelta(seconds=age) > _STALE_AFTER
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


def lifecycle_allows_pass(observations: Sequence[LifecycleProxy]) -> bool:
    if not observations:
        return False
    for item in observations:
        if type(item) is not LifecycleProxy:
            return False
        try:
            expected = classify_lifecycle_proxy(
                last_harvested_at=item.last_harvested_at,
                created_at=item.created_at,
                observed_at=item.observed_at,
            )
        except G5AdapterContractError:
            return False
        if item != expected or item.classification != "NOT_STALE":
            return False
    return True


def public_contract_projection(plan: AuthorizedAdapterPlan) -> Mapping[str, object]:
    if (
        type(plan) is not AuthorizedAdapterPlan
        or not _valid_digest(plan.target_binding_digest)
        or plan.completed_steps != COMPLETED_AUTHORIZATION_STEPS
        or plan.next_step != CONNECTED_STOP
        or type(plan.transport_created) is not bool
        or plan.transport_created
        or type(plan.authorization_complete) is not bool
        or plan.authorization_complete
        or type(plan.independent_execution_verification_required) is not bool
        or not plan.independent_execution_verification_required
    ):
        raise G5AdapterContractError(STOP_TARGET_BINDING_INVALID)
    return MappingProxyType(
        {
            "contract_version": CONTRACT_VERSION,
            "decision": "STOP",
            "reason_code": plan.next_step,
            "target_binding_digest": plan.target_binding_digest,
            "authorization_complete": plan.authorization_complete,
            "transport_created": plan.transport_created,
        }
    )


__all__ = [
    "ALGORITHM_VERSION",
    "APPROVED_GATE_STATUS",
    "AUTHORIZATION_ORDER",
    "AdapterCapability",
    "AuthorizationRequest",
    "AuthorizedAdapterPlan",
    "CONNECTED_STOP",
    "CONTRACT_VERSION",
    "CURRENT_GATE_STATUS",
    "CredentialAvailabilityAttestation",
    "EXPECTED_ENVIRONMENT",
    "EXPECTED_WORKFLOW",
    "FG3_HISTORICAL_CATEGORY_COUNTS",
    "FG3_HISTORICAL_REQUIREMENT",
    "FG3_INACTIVE_ADMISSION",
    "FG3_PRIMARY_COHORT",
    "FG3CohortEvidence",
    "FG3CourseCohortEvidence",
    "FG3HistoricalObservationEvidence",
    "FINGERPRINT_DECLARATION",
    "FORBIDDEN_METHODS",
    "G5AdapterContractError",
    "GATE_NAME",
    "GET_ONLY_CAPABILITY",
    "GateAttestation",
    "HistoricalFG3AnchorAttestation",
    "HistoricalFG3AnchorProvider",
    "HistoricalFG3ManifestBuilder",
    "HistoricalFG3ManifestAttestation",
    "LIFECYCLE_CLASSIFICATIONS",
    "LIFECYCLE_PROXY_ORDER",
    "LIFECYCLE_TIMESTAMP_ORIGINS",
    "LifecycleProxy",
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
    "STOP_ANCHOR_NOT_INDEPENDENT",
    "STOP_CAPABILITY_INVALID",
    "STOP_CLOCK_TIMING_INVALID",
    "STOP_COUNT_DRIFT",
    "STOP_GATE_NOT_APPROVED",
    "STOP_MANIFEST_ANCHOR_MISMATCH",
    "STOP_PAGINATION_INCOMPLETE",
    "STOP_PAYLOAD_EXPIRED",
    "STOP_PROTECTED_SOURCE_INVALID",
    "STOP_TARGET_BINDING_INVALID",
    "SourceObservationEvidence",
    "SourceObservationProvider",
    "SourceObservationRequest",
    "SnapshotPairPayloadEvidence",
    "TABLE_COLUMNS",
    "TargetBinding",
    "TRUSTED_CREDENTIAL_AUTHORITY",
    "TRUSTED_GATE_AUTHORITY",
    "TRUSTED_HISTORICAL_ANCHOR_AUTHORITY",
    "authorize_future_adapter",
    "classify_lifecycle_proxy",
    "credential_attestation_digest",
    "evidence_binding_digest",
    "gate_approval_digest",
    "historical_anchor_digest",
    "historical_manifest_digest",
    "inventory_digest",
    "lifecycle_allows_pass",
    "obtain_independent_historical_anchor",
    "page_evidence_digest",
    "public_contract_projection",
    "row_fingerprint",
    "snapshot_payload_digest",
    "target_binding_digest",
    "validate_capability",
    "validate_historical_anchor",
    "validate_fg3_cohort",
    "validate_pagination",
    "validate_read_timing",
    "validate_source_observation",
    "validate_snapshot_pair_payload",
]
