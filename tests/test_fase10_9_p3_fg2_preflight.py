from __future__ import annotations

import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from scripts.core import master_orchestrator
from scripts.shared.f10_9_fg2_preflight import (
    ExistingDbReadFacade,
    PreflightError,
    build_runtime_manifest,
    run_preflight,
    safe_source_probe,
)
from scripts.shared.safe_http import UnsafeURL


NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tables(institution_count: int = 2, staging_count: int = 2) -> dict[str, list[dict]]:
    institutions = [
        {
            "id": f"00000000-0000-0000-0000-{index:012d}",
            "name": f"Private Institution {index}",
            "slug": f"private-{index}",
            "website_url": f"https://private-{index}.example.invalid",
            "last_harvest_at": None,
        }
        for index in range(1, institution_count + 1)
    ]
    profiles = [
        {
            "id": f"10000000-0000-0000-0000-{index:012d}",
            "institution_id": institution["id"],
            "discovery_enabled": True,
            "pipeline_enabled": True,
            "pipeline_ready": True,
            "discovery_mode": "hardcoded_urls",
            "seed_urls": [f"{institution['website_url']}/program"],
            "catalog_url_patterns": [],
            "allowed_url_patterns": ["/program"],
            "circuit_open": False,
            "circuit_opened_at": None,
        }
        for index, institution in enumerate(institutions, 1)
    ]
    staging = []
    for index in range(staging_count):
        institution = institutions[index % len(institutions)]
        payload = f"payload-{index}"
        staging.append(
            {
                "id": f"20000000-0000-0000-{index // 10000:04d}-{index:012d}",
                "institution_id": institution["id"],
                "url": f"{institution['website_url']}/program/{index}",
                "status": "pending",
                "raw_html": payload,
                "content_hash": _hash(payload),
                "last_harvested_at": "2026-08-10T10:00:00Z",
                "created_at": "2026-08-10T10:00:00Z",
            }
        )
    return {
        "institutions": institutions,
        "institution_site_profiles": profiles,
        "staging_raw": staging,
        "cleansed_programs": [],
    }


class FakeReadFacade:
    def __init__(self, tables: dict[str, list[dict]]) -> None:
        self.tables = copy.deepcopy(tables)
        self.select_calls: list[tuple[str, int, int]] = []
        self.count_calls: list[str] = []

    def select(self, table, *, columns, limit, offset, order):
        assert order == "id.asc"
        self.select_calls.append((table, offset, limit))
        rows = sorted(self.tables[table], key=lambda row: str(row["id"]))
        return copy.deepcopy(rows[offset : offset + limit])

    def count(self, table):
        self.count_calls.append(table)
        return len(self.tables[table])


def _accessible(_url, _profile):
    return "ACCESSIBLE"


def _main(facade, runner, probe=_accessible, argv=None, clock=None):
    return master_orchestrator.main(
        argv or ["--limit", "2"],
        db_facade=facade,
        source_probe=probe,
        script_runner=runner,
        clock=clock,
    )


def test_complete_pagination_over_one_thousand_rows() -> None:
    facade = FakeReadFacade(_tables(staging_count=1005))
    manifest = run_preflight(facade, _accessible, now=NOW, page_size=1000).manifest

    assert manifest["result"] == "PASS"
    assert manifest["collection"]["staging_raw"] == {"rows": 1005, "pages": 2}
    assert ("staging_raw", 0, 1000) in facade.select_calls
    assert ("staging_raw", 1000, 1000) in facade.select_calls
    assert facade.count_calls.count("staging_raw") == 2


def test_concurrent_preflights_are_deterministic_and_private() -> None:
    tables = _tables()

    def collect(_index):
        return dict(run_preflight(FakeReadFacade(tables), _accessible, now=NOW).manifest)

    with ThreadPoolExecutor(max_workers=4) as executor:
        manifests = list(executor.map(collect, range(8)))

    assert all(manifest == manifests[0] for manifest in manifests)
    assert manifests[0]["cohort"]["size"] == 2
    assert manifests[0]["cohort"]["fingerprint"].startswith("sha256:")


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (
            lambda tables: tables["staging_raw"].append(
                {**tables["staging_raw"][0], "id": "duplicate-row"}
            ),
            "DUPLICATE_NORMALIZED_URL",
        ),
        (
            lambda tables: tables["staging_raw"][0].update(
                {"status": "processing", "last_harvested_at": "2026-08-01T00:00:00Z"}
            ),
            "STALE_PROCESSING",
        ),
        (
            lambda tables: tables["staging_raw"][0].update(
                {"content_hash": "0" * 64}
            ),
            "CONFLICTING_CONTENT_HASH",
        ),
        (
            lambda tables: tables["cleansed_programs"].append(
                {
                    "id": "downstream-conflict",
                    "staging_id": "missing-staging",
                    "institution_id": tables["institutions"][0]["id"],
                    "url": "https://private.example.invalid/program",
                }
            ),
            "DOWNSTREAM_REFERENCE_CONFLICT",
        ),
        (
            lambda tables: tables["institution_site_profiles"][0].update(
                {"seed_urls": []}
            ),
            "INVALID_EMPTY_HARDCODED_PROFILE",
        ),
        (
            lambda tables: tables["staging_raw"][0].update({"status": "unknown"}),
            "UNKNOWN_STAGING_STATUS",
        ),
        (
            lambda tables: tables["staging_raw"][0].update({"content_hash": None}),
            "INCOMPLETE_CONTENT_EVIDENCE",
        ),
    ],
)
def test_each_data_blocker_prevents_all_runtime_calls(mutate, reason) -> None:
    tables = _tables()
    mutate(tables)
    calls = []

    result = _main(FakeReadFacade(tables), lambda *args, **kwargs: calls.append(args) or True)

    manifest = run_preflight(FakeReadFacade(tables), _accessible, now=NOW).manifest
    assert result != 0
    assert calls == []
    assert manifest["reason_counts"][reason] > 0


@pytest.mark.parametrize("outcome", ["SOURCE_ACCESS_403", "SOURCE_TIMEOUT", "SOURCE_FAILURE"])
def test_source_failures_are_not_noop_and_call_no_runtime(outcome) -> None:
    calls = []
    result = _main(
        FakeReadFacade(_tables()),
        lambda *args, **kwargs: calls.append(args) or True,
        probe=lambda _url, _profile: outcome,
    )

    manifest = run_preflight(
        FakeReadFacade(_tables()), lambda _url, _profile: outcome, now=NOW
    ).manifest
    assert result != 0
    assert calls == []
    assert manifest["result"] == "BLOCKED_PREWRITE"
    assert manifest["reason_counts"][outcome] == 2


def test_valid_zero_limit_noop_is_success_without_probe_or_runtime() -> None:
    calls = []
    facade = FakeReadFacade(_tables())

    result = _main(
        facade,
        lambda *args, **kwargs: calls.append(args) or True,
        probe=None,
        argv=["--limit", "0"],
    )

    manifest = run_preflight(
        FakeReadFacade(_tables()), None, limit=0, now=NOW
    ).manifest
    assert result == 0
    assert calls == []
    assert manifest["result"] == "NOOP"
    assert manifest["source_outcomes"] == {}


def test_missing_exact_cohort_is_blocked_not_noop() -> None:
    calls = []
    result = _main(
        FakeReadFacade(_tables()),
        lambda *args, **kwargs: calls.append(args) or True,
        probe=None,
        argv=["--institution-slug", "not-present"],
    )
    manifest = run_preflight(
        FakeReadFacade(_tables()), None, only_slug="not-present", now=NOW
    ).manifest
    assert result == 1
    assert calls == []
    assert manifest["result"] == "BLOCKED_PREWRITE"
    assert manifest["reason_counts"] == {"REQUESTED_COHORT_NOT_FOUND": 1}


def test_success_consumes_frozen_cohort_then_runs_cleansing() -> None:
    calls = []

    result = _main(
        FakeReadFacade(_tables()),
        lambda path, args=None, timeout=None: calls.append((path, args, timeout)) or True,
    )

    assert result == 0
    assert [call[0] for call in calls] == [
        "scripts/core/universal_harvester.py",
        "scripts/core/universal_harvester.py",
        "scripts/core/cleansing_worker.py",
    ]
    runtime_institutions = [json.loads(call[1][0]) for call in calls[:2]]
    assert [item["id"] for item in runtime_institutions] == [
        row["id"] for row in _tables()["institutions"]
    ]


def test_runtime_manifest_reports_success_and_partial_without_identifiers() -> None:
    manifests = []
    assert master_orchestrator.main(
        ["--limit", "2"],
        db_facade=FakeReadFacade(_tables()),
        source_probe=_accessible,
        script_runner=lambda *_args, **_kwargs: True,
        manifest_sink=manifests.append,
    ) == 0
    assert manifests[0]["result"] == "SUCCESS"
    assert manifests[0]["member_outcomes"] == {"SUCCESS": 2}

    preflight = run_preflight(FakeReadFacade(_tables()), _accessible, now=NOW)
    partial = build_runtime_manifest(
        preflight.manifest,
        result="PARTIAL_GLOBAL",
        member_outcomes={"SUCCESS": 1, "FAILED": 1},
    )
    rendered = json.dumps(dict(partial), sort_keys=True)
    assert partial["downstream"] == "BLOCKED"
    assert all(row["id"] not in rendered for row in _tables()["institutions"])


def test_default_safe_source_probe_classifies_without_exposing_target() -> None:
    assert safe_source_probe(
        "https://source.example.invalid",
        {},
        head=lambda *_args, **_kwargs: type("Response", (), {"status_code": 403})(),
        get=lambda *_args, **_kwargs: type("Response", (), {"status_code": 403})(),
    ) == "SOURCE_ACCESS_403"

    def timeout(*_args, **_kwargs):
        raise UnsafeURL("SAFE_TOTAL_TIMEOUT")

    assert safe_source_probe(
        "https://source.example.invalid",
        {},
        head=timeout,
    ) == "SOURCE_TIMEOUT"


def test_orchestrator_uses_safe_probe_by_default(monkeypatch) -> None:
    probe_calls = []
    runtime_calls = []
    monkeypatch.setattr(
        master_orchestrator,
        "safe_source_probe",
        lambda url, profile: probe_calls.append((url, profile)) or "ACCESSIBLE",
    )

    result = master_orchestrator.main(
        ["--limit", "2", "--skip-cleansing"],
        db_facade=FakeReadFacade(_tables()),
        script_runner=lambda path, args=None, timeout=None: runtime_calls.append(path) or True,
    )

    assert result == 0
    assert len(probe_calls) == 4
    assert runtime_calls == [
        "scripts/core/universal_harvester.py",
        "scripts/core/universal_harvester.py",
    ]


def test_runtime_logs_redact_institution_and_subprocess_arguments(caplog) -> None:
    tables = _tables(institution_count=1, staging_count=1)
    caplog.set_level("INFO")
    assert _main(
        FakeReadFacade(tables),
        lambda *_args, **_kwargs: True,
        argv=["--limit", "1", "--skip-cleansing"],
    ) == 0
    rendered = "\n".join(record.getMessage() for record in caplog.records)
    institution = tables["institutions"][0]
    for private in (
        institution["id"],
        institution["name"],
        institution["slug"],
        institution["website_url"],
    ):
        assert private not in rendered

    caplog.clear()
    private_argument = json.dumps(institution)
    child_private = "https://private-child.example.invalid/program"
    monkey_result = type(
        "Result",
        (),
        {"returncode": 0, "stdout": child_private, "stderr": child_private},
    )()
    run_kwargs = {}
    original_run = master_orchestrator.subprocess.run
    try:
        def fake_run(*_args, **kwargs):
            run_kwargs.update(kwargs)
            return monkey_result

        master_orchestrator.subprocess.run = fake_run
        assert master_orchestrator.run_script("synthetic.py", [private_argument]) is True
    finally:
        master_orchestrator.subprocess.run = original_run
    rendered = "\n".join(record.getMessage() for record in caplog.records)
    assert private_argument not in rendered
    assert child_private not in rendered
    assert "args=redacted count=1" in rendered
    assert "STAGE STDOUT REDACTED" in rendered
    assert "STAGE STDERR REDACTED" in rendered
    assert run_kwargs["capture_output"] is True
    assert run_kwargs["text"] is True


def test_institution_failure_reports_partial_global_and_blocks_cleansing() -> None:
    calls = []

    def runner(path, args=None, timeout=None):
        calls.append(path)
        return len(calls) == 1

    result = _main(FakeReadFacade(_tables()), runner)

    assert result != 0
    assert calls == [
        "scripts/core/universal_harvester.py",
        "scripts/core/universal_harvester.py",
    ]


def test_time_budget_partial_is_nonzero_and_blocks_downstream(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(master_orchestrator, "MAX_RUN_SECONDS", 5)
    times = iter([100.0, 101.0, 106.0])

    result = _main(
        FakeReadFacade(_tables()),
        lambda path, args=None, timeout=None: calls.append(path) or True,
        clock=lambda: next(times),
    )

    assert result != 0
    assert calls == ["scripts/core/universal_harvester.py"]


class DriftFacade(FakeReadFacade):
    def __init__(self, tables):
        super().__init__(tables)
        self.institution_count_reads = 0

    def count(self, table):
        if table == "institutions":
            self.institution_count_reads += 1
            if self.institution_count_reads == 3:
                self.tables["institutions"][0]["name"] = "Changed During Gate"
        return super().count(table)


def test_fingerprint_drift_blocks_before_first_runtime_call() -> None:
    calls = []
    result = _main(
        DriftFacade(_tables()),
        lambda *args, **kwargs: calls.append(args) or True,
    )
    assert result != 0
    assert calls == []


def test_collection_error_and_incomplete_page_fail_closed() -> None:
    class BrokenFacade(FakeReadFacade):
        def select(self, table, *, columns, limit, offset, order):
            if table == "staging_raw":
                return []
            return super().select(
                table, columns=columns, limit=limit, offset=offset, order=order
            )

    calls = []
    result = _main(
        BrokenFacade(_tables()),
        lambda *args, **kwargs: calls.append(args) or True,
    )
    assert result != 0
    assert calls == []
    with pytest.raises(PreflightError, match="PAGINATION_INCOMPLETE"):
        run_preflight(BrokenFacade(_tables()), _accessible, now=NOW)


def test_manifest_is_sanitized_and_exposes_no_private_cohort() -> None:
    tables = _tables()
    result = run_preflight(FakeReadFacade(tables), _accessible, now=NOW)
    serialized = json.dumps(dict(result.manifest), sort_keys=True)

    forbidden = []
    for institution in tables["institutions"]:
        forbidden.extend(
            [
                institution["id"],
                institution["name"],
                institution["slug"],
                institution["website_url"],
                "private-1.example.invalid",
            ]
        )
    forbidden.extend([tables["staging_raw"][0]["raw_html"], tables["staging_raw"][0]["url"]])
    assert all(secret not in serialized for secret in forbidden)
    assert not hasattr(result, "cohort")
    assert result.manifest["writes"] == 0


def test_existing_db_adapter_exposes_only_select_and_count() -> None:
    class ExistingClient:
        def select_all_service(self, table, **kwargs):
            return []

        def select_all_pipeline(self, table, **kwargs):
            return []

        def count_service_raise(self, table):
            return 0

        def count_pipeline_raise(self, table):
            return 0

        def patch(self, *_args, **_kwargs):
            raise AssertionError("mutation method must never be reachable")

    facade = ExistingDbReadFacade(ExistingClient())
    assert facade.count("institutions") == 0
    assert facade.select(
        "institutions", columns="id", limit=1000, offset=0, order="id.asc"
    ) == ()
    assert not hasattr(facade, "patch")
