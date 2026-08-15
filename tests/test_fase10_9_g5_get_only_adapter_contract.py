from __future__ import annotations

import ast
import inspect
import json
from itertools import product
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path

import pytest

import scripts.shared.f10_9_g5_get_only_adapter_contract as contract
from scripts.shared.f10_9_g5_get_only_adapter_contract import (
    ALGORITHM_VERSION,
    AUTHORIZATION_ORDER,
    CLOCK_DURATION_TOLERANCE_NS,
    COMPLETED_STRUCTURAL_STEPS,
    CONNECTED_STOP,
    CONTRACT_VERSION,
    CURRENT_GATE_STATUS,
    EXPECTED_ENVIRONMENT,
    EXPECTED_WORKFLOW,
    FG3CohortEvidence,
    FG3CourseCohortEvidence,
    FG3HistoricalObservationEvidence,
    FG3PriorMutationEvidence,
    FINGERPRINT_DECLARATION,
    FORBIDDEN_METHODS,
    FrozenRow,
    G5AdapterContractError,
    GET_ONLY_CAPABILITY,
    HISTORICAL_CONTRACT_VERSION,
    HISTORICAL_V2_STATUS,
    HistoricalFG3Anchor,
    HistoricalFG3Manifest,
    LifecycleEvidence,
    LifecycleProxy,
    MAX_IMMUTABLE_DEPTH,
    MAX_IMMUTABLE_INTEGER_ABS,
    MAX_IMMUTABLE_NODES,
    MAX_IMMUTABLE_STRING_BYTES,
    MAX_SOURCES_PER_PROFILE,
    ManifestBuilderEvidenceReceipt,
    AnchorProviderEvidenceReceipt,
    PageEvidence,
    PaginationEvidence,
    PROTECTED_SOURCE_SHA,
    PROTECTED_SOURCE_TREE,
    PUBLIC_PROJECTION_FORBIDDEN_FIELDS,
    READ_CAPTURE_SEQUENCE,
    READ_CLOCK_SOURCE,
    ReadTiming,
    RowCursor,
    SCHEMA_VERSION,
    SOURCE_ATTEMPT_BUDGET_NS,
    SOURCE_ATTEMPT_GRAMMAR,
    STOP_ANCHOR_NOT_INDEPENDENT,
    STOP_CAPABILITY_INVALID,
    STOP_CLOCK_TIMING_INVALID,
    STOP_COUNT_DRIFT,
    STOP_MANIFEST_ANCHOR_MISMATCH,
    STOP_PAGINATION_INCOMPLETE,
    STOP_PROTECTED_SOURCE_INVALID,
    STOP_SNAPSHOT_CONTENT_DRIFT,
    STOP_TARGET_BINDING_INVALID,
    SourceObservationBundle,
    SourceObservationEvidence,
    SourceObservationRequest,
    SourceAttemptTiming,
    SnapshotPairPayloadEvidence,
    TABLE_COLUMNS,
    TRUST_MODEL_FUTURE_REQUIREMENTS,
    TRUST_STOP,
    TargetBinding,
    AuthorizationRequest,
    AuthorizedAdapterPlan,
    anchor_provider_receipt_digest,
    authorize_future_adapter,
    classify_lifecycle_proxy,
    evidence_binding_digest,
    historical_anchor_digest,
    historical_manifest_digest,
    historical_observation_fingerprint,
    inventory_digest,
    lifecycle_allows_pass,
    manifest_builder_receipt_digest,
    page_evidence_digest,
    prior_mutation_fingerprint,
    profile_source_fingerprints,
    public_contract_projection,
    row_fingerprint,
    snapshot_payload_digest,
    target_binding_digest,
    validate_capability,
    validate_fg3_cohort,
    validate_historical_anchor,
    validate_lifecycle_evidence,
    validate_pagination,
    validate_read_timing,
    validate_snapshot_pair_payload,
    validate_source_coverage,
    validate_source_observation,
)
from scripts.shared.f10_9_g5_readonly_collector import G5Error, collect_g5_connected


NOW = datetime(2026, 8, 14, 18, 0, tzinfo=timezone.utc)
DIGESTS = tuple(f"sha256:{index:064x}" for index in range(1, 100))
RUN_ID, PAIR_ID = DIGESTS[:2]


def _reason(call, reason: str) -> None:
    with pytest.raises(G5AdapterContractError) as error:
        call()
    assert str(error.value) == reason


def _target(**overrides: object) -> TargetBinding:
    values = {
        "environment": EXPECTED_ENVIRONMENT,
        "protected_source_sha": PROTECTED_SOURCE_SHA,
        "protected_source_tree": PROTECTED_SOURCE_TREE,
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "workflow": EXPECTED_WORKFLOW,
        "run_id": RUN_ID,
        "issued_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(minutes=1),
        "snapshot_pair_id": PAIR_ID,
        "payload_digest": DIGESTS[2],
        "manifest_digest": DIGESTS[3],
        "anchor_digest": DIGESTS[4],
    }
    values.update(overrides)
    return TargetBinding(**values)


def _timing(operation: str, start_us: int, **overrides: object) -> ReadTiming:
    values = {
        "snapshot_pair_id": PAIR_ID,
        "operation": operation,
        "clock_source": READ_CLOCK_SOURCE,
        "capture_sequence": READ_CAPTURE_SEQUENCE,
        "started_at_utc": NOW + timedelta(microseconds=start_us),
        "ended_at_utc": NOW + timedelta(microseconds=start_us + 100),
        "monotonic_started_ns": start_us * 1000,
        "monotonic_ended_ns": (start_us + 100) * 1000,
    }
    values.update(overrides)
    return ReadTiming(**values)


def _frozen_row(table: str, **overrides: object) -> FrozenRow:
    values: dict[str, object] = {column: None for column in TABLE_COLUMNS[table]}
    values.update(overrides)
    return FrozenRow(tuple((column, values[column]) for column in TABLE_COLUMNS[table]))


def _rows(
    table: str,
    *,
    changed: bool = False,
    course_active_overrides: dict[int, object] | None = None,
    profile_rows: tuple[FrozenRow, ...] | None = None,
) -> tuple[FrozenRow, ...]:
    if table == "institution_site_profiles":
        if profile_rows is not None:
            return profile_rows
        return (
            _frozen_row(
                table,
                id="profile-001",
                institution_id="institution-001",
                discovery_enabled=True,
                pipeline_enabled=True,
                pipeline_ready=True,
                discovery_mode="sitemap",
                seed_urls=("opaque-seed",),
                catalog_url_patterns=(),
                allowed_url_patterns=(),
                circuit_open=False,
            ),
        )
    if table == "staging_raw":
        return (
            _frozen_row(
                table,
                id="staging-001",
                institution_id="institution-001",
                url="https://private.invalid/staging",
                status="processing",
                content_hash="opaque-content",
                last_harvested_at=(NOW - timedelta(days=1)).isoformat(),
                created_at=(NOW - timedelta(days=10)).isoformat(),
            ),
        )
    if table == "courses":
        return tuple(
            _frozen_row(
                table,
                id=f"course-{index:03d}",
                institution_id="institution-001",
                url=(
                    "https://private.invalid/changed"
                    if changed and index == 2
                    else f"https://private.invalid/course-{index}"
                ),
                is_active=(course_active_overrides or {}).get(index, index < 3),
            )
            for index in range(1, 4)
        )
    return ()


def _page(
    table: str,
    rows: tuple[FrozenRow, ...],
    target: TargetBinding,
    start_us: int,
) -> PageEvidence:
    target_digest = evidence_binding_digest(target)
    cursors = tuple(
        RowCursor(
            order_value=str(dict(row.values)["id"]),
            tie_breaker=str(dict(row.values)["id"]),
            row_fingerprint=row_fingerprint(table, target_digest, PAIR_ID, row),
            row=row,
        )
        for row in rows
    )
    page = PageEvidence(
        after_id=None,
        requested_limit=1000,
        rows=cursors,
        page_digest="",
        timing=_timing("SELECT_PAGE", start_us),
    )
    return replace(
        page,
        page_digest=page_evidence_digest(table, target_digest, PAIR_ID, page),
    )


def _pagination(
    table: str,
    rows: tuple[FrozenRow, ...],
    target: TargetBinding,
    shift: int,
) -> PaginationEvidence:
    pages = (_page(table, rows, target, shift + 300),) if rows else ()
    evidence = PaginationEvidence(
        target_binding_digest=evidence_binding_digest(target),
        snapshot_pair_id=PAIR_ID,
        table=table,
        initial_count=len(rows),
        initial_count_timing=_timing("COUNT_INITIAL", shift + 100),
        final_count=len(rows),
        final_count_timing=_timing("COUNT_FINAL", shift + 700),
        pages=pages,
        inventory_digest="",
    )
    return replace(evidence, inventory_digest=inventory_digest(evidence))


def _snapshot_bundle(
    *,
    changed_second: bool = False,
    course_active_overrides: dict[int, object] | None = None,
    first_course_active_overrides: dict[int, object] | None = None,
    second_course_active_overrides: dict[int, object] | None = None,
    profile_rows: tuple[FrozenRow, ...] | None = None,
):
    target = _target()
    first = tuple(
        _pagination(
            table,
            _rows(
                table,
                course_active_overrides=(
                    first_course_active_overrides or course_active_overrides
                ),
                profile_rows=profile_rows,
            ),
            target,
            0,
        )
        for table in sorted(TABLE_COLUMNS)
    )
    second = tuple(
        _pagination(
            table,
            _rows(
                table,
                changed=changed_second and table == "courses",
                course_active_overrides=(
                    second_course_active_overrides or course_active_overrides
                ),
                profile_rows=profile_rows,
            ),
            target,
            2_000,
        )
        for table in sorted(TABLE_COLUMNS)
    )
    payload = SnapshotPairPayloadEvidence(PAIR_ID, first, second, "")
    payload = replace(payload, payload_digest=snapshot_payload_digest(payload))
    return payload, replace(target, payload_digest=payload.payload_digest)


def _shift_second_snapshot(
    payload: SnapshotPairPayloadEvidence,
    target: TargetBinding,
    delta: timedelta,
) -> tuple[SnapshotPairPayloadEvidence, TargetBinding]:
    delta_ns = (
        delta.days * 86_400_000_000_000
        + delta.seconds * 1_000_000_000
        + delta.microseconds * 1_000
    )

    def shifted(timing: ReadTiming) -> ReadTiming:
        return replace(
            timing,
            started_at_utc=timing.started_at_utc + delta,
            ended_at_utc=timing.ended_at_utc + delta,
            monotonic_started_ns=timing.monotonic_started_ns + delta_ns,
            monotonic_ended_ns=timing.monotonic_ended_ns + delta_ns,
        )

    inventories: list[PaginationEvidence] = []
    for item in payload.snapshot_2:
        pages: list[PageEvidence] = []
        for page in item.pages:
            updated_page = replace(page, timing=shifted(page.timing), page_digest="")
            updated_page = replace(
                updated_page,
                page_digest=page_evidence_digest(
                    item.table,
                    item.target_binding_digest,
                    item.snapshot_pair_id,
                    updated_page,
                ),
            )
            pages.append(updated_page)
        updated = replace(
            item,
            initial_count_timing=shifted(item.initial_count_timing),
            final_count_timing=shifted(item.final_count_timing),
            pages=tuple(pages),
            inventory_digest="",
        )
        inventories.append(replace(updated, inventory_digest=inventory_digest(updated)))
    updated_payload = replace(
        payload,
        snapshot_2=tuple(inventories),
        payload_digest="",
    )
    updated_payload = replace(
        updated_payload,
        payload_digest=snapshot_payload_digest(updated_payload),
    )
    return updated_payload, replace(target, payload_digest=updated_payload.payload_digest)


def _inventory(payload: SnapshotPairPayloadEvidence, table: str, snapshot: int = 1):
    items = payload.snapshot_1 if snapshot == 1 else payload.snapshot_2
    return next(item for item in items if item.table == table)


def _course_fingerprints(target: TargetBinding, payload: SnapshotPairPayloadEvidence):
    target_digest = evidence_binding_digest(target)
    return tuple(
        cursor.row_fingerprint
        for page in _inventory(payload, "courses").pages
        for cursor in page.rows
    ), target_digest


def _historical_bundle(target: TargetBinding, payload: SnapshotPairPayloadEvidence):
    course_fingerprints, target_digest = _course_fingerprints(target, payload)
    observations: list[FG3HistoricalObservationEvidence] = []
    for index in range(27):
        category = (
            "INCONCLUSIVE" if index < 24 else "FIRST_GET_404" if index < 26 else "DEACTIVATION"
        )
        course = course_fingerprints[index % 2] if index < 26 else course_fingerprints[2]
        observation = FG3HistoricalObservationEvidence(
            observation_fingerprint="",
            target_binding_digest=target_digest,
            snapshot_pair_id=PAIR_ID,
            course_fingerprint=course,
            run_id=DIGESTS[5] if category == "DEACTIVATION" else RUN_ID,
            category=category,
            active_at_snapshot_1=index < 26,
            observed_at=NOW - timedelta(seconds=50) + timedelta(microseconds=index),
        )
        observations.append(
            replace(
                observation,
                observation_fingerprint=historical_observation_fingerprint(observation),
            )
        )
    categories = tuple((item.observation_fingerprint, item.category) for item in observations)
    manifest = HistoricalFG3Manifest(
        manifest_digest="",
        builder_identity="manifest-builder-v2",
        builder_instance_identity="manifest-builder-instance-v2",
        candidate_sha=PROTECTED_SOURCE_SHA,
        candidate_tree=PROTECTED_SOURCE_TREE,
        run_id=RUN_ID,
        issued_at=NOW - timedelta(seconds=40),
        complete=True,
        expected_observation_fingerprints=tuple(item.observation_fingerprint for item in observations),
        observation_categories=categories,
        category_counts=(("INCONCLUSIVE", 24), ("FIRST_GET_404", 2), ("DEACTIVATION", 1)),
        published_count_tuple=(24, 2, 1),
    )
    manifest = replace(manifest, manifest_digest=historical_manifest_digest(manifest))
    anchor = HistoricalFG3Anchor(
        anchor_digest="",
        manifest_digest=manifest.manifest_digest,
        provider_identity="historical-provider-v2",
        provider_instance_identity="historical-provider-instance-v2",
        provenance="INDEPENDENT_HISTORICAL_FG3_SOURCE",
        candidate_sha=PROTECTED_SOURCE_SHA,
        candidate_tree=PROTECTED_SOURCE_TREE,
        run_id=RUN_ID,
        issued_at=NOW - timedelta(seconds=30),
    )
    anchor = replace(anchor, anchor_digest=historical_anchor_digest(anchor))
    target = replace(
        target,
        manifest_digest=manifest.manifest_digest,
        anchor_digest=anchor.anchor_digest,
    )
    builder = ManifestBuilderEvidenceReceipt(
        manifest.builder_identity,
        manifest.builder_instance_identity,
        manifest.manifest_digest,
        "",
    )
    builder = replace(builder, evidence_digest=manifest_builder_receipt_digest(builder))
    provider = AnchorProviderEvidenceReceipt(
        anchor.provider_identity,
        anchor.provider_instance_identity,
        manifest.manifest_digest,
        anchor.anchor_digest,
        "",
    )
    provider = replace(provider, evidence_digest=anchor_provider_receipt_digest(provider))
    return manifest, anchor, builder, provider, tuple(observations), target


def _cohort(
    target: TargetBinding,
    payload: SnapshotPairPayloadEvidence,
    observations: tuple[FG3HistoricalObservationEvidence, ...],
) -> FG3CohortEvidence:
    course_fingerprints, target_digest = _course_fingerprints(target, payload)
    antecedent_at = observations[-1].observed_at
    mutation = prior_mutation_fingerprint(
        course_fingerprints[2],
        DIGESTS[5],
        antecedent_at,
        "DEACTIVATION",
        observations[-1].observation_fingerprint,
    )
    return FG3CohortEvidence(
        target_binding_digest=target_digest,
        snapshot_pair_id=PAIR_ID,
        run_id=RUN_ID,
        courses=tuple(
            FG3CourseCohortEvidence(
                fingerprint,
                True,
                True,
            )
            for fingerprint in course_fingerprints[:2]
        )
        + (
            FG3CourseCohortEvidence(
                course_fingerprints[2],
                False,
                True,
            ),
        ),
        prior_mutations=(
            FG3PriorMutationEvidence(
                course_fingerprints[2],
                DIGESTS[5],
                antecedent_at,
                "DEACTIVATION",
                mutation,
                observations[-1].observation_fingerprint,
            ),
        ),
        historical_observations=observations,
    )


def _source_bundle(
    target: TargetBinding,
    payload: SnapshotPairPayloadEvidence,
    *,
    profile_index: int = 0,
    source_fingerprint: str | None = None,
    **overrides,
):
    profile = _inventory(payload, "institution_site_profiles").pages[0].rows[
        profile_index
    ]
    if source_fingerprint is None:
        source_fingerprint = sorted(
            profile_source_fingerprints(profile.row_fingerprint, profile.row)
        )[0]
    request = SourceObservationRequest(
        evidence_binding_digest(target),
        PAIR_ID,
        profile.row_fingerprint,
        source_fingerprint,
        RUN_ID,
        DIGESTS[7],
        ("HEAD", "GET"),
        2,
    )
    timings = (
        SourceAttemptTiming(
            "HEAD",
            NOW + timedelta(microseconds=1_000),
            NOW + timedelta(microseconds=1_100),
            1_000_000,
            1_100_000,
        ),
        SourceAttemptTiming(
            "GET",
            NOW + timedelta(microseconds=1_200),
            NOW + timedelta(microseconds=1_300),
            1_200_000,
            1_300_000,
        ),
    )
    evidence = SourceObservationEvidence(
        target_binding_digest=evidence_binding_digest(target),
        snapshot_pair_id=PAIR_ID,
        profile_fingerprint=profile.row_fingerprint,
        source_fingerprint=source_fingerprint,
        run_fingerprint=RUN_ID,
        cohort_fingerprint=DIGESTS[7],
        method_sequence=("HEAD", "GET"),
        attempt_timings=timings,
        attempts=2,
        terminal_reason="SOURCE_ACCESSIBLE",
        observed_at=timings[-1].ended_at_utc,
    )
    for name, value in overrides.items():
        if name.startswith("request_"):
            request = replace(request, **{name.removeprefix("request_"): value})
        else:
            evidence = replace(evidence, **{name: value})
    return SourceObservationBundle(request, evidence)


def _source_bundles(
    target: TargetBinding, payload: SnapshotPairPayloadEvidence
) -> tuple[SourceObservationBundle, ...]:
    profiles = _inventory(payload, "institution_site_profiles").pages[0].rows
    bundles: list[SourceObservationBundle] = []
    for index, profile in enumerate(profiles):
        values = dict(profile.row.values)
        pipeline_gate = (
            values["pipeline_ready"]
            if values["pipeline_enabled"] is None
            else values["pipeline_enabled"]
        )
        if values["discovery_enabled"] is True and pipeline_gate is True and values["circuit_open"] is False:
            bundles.extend(
                _source_bundle(
                    target,
                    payload,
                    profile_index=index,
                    source_fingerprint=fingerprint,
                )
                for fingerprint in sorted(
                    profile_source_fingerprints(profile.row_fingerprint, profile.row)
                )
            )
    return tuple(bundles)


def _lifecycle(target: TargetBinding, payload: SnapshotPairPayloadEvidence, evaluated_at: datetime):
    cursor = _inventory(payload, "staging_raw").pages[0].rows[0]
    values = dict(cursor.row.values)
    proxy = classify_lifecycle_proxy(
        last_harvested_at=values["last_harvested_at"],
        created_at=values["created_at"],
        observed_at=evaluated_at,
    )
    return (LifecycleEvidence(cursor.row_fingerprint, proxy),)


def _authorization(
    *,
    course_active_overrides: dict[int, object] | None = None,
    first_course_active_overrides: dict[int, object] | None = None,
    second_course_active_overrides: dict[int, object] | None = None,
    profile_rows: tuple[FrozenRow, ...] | None = None,
    **overrides: object,
) -> AuthorizationRequest:
    payload, target = _snapshot_bundle(
        course_active_overrides=course_active_overrides,
        first_course_active_overrides=first_course_active_overrides,
        second_course_active_overrides=second_course_active_overrides,
        profile_rows=profile_rows,
    )
    manifest, anchor, builder, provider, observations, target = _historical_bundle(
        target, payload
    )
    evaluated_at = NOW + timedelta(microseconds=3_000)
    values = {
        "execution_sha": PROTECTED_SOURCE_SHA,
        "execution_tree": PROTECTED_SOURCE_TREE,
        "workflow": EXPECTED_WORKFLOW,
        "environment": EXPECTED_ENVIRONMENT,
        "target": target,
        "capability": GET_ONLY_CAPABILITY,
        "historical_manifest": manifest,
        "historical_anchor": anchor,
        "manifest_builder_receipt": builder,
        "anchor_provider_receipt": provider,
        "fg3_cohort": _cohort(target, payload, observations),
        "snapshot_payload": payload,
        "source_observations": _source_bundles(target, payload),
        "lifecycle_evidence": _lifecycle(target, payload, evaluated_at),
        "evaluated_at": evaluated_at,
    }
    values.update(overrides)
    return AuthorizationRequest(**values)


def _with_source_timings(
    request: AuthorizationRequest,
    timings: tuple[SourceAttemptTiming, ...],
    *,
    observed_at: datetime | None = None,
) -> AuthorizationRequest:
    bundle = request.source_observations[0]
    evidence = replace(
        bundle.evidence,
        attempt_timings=timings,
        observed_at=timings[-1].ended_at_utc if observed_at is None else observed_at,
    )
    return replace(
        request,
        source_observations=(
            replace(bundle, evidence=evidence),
            *request.source_observations[1:],
        ),
    )


def _with_historical_times(
    request: AuthorizationRequest,
    *,
    manifest_issued_at: datetime,
    anchor_issued_at: datetime,
) -> AuthorizationRequest:
    manifest = replace(
        request.historical_manifest,
        issued_at=manifest_issued_at,
        manifest_digest="",
    )
    manifest = replace(manifest, manifest_digest=historical_manifest_digest(manifest))
    anchor = replace(
        request.historical_anchor,
        issued_at=anchor_issued_at,
        manifest_digest=manifest.manifest_digest,
        anchor_digest="",
    )
    anchor = replace(anchor, anchor_digest=historical_anchor_digest(anchor))
    builder = replace(
        request.manifest_builder_receipt,
        manifest_digest=manifest.manifest_digest,
        evidence_digest="",
    )
    builder = replace(builder, evidence_digest=manifest_builder_receipt_digest(builder))
    provider = replace(
        request.anchor_provider_receipt,
        manifest_digest=manifest.manifest_digest,
        anchor_digest=anchor.anchor_digest,
        evidence_digest="",
    )
    provider = replace(provider, evidence_digest=anchor_provider_receipt_digest(provider))
    target = replace(
        request.target,
        manifest_digest=manifest.manifest_digest,
        anchor_digest=anchor.anchor_digest,
    )
    return replace(
        request,
        target=target,
        historical_manifest=manifest,
        historical_anchor=anchor,
        manifest_builder_receipt=builder,
        anchor_provider_receipt=provider,
    )


def test_v2_2_freezes_v2_1_and_valid_request_stops_at_trust() -> None:
    assert (CONTRACT_VERSION, SCHEMA_VERSION, ALGORITHM_VERSION) == (
        "f10.9-g5-get-only-adapter-contract.v2.2",
        "f10.9-g5-get-only-adapter-schema.v2.2",
        "f10.9-g5-get-only-adapter-v2.2",
    )
    assert HISTORICAL_CONTRACT_VERSION.endswith(".v2.1")
    assert HISTORICAL_V2_STATUS == "HISTORICAL_ANTECENT_NOT_FIT_FOR_CONNECTED_MODE".replace(
        "ANTECENT", "ANTECEDENT"
    )
    assert PROTECTED_SOURCE_SHA == "c998b0293b364b1c59d9c52824178927977f0b56"
    assert PROTECTED_SOURCE_TREE == "d93843d4e08dfd9c45571b72040994926dffc221"
    assert CURRENT_GATE_STATUS == "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
    plan = authorize_future_adapter(_authorization())
    assert plan.completed_steps == COMPLETED_STRUCTURAL_STEPS == AUTHORIZATION_ORDER[:-1]
    assert plan.next_step == plan.reason == TRUST_STOP
    assert plan.authorization_complete is plan.transport_created is False
    assert plan.trust_verification_implemented is False
    assert len(TRUST_MODEL_FUTURE_REQUIREMENTS) == 5


def test_historical_causality_accepts_inclusive_edges_before_snapshot_1() -> None:
    request = _authorization()
    latest_observation = max(
        item.observed_at for item in request.fg3_cohort.historical_observations
    )
    equal_observation_manifest = _with_historical_times(
        request,
        manifest_issued_at=latest_observation,
        anchor_issued_at=NOW - timedelta(seconds=20),
    )
    assert authorize_future_adapter(equal_observation_manifest).reason == TRUST_STOP
    equal_manifest_anchor = _with_historical_times(
        request,
        manifest_issued_at=NOW - timedelta(seconds=20),
        anchor_issued_at=NOW - timedelta(seconds=20),
    )
    assert authorize_future_adapter(equal_manifest_anchor).reason == TRUST_STOP


@pytest.mark.parametrize(
    "manifest_at,anchor_at",
    (
        (NOW - timedelta(seconds=51), NOW - timedelta(seconds=20)),
        (NOW - timedelta(seconds=20), NOW - timedelta(seconds=21)),
        (NOW - timedelta(seconds=20), NOW + timedelta(microseconds=100)),
    ),
)
def test_historical_causality_rejects_future_knowledge(
    manifest_at: datetime,
    anchor_at: datetime,
) -> None:
    request = _with_historical_times(
        _authorization(),
        manifest_issued_at=manifest_at,
        anchor_issued_at=anchor_at,
    )
    _reason(lambda: authorize_future_adapter(request), STOP_CLOCK_TIMING_INVALID)


@pytest.mark.parametrize(
    "pipeline_enabled,pipeline_ready,expected",
    (
        (True, False, TRUST_STOP),
        (False, True, TRUST_STOP),
        (None, True, TRUST_STOP),
        (None, False, TRUST_STOP),
        (0, True, STOP_TARGET_BINDING_INVALID),
        (1, True, STOP_TARGET_BINDING_INVALID),
        (True, 0, STOP_TARGET_BINDING_INVALID),
        (True, 1, STOP_TARGET_BINDING_INVALID),
        (True, None, STOP_TARGET_BINDING_INVALID),
        (None, None, STOP_TARGET_BINDING_INVALID),
        ("true", True, STOP_TARGET_BINDING_INVALID),
    ),
)
def test_pipeline_enabled_primary_gate_and_pipeline_ready_fallback(
    pipeline_enabled: object,
    pipeline_ready: object,
    expected: str,
) -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-gate",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=pipeline_enabled,
        pipeline_ready=pipeline_ready,
        discovery_mode="sitemap",
        seed_urls=("private-seed",),
        catalog_url_patterns=(),
        allowed_url_patterns=(),
        circuit_open=False,
    )
    request = _authorization(profile_rows=(profile,))
    if expected == TRUST_STOP:
        assert authorize_future_adapter(request).reason == TRUST_STOP
    else:
        _reason(lambda: authorize_future_adapter(request), expected)


def test_multiple_profiles_and_multiple_configured_sources_are_exactly_covered() -> None:
    profiles = (
        _frozen_row(
            "institution_site_profiles",
            id="profile-001",
            institution_id="institution-001",
            discovery_enabled=True,
            pipeline_enabled=True,
            pipeline_ready=False,
            discovery_mode="sitemap",
            seed_urls=("private-seed-a", "private-seed-b"),
            catalog_url_patterns=("private-catalog-a",),
            allowed_url_patterns=("private-allowed-a",),
            circuit_open=False,
        ),
        _frozen_row(
            "institution_site_profiles",
            id="profile-002",
            institution_id="institution-002",
            discovery_enabled=True,
            pipeline_enabled=None,
            pipeline_ready=True,
            discovery_mode="hardcoded_urls",
            seed_urls=("private-seed-c",),
            catalog_url_patterns=(),
            allowed_url_patterns=("private-allowed-b",),
            circuit_open=False,
        ),
    )
    request = _authorization(profile_rows=profiles)
    assert len(request.source_observations) == 6
    assert authorize_future_adapter(request).reason == TRUST_STOP
    _reason(
        lambda: authorize_future_adapter(
            replace(request, source_observations=request.source_observations[:-1])
        ),
        STOP_TARGET_BINDING_INVALID,
    )
    extra = request.source_observations[0]
    arbitrary = replace(
        extra,
        request=replace(extra.request, source_fingerprint=DIGESTS[90]),
        evidence=replace(extra.evidence, source_fingerprint=DIGESTS[90]),
    )
    _reason(
        lambda: authorize_future_adapter(
            replace(request, source_observations=(*request.source_observations, arbitrary))
        ),
        STOP_TARGET_BINDING_INVALID,
    )


@pytest.mark.parametrize("sequence", SOURCE_ATTEMPT_GRAMMAR)
def test_every_accepted_head_get_sequence_reaches_trust_stop(
    sequence: tuple[str, ...],
) -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    timings = tuple(
        SourceAttemptTiming(
            method,
            NOW + timedelta(microseconds=1_000 + index * 200),
            NOW + timedelta(microseconds=1_100 + index * 200),
            1_000_000 + index * 200_000,
            1_100_000 + index * 200_000,
        )
        for index, method in enumerate(sequence)
    )
    updated = replace(
        bundle,
        request=replace(
            bundle.request,
            method_sequence=sequence,
            max_attempts=len(sequence),
        ),
        evidence=replace(
            bundle.evidence,
            method_sequence=sequence,
            attempt_timings=timings,
            attempts=len(sequence),
            observed_at=timings[-1].ended_at_utc,
        ),
    )
    assert authorize_future_adapter(
        replace(request, source_observations=(updated,))
    ).reason == TRUST_STOP


@pytest.mark.parametrize(
    "sequence",
    (
        ("GET",),
        ("HEAD",),
        ("GET", "HEAD"),
        ("HEAD", "GET", "HEAD"),
        ("HEAD", "HEAD", "HEAD", "GET"),
    ),
)
def test_every_rejected_head_get_sequence_has_stable_reason(
    sequence: tuple[str, ...],
) -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    timing = bundle.evidence.attempt_timings[0]
    timings = tuple(replace(timing, method=method) for method in sequence)
    updated = replace(
        bundle,
        request=replace(
            bundle.request,
            method_sequence=sequence,
            max_attempts=len(sequence),
        ),
        evidence=replace(
            bundle.evidence,
            method_sequence=sequence,
            attempt_timings=timings,
            attempts=len(sequence),
        ),
    )
    _reason(
        lambda: authorize_future_adapter(
            replace(request, source_observations=(updated,))
        ),
        STOP_TARGET_BINDING_INVALID,
    )


def test_head_get_grammar_is_exhaustively_closed_through_four_attempts() -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    for length in range(5):
        for sequence in product(("HEAD", "GET"), repeat=length):
            timings = tuple(
                SourceAttemptTiming(
                    method,
                    NOW + timedelta(microseconds=1_000 + index * 200),
                    NOW + timedelta(microseconds=1_100 + index * 200),
                    1_000_000 + index * 200_000,
                    1_100_000 + index * 200_000,
                )
                for index, method in enumerate(sequence)
            )
            updated_request = replace(
                bundle.request,
                method_sequence=sequence,
                max_attempts=length,
            )
            updated_evidence = replace(
                bundle.evidence,
                method_sequence=sequence,
                attempt_timings=timings,
                attempts=length,
                observed_at=(
                    timings[-1].ended_at_utc if timings else bundle.evidence.observed_at
                ),
            )
            call = lambda: validate_source_observation(
                updated_request,
                updated_evidence,
                request.target,
                request.snapshot_payload,
                request.evaluated_at,
            )
            if sequence in SOURCE_ATTEMPT_GRAMMAR:
                call()
            else:
                _reason(call, STOP_TARGET_BINDING_INVALID)


def test_hostile_method_member_is_rejected_without_comparison() -> None:
    calls: list[str] = []

    class Hostile:
        def __eq__(self, _other: object) -> bool:
            calls.append("eq")
            raise AssertionError("hostile method compared")

        def __iter__(self):
            calls.append("iter")
            raise AssertionError("hostile method iterated")

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("hostile method hashed")

        def __str__(self):
            calls.append("str")
            raise AssertionError("hostile method stringified")

    request = _authorization()
    bundle = request.source_observations[0]
    malformed = replace(
        bundle.request,
        method_sequence=(Hostile(), "GET"),  # type: ignore[arg-type]
    )
    _reason(
        lambda: validate_source_observation(
            malformed,
            bundle.evidence,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_TARGET_BINDING_INVALID,
    )
    assert calls == []


def test_profile_source_cardinality_is_bounded_before_hashing() -> None:
    request = _authorization()
    profile = _inventory(
        request.snapshot_payload, "institution_site_profiles"
    ).pages[0].rows[0]
    values = dict(profile.row.values)
    values["seed_urls"] = tuple(
        f"private-source-{index}" for index in range(MAX_SOURCES_PER_PROFILE + 1)
    )
    oversized = FrozenRow(
        tuple((column, values[column]) for column in TABLE_COLUMNS["institution_site_profiles"])
    )
    _reason(
        lambda: profile_source_fingerprints(profile.row_fingerprint, oversized),
        STOP_TARGET_BINDING_INVALID,
    )


def test_profile_source_cardinality_accepts_exact_limit() -> None:
    request = _authorization()
    profile = _inventory(
        request.snapshot_payload, "institution_site_profiles"
    ).pages[0].rows[0]
    values = dict(profile.row.values)
    values["seed_urls"] = tuple(
        f"private-source-{index}" for index in range(MAX_SOURCES_PER_PROFILE)
    )
    exact = FrozenRow(
        tuple((column, values[column]) for column in TABLE_COLUMNS["institution_site_profiles"])
    )
    assert len(profile_source_fingerprints(profile.row_fingerprint, exact)) == 64


def test_global_profile_source_cardinality_exact_and_plus_one(monkeypatch) -> None:
    profiles = tuple(
        _frozen_row(
            "institution_site_profiles",
            id=f"profile-{index}",
            institution_id=f"institution-{index}",
            discovery_enabled=True,
            pipeline_enabled=True,
            pipeline_ready=False,
            discovery_mode="sitemap",
            seed_urls=(f"private-seed-{index}",),
            catalog_url_patterns=(),
            allowed_url_patterns=(),
            circuit_open=False,
        )
        for index in range(2)
    )
    request = _authorization(profile_rows=profiles)
    assert contract.MAX_PROFILE_SOURCE_PAIRS == 50_000
    monkeypatch.setattr(contract, "MAX_PROFILE_SOURCE_PAIRS", 2)
    assert authorize_future_adapter(request).reason == TRUST_STOP
    monkeypatch.setattr(contract, "MAX_PROFILE_SOURCE_PAIRS", 1)
    _reason(lambda: authorize_future_adapter(request), STOP_TARGET_BINDING_INVALID)


def test_authorization_request_is_deeply_immutable_data_only() -> None:
    request_fields = {field.name for field in fields(AuthorizationRequest)}
    assert not request_fields & {
        "provider", "callback", "factory", "transport", "gate", "credential", "nonce"
    }
    assert RowCursor.__annotations__["row"] in {FrozenRow, "FrozenRow"}
    assert "snapshot_1_courses" not in FG3CohortEvidence.__dataclass_fields__
    request = _authorization()
    assert type(request.snapshot_payload.snapshot_1) is tuple
    assert type(_inventory(request.snapshot_payload, "courses").pages[0].rows[0].row.values) is tuple
    assert set(inspect.signature(authorize_future_adapter).parameters) == {"request"}


def test_evaluated_at_must_follow_complete_snapshot_2() -> None:
    request = _authorization()
    _reason(
        lambda: authorize_future_adapter(
            replace(request, evaluated_at=NOW + timedelta(microseconds=2_750))
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


@pytest.mark.parametrize(
    "position",
    ("before_snapshot_1", "at_snapshot_2_start", "after_snapshot_2", "after_evaluated"),
)
def test_source_observation_temporal_order_is_exact(position: str) -> None:
    request = _authorization()
    observed = {
        "before_snapshot_1": NOW,
        "at_snapshot_2_start": NOW + timedelta(microseconds=2_100),
        "after_snapshot_2": NOW + timedelta(microseconds=2_900),
        "after_evaluated": request.evaluated_at + timedelta(microseconds=1),
    }[position]
    bundle = replace(
        request.source_observations[0],
        evidence=replace(request.source_observations[0].evidence, observed_at=observed),
    )
    _reason(
        lambda: authorize_future_adapter(replace(request, source_observations=(bundle,))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_head_must_start_after_snapshot_1_closes() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    head = replace(
        head,
        started_at_utc=NOW + timedelta(microseconds=700),
        ended_at_utc=NOW + timedelta(microseconds=900),
        monotonic_started_ns=700_000,
        monotonic_ended_ns=900_000,
    )
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_head_wholly_before_snapshot_1_is_rejected() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    head = replace(
        head,
        started_at_utc=NOW - timedelta(microseconds=200),
        ended_at_utc=NOW - timedelta(microseconds=100),
        monotonic_started_ns=10_000,
        monotonic_ended_ns=110_000,
    )
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_get_must_end_before_snapshot_2_starts() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    get = replace(
        get,
        ended_at_utc=NOW + timedelta(microseconds=2_200),
        monotonic_ended_ns=2_200_000,
    )
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_get_wholly_after_snapshot_2_is_rejected() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    get = replace(
        get,
        started_at_utc=NOW + timedelta(microseconds=2_900),
        ended_at_utc=NOW + timedelta(microseconds=3_000),
        monotonic_started_ns=2_900_000,
        monotonic_ended_ns=3_000_000,
    )
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_crossing_attempt_is_rejected_even_when_observed_at_is_valid() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    head = replace(
        head,
        started_at_utc=NOW + timedelta(microseconds=750),
        ended_at_utc=NOW + timedelta(microseconds=950),
        monotonic_started_ns=750_000,
        monotonic_ended_ns=950_000,
    )
    _reason(
        lambda: authorize_future_adapter(
            _with_source_timings(
                request,
                (head, get),
                observed_at=get.ended_at_utc,
            )
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_attempts_must_not_overlap() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    get = replace(
        get,
        started_at_utc=NOW + timedelta(microseconds=1_050),
        monotonic_started_ns=1_050_000,
    )
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_attempts_must_match_method_order() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    out_of_order = (replace(head, method="GET"), replace(get, method="HEAD"))
    _reason(
        lambda: authorize_future_adapter(
            _with_source_timings(request, out_of_order)
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_attempt_utc_and_monotonic_durations_must_agree() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    head = replace(head, monotonic_ended_ns=head.monotonic_ended_ns + 250_000_001)
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_timing_count_must_equal_method_sequence() -> None:
    request = _authorization()
    head, _ = request.source_observations[0].evidence.attempt_timings
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head,))),
        STOP_CLOCK_TIMING_INVALID,
    )
    head, get = request.source_observations[0].evidence.attempt_timings
    extra = replace(
        get,
        started_at_utc=NOW + timedelta(microseconds=1_400),
        ended_at_utc=NOW + timedelta(microseconds=1_500),
        monotonic_started_ns=1_400_000,
        monotonic_ended_ns=1_500_000,
    )
    _reason(
        lambda: authorize_future_adapter(
            _with_source_timings(request, (head, get, extra))
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_observed_at_must_equal_real_final_attempt_end() -> None:
    request = _authorization()
    timings = request.source_observations[0].evidence.attempt_timings
    _reason(
        lambda: authorize_future_adapter(
            _with_source_timings(
                request,
                timings,
                observed_at=timings[-1].ended_at_utc + timedelta(microseconds=1),
            )
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


@pytest.mark.parametrize("duration", (0, -1, SOURCE_ATTEMPT_BUDGET_NS + 1))
def test_source_attempt_duration_must_be_positive_and_within_budget(
    duration: int,
) -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    head = replace(
        head,
        monotonic_ended_ns=head.monotonic_started_ns + duration,
    )
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_same_count_content_drift_and_count_reasons_stay_split() -> None:
    payload, target = _snapshot_bundle(changed_second=True)
    _reason(lambda: validate_snapshot_pair_payload(payload, target), STOP_SNAPSHOT_CONTENT_DRIFT)
    request = _authorization()
    courses = _inventory(request.snapshot_payload, "courses")
    _reason(
        lambda: validate_pagination(replace(courses, final_count=2), request.target),
        STOP_COUNT_DRIFT,
    )
    _reason(
        lambda: validate_pagination(replace(courses, pages=()), request.target),
        STOP_PAGINATION_INCOMPLETE,
    )
    _reason(
        lambda: authorize_future_adapter(
            replace(
                request,
                target=replace(request.target, manifest_digest=DIGESTS[91]),
            )
        ),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


def test_stable_over_capacity_count_is_pagination_not_count_drift() -> None:
    request = _authorization()
    courses = _inventory(request.snapshot_payload, "courses")
    oversized = replace(courses, initial_count=50_001, final_count=50_001)
    oversized = replace(oversized, inventory_digest=inventory_digest(oversized))
    _reason(lambda: validate_pagination(oversized, request.target), STOP_PAGINATION_INCOMPLETE)


def test_pagination_ordering_error_uses_exact_temporal_reason() -> None:
    request = _authorization()
    courses = _inventory(request.snapshot_payload, "courses")
    page = courses.pages[0]
    overlapping = replace(
        page,
        timing=replace(
            page.timing,
            started_at_utc=courses.initial_count_timing.ended_at_utc,
            monotonic_started_ns=courses.initial_count_timing.monotonic_ended_ns,
        ),
    )
    _reason(
        lambda: validate_pagination(replace(courses, pages=(overlapping,)), request.target),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_coverage_is_exact_for_eligible_profiles() -> None:
    request = _authorization()
    validate_source_coverage(
        request.source_observations,
        request.target,
        request.snapshot_payload,
        request.evaluated_at,
    )
    _reason(
        lambda: validate_source_coverage(
            (), request.target, request.snapshot_payload, request.evaluated_at
        ),
        STOP_TARGET_BINDING_INVALID,
    )


def test_source_observation_unit_is_profile_source_not_course() -> None:
    request = _authorization()
    request_fields = set(SourceObservationRequest.__dataclass_fields__)
    evidence_fields = set(SourceObservationEvidence.__dataclass_fields__)
    assert {"profile_fingerprint", "source_fingerprint"} <= request_fields
    assert {"profile_fingerprint", "source_fingerprint"} <= evidence_fields
    assert "course_fingerprint" not in request_fields | evidence_fields
    bundle = request.source_observations[0]
    assert bundle.request.profile_fingerprint == bundle.evidence.profile_fingerprint
    assert bundle.request.source_fingerprint == bundle.evidence.source_fingerprint
    other_source = replace(
        bundle,
        request=replace(bundle.request, source_fingerprint=DIGESTS[10]),
        evidence=replace(bundle.evidence, source_fingerprint=DIGESTS[10]),
    )
    _reason(
        lambda: validate_source_coverage(
            (bundle, other_source),
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_TARGET_BINDING_INVALID,
    )
    _reason(
        lambda: validate_source_coverage(
            request.source_observations * 2,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_TARGET_BINDING_INVALID,
    )
    wrong = replace(
        request.source_observations[0],
        request=replace(request.source_observations[0].request, profile_fingerprint=DIGESTS[9]),
        evidence=replace(request.source_observations[0].evidence, profile_fingerprint=DIGESTS[9]),
    )
    _reason(
        lambda: validate_source_coverage(
            (wrong,), request.target, request.snapshot_payload, request.evaluated_at
        ),
        STOP_TARGET_BINDING_INVALID,
    )


def test_historical_observations_and_prior_mutation_are_recomputed_and_predate_snapshot() -> None:
    request = _authorization()
    assert len(request.fg3_cohort.historical_observations) == 27
    assert len({item.observation_fingerprint for item in request.fg3_cohort.historical_observations}) == 27
    assert len({item.course_fingerprint for item in request.fg3_cohort.historical_observations}) == 3
    validate_fg3_cohort(
        request.fg3_cohort,
        request.historical_manifest,
        request.target,
        request.snapshot_payload,
    )
    item = request.fg3_cohort.historical_observations[0]
    future = replace(item, observed_at=NOW + timedelta(microseconds=200))
    future = replace(future, observation_fingerprint=historical_observation_fingerprint(future))
    cohort = replace(
        request.fg3_cohort,
        historical_observations=(future, *request.fg3_cohort.historical_observations[1:]),
    )
    _reason(
        lambda: validate_fg3_cohort(
            cohort,
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


@pytest.mark.parametrize(
    "offset_us,accepted",
    ((799, False), (800, False), (801, True)),
)
def test_source_start_boundary_around_snapshot_1_close(
    offset_us: int,
    accepted: bool,
) -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    head = replace(
        head,
        started_at_utc=NOW + timedelta(microseconds=offset_us),
        monotonic_started_ns=offset_us * 1_000,
    )
    updated = _with_source_timings(request, (head, get))
    if accepted:
        assert authorize_future_adapter(updated).reason == TRUST_STOP
    else:
        _reason(lambda: authorize_future_adapter(updated), STOP_CLOCK_TIMING_INVALID)


@pytest.mark.parametrize(
    "offset_us,accepted",
    ((2_099, True), (2_100, False), (2_101, False)),
)
def test_source_end_boundary_around_snapshot_2_start(
    offset_us: int,
    accepted: bool,
) -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    get = replace(
        get,
        ended_at_utc=NOW + timedelta(microseconds=offset_us),
        monotonic_ended_ns=offset_us * 1_000,
    )
    updated = _with_source_timings(request, (head, get))
    if accepted:
        assert authorize_future_adapter(updated).reason == TRUST_STOP
    else:
        _reason(lambda: authorize_future_adapter(updated), STOP_CLOCK_TIMING_INVALID)


@pytest.mark.parametrize("clock", ("utc", "monotonic"))
@pytest.mark.parametrize("offset_us,accepted", ((800, False), (801, True)))
def test_source_start_boundary_is_enforced_by_each_clock(
    clock: str,
    offset_us: int,
    accepted: bool,
) -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    if clock == "utc":
        head = replace(
            head,
            started_at_utc=NOW + timedelta(microseconds=offset_us),
        )
    else:
        head = replace(head, monotonic_started_ns=offset_us * 1_000)
    updated = _with_source_timings(request, (head, get))
    if accepted:
        assert authorize_future_adapter(updated).reason == TRUST_STOP
    else:
        _reason(lambda: authorize_future_adapter(updated), STOP_CLOCK_TIMING_INVALID)


@pytest.mark.parametrize("clock", ("utc", "monotonic"))
@pytest.mark.parametrize("offset_us,accepted", ((2_099, True), (2_100, False)))
def test_source_end_boundary_is_enforced_by_each_clock(
    clock: str,
    offset_us: int,
    accepted: bool,
) -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    if clock == "utc":
        get = replace(
            get,
            ended_at_utc=NOW + timedelta(microseconds=offset_us),
        )
    else:
        get = replace(get, monotonic_ended_ns=offset_us * 1_000)
    updated = _with_source_timings(request, (head, get))
    if accepted:
        assert authorize_future_adapter(updated).reason == TRUST_STOP
    else:
        _reason(lambda: authorize_future_adapter(updated), STOP_CLOCK_TIMING_INVALID)


@pytest.mark.parametrize("clock", ("utc", "monotonic"))
def test_source_overlap_is_rejected_independently_in_each_clock(clock: str) -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    if clock == "utc":
        get = replace(get, started_at_utc=head.ended_at_utc - timedelta(microseconds=1))
    else:
        get = replace(get, monotonic_started_ns=head.monotonic_ended_ns - 1)
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


@pytest.mark.parametrize("clock", ("utc", "monotonic"))
def test_source_temporal_order_is_rejected_independently_in_each_clock(
    clock: str,
) -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_timings
    if clock == "utc":
        get = replace(
            get,
            started_at_utc=NOW + timedelta(microseconds=900),
            ended_at_utc=NOW + timedelta(microseconds=950),
        )
    else:
        get = replace(
            get,
            monotonic_started_ns=900_000,
            monotonic_ended_ns=950_000,
        )
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_exact_duration_and_clock_tolerance_boundaries() -> None:
    exact_budget = ReadTiming(
        PAIR_ID,
        "SELECT_PAGE",
        READ_CLOCK_SOURCE,
        READ_CAPTURE_SEQUENCE,
        NOW,
        NOW + timedelta(seconds=15),
        0,
        SOURCE_ATTEMPT_BUDGET_NS,
    )
    validate_read_timing(exact_budget, PAIR_ID)
    _reason(
        lambda: validate_read_timing(
            replace(exact_budget, monotonic_ended_ns=SOURCE_ATTEMPT_BUDGET_NS + 1),
            PAIR_ID,
        ),
        STOP_CLOCK_TIMING_INVALID,
    )
    exact_tolerance = replace(
        exact_budget,
        ended_at_utc=NOW + timedelta(seconds=1),
        monotonic_ended_ns=1_000_000_000 + CLOCK_DURATION_TOLERANCE_NS,
    )
    validate_read_timing(exact_tolerance, PAIR_ID)
    _reason(
        lambda: validate_read_timing(
            replace(
                exact_tolerance,
                monotonic_ended_ns=1_000_000_000 + CLOCK_DURATION_TOLERANCE_NS + 1,
            ),
            PAIR_ID,
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_attempt_exact_budget_and_tolerance_edges() -> None:
    request = _authorization()
    payload, target = _shift_second_snapshot(
        request.snapshot_payload, request.target, timedelta(seconds=20)
    )
    bundle = request.source_observations[0]
    exact_budget = (
        SourceAttemptTiming(
            "HEAD",
            NOW + timedelta(milliseconds=1),
            NOW + timedelta(seconds=15, milliseconds=1),
            1_000_000,
            15_001_000_000,
        ),
        SourceAttemptTiming(
            "GET",
            NOW + timedelta(seconds=15, milliseconds=100),
            NOW + timedelta(seconds=15, milliseconds=200),
            15_100_000_000,
            15_200_000_000,
        ),
    )

    def validate(timings: tuple[SourceAttemptTiming, ...]) -> None:
        validate_source_observation(
            bundle.request,
            replace(
                bundle.evidence,
                attempt_timings=timings,
                observed_at=timings[-1].ended_at_utc,
            ),
            target,
            payload,
            NOW + timedelta(seconds=21),
        )

    validate(exact_budget)
    over_budget = (
        replace(
            exact_budget[0],
            monotonic_ended_ns=exact_budget[0].monotonic_ended_ns + 1,
        ),
        exact_budget[1],
    )
    _reason(lambda: validate(over_budget), STOP_CLOCK_TIMING_INVALID)
    utc_over_budget = (
        replace(
            exact_budget[0],
            ended_at_utc=exact_budget[0].ended_at_utc + timedelta(microseconds=1),
        ),
        exact_budget[1],
    )
    _reason(lambda: validate(utc_over_budget), STOP_CLOCK_TIMING_INVALID)

    exact_tolerance = (
        SourceAttemptTiming(
            "HEAD",
            NOW + timedelta(milliseconds=1),
            NOW + timedelta(seconds=1, milliseconds=1),
            1_000_000,
            1_251_000_000,
        ),
        SourceAttemptTiming(
            "GET",
            NOW + timedelta(seconds=2),
            NOW + timedelta(seconds=2, milliseconds=100),
            2_000_000_000,
            2_100_000_000,
        ),
    )
    validate(exact_tolerance)
    over_tolerance = (
        replace(
            exact_tolerance[0],
            monotonic_ended_ns=exact_tolerance[0].monotonic_ended_ns + 1,
        ),
        exact_tolerance[1],
    )
    _reason(lambda: validate(over_tolerance), STOP_CLOCK_TIMING_INVALID)
    inverse_tolerance = (
        SourceAttemptTiming(
            "HEAD",
            NOW + timedelta(milliseconds=1),
            NOW + timedelta(seconds=1, milliseconds=1),
            1_000_000,
            751_000_000,
        ),
        exact_tolerance[1],
    )
    validate(inverse_tolerance)
    inverse_over_tolerance = (
        replace(
            inverse_tolerance[0],
            monotonic_ended_ns=inverse_tolerance[0].monotonic_ended_ns - 1,
        ),
        inverse_tolerance[1],
    )
    _reason(lambda: validate(inverse_over_tolerance), STOP_CLOCK_TIMING_INVALID)


@pytest.mark.parametrize("case", ("missing", "duplicate", "extra", "unrelated"))
def test_exact_one_is_derived_from_immutable_mutation_evidence(case: str) -> None:
    request = _authorization()
    mutation = request.fg3_cohort.prior_mutations[0]
    if case == "missing":
        mutations = ()
    elif case == "duplicate":
        mutations = (mutation, mutation)
    else:
        course_fingerprint = (
            request.fg3_cohort.courses[0].course_fingerprint
            if case == "extra"
            else DIGESTS[89]
        )
        invalid = replace(
            mutation,
            course_fingerprint=course_fingerprint,
            mutation_fingerprint=prior_mutation_fingerprint(
                course_fingerprint,
                mutation.antecedent_run_fingerprint,
                mutation.antecedent_observed_at,
                mutation.mutation_kind,
                mutation.historical_observation_fingerprint,
            ),
        )
        mutations = (mutation, invalid)
    _reason(
        lambda: validate_fg3_cohort(
            replace(request.fg3_cohort, prior_mutations=mutations),
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        ),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


def test_mutation_links_antecedent_run_timestamp_and_deactivation_observation() -> None:
    request = _authorization()
    mutation = request.fg3_cohort.prior_mutations[0]
    observation = request.fg3_cohort.historical_observations[-1]
    assert mutation.course_fingerprint == observation.course_fingerprint
    assert mutation.antecedent_run_fingerprint == observation.run_id
    assert mutation.antecedent_observed_at == observation.observed_at
    assert observation.category == mutation.mutation_kind == "DEACTIVATION"
    assert mutation.mutation_fingerprint == prior_mutation_fingerprint(
        mutation.course_fingerprint,
        mutation.antecedent_run_fingerprint,
        mutation.antecedent_observed_at,
        mutation.mutation_kind,
        mutation.historical_observation_fingerprint,
    )
    inactive = request.fg3_cohort.prior_mutations[0]
    late = replace(inactive, antecedent_observed_at=NOW + timedelta(microseconds=200))
    _reason(
        lambda: validate_fg3_cohort(
            replace(request.fg3_cohort, prior_mutations=(late,)),
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


@pytest.mark.parametrize(
    "course_index,value",
    ((1, 0), (1, 1), (3, 0), (3, 1)),
)
def test_courses_is_active_rejects_integers_in_active_and_inactive_cohorts(
    course_index: int,
    value: int,
) -> None:
    request = _authorization(course_active_overrides={course_index: value})
    _reason(
        lambda: authorize_future_adapter(request),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


@pytest.mark.parametrize("snapshot", (1, 2))
def test_courses_is_active_is_checked_independently_in_each_snapshot(
    snapshot: int,
) -> None:
    request = _authorization(
        first_course_active_overrides={1: 1} if snapshot == 1 else None,
        second_course_active_overrides={1: 1} if snapshot == 2 else None,
    )
    _reason(
        lambda: validate_fg3_cohort(
            request.fg3_cohort,
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        ),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


def test_lifecycle_proxy_regressions_and_completeness() -> None:
    current = classify_lifecycle_proxy(
        last_harvested_at=NOW.isoformat(),
        created_at=(NOW - timedelta(days=30)).isoformat(),
        observed_at=NOW,
    )
    fallback = classify_lifecycle_proxy(
        last_harvested_at=None,
        created_at=(NOW - timedelta(days=7)).isoformat(),
        observed_at=NOW,
    )
    stale = classify_lifecycle_proxy(
        last_harvested_at=None,
        created_at=(NOW - timedelta(days=7, seconds=1)).isoformat(),
        observed_at=NOW,
    )
    unknown = classify_lifecycle_proxy(last_harvested_at=None, created_at=None, observed_at=NOW)
    future = classify_lifecycle_proxy(
        last_harvested_at=(NOW + timedelta(microseconds=1)).isoformat(),
        created_at=None,
        observed_at=NOW,
    )
    assert current.timestamp_origin == "LAST_HARVESTED_AT_PROXY"
    assert fallback.timestamp_origin == "CREATED_AT_PROXY"
    assert fallback.classification == "NOT_STALE"
    assert stale.classification == "STALE"
    subsecond_stale = classify_lifecycle_proxy(
        last_harvested_at=(NOW - timedelta(days=7, microseconds=1)).isoformat(),
        created_at=None,
        observed_at=NOW,
    )
    assert subsecond_stale.classification == "STALE"
    assert unknown.classification == "AGE_UNKNOWN"
    assert future.classification == "FUTURE_TIMESTAMP"
    assert lifecycle_allows_pass((current,))
    assert not lifecycle_allows_pass((replace(unknown, classification="NOT_STALE"),))
    request = _authorization()
    validate_lifecycle_evidence(
        request.lifecycle_evidence,
        request.target,
        request.snapshot_payload,
        request.evaluated_at,
    )
    for invalid in ((), request.lifecycle_evidence * 2):
        _reason(
            lambda invalid=invalid: validate_lifecycle_evidence(
                invalid, request.target, request.snapshot_payload, request.evaluated_at
            ),
            STOP_TARGET_BINDING_INVALID,
        )
    _reason(
        lambda: validate_lifecycle_evidence(
            (LifecycleEvidence(DIGESTS[90], current),),
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_TARGET_BINDING_INVALID,
    )


def test_lifecycle_rejects_non_string_raw_timestamp_without_coercion() -> None:
    _reason(
        lambda: classify_lifecycle_proxy(
            last_harvested_at=object(),  # type: ignore[arg-type]
            created_at=None,
            observed_at=NOW,
        ),
        STOP_TARGET_BINDING_INVALID,
    )


@pytest.mark.parametrize(
    "helper",
    (
        "target_binding_digest",
        "evidence_binding_digest",
        "row_fingerprint",
        "page_evidence_digest",
        "inventory_digest",
        "snapshot_payload_digest",
        "historical_manifest_digest",
        "historical_anchor_digest",
        "manifest_builder_receipt_digest",
        "anchor_provider_receipt_digest",
        "historical_observation_fingerprint",
        "prior_mutation_fingerprint",
        "classify_lifecycle_proxy",
        "lifecycle_allows_pass",
        "validate_capability",
        "validate_read_timing",
        "validate_pagination",
        "validate_snapshot_pair_payload",
        "validate_historical_anchor",
        "validate_fg3_cohort",
        "validate_source_observation",
        "validate_source_coverage",
        "validate_lifecycle_evidence",
        "public_contract_projection",
        "authorize_future_adapter",
    ),
)
def test_exported_helpers_have_stable_malformed_top_level_errors(helper: str) -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    calls = {
        "target_binding_digest": (lambda: target_binding_digest(object()), STOP_TARGET_BINDING_INVALID),
        "evidence_binding_digest": (lambda: evidence_binding_digest(object()), STOP_TARGET_BINDING_INVALID),
        "row_fingerprint": (lambda: row_fingerprint("courses", DIGESTS[1], PAIR_ID, object()), STOP_PAGINATION_INCOMPLETE),
        "page_evidence_digest": (lambda: page_evidence_digest("courses", DIGESTS[1], PAIR_ID, object()), STOP_PAGINATION_INCOMPLETE),
        "inventory_digest": (lambda: inventory_digest(object()), STOP_PAGINATION_INCOMPLETE),
        "snapshot_payload_digest": (lambda: snapshot_payload_digest(object()), STOP_PAGINATION_INCOMPLETE),
        "historical_manifest_digest": (lambda: historical_manifest_digest(object()), STOP_MANIFEST_ANCHOR_MISMATCH),
        "historical_anchor_digest": (lambda: historical_anchor_digest(object()), STOP_MANIFEST_ANCHOR_MISMATCH),
        "manifest_builder_receipt_digest": (lambda: manifest_builder_receipt_digest(object()), STOP_ANCHOR_NOT_INDEPENDENT),
        "anchor_provider_receipt_digest": (lambda: anchor_provider_receipt_digest(object()), STOP_ANCHOR_NOT_INDEPENDENT),
        "historical_observation_fingerprint": (lambda: historical_observation_fingerprint(object()), STOP_MANIFEST_ANCHOR_MISMATCH),
        "prior_mutation_fingerprint": (lambda: prior_mutation_fingerprint("bad", "bad", NOW, "bad", "bad"), STOP_MANIFEST_ANCHOR_MISMATCH),
        "classify_lifecycle_proxy": (lambda: classify_lifecycle_proxy(last_harvested_at=object(), created_at=None, observed_at=NOW), STOP_TARGET_BINDING_INVALID),
        "lifecycle_allows_pass": (lambda: lifecycle_allows_pass(object()), STOP_TARGET_BINDING_INVALID),
        "validate_capability": (lambda: validate_capability(object()), STOP_CAPABILITY_INVALID),
        "validate_read_timing": (lambda: validate_read_timing(object(), PAIR_ID), STOP_CLOCK_TIMING_INVALID),
        "validate_pagination": (lambda: validate_pagination(object(), request.target), STOP_PAGINATION_INCOMPLETE),
        "validate_snapshot_pair_payload": (lambda: validate_snapshot_pair_payload(object(), request.target), STOP_PAGINATION_INCOMPLETE),
        "validate_historical_anchor": (lambda: validate_historical_anchor(object(), request.historical_anchor, request.manifest_builder_receipt, request.anchor_provider_receipt, request.target, request.snapshot_payload, request.fg3_cohort.historical_observations, request.evaluated_at), STOP_MANIFEST_ANCHOR_MISMATCH),
        "validate_fg3_cohort": (lambda: validate_fg3_cohort(object(), request.historical_manifest, request.target, request.snapshot_payload), STOP_MANIFEST_ANCHOR_MISMATCH),
        "validate_source_observation": (lambda: validate_source_observation(object(), bundle.evidence, request.target, request.snapshot_payload, request.evaluated_at), STOP_TARGET_BINDING_INVALID),
        "validate_source_coverage": (lambda: validate_source_coverage(object(), request.target, request.snapshot_payload, request.evaluated_at), STOP_TARGET_BINDING_INVALID),
        "validate_lifecycle_evidence": (lambda: validate_lifecycle_evidence(object(), request.target, request.snapshot_payload, request.evaluated_at), STOP_TARGET_BINDING_INVALID),
        "public_contract_projection": (lambda: public_contract_projection(object()), STOP_TARGET_BINDING_INVALID),
        "authorize_future_adapter": (lambda: authorize_future_adapter(object()), STOP_TARGET_BINDING_INVALID),
    }
    call, reason = calls[helper]
    _reason(call, reason)


@pytest.mark.parametrize("surface", ("target", "source", "plan"))
def test_exact_dataclass_with_deleted_field_has_stable_reason(surface: str) -> None:
    request = _authorization()
    if surface == "target":
        malformed = request.target
        object.__delattr__(malformed, "environment")
        call = lambda: target_binding_digest(malformed)
        reason = STOP_TARGET_BINDING_INVALID
    elif surface == "source":
        bundle = request.source_observations[0]
        malformed = bundle.evidence
        object.__delattr__(malformed, "attempt_timings")
        call = lambda: validate_source_observation(
            bundle.request,
            malformed,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        )
        reason = STOP_TARGET_BINDING_INVALID
    else:
        malformed = authorize_future_adapter(request)
        object.__delattr__(malformed, "reason")
        call = lambda: public_contract_projection(malformed)
        reason = STOP_TARGET_BINDING_INVALID
    _reason(call, reason)


@pytest.mark.parametrize(
    "surface,reason",
    (
        ("source", STOP_TARGET_BINDING_INVALID),
        ("lifecycle", STOP_TARGET_BINDING_INVALID),
        ("fg3", STOP_MANIFEST_ANCHOR_MISMATCH),
    ),
)
def test_nested_inventory_with_deleted_field_has_stable_reason(
    surface: str,
    reason: str,
) -> None:
    request = _authorization()
    malformed = request.snapshot_payload.snapshot_1[0]
    object.__delattr__(malformed, "table")
    calls = {
        "source": lambda: validate_source_coverage(
            request.source_observations,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        "lifecycle": lambda: validate_lifecycle_evidence(
            request.lifecycle_evidence,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        "fg3": lambda: validate_fg3_cohort(
            request.fg3_cohort,
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        ),
    }
    _reason(calls[surface], reason)


def test_hostile_snapshot_collection_is_rejected_without_iteration() -> None:
    calls: list[str] = []

    class Hostile:
        def __iter__(self):
            calls.append("iter")
            raise AssertionError("hostile snapshot iterated")

    request = _authorization()
    payload = replace(request.snapshot_payload, snapshot_1=Hostile())
    _reason(
        lambda: validate_source_coverage(
            request.source_observations,
            request.target,
            payload,
            request.evaluated_at,
        ),
        STOP_TARGET_BINDING_INVALID,
    )
    assert calls == []


@pytest.mark.parametrize(
    "surface,reason",
    (
        ("source_bundles", STOP_TARGET_BINDING_INVALID),
        ("prior_mutations", STOP_MANIFEST_ANCHOR_MISMATCH),
        ("historical_observations", STOP_MANIFEST_ANCHOR_MISMATCH),
        ("pages", STOP_PAGINATION_INCOMPLETE),
        ("rows", STOP_PAGINATION_INCOMPLETE),
    ),
)
def test_hostile_tuple_bearing_surfaces_are_rejected_without_iteration(
    surface: str,
    reason: str,
) -> None:
    calls: list[str] = []

    class Hostile:
        def __iter__(self):
            calls.append("iter")
            raise AssertionError("hostile collection iterated")

    request = _authorization()
    hostile = Hostile()
    if surface == "source_bundles":
        call = lambda: validate_source_coverage(
            hostile,  # type: ignore[arg-type]
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        )
    elif surface in {"prior_mutations", "historical_observations"}:
        cohort = replace(request.fg3_cohort, **{surface: hostile})
        call = lambda: validate_fg3_cohort(
            cohort,
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        )
    else:
        courses = _inventory(request.snapshot_payload, "courses")
        if surface == "pages":
            malformed = replace(courses, pages=hostile)
        else:
            malformed = replace(
                courses,
                pages=(replace(courses.pages[0], rows=hostile),),
            )
        call = lambda: validate_pagination(malformed, request.target)
    _reason(call, reason)
    assert calls == []


@pytest.mark.parametrize(
    "surface,reason",
    (
        ("source_request", STOP_TARGET_BINDING_INVALID),
        ("page", STOP_PAGINATION_INCOMPLETE),
        ("cohort", STOP_MANIFEST_ANCHOR_MISMATCH),
    ),
)
def test_incomplete_tuple_bearing_dataclasses_have_stable_reason(
    surface: str,
    reason: str,
) -> None:
    request = _authorization()
    if surface == "source_request":
        malformed = request.source_observations[0].request
        object.__delattr__(malformed, "method_sequence")
        call = lambda: validate_source_observation(
            malformed,
            request.source_observations[0].evidence,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        )
    elif surface == "page":
        courses = _inventory(request.snapshot_payload, "courses")
        malformed = courses.pages[0]
        object.__delattr__(malformed, "rows")
        call = lambda: validate_pagination(
            replace(courses, pages=(malformed,)), request.target
        )
    else:
        malformed = request.fg3_cohort
        object.__delattr__(malformed, "prior_mutations")
        call = lambda: validate_fg3_cohort(
            malformed,
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        )
    _reason(call, reason)


@pytest.mark.parametrize("case", ("unhashable_manifest", "empty_source_payload", "bad_page", "bad_row", "bad_cohort"))
def test_nested_malformed_matrix_is_stable(case: str) -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    if case == "unhashable_manifest":
        malformed = replace(
            request.historical_manifest,
            observation_categories=(([], "INCONCLUSIVE"),),  # type: ignore[arg-type]
        )
        call = lambda: validate_historical_anchor(
            malformed,
            request.historical_anchor,
            request.manifest_builder_receipt,
            request.anchor_provider_receipt,
            request.target,
            request.snapshot_payload,
            request.fg3_cohort.historical_observations,
            request.evaluated_at,
        )
        reason = STOP_MANIFEST_ANCHOR_MISMATCH
    elif case == "empty_source_payload":
        empty = SnapshotPairPayloadEvidence(PAIR_ID, (), (), "")
        call = lambda: validate_source_observation(
            bundle.request, bundle.evidence, request.target, empty, request.evaluated_at
        )
        reason = STOP_TARGET_BINDING_INVALID
    elif case == "bad_page":
        courses = _inventory(request.snapshot_payload, "courses")
        call = lambda: validate_pagination(
            replace(courses, pages=(object(),)), request.target  # type: ignore[arg-type]
        )
        reason = STOP_PAGINATION_INCOMPLETE
    elif case == "bad_row":
        courses = _inventory(request.snapshot_payload, "courses")
        page = replace(courses.pages[0], rows=(object(),))  # type: ignore[arg-type]
        call = lambda: validate_pagination(replace(courses, pages=(page,)), request.target)
        reason = STOP_PAGINATION_INCOMPLETE
    else:
        call = lambda: validate_fg3_cohort(
            replace(request.fg3_cohort, courses=(object(),)),  # type: ignore[arg-type]
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        )
        reason = STOP_MANIFEST_ANCHOR_MISMATCH
    _reason(call, reason)


def test_hostile_nested_object_and_all_request_surfaces_are_rejected_without_execution() -> None:
    calls: list[str] = []

    class Hostile:
        def __getattribute__(self, name):
            if name == "__class__":
                return object.__getattribute__(self, name)
            calls.append(f"get:{name}")
            raise AssertionError(name)

        def __eq__(self, _other):
            calls.append("eq")
            raise AssertionError("eq")

        def __iter__(self):
            calls.append("iter")
            raise AssertionError("iter")

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("hash")

        def __str__(self):
            calls.append("str")
            raise AssertionError("str")

    hostile = Hostile()
    request = _authorization()
    for field_name in {field.name for field in fields(AuthorizationRequest)}:
        _reason(
            lambda field_name=field_name: authorize_future_adapter(
                replace(request, **{field_name: hostile})
            ),
            {
                "execution_sha": STOP_PROTECTED_SOURCE_INVALID,
                "execution_tree": STOP_PROTECTED_SOURCE_INVALID,
                "evaluated_at": STOP_CLOCK_TIMING_INVALID,
                "capability": STOP_CAPABILITY_INVALID,
                "historical_manifest": STOP_MANIFEST_ANCHOR_MISMATCH,
                "historical_anchor": STOP_MANIFEST_ANCHOR_MISMATCH,
                "manifest_builder_receipt": STOP_MANIFEST_ANCHOR_MISMATCH,
                "anchor_provider_receipt": STOP_MANIFEST_ANCHOR_MISMATCH,
                "fg3_cohort": STOP_MANIFEST_ANCHOR_MISMATCH,
                "snapshot_payload": STOP_PAGINATION_INCOMPLETE,
            }.get(field_name, STOP_TARGET_BINDING_INVALID),
        )
    row = _frozen_row("courses", id="course-hostile", institution_id="i", url="u", is_active=True)
    hostile_row = replace(row, values=(*row.values[:-1], (row.values[-1][0], hostile)))
    _reason(
        lambda: row_fingerprint("courses", DIGESTS[1], PAIR_ID, hostile_row),
        STOP_PAGINATION_INCOMPLETE,
    )
    assert calls == []
    with pytest.raises(TypeError):
        AuthorizationRequest(**{**request.__dict__, "provider": hostile})


def test_hostile_nested_snapshot_identifier_is_rejected_without_comparison() -> None:
    calls: list[str] = []

    class Hostile:
        def __ne__(self, _other: object) -> bool:
            calls.append("ne")
            raise AssertionError("hostile nested identifier compared")

    request = _authorization()
    payload = replace(request.snapshot_payload, snapshot_pair_id=Hostile())
    _reason(
        lambda: validate_snapshot_pair_payload(payload, request.target),
        STOP_PAGINATION_INCOMPLETE,
    )
    _reason(
        lambda: authorize_future_adapter(replace(request, snapshot_payload=payload)),
        STOP_PAGINATION_INCOMPLETE,
    )
    assert calls == []


def test_immutable_row_values_are_bounded_before_serialization() -> None:
    request = _authorization()
    courses = next(
        item for item in request.snapshot_payload.snapshot_1 if item.table == "courses"
    )
    row = courses.pages[0].rows[0]

    too_deep: object = "leaf"
    for _ in range(MAX_IMMUTABLE_DEPTH + 1):
        too_deep = (too_deep,)
    invalid_values = (
        too_deep,
        MAX_IMMUTABLE_INTEGER_ABS + 1,
        tuple("node" for _ in range(MAX_IMMUTABLE_NODES + 1)),
    )
    for invalid in invalid_values:
        values = tuple(
            (key, invalid if key == "url" else value) for key, value in row.row.values
        )
        _reason(
            lambda values=values: row_fingerprint(
                "courses",
                evidence_binding_digest(request.target),
                request.target.snapshot_pair_id,
                FrozenRow(values),
            ),
            STOP_PAGINATION_INCOMPLETE,
        )


def test_immutable_strings_enforce_utf8_boundaries_without_encoding_errors() -> None:
    request = _authorization()
    courses = next(
        item for item in request.snapshot_payload.snapshot_1 if item.table == "courses"
    )
    row = courses.pages[0].rows[0]

    def with_url(value: str) -> FrozenRow:
        return FrozenRow(
            tuple((key, value if key == "url" else current) for key, current in row.row.values)
        )

    exact_multibyte = "é" * (MAX_IMMUTABLE_STRING_BYTES // 2)
    assert row_fingerprint(
        "courses",
        evidence_binding_digest(request.target),
        request.target.snapshot_pair_id,
        with_url(exact_multibyte),
    ).startswith("sha256:")
    for invalid in (exact_multibyte + "é", "\ud800"):
        _reason(
            lambda invalid=invalid: row_fingerprint(
                "courses",
                evidence_binding_digest(request.target),
                request.target.snapshot_pair_id,
                with_url(invalid),
            ),
            STOP_PAGINATION_INCOMPLETE,
        )


def test_custom_tzinfo_is_rejected_without_invoking_it() -> None:
    calls: list[str] = []

    class HostileTimezone(tzinfo):
        def utcoffset(self, _dt):
            calls.append("utcoffset")
            raise AssertionError("custom timezone invoked")

        def dst(self, _dt):
            return None

        def tzname(self, _dt):
            return "hostile"

    request = _authorization()
    hostile_time = datetime(2026, 8, 14, 18, 0, tzinfo=HostileTimezone())
    _reason(
        lambda: authorize_future_adapter(replace(request, evaluated_at=hostile_time)),
        STOP_CLOCK_TIMING_INVALID,
    )
    assert calls == []


@pytest.mark.parametrize(
    "family,field_name",
    (
        ("query", "page_size"),
        ("query", "max_rows"),
        ("query", "max_pages"),
        ("query", "timeout_seconds"),
        ("query", "retry_budget"),
        ("capability", "max_snapshot_bytes"),
        ("pagination", "initial_count"),
        ("pagination", "final_count"),
        ("page", "requested_limit"),
        ("timing", "monotonic_started_ns"),
        ("timing", "monotonic_ended_ns"),
        ("source_request", "max_attempts"),
        ("source_evidence", "attempts"),
    ),
)
def test_bool_rejected_for_all_integer_fields(family: str, field_name: str) -> None:
    request = _authorization()
    if family == "query":
        query = GET_ONLY_CAPABILITY.queries[0]
        invalid = replace(query, **{field_name: True})
        capability = replace(
            GET_ONLY_CAPABILITY,
            queries=tuple(invalid if item.table == query.table else item for item in GET_ONLY_CAPABILITY.queries),
        )
        call, reason = lambda: validate_capability(capability), STOP_CAPABILITY_INVALID
    elif family == "capability":
        call, reason = lambda: validate_capability(replace(GET_ONLY_CAPABILITY, **{field_name: True})), STOP_CAPABILITY_INVALID
    elif family == "pagination":
        courses = _inventory(request.snapshot_payload, "courses")
        call, reason = lambda: validate_pagination(replace(courses, **{field_name: True}), request.target), STOP_COUNT_DRIFT
    elif family == "page":
        courses = _inventory(request.snapshot_payload, "courses")
        page = replace(courses.pages[0], **{field_name: True})
        call, reason = lambda: validate_pagination(replace(courses, pages=(page,)), request.target), STOP_PAGINATION_INCOMPLETE
    elif family == "timing":
        timing = replace(_timing("SELECT_PAGE", 300), **{field_name: True})
        call, reason = lambda: validate_read_timing(timing, PAIR_ID), STOP_CLOCK_TIMING_INVALID
    elif family == "source_request":
        bundle = request.source_observations[0]
        bad = replace(bundle, request=replace(bundle.request, **{field_name: True}))
        call, reason = lambda: authorize_future_adapter(replace(request, source_observations=(bad,))), STOP_TARGET_BINDING_INVALID
    else:
        bundle = request.source_observations[0]
        bad = replace(bundle, evidence=replace(bundle.evidence, **{field_name: True}))
        call, reason = lambda: authorize_future_adapter(replace(request, source_observations=(bad,))), STOP_TARGET_BINDING_INVALID
    _reason(call, reason)


@pytest.mark.parametrize("index", (0, 1, 2))
def test_bool_rejected_for_each_published_count_slot(index: int) -> None:
    request = _authorization()
    counts = list(request.historical_manifest.published_count_tuple)
    counts[index] = True
    malformed = replace(request.historical_manifest, published_count_tuple=tuple(counts))
    _reason(lambda: historical_manifest_digest(malformed), STOP_MANIFEST_ANCHOR_MISMATCH)


def test_utc_monotonic_tolerance_is_250ms() -> None:
    timing = _timing("SELECT_PAGE", 300)
    validate_read_timing(timing, PAIR_ID)
    assert CLOCK_DURATION_TOLERANCE_NS == 250_000_000
    _reason(
        lambda: validate_read_timing(
            replace(timing, ended_at_utc=timing.ended_at_utc + timedelta(milliseconds=251)),
            PAIR_ID,
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_public_projection_is_closed_and_private_free() -> None:
    projection = dict(public_contract_projection(authorize_future_adapter(_authorization())))
    assert projection == {
        "contract_version": CONTRACT_VERSION,
        "decision": "STOP",
        "reason_code": TRUST_STOP,
        "authorization_complete": False,
        "transport_created": False,
    }
    serialized = json.dumps(projection).lower()
    assert not any(field in serialized for field in PUBLIC_PROJECTION_FORBIDDEN_FIELDS)
    assert FINGERPRINT_DECLARATION == "INTEGRITY_NOT_AUTHORITY_OR_ANONYMIZATION"


class _ConnectedHostile:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"connected argument inspected: {name}")


def test_connected_mode_is_unchanged_unconditional_stop() -> None:
    with pytest.raises(G5Error, match=CONNECTED_STOP):
        collect_g5_connected(
            _ConnectedHostile(),  # type: ignore[arg-type]
            facade_factory=_ConnectedHostile(),
            observations=_ConnectedHostile(),  # type: ignore[arg-type]
            binding=_ConnectedHostile(),  # type: ignore[arg-type]
        )


def test_contract_ast_has_no_executable_caller_interface_or_mapping_rows() -> None:
    source = Path("scripts/shared/f10_9_g5_get_only_adapter_contract.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    assert "Protocol" not in source
    assert "runtime_checkable" not in source
    assert "asdict" not in source
    assert "row: Mapping" not in source
    assert "class FrozenRow" in source
    forbidden_modules = {
        "supabase", "requests", "httpx", "urllib", "socket", "subprocess",
        "db_client", "psycopg", "sqlalchemy", "boto3", "os",
    }
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not imports & forbidden_modules
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert not calls & {
        "getattr", "getenv", "open", "urlopen", "connect", "create_client",
        "run", "check_output", "eval", "exec", "__import__", "import_module",
    }


def test_collector_connected_body_is_still_only_del_then_stop() -> None:
    source = Path("scripts/shared/f10_9_g5_readonly_collector.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "collect_g5_connected"
    )
    executable = [
        node for node in function.body
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
