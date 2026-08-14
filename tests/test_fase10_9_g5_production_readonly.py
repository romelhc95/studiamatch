from __future__ import annotations

import ast
import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.shared.f10_9_g5_readonly_collector import (
    CandidateBinding,
    ConnectedAuthorization,
    FG3Observation,
    G5Error,
    G5ReadOnlyFacade,
    GATE,
    GATE_CANDIDATE_STATUS,
    HashObservation,
    PrivateObservations,
    SourceObservation,
    STOP_SNAPSHOT_DRIFT,
    collect_g5_connected,
    collect_g5_projection,
    snapshot_fingerprint,
)


NOW = datetime(2026, 8, 14, 4, 30, tzinfo=timezone.utc)
BINDING = CandidateBinding(
    base_sha="2c9d2438c5fc309d3692d1a1de1233e0fcc95afc",
    base_tree="161a8df69bf5e527c4ba863891504551ec5f7aa7",
    candidate_sha="a" * 40,
    candidate_tree="b" * 40,
    observed_at=NOW,
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _tables(staging_count: int = 2) -> dict[str, list[dict[str, object]]]:
    institution_id = "private-institution-id"
    staging = [
        {
            "id": f"private-staging-{index:05d}",
            "institution_id": institution_id,
            "url": f"https://private.example.invalid/program/{index}",
            "status": "pending",
            "content_hash": _hash(f"private-payload-{index}"),
            "last_harvested_at": "2026-08-14T03:00:00Z",
            "created_at": "2026-08-14T03:00:00Z",
        }
        for index in range(staging_count)
    ]
    return {
        "institutions": [
            {
                "id": institution_id,
                "name": "Private Institution",
                "slug": "private-slug",
                "website_url": "https://private.example.invalid",
                "last_harvest_at": None,
            }
        ],
        "institution_site_profiles": [
            {
                "id": "private-profile-id",
                "institution_id": institution_id,
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
        "staging_raw": staging,
        "cleansed_programs": [],
        "enriched_programs": [],
        "courses": [
            {
                "id": "private-course-id",
                "institution_id": institution_id,
                "url": "https://private.example.invalid/course?secret=value",
                "is_active": True,
                "last_404_at": None,
                "start_date": None,
            }
        ],
    }


def _facade(
    first: dict[str, list[dict[str, object]]],
    second: dict[str, list[dict[str, object]]] | None = None,
) -> G5ReadOnlyFacade:
    return G5ReadOnlyFacade(first, second or first)


def _observations(
    tables: dict[str, list[dict[str, object]]],
    *,
    source: str = "ACCESSIBLE",
    inventory_loaded: bool = True,
    fg3: str = "HEALTHY",
) -> PrivateObservations:
    return PrivateObservations(
        snapshot_fingerprint=snapshot_fingerprint(tables),
        base_sha=BINDING.base_sha,
        base_tree=BINDING.base_tree,
        candidate_sha=BINDING.candidate_sha,
        candidate_tree=BINDING.candidate_tree,
        observed_at=BINDING.observed_at,
        sources=(
            SourceObservation(
                "private-institution-id",
                inventory_loaded,
                source,
            ),
        ),
        fg3=(FG3Observation("private-course-id", fg3),),
        hashes=tuple(
            HashObservation(
                str(row["id"]),
                isinstance(row.get("content_hash"), str)
                and len(str(row["content_hash"])) == 64,
            )
            for row in tables["staging_raw"]
            if row.get("status") in {"pending", "processing", "processed"}
        ),
    )


def _plain(value):
    if isinstance(value, dict) or hasattr(value, "items"):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def test_facade_exposes_only_scoped_select_and_count() -> None:
    tables = _tables()
    facade = _facade(tables)
    result = collect_g5_projection(facade, _observations(tables), BINDING)

    assert result["decision"] == "PASS"
    assert result["reason_codes"] == {}
    for forbidden in ("patch", "insert", "upsert", "update", "delete", "rpc"):
        assert not hasattr(facade, forbidden)
    with pytest.raises(G5Error, match="STOP_G5_FACADE_SCOPE"):
        facade.select(0, "courses", columns="id,secret", limit=1, offset=0, order="id.asc")
    with pytest.raises(G5Error, match="STOP_G5_FACADE_SCOPE"):
        facade.count(0, "unknown_table")

    extra = _tables()
    extra["courses"][0]["secret"] = "must-not-cross-facade"
    with pytest.raises(G5Error, match="STOP_G5_FACADE_SCOPE"):
        _facade(extra)


def test_complete_stable_pagination_over_one_thousand_rows_twice() -> None:
    tables = _tables(staging_count=1005)
    result = collect_g5_projection(
        _facade(tables), _observations(tables), BINDING, page_size=1000
    )
    assert result["counts"]["tables"]["staging_raw"] == {
        "rows": 1005,
        "pages_per_snapshot": [2, 2],
    }
    assert result["counts"]["snapshots"] == 2


def test_same_count_changed_row_stops_on_snapshot_drift() -> None:
    first = _tables()
    second = copy.deepcopy(first)
    second["staging_raw"][0]["status"] = "processing"
    result = collect_g5_projection(
        _facade(first, second), _observations(first), BINDING
    )
    assert result["decision"] == "STOP"
    assert result["reason_codes"] == {STOP_SNAPSHOT_DRIFT: 1}
    assert result["fingerprints"] == {"snapshot": None, "observations": None}


def test_duplicate_ids_and_explicit_row_and_byte_limits_fail_closed() -> None:
    duplicate = _tables()
    duplicate["staging_raw"].append(copy.deepcopy(duplicate["staging_raw"][0]))
    with pytest.raises(G5Error, match="STOP_G5_DUPLICATE_ID"):
        collect_g5_projection(_facade(duplicate), _observations(duplicate), BINDING)

    tables = _tables(staging_count=3)
    with pytest.raises(G5Error, match="STOP_G5_LIMIT_EXCEEDED"):
        collect_g5_projection(
            _facade(tables),
            _observations(tables),
            BINDING,
            page_size=2,
            max_rows_per_table=2,
        )
    with pytest.raises(G5Error, match="STOP_G5_LIMIT_EXCEEDED"):
        collect_g5_projection(
            _facade(tables),
            _observations(tables),
            BINDING,
            max_snapshot_bytes=10,
        )


def test_duplicates_hash_lifecycle_and_full_downstream_are_deterministic() -> None:
    tables = _tables()
    duplicate = copy.deepcopy(tables["staging_raw"][0])
    duplicate.update(
        {
            "id": "private-staging-duplicate",
            "url": "HTTPS://PRIVATE.EXAMPLE.INVALID/program/0#fragment",
            "content_hash": _hash("changed-private-payload"),
            "status": "processing",
            "last_harvested_at": "2026-08-01T00:00:00Z",
        }
    )
    tables["staging_raw"].append(duplicate)
    tables["cleansed_programs"].append(
        {
            "id": "private-cleansed-id",
            "staging_id": "missing-private-staging",
            "institution_id": "private-institution-id",
            "url": "https://private.example.invalid/program/0",
        }
    )
    tables["enriched_programs"].append(
        {
            "id": "private-enriched-id",
            "cleansed_id": "missing-private-cleansed",
            "institution_id": "private-institution-id",
            "url": "https://private.example.invalid/program/0",
        }
    )
    first = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    shuffled = copy.deepcopy(tables)
    shuffled["staging_raw"].reverse()
    observations = _observations(shuffled)
    second = collect_g5_projection(_facade(shuffled), observations, BINDING)

    assert _plain(first) == _plain(second)
    assert first["counts"]["duplicate_groups"] == 1
    assert first["counts"]["duplicate_excess_rows"] == 1
    for reason in (
        "DUPLICATE_NORMALIZED_URL",
        "CONFLICTING_CONTENT_HASH",
        "STALE_PROCESSING",
        "DOWNSTREAM_REFERENCE_CONFLICT",
    ):
        assert first["reason_codes"][reason] > 0


def test_future_processing_unknown_status_and_missing_evidence_are_blocked() -> None:
    tables = _tables()
    tables["staging_raw"][0].update(
        {
            "status": "processing",
            "content_hash": None,
            "last_harvested_at": "2026-08-15T00:00:00Z",
        }
    )
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    assert result["reason_codes"]["PROCESSING_TIME_INVALID"] == 1
    assert result["reason_codes"]["INCOMPLETE_CONTENT_EVIDENCE"] == 1
    assert result["reason_codes"]["CONTENT_HASH_INVALID"] == 1

    tables["staging_raw"][0]["status"] = "unknown"
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    assert result["reason_codes"]["UNKNOWN_STAGING_STATUS"] == 1


def test_invalid_enabled_profile_is_classified() -> None:
    tables = _tables()
    tables["institution_site_profiles"][0]["seed_urls"] = []
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    assert result["reason_codes"]["INVALID_EMPTY_HARDCODED_PROFILE"] == 1

    tables = _tables()
    tables["institution_site_profiles"][0]["seed_urls"] = ["file:///private"]
    result = collect_g5_projection(_facade(tables), _observations(tables), BINDING)
    assert result["reason_codes"]["INVALID_ENABLED_DISCOVERY_PROFILE"] == 1

    for invalid_profile in (
        {
            "discovery_mode": "paginated_catalog",
            "catalog_url_patterns": [
                "https://private.example.invalid/catalog?page={page}&other={other}"
            ],
        },
        {"allowed_url_patterns": ["re:(a+)+$"]},
    ):
        tables = _tables()
        tables["institution_site_profiles"][0].update(invalid_profile)
        result = collect_g5_projection(
            _facade(tables), _observations(tables), BINDING
        )
        assert result["reason_codes"]["INVALID_ENABLED_DISCOVERY_PROFILE"] == 1


@pytest.mark.parametrize(
    ("source", "inventory_loaded", "expected"),
    [
        ("SOURCE_ACCESS_403", True, "SOURCE_ACCESS_403"),
        ("SOURCE_TIMEOUT", True, "SOURCE_TIMEOUT"),
        ("SOURCE_FAILURE", True, "SOURCE_FAILURE"),
        ("ACCESSIBLE", False, "INSTITUTION_INVENTORY_LOAD_FAILED"),
    ],
)
def test_private_source_observations_are_classified(
    source, inventory_loaded, expected
) -> None:
    tables = _tables()
    result = collect_g5_projection(
        _facade(tables),
        _observations(tables, source=source, inventory_loaded=inventory_loaded),
        BINDING,
    )
    assert result["reason_codes"][expected] == 1


def test_private_observations_are_bound_and_order_independent() -> None:
    tables = _tables()
    observations = _observations(tables)
    drifted = PrivateObservations(
        **{
            **observations.__dict__,
            "candidate_tree": "c" * 40,
        }
    )
    with pytest.raises(G5Error, match="STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED"):
        collect_g5_projection(_facade(tables), drifted, BINDING)

    multi = copy.deepcopy(tables)
    second_institution = copy.deepcopy(multi["institutions"][0])
    second_institution["id"] = "private-institution-2"
    multi["institutions"].append(second_institution)
    second_profile = copy.deepcopy(multi["institution_site_profiles"][0])
    second_profile.update({"id": "private-profile-2", "institution_id": "private-institution-2"})
    multi["institution_site_profiles"].append(second_profile)
    obs = _observations(multi)
    obs = PrivateObservations(
        **{
            **obs.__dict__,
            "sources": obs.sources
            + (SourceObservation("private-institution-2", True, "ACCESSIBLE"),),
        }
    )
    forward = collect_g5_projection(_facade(multi), obs, BINDING)
    reverse = collect_g5_projection(
        _facade(multi),
        PrivateObservations(**{**obs.__dict__, "sources": tuple(reversed(obs.sources))}),
        BINDING,
    )
    assert _plain(forward) == _plain(reverse)


def test_fg3_inconclusive_gone_recovery_and_inactive_recovery_are_fail_closed() -> None:
    tables = _tables()
    inconclusive = collect_g5_projection(
        _facade(tables), _observations(tables, fg3="INCONCLUSIVE"), BINDING
    )
    assert inconclusive["reason_codes"]["FG3_INCONCLUSIVE"] == 1

    first = collect_g5_projection(
        _facade(tables), _observations(tables, fg3="GONE"), BINDING
    )
    assert first["reason_codes"]["FIRST_404_410_OBSERVATION"] == 1

    old = copy.deepcopy(tables)
    old["courses"][0]["last_404_at"] = (
        NOW - timedelta(days=4)
    ).isoformat().replace("+00:00", "Z")
    revalidation = collect_g5_projection(
        _facade(old), _observations(old, fg3="GONE"), BINDING
    )
    assert revalidation["reason_codes"]["DEACTIVATION_REVALIDATION_REQUIRED"] == 1

    recovery = collect_g5_projection(
        _facade(old), _observations(old, fg3="HEALTHY"), BINDING
    )
    assert recovery["reason_codes"]["FG3_RECOVERY_REQUIRED"] == 1

    inactive = copy.deepcopy(old)
    inactive["courses"][0]["is_active"] = False
    inactive_recovery = collect_g5_projection(
        _facade(inactive), _observations(inactive, fg3="HEALTHY"), BINDING
    )
    assert (
        inactive_recovery["reason_codes"]["FG3_INACTIVE_RECOVERY_REQUIRES_REBASELINE"]
        == 1
    )


def test_public_projection_and_failures_are_sanitized() -> None:
    tables = _tables()
    rendered = json.dumps(
        _plain(
            collect_g5_projection(
                _facade(tables),
                _observations(tables, source="SOURCE_ACCESS_403", fg3="INCONCLUSIVE"),
                BINDING,
            )
        ),
        sort_keys=True,
    )
    for forbidden in (
        "private-institution-id",
        "private-profile-id",
        "private-staging",
        "private-course-id",
        "private.example.invalid",
        "private-payload",
        "secret=value",
    ):
        assert forbidden not in rendered
    assert set(json.loads(rendered)) == {
        "schema",
        "decision",
        "reason_codes",
        "counts",
        "fingerprints",
        "digests",
        "timestamps",
        "sha_tree",
    }

    invalid = _tables()
    invalid["courses"][0]["last_404_at"] = "private-invalid-timestamp"
    with pytest.raises(G5Error) as error:
        collect_g5_projection(_facade(invalid), _observations(invalid), BINDING)
    assert error.value.__cause__ is None


def test_excluded_surfaces_and_mutation_calls_are_absent_from_collector() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts/shared/f10_9_g5_readonly_collector.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "f10_9_metadata_planner" not in " ".join(imported)
    assert "f10_9_fg2_preflight" not in source
    assert "f10_9_fg3_atomic" not in source
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called_attributes.isdisjoint(
        {"insert", "upsert", "patch", "update", "delete", "rpc", "execute_sql", "apply_migration"}
    )
    for forbidden in ("syllabus", "objectives", "metadata completeness", "H2-CA2"):
        assert forbidden not in source


def _authorization(**overrides) -> ConnectedAuthorization:
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


def test_missing_or_unapproved_gate_blocks_before_network() -> None:
    tables = _tables()
    factory = lambda: pytest.fail("network factory must remain unreachable")
    for authorization, reason in (
        (_authorization(gate=None), "STOP_G5_GATE_MISSING"),
        (
            _authorization(gate_status=GATE_CANDIDATE_STATUS),
            "STOP_G5_GATE_NOT_APPROVED",
        ),
    ):
        with pytest.raises(G5Error, match=reason):
            collect_g5_connected(
                authorization,
                facade_factory=factory,
                observations=_observations(tables),
                binding=BINDING,
            )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"security_check_sha": "c" * 40}, "STOP_G5_PROTECTED_MERGE_REQUIRED"),
        ({"payload_merge_tree": "c" * 40}, "STOP_G5_PRIVATE_PAYLOAD_BINDING_REQUIRED"),
        ({"production_target_digest": None}, "STOP_G5_PRODUCTION_TARGET_REQUIRED"),
    ],
)
def test_connected_bindings_fail_before_network(overrides, reason) -> None:
    tables = _tables()
    with pytest.raises(G5Error, match=reason):
        collect_g5_connected(
            _authorization(**overrides),
            facade_factory=lambda: pytest.fail("network factory must remain unreachable"),
            observations=_observations(tables),
            binding=BINDING,
        )


def test_connected_mode_remains_unimplemented_even_with_all_preconditions() -> None:
    tables = _tables()
    with pytest.raises(G5Error, match="STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED"):
        collect_g5_connected(
            _authorization(),
            facade_factory=lambda: pytest.fail("network factory must remain unreachable"),
            observations=_observations(tables),
            binding=BINDING,
        )
