from __future__ import annotations

import ast
import inspect
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.shared.f10_9_g5_get_only_adapter_contract import (
    ALGORITHM_VERSION,
    APPROVED_GATE_STATUS,
    AUTHORIZATION_ORDER,
    CONNECTED_STOP,
    CONTRACT_VERSION,
    CURRENT_GATE_STATUS,
    EXPECTED_ENVIRONMENT,
    EXPECTED_WORKFLOW,
    FG3_HISTORICAL_REQUIREMENT,
    FG3_INACTIVE_ADMISSION,
    FG3_PRIMARY_COHORT,
    FINGERPRINT_DECLARATION,
    FORBIDDEN_METHODS,
    G5AdapterContractError,
    GATE_NAME,
    GET_ONLY_CAPABILITY,
    LIFECYCLE_CLASSIFICATIONS,
    LIFECYCLE_PROXY_ORDER,
    PUBLIC_PROJECTION_FORBIDDEN_FIELDS,
    PROTECTED_SOURCE_SHA,
    PROTECTED_SOURCE_TREE,
    READ_CAPTURE_SEQUENCE,
    READ_CLOCK_SOURCE,
    SCHEMA_VERSION,
    STOP_ANCHOR_NOT_INDEPENDENT,
    STOP_CAPABILITY_INVALID,
    STOP_CLOCK_TIMING_INVALID,
    STOP_COUNT_DRIFT,
    STOP_GATE_NOT_APPROVED,
    STOP_MANIFEST_ANCHOR_MISMATCH,
    STOP_PAGINATION_INCOMPLETE,
    STOP_PAYLOAD_EXPIRED,
    STOP_PROTECTED_SOURCE_INVALID,
    TABLE_COLUMNS,
    TRUSTED_CREDENTIAL_AUTHORITY,
    TRUSTED_GATE_AUTHORITY,
    TRUSTED_HISTORICAL_ANCHOR_AUTHORITY,
    AdapterCapability,
    AuthorizationRequest,
    CredentialAvailabilityAttestation,
    GateAttestation,
    FG3CohortEvidence,
    FG3CourseCohortEvidence,
    FG3HistoricalObservationEvidence,
    HistoricalFG3AnchorAttestation,
    HistoricalFG3ManifestAttestation,
    PageEvidence,
    PaginationEvidence,
    ReadTiming,
    RowCursor,
    SourceObservationEvidence,
    SourceObservationRequest,
    SnapshotPairPayloadEvidence,
    TargetBinding,
    authorize_future_adapter,
    classify_lifecycle_proxy,
    credential_attestation_digest,
    evidence_binding_digest,
    gate_approval_digest,
    historical_anchor_digest,
    historical_manifest_digest,
    inventory_digest,
    lifecycle_allows_pass,
    obtain_independent_historical_anchor,
    page_evidence_digest,
    public_contract_projection,
    row_fingerprint,
    snapshot_payload_digest,
    target_binding_digest,
    validate_capability,
    validate_historical_anchor,
    validate_fg3_cohort,
    validate_pagination,
    validate_read_timing,
    validate_source_observation,
    validate_snapshot_pair_payload,
)
from scripts.shared.f10_9_g5_readonly_collector import (
    CandidateBinding,
    ConnectedAuthorization,
    G5Error,
    PrivateObservations,
    collect_g5_connected,
)


NOW = datetime(2026, 8, 14, 18, 0, tzinfo=timezone.utc)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64
DIGEST_E = "sha256:" + "e" * 64
HISTORICAL_DIGESTS = tuple(f"sha256:{value:064x}" for value in range(1, 28))


def _target(**overrides: object) -> TargetBinding:
    values = {
        "environment": EXPECTED_ENVIRONMENT,
        "protected_source_sha": PROTECTED_SOURCE_SHA,
        "protected_source_tree": PROTECTED_SOURCE_TREE,
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "workflow": EXPECTED_WORKFLOW,
        "run_id": DIGEST_A,
        "issued_at": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(minutes=5),
        "snapshot_pair_id": DIGEST_B,
        "payload_digest": DIGEST_C,
        "manifest_digest": DIGEST_D,
        "anchor_digest": DIGEST_E,
    }
    values.update(overrides)
    return TargetBinding(**values)


def _authorization(**overrides: object) -> AuthorizationRequest:
    payload, payload_target = _snapshot_bundle()
    manifest, anchor, target = _historical_bundle(payload_target)
    cohort = _fg3_evidence(target, payload)
    binding_digest = target_binding_digest(target)
    gate = GateAttestation(
        name=GATE_NAME,
        status=APPROVED_GATE_STATUS,
        authority_identity=TRUSTED_GATE_AUTHORITY,
        target_binding_digest=binding_digest,
        run_id=target.run_id,
        approval_nonce=DIGEST_B,
        issued_at=NOW - timedelta(minutes=4),
        expires_at=NOW + timedelta(minutes=4),
        consumed=False,
        approval_digest="",
    )
    gate = replace(gate, approval_digest=gate_approval_digest(gate))
    credential = CredentialAvailabilityAttestation(
        available=True,
        source="ENVIRONMENT_AVAILABILITY_ATTESTATION",
        authority_identity=TRUSTED_CREDENTIAL_AUTHORITY,
        target_binding_digest=binding_digest,
        run_id=target.run_id,
        issued_at=NOW - timedelta(minutes=3),
        expires_at=NOW + timedelta(minutes=3),
        attestation_digest="",
    )
    credential = replace(
        credential,
        attestation_digest=credential_attestation_digest(credential),
    )
    builder = _ManifestBuilder(manifest)
    provider = _AnchorProvider(anchor)
    values = {
        "gate": gate,
        "execution_sha": PROTECTED_SOURCE_SHA,
        "execution_tree": PROTECTED_SOURCE_TREE,
        "workflow": EXPECTED_WORKFLOW,
        "environment": EXPECTED_ENVIRONMENT,
        "target": target,
        "capability": GET_ONLY_CAPABILITY,
        "payload_digest": target.payload_digest,
        "manifest_digest": target.manifest_digest,
        "anchor_digest": target.anchor_digest,
        "historical_manifest": manifest,
        "historical_anchor": anchor,
        "manifest_builder": builder,
        "anchor_provider": provider,
        "fg3_cohort": cohort,
        "snapshot_payload": payload,
        "evaluated_at": NOW,
        "credential_availability": credential,
    }
    values.update(overrides)
    return AuthorizationRequest(**values)


def _timing(**overrides: object) -> ReadTiming:
    values = {
        "snapshot_pair_id": DIGEST_B,
        "operation": "SELECT_PAGE",
        "clock_source": READ_CLOCK_SOURCE,
        "capture_sequence": READ_CAPTURE_SEQUENCE,
        "started_at_utc": NOW,
        "ended_at_utc": NOW + timedelta(milliseconds=1),
        "monotonic_started_ns": 1_000,
        "monotonic_ended_ns": 2_000,
    }
    values.update(overrides)
    return ReadTiming(**values)


def _course_row(value: str, *, active: bool = True) -> dict[str, object]:
    return {
        "id": value,
        "institution_id": "private-institution",
        "url": "https://private.invalid/course",
        "is_active": active,
        "last_404_at": None,
        "start_date": None,
    }


def _row(value: str, *, target: TargetBinding | None = None, active: bool = True) -> RowCursor:
    target = _target() if target is None else target
    row = _course_row(value, active=active)
    fingerprint = row_fingerprint(
        "courses",
        evidence_binding_digest(target),
        DIGEST_B,
        row,
    )
    return RowCursor(value, value, fingerprint, row)


def _manifest(**overrides: object) -> HistoricalFG3ManifestAttestation:
    observation_categories = tuple(
        (fingerprint, "INCONCLUSIVE" if index < 24 else "FIRST_GET_404" if index < 26 else "DEACTIVATION")
        for index, fingerprint in enumerate(HISTORICAL_DIGESTS)
    )
    values = {
        "manifest_digest": DIGEST_D,
        "builder_identity": "manifest-builder-authority-v1",
        "builder_instance_identity": "manifest-builder-instance-v1",
        "candidate_sha": PROTECTED_SOURCE_SHA,
        "candidate_tree": PROTECTED_SOURCE_TREE,
        "run_id": DIGEST_A,
        "issued_at": NOW - timedelta(minutes=2),
        "complete": True,
        "expected_observation_fingerprints": HISTORICAL_DIGESTS,
        "observation_categories": observation_categories,
        "category_counts": (
            ("INCONCLUSIVE", 24),
            ("FIRST_GET_404", 2),
            ("DEACTIVATION", 1),
        ),
        "published_count_tuple": (24, 2, 1),
    }
    values.update(overrides)
    manifest = HistoricalFG3ManifestAttestation(**values)
    return replace(manifest, manifest_digest=historical_manifest_digest(manifest))


def _anchor(**overrides: object) -> HistoricalFG3AnchorAttestation:
    values = {
        "anchor_digest": DIGEST_E,
        "manifest_digest": _manifest().manifest_digest,
        "provider_identity": "historical-anchor-authority-v1",
        "provider_instance_identity": "historical-anchor-instance-v1",
        "provenance": "INDEPENDENT_HISTORICAL_FG3_SOURCE",
        "candidate_sha": PROTECTED_SOURCE_SHA,
        "candidate_tree": PROTECTED_SOURCE_TREE,
        "run_id": DIGEST_A,
        "authority_identity": TRUSTED_HISTORICAL_ANCHOR_AUTHORITY,
        "issued_at": NOW - timedelta(minutes=1),
    }
    values.update(overrides)
    anchor = HistoricalFG3AnchorAttestation(**values)
    return replace(anchor, anchor_digest=historical_anchor_digest(anchor))


def _historical_bundle(base_target: TargetBinding | None = None):
    manifest = _manifest()
    anchor = _anchor(manifest_digest=manifest.manifest_digest)
    target = (base_target or _target())
    target = replace(
        target,
        manifest_digest=manifest.manifest_digest,
        anchor_digest=anchor.anchor_digest,
    )
    return manifest, anchor, target


def _fg3_evidence(
    target: TargetBinding,
    payload: SnapshotPairPayloadEvidence,
) -> FG3CohortEvidence:
    first_courses = next(item for item in payload.snapshot_1 if item.table == "courses")
    second_courses = next(item for item in payload.snapshot_2 if item.table == "courses")
    first_rows = tuple(dict(row.row) for page in first_courses.pages for row in page.rows)
    second_rows = tuple(dict(row.row) for page in second_courses.pages for row in page.rows)
    course_fingerprints = tuple(
        row_fingerprint(
            "courses", evidence_binding_digest(target), DIGEST_B, row
        )
        for row in first_rows
    )
    active_fingerprints = course_fingerprints[:-1]
    inactive_fingerprint = course_fingerprints[-1]
    return FG3CohortEvidence(
        target_binding_digest=evidence_binding_digest(target),
        snapshot_pair_id=target.snapshot_pair_id,
        run_id=target.run_id,
        snapshot_1_courses=first_rows,
        snapshot_2_courses=second_rows,
        courses=tuple(
            FG3CourseCohortEvidence(
                course_fingerprint=fingerprint,
                active_at_snapshot_1=True,
                attributable_prior_mutation=False,
                exact_one_verified=False,
                antecedent_run_fingerprint=None,
                historical_observation_fingerprint=None,
                historical_category=None,
                related_to_current_run=True,
            )
            for fingerprint in active_fingerprints
        )
        + (
            FG3CourseCohortEvidence(
                course_fingerprint=inactive_fingerprint,
                active_at_snapshot_1=False,
                attributable_prior_mutation=True,
                exact_one_verified=True,
                antecedent_run_fingerprint=DIGEST_B,
                historical_observation_fingerprint=HISTORICAL_DIGESTS[-1],
                historical_category="DEACTIVATION",
                related_to_current_run=True,
            ),
        ),
        additional_historical_observations=tuple(
            FG3HistoricalObservationEvidence(
                observation_fingerprint=fingerprint,
                course_fingerprint=course_fingerprint,
                run_id=target.run_id,
                category=(
                    "INCONCLUSIVE"
                    if index < 24
                    else "FIRST_GET_404"
                ),
                active_at_snapshot_1=True,
            )
            for index, (fingerprint, course_fingerprint) in enumerate(
                zip(HISTORICAL_DIGESTS[:-1], active_fingerprints, strict=True)
            )
        ),
    )


class _ManifestBuilder:
    def __init__(self, manifest: HistoricalFG3ManifestAttestation) -> None:
        self.builder_identity = manifest.builder_identity
        self.builder_instance_identity = manifest.builder_instance_identity


class _AnchorProvider:
    def __init__(self, anchor: HistoricalFG3AnchorAttestation) -> None:
        self.provider_identity = anchor.provider_identity
        self.provider_instance_identity = anchor.provider_instance_identity
        self.provenance = anchor.provenance
        self._anchor = anchor

    def provide_anchor(self, **_kwargs):
        return self._anchor


def _page(
    rows: tuple[RowCursor, ...],
    *,
    target: TargetBinding | None = None,
    table: str = "courses",
    after_id: str | None = None,
    monotonic_start: int = 3_000,
) -> PageEvidence:
    target = _target() if target is None else target
    timing = _timing(
        operation="SELECT_PAGE",
        started_at_utc=NOW + timedelta(microseconds=monotonic_start),
        ended_at_utc=NOW + timedelta(microseconds=monotonic_start + 500),
        monotonic_started_ns=monotonic_start,
        monotonic_ended_ns=monotonic_start + 500,
    )
    page = PageEvidence(after_id, 1000, rows, "", timing)
    return replace(
        page,
        page_digest=page_evidence_digest(
            table, evidence_binding_digest(target), DIGEST_B, page
        ),
    )


def _pagination(
    pages: tuple[PageEvidence, ...],
    *,
    target: TargetBinding | None = None,
    table: str = "courses",
    initial_count: int,
    final_count: int | None = None,
    timing_shift: int = 0,
) -> PaginationEvidence:
    target = _target() if target is None else target
    evidence = PaginationEvidence(
        target_binding_digest=evidence_binding_digest(target),
        snapshot_pair_id=DIGEST_B,
        table=table,
        initial_count=initial_count,
        initial_count_timing=_timing(
            operation="COUNT_INITIAL",
            started_at_utc=NOW + timedelta(microseconds=1_000 + timing_shift),
            ended_at_utc=NOW + timedelta(microseconds=2_000 + timing_shift),
            monotonic_started_ns=1_000 + timing_shift,
            monotonic_ended_ns=2_000 + timing_shift,
        ),
        final_count=initial_count if final_count is None else final_count,
        final_count_timing=_timing(
            operation="COUNT_FINAL",
            started_at_utc=NOW + timedelta(microseconds=10_000 + timing_shift),
            ended_at_utc=NOW + timedelta(microseconds=11_000 + timing_shift),
            monotonic_started_ns=10_000 + timing_shift,
            monotonic_ended_ns=11_000 + timing_shift,
        ),
        pages=pages,
        inventory_digest="",
    )
    return replace(evidence, inventory_digest=inventory_digest(evidence))


def _snapshot_bundle() -> tuple[SnapshotPairPayloadEvidence, TargetBinding]:
    target = _target()
    course_rows = tuple(
        _row(
            f"{index:03d}",
            target=target,
            active=index < 27,
        )
        for index in range(1, 28)
    )
    first_inventories = []
    second_inventories = []
    for table in sorted(TABLE_COLUMNS):
        first_pages = (
            (_page(course_rows, target=target, table=table),)
            if table == "courses"
            else ()
        )
        second_pages = (
            (
                _page(
                    course_rows,
                    target=target,
                    table=table,
                    monotonic_start=23_000,
                ),
            )
            if table == "courses"
            else ()
        )
        first_inventories.append(
            _pagination(
                first_pages,
                target=target,
                table=table,
                initial_count=27 if table == "courses" else 0,
            )
        )
        second_inventories.append(
            _pagination(
                second_pages,
                target=target,
                table=table,
                initial_count=27 if table == "courses" else 0,
                timing_shift=20_000,
            )
        )
    payload = SnapshotPairPayloadEvidence(
        snapshot_pair_id=DIGEST_B,
        snapshot_1=tuple(first_inventories),
        snapshot_2=tuple(second_inventories),
        payload_digest="",
    )
    payload = replace(payload, payload_digest=snapshot_payload_digest(payload))
    return payload, replace(target, payload_digest=payload.payload_digest)


def test_contract_freezes_repository_only_target_and_gate_state() -> None:
    assert PROTECTED_SOURCE_SHA == "bfdeb34c82d3e2fc4545b36f384436ff96ef1cb3"
    assert PROTECTED_SOURCE_TREE == "dabf61ced4012419c4cd9f688506b4fe77e613dd"
    assert CURRENT_GATE_STATUS == "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
    assert CONNECTED_STOP == "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"
    assert AUTHORIZATION_ORDER[-1] == "TRANSPORT_CREATION"


def test_capability_is_exact_select_count_only() -> None:
    validate_capability(GET_ONLY_CAPABILITY)
    assert GET_ONLY_CAPABILITY.methods == ("select", "count")
    assert not (set(GET_ONLY_CAPABILITY.methods) & FORBIDDEN_METHODS)
    assert {query.table for query in GET_ONLY_CAPABILITY.queries} == {
        "institutions",
        "institution_site_profiles",
        "staging_raw",
        "cleansed_programs",
        "enriched_programs",
        "courses",
    }
    assert all(query.filters == () for query in GET_ONLY_CAPABILITY.queries)
    assert all(query.order == ("id.asc",) for query in GET_ONLY_CAPABILITY.queries)
    assert all(query.stable_tie_breaker == "id" for query in GET_ONLY_CAPABILITY.queries)


@pytest.mark.parametrize("method", sorted(FORBIDDEN_METHODS | {"head", "post"}))
def test_capability_rejects_write_or_extra_methods(method: str) -> None:
    capability = replace(
        GET_ONLY_CAPABILITY,
        methods=GET_ONLY_CAPABILITY.methods + (method,),
    )
    with pytest.raises(G5AdapterContractError, match=STOP_CAPABILITY_INVALID):
        validate_capability(capability)


def test_capability_rejects_extra_columns_filters_limits_and_retries() -> None:
    query = GET_ONLY_CAPABILITY.queries[0]
    invalid_queries = (
        replace(query, columns=query.columns + ("secret",)),
        replace(query, filters=(("id", "eq", "private"),)),
        replace(query, timeout_seconds=16),
        replace(query, retry_budget=3),
        replace(query, page_size=1001),
    )
    for invalid in invalid_queries:
        queries = tuple(invalid if item.table == query.table else item for item in GET_ONLY_CAPABILITY.queries)
        with pytest.raises(G5AdapterContractError, match=STOP_CAPABILITY_INVALID):
            validate_capability(replace(GET_ONLY_CAPABILITY, queries=queries))


def test_authorization_completes_offline_and_stops_before_transport() -> None:
    plan = authorize_future_adapter(_authorization())
    assert plan.completed_steps == AUTHORIZATION_ORDER[:-1]
    assert plan.next_step == CONNECTED_STOP
    assert plan.transport_created is False
    assert plan.authorization_complete is False
    assert plan.independent_execution_verification_required is True
    assert plan.target_binding_digest.startswith("sha256:")
    assert set(public_contract_projection(plan)) == {
        "contract_version",
        "decision",
        "reason_code",
        "target_binding_digest",
        "authorization_complete",
        "transport_created",
    }


def test_authorization_rejects_same_manifest_and_anchor_runtime_object() -> None:
    request = _authorization()

    class Dual:
        builder_identity = request.historical_manifest.builder_identity
        builder_instance_identity = request.historical_manifest.builder_instance_identity
        provider_identity = request.historical_anchor.provider_identity
        provider_instance_identity = request.historical_anchor.provider_instance_identity
        provenance = request.historical_anchor.provenance

        def provide_anchor(self, **_kwargs):
            raise AssertionError("self-attested provider must not be called")

    dual = Dual()
    with pytest.raises(G5AdapterContractError, match=STOP_ANCHOR_NOT_INDEPENDENT):
        authorize_future_adapter(
            replace(request, manifest_builder=dual, anchor_provider=dual)
        )


def test_public_projection_rejects_forged_plan() -> None:
    valid = authorize_future_adapter(_authorization())
    with pytest.raises(G5AdapterContractError):
        public_contract_projection(replace(valid, next_step="private-response-body"))
    with pytest.raises(G5AdapterContractError):
        public_contract_projection(replace(valid, authorization_complete=True))


class _ExplodingCredential:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"credential inspected prematurely: {name}")


def test_gate_fails_before_credential_or_environment_inspection() -> None:
    gate = replace(_authorization().gate, status=CURRENT_GATE_STATUS)
    request = _authorization(
        gate=gate,
        credential_availability=_ExplodingCredential(),
    )
    with pytest.raises(G5AdapterContractError, match=STOP_GATE_NOT_APPROVED):
        authorize_future_adapter(request)


@pytest.mark.parametrize(
    "change",
    (
        {"authority_identity": DIGEST_A},
        {"consumed": True},
        {"run_id": DIGEST_B},
        {"approval_nonce": "invalid"},
        {"approval_digest": DIGEST_A},
    ),
)
def test_gate_attestation_rejects_authority_binding_and_consumption_drift(change) -> None:
    gate = replace(_authorization().gate, **change)
    if "approval_digest" not in change:
        gate = replace(gate, approval_digest=gate_approval_digest(gate))
    with pytest.raises(G5AdapterContractError):
        authorize_future_adapter(_authorization(gate=gate))


def test_source_sha_tree_drift_fails_before_credential_inspection() -> None:
    request = _authorization(
        execution_sha="1" * 40,
        credential_availability=_ExplodingCredential(),
    )
    with pytest.raises(G5AdapterContractError, match=STOP_PROTECTED_SOURCE_INVALID):
        authorize_future_adapter(request)

    request = _authorization(
        execution_tree="2" * 40,
        credential_availability=_ExplodingCredential(),
    )
    with pytest.raises(G5AdapterContractError, match=STOP_PROTECTED_SOURCE_INVALID):
        authorize_future_adapter(request)


def test_payload_expiration_fails_before_credential_inspection() -> None:
    request = _authorization(
        evaluated_at=NOW + timedelta(minutes=5),
        credential_availability=_ExplodingCredential(),
    )
    with pytest.raises(G5AdapterContractError, match=STOP_PAYLOAD_EXPIRED):
        authorize_future_adapter(request)


def test_authorization_api_cannot_receive_factory_env_or_secret_values() -> None:
    parameters = set(inspect.signature(authorize_future_adapter).parameters)
    assert parameters == {"request"}
    fields = set(AuthorizationRequest.__dataclass_fields__)
    assert not fields & {
        "factory",
        "transport",
        "environment_reader",
        "credential",
        "secret",
        "secret_value",
    }


@pytest.mark.parametrize(
    "change",
    (
        {"available": False},
        {"secret_values_inspected": True},
        {"source": "PROCESS_ENVIRONMENT"},
        {"authority_identity": DIGEST_A},
        {"target_binding_digest": DIGEST_A},
        {"attestation_digest": DIGEST_A},
    ),
)
def test_credential_attestation_is_bound_and_never_contains_secret_values(change) -> None:
    credential = replace(_authorization().credential_availability, **change)
    if "attestation_digest" not in change:
        credential = replace(
            credential,
            attestation_digest=credential_attestation_digest(credential),
        )
    with pytest.raises(G5AdapterContractError):
        authorize_future_adapter(_authorization(credential_availability=credential))


def test_pagination_accepts_complete_stable_unique_inventory() -> None:
    rows = (_row("001"), _row("002"))
    evidence = _pagination((_page(rows),), initial_count=2)
    assert validate_pagination(evidence, _target()) == tuple(
        row.row_fingerprint for row in rows
    )


def test_pagination_rejects_repeated_page_and_duplicate_rows() -> None:
    first = _page((_row("001"),))
    repeated = replace(
        _page((_row("002"),), after_id="001", monotonic_start=5_000),
        page_digest=first.page_digest,
    )
    evidence = _pagination((first, repeated), initial_count=2)
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_pagination(evidence, _target())

    duplicate = _page((_row("001"),), after_id="001", monotonic_start=5_000)
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_pagination(_pagination((first, duplicate), initial_count=2), _target())


def test_pagination_rejects_truncation_and_count_drift() -> None:
    page = _page((_row("001"),))
    truncated = _pagination((page,), initial_count=2)
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_pagination(truncated, _target())
    with pytest.raises(G5AdapterContractError, match=STOP_COUNT_DRIFT):
        validate_pagination(
            _pagination((page,), initial_count=1, final_count=2), _target()
        )


def test_pagination_rejects_unstable_order_and_tie_breaker_collision() -> None:
    rows = (_row("002"), _row("001"))
    page = _page(rows)
    evidence = _pagination((page,), initial_count=2)
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_pagination(evidence, _target())


def test_pagination_recomputes_row_page_and_inventory_digests() -> None:
    row = _row("001")
    page = _page((row,))
    evidence = _pagination((page,), initial_count=1)
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_pagination(
            replace(evidence, pages=(replace(page, page_digest=DIGEST_A),)),
            _target(),
        )
    forged_row = replace(row, row_fingerprint=DIGEST_A)
    forged_page = _page((forged_row,))
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_pagination(_pagination((forged_page,), initial_count=1), _target())
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_pagination(replace(evidence, inventory_digest=DIGEST_A), _target())


def test_snapshot_payload_binds_all_six_tables_and_double_read() -> None:
    payload, target = _snapshot_bundle()
    validate_snapshot_pair_payload(payload, target)
    with pytest.raises(G5AdapterContractError, match=STOP_MANIFEST_ANCHOR_MISMATCH):
        validate_snapshot_pair_payload(payload, replace(target, payload_digest=DIGEST_A))
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_snapshot_pair_payload(
            replace(payload, snapshot_2=payload.snapshot_2[:-1]), target
        )
    with pytest.raises(G5AdapterContractError, match=STOP_PAGINATION_INCOMPLETE):
        validate_snapshot_pair_payload(payload, target, max_snapshot_bytes=1)
    duplicated_read = replace(payload, snapshot_2=payload.snapshot_1)
    with pytest.raises(G5AdapterContractError, match=STOP_CLOCK_TIMING_INVALID):
        validate_snapshot_pair_payload(duplicated_read, target)


def test_pagination_timing_must_remain_inside_target_window() -> None:
    page = _page((_row("001"),))
    evidence = _pagination((page,), initial_count=1)
    outside = replace(
        evidence.initial_count_timing,
        started_at_utc=_target().expires_at,
        ended_at_utc=_target().expires_at + timedelta(milliseconds=1),
    )
    with pytest.raises(G5AdapterContractError, match=STOP_CLOCK_TIMING_INVALID):
        validate_pagination(replace(evidence, initial_count_timing=outside), _target())


@pytest.mark.parametrize(
    "timing",
    (
        _timing(started_at_utc=NOW.replace(tzinfo=None)),
        _timing(ended_at_utc=NOW),
        _timing(monotonic_ended_ns=1_000),
        _timing(clock_source="WALL_CLOCK_ONLY"),
        _timing(snapshot_pair_id=DIGEST_A),
    ),
)
def test_read_timing_requires_utc_monotonic_pair_boundaries(timing: ReadTiming) -> None:
    with pytest.raises(G5AdapterContractError, match=STOP_CLOCK_TIMING_INVALID):
        validate_read_timing(timing, DIGEST_B)


def test_historical_anchor_requires_independent_provider() -> None:
    manifest, anchor, target = _historical_bundle()
    validate_historical_anchor(manifest, anchor, target)

    self_attested = _anchor(
        provider_identity=manifest.builder_identity,
        provider_instance_identity=manifest.builder_instance_identity,
    )
    with pytest.raises(G5AdapterContractError, match=STOP_ANCHOR_NOT_INDEPENDENT):
        validate_historical_anchor(manifest, self_attested, target)


def test_same_object_cannot_build_manifest_and_provide_anchor() -> None:
    manifest, anchor, target = _historical_bundle()

    class Builder:
        builder_identity = manifest.builder_identity
        builder_instance_identity = manifest.builder_instance_identity

    class Provider:
        provider_identity = "historical-anchor-authority-v1"
        provider_instance_identity = "historical-anchor-instance-v1"
        provenance = "INDEPENDENT_HISTORICAL_FG3_SOURCE"

        def provide_anchor(self, **_kwargs):
            return anchor

    assert obtain_independent_historical_anchor(
        Builder(), Provider(), manifest, target
    ) == anchor

    class Dual:
        builder_identity = manifest.builder_identity
        builder_instance_identity = manifest.builder_instance_identity
        provider_identity = "historical-anchor-authority-v1"
        provider_instance_identity = "historical-anchor-instance-v1"
        provenance = "INDEPENDENT_HISTORICAL_FG3_SOURCE"

        def provide_anchor(self, **_kwargs):
            raise AssertionError("self-attested provider must not be called")

    dual = Dual()
    with pytest.raises(G5AdapterContractError, match=STOP_ANCHOR_NOT_INDEPENDENT):
        obtain_independent_historical_anchor(dual, dual, manifest, target)


def test_historical_anchor_rejects_manifest_candidate_and_run_mismatch() -> None:
    manifest, anchor, target = _historical_bundle()
    mismatches = (
        replace(anchor, manifest_digest=DIGEST_C),
        replace(anchor, candidate_sha="1" * 40),
        replace(anchor, run_id=DIGEST_B),
        replace(anchor, provenance="SELF_ATTESTED"),
    )
    for anchor in mismatches:
        with pytest.raises(G5AdapterContractError, match=STOP_MANIFEST_ANCHOR_MISMATCH):
            validate_historical_anchor(manifest, anchor, target)


def test_historical_manifest_digest_and_inventory_are_recomputed() -> None:
    manifest, anchor, target = _historical_bundle()
    validate_historical_anchor(manifest, anchor, target)
    tampered = replace(
        manifest,
        expected_observation_fingerprints=(DIGEST_C, DIGEST_E),
        observation_categories=(
            (DIGEST_C, "FIRST_GET_404"),
            (DIGEST_E, "FIRST_GET_404"),
        ),
        category_counts=(("FIRST_GET_404", 2),),
    )
    with pytest.raises(G5AdapterContractError, match=STOP_MANIFEST_ANCHOR_MISMATCH):
        validate_historical_anchor(tampered, anchor, target)

    malformed = replace(manifest, category_counts=("malformed",))
    with pytest.raises(G5AdapterContractError, match=STOP_MANIFEST_ANCHOR_MISMATCH):
        validate_historical_anchor(malformed, anchor, target)


def test_fg3_cohort_recomputes_active_and_attributable_inactive_membership() -> None:
    request = _authorization()
    evidence = request.fg3_cohort
    primary, inactive = validate_fg3_cohort(
        evidence,
        request.historical_manifest,
        request.target,
        request.snapshot_payload,
    )
    assert len(primary) == 26
    assert len(inactive) == 1

    unrelated = replace(evidence.courses[-1], related_to_current_run=False)
    with pytest.raises(G5AdapterContractError, match=STOP_MANIFEST_ANCHOR_MISMATCH):
        validate_fg3_cohort(
            replace(evidence, courses=(evidence.courses[0], unrelated)),
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        )
    duplicate_course = replace(
        evidence.additional_historical_observations[1],
        course_fingerprint=evidence.additional_historical_observations[0].course_fingerprint,
    )
    with pytest.raises(G5AdapterContractError, match=STOP_MANIFEST_ANCHOR_MISMATCH):
        validate_fg3_cohort(
            replace(
                evidence,
                additional_historical_observations=(
                    evidence.additional_historical_observations[0],
                    duplicate_course,
                    *evidence.additional_historical_observations[2:],
                ),
            ),
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        )
    overlap = replace(
        evidence.additional_historical_observations[0],
        observation_fingerprint=HISTORICAL_DIGESTS[-1],
        category="DEACTIVATION",
    )
    with pytest.raises(G5AdapterContractError, match=STOP_MANIFEST_ANCHOR_MISMATCH):
        validate_fg3_cohort(
            replace(
                evidence,
                additional_historical_observations=(
                    overlap,
                    *evidence.additional_historical_observations[1:],
                ),
            ),
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        )


def test_source_observation_contract_supports_head_get_without_probe() -> None:
    target = _target()
    request = SourceObservationRequest(
        target_binding_digest=evidence_binding_digest(target),
        snapshot_pair_id=DIGEST_B,
        profile_fingerprint=DIGEST_A,
        source_fingerprint=DIGEST_C,
        run_fingerprint=DIGEST_A,
        cohort_fingerprint=DIGEST_E,
        method_sequence=("HEAD", "GET"),
        max_attempts=2,
    )
    evidence = SourceObservationEvidence(
        target_binding_digest=evidence_binding_digest(target),
        snapshot_pair_id=DIGEST_B,
        profile_fingerprint=DIGEST_A,
        source_fingerprint=DIGEST_C,
        run_fingerprint=DIGEST_A,
        cohort_fingerprint=DIGEST_E,
        method_sequence=("HEAD", "GET"),
        attempts=2,
        terminal_reason="SOURCE_ACCESSIBLE",
        observed_at=NOW,
    )
    validate_source_observation(request, evidence, target)
    with pytest.raises(G5AdapterContractError):
        validate_source_observation(
            replace(request, method_sequence=("POST",)), evidence, target
        )


def test_lifecycle_preserves_proxies_unknown_future_and_blocks_pass() -> None:
    unknown = classify_lifecycle_proxy(
        last_harvested_at=None,
        created_at=None,
        observed_at=NOW,
    )
    future = classify_lifecycle_proxy(
        last_harvested_at=(NOW + timedelta(seconds=1)).isoformat(),
        created_at=None,
        observed_at=NOW,
    )
    current = classify_lifecycle_proxy(
        last_harvested_at=NOW.isoformat(),
        created_at=(NOW - timedelta(days=30)).isoformat(),
        observed_at=NOW,
    )
    assert LIFECYCLE_PROXY_ORDER == ("last_harvested_at", "created_at")
    assert set(LIFECYCLE_CLASSIFICATIONS) == {
        "STALE",
        "NOT_STALE",
        "AGE_UNKNOWN",
        "FUTURE_TIMESTAMP",
    }
    assert unknown.classification == "AGE_UNKNOWN"
    assert future.classification == "FUTURE_TIMESTAMP"
    assert current.timestamp_origin == "LAST_HARVESTED_AT_PROXY"
    assert not lifecycle_allows_pass((unknown,))
    assert not lifecycle_allows_pass((future,))
    assert lifecycle_allows_pass((current,))


def test_lifecycle_rejects_forged_pass_and_subsecond_future_timestamp() -> None:
    future = classify_lifecycle_proxy(
        last_harvested_at=(NOW + timedelta(microseconds=1)).isoformat(),
        created_at=None,
        observed_at=NOW,
    )
    assert future.classification == "FUTURE_TIMESTAMP"
    forged = replace(
        classify_lifecycle_proxy(
            last_harvested_at=None,
            created_at=None,
            observed_at=NOW,
        ),
        classification="NOT_STALE",
    )
    assert not lifecycle_allows_pass((forged,))
    boundary = classify_lifecycle_proxy(
        last_harvested_at=None,
        created_at=(NOW - timedelta(days=7)).isoformat(),
        observed_at=NOW,
    )
    assert boundary.classification == "NOT_STALE"
    assert boundary.timestamp_origin == "CREATED_AT_PROXY"


def test_fg3_cohort_and_privacy_contract_remain_exact() -> None:
    assert FG3_PRIMARY_COHORT == "ACTIVE_AT_SNAPSHOT_1"
    assert FG3_INACTIVE_ADMISSION == "ATTRIBUTABLE_PRIOR_MUTATION_ONLY"
    assert FG3_HISTORICAL_REQUIREMENT.endswith("24_2_1")
    assert FINGERPRINT_DECLARATION == "INTEGRITY_NOT_ANONYMIZATION"
    assert {
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
    } == PUBLIC_PROJECTION_FORBIDDEN_FIELDS


class _Hostile:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"connected argument inspected: {name}")


def test_connected_mode_remains_unconditional_before_factory_inspection() -> None:
    with pytest.raises(G5Error, match=CONNECTED_STOP):
        collect_g5_connected(
            _Hostile(),  # type: ignore[arg-type]
            facade_factory=_Hostile(),
            observations=_Hostile(),  # type: ignore[arg-type]
            binding=_Hostile(),  # type: ignore[arg-type]
        )


def test_contract_has_no_connected_imports_or_environment_secret_access() -> None:
    path = Path("scripts/shared/f10_9_g5_get_only_adapter_contract.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_modules = {
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "db_client",
        "psycopg",
        "sqlalchemy",
        "boto3",
    }
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not (imports & forbidden_modules)
    assert imports <= {
        "__future__",
        "hashlib",
        "json",
        "re",
        "dataclasses",
        "datetime",
        "types",
        "typing",
    }
    forbidden_calls = {
        "getenv",
        "environ",
        "open",
        "urlopen",
        "connect",
        "create_client",
        "Popen",
        "run",
        "check_call",
        "check_output",
        "eval",
        "exec",
        "__import__",
        "import_module",
    }
    calls = {
        node.func.attr
        if isinstance(node.func, ast.Attribute)
        else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert not (calls & forbidden_calls)
    referenced = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    assert not referenced & {
        "__import__",
        "import_module",
        "getattr",
        "globals",
        "locals",
        "open",
        "compile",
        "eval",
        "exec",
    }
    lowered = source.lower()
    assert "insert(" not in lowered
    assert "update(" not in lowered
    assert "upsert(" not in lowered
    assert "patch(" not in lowered
    assert "delete(" not in lowered
    assert "rpc(" not in lowered


def test_collector_connected_body_is_still_only_del_then_stop() -> None:
    source = Path("scripts/shared/f10_9_g5_readonly_collector.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "collect_g5_connected"
    )
    executable = [
        node
        for node in function.body
        if not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
    ]
    assert len(executable) == 2
    assert isinstance(executable[0], ast.Delete)
    assert isinstance(executable[1], ast.Raise)
    assert CONNECTED_STOP in ast.unparse(executable[1])
