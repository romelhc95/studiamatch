from __future__ import annotations

import ast
import inspect
import json
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path

import pytest

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
) -> tuple[FrozenRow, ...]:
    if table == "institution_site_profiles":
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
                allowed_url_patterns=("opaque-pattern",),
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
            ),
            target,
            2_000,
        )
        for table in sorted(TABLE_COLUMNS)
    )
    payload = SnapshotPairPayloadEvidence(PAIR_ID, first, second, "")
    payload = replace(payload, payload_digest=snapshot_payload_digest(payload))
    return payload, replace(target, payload_digest=payload.payload_digest)


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
            run_id=RUN_ID,
            category=category,
            active_at_snapshot_1=index < 26,
            observed_at=NOW - timedelta(seconds=20) + timedelta(microseconds=index),
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
        issued_at=NOW - timedelta(seconds=50),
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
        issued_at=NOW - timedelta(seconds=40),
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
    antecedent_at = NOW - timedelta(seconds=10)
    mutation = prior_mutation_fingerprint(
        course_fingerprints[2], DIGESTS[5], antecedent_at, "DEACTIVATION"
    )
    return FG3CohortEvidence(
        target_binding_digest=target_digest,
        snapshot_pair_id=PAIR_ID,
        run_id=RUN_ID,
        courses=tuple(
            FG3CourseCohortEvidence(
                fingerprint,
                True,
                False,
                False,
                None,
                None,
                None,
                True,
                None,
                None,
                None,
            )
            for fingerprint in course_fingerprints[:2]
        )
        + (
            FG3CourseCohortEvidence(
                course_fingerprints[2],
                False,
                True,
                True,
                DIGESTS[5],
                observations[-1].observation_fingerprint,
                "DEACTIVATION",
                True,
                antecedent_at,
                mutation,
                "DEACTIVATION",
            ),
        ),
        historical_observations=observations,
    )


def _source_bundle(target: TargetBinding, payload: SnapshotPairPayloadEvidence, **overrides):
    profile = _inventory(payload, "institution_site_profiles").pages[0].rows[0]
    request = SourceObservationRequest(
        evidence_binding_digest(target),
        PAIR_ID,
        profile.row_fingerprint,
        DIGESTS[6],
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
        source_fingerprint=DIGESTS[6],
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
    **overrides: object,
) -> AuthorizationRequest:
    payload, target = _snapshot_bundle(
        course_active_overrides=course_active_overrides,
        first_course_active_overrides=first_course_active_overrides,
        second_course_active_overrides=second_course_active_overrides,
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
        "source_observations": (_source_bundle(target, payload),),
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
        source_observations=(replace(bundle, evidence=evidence),),
    )


def test_v2_1_freezes_v2_and_valid_request_stops_at_trust() -> None:
    assert (CONTRACT_VERSION, SCHEMA_VERSION, ALGORITHM_VERSION) == (
        "f10.9-g5-get-only-adapter-contract.v2.1",
        "f10.9-g5-get-only-adapter-schema.v2.1",
        "f10.9-g5-get-only-adapter-v2.1",
    )
    assert HISTORICAL_CONTRACT_VERSION.endswith(".v2")
    assert HISTORICAL_V2_STATUS == "HISTORICAL_ANTECENT_NOT_FIT_FOR_CONNECTED_MODE".replace(
        "ANTECENT", "ANTECEDENT"
    )
    assert PROTECTED_SOURCE_SHA == "c7783af918c4e434d31b80e9a65247329c0b3595"
    assert PROTECTED_SOURCE_TREE == "37d4ab05738355436169188d2613f860c6b35148"
    assert CURRENT_GATE_STATUS == "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED"
    plan = authorize_future_adapter(_authorization())
    assert plan.completed_steps == COMPLETED_STRUCTURAL_STEPS == AUTHORIZATION_ORDER[:-1]
    assert plan.next_step == plan.reason == TRUST_STOP
    assert plan.authorization_complete is plan.transport_created is False
    assert plan.trust_verification_implemented is False
    assert len(TRUST_MODEL_FUTURE_REQUIREMENTS) == 5


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
    inactive = request.fg3_cohort.courses[-1]
    late = replace(inactive, antecedent_observed_at=NOW + timedelta(microseconds=200))
    late = replace(
        late,
        mutation_fingerprint=prior_mutation_fingerprint(
            late.course_fingerprint,
            str(late.antecedent_run_fingerprint),
            late.antecedent_observed_at,
            str(late.mutation_kind),
        ),
    )
    _reason(
        lambda: validate_fg3_cohort(
            replace(request.fg3_cohort, courses=(*request.fg3_cohort.courses[:-1], late)),
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
        "prior_mutation_fingerprint": (lambda: prior_mutation_fingerprint("bad", "bad", NOW, "bad"), STOP_MANIFEST_ANCHOR_MISMATCH),
        "classify_lifecycle_proxy": (lambda: classify_lifecycle_proxy(last_harvested_at=object(), created_at=None, observed_at=NOW), STOP_TARGET_BINDING_INVALID),
        "lifecycle_allows_pass": (lambda: lifecycle_allows_pass(object()), STOP_TARGET_BINDING_INVALID),
        "validate_capability": (lambda: validate_capability(object()), STOP_CAPABILITY_INVALID),
        "validate_read_timing": (lambda: validate_read_timing(object(), PAIR_ID), STOP_CLOCK_TIMING_INVALID),
        "validate_pagination": (lambda: validate_pagination(object(), request.target), STOP_PAGINATION_INCOMPLETE),
        "validate_snapshot_pair_payload": (lambda: validate_snapshot_pair_payload(object(), request.target), STOP_PAGINATION_INCOMPLETE),
        "validate_historical_anchor": (lambda: validate_historical_anchor(object(), request.historical_anchor, request.manifest_builder_receipt, request.anchor_provider_receipt, request.target, request.evaluated_at), STOP_MANIFEST_ANCHOR_MISMATCH),
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
