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
    EXCLUDED_DYNAMIC_SOURCE_KINDS,
    EffectiveProfileRouting,
    FG3CohortEvidence,
    FG3CourseCohortEvidence,
    FG3HistoricalObservationEvidence,
    FG3PriorMutationEvidence,
    FINGERPRINT_DECLARATION,
    FORBIDDEN_METHODS,
    GO_COMPATIBLE_SOURCE_TERMINALS,
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
    MAX_FG3_HISTORICAL_OBSERVATIONS,
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
    REDIRECT_EVIDENCE_POLICY,
    ReadTiming,
    RowCursor,
    SCHEMA_VERSION,
    SOURCE_ATTEMPT_BUDGET_NS,
    SOURCE_ATTEMPT_GRAMMAR,
    SOURCE_CONFIGURATION_ROLES,
    SOURCE_ROLE_FILTER,
    SOURCE_ROLE_PROBE_TARGET,
    SOURCE_ROLE_TEMPLATE,
    SOURCE_SCOPE,
    STOP_ANCHOR_NOT_INDEPENDENT,
    STOP_CAPABILITY_INVALID,
    STOP_CLOCK_TIMING_INVALID,
    STOP_COUNT_DRIFT,
    STOP_MANIFEST_ANCHOR_MISMATCH,
    STOP_PROFILE_ROUTING_INVALID,
    STOP_SOURCE_BLOCKERS_PRESENT,
    STOP_LIFECYCLE_BLOCKERS_PRESENT,
    STOP_PAGINATION_INCOMPLETE,
    STOP_PROTECTED_SOURCE_INVALID,
    STOP_SNAPSHOT_CONTENT_DRIFT,
    STOP_TARGET_BINDING_INVALID,
    SourceObservationBundle,
    SourceObservationEvidence,
    SourceObservationRequest,
    SourceAttemptResult,
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
    derive_effective_profile_routing,
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
    source_terminal_reason,
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
    if table == "institution_site_profiles":
        values.update(
            {
                "site_type": "traditional_ssr",
                "seed_urls": (),
                "catalog_url_patterns": (),
                "catalog_max_pages": 5,
                "allowed_url_patterns": (),
                "exclusion_patterns": (),
                "requires_cloudflare_bypass": False,
                "warmup_url": None,
                "circuit_opened_at": None,
            }
        )
    values.update(overrides)
    return FrozenRow(tuple((column, values[column]) for column in TABLE_COLUMNS[table]))


def _rows(
    table: str,
    *,
    changed: bool = False,
    course_active_overrides: dict[int, object] | None = None,
    profile_rows: tuple[FrozenRow, ...] | None = None,
) -> tuple[FrozenRow, ...]:
    if table == "institutions":
        institution_ids = (
            tuple(str(dict(row.values)["institution_id"]) for row in profile_rows)
            if profile_rows is not None
            else ("institution-001",)
        )
        return tuple(
            _frozen_row(
                table,
                id=identifier,
                name=f"Institution {index}",
                slug=f"institution-{index}",
                website_url=f"https://institution-{index}.example.invalid/base",
            )
            for index, identifier in enumerate(institution_ids, 1)
        )
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
                site_type="traditional_ssr",
                discovery_mode="hardcoded_urls",
                seed_urls=("https://institution-1.example.invalid/course",),
                catalog_url_patterns=(),
                catalog_max_pages=5,
                allowed_url_patterns=(),
                exclusion_patterns=(),
                requires_cloudflare_bypass=False,
                warmup_url=None,
                circuit_open=False,
                circuit_opened_at=None,
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
                last_harvested_at=(NOW - timedelta(hours=12)).isoformat(),
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
            for index in range(1, 5)
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
    target_issued_at: datetime | None = None,
):
    target = _target(**({"issued_at": target_issued_at} if target_issued_at is not None else {}))
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
    for inactive_index, course in enumerate(course_fingerprints[3:], 1):
        observation = FG3HistoricalObservationEvidence(
            observation_fingerprint="",
            target_binding_digest=target_digest,
            snapshot_pair_id=PAIR_ID,
            course_fingerprint=course,
            run_id=DIGESTS[5 + inactive_index],
            category="PRIOR_DEACTIVATION",
            active_at_snapshot_1=False,
            observed_at=NOW - timedelta(seconds=49, microseconds=inactive_index),
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
    mutation_observations = tuple(
        item for item in observations if item.category in {"DEACTIVATION", "PRIOR_DEACTIVATION"}
    )
    mutations = tuple(
        FG3PriorMutationEvidence(
            observation.course_fingerprint,
            observation.run_id,
            observation.observed_at,
            "DEACTIVATION",
            prior_mutation_fingerprint(
                observation.course_fingerprint,
                observation.run_id,
                observation.observed_at,
                "DEACTIVATION",
                observation.observation_fingerprint,
            ),
            observation.observation_fingerprint,
        )
        for observation in mutation_observations
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
        + tuple(
            FG3CourseCohortEvidence(fingerprint, False, True)
            for fingerprint in course_fingerprints[2:]
        ),
        prior_mutations=mutations,
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
    profile_values = dict(profile.row.values)
    institution = next(
        cursor
        for page in _inventory(payload, "institutions").pages
        for cursor in page.rows
        if dict(cursor.row.values)["id"] == profile_values["institution_id"]
    )
    if source_fingerprint is None:
        source_fingerprint = sorted(
            profile_source_fingerprints(
                profile.row_fingerprint,
                profile.row,
                institution.row_fingerprint,
                institution.row,
                NOW + timedelta(microseconds=1_000),
            )
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
        SourceAttemptResult(
            "HEAD",
            NOW + timedelta(microseconds=1_000),
            NOW + timedelta(microseconds=1_100),
            1_000_000,
            1_100_000,
            403,
        ),
        SourceAttemptResult(
            "GET",
            NOW + timedelta(microseconds=1_200),
            NOW + timedelta(microseconds=1_300),
            1_200_000,
            1_300_000,
            200,
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
        attempt_results=timings,
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
        pipeline_gate = values.get("pipeline_enabled", values["pipeline_ready"])
        if (
            type(values["discovery_enabled"]) is bool
            and type(pipeline_gate) is bool
            and type(values["pipeline_ready"]) is bool
            and type(values["circuit_open"]) is bool
        ):
            institution = next(
                cursor
                for page in _inventory(payload, "institutions").pages
                for cursor in page.rows
                if dict(cursor.row.values)["id"] == values["institution_id"]
            )
            try:
                routing = derive_effective_profile_routing(
                    profile.row_fingerprint,
                    profile.row,
                    institution.row_fingerprint,
                    institution.row,
                    NOW + timedelta(microseconds=1_000),
                )
            except G5AdapterContractError:
                continue
            if routing.eligible:
                bundles.extend(
                    _source_bundle(
                        target,
                        payload,
                        profile_index=index,
                        source_fingerprint=item.source_fingerprint,
                    )
                    for item in routing.static_targets
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


def _routing_for(request: AuthorizationRequest, profile_index: int = 0) -> EffectiveProfileRouting:
    profile = _inventory(request.snapshot_payload, "institution_site_profiles").pages[0].rows[
        profile_index
    ]
    profile_values = dict(profile.row.values)
    institution = next(
        cursor
        for page in _inventory(request.snapshot_payload, "institutions").pages
        for cursor in page.rows
        if dict(cursor.row.values)["id"] == profile_values["institution_id"]
    )
    routing_observed_at = (
        min(
            bundle.evidence.attempt_results[0].started_at_utc
            for bundle in request.source_observations
        )
        if request.source_observations
        else max(
            timing.ended_at_utc
            for inventory in request.snapshot_payload.snapshot_1
            for timing in (
                inventory.initial_count_timing,
                *(page.timing for page in inventory.pages),
                inventory.final_count_timing,
            )
        )
    )
    return derive_effective_profile_routing(
        profile.row_fingerprint,
        profile.row,
        institution.row_fingerprint,
        institution.row,
        routing_observed_at,
    )


def _authorization(
    *,
    course_active_overrides: dict[int, object] | None = None,
    first_course_active_overrides: dict[int, object] | None = None,
    second_course_active_overrides: dict[int, object] | None = None,
    profile_rows: tuple[FrozenRow, ...] | None = None,
    target_issued_at: datetime | None = None,
    **overrides: object,
) -> AuthorizationRequest:
    payload, target = _snapshot_bundle(
        course_active_overrides=course_active_overrides,
        first_course_active_overrides=first_course_active_overrides,
        second_course_active_overrides=second_course_active_overrides,
        profile_rows=profile_rows,
        target_issued_at=target_issued_at,
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
    timings: tuple[SourceAttemptResult, ...],
    *,
    observed_at: datetime | None = None,
) -> AuthorizationRequest:
    bundle = request.source_observations[0]
    profile = _inventory(request.snapshot_payload, "institution_site_profiles").pages[0].rows[0]
    institution = _inventory(request.snapshot_payload, "institutions").pages[0].rows[0]
    routing = derive_effective_profile_routing(
        profile.row_fingerprint,
        profile.row,
        institution.row_fingerprint,
        institution.row,
        timings[0].started_at_utc,
    )
    source_fingerprint = routing.static_targets[0].source_fingerprint
    evidence = replace(
        bundle.evidence,
        source_fingerprint=source_fingerprint,
        attempt_results=timings,
        observed_at=timings[-1].ended_at_utc if observed_at is None else observed_at,
    )
    return replace(
        request,
        source_observations=(
            replace(
                bundle,
                request=replace(
                    bundle.request, source_fingerprint=source_fingerprint
                ),
                evidence=evidence,
            ),
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


def test_v2_3_freezes_v2_2_and_valid_request_stops_at_trust() -> None:
    assert (CONTRACT_VERSION, SCHEMA_VERSION, ALGORITHM_VERSION) == (
        "f10.9-g5-get-only-adapter-contract.v2.3",
        "f10.9-g5-get-only-adapter-schema.v2.3",
        "f10.9-g5-get-only-adapter-v2.3",
    )
    assert HISTORICAL_CONTRACT_VERSION.endswith(".v2.2")
    assert HISTORICAL_V2_STATUS == "HISTORICAL_ANTECENT_NOT_FIT_FOR_CONNECTED_MODE".replace(
        "ANTECENT", "ANTECEDENT"
    )
    assert PROTECTED_SOURCE_SHA == "58e0a0b37f7a3795e9487ab01aa558b5ecaa6ae3"
    assert PROTECTED_SOURCE_TREE == "13eb0465233c9e870995763630ee9e6541a45add"
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


@pytest.mark.parametrize("offset_us,accepted", ((-1, True), (0, True), (1, False)))
def test_target_issued_at_may_precede_or_equal_first_historical_observation(
    offset_us: int, accepted: bool
) -> None:
    issued_at = NOW - timedelta(seconds=50) + timedelta(microseconds=offset_us)
    request = _authorization(target_issued_at=issued_at)
    if accepted:
        assert authorize_future_adapter(request).reason == TRUST_STOP
    else:
        _reason(lambda: authorize_future_adapter(request), STOP_CLOCK_TIMING_INVALID)


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
        (None, True, STOP_PROFILE_ROUTING_INVALID),
        (None, False, STOP_PROFILE_ROUTING_INVALID),
        (0, True, STOP_PROFILE_ROUTING_INVALID),
        (1, True, STOP_PROFILE_ROUTING_INVALID),
        (True, 0, STOP_PROFILE_ROUTING_INVALID),
        (True, 1, STOP_PROFILE_ROUTING_INVALID),
        (True, None, STOP_PROFILE_ROUTING_INVALID),
        (None, None, STOP_PROFILE_ROUTING_INVALID),
        ("true", True, STOP_PROFILE_ROUTING_INVALID),
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
        discovery_mode="sitemap_bfs",
        catalog_url_patterns=(),
        allowed_url_patterns=(),
        circuit_open=False,
    )
    request = _authorization(profile_rows=(profile,))
    if expected == TRUST_STOP:
        assert authorize_future_adapter(request).reason == TRUST_STOP
    else:
        _reason(lambda: authorize_future_adapter(request), expected)


def test_pipeline_ready_fallback_applies_only_when_pipeline_column_is_absent() -> None:
    current = _frozen_row(
        "institution_site_profiles",
        id="profile-legacy",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="sitemap_bfs",
        circuit_open=False,
    )
    legacy = FrozenRow(tuple(pair for pair in current.values if pair[0] != "pipeline_enabled"))
    request = _authorization(profile_rows=(legacy,))
    assert authorize_future_adapter(request).reason == TRUST_STOP
    profile = _inventory(request.snapshot_payload, "institution_site_profiles").pages[0].rows[0]
    institution = _inventory(request.snapshot_payload, "institutions").pages[0].rows[0]
    routing = derive_effective_profile_routing(
        profile.row_fingerprint,
        profile.row,
        institution.row_fingerprint,
        institution.row,
        request.evaluated_at,
    )
    assert routing.pipeline_enabled_present is False
    assert routing.pipeline_enabled is None


@pytest.mark.parametrize("field,value", (("discovery_enabled", 1), ("circuit_open", 0)))
def test_discovery_and_circuit_gates_require_strict_booleans(field: str, value: object) -> None:
    gates = {"discovery_enabled": True, "circuit_open": False}
    gates[field] = value
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-strict",
        institution_id="institution-001",
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        **gates,
    )
    _reason(
        lambda: authorize_future_adapter(_authorization(profile_rows=(profile,))),
        STOP_PROFILE_ROUTING_INVALID,
    )


@pytest.mark.parametrize(
    "mode,overrides,expected",
    (
        (
            "hardcoded_urls",
            {"seed_urls": ("https://institution-1.example.invalid/a", "https://institution-1.example.invalid/b")},
            (("HARDCODED_DETAIL", "https://institution-1.example.invalid/a"), ("HARDCODED_DETAIL", "https://institution-1.example.invalid/b")),
        ),
        (
            "paginated_catalog",
            {"catalog_url_patterns": ("https://institution-1.example.invalid/catalog/{page}",), "catalog_max_pages": 3},
            tuple(("CATALOG_PAGE", f"https://institution-1.example.invalid/catalog/{page}") for page in range(1, 4)),
        ),
        (
            "catalog_link_extraction",
            {"seed_urls": ("https://institution-1.example.invalid/catalog",)},
            (("CATALOG_ROOT", "https://institution-1.example.invalid/catalog"), ("CATALOG_ROOT", "https://institution-1.example.invalid/base")),
        ),
        (
            "sitemap_bfs",
            {},
            (("SITEMAP_ROOT", "https://institution-1.example.invalid/sitemap.xml"), ("BFS_ROOT", "https://institution-1.example.invalid/base")),
        ),
    ),
)
def test_effective_routing_matches_static_harvester_targets(
    mode: str,
    overrides: dict[str, object],
    expected: tuple[tuple[str, str], ...],
) -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-routing",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode=mode,
        circuit_open=False,
        allowed_url_patterns=("re:^/",),
        exclusion_patterns=("/news/",),
        **overrides,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert tuple((item.kind, item.url) for item in routing.static_targets) == expected
    assert all(item.role == SOURCE_ROLE_PROBE_TARGET for item in routing.static_targets)
    assert all("allowed" not in item.kind.lower() and "exclusion" not in item.kind.lower() for item in routing.static_targets)
    assert dict(SOURCE_CONFIGURATION_ROLES) == {
        "static_targets": SOURCE_ROLE_PROBE_TARGET,
        "catalog_url_patterns": SOURCE_ROLE_TEMPLATE,
        "allowed_url_patterns": SOURCE_ROLE_FILTER,
        "exclusion_patterns": SOURCE_ROLE_FILTER,
    }
    assert SOURCE_SCOPE == "STATIC_HARVESTER_ENTRY_TARGETS_ONLY"
    assert EXCLUDED_DYNAMIC_SOURCE_KINDS == (
        "NESTED_SITEMAP",
        "CATALOG_EXTRACTED_LINK",
        "BFS_CHILD",
    )


def test_warmup_is_conditional_and_dormant_configuration_is_only_fingerprinted() -> None:
    base = dict(
        id="profile-warmup",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        catalog_url_patterns=("https://dormant.invalid/{page}",),
        allowed_url_patterns=("/course",),
        exclusion_patterns=("/news",),
        requires_cloudflare_bypass=True,
        warmup_url="https://institution-1.example.invalid/warmup",
        circuit_open=False,
    )
    no_browser = _routing_for(
        _authorization(profile_rows=(_frozen_row("institution_site_profiles", site_type="traditional_ssr", **base),))
    )
    browser = _routing_for(
        _authorization(profile_rows=(_frozen_row("institution_site_profiles", site_type="spa_js_heavy", **base),))
    )
    assert [item.kind for item in no_browser.static_targets] == ["HARDCODED_DETAIL"]
    assert [item.kind for item in browser.static_targets] == ["WARMUP", "HARDCODED_DETAIL"]
    assert no_browser.routing_fingerprint != browser.routing_fingerprint
    assert all("dormant.invalid" not in item.url for item in browser.static_targets)


def test_dormant_template_changes_fingerprints_without_becoming_target() -> None:
    common = dict(
        id="profile-dormant",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        circuit_open=False,
    )
    first = _routing_for(
        _authorization(
            profile_rows=(
                _frozen_row(
                    "institution_site_profiles",
                    catalog_url_patterns=("https://dormant-a.invalid/{page}",),
                    **common,
                ),
            )
        )
    )
    second = _routing_for(
        _authorization(
            profile_rows=(
                _frozen_row(
                    "institution_site_profiles",
                    catalog_url_patterns=("https://dormant-b.invalid/{page}",),
                    **common,
                ),
            )
        )
    )
    assert tuple((item.kind, item.url) for item in first.static_targets) == tuple(
        (item.kind, item.url) for item in second.static_targets
    )
    assert first.routing_fingerprint != second.routing_fingerprint
    assert first.static_targets[0].source_fingerprint != second.static_targets[0].source_fingerprint
    assert all("dormant" not in item.url for item in (*first.static_targets, *second.static_targets))


def test_effective_routing_contains_only_requested_source_derivation_fields() -> None:
    fields = set(EffectiveProfileRouting.__dataclass_fields__)
    removed = {"catalog_scroll_iterations", "catalog_link_selector"}
    assert not fields & removed
    assert not set(TABLE_COLUMNS["institution_site_profiles"]) & removed
    profile_query = next(
        query for query in GET_ONLY_CAPABILITY.queries if query.table == "institution_site_profiles"
    )
    assert not set(profile_query.columns) & removed


def test_allowed_and_exclusion_patterns_filter_hardcoded_targets_but_are_never_targets() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-filters",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=(
            "https://institution-1.example.invalid/course/keep",
            "https://institution-1.example.invalid/course/news/drop",
            "https://institution-1.example.invalid/other/drop",
        ),
        allowed_url_patterns=("re:^/course/",),
        exclusion_patterns=("/news/",),
        circuit_open=False,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert tuple((item.kind, item.url) for item in routing.static_targets) == (
        ("HARDCODED_DETAIL", "https://institution-1.example.invalid/course/keep"),
    )


def test_targets_are_canonical_and_deduplicated_by_kind_and_url() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-canonical",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        site_type="spa_js_heavy",
        discovery_mode="hardcoded_urls",
        seed_urls=(
            "HTTPS://INSTITUTION-1.EXAMPLE.INVALID:443/course?utm_source=x",
            "https://institution-1.example.invalid/course",
        ),
        requires_cloudflare_bypass=True,
        warmup_url="https://institution-1.example.invalid/course?fbclid=x",
        circuit_open=False,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert tuple((item.kind, item.url) for item in routing.static_targets) == (
        ("WARMUP", "https://institution-1.example.invalid/course"),
        ("HARDCODED_DETAIL", "https://institution-1.example.invalid/course"),
    )
    assert routing.seed_urls == (
        "https://institution-1.example.invalid/course",
        "https://institution-1.example.invalid/course",
    )
    assert routing.warmup_url == "https://institution-1.example.invalid/course"
    assert len({(item.kind, item.url) for item in routing.static_targets}) == 2


@pytest.mark.parametrize(
    "url",
    (
        "http://localhost/course",
        "http://sub.localhost/course",
        "http://127.0.0.1/course",
        "http://10.0.0.1/course",
        "http://169.254.1.1/course",
        "http://[::1]/course",
    ),
)
def test_routing_url_rejects_localhost_and_non_global_ip_literals(url: str) -> None:
    _reason(lambda: contract._routing_url(url), STOP_PROFILE_ROUTING_INVALID)


def test_routing_url_does_not_resolve_dns_names() -> None:
    assert contract._routing_url("HTTPS://Does-Not-Resolve.Example.Invalid:443/path") == (
        "https://does-not-resolve.example.invalid/path"
    )


@pytest.mark.parametrize(
    "pattern",
    (
        "re:" + "a" * 201,
        "re:(a+)+",
        r"re:(a)\1",
        "re:(?=admin)",
        "re:(?<=admin)",
        "re:[",
        "re:a*a*a*a*a*a*b",
        "re:a+a+a+a+a+a+b",
        "re:a?a?a?a?a?a?b",
        "re:a{1}b",
    ),
)
@pytest.mark.parametrize("field", ("allowed_url_patterns", "exclusion_patterns"))
def test_profile_regex_security_rejects_unsafe_or_invalid_patterns(
    pattern: str, field: str
) -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-regex",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        circuit_open=False,
        **{field: (pattern,)},
    )
    _reason(
        lambda: authorize_future_adapter(_authorization(profile_rows=(profile,))),
        STOP_PROFILE_ROUTING_INVALID,
    )


@pytest.mark.parametrize(
    "age,eligible,effective_open,auto_closed",
    (
        (timedelta(hours=24) - timedelta(microseconds=1), False, True, False),
        (timedelta(hours=24), True, False, True),
        (timedelta(hours=24) + timedelta(microseconds=1), True, False, True),
    ),
)
def test_circuit_effective_state_matches_harvester_24_hour_boundary(
    age: timedelta,
    eligible: bool,
    effective_open: bool,
    auto_closed: bool,
) -> None:
    observed_at = NOW + timedelta(microseconds=1_000)
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-circuit",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        circuit_open=True,
        circuit_opened_at=(observed_at - age).isoformat(),
        )
    request = _authorization(profile_rows=(profile,))
    profile_cursor = _inventory(
        request.snapshot_payload, "institution_site_profiles"
    ).pages[0].rows[0]
    institution_cursor = _inventory(
        request.snapshot_payload, "institutions"
    ).pages[0].rows[0]
    routing = derive_effective_profile_routing(
        profile_cursor.row_fingerprint,
        profile_cursor.row,
        institution_cursor.row_fingerprint,
        institution_cursor.row,
        observed_at,
    )
    assert routing.observed_at == observed_at
    assert routing.eligible is eligible
    assert routing.circuit_effective_open is effective_open
    assert routing.circuit_auto_closed is auto_closed
    assert authorize_future_adapter(request).reason == TRUST_STOP


def test_circuit_cooldown_crossing_before_evaluated_at_uses_routing_start() -> None:
    evaluated_at = NOW + timedelta(microseconds=3_000)
    routing_start = NOW + timedelta(microseconds=1_000)
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-circuit-crossing",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        circuit_open=True,
        circuit_opened_at=(evaluated_at - timedelta(hours=24)).isoformat(),
    )
    request = _authorization(profile_rows=(profile,))
    routing = derive_effective_profile_routing(
        _inventory(request.snapshot_payload, "institution_site_profiles").pages[0].rows[0].row_fingerprint,
        _inventory(request.snapshot_payload, "institution_site_profiles").pages[0].rows[0].row,
        _inventory(request.snapshot_payload, "institutions").pages[0].rows[0].row_fingerprint,
        _inventory(request.snapshot_payload, "institutions").pages[0].rows[0].row,
        routing_start,
    )
    assert routing.circuit_effective_open is True
    assert routing.eligible is False
    assert request.evaluated_at == evaluated_at
    assert authorize_future_adapter(request).reason == TRUST_STOP


@pytest.mark.parametrize("opened_at", ("not-a-timestamp", "2026-08-15T12:00:00"))
def test_circuit_opened_at_must_be_well_formed_utc(opened_at: str) -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-circuit-invalid",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        circuit_open=True,
        circuit_opened_at=opened_at,
    )
    _reason(
        lambda: authorize_future_adapter(_authorization(profile_rows=(profile,))),
        STOP_PROFILE_ROUTING_INVALID,
    )


def test_dormant_circuit_timestamp_is_fingerprinted_without_parsing() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-circuit-dormant",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        circuit_open=False,
        circuit_opened_at="dormant-malformed-timestamp",
    )
    request = _authorization(profile_rows=(profile,))
    routing = _routing_for(request)
    assert routing.circuit_opened_at == "dormant-malformed-timestamp"
    assert routing.circuit_effective_open is False
    assert authorize_future_adapter(request).reason == TRUST_STOP


def test_noneligible_profile_binds_config_without_deriving_invalid_active_targets() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-disabled",
        institution_id="institution-001",
        discovery_enabled=False,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("not a valid target",),
        catalog_max_pages=-99,
        warmup_url="also not a valid target",
        circuit_open=False,
    )
    request = _authorization(profile_rows=(profile,))
    routing = _routing_for(request)
    assert routing.eligible is False
    assert routing.static_targets == ()
    assert authorize_future_adapter(request).reason == TRUST_STOP


def test_noneligible_profile_still_rejects_unsafe_fingerprint_configuration() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-disabled-unsafe",
        institution_id="institution-001",
        discovery_enabled=False,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("not a valid target",),
        allowed_url_patterns=("re:(a+)+",),
        circuit_open=False,
    )
    _reason(
        lambda: authorize_future_adapter(_authorization(profile_rows=(profile,))),
        STOP_PROFILE_ROUTING_INVALID,
    )


def test_invalid_active_target_blocks_only_when_profile_is_eligible() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-active-invalid",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://user:password@institution-1.example.invalid/course",),
        circuit_open=False,
    )
    _reason(
        lambda: authorize_future_adapter(_authorization(profile_rows=(profile,))),
        STOP_PROFILE_ROUTING_INVALID,
    )


@pytest.mark.parametrize("mode", ("hardcoded_urls", "sitemap_bfs"))
def test_hardcoded_and_sitemap_do_not_invent_preflight_pattern_requirements(
    mode: str,
) -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-real-harvester",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode=mode,
        seed_urls=(),
        allowed_url_patterns=(),
        exclusion_patterns=(),
        circuit_open=False,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert tuple(item.kind for item in routing.static_targets) == (
        "SITEMAP_ROOT",
        "BFS_ROOT",
    )


def test_profile_regex_search_text_is_limited_to_2000_characters() -> None:
    long_path = "/" + "a" * 2000 + "blocked"
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-regex-limit",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=(f"https://institution-1.example.invalid{long_path}",),
        exclusion_patterns=("re:blocked$",),
        circuit_open=False,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert len(routing.static_targets) == 1


def test_profile_literal_filter_uses_the_complete_url() -> None:
    long_path = "/" + "a" * 2100 + "blocked"
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-literal-full",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=(f"https://institution-1.example.invalid{long_path}",),
        exclusion_patterns=("blocked",),
        circuit_open=False,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert routing.static_targets == ()


def test_linear_regex_subset_keeps_anchors_and_character_classes() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-linear-regex",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/a/course",),
        allowed_url_patterns=("re:^/[a-z]/course$",),
        circuit_open=False,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert len(routing.static_targets) == 1


@pytest.mark.parametrize(
    "expression",
    ("(a|aa)+$", "a*a*a*a*a*a*b", "a+a+a+a+a+a+b", "a?a?a?a?a?a?b"),
)
def test_hostile_quantifiers_are_rejected_before_regex_engine_execution(
    expression: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def forbidden_compile(*_args, **_kwargs):
        calls.append("compile")
        raise AssertionError("hostile regex reached compiler")

    def forbidden_search(*_args, **_kwargs):
        calls.append("search")
        raise AssertionError("hostile regex reached search")

    monkeypatch.setattr(contract.re, "compile", forbidden_compile)
    monkeypatch.setattr(contract.re, "search", forbidden_search)
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-hostile-regex",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/" + "a" * 2000 + "!",),
        allowed_url_patterns=(f"re:{expression}",),
        circuit_open=False,
    )
    _reason(
        lambda: authorize_future_adapter(_authorization(profile_rows=(profile,))),
        STOP_PROFILE_ROUTING_INVALID,
    )
    assert calls == []


def test_profile_institution_join_is_exact_one() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-orphan",
        institution_id="missing-institution",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="hardcoded_urls",
        seed_urls=("https://institution-1.example.invalid/course",),
        circuit_open=False,
    )
    # The fixture joins institutions from profiles; force a cross-id mismatch at the pure helper.
    request = _authorization()
    valid_profile = _inventory(request.snapshot_payload, "institution_site_profiles").pages[0].rows[0]
    institution = _inventory(request.snapshot_payload, "institutions").pages[0].rows[0]
    _reason(
        lambda: derive_effective_profile_routing(
            valid_profile.row_fingerprint,
            profile,
            institution.row_fingerprint,
            institution.row,
            request.evaluated_at,
        ),
        STOP_PROFILE_ROUTING_INVALID,
    )


@pytest.mark.parametrize("case", ("missing", "duplicate", "contradictory"))
def test_profile_institution_join_rejects_missing_duplicate_and_contradictory(
    case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _authorization()
    profile = _inventory(request.snapshot_payload, "institution_site_profiles").pages[0].rows[0].row
    institution = _inventory(request.snapshot_payload, "institutions").pages[0].rows[0].row
    if case == "missing":
        profiles, institutions = (profile,), ()
    elif case == "duplicate":
        profiles, institutions = (profile, profile), (institution,)
    else:
        contradictory = FrozenRow(
            tuple(
                (key, "different-institution" if key == "institution_id" else value)
                for key, value in profile.values
            )
        )
        profiles, institutions = (contradictory,), (institution,)

    def inventory_rows(_payload, _snapshot, table, _reason):
        return profiles if table == "institution_site_profiles" else institutions

    monkeypatch.setattr(contract, "_inventory_rows", inventory_rows)
    _reason(
        lambda: contract._eligible_profile_sources(
            request.target, request.snapshot_payload, request.evaluated_at
        ),
        STOP_PROFILE_ROUTING_INVALID,
    )


def test_paginated_catalog_without_placeholder_follows_harvester_and_deduplicates() -> None:
    profile = _frozen_row(
        "institution_site_profiles",
        id="profile-template",
        institution_id="institution-001",
        discovery_enabled=True,
        pipeline_enabled=True,
        pipeline_ready=True,
        discovery_mode="paginated_catalog",
        catalog_url_patterns=("https://institution-1.example.invalid/catalog",),
        circuit_open=False,
    )
    routing = _routing_for(_authorization(profile_rows=(profile,)))
    assert tuple((item.kind, item.url) for item in routing.static_targets) == (
        ("CATALOG_PAGE", "https://institution-1.example.invalid/catalog"),
    )


def test_multiple_profiles_and_multiple_configured_sources_are_exactly_covered() -> None:
    profiles = (
        _frozen_row(
            "institution_site_profiles",
            id="profile-001",
            institution_id="institution-001",
            discovery_enabled=True,
            pipeline_enabled=True,
            pipeline_ready=False,
            discovery_mode="sitemap_bfs",
            seed_urls=("https://dormant-a.invalid", "https://dormant-b.invalid"),
            catalog_url_patterns=("https://dormant.invalid/{page}",),
            allowed_url_patterns=("private-allowed-a",),
            circuit_open=False,
        ),
        _frozen_row(
            "institution_site_profiles",
            id="profile-002",
            institution_id="institution-002",
            discovery_enabled=True,
            pipeline_enabled=True,
            pipeline_ready=True,
            discovery_mode="hardcoded_urls",
            seed_urls=("https://institution-2.example.invalid/course",),
            catalog_url_patterns=(),
            allowed_url_patterns=("/course",),
            circuit_open=False,
        ),
    )
    request = _authorization(profile_rows=profiles)
    assert len(request.source_observations) == 3
    assert authorize_future_adapter(request).reason == TRUST_STOP
    _reason(
        lambda: authorize_future_adapter(
            replace(request, source_observations=request.source_observations[:-1])
        ),
        STOP_SOURCE_BLOCKERS_PRESENT,
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
        STOP_SOURCE_BLOCKERS_PRESENT,
    )


@pytest.mark.parametrize("sequence", SOURCE_ATTEMPT_GRAMMAR)
def test_every_accepted_head_get_sequence_reaches_trust_stop(
    sequence: tuple[str, ...],
) -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    timings = tuple(
        SourceAttemptResult(
            method,
            NOW + timedelta(microseconds=1_000 + index * 200),
            NOW + timedelta(microseconds=1_100 + index * 200),
            1_000_000 + index * 200_000,
            1_100_000 + index * 200_000,
            403 if method == "HEAD" and len(sequence) == 2 else 200,
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
            attempt_results=timings,
            attempts=len(sequence),
            observed_at=timings[-1].ended_at_utc,
        ),
    )
    assert authorize_future_adapter(
        replace(request, source_observations=(updated,))
    ).reason == TRUST_STOP


@pytest.mark.parametrize(
    "head_status,get_status,error_class,terminal",
    (
        (200, None, "NONE", "SOURCE_ACCESSIBLE"),
        (404, None, "NONE", "SOURCE_HTTP_404"),
        (410, None, "NONE", "SOURCE_HTTP_410"),
        (418, None, "NONE", "SOURCE_INACCESSIBLE"),
        (403, 403, "NONE", "SOURCE_ACCESS_403"),
        (405, 200, "NONE", "SOURCE_ACCESSIBLE"),
        (501, 404, "NONE", "SOURCE_HTTP_404"),
        (429, None, "NONE", "SOURCE_TIMEOUT"),
        (None, None, "DNS_FAILURE", "SOURCE_DNS_FAILURE"),
        (None, None, "TLS_FAILURE", "SOURCE_TLS_FAILURE"),
        (None, None, "TRANSPORT_FAILURE", "SOURCE_TRANSPORT_FAILURE"),
    ),
)
def test_source_terminal_reason_is_recomputed_from_closed_attempt_results(
    head_status: int | None,
    get_status: int | None,
    error_class: str,
    terminal: str,
) -> None:
    head = SourceAttemptResult("HEAD", NOW, NOW + timedelta(microseconds=1), 1, 1001, head_status, error_class)
    results = (head,)
    if get_status is not None:
        results += (
            SourceAttemptResult("GET", NOW + timedelta(microseconds=2), NOW + timedelta(microseconds=3), 2001, 3001, get_status),
        )
    assert source_terminal_reason(results) == terminal


def test_non_accessible_source_is_structurally_valid_but_blocks_authorization() -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    head, get = bundle.evidence.attempt_results
    blocked = replace(
        bundle,
        evidence=replace(
            bundle.evidence,
            attempt_results=(head, replace(get, status_code=403)),
            terminal_reason="SOURCE_ACCESS_403",
        ),
    )
    validate_source_observation(
        blocked.request,
        blocked.evidence,
        request.target,
        request.snapshot_payload,
        request.evaluated_at,
    )
    _reason(
        lambda: authorize_future_adapter(replace(request, source_observations=(blocked,))),
        STOP_SOURCE_BLOCKERS_PRESENT,
    )
    assert GO_COMPATIBLE_SOURCE_TERMINALS == frozenset({"SOURCE_ACCESSIBLE"})


def test_source_terminal_result_mismatch_is_a_source_blocker() -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    mismatch = replace(
        bundle,
        evidence=replace(bundle.evidence, terminal_reason="SOURCE_ACCESS_403"),
    )
    _reason(
        lambda: validate_source_observation(
            mismatch.request,
            mismatch.evidence,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_SOURCE_BLOCKERS_PRESENT,
    )


@pytest.mark.parametrize("classification", ("SAME_ORIGIN_PUBLIC", "OTHER_PUBLIC"))
def test_redirect_classification_requires_derivation_evidence_not_present_in_v2_3(
    classification: str,
) -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    head, get = bundle.evidence.attempt_results
    unsupported = replace(
        bundle.evidence,
        attempt_results=(head, replace(get, redirect_classification=classification)),
    )
    assert REDIRECT_EVIDENCE_POLICY == "NO_REDIRECT_WITHOUT_DERIVATION_EVIDENCE"
    _reason(
        lambda: validate_source_observation(
            bundle.request,
            unsupported,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_TARGET_BINDING_INVALID,
    )


@pytest.mark.parametrize(
    "sequence",
    (
        ("GET",),
        ("GET", "HEAD"),
        ("HEAD", "GET", "HEAD"),
        ("HEAD", "HEAD", "GET"),
        ("HEAD", "GET", "GET"),
        ("HEAD", "HEAD", "HEAD", "GET"),
    ),
)
def test_every_rejected_head_get_sequence_has_stable_reason(
    sequence: tuple[str, ...],
) -> None:
    request = _authorization()
    bundle = request.source_observations[0]
    timing = bundle.evidence.attempt_results[0]
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
            attempt_results=timings,
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
                SourceAttemptResult(
                    method,
                    NOW + timedelta(microseconds=1_000 + index * 200),
                    NOW + timedelta(microseconds=1_100 + index * 200),
                    1_000_000 + index * 200_000,
                    1_100_000 + index * 200_000,
                    403 if method == "HEAD" and sequence == ("HEAD", "GET") else 200,
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
                attempt_results=timings,
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
    institution = _inventory(request.snapshot_payload, "institutions").pages[0].rows[0]
    values = dict(profile.row.values)
    values["discovery_mode"] = "paginated_catalog"
    values["catalog_url_patterns"] = ("https://institution-1.example.invalid/page/{page}",)
    values["catalog_max_pages"] = MAX_SOURCES_PER_PROFILE + 1
    oversized = FrozenRow(
        tuple((column, values[column]) for column in TABLE_COLUMNS["institution_site_profiles"])
    )
    _reason(
        lambda: profile_source_fingerprints(
            profile.row_fingerprint,
            oversized,
            institution.row_fingerprint,
            institution.row,
            request.evaluated_at,
        ),
        STOP_TARGET_BINDING_INVALID,
    )


def test_profile_source_cardinality_accepts_exact_limit() -> None:
    request = _authorization()
    profile = _inventory(
        request.snapshot_payload, "institution_site_profiles"
    ).pages[0].rows[0]
    institution = _inventory(request.snapshot_payload, "institutions").pages[0].rows[0]
    values = dict(profile.row.values)
    values["discovery_mode"] = "paginated_catalog"
    values["catalog_url_patterns"] = ("https://institution-1.example.invalid/page/{page}",)
    values["catalog_max_pages"] = MAX_SOURCES_PER_PROFILE
    exact = FrozenRow(
        tuple((column, values[column]) for column in TABLE_COLUMNS["institution_site_profiles"])
    )
    assert len(
        profile_source_fingerprints(
            profile.row_fingerprint,
            exact,
            institution.row_fingerprint,
            institution.row,
            request.evaluated_at,
        )
    ) == 64


def test_global_profile_source_cardinality_exact_and_plus_one(monkeypatch) -> None:
    assert contract.MAX_PROFILE_SOURCE_PAIRS == 50_000
    contract._enforce_profile_source_pair_limit(50_000)
    _reason(
        lambda: contract._enforce_profile_source_pair_limit(50_001),
        STOP_TARGET_BINDING_INVALID,
    )
    monkeypatch.setattr(contract, "MAX_PROFILE_SOURCE_PAIRS", 2)
    contract._enforce_profile_source_pair_limit(2)
    _reason(
        lambda: contract._enforce_profile_source_pair_limit(3),
        STOP_TARGET_BINDING_INVALID,
    )


def test_fg3_historical_cardinality_is_bounded_before_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert MAX_FG3_HISTORICAL_OBSERVATIONS == 50_000
    contract._enforce_fg3_historical_observation_limit(50_000)
    _reason(
        lambda: contract._enforce_fg3_historical_observation_limit(50_001),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )
    monkeypatch.setattr(contract, "MAX_FG3_HISTORICAL_OBSERVATIONS", 2)
    contract._enforce_fg3_historical_observation_limit(2)
    _reason(
        lambda: contract._enforce_fg3_historical_observation_limit(3),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


def test_fg3_courses_and_prior_mutations_share_early_50000_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract._enforce_fg3_collection_limit(50_000)
    _reason(
        lambda: contract._enforce_fg3_collection_limit(50_001),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )
    monkeypatch.setattr(contract, "MAX_FG3_HISTORICAL_OBSERVATIONS", 2)
    contract._enforce_fg3_collection_limit(2)
    _reason(
        lambda: contract._enforce_fg3_collection_limit(3),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


def test_manifest_category_counts_cardinality_is_exactly_three() -> None:
    request = _authorization()
    malformed = replace(
        request.historical_manifest,
        category_counts=(*request.historical_manifest.category_counts, ("EXTRA", 0)),
    )
    _reason(
        lambda: historical_manifest_digest(malformed),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
    out_of_order = (replace(head, method="GET"), replace(get, method="HEAD"))
    _reason(
        lambda: authorize_future_adapter(
            _with_source_timings(request, out_of_order)
        ),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_attempt_utc_and_monotonic_durations_must_agree() -> None:
    request = _authorization()
    head, get = request.source_observations[0].evidence.attempt_results
    head = replace(head, monotonic_ended_ns=head.monotonic_ended_ns + 250_000_001)
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head, get))),
        STOP_CLOCK_TIMING_INVALID,
    )


def test_source_timing_count_must_equal_method_sequence() -> None:
    request = _authorization()
    head, _ = request.source_observations[0].evidence.attempt_results
    _reason(
        lambda: authorize_future_adapter(_with_source_timings(request, (head,))),
        STOP_CLOCK_TIMING_INVALID,
    )
    head, get = request.source_observations[0].evidence.attempt_results
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
    timings = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
        STOP_SOURCE_BLOCKERS_PRESENT,
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
        STOP_SOURCE_BLOCKERS_PRESENT,
    )


def test_extra_bundle_cannot_forge_an_earlier_routing_instant() -> None:
    request = _authorization()
    original = request.source_observations[0]
    shifted_results = tuple(
        replace(
            result,
            started_at_utc=result.started_at_utc - timedelta(microseconds=100),
            ended_at_utc=result.ended_at_utc - timedelta(microseconds=100),
            monotonic_started_ns=result.monotonic_started_ns - 100_000,
            monotonic_ended_ns=result.monotonic_ended_ns - 100_000,
        )
        for result in original.evidence.attempt_results
    )
    extra = replace(
        original,
        request=replace(original.request, source_fingerprint=DIGESTS[45]),
        evidence=replace(
            original.evidence,
            source_fingerprint=DIGESTS[45],
            attempt_results=shifted_results,
            observed_at=shifted_results[-1].ended_at_utc,
        ),
    )
    _reason(
        lambda: validate_source_coverage(
            (original, extra),
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_SOURCE_BLOCKERS_PRESENT,
    )
    _reason(
        lambda: validate_source_coverage(
            request.source_observations * 2,
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_SOURCE_BLOCKERS_PRESENT,
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
        STOP_SOURCE_BLOCKERS_PRESENT,
    )


def test_historical_observations_and_prior_mutation_are_recomputed_and_predate_snapshot() -> None:
    request = _authorization()
    assert len(request.fg3_cohort.historical_observations) == 28
    assert len({item.observation_fingerprint for item in request.fg3_cohort.historical_observations}) == 28
    assert len({item.course_fingerprint for item in request.fg3_cohort.historical_observations}) == 4
    assert len(request.fg3_cohort.prior_mutations) == 2
    assert len({item.course_fingerprint for item in request.fg3_cohort.prior_mutations}) == 2
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
    head, get = request.source_observations[0].evidence.attempt_results
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
        15_000_000_000,
    )
    validate_read_timing(exact_budget, PAIR_ID)
    _reason(
        lambda: validate_read_timing(
            replace(exact_budget, monotonic_ended_ns=15_000_000_001),
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
    assert SOURCE_ATTEMPT_BUDGET_NS == 15_000_000_000
    request = _authorization()
    payload, target = _shift_second_snapshot(
        request.snapshot_payload, request.target, timedelta(seconds=20)
    )
    bundle = request.source_observations[0]
    exact_budget = (
        SourceAttemptResult(
            "HEAD",
            NOW + timedelta(milliseconds=1),
            NOW + timedelta(seconds=15, milliseconds=1),
            1_000_000,
            15_001_000_000,
            403,
        ),
        SourceAttemptResult(
            "GET",
            NOW + timedelta(seconds=15, milliseconds=100),
            NOW + timedelta(seconds=15, milliseconds=200),
            15_100_000_000,
            15_200_000_000,
            200,
        ),
    )

    def validate(timings: tuple[SourceAttemptResult, ...]) -> None:
        validate_source_observation(
            bundle.request,
            replace(
                bundle.evidence,
                attempt_results=timings,
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
        SourceAttemptResult(
            "HEAD",
            NOW + timedelta(milliseconds=1),
            NOW + timedelta(seconds=1, milliseconds=1),
            1_000_000,
            1_251_000_000,
            403,
        ),
        SourceAttemptResult(
            "GET",
            NOW + timedelta(seconds=2),
            NOW + timedelta(seconds=2, milliseconds=100),
            2_000_000_000,
            2_100_000_000,
            200,
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
        SourceAttemptResult(
            "HEAD",
            NOW + timedelta(milliseconds=1),
            NOW + timedelta(seconds=1, milliseconds=1),
            1_000_000,
            751_000_000,
            403,
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
    observation = next(
        item
        for item in request.fg3_cohort.historical_observations
        if item.observation_fingerprint == mutation.historical_observation_fingerprint
    )
    assert mutation.course_fingerprint == observation.course_fingerprint
    assert mutation.antecedent_run_fingerprint == observation.run_id
    assert mutation.antecedent_observed_at == observation.observed_at
    assert observation.category in {"DEACTIVATION", "PRIOR_DEACTIVATION"}
    assert mutation.mutation_kind == "DEACTIVATION"
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


def test_extra_active_deactivation_observation_is_rejected() -> None:
    request = _authorization()
    active_course = request.fg3_cohort.courses[0]
    extra = FG3HistoricalObservationEvidence(
        observation_fingerprint="",
        target_binding_digest=evidence_binding_digest(request.target),
        snapshot_pair_id=request.target.snapshot_pair_id,
        course_fingerprint=active_course.course_fingerprint,
        run_id=DIGESTS[40],
        category="PRIOR_DEACTIVATION",
        active_at_snapshot_1=True,
        observed_at=NOW - timedelta(seconds=45),
    )
    extra = replace(extra, observation_fingerprint=historical_observation_fingerprint(extra))
    _reason(
        lambda: validate_fg3_cohort(
            replace(
                request.fg3_cohort,
                historical_observations=(*request.fg3_cohort.historical_observations, extra),
            ),
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        ),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


def test_unreferenced_deactivation_observation_is_rejected_exact_one() -> None:
    request = _authorization()
    assert len(request.fg3_cohort.historical_observations) == 27 + max(
        0,
        sum(not course.active_at_snapshot_1 for course in request.fg3_cohort.courses) - 1,
    )
    _reason(
        lambda: validate_fg3_cohort(
            replace(
                request.fg3_cohort,
                prior_mutations=request.fg3_cohort.prior_mutations[:-1],
            ),
            request.historical_manifest,
            request.target,
            request.snapshot_payload,
        ),
        STOP_MANIFEST_ANCHOR_MISMATCH,
    )


@pytest.mark.parametrize(
    "course_index,value",
    ((1, 0), (1, 1), (3, 0), (3, 1), (4, 0), (4, 1)),
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
        created_at=(NOW - timedelta(hours=24)).isoformat(),
        observed_at=NOW,
    )
    stale = classify_lifecycle_proxy(
        last_harvested_at=None,
        created_at=(NOW - timedelta(hours=24, microseconds=1)).isoformat(),
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
        last_harvested_at=(NOW - timedelta(hours=24, microseconds=1)).isoformat(),
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
            STOP_LIFECYCLE_BLOCKERS_PRESENT,
        )
    _reason(
        lambda: validate_lifecycle_evidence(
            (LifecycleEvidence(DIGESTS[90], current),),
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_LIFECYCLE_BLOCKERS_PRESENT,
    )


def test_lifecycle_proxy_mismatch_is_a_lifecycle_blocker() -> None:
    request = _authorization()
    item = request.lifecycle_evidence[0]
    mismatch = replace(
        item.proxy,
        timestamp_used=(request.evaluated_at - timedelta(hours=1)).isoformat(),
    )
    _reason(
        lambda: validate_lifecycle_evidence(
            (replace(item, proxy=mismatch),),
            request.target,
            request.snapshot_payload,
            request.evaluated_at,
        ),
        STOP_LIFECYCLE_BLOCKERS_PRESENT,
    )


@pytest.mark.parametrize("classification", ("STALE", "AGE_UNKNOWN", "FUTURE_TIMESTAMP"))
def test_lifecycle_blockers_stop_before_trust(classification: str) -> None:
    request = _authorization()
    if classification == "STALE":
        changed = classify_lifecycle_proxy(
            last_harvested_at=(request.evaluated_at - timedelta(hours=24, microseconds=1)).isoformat(),
            created_at=None,
            observed_at=request.evaluated_at,
        )
    elif classification == "AGE_UNKNOWN":
        changed = classify_lifecycle_proxy(
            last_harvested_at=None, created_at=None, observed_at=request.evaluated_at
        )
    else:
        changed = classify_lifecycle_proxy(
            last_harvested_at=(request.evaluated_at + timedelta(microseconds=1)).isoformat(),
            created_at=None,
            observed_at=request.evaluated_at,
        )
    assert changed.classification == classification
    _reason(
        lambda: authorize_future_adapter(
            replace(
                request,
                lifecycle_evidence=(replace(request.lifecycle_evidence[0], proxy=changed),),
            )
        ),
        STOP_LIFECYCLE_BLOCKERS_PRESENT,
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
        object.__delattr__(malformed, "attempt_results")
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
        "supabase", "requests", "httpx", "socket", "subprocess",
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
