"""Pure repository-only v2.3 contract for a future G5 GET-only adapter.

The contract consumes exact frozen dataclasses containing deeply immutable data.
It validates structure and integrity only. It cannot establish operational trust,
approve or consume a gate, inspect credentials, execute caller code, or create a
transport.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urljoin, urlparse

from .url_identity import build_url_identity


CONTRACT_VERSION = "f10.9-g5-get-only-adapter-contract.v2.3"
SCHEMA_VERSION = "f10.9-g5-get-only-adapter-schema.v2.3"
ALGORITHM_VERSION = "f10.9-g5-get-only-adapter-v2.3"
HISTORICAL_CONTRACT_VERSION = "f10.9-g5-get-only-adapter-contract.v2.2"
HISTORICAL_V2_STATUS = "HISTORICAL_ANTECEDENT_NOT_FIT_FOR_CONNECTED_MODE"
EXPECTED_ENVIRONMENT = "Production"
EXPECTED_WORKFLOW = "F10.9 G5 Production Read-Only Diagnostic"
EXPECTED_WORKFLOW_PATH = ".github/workflows/f9-7-contract.yml"
EXPECTED_REPOSITORY = "romelhc95/studiamatch"
EXPECTED_REF = "refs/heads/main"
EXPECTED_OIDC_ISSUER = "https://token.actions.githubusercontent.com"
EXPECTED_OIDC_AUDIENCE = "studiamatch-f10-9-g5-production-trust-plane"
PROTECTED_SOURCE_SHA = "9045c90ac78634f17a66cb3e30e723a2431cb6b4"
PROTECTED_SOURCE_TREE = "3d8455a29b63a38906a67343ee4ba6dd15b366d7"
EXPECTED_WORKFLOW_SHA = PROTECTED_SOURCE_SHA
EXPECTED_WORKFLOW_BLOB_SHA = "5a5dcf971e0e1686393b9be0e331688f83ef7fa2"
CURRENT_GATE_STATUS = "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
CONNECTED_STOP = "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"
TRUST_STOP = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED"
G5_TRUST_PLANE_PR_A_STATUS = "REPOSITORY_ONLY_TRUST_PLANE_PR_A_STOP"
G5_TRUST_GATE_STATE_READY = "READY"
G5_TRUST_GATE_STATE_CONSUMED = "CONSUMED"
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
STOP_PROFILE_ROUTING_INVALID = "STOP_G5_PROFILE_ROUTING_INVALID"
STOP_SOURCE_BLOCKERS_PRESENT = "STOP_G5_SOURCE_BLOCKERS_PRESENT"
STOP_LIFECYCLE_BLOCKERS_PRESENT = "STOP_G5_LIFECYCLE_BLOCKERS_PRESENT"
STOP_AUTHORITY_INVALID = "STOP_G5_AUTHORITY_INVALID"
STOP_APPROVAL_INVALID = "STOP_G5_APPROVAL_INVALID"
STOP_BINDING_DRIFT = "STOP_G5_BINDING_DRIFT"
STOP_REPLAY_DETECTED = "STOP_G5_REPLAY_DETECTED"
STOP_GATE_EXPIRED = "STOP_G5_GATE_EXPIRED"
STOP_CONSUMPTION_AMBIGUOUS = "STOP_G5_CONSUMPTION_AMBIGUOUS"
STOP_ATOMIC_LEDGER_REQUIRED = "STOP_G5_ATOMIC_LEDGER_REQUIRED"
STOP_PROOF_INVALID = "STOP_G5_PROOF_INVALID"

CALLER_SUPPLIED_AUTHORITY_FIELDS = frozenset(
    {
        "authority", "approval", "approval_evidence", "credential", "gate_status",
        "gate_intent", "consumed_nonce", "nonce_digest", "jti", "proof", "run_id",
        "workflow", "workflow_id", "workflow_name", "workflow_path", "workflow_sha",
        "workflow_blob_sha", "workflow_ref", "check_run_id", "deployment",
        "deployments", "deployment_id", "deployment_ref", "deployment_state",
        "environment", "environment_name", "environment_id", "repository",
        "repository_owner", "repository_id", "repo", "owner_id", "approver",
        "approver_id", "approver_login", "reviewer", "reviewer_id", "receipt",
        "receipt_proof", "gate_consumption_receipt", "ledger", "ledger_receipt",
        "ledger_proof", "atomic_ledger_proof", "sha", "tree", "digest", "oidc", "oidc_claims", "workflow_run",
        "environment_approval", "ledger_atomicity_proven",
    }
)
G5_ATOMIC_LEDGER_INTERFACE = (
    "read_gate_intent",
    "compare_and_set_ready_to_consumed",
    "record_jti_once",
    "record_nonce_once",
    "return_consumption_receipt",
)

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
MAX_FG3_HISTORICAL_OBSERVATIONS = 50_000
SOURCE_ATTEMPT_GRAMMAR = (
    ("HEAD",),
    ("HEAD", "GET"),
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
_STALE_AFTER = timedelta(hours=24)

DISCOVERY_MODES = (
    "hardcoded_urls",
    "paginated_catalog",
    "catalog_link_extraction",
    "sitemap_bfs",
)
SITE_TYPES = (
    "traditional_ssr",
    "ecommerce",
    "spa_js_heavy",
    "paginated_catalog",
    "catalog_link_extraction",
    "cloudflare_protected",
)
SOURCE_ERROR_CLASSES = (
    "NONE",
    "TIMEOUT",
    "DNS_FAILURE",
    "TLS_FAILURE",
    "TRANSPORT_FAILURE",
    "UNSAFE_TARGET",
)
SOURCE_REDIRECT_CLASSIFICATIONS = (
    "NO_REDIRECT",
    "SAME_ORIGIN_PUBLIC",
    "OTHER_PUBLIC",
)
REDIRECT_EVIDENCE_POLICY = "NO_REDIRECT_WITHOUT_DERIVATION_EVIDENCE"
SOURCE_TERMINAL_REASONS = (
    "SOURCE_ACCESSIBLE",
    "SOURCE_HTTP_404",
    "SOURCE_HTTP_410",
    "SOURCE_INACCESSIBLE",
    "SOURCE_ACCESS_403",
    "SOURCE_TIMEOUT",
    "SOURCE_DNS_FAILURE",
    "SOURCE_TLS_FAILURE",
    "SOURCE_TRANSPORT_FAILURE",
    "SOURCE_UNSAFE_TARGET",
)
SOURCE_ROLE_PROBE_TARGET = "PROBE_TARGET"
SOURCE_ROLE_TEMPLATE = "TEMPLATE"
SOURCE_ROLE_FILTER = "FILTER"
SOURCE_CONFIGURATION_ROLES = MappingProxyType(
    {
        "static_targets": SOURCE_ROLE_PROBE_TARGET,
        "catalog_url_patterns": SOURCE_ROLE_TEMPLATE,
        "allowed_url_patterns": SOURCE_ROLE_FILTER,
        "exclusion_patterns": SOURCE_ROLE_FILTER,
    }
)
GO_COMPATIBLE_SOURCE_TERMINALS = frozenset({"SOURCE_ACCESSIBLE"})
SOURCE_SCOPE = "STATIC_HARVESTER_ENTRY_TARGETS_ONLY"
EXCLUDED_DYNAMIC_SOURCE_KINDS = (
    "NESTED_SITEMAP",
    "CATALOG_EXTRACTED_LINK",
    "BFS_CHILD",
)
NON_HTML_EXTENSIONS = (
    ".pdf", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".jpg", ".jpeg", ".png",
    ".gif", ".svg", ".webp", ".bmp", ".ico", ".mp4", ".mp3", ".avi",
    ".mov", ".wmv", ".css", ".js", ".json", ".xml",
)

TABLE_COLUMNS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "institutions": ("id", "name", "slug", "website_url", "last_harvest_at"),
        "institution_site_profiles": (
            "id",
            "institution_id",
            "discovery_enabled",
            "pipeline_enabled",
            "pipeline_ready",
            "site_type",
            "discovery_mode",
            "seed_urls",
            "catalog_url_patterns",
            "catalog_max_pages",
            "allowed_url_patterns",
            "exclusion_patterns",
            "requires_cloudflare_bypass",
            "warmup_url",
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
LEGACY_PROFILE_COLUMNS = tuple(
    column
    for column in TABLE_COLUMNS["institution_site_profiles"]
    if column != "pipeline_enabled"
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
class GateIntent:
    gate_id: str
    repository_id: int
    owner_id: int
    ref: str
    ref_protected: bool
    candidate_sha: str
    candidate_tree: str
    workflow_path: str
    workflow_ref: str
    workflow_sha: str
    workflow_blob_sha: str
    run_id: int
    run_attempt: int
    check_run_id: int
    job_name: str
    environment_name: str
    environment_id: int
    deployment_id: int
    actor_id: int
    triggering_actor_id: int
    approver_id: int
    contract_digest: str
    schema_digest: str
    algorithm_digest: str
    capability_digest: str
    issued_at: datetime
    expires_at: datetime
    nonce_digest: str


@dataclass(frozen=True)
class GitHubOidcClaims:
    issuer: str
    audience: str
    repository_id: int
    owner_id: int
    ref: str
    ref_protected: bool
    sha: str
    workflow_ref: str
    workflow_sha: str
    run_id: int
    run_attempt: int
    actor_id: int
    triggering_actor_id: int
    jti: str
    issued_at: datetime
    expires_at: datetime
    signature_verified: bool
    jwks_verified: bool


@dataclass(frozen=True)
class WorkflowRunEvidence:
    run_id: int
    run_attempt: int
    check_run_id: int
    job_name: str
    workflow_path: str
    workflow_ref: str
    workflow_sha: str
    workflow_blob_sha: str
    head_sha: str
    head_tree: str
    actor_id: int
    triggering_actor_id: int
    event: str
    conclusion: str


@dataclass(frozen=True)
class EnvironmentEvidence:
    name: str
    environment_id: int
    protected: bool
    deployment_branch_policy_ref: str


@dataclass(frozen=True)
class ApprovalEvidence:
    environment_name: str
    environment_id: int
    run_id: int
    check_run_id: int
    deployment_id: int
    sha: str
    workflow_sha: str
    approver_id: int
    approver_login: str
    initiated_by_id: int
    state: str
    approved_at: datetime


@dataclass(frozen=True)
class DeploymentEvidence:
    deployment_id: int
    environment_name: str
    environment_id: int
    sha: str
    ref: str
    state: str


@dataclass(frozen=True)
class GateConsumptionReceipt:
    gate_id: str
    identity: str
    result: str
    state_before: str
    state_after: str
    compare_and_set_matched: bool
    nonce_digest: str
    jti: str
    consumed_at: datetime
    diagnosis_completed: bool


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
class StaticSourceTarget:
    role: str
    kind: str
    url: str
    source_fingerprint: str


@dataclass(frozen=True)
class EffectiveProfileRouting:
    profile_fingerprint: str
    institution_fingerprint: str
    institution_id: str
    website_url: str
    discovery_enabled: bool
    pipeline_enabled_present: bool
    pipeline_enabled: bool | None
    pipeline_ready: bool
    circuit_open: bool
    circuit_opened_at: str | None
    circuit_effective_open: bool
    circuit_auto_closed: bool
    observed_at: datetime
    site_type: str
    discovery_mode: str
    seed_urls: tuple[str, ...]
    catalog_url_patterns: tuple[str, ...]
    catalog_max_pages: int
    allowed_url_patterns: tuple[str, ...]
    exclusion_patterns: tuple[str, ...]
    requires_cloudflare_bypass: bool
    warmup_url: str | None
    browser_required: bool
    eligible: bool
    static_targets: tuple[StaticSourceTarget, ...]
    routing_fingerprint: str


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
class SourceAttemptResult:
    method: str
    started_at_utc: datetime
    ended_at_utc: datetime
    monotonic_started_ns: int
    monotonic_ended_ns: int
    status_code: int | None = None
    error_class: str = "NONE"
    redirect_classification: str = "NO_REDIRECT"


@dataclass(frozen=True)
class SourceObservationEvidence:
    target_binding_digest: str
    snapshot_pair_id: str
    profile_fingerprint: str
    source_fingerprint: str
    run_fingerprint: str
    cohort_fingerprint: str
    method_sequence: tuple[str, ...]
    attempt_results: tuple[SourceAttemptResult, ...]
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
        GateIntent: (
            "gate_id", "repository_id", "owner_id", "ref", "ref_protected",
            "candidate_sha", "candidate_tree", "workflow_path", "workflow_ref",
            "workflow_sha", "workflow_blob_sha", "run_id", "run_attempt",
            "check_run_id", "job_name", "environment_name", "environment_id",
            "deployment_id", "actor_id", "triggering_actor_id", "approver_id",
            "contract_digest", "schema_digest", "algorithm_digest", "capability_digest",
            "issued_at", "expires_at", "nonce_digest",
        ),
        GitHubOidcClaims: (
            "issuer", "audience", "repository_id", "owner_id", "ref",
            "ref_protected", "sha", "workflow_ref", "workflow_sha", "run_id",
            "run_attempt", "actor_id", "triggering_actor_id", "jti", "issued_at",
            "expires_at", "signature_verified", "jwks_verified",
        ),
        WorkflowRunEvidence: (
            "run_id", "run_attempt", "check_run_id", "job_name", "workflow_path",
            "workflow_ref", "workflow_sha", "workflow_blob_sha", "head_sha",
            "head_tree", "actor_id", "triggering_actor_id", "event", "conclusion",
        ),
        EnvironmentEvidence: (
            "name", "environment_id", "protected", "deployment_branch_policy_ref",
        ),
        ApprovalEvidence: (
            "environment_name", "environment_id", "run_id", "check_run_id",
            "deployment_id", "sha", "workflow_sha", "approver_id", "approver_login",
            "initiated_by_id", "state", "approved_at",
        ),
        DeploymentEvidence: (
            "deployment_id", "environment_name", "environment_id", "sha", "ref",
            "state",
        ),
        GateConsumptionReceipt: (
            "gate_id", "identity", "result", "state_before", "state_after",
            "compare_and_set_matched", "nonce_digest", "jti", "consumed_at",
            "diagnosis_completed",
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
        StaticSourceTarget: ("role", "kind", "url", "source_fingerprint"),
        EffectiveProfileRouting: (
            "profile_fingerprint", "institution_fingerprint", "institution_id",
            "website_url", "discovery_enabled", "pipeline_enabled_present",
            "pipeline_enabled", "pipeline_ready", "circuit_open", "circuit_opened_at",
            "circuit_effective_open", "circuit_auto_closed", "observed_at", "site_type",
            "discovery_mode", "seed_urls", "catalog_url_patterns",
            "catalog_max_pages", "allowed_url_patterns", "exclusion_patterns",
            "requires_cloudflare_bypass", "warmup_url", "browser_required",
            "eligible", "static_targets", "routing_fingerprint",
        ),
        SourceObservationRequest: (
            "target_binding_digest", "snapshot_pair_id", "profile_fingerprint",
            "source_fingerprint", "run_fingerprint", "cohort_fingerprint",
            "method_sequence", "max_attempts",
        ),
        SourceAttemptResult: (
            "method", "started_at_utc", "ended_at_utc", "monotonic_started_ns",
            "monotonic_ended_ns", "status_code", "error_class",
            "redirect_classification",
        ),
        SourceObservationEvidence: (
            "target_binding_digest", "snapshot_pair_id", "profile_fingerprint",
            "source_fingerprint", "run_fingerprint", "cohort_fingerprint",
            "method_sequence", "attempt_results", "attempts", "terminal_reason",
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
            "target", "capability", "historical_manifest", "historical_anchor",
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
    accepted_columns = (columns,)
    if columns == TABLE_COLUMNS["institution_site_profiles"]:
        accepted_columns = (columns, LEGACY_PROFILE_COLUMNS)
    if tuple(keys) not in accepted_columns or len(keys) != len(set(keys)):
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
        + b":v2.3\0"
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


def expected_trust_digest(kind: str) -> str:
    if kind == "contract":
        return _digest("trust-contract", CONTRACT_VERSION)
    if kind == "schema":
        return _digest("trust-schema", SCHEMA_VERSION)
    if kind == "algorithm":
        return _digest("trust-algorithm", ALGORITHM_VERSION)
    if kind == "capability":
        return _digest(
            "trust-capability",
            (
                GET_ONLY_CAPABILITY.methods,
                tuple(
                    (query.table, query.columns, query.filters, query.order)
                    for query in GET_ONLY_CAPABILITY.queries
                ),
                GET_ONLY_CAPABILITY.max_snapshot_bytes,
            ),
        )
    _raise(STOP_AUTHORITY_INVALID)


def reject_caller_supplied_authority(payload: Mapping[str, object]) -> None:
    if type(payload) is not dict or any(type(key) is not str for key in payload):
        _raise(STOP_AUTHORITY_INVALID)
    if CALLER_SUPPLIED_AUTHORITY_FIELDS & set(payload):
        _raise(STOP_AUTHORITY_INVALID)


def _valid_positive_id(value: object) -> bool:
    return type(value) is int and value > 0 and value <= MAX_IMMUTABLE_INTEGER_ABS


def _validate_gate_intent(intent: object, evaluated_at: datetime) -> GateIntent:
    _require_complete(intent, GateIntent, STOP_AUTHORITY_INVALID)
    if (
        not _valid_digest(intent.gate_id)
        or not _valid_positive_id(intent.repository_id)
        or not _valid_positive_id(intent.owner_id)
        or intent.ref != EXPECTED_REF
        or type(intent.ref_protected) is not bool
        or not intent.ref_protected
        or intent.candidate_sha != PROTECTED_SOURCE_SHA
        or intent.candidate_tree != PROTECTED_SOURCE_TREE
        or intent.workflow_path != EXPECTED_WORKFLOW_PATH
        or intent.workflow_ref != f"{EXPECTED_REPOSITORY}/{EXPECTED_WORKFLOW_PATH}@{EXPECTED_REF}"
        or intent.workflow_sha != EXPECTED_WORKFLOW_SHA
        or intent.workflow_blob_sha != EXPECTED_WORKFLOW_BLOB_SHA
        or not _valid_positive_id(intent.run_id)
        or intent.run_attempt != 1
        or not _valid_positive_id(intent.check_run_id)
        or intent.job_name != EXPECTED_WORKFLOW
        or intent.environment_name != EXPECTED_ENVIRONMENT
        or not _valid_positive_id(intent.environment_id)
        or not _valid_positive_id(intent.deployment_id)
        or not _valid_positive_id(intent.actor_id)
        or not _valid_positive_id(intent.triggering_actor_id)
        or not _valid_positive_id(intent.approver_id)
        or intent.approver_id in {intent.actor_id, intent.triggering_actor_id}
        or intent.contract_digest != expected_trust_digest("contract")
        or intent.schema_digest != expected_trust_digest("schema")
        or intent.algorithm_digest != expected_trust_digest("algorithm")
        or intent.capability_digest != expected_trust_digest("capability")
        or not _valid_digest(intent.nonce_digest)
        or not _is_utc(intent.issued_at)
        or not _is_utc(intent.expires_at)
        or intent.expires_at <= intent.issued_at
    ):
        _raise(STOP_AUTHORITY_INVALID)
    if not _is_utc(evaluated_at):
        _raise(STOP_CLOCK_TIMING_INVALID)
    if not (intent.issued_at <= evaluated_at < intent.expires_at):
        _raise(STOP_GATE_EXPIRED)
    return intent


def _validate_oidc_claims(claims: object, intent: GateIntent, evaluated_at: datetime) -> GitHubOidcClaims:
    _require_complete(claims, GitHubOidcClaims, STOP_PROOF_INVALID)
    if (
        claims.issuer != EXPECTED_OIDC_ISSUER
        or claims.audience != EXPECTED_OIDC_AUDIENCE
        or claims.repository_id != intent.repository_id
        or claims.owner_id != intent.owner_id
        or claims.ref != intent.ref
        or claims.ref_protected != intent.ref_protected
        or claims.sha != intent.candidate_sha
        or claims.workflow_ref != intent.workflow_ref
        or claims.workflow_sha != intent.workflow_sha
        or claims.run_id != intent.run_id
        or claims.run_attempt != 1
        or claims.actor_id != intent.actor_id
        or claims.triggering_actor_id != intent.triggering_actor_id
        or type(claims.jti) is not str
        or len(claims.jti) < 16
        or not _is_utc(claims.issued_at)
        or not _is_utc(claims.expires_at)
        or not (claims.issued_at <= evaluated_at < claims.expires_at)
        or type(claims.signature_verified) is not bool
        or type(claims.jwks_verified) is not bool
        or not claims.signature_verified
        or not claims.jwks_verified
    ):
        _raise(STOP_PROOF_INVALID)
    return claims


def _validate_workflow_run(run: object, intent: GateIntent) -> WorkflowRunEvidence:
    _require_complete(run, WorkflowRunEvidence, STOP_BINDING_DRIFT)
    if (
        run.run_id != intent.run_id
        or run.run_attempt != 1
        or run.check_run_id != intent.check_run_id
        or run.job_name != intent.job_name
        or run.workflow_path != intent.workflow_path
        or run.workflow_ref != intent.workflow_ref
        or run.workflow_sha != intent.workflow_sha
        or run.workflow_blob_sha != intent.workflow_blob_sha
        or run.head_sha != intent.candidate_sha
        or run.head_tree != intent.candidate_tree
        or run.actor_id != intent.actor_id
        or run.triggering_actor_id != intent.triggering_actor_id
        or run.event != "workflow_dispatch"
        or run.conclusion != "success"
    ):
        _raise(STOP_BINDING_DRIFT)
    return run


def _validate_environment(environment: object, intent: GateIntent) -> EnvironmentEvidence:
    _require_complete(environment, EnvironmentEvidence, STOP_BINDING_DRIFT)
    if (
        environment.name != EXPECTED_ENVIRONMENT
        or environment.environment_id != intent.environment_id
        or type(environment.protected) is not bool
        or not environment.protected
        or environment.deployment_branch_policy_ref != EXPECTED_REF
    ):
        _raise(STOP_BINDING_DRIFT)
    return environment


def _validate_approval(
    approvals: object, intent: GateIntent, evaluated_at: datetime,
) -> ApprovalEvidence:
    if type(approvals) is not tuple or len(approvals) != 1:
        _raise(STOP_APPROVAL_INVALID)
    approval = approvals[0]
    _require_complete(approval, ApprovalEvidence, STOP_APPROVAL_INVALID)
    if (
        approval.environment_name != intent.environment_name
        or approval.environment_id != intent.environment_id
        or approval.run_id != intent.run_id
        or approval.check_run_id != intent.check_run_id
        or approval.deployment_id != intent.deployment_id
        or approval.sha != intent.candidate_sha
        or approval.workflow_sha != intent.workflow_sha
        or approval.approver_id != intent.approver_id
        or not _valid_positive_id(approval.approver_id)
        or type(approval.approver_login) is not str
        or not _valid_identity(approval.approver_login)
        or approval.initiated_by_id != intent.actor_id
        or approval.approver_id == approval.initiated_by_id
        or approval.state != "approved"
        or not _is_utc(approval.approved_at)
        or not (intent.issued_at <= approval.approved_at <= evaluated_at < intent.expires_at)
    ):
        _raise(STOP_APPROVAL_INVALID)
    return approval


def _validate_deployment(deployments: object, intent: GateIntent) -> DeploymentEvidence:
    if type(deployments) is not tuple or len(deployments) != 1:
        _raise(STOP_BINDING_DRIFT)
    deployment = deployments[0]
    _require_complete(deployment, DeploymentEvidence, STOP_BINDING_DRIFT)
    if (
        deployment.deployment_id != intent.deployment_id
        or deployment.environment_name != intent.environment_name
        or deployment.environment_id != intent.environment_id
        or deployment.sha != intent.candidate_sha
        or deployment.ref != intent.ref
        or deployment.state != "success"
    ):
        _raise(STOP_BINDING_DRIFT)
    return deployment


def _validate_receipt(
    receipt: object, intent: GateIntent, claims: GitHubOidcClaims, evaluated_at: datetime,
) -> GateConsumptionReceipt:
    _require_complete(receipt, GateConsumptionReceipt, STOP_CONSUMPTION_AMBIGUOUS)
    expected_identity = _digest(
        "gate-consumer",
        (intent.repository_id, intent.run_id, intent.run_attempt, intent.check_run_id),
    )
    if (
        receipt.gate_id != intent.gate_id
        or receipt.identity != expected_identity
        or receipt.result != "CONSUMED"
        or receipt.state_before != G5_TRUST_GATE_STATE_READY
        or receipt.state_after != G5_TRUST_GATE_STATE_CONSUMED
        or type(receipt.compare_and_set_matched) is not bool
        or not receipt.compare_and_set_matched
        or receipt.nonce_digest != intent.nonce_digest
        or receipt.jti != claims.jti
        or not _is_utc(receipt.consumed_at)
        or not (intent.issued_at <= receipt.consumed_at <= evaluated_at < intent.expires_at)
        or type(receipt.diagnosis_completed) is not bool
    ):
        _raise(STOP_CONSUMPTION_AMBIGUOUS)
    return receipt


def validate_future_trust_plane(
    *,
    intent: GateIntent,
    oidc_claims: GitHubOidcClaims,
    workflow_run: WorkflowRunEvidence,
    environment: EnvironmentEvidence,
    approvals: tuple[ApprovalEvidence, ...],
    deployments: tuple[DeploymentEvidence, ...],
    receipt: GateConsumptionReceipt,
    evaluated_at: datetime,
    seen_jtis: tuple[str, ...] = (),
    seen_nonce_digests: tuple[str, ...] = (),
    consumed_identities: tuple[str, ...] = (),
) -> str:
    gate = _validate_gate_intent(intent, evaluated_at)
    claims = _validate_oidc_claims(oidc_claims, gate, evaluated_at)
    if claims.jti in seen_jtis or gate.nonce_digest in seen_nonce_digests:
        _raise(STOP_REPLAY_DETECTED)
    _validate_workflow_run(workflow_run, gate)
    _validate_environment(environment, gate)
    _validate_approval(approvals, gate, evaluated_at)
    _validate_deployment(deployments, gate)
    consumption = _validate_receipt(receipt, gate, claims, evaluated_at)
    if consumption.identity in consumed_identities:
        _raise(STOP_CONSUMPTION_AMBIGUOUS)
    _raise(STOP_ATOMIC_LEDGER_REQUIRED)


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


def _enforce_fg3_collection_limit(count: int) -> None:
    if (
        type(count) is not int
        or count < 0
        or count > MAX_FG3_HISTORICAL_OBSERVATIONS
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)


def _enforce_fg3_historical_observation_limit(count: int) -> None:
    _enforce_fg3_collection_limit(count)


def _validate_manifest_shape(manifest: object) -> HistoricalFG3Manifest:
    _require_complete(manifest, HistoricalFG3Manifest, STOP_MANIFEST_ANCHOR_MISMATCH)
    if (
        type(manifest.expected_observation_fingerprints) is not tuple
        or type(manifest.observation_categories) is not tuple
        or type(manifest.category_counts) is not tuple
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    _enforce_fg3_historical_observation_limit(
        len(manifest.expected_observation_fingerprints)
    )
    _enforce_fg3_historical_observation_limit(len(manifest.observation_categories))
    if len(manifest.category_counts) != 3:
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
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
    if type(historical_observations) is not tuple:
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    _enforce_fg3_historical_observation_limit(len(historical_observations))
    if not historical_observations:
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
    allowed_historical_categories = set(FG3_HISTORICAL_CATEGORY_COUNTS) | {
        "PRIOR_DEACTIVATION"
    }
    observed_counts = {
        category: sum(value == category for value in categories.values())
        for category in FG3_HISTORICAL_CATEGORY_COUNTS
    }
    if (
        set(categories) != set(fingerprints)
        or not set(categories.values()) <= allowed_historical_categories
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
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    _enforce_fg3_collection_limit(len(evidence.courses))
    _enforce_fg3_collection_limit(len(evidence.prior_mutations))
    _enforce_fg3_historical_observation_limit(
        len(evidence.historical_observations)
    )
    if len(evidence.historical_observations) < 27:
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
    expected_historical_count = 27 + max(0, len(required_inactive) - 1)
    deactivation_observations = {
        fingerprint
        for fingerprint, observation in observations_by_fingerprint.items()
        if observation.category in {"DEACTIVATION", "PRIOR_DEACTIVATION"}
    }
    if (
        len(evidence.historical_observations) != expected_historical_count
        or len(deactivation_observations) != len(required_inactive)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    mutations_by_course: dict[str, list[FG3PriorMutationEvidence]] = {}
    seen_mutation_fingerprints: set[str] = set()
    consumed_deactivation_observations: set[str] = set()
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
            or mutation.historical_observation_fingerprint
            in consumed_deactivation_observations
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
            or observation.category not in {"DEACTIVATION", "PRIOR_DEACTIVATION"}
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
        consumed_deactivation_observations.add(
            mutation.historical_observation_fingerprint
        )
        mutations_by_course.setdefault(mutation.course_fingerprint, []).append(mutation)
    if (
        primary != required_active
        or seen_courses != set(first_by_fingerprint)
        or set(mutations_by_course) != required_inactive
        or any(len(items) != 1 for items in mutations_by_course.values())
        or consumed_deactivation_observations != deactivation_observations
        or historical != set(validated_manifest.expected_observation_fingerprints)
    ):
        _raise(STOP_MANIFEST_ANCHOR_MISMATCH)
    return frozenset(primary), frozenset(mutations_by_course)


def _routing_list(value: ImmutableValue) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str or not item for item in value):
        _raise(STOP_PROFILE_ROUTING_INVALID)
    return value


def _routing_optional_string(value: ImmutableValue) -> str | None:
    if type(value) not in {str, type(None)}:
        _raise(STOP_PROFILE_ROUTING_INVALID)
    return value


def _routing_url(value: object) -> str:
    if type(value) is not str or not value:
        _raise(STOP_PROFILE_ROUTING_INVALID)
    identity = build_url_identity(value)
    if (
        not identity.host
        or not identity.canonical_url
        or identity.canonical_url.startswith("urn:")
    ):
        _raise(STOP_PROFILE_ROUTING_INVALID)
    host = identity.host.lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        _raise(STOP_PROFILE_ROUTING_INVALID)
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        _raise(STOP_PROFILE_ROUTING_INVALID)
    return identity.canonical_url


def _is_safe_profile_regex(pattern: object) -> bool:
    if type(pattern) is not str or len(pattern) > 200:
        return False
    # Deliberately linear subset.  Reject all unescaped grouping,
    # alternation and quantifier metacharacters before invoking re.search.
    escaped = False
    for character in pattern:
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character in "()|*+?{}":
            return False
    if escaped:
        return False
    unsafe = (r"(\([^)]*[*+][^)]*\))+[*+]", r"\\[1-9]", r"\(\?([=!<])")
    return not any(re.search(expression, pattern) for expression in unsafe)


def _validated_profile_patterns(value: ImmutableValue) -> tuple[str, ...]:
    patterns = _routing_list(value)
    for pattern in patterns:
        if pattern.startswith("re:"):
            expression = pattern[3:]
            if not _is_safe_profile_regex(expression):
                _raise(STOP_PROFILE_ROUTING_INVALID)
            try:
                re.compile(expression, re.IGNORECASE)
            except re.error:
                _raise(STOP_PROFILE_ROUTING_INVALID)
    return patterns


def _ordered_hardcoded_seeds(seeds: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for seed in seeds:
        canonical = _routing_url(seed)
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return tuple(result)


def _harvester_candidate_allowed(
    url: str,
    website_url: str,
    allowed_patterns: tuple[str, ...],
    exclusion_patterns: tuple[str, ...],
) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != urlparse(website_url).netloc or parsed.path.lower().endswith(NON_HTML_EXTENSIONS):
        return False
    lowered = url.lower()
    regex_url_text = lowered[:2000]
    for pattern in exclusion_patterns:
        if pattern.startswith("re:"):
            expression = pattern[3:]
            if not _is_safe_profile_regex(expression):
                _raise(STOP_PROFILE_ROUTING_INVALID)
            try:
                compiled = re.compile(expression, re.IGNORECASE)
                if compiled.search(regex_url_text):
                    return False
            except re.error:
                _raise(STOP_PROFILE_ROUTING_INVALID)
        elif pattern.lower() in lowered:
            return False
    if not allowed_patterns:
        return True
    for pattern in allowed_patterns:
        if pattern.startswith("re:"):
            expression = pattern[3:]
            if not _is_safe_profile_regex(expression):
                _raise(STOP_PROFILE_ROUTING_INVALID)
            try:
                compiled = re.compile(expression, re.IGNORECASE)
                if compiled.search(parsed.path[:2000]):
                    return True
            except re.error:
                _raise(STOP_PROFILE_ROUTING_INVALID)
        elif pattern.lower() in lowered:
            return True
    return False


def _enforce_profile_source_pair_limit(count: int) -> None:
    if type(count) is not int or count < 0 or count > MAX_PROFILE_SOURCE_PAIRS:
        _raise(STOP_TARGET_BINDING_INVALID)


def derive_effective_profile_routing(
    profile_fingerprint: str,
    profile_row: FrozenRow,
    institution_fingerprint: str,
    institution_row: FrozenRow,
    observed_at: datetime,
) -> EffectiveProfileRouting:
    if (
        not _valid_digest(profile_fingerprint)
        or not _valid_digest(institution_fingerprint)
        or not _is_utc(observed_at)
    ):
        _raise(STOP_PROFILE_ROUTING_INVALID)
    profile = _validate_frozen_row(
        profile_row,
        TABLE_COLUMNS["institution_site_profiles"],
        STOP_PROFILE_ROUTING_INVALID,
    )
    institution = _validate_frozen_row(
        institution_row, TABLE_COLUMNS["institutions"], STOP_PROFILE_ROUTING_INVALID
    )
    profile_values = dict(profile.values)
    institution_values = dict(institution.values)
    institution_id = profile_values.get("institution_id")
    if (
        type(institution_id) is not str
        or institution_id != institution_values.get("id")
        or type(profile_values.get("discovery_enabled")) is not bool
        or type(profile_values.get("pipeline_ready")) is not bool
        or type(profile_values.get("circuit_open")) is not bool
        or type(profile_values.get("requires_cloudflare_bypass")) is not bool
    ):
        _raise(STOP_PROFILE_ROUTING_INVALID)

    pipeline_enabled_present = "pipeline_enabled" in profile_values
    pipeline_enabled = profile_values.get("pipeline_enabled")
    if pipeline_enabled_present and type(pipeline_enabled) is not bool:
        _raise(STOP_PROFILE_ROUTING_INVALID)
    pipeline_gate = pipeline_enabled if pipeline_enabled_present else profile_values["pipeline_ready"]
    raw_circuit_opened_at = _routing_optional_string(profile_values.get("circuit_opened_at"))
    parsed_circuit_opened_at: datetime | None = None
    if profile_values["circuit_open"] and raw_circuit_opened_at is not None:
        try:
            parsed_circuit_opened_at = datetime.fromisoformat(
                raw_circuit_opened_at.replace("Z", "+00:00")
            )
        except ValueError:
            _raise(STOP_PROFILE_ROUTING_INVALID)
        if not _is_utc(parsed_circuit_opened_at):
            _raise(STOP_PROFILE_ROUTING_INVALID)
        parsed_circuit_opened_at = parsed_circuit_opened_at.astimezone(timezone.utc)
    circuit_opened_at = (
        _timestamp_text(parsed_circuit_opened_at)
        if parsed_circuit_opened_at is not None
        else raw_circuit_opened_at
    )
    circuit_effective_open = bool(
        profile_values["circuit_open"]
        and parsed_circuit_opened_at is not None
        and observed_at - parsed_circuit_opened_at < timedelta(hours=24)
    )
    circuit_auto_closed = bool(
        profile_values["circuit_open"]
        and parsed_circuit_opened_at is not None
        and not circuit_effective_open
    )

    website_url = _routing_url(institution_values.get("website_url"))
    site_type = profile_values.get("site_type")
    discovery_mode = profile_values.get("discovery_mode")
    if type(site_type) is not str or site_type not in SITE_TYPES:
        _raise(STOP_PROFILE_ROUTING_INVALID)
    if type(discovery_mode) is not str or discovery_mode not in DISCOVERY_MODES:
        _raise(STOP_PROFILE_ROUTING_INVALID)
    seeds = _routing_list(profile_values.get("seed_urls"))
    catalogs = _routing_list(profile_values.get("catalog_url_patterns"))
    allowed = _validated_profile_patterns(profile_values.get("allowed_url_patterns"))
    exclusions = _validated_profile_patterns(profile_values.get("exclusion_patterns"))
    max_pages = profile_values.get("catalog_max_pages")
    warmup_url = _routing_optional_string(profile_values.get("warmup_url"))
    if type(max_pages) is not int:
        _raise(STOP_PROFILE_ROUTING_INVALID)

    browser_required = site_type in {"spa_js_heavy", "ecommerce"} or discovery_mode == "catalog_link_extraction"
    eligible = bool(
        profile_values["discovery_enabled"]
        and pipeline_gate
        and not circuit_effective_open
    )
    bound_seeds = (
        tuple(_routing_url(seed) for seed in seeds)
        if eligible and discovery_mode in {"hardcoded_urls", "catalog_link_extraction"}
        else seeds
    )
    bound_warmup_url = (
        _routing_url(warmup_url)
        if eligible
        and browser_required
        and profile_values["requires_cloudflare_bypass"]
        and warmup_url
        else warmup_url
    )
    target_values: list[tuple[str, str]] = []
    if eligible and discovery_mode == "hardcoded_urls" and bound_seeds:
        if len(bound_seeds) > MAX_SOURCES_PER_PROFILE:
            _raise(STOP_TARGET_BINDING_INVALID)
        effective_seeds = tuple(
            seed
            for seed in _ordered_hardcoded_seeds(bound_seeds)
            if _harvester_candidate_allowed(seed, website_url, allowed, exclusions)
        )
        target_values.extend(("HARDCODED_DETAIL", value) for value in effective_seeds)
    elif eligible and discovery_mode == "paginated_catalog" and catalogs:
        if not 1 <= max_pages <= MAX_SOURCES_PER_PROFILE:
            _raise(STOP_TARGET_BINDING_INVALID)
        for template in catalogs:
            for page in range(1, max_pages + 1):
                target_values.append(("CATALOG_PAGE", _routing_url(template.replace("{page}", str(page)))))
    elif eligible and discovery_mode == "catalog_link_extraction":
        if len(bound_seeds) > MAX_SOURCES_PER_PROFILE:
            _raise(STOP_TARGET_BINDING_INVALID)
        catalog_roots = list(bound_seeds)
        if website_url not in catalog_roots:
            catalog_roots.append(website_url)
        target_values.extend(("CATALOG_ROOT", value) for value in catalog_roots)
    elif eligible:
        # Empty hardcoded/catalog configuration follows the harvester's real
        # None fallback into sitemap+BFS; no preflight-only requirement is added.
        target_values.extend(
            (
                ("SITEMAP_ROOT", _routing_url(urljoin(website_url, "/sitemap.xml"))),
                ("BFS_ROOT", website_url),
            )
        )
    if eligible and browser_required and profile_values["requires_cloudflare_bypass"] and bound_warmup_url:
        target_values.insert(0, ("WARMUP", bound_warmup_url))
    deduplicated_targets: list[tuple[str, str]] = []
    seen_targets: set[tuple[str, str]] = set()
    for kind, url in target_values:
        canonical_target = (kind, _routing_url(url))
        if canonical_target not in seen_targets:
            seen_targets.add(canonical_target)
            deduplicated_targets.append(canonical_target)
    target_values = deduplicated_targets
    if len(target_values) > MAX_SOURCES_PER_PROFILE:
        _raise(STOP_TARGET_BINDING_INVALID)

    configuration = (
        profile_fingerprint,
        institution_fingerprint,
        institution_id,
        website_url,
        profile_values["discovery_enabled"],
        pipeline_enabled_present,
        pipeline_enabled,
        profile_values["pipeline_ready"],
        profile_values["circuit_open"],
        circuit_opened_at,
        circuit_effective_open,
        circuit_auto_closed,
        _timestamp_text(observed_at),
        site_type,
        discovery_mode,
        bound_seeds,
        catalogs,
        max_pages,
        allowed,
        exclusions,
        profile_values["requires_cloudflare_bypass"],
        bound_warmup_url,
        browser_required,
        eligible,
    )
    configuration_digest = _digest("effective-routing-configuration", configuration)
    targets = tuple(
        StaticSourceTarget(
            SOURCE_ROLE_PROBE_TARGET,
            kind,
            value,
            _digest(
                "profile-source",
                (configuration_digest, index, SOURCE_ROLE_PROBE_TARGET, kind, value),
            ),
        )
        for index, (kind, value) in enumerate(target_values)
    )
    routing_fingerprint = _digest(
        "effective-routing",
        (
            configuration,
            tuple(
                (item.role, item.kind, item.url, item.source_fingerprint)
                for item in targets
            ),
        ),
    )
    return EffectiveProfileRouting(
        profile_fingerprint,
        institution_fingerprint,
        institution_id,
        website_url,
        profile_values["discovery_enabled"],
        pipeline_enabled_present,
        pipeline_enabled,
        profile_values["pipeline_ready"],
        profile_values["circuit_open"],
        circuit_opened_at,
        circuit_effective_open,
        circuit_auto_closed,
        observed_at,
        site_type,
        discovery_mode,
        bound_seeds,
        catalogs,
        max_pages,
        allowed,
        exclusions,
        profile_values["requires_cloudflare_bypass"],
        bound_warmup_url,
        browser_required,
        eligible,
        targets,
        routing_fingerprint,
    )


def profile_source_fingerprints(
    profile_fingerprint: str,
    row: FrozenRow,
    institution_fingerprint: str,
    institution_row: FrozenRow,
    observed_at: datetime,
) -> frozenset[str]:
    routing = derive_effective_profile_routing(
        profile_fingerprint,
        row,
        institution_fingerprint,
        institution_row,
        observed_at,
    )
    return frozenset(item.source_fingerprint for item in routing.static_targets)


def _eligible_profile_sources(
    target: TargetBinding,
    payload: SnapshotPairPayloadEvidence,
    observed_at: datetime,
) -> frozenset[tuple[str, str]]:
    if not _is_utc(observed_at):
        _raise(STOP_PROFILE_ROUTING_INVALID)
    profiles = _inventory_rows(
        payload, 1, "institution_site_profiles", STOP_PROFILE_ROUTING_INVALID
    )
    institutions = _inventory_rows(
        payload, 1, "institutions", STOP_PROFILE_ROUTING_INVALID
    )
    target_digest = evidence_binding_digest(target)
    institutions_by_id: dict[str, tuple[str, FrozenRow]] = {}
    for institution in institutions:
        identifier = _row_value(institution, "id")
        if type(identifier) is not str or identifier in institutions_by_id:
            _raise(STOP_PROFILE_ROUTING_INVALID)
        fingerprint = row_fingerprint(
            "institutions", target_digest, target.snapshot_pair_id, institution
        )
        institutions_by_id[identifier] = (fingerprint, institution)
    seen_institutions: set[str] = set()
    eligible: set[tuple[str, str]] = set()
    for profile in profiles:
        values = dict(profile.values)
        institution_id = values.get("institution_id")
        if type(institution_id) is not str or institution_id in seen_institutions:
            _raise(STOP_PROFILE_ROUTING_INVALID)
        joined = institutions_by_id.get(institution_id)
        if joined is None:
            _raise(STOP_PROFILE_ROUTING_INVALID)
        seen_institutions.add(institution_id)
        profile_fingerprint = row_fingerprint(
            "institution_site_profiles", target_digest, target.snapshot_pair_id, profile
        )
        routing = derive_effective_profile_routing(
            profile_fingerprint, profile, joined[0], joined[1], observed_at
        )
        if routing.eligible:
            _enforce_profile_source_pair_limit(len(eligible) + len(routing.static_targets))
            eligible.update(
                (profile_fingerprint, item.source_fingerprint)
                for item in routing.static_targets
            )
    return frozenset(eligible)


def _source_error_terminal(error_class: str) -> str:
    if type(error_class) is not str or error_class not in SOURCE_ERROR_CLASSES or error_class == "NONE":
        _raise(STOP_TARGET_BINDING_INVALID)
    return {
        "TIMEOUT": "SOURCE_TIMEOUT",
        "DNS_FAILURE": "SOURCE_DNS_FAILURE",
        "TLS_FAILURE": "SOURCE_TLS_FAILURE",
        "TRANSPORT_FAILURE": "SOURCE_TRANSPORT_FAILURE",
        "UNSAFE_TARGET": "SOURCE_UNSAFE_TARGET",
    }[error_class]


def _source_status_terminal(status: int, *, method: str) -> str:
    if type(status) is not int or not 100 <= status <= 599 or method not in {"HEAD", "GET"}:
        _raise(STOP_TARGET_BINDING_INVALID)
    if 200 <= status < 300:
        return "SOURCE_ACCESSIBLE"
    if status == 404:
        return "SOURCE_HTTP_404"
    if status == 410:
        return "SOURCE_HTTP_410"
    if method == "GET" and status == 403:
        return "SOURCE_ACCESS_403"
    if status in {408, 425, 429, 500, 502, 503, 504}:
        return "SOURCE_TIMEOUT"
    return "SOURCE_INACCESSIBLE"


def source_terminal_reason(results: tuple[SourceAttemptResult, ...]) -> str:
    if type(results) is not tuple or len(results) not in {1, 2}:
        _raise(STOP_TARGET_BINDING_INVALID)
    first = results[0]
    if type(first) is not SourceAttemptResult or first.method != "HEAD":
        _raise(STOP_TARGET_BINDING_INVALID)
    if (
        type(first.error_class) is not str
        or first.error_class not in SOURCE_ERROR_CLASSES
        or (first.error_class == "NONE") != (type(first.status_code) is int)
        or type(first.status_code) is bool
    ):
        _raise(STOP_TARGET_BINDING_INVALID)
    if first.error_class != "NONE":
        if len(results) != 1:
            _raise(STOP_TARGET_BINDING_INVALID)
        return _source_error_terminal(first.error_class)
    if type(first.status_code) is not int:
        _raise(STOP_TARGET_BINDING_INVALID)
    if first.status_code in {403, 405, 501}:
        if len(results) != 2 or type(results[1]) is not SourceAttemptResult or results[1].method != "GET":
            _raise(STOP_TARGET_BINDING_INVALID)
        final = results[1]
        if (
            type(final.error_class) is not str
            or final.error_class not in SOURCE_ERROR_CLASSES
            or (final.error_class == "NONE") != (type(final.status_code) is int)
            or type(final.status_code) is bool
        ):
            _raise(STOP_TARGET_BINDING_INVALID)
        if final.error_class != "NONE":
            return _source_error_terminal(final.error_class)
        if type(final.status_code) is not int:
            _raise(STOP_TARGET_BINDING_INVALID)
        return _source_status_terminal(final.status_code, method="GET")
    if len(results) != 1:
        _raise(STOP_TARGET_BINDING_INVALID)
    return _source_status_terminal(first.status_code, method="HEAD")


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
        type(evidence.attempt_results) is not tuple
        or type(methods) is not tuple
        or len(evidence.attempt_results) != len(methods)
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
        or evidence.terminal_reason not in SOURCE_TERMINAL_REASONS
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
    previous: SourceAttemptResult | None = None
    for index, timing in enumerate(evidence.attempt_results):
        _require_complete(timing, SourceAttemptResult, STOP_CLOCK_TIMING_INVALID)
        if (
            type(timing.method) is not str
            or timing.method != methods[index]
            or not _is_utc(timing.started_at_utc)
            or not _is_utc(timing.ended_at_utc)
            or not _strict_int(timing.monotonic_started_ns, 0, 2**63 - 1)
            or not _strict_int(timing.monotonic_ended_ns, 1, 2**63 - 1)
        ):
            _raise(STOP_CLOCK_TIMING_INVALID)
        if (
            type(timing.error_class) is not str
            or timing.error_class not in SOURCE_ERROR_CLASSES
            or type(timing.redirect_classification) is not str
            or timing.redirect_classification not in SOURCE_REDIRECT_CLASSIFICATIONS
            or timing.redirect_classification != "NO_REDIRECT"
            or type(timing.status_code) not in {int, type(None)}
            or type(timing.status_code) is bool
            or (timing.status_code is not None and not 100 <= timing.status_code <= 599)
            or (timing.error_class == "NONE") != (timing.status_code is not None)
        ):
            _raise(STOP_TARGET_BINDING_INVALID)
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
    if source_terminal_reason(evidence.attempt_results) != evidence.terminal_reason:
        _raise(STOP_SOURCE_BLOCKERS_PRESENT)


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
    observed_pairs: set[tuple[str, str]] = set()
    blockers = False
    first_attempts: list[tuple[tuple[str, str], SourceAttemptResult]] = []
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
        if unit in observed_pairs:
            _raise(STOP_SOURCE_BLOCKERS_PRESENT)
        validate_source_observation(
            bundle.request,
            bundle.evidence,
            validated_target,
            snapshot_payload,
            evaluated_at,
        )
        blockers = blockers or bundle.evidence.terminal_reason not in GO_COMPATIBLE_SOURCE_TERMINALS
        observed_pairs.add(unit)
        first_attempts.append((unit, bundle.evidence.attempt_results[0]))
    if first_attempts:
        utc_first = min(first_attempts, key=lambda item: item[1].started_at_utc)
        monotonic_first = min(
            first_attempts, key=lambda item: item[1].monotonic_started_ns
        )
        if utc_first[0] != monotonic_first[0]:
            _raise(STOP_CLOCK_TIMING_INVALID)
        routing_observed_at = utc_first[1].started_at_utc
    else:
        _, routing_observed_at, _, _ = _snapshot_bounds(
            snapshot_payload, STOP_TARGET_BINDING_INVALID
        )
    eligible = _eligible_profile_sources(
        validated_target, snapshot_payload, routing_observed_at
    )
    if any(unit not in eligible for unit in observed_pairs):
        _raise(STOP_SOURCE_BLOCKERS_PRESENT)
    if observed_pairs != set(eligible):
        _raise(STOP_SOURCE_BLOCKERS_PRESENT)
    if blockers:
        _raise(STOP_SOURCE_BLOCKERS_PRESENT)


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
    blockers = False
    for item in evidence:
        if type(item) is LifecycleEvidence:
            _require_complete(item, LifecycleEvidence, STOP_TARGET_BINDING_INVALID)
        if (
            type(item) is not LifecycleEvidence
            or not _valid_digest(item.staging_row_fingerprint)
            or type(item.proxy) is not LifecycleProxy
            or not _valid_lifecycle_proxy_shape(item.proxy)
        ):
            _raise(STOP_TARGET_BINDING_INVALID)
        if item.staging_row_fingerprint in observed:
            _raise(STOP_LIFECYCLE_BLOCKERS_PRESENT)
        row = expected.get(item.staging_row_fingerprint)
        if row is None:
            _raise(STOP_LIFECYCLE_BLOCKERS_PRESENT)
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
        if item.proxy.classification in {"STALE", "AGE_UNKNOWN", "FUTURE_TIMESTAMP"}:
            blockers = True
        if item.proxy != expected_proxy:
            _raise(STOP_LIFECYCLE_BLOCKERS_PRESENT)
        observed.add(item.staging_row_fingerprint)
    if observed != set(expected):
        _raise(STOP_LIFECYCLE_BLOCKERS_PRESENT)
    if blockers:
        _raise(STOP_LIFECYCLE_BLOCKERS_PRESENT)


def authorize_future_adapter(request: AuthorizationRequest) -> AuthorizedAdapterPlan:
    """Validate all pure evidence, then stop because trusted authority is absent."""
    _require_complete(request, AuthorizationRequest, STOP_TARGET_BINDING_INVALID)
    reject_caller_supplied_authority(request.__dict__)
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
    "ApprovalEvidence",
    "AuthorizationRequest",
    "AuthorizedAdapterPlan",
    "CALLER_SUPPLIED_AUTHORITY_FIELDS",
    "CLOCK_DURATION_TOLERANCE_NS",
    "MAX_IMMUTABLE_DEPTH",
    "MAX_IMMUTABLE_INTEGER_ABS",
    "MAX_IMMUTABLE_NODES",
    "MAX_IMMUTABLE_STRING_BYTES",
    "MAX_PROFILE_SOURCE_PAIRS",
    "MAX_SOURCES_PER_PROFILE",
    "MAX_FG3_HISTORICAL_OBSERVATIONS",
    "COMPLETED_STRUCTURAL_STEPS",
    "CONNECTED_STOP",
    "CONTRACT_VERSION",
    "CURRENT_GATE_STATUS",
    "DeploymentEvidence",
    "EXPECTED_ENVIRONMENT",
    "EXPECTED_OIDC_AUDIENCE",
    "EXPECTED_OIDC_ISSUER",
    "EXPECTED_REPOSITORY",
    "EXPECTED_REF",
    "EXPECTED_WORKFLOW",
    "EXPECTED_WORKFLOW_BLOB_SHA",
    "EXPECTED_WORKFLOW_PATH",
    "EXPECTED_WORKFLOW_SHA",
    "EXCLUDED_DYNAMIC_SOURCE_KINDS",
    "EffectiveProfileRouting",
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
    "G5_ATOMIC_LEDGER_INTERFACE",
    "GO_COMPATIBLE_SOURCE_TERMINALS",
    "G5_TRUST_GATE_STATE_CONSUMED",
    "G5_TRUST_GATE_STATE_READY",
    "G5_TRUST_PLANE_PR_A_STATUS",
    "GateConsumptionReceipt",
    "GateIntent",
    "GitHubOidcClaims",
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
    "REDIRECT_EVIDENCE_POLICY",
    "ReadTiming",
    "RowCursor",
    "SCHEMA_VERSION",
    "STOP_APPROVAL_INVALID",
    "STOP_ATOMIC_LEDGER_REQUIRED",
    "STOP_AUTHORITY_INVALID",
    "STOP_BINDING_DRIFT",
    "STOP_CONSUMPTION_AMBIGUOUS",
    "STOP_GATE_EXPIRED",
    "STOP_PROOF_INVALID",
    "STOP_REPLAY_DETECTED",
    "SOURCE_ATTEMPT_BUDGET_NS",
    "SOURCE_ATTEMPT_GRAMMAR",
    "SOURCE_ERROR_CLASSES",
    "SOURCE_CONFIGURATION_ROLES",
    "SOURCE_REDIRECT_CLASSIFICATIONS",
    "SOURCE_SCOPE",
    "SOURCE_ROLE_FILTER",
    "SOURCE_ROLE_PROBE_TARGET",
    "SOURCE_ROLE_TEMPLATE",
    "SOURCE_TERMINAL_REASONS",
    "STOP_ANCHOR_NOT_INDEPENDENT",
    "STOP_CAPABILITY_INVALID",
    "STOP_CLOCK_TIMING_INVALID",
    "STOP_COUNT_DRIFT",
    "STOP_MANIFEST_ANCHOR_MISMATCH",
    "STOP_PROFILE_ROUTING_INVALID",
    "STOP_SOURCE_BLOCKERS_PRESENT",
    "STOP_LIFECYCLE_BLOCKERS_PRESENT",
    "STOP_PAGINATION_INCOMPLETE",
    "STOP_PROTECTED_SOURCE_INVALID",
    "STOP_SNAPSHOT_CONTENT_DRIFT",
    "STOP_TARGET_BINDING_INVALID",
    "SourceObservationBundle",
    "SourceObservationEvidence",
    "SourceObservationRequest",
    "SourceAttemptResult",
    "StaticSourceTarget",
    "SnapshotPairPayloadEvidence",
    "TABLE_COLUMNS",
    "TRUST_MODEL_FUTURE_REQUIREMENTS",
    "TRUST_STOP",
    "TargetBinding",
    "WorkflowRunEvidence",
    "anchor_provider_receipt_digest",
    "authorize_future_adapter",
    "classify_lifecycle_proxy",
    "derive_effective_profile_routing",
    "evidence_binding_digest",
    "expected_trust_digest",
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
    "reject_caller_supplied_authority",
    "row_fingerprint",
    "snapshot_payload_digest",
    "source_terminal_reason",
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
    "validate_future_trust_plane",
]
