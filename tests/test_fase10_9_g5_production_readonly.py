from __future__ import annotations

import ast
import copy
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.shared.f10_9_g5_readonly_collector import (
    AGGREGATE_DEFINITIONS,
    ALGORITHM_VERSION,
    ALGORITHM_VERSION_V1,
    EXCLUDED_SURFACES,
    LEGACY_ALGORITHM_VERSION_V1,
    LEGACY_SCHEMA_V1,
    REASON_DEFINITIONS,
    SCHEMA,
    SCHEMA_V1,
    SNAPSHOT_DECLARATION,
    CandidateBinding,
    ConnectedAuthorization,
    FG3Observation,
    G5Error,
    G5ReadOnlyFacade,
    GATE,
    GATE_CANDIDATE_STATUS,
    HashObservation,
    HistoricalFG3Anchor,
    HistoricalFG3Manifest,
    InventoryObservation,
    PrivateObservations,
    ProcessingLifecycleObservation,
    SnapshotPairEvidence,
    SourceObservation,
    collect_g5_connected,
    collect_g5_projection as _collect_g5_projection,
    fg3_cohort_fingerprint,
    historical_manifest_fingerprint,
    historical_observation_fingerprint,
    mutation_fingerprint,
    profile_fingerprint,
    run_fingerprint,
    snapshot_fingerprint,
    snapshot_pair_fingerprint,
    source_cohort_fingerprint,
    source_fingerprint,
)


NOW = datetime(2026, 8, 14, 4, 30, tzinfo=timezone.utc)
RUN = "sha256:" + "1" * 64
SOURCE_COHORT = "sha256:" + "2" * 64
FG3_COHORT = "sha256:" + "3" * 64
PAIR_ID = "sha256:" + "4" * 64
BINDING = CandidateBinding(
    base_sha="30f77b88778372de112c6a8fb51a1344155db025",
    base_tree="b25fca6fc4e37db5b1e2c0e048748ee0ec3d839c",
    candidate_sha="a" * 40,
    candidate_tree="b" * 40,
    observed_at=NOW,
)
PAIR = SnapshotPairEvidence(
    snapshot_pair_id=PAIR_ID,
    snapshot_1_started_at=NOW - timedelta(minutes=6),
    snapshot_1_ended_at=NOW - timedelta(minutes=5),
    observations_started_at=NOW - timedelta(minutes=4),
    observations_ended_at=NOW + timedelta(minutes=4),
    snapshot_2_started_at=NOW + timedelta(minutes=5),
    snapshot_2_ended_at=NOW + timedelta(minutes=6),
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _tables() -> dict[str, list[dict[str, object]]]:
    institution = "private-institution"
    return {
        "institutions": [
            {
                "id": institution,
                "name": "Private Institution",
                "slug": "private-slug",
                "website_url": "https://private.example.invalid",
                "last_harvest_at": None,
            }
        ],
        "institution_site_profiles": [
            {
                "id": "private-profile",
                "institution_id": institution,
                "discovery_enabled": True,
                "pipeline_enabled": True,
                "pipeline_ready": True,
                "discovery_mode": "hardcoded_urls",
                "seed_urls": ["https://private.example.invalid/program"],
                "catalog_url_patterns": [],
                "allowed_url_patterns": ["/program"],
                "circuit_open": False,
                "circuit_opened_at": None,
            }
        ],
        "staging_raw": [
            {
                "id": "private-staging",
                "institution_id": institution,
                "url": "https://private.example.invalid/program/1",
                "status": "pending",
                "content_hash": _hash("payload"),
                "last_harvested_at": "2026-08-14T03:00:00Z",
                "created_at": "2026-08-14T02:00:00Z",
            }
        ],
        "cleansed_programs": [],
        "enriched_programs": [],
        "courses": [
            {
                "id": "private-course-active",
                "institution_id": institution,
                "url": "https://private.example.invalid/course?secret=value",
                "is_active": True,
                "last_404_at": None,
                "start_date": None,
            },
            {
                "id": "private-course-unrelated-inactive",
                "institution_id": institution,
                "url": "https://private.example.invalid/old-course",
                "is_active": False,
                "last_404_at": None,
                "start_date": None,
            },
        ],
    }


def _facade(tables, second=None):
    return G5ReadOnlyFacade(tables, tables if second is None else second)


def _lifecycle(row: dict[str, object]) -> ProcessingLifecycleObservation:
    raw = row.get("last_harvested_at")
    origin = "LAST_HARVESTED_AT_PROXY"
    if raw is None:
        raw = row.get("created_at")
        origin = "CREATED_AT_PROXY" if raw is not None else "NONE"
    if raw is None:
        return ProcessingLifecycleObservation(str(row["id"]), None, origin, None, "AGE_UNKNOWN")
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
            raise ValueError
    except ValueError:
        return ProcessingLifecycleObservation(str(row["id"]), str(raw), origin, None, "AGE_UNKNOWN")
    age = int((NOW - parsed).total_seconds())
    classification = "FUTURE_TIMESTAMP" if age < 0 else "STALE" if age > 604800 else "NOT_STALE"
    return ProcessingLifecycleObservation(
        str(row["id"]), parsed.isoformat(), origin, age, classification
    )


def _fg3(row: dict[str, object], classification="HEALTHY", **overrides) -> FG3Observation:
    values = {
        "course_id": str(row["id"]),
        "run_fingerprint": RUN,
        "cohort_fingerprint": FG3_COHORT,
        "observed_at": NOW,
        "pre_is_active": row["is_active"],
        "post_is_active": row["is_active"],
        "pre_last_404_at": row["last_404_at"],
        "post_last_404_at": row["last_404_at"],
        "classification": classification,
        "method_sequence": ("HEAD", "GET"),
        "attempts": 2,
        "mutation_kind": "NONE",
        "apply_outcome": "NOT_APPLIED_READ_ONLY",
        "exact_one_verified": False,
        "antecedent_run_fingerprint": None,
        "antecedent_mutation_fingerprint": None,
        "antecedent_applied_at": None,
    }
    values.update(overrides)
    if values["mutation_kind"] != "NONE":
        antecedent_run = values.get("antecedent_run_fingerprint") or "sha256:" + "5" * 64
        antecedent_at = values.get("antecedent_applied_at") or (
            PAIR.snapshot_1_started_at - timedelta(days=1)
        )
        values["antecedent_run_fingerprint"] = antecedent_run
        values["antecedent_applied_at"] = antecedent_at
        values["antecedent_mutation_fingerprint"] = mutation_fingerprint(
            str(values["course_id"]),
            str(antecedent_run),
            antecedent_at,
            str(values["mutation_kind"]),
            str(values["apply_outcome"]),
            bool(values["exact_one_verified"]),
        )
    return FG3Observation(**values)


def _observations(tables, *, second=None, inventory=None, source=None, fg3=None):
    second = tables if second is None else second
    pair = replace(
        PAIR,
        snapshot_pair_id=snapshot_pair_fingerprint(tables, second, PAIR, BINDING),
    )
    run = run_fingerprint(pair.snapshot_pair_id, BINDING)
    enabled_profiles = [
        profile
        for profile in tables["institution_site_profiles"]
        if profile["discovery_enabled"] and profile["pipeline_enabled"]
    ]
    source_cohort = source_cohort_fingerprint(
        tuple(profile_fingerprint(profile) for profile in enabled_profiles)
    )
    active = [row for row in tables["courses"] if row["is_active"]]
    raw_fg3 = tuple(_fg3(row) for row in active) if fg3 is None else tuple(fg3)
    prior_inactive = [
        item.course_id
        for item in raw_fg3
        if item.mutation_kind != "NONE"
        and not next(row for row in tables["courses"] if str(row["id"]) == item.course_id)[
            "is_active"
        ]
    ]
    fg3_cohort = fg3_cohort_fingerprint(
        tuple(str(row["id"]) for row in active), tuple(prior_inactive)
    )
    inventories = []
    sources = []
    for profile in enabled_profiles:
        common = {
            "institution_id": str(profile["institution_id"]),
            "profile_fingerprint": profile_fingerprint(profile),
            "source_fingerprint": source_fingerprint(profile),
            "attempts": 1,
            "observed_at": NOW,
            "run_fingerprint": run,
            "cohort_fingerprint": source_cohort,
        }
        inventories.append(
            InventoryObservation(
                **common,
                stage="INVENTORY_QUERY",
                terminal_reason=inventory or "INVENTORY_OK",
                method_sequence=(),
            )
        )
        sources.append(
            SourceObservation(
                **{**common, "attempts": 2},
                stage="GET",
                terminal_reason=source or "SOURCE_ACCESSIBLE",
                method_sequence=("HEAD", "GET"),
            )
        )
    processing = [row for row in tables["staging_raw"] if row["status"] == "processing"]
    bound_fg3 = tuple(
        replace(item, run_fingerprint=run, cohort_fingerprint=fg3_cohort)
        for item in raw_fg3
    )
    historical = tuple(
        historical_observation_fingerprint(item)
        for item in bound_fg3
        if item.mutation_kind != "NONE"
        or item.classification
        in {"GET_403", "TIMEOUT", "DNS_FAILURE", "TLS_FAILURE", "TRANSPORT_FAILURE"}
    )
    manifest = HistoricalFG3Manifest(
        manifest_fingerprint=historical_manifest_fingerprint(True, historical),
        complete=True,
        expected_observation_fingerprints=historical,
    )
    return PrivateObservations(
        snapshot_fingerprint=snapshot_fingerprint(tables),
        base_sha=BINDING.base_sha,
        base_tree=BINDING.base_tree,
        candidate_sha=BINDING.candidate_sha,
        candidate_tree=BINDING.candidate_tree,
        observed_at=NOW,
        run_fingerprint=run,
        source_cohort_fingerprint=source_cohort,
        fg3_cohort_fingerprint=fg3_cohort,
        fg3_historical_manifest=manifest,
        pair=pair,
        inventories=tuple(inventories),
        sources=tuple(sources),
        fg3=bound_fg3,
        hashes=tuple(
            HashObservation(str(row["id"]), bool(row.get("content_hash")))
            for row in tables["staging_raw"]
            if row["status"] in {"pending", "processing", "processed"}
        ),
        lifecycle=tuple(_lifecycle(row) for row in processing),
    )


def _plain(value):
    if isinstance(value, dict) or hasattr(value, "items"):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def collect_g5_projection(facade, observations, binding, **kwargs):
    anchor = HistoricalFG3Anchor(
        expected_manifest_fingerprint=(
            observations.fg3_historical_manifest.manifest_fingerprint
        ),
        base_sha=binding.base_sha,
        base_tree=binding.base_tree,
        candidate_sha=binding.candidate_sha,
        candidate_tree=binding.candidate_tree,
    )
    return _collect_g5_projection(
        facade,
        observations,
        binding,
        historical_anchor=anchor,
        **kwargs,
    )


def test_v1_is_explicit_legacy_and_v2_is_active() -> None:
    assert SCHEMA_V1 == LEGACY_SCHEMA_V1 and SCHEMA.endswith(".v2")
    assert ALGORITHM_VERSION_V1 == LEGACY_ALGORITHM_VERSION_V1
    assert ALGORITHM_VERSION.endswith("-v2")


def test_facade_scope_stable_pagination_and_limits() -> None:
    tables = _tables()
    facade = _facade(tables)
    assert set(name for name in dir(facade) if not name.startswith("_")) == {"count", "select"}
    with pytest.raises(G5Error, match="STOP_G5_FACADE_SCOPE"):
        facade.select(0, "courses", columns="id,url", limit=1, offset=0, order="id.asc")
    with pytest.raises(G5Error, match="STOP_G5_FACADE_SCOPE"):
        facade.select(0, "courses", columns="id,institution_id,url,is_active,last_404_at,start_date", limit=1001, offset=0, order="id.asc")
    for index in range(1004):
        row = copy.deepcopy(tables["staging_raw"][0])
        row["id"] = f"page-{index:04d}"
        row["url"] = f"https://private.example.invalid/unique/{index}"
        tables["staging_raw"].append(row)
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    assert result["snapshot_pair"]["tables"]["staging_raw"]["pages"] == (2, 2)


def test_snapshot_pair_timing_fingerprints_and_drift() -> None:
    tables = _tables()
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    pair = result["snapshot_pair"]
    assert pair["snapshot_pair_id"] == _observations(tables).pair.snapshot_pair_id
    assert pair["declaration"] == SNAPSHOT_DECLARATION
    assert pair["sequence"] == ("snapshot_1", "observations", "snapshot_2")
    assert pair["global"]["initial_count"] == pair["global"]["final_count"]
    assert pair["global"]["initial_fingerprint"] == pair["global"]["final_fingerprint"]
    for evidence in pair["tables"].values():
        assert evidence["initial_count"] == evidence["final_count"]
        assert evidence["initial_fingerprint"] == evidence["final_fingerprint"]

    bad_pair = replace(PAIR, snapshot_2_started_at=NOW - timedelta(minutes=7))
    with pytest.raises(G5Error, match="STOP_G5_SNAPSHOT_PAIR_ORDER_INVALID"):
        collect_g5_projection(
            _facade(tables), replace(_observations(tables), pair=bad_pair), BINDING
        )
    second = copy.deepcopy(tables)
    second["staging_raw"][0]["status"] = "processed"
    drift = collect_g5_projection(
        _facade(tables, second), _observations(tables, second=second), BINDING
    )
    assert drift["decision"] == "STOP"
    assert drift["reason_codes"] == {"STOP_G5_SNAPSHOT_DRIFT": 1}
    assert drift["aggregates"] == {}

    for mutation in ("add", "remove", "active", "last_404"):
        changed = copy.deepcopy(tables)
        if mutation == "add":
            extra = copy.deepcopy(changed["courses"][0])
            extra["id"] = "drift-extra"
            changed["courses"].append(extra)
        elif mutation == "remove":
            changed["courses"].pop()
        elif mutation == "active":
            changed["courses"][0]["is_active"] = False
        else:
            changed["courses"][0]["last_404_at"] = "2026-08-14T04:00:00Z"
        observations = _observations(tables, second=changed)
        result = collect_g5_projection(_facade(tables, changed), observations, BINDING)
        assert result["reason_codes"] == {"STOP_G5_SNAPSHOT_DRIFT": 1}

    observations = _observations(tables)
    with pytest.raises(G5Error, match="STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED"):
        collect_g5_projection(
            _facade(tables),
            replace(
                observations,
                pair=replace(observations.pair, snapshot_pair_id="sha256:" + "f" * 64),
            ),
            BINDING,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("profile_fingerprint", "sha256:" + "9" * 64),
        ("source_fingerprint", "sha256:" + "8" * 64),
        ("stage", "SOURCE"),
        ("method_sequence", ("GET",)),
        ("attempts", 0),
        ("observed_at", NOW.replace(tzinfo=None)),
        ("run_fingerprint", "sha256:" + "7" * 64),
    ],
)
def test_inventory_attribution_is_independent_and_exact(field, value) -> None:
    tables = _tables()
    observations = _observations(tables)
    bad = replace(observations.inventories[0], **{field: value})
    with pytest.raises(G5Error, match="STOP_G5_PRIVATE_OBSERVATION_INVALID"):
        collect_g5_projection(
            _facade(tables), replace(observations, inventories=(bad,)), BINDING
        )


@pytest.mark.parametrize(
    "code",
    [
        "INVENTORY_QUERY_FAILED",
        "INVENTORY_INCOMPLETE",
        "SOURCE_GET_403",
        "SOURCE_TIMEOUT",
        "SOURCE_DNS_FAILURE",
        "SOURCE_TLS_FAILURE",
        "SOURCE_TRANSPORT_FAILURE",
    ],
)
def test_closed_inventory_and_source_terminal_reasons(code) -> None:
    tables = _tables()
    kwargs = {"inventory": code} if code.startswith("INVENTORY") else {"source": code}
    result = collect_g5_projection(_facade(tables), _observations(tables, **kwargs), BINDING)
    assert result["decision"] == "STOP"
    assert result["reason_codes"][code] == 1


def test_multiple_profiles_per_institution_remain_independently_attributed() -> None:
    tables = _tables()
    profile = copy.deepcopy(tables["institution_site_profiles"][0])
    profile["id"] = "private-profile-second"
    profile["seed_urls"] = ["https://private.example.invalid/second"]
    tables["institution_site_profiles"].append(profile)
    observations = _observations(tables)
    assert len(observations.inventories) == 2
    assert len({item.profile_fingerprint for item in observations.inventories}) == 2
    result = collect_g5_projection(_facade(tables), observations, BINDING)
    assert result["denominator_values"]["enabled_profiles"] == 2


def test_http_sequence_and_attempt_limits_are_fail_closed() -> None:
    tables = _tables()
    observations = _observations(tables)
    head_source = replace(
        observations.sources[0], stage="HEAD", method_sequence=("HEAD",), attempts=1
    )
    head_fg3 = replace(
        observations.fg3[0], method_sequence=("HEAD",), attempts=1
    )
    result = collect_g5_projection(
        _facade(tables),
        replace(observations, sources=(head_source,), fg3=(head_fg3,)),
        BINDING,
    )
    assert result["decision"] == "PASS"

    for bad in (
        replace(head_fg3, classification="GET_404"),
        replace(observations.fg3[0], method_sequence=("HEAD",) * 4, attempts=4),
        replace(observations.fg3[0], attempts=3),
    ):
        with pytest.raises(G5Error, match="STOP_G5_PRIVATE_OBSERVATION_INVALID"):
            collect_g5_projection(
                _facade(tables), replace(observations, fg3=(bad,)), BINDING
            )


def test_processing_proxy_stale_unknown_future_and_exact_evidence() -> None:
    tables = _tables()
    base = tables["staging_raw"][0]
    rows = []
    for suffix, last, created in (
        ("stale", "2026-08-01T00:00:00Z", "2026-08-13T00:00:00Z"),
        ("unknown", "not-a-time", "2026-08-01T00:00:00Z"),
        ("future", "2026-08-15T00:00:00Z", None),
        ("fresh", None, "2026-08-14T03:00:00Z"),
    ):
        row = copy.deepcopy(base)
        row.update(
            {
                "id": suffix,
                "url": f"https://private.example.invalid/{suffix}",
                "status": "processing",
                "last_harvested_at": last,
                "created_at": created,
            }
        )
        rows.append(row)
    tables["staging_raw"] = rows
    observations = _observations(tables)
    result = collect_g5_projection(_facade(tables), observations, BINDING)
    assert result["aggregates"]["processing_stale"] == 1
    assert result["aggregates"]["processing_age_unknown"] == 1
    assert result["aggregates"]["processing_future_timestamp"] == 1
    assert result["aggregates"]["processing_not_stale"] == 1
    assert result["decision"] == "STOP"
    unknown = next(item for item in observations.lifecycle if item.staging_id == "unknown")
    assert unknown.timestamp_origin == "LAST_HARVESTED_AT_PROXY"
    assert unknown.classification == "AGE_UNKNOWN"
    with pytest.raises(G5Error, match="STOP_G5_LIFECYCLE_EVIDENCE_MISMATCH"):
        collect_g5_projection(
            _facade(tables),
            replace(
                observations,
                lifecycle=tuple(
                    replace(item, calculated_age_seconds=0)
                    if item.staging_id == "stale"
                    else item
                    for item in observations.lifecycle
                ),
            ),
            BINDING,
        )


def test_fg3_active_cohort_prior_mutation_and_unrelated_inactive_exclusion() -> None:
    tables = _tables()
    active, unrelated = tables["courses"]
    prior = copy.deepcopy(unrelated)
    prior.update(
        {
            "id": "private-prior-deactivation",
            "last_404_at": "2026-08-01T00:00:00Z",
            "url": "https://private.example.invalid/prior",
        }
    )
    tables["courses"].append(prior)
    observations = _observations(
        tables,
        fg3=(
            _fg3(active),
            _fg3(
                prior,
                "GET_410",
                mutation_kind="DEACTIVATE_PERSISTENT_GONE",
                apply_outcome="APPLIED_PRIOR_EXACT_ONE",
                exact_one_verified=True,
            ),
        ),
    )
    result = collect_g5_projection(_facade(tables), observations, BINDING)
    fg3 = result["aggregates"]
    assert fg3["fg3_evaluated_courses"] == 2
    assert fg3["fg3_active_before"] == 1
    assert fg3["fg3_active_after"] == 1
    assert fg3["deactivations_persistent_gone"] == 1
    assert fg3["prior_mutations_revalidated"] == 1
    assert "private-course-unrelated-inactive" not in json.dumps(_plain(result))


def test_fg3_404_410_and_inconclusive_reasons_are_separate() -> None:
    tables = _tables()
    active = tables["courses"][0]
    rows = []
    classifications = [
        "GET_404",
        "GET_410",
        "GET_403",
        "TIMEOUT",
        "DNS_FAILURE",
        "TLS_FAILURE",
        "TRANSPORT_FAILURE",
    ]
    for index, classification in enumerate(classifications):
        row = copy.deepcopy(active)
        row["id"] = f"course-{index}"
        row["url"] = f"https://private.example.invalid/course/{index}"
        rows.append(row)
    tables["courses"] = rows + [tables["courses"][1]]
    rows[0]["last_404_at"] = "2026-08-01T00:00:00Z"
    rows[1]["last_404_at"] = "2026-08-01T00:00:00Z"
    fg3 = []
    for row, code in zip(rows, classifications):
        mutation = (
            "FIRST_GET_404" if code == "GET_404" else
            "FIRST_GET_410" if code == "GET_410" else
            "NONE"
        )
        fg3.append(
            _fg3(
                row,
                code,
                mutation_kind=mutation,
                apply_outcome=(
                    "APPLIED_PRIOR_EXACT_ONE"
                    if mutation != "NONE"
                    else "NOT_APPLIED_READ_ONLY"
                ),
                exact_one_verified=mutation != "NONE",
            )
        )
    result = collect_g5_projection(
        _facade(tables),
        _observations(tables, fg3=tuple(fg3)),
        BINDING,
    )
    fg3 = result["aggregates"]
    assert fg3["first_get_404_observations"] == 1
    assert fg3["first_get_410_observations"] == 1
    assert fg3["fg3_inconclusive_total"] == 5
    assert fg3["fg3_inconclusive_by_reason"] == {
        "DNS_FAILURE": 1,
        "GET_403": 1,
        "TIMEOUT": 1,
        "TLS_FAILURE": 1,
        "TRANSPORT_FAILURE": 1,
    }


def test_fg3_prior_deactivation_recovery_and_inconclusive_are_attributed() -> None:
    tables = _tables()
    prior = tables["courses"][1]
    prior["last_404_at"] = "2026-08-01T00:00:00Z"
    antecedent = {
        "mutation_kind": "DEACTIVATE_PERSISTENT_GONE",
        "apply_outcome": "APPLIED_PRIOR_EXACT_ONE",
        "exact_one_verified": True,
    }
    healthy = _observations(
        tables,
        fg3=(
            _fg3(tables["courses"][0]),
            _fg3(prior, "HEALTHY", **antecedent),
        ),
    )
    result = collect_g5_projection(_facade(tables), healthy, BINDING)
    assert result["aggregates"]["recoveries_required"] == 1
    assert result["aggregates"]["prior_mutations_revalidated"] == 1
    assert result["aggregates"]["deactivations_persistent_gone"] == 0

    inconclusive = _observations(
        tables,
        fg3=(
            _fg3(tables["courses"][0]),
            _fg3(prior, "TIMEOUT", **antecedent),
        ),
    )
    result = collect_g5_projection(_facade(tables), inconclusive, BINDING)
    assert result["aggregates"]["recoveries_required"] == 0
    assert result["aggregates"]["prior_mutations_revalidated"] == 0
    assert result["aggregates"]["fg3_inconclusive_by_reason"] == {"TIMEOUT": 1}

    invalid = replace(
        healthy.fg3[1], antecedent_mutation_fingerprint="sha256:" + "e" * 64
    )
    with pytest.raises(G5Error, match="STOP_G5_PRIVATE_OBSERVATION_INVALID"):
        collect_g5_projection(
            _facade(tables), replace(healthy, fg3=(healthy.fg3[0], invalid)), BINDING
        )


def test_fg3_missing_historical_evidence_stops_before_publishing_counts() -> None:
    tables = _tables()
    observations = _observations(tables)
    incomplete = HistoricalFG3Manifest(
        manifest_fingerprint=historical_manifest_fingerprint(
            False,
            observations.fg3_historical_manifest.expected_observation_fingerprints,
        ),
        complete=False,
        expected_observation_fingerprints=(
            observations.fg3_historical_manifest.expected_observation_fingerprints
        ),
    )
    with pytest.raises(G5Error, match="STOP_G5_FG3_HISTORICAL_EVIDENCE_MISSING"):
        collect_g5_projection(
            _facade(tables),
            replace(observations, fg3_historical_manifest=incomplete),
            BINDING,
        )


def test_fg3_manifest_detects_omitted_historical_observation() -> None:
    tables = _tables()
    prior = tables["courses"][1]
    prior["last_404_at"] = "2026-08-01T00:00:00Z"
    observations = _observations(
        tables,
        fg3=(
            _fg3(tables["courses"][0]),
            _fg3(
                prior,
                "GET_410",
                mutation_kind="DEACTIVATE_PERSISTENT_GONE",
                apply_outcome="APPLIED_PRIOR_EXACT_ONE",
                exact_one_verified=True,
            ),
        ),
    )
    with pytest.raises(G5Error, match="STOP_G5_FG3_HISTORICAL_EVIDENCE_MISSING"):
        collect_g5_projection(
            _facade(tables), replace(observations, fg3=observations.fg3[:1]), BINDING
        )


def test_fg3_manifest_requires_independent_candidate_bound_anchor() -> None:
    tables = _tables()
    observations = _observations(tables)
    with pytest.raises(
        G5Error, match="STOP_G5_FG3_HISTORICAL_EVIDENCE_ANCHOR_MISSING"
    ):
        _collect_g5_projection(_facade(tables), observations, BINDING)
    bad_anchor = HistoricalFG3Anchor(
        expected_manifest_fingerprint="sha256:" + "f" * 64,
        base_sha=BINDING.base_sha,
        base_tree=BINDING.base_tree,
        candidate_sha=BINDING.candidate_sha,
        candidate_tree=BINDING.candidate_tree,
    )
    with pytest.raises(
        G5Error, match="STOP_G5_FG3_HISTORICAL_EVIDENCE_ANCHOR_MISSING"
    ):
        _collect_g5_projection(
            _facade(tables),
            observations,
            BINDING,
            historical_anchor=bad_anchor,
        )


@pytest.mark.parametrize(
    "classification,mutation_kind",
    [
        ("GET_404", "NONE"),
        ("GET_410", "NONE"),
    ],
)
def test_fg3_rejects_unattributed_gone_history(classification, mutation_kind) -> None:
    tables = _tables()
    row = tables["courses"][0]
    row["last_404_at"] = "2026-08-01T00:00:00Z"
    item = _fg3(
        row,
        classification,
        mutation_kind=mutation_kind,
        apply_outcome=(
            "APPLIED_PRIOR_EXACT_ONE"
            if mutation_kind != "NONE"
            else "NOT_APPLIED_READ_ONLY"
        ),
        exact_one_verified=mutation_kind != "NONE",
    )
    observations = _observations(tables, fg3=(item,))
    with pytest.raises(G5Error, match="STOP_G5_FG3_HISTORICAL_EVIDENCE_MISSING"):
        collect_g5_projection(_facade(tables), observations, BINDING)


def test_observation_fingerprint_is_order_independent() -> None:
    tables = _tables()
    profile = copy.deepcopy(tables["institution_site_profiles"][0])
    profile.update(
        {
            "id": "private-profile-second",
            "institution_id": "private-institution-second",
            "seed_urls": ["https://private.example.invalid/second"],
        }
    )
    tables["institution_site_profiles"].append(profile)
    institution = copy.deepcopy(tables["institutions"][0])
    institution["id"] = "private-institution-second"
    tables["institutions"].append(institution)
    staging = copy.deepcopy(tables["staging_raw"][0])
    staging.update(
        {
            "id": "private-staging-second",
            "institution_id": "private-institution-second",
            "url": "https://private.example.invalid/second",
        }
    )
    tables["staging_raw"].append(staging)
    course = copy.deepcopy(tables["courses"][0])
    course.update(
        {
            "id": "private-course-second",
            "institution_id": "private-institution-second",
            "url": "https://private.example.invalid/course/second",
        }
    )
    tables["courses"].append(course)
    observations = _observations(tables)
    forward = collect_g5_projection(_facade(tables), observations, BINDING)
    reversed_observations = replace(
        observations,
        inventories=tuple(reversed(observations.inventories)),
        sources=tuple(reversed(observations.sources)),
        fg3=tuple(reversed(observations.fg3)),
        hashes=tuple(reversed(observations.hashes)),
        lifecycle=tuple(reversed(observations.lifecycle)),
    )
    reverse = collect_g5_projection(_facade(tables), reversed_observations, BINDING)
    assert _plain(forward) == _plain(reverse)


def test_every_published_count_has_allowlisted_unit_and_denominator() -> None:
    tables = _tables()
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    assert set(result["aggregates"]) == set(AGGREGATE_DEFINITIONS)
    assert set(result["definitions"]["aggregates"]) == set(result["aggregates"])
    assert set(result["definitions"]["reason_codes"]) == set(result["reason_codes"])
    for section in result["definitions"].values():
        for definition in section.values():
            assert definition["unit"] and definition["denominator"]
    assert set(result["reason_codes"]).issubset(REASON_DEFINITIONS)
    assert all(type(value) is int and value >= 0 for value in result["reason_codes"].values())
    used = {
        definition["denominator"]
        for section in ("reason_codes", "aggregates")
        for definition in result["definitions"][section].values()
    }
    assert used <= set(result["denominator_values"])
    assert REASON_DEFINITIONS["INVENTORY_QUERY_FAILED"] == (
        "profiles",
        "enabled_profiles",
    )
    assert REASON_DEFINITIONS["SOURCE_GET_403"] == (
        "source_observations",
        "enabled_profiles",
    )
    assert AGGREGATE_DEFINITIONS["prior_mutations_revalidated"] == (
        "courses",
        "fg3_attributable_prior_mutations",
    )


def test_projection_is_sanitized_and_deeply_immutable() -> None:
    tables = _tables()
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    rendered = json.dumps(_plain(result), sort_keys=True)
    for forbidden in (
        "private-institution",
        "private-profile",
        "private-staging",
        "private-course",
        "private.example.invalid",
        "secret=value",
        "website_url",
        "institution_id",
        "course_id",
        "staging_id",
        "response_body",
        "project_ref",
    ):
        assert forbidden not in rendered
    with pytest.raises(TypeError):
        result["decision"] = "PASS"
    with pytest.raises(TypeError):
        result["snapshot_pair"]["global"]["initial_count"] = 0


def test_synthetic_attribution_vector() -> None:
    tables = _tables()
    tables["staging_raw"] = []
    # 38 groups: one has 244 excess rows and 37 have one, for 281 total.
    group_sizes = [245] + [2] * 37
    index = 0
    for group, size in enumerate(group_sizes):
        for member in range(size):
            tables["staging_raw"].append(
                {
                    "id": f"duplicate-{index:04d}",
                    "institution_id": "private-institution",
                    "url": f"https://private.example.invalid/duplicate/{group}#{member}",
                    "status": "pending",
                    "content_hash": _hash(f"same-{group}"),
                    "last_harvested_at": "2026-08-14T03:00:00Z",
                    "created_at": "2026-08-14T03:00:00Z",
                }
            )
            index += 1
    for stale in range(798):
        tables["staging_raw"].append(
            {
                "id": f"stale-{stale:04d}",
                "institution_id": "private-institution",
                "url": f"https://private.example.invalid/stale/{stale}",
                "status": "processing",
                "content_hash": _hash(f"stale-{stale}"),
                "last_harvested_at": "2026-08-01T00:00:00Z",
                "created_at": "2026-08-01T00:00:00Z",
            }
        )
    # Seven enabled profiles total: six failed inventories, two blocked sources.
    for number in range(1, 7):
        institution = copy.deepcopy(tables["institutions"][0])
        institution["id"] = f"institution-{number}"
        tables["institutions"].append(institution)
        profile = copy.deepcopy(tables["institution_site_profiles"][0])
        profile.update({"id": f"profile-{number}", "institution_id": f"institution-{number}"})
        tables["institution_site_profiles"].append(profile)
    active_template = tables["courses"][0]
    tables["courses"] = [tables["courses"][1]]
    fg3_items = []
    for number in range(27):
        row = copy.deepcopy(active_template)
        row["id"] = f"vector-course-{number}"
        row["url"] = f"https://private.example.invalid/vector/{number}"
        tables["courses"].append(row)
        classification = "GET_404" if number < 2 else "TIMEOUT" if number < 26 else "HEALTHY"
        if classification == "GET_404":
            row["last_404_at"] = "2026-08-01T00:00:00Z"
        fg3_items.append(
            _fg3(
                row,
                classification,
                mutation_kind=(
                    "FIRST_GET_404" if classification == "GET_404" else "NONE"
                ),
                apply_outcome=(
                    "APPLIED_PRIOR_EXACT_ONE"
                    if classification == "GET_404"
                    else "NOT_APPLIED_READ_ONLY"
                ),
                exact_one_verified=classification == "GET_404",
            )
        )
    prior = copy.deepcopy(active_template)
    prior.update(
        {
            "id": "vector-prior",
            "url": "https://private.example.invalid/vector/prior",
            "is_active": False,
            "last_404_at": "2026-08-01T00:00:00Z",
        }
    )
    tables["courses"].append(prior)
    fg3_items.append(
        _fg3(
            prior,
            "GET_404",
            mutation_kind="DEACTIVATE_PERSISTENT_GONE",
            apply_outcome="APPLIED_PRIOR_EXACT_ONE",
            exact_one_verified=True,
        )
    )
    observations = _observations(tables, fg3=tuple(fg3_items))
    inventories = tuple(
        replace(item, terminal_reason="INVENTORY_QUERY_FAILED") if index < 6 else item
        for index, item in enumerate(observations.inventories)
    )
    sources = tuple(
        replace(item, terminal_reason="SOURCE_GET_403") if index < 2 else item
        for index, item in enumerate(observations.sources)
    )
    result = collect_g5_projection(
        _facade(tables), replace(observations, inventories=inventories, sources=sources), BINDING
    )
    assert result["aggregates"]["duplicate_groups"] == 38
    assert result["aggregates"]["duplicate_excess_rows"] == 281
    assert result["aggregates"]["processing_stale"] == 798
    assert result["reason_codes"]["INVENTORY_QUERY_FAILED"] == 6
    assert result["reason_codes"]["SOURCE_GET_403"] == 2
    assert result["aggregates"]["fg3_inconclusive_total"] == 24
    assert result["aggregates"]["first_get_404_observations"] == 2
    assert result["aggregates"]["deactivations_persistent_gone"] == 1
    assert result["aggregates"]["prior_mutations_revalidated"] == 3
    assert result["denominator_values"]["fg3_attributable_prior_mutations"] == 3


def test_static_repository_only_exclusions() -> None:
    path = Path(__file__).parents[1] / "scripts/shared/f10_9_g5_readonly_collector.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called.isdisjoint(
        {"insert", "upsert", "patch", "update", "delete", "rpc", "execute_sql", "apply_migration"}
    )
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported.isdisjoint(
        {"requests", "httpx", "socket", "urllib", "subprocess", "supabase", "importlib"}
    )
    assert EXCLUDED_SURFACES == {
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


def _authorization(**overrides):
    values = {
        "gate": GATE,
        "gate_status": "APPROVED_NOT_CONSUMED",
        "protected_merge_sha": BINDING.candidate_sha,
        "protected_merge_tree": BINDING.candidate_tree,
        "security_check_sha": BINDING.candidate_sha,
        "contract_check_sha": BINDING.candidate_sha,
        "payload_merge_sha": BINDING.candidate_sha,
        "payload_merge_tree": BINDING.candidate_tree,
        "production_target_digest": "sha256:" + "d" * 64,
    }
    values.update(overrides)
    return ConnectedAuthorization(**values)


class UntouchableFactory:
    def __getattribute__(self, name):
        raise AssertionError("factory was inspected")

    def __call__(self):
        raise AssertionError("factory was called")


@pytest.mark.parametrize(
    "authorization",
    [
        object(),
        _authorization(gate=None),
        _authorization(gate_status=GATE_CANDIDATE_STATUS),
        _authorization(security_check_sha="c" * 40),
        _authorization(payload_merge_tree="c" * 40),
        _authorization(production_target_digest=None),
    ],
)
def test_connected_mode_is_unconditionally_closed_without_factory(authorization) -> None:
    tables = _tables()
    with pytest.raises(G5Error, match="STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"):
        collect_g5_connected(
            authorization,
            facade_factory=UntouchableFactory(),
            observations=_observations(tables),
            binding=BINDING,
        )


def test_connected_exact_types_and_unimplemented_stop_without_factory() -> None:
    tables = _tables()
    with pytest.raises(G5Error, match="STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"):
        collect_g5_connected(
            _authorization(),
            facade_factory=UntouchableFactory(),
            observations=_observations(tables),
            binding=BINDING,
        )
    with pytest.raises(G5Error, match="STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"):
        collect_g5_connected(
            object(),
            facade_factory=UntouchableFactory(),
            observations=_observations(tables),
            binding=BINDING,
        )
