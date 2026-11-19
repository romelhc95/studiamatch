"""Offline tests for rotation and exact cohort selection in controlled FG2."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import base64
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
from unittest.mock import AsyncMock, Mock, patch
from types import SimpleNamespace
from urllib.parse import unquote

import pytest

from scripts.core import master_orchestrator as orchestrator
from scripts.core import fg2_bounded_run as fg2_run
from scripts.core.master_orchestrator import _approved_lot_preflight_error_label
from scripts.core import universal_harvester as harvester_module
from scripts.core.universal_harvester import HarvesterRunError, UniversalHarvester
from scripts.core.fg2_bounded_run import (
    FG2ApprovedLotManifest,
    FG2CohortManifest,
    FG2_LIMITS,
    append_manifest_discovery_row,
    append_manifest_entry,
    cleansed_url_sha256_for_record,
    initialize_manifest,
    stable_json_sha256,
    update_manifest_institution,
    UnsafePublicTarget,
    url_sha256,
    validate_controlled_profile,
)


INSTITUTION_A = "00000000-0000-0000-0000-000000000001"
INSTITUTION_B = "00000000-0000-0000-0000-000000000002"
STAGING_B = "40000000-0000-0000-0000-000000000002"
COURSE_B = "70000000-0000-0000-0000-000000000002"
URL_B = "https://b.example/programs"
SOURCE_SHA = "a" * 40


class FakeDB:
    def __init__(self) -> None:
        self.supabase_url = "https://test.supabase.co"
        self.institutions = [
            {"id": INSTITUTION_A, "name": "A", "slug": "a", "website_url": "https://a.example", "last_harvest_at": None},
            {"id": INSTITUTION_B, "name": "B", "slug": "b", "website_url": "https://b.example", "last_harvest_at": None},
        ]
        self.profiles = [
            {
                "institution_id": INSTITUTION_A,
                "discovery_enabled": True,
                "pipeline_enabled": True,
                "production_enabled": True,
                "circuit_open": False,
                "site_type": "traditional_ssr",
                "discovery_mode": "hardcoded_urls",
                "seed_urls": [],
            },
            {
                "institution_id": INSTITUTION_B,
                "discovery_enabled": True,
                "pipeline_enabled": True,
                "production_enabled": True,
                "circuit_open": False,
                "site_type": "traditional_ssr",
                "discovery_mode": "hardcoded_urls",
                "seed_urls": ["https://b.example/programs/"],
            },
        ]
        self.staging_rows = [
            {
                "id": STAGING_B,
                "institution_id": INSTITUTION_B,
                "url": URL_B,
                "status": "discovered",
                "content_hash": "f" * 64,
            }
        ]
        self.course_rows = [
            {
                "id": COURSE_B,
                "institution_id": INSTITUTION_B,
                "url": URL_B,
                "is_active": True,
                "is_verified": True,
            }
        ]
        self.cleansed_rows = []
        self.enriched_rows = []
        self.writes: list[tuple] = []

    def select_pipeline_raise(self, table: str, **kwargs):
        if table == "institution_site_profiles":
            filters = kwargs.get("filters", "")
            institution_id = filters.removeprefix("institution_id=eq.").lower()
            rows = [
                row for row in self.profiles
                if not filters or str(row.get("institution_id", "")).lower() == institution_id
            ]
        elif table == "staging_raw":
            rows = list(self.staging_rows)
        elif table == "cleansed_programs":
            rows = list(self.cleansed_rows)
        elif table == "enriched_programs":
            rows = list(self.enriched_rows)
        else:
            raise AssertionError(f"unexpected pipeline read: {table}")
        return self._apply_scoped_query(rows, **kwargs)

    def _apply_scoped_query(self, rows: list[dict], **kwargs):
        filters = kwargs.get("filters") or ""
        if filters.startswith("url=match."):
            pattern = unquote(filters.removeprefix("url=match."))
            rows = [row for row in rows if re.fullmatch(pattern, row.get("url", ""))]
        elif "=in.(" in filters:
            column, values = filters.split("=in.(", 1)
            ids = set(values.removesuffix(")").split(","))
            rows = [row for row in rows if str(row.get(column)) in ids]
        elif filters.startswith("institution_id=eq."):
            wanted = filters.removeprefix("institution_id=eq.").lower()
            rows = [row for row in rows if str(row.get("institution_id", "")).lower() == wanted]
        elif filters.startswith("id=eq."):
            wanted = filters.removeprefix("id=eq.").lower()
            rows = [row for row in rows if str(row.get("id", "")).lower() == wanted]
        elif filters.startswith("url=eq."):
            wanted = unquote(filters.removeprefix("url=eq."))
            rows = [row for row in rows if row.get("url") == wanted]
        if kwargs.get("order") == "id.asc":
            rows = sorted(rows, key=lambda row: str(row.get("id", "")))
        limit = kwargs.get("limit")
        return rows[:limit] if limit is not None else rows

    def select_service_raise(self, table: str, **kwargs):
        if table == "institutions":
            filters = kwargs.get("filters", "")
            institution_id = filters.removeprefix("id=eq.").lower()
            rows = [
                row for row in self.institutions
                if not filters or str(row.get("id", "")).lower() == institution_id
            ]
        elif table == "courses":
            rows = list(self.course_rows)
        else:
            raise AssertionError(f"unexpected service read: {table}")
        return self._apply_scoped_query(rows, **kwargs)

    def select_all_pipeline(self, table: str, **_kwargs):
        rows = list(
            {
                "staging_raw": self.staging_rows,
                "cleansed_programs": self.cleansed_rows,
                "enriched_programs": self.enriched_rows,
            }[table]
        )
        return self._apply_exact_url_filter(rows, _kwargs.get("filters", ""))

    def select_all_service(self, table: str, **_kwargs):
        assert table == "courses"
        return self._apply_exact_url_filter(list(self.course_rows), _kwargs.get("filters", ""))

    @staticmethod
    def _apply_exact_url_filter(rows: list[dict], filters: str) -> list[dict]:
        marker = "url=in.("
        if not filters or marker not in filters:
            return rows
        encoded = filters.split(marker, 1)[1].split(")", 1)[0]
        urls = {value.strip('"') for value in unquote(encoded).split(",")}
        return [row for row in rows if row.get("url") in urls]

    def count_pipeline_raise(self, *_args, **_kwargs):
        return 0

    def patch(self, *args, **kwargs):
        self.writes.append((args, kwargs))

    def patch_exact_one_raise(self, table: str, filters: str, data: dict, expected_id: str):
        rows = {
            "staging_raw": self.staging_rows,
            "courses": self.course_rows,
        }[table]
        match = next((row for row in rows if row.get("id") == expected_id), None)
        if match is None:
            raise AssertionError(f"synthetic fixture did not find {table}/{expected_id}")
        match.update(data)
        self.writes.append((table, filters, dict(data)))
        return dict(match)

    def insert(self, *args, **kwargs):
        self.writes.append((args, kwargs))
        return None


def approved_lot(
    database: FakeDB,
    *,
    selected_seed_urls: list[str] | None = None,
) -> tuple[dict, bytes, str]:
    institution = next(row for row in database.institutions if row["id"] == INSTITUTION_B)
    profile = next(row for row in database.profiles if row["institution_id"] == INSTITUTION_B)
    preflight = validate_controlled_profile(
        institution,
        profile,
        selected_seed_urls=selected_seed_urls,
    )
    payload = {
        "schema_version": 1,
        "reference": "H1REQ1-FG2-LOT-REVIEW-001",
        "source_sha": SOURCE_SHA,
        "limits": dict(FG2_LIMITS),
        "institutions": [
            {
                "institution_id": INSTITUTION_B,
                "institution_sha256": stable_json_sha256(
                    {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
                ),
                "profile_sha256": preflight["profile_sha256"],
                "seed_sha256": preflight["seed_sha256"],
                "seed_urls": preflight["seed_urls"],
            }
        ],
        "scope": [
            {
                "institution_id": INSTITUTION_B,
                "url": URL_B,
                "url_sha256": url_sha256(URL_B),
                "kind": "refresh_existing",
                "snapshot": {
                    "staging_rows": [
                        {
                            "id": STAGING_B,
                            "institution_id": INSTITUTION_B,
                            "url": database.staging_rows[0]["url"],
                            "status": "discovered",
                            "content_hash": "f" * 64,
                        }
                    ],
                    "course_rows": [
                        {
                            "id": COURSE_B,
                            "institution_id": INSTITUTION_B,
                            "url": database.course_rows[0]["url"],
                            "is_active": True,
                            "is_verified": True,
                            "last_404_at": None,
                        }
                    ],
                    "cleansed_rows": [],
                    "enriched_rows": [],
                },
            }
        ],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return payload, raw, hashlib.sha256(raw).hexdigest()


def approved_lot_for_urls(
    database: FakeDB,
    urls: list[str],
    *,
    refresh_urls: set[str] | None = None,
) -> FG2ApprovedLotManifest:
    database.profiles[1]["seed_urls"] = list(urls)
    payload, _raw, _digest = approved_lot(database, selected_seed_urls=urls)
    refresh_urls = set(urls) if refresh_urls is None else refresh_urls
    database.staging_rows = []
    database.cleansed_rows = []
    database.enriched_rows = []
    database.course_rows = []
    scope = []
    for index, url in enumerate(urls, start=1):
        snapshot = {
            "staging_rows": [],
            "course_rows": [],
            "cleansed_rows": [],
            "enriched_rows": [],
        }
        kind = "new_discovery"
        if url in refresh_urls:
            course = {
                "id": f"70000000-0000-0000-0000-{index:012d}",
                "institution_id": INSTITUTION_B,
                "url": url,
                "is_active": True,
                "is_verified": True,
                "last_404_at": None,
            }
            database.course_rows.append(dict(course))
            snapshot["course_rows"] = [course]
            kind = "refresh_existing"
        scope.append(
            {
                "institution_id": INSTITUTION_B,
                "url": url,
                "url_sha256": url_sha256(url),
                "kind": kind,
                "snapshot": snapshot,
            }
        )
    payload["scope"] = scope
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )


def run_approved_dispatch(
    database: FakeDB,
    tmp_path: Path,
    *,
    source_runner,
    approved=None,
    lot_reference=None,
    lot_digest=None,
    source_sha=SOURCE_SHA,
):
    payload, raw, digest = approved or approved_lot(database)
    approved_path = tmp_path / "approved-lot.json"
    cohort_path = tmp_path / "result-cohort.json"
    ref = lot_reference or payload["reference"]
    digest = lot_digest or digest
    env = {
        "GITHUB_RUN_ID": "123456789",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SHA": source_sha,
        "GITHUB_REF": "refs/heads/main",
        "FG2_APPROVED_LOT_MANIFEST_B64": base64.b64encode(raw).decode("ascii"),
    }
    args = [
        "--controlled-first-run",
        "--skip-cleansing",
        "--cohort-manifest",
        str(cohort_path),
        "--approved-lot-manifest",
        str(approved_path),
        "--approved-lot-reference",
        ref,
        "--approved-lot-sha256",
        digest,
    ]
    with (
        patch.dict(os.environ, env, clear=False),
        patch.object(orchestrator, "_get_db", return_value=database),
        patch.object(orchestrator, "run_script", side_effect=source_runner),
    ):
        result = orchestrator.main(args)
    return result, payload, raw, digest, approved_path, cohort_path


def test_controlled_selection_preserves_rotation_but_skips_missing_seeds_before_run() -> None:
    database = FakeDB()
    with patch.object(orchestrator, "_get_db", return_value=database):
        selected = orchestrator.get_institutions(
            limit=1,
            controlled=True,
            now=datetime(2026, 11, 9, tzinfo=timezone.utc),
        )

    assert [row["id"] for row in selected] == [INSTITUTION_B]
    assert selected[0]["_controlled_seed_urls"] == ["https://b.example/programs/"]
    assert len(selected[0]["_controlled_profile_sha256"]) == 64
    assert len(selected[0]["_controlled_seed_sha256"]) == 64
    assert database.writes == []


def test_controlled_orchestrator_requires_manifest_delegation_before_database_or_harvester(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GITHUB_RUN_ID", "123456789")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", SOURCE_SHA)
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setattr(
        orchestrator,
        "_get_db",
        lambda: pytest.fail("invalid controlled invocation must stop before DB access"),
    )
    monkeypatch.setattr(
        orchestrator,
        "run_script",
        lambda *_args, **_kwargs: pytest.fail("invalid invocation must not launch a worker"),
    )

    result = orchestrator.main(
        [
            "--controlled-first-run",
            "--cohort-manifest",
            str(tmp_path / "cohort.json"),
            "--approved-lot-manifest",
            str(tmp_path / "approved.json"),
            "--approved-lot-reference",
            "h1-lot-2026-11-09",
            "--approved-lot-sha256",
            "a" * 64,
        ]
    )

    assert result == 1


def test_scheduled_cohort_freezes_main_rotation_selection_without_source_or_database_writes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database = FakeDB()
    database.profiles[1]["discovery_mode"] = "sitemap_bfs"
    database.profiles[1]["seed_urls"] = ["https://b.example/catalog/program-one"]
    cohort_path = tmp_path / "scheduled-cohort.json"
    started: list[tuple[str, list[str]]] = []
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456789")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", SOURCE_SHA)
    monkeypatch.setattr(orchestrator, "_get_db", lambda: database)
    monkeypatch.setattr(
        orchestrator,
        "run_script",
        lambda script, args=None, **_kwargs: started.append((script, list(args or []))) or True,
    )

    result = orchestrator.main(
        [
            "--scheduled-cohort",
            "--skip-cleansing",
            "--limit",
            "10",
            "--max-urls",
            "10",
            "--cohort-manifest",
            str(cohort_path),
        ]
    )

    assert result == 0
    assert len(started) == 1
    script, args = started[0]
    assert script.endswith("universal_harvester.py")
    assert "--scheduled-cohort" in args
    assert "--controlled" not in args
    assert "--cohort-manifest" in args
    assert "--approved-lot-manifest" not in args
    child_institution = json.loads(args[0])
    assert child_institution["id"] == INSTITUTION_B
    assert child_institution["_controlled_seed_urls"] == ["https://b.example/sitemap.xml"]
    manifest = FG2CohortManifest.load(
        cohort_path,
        expected_run_id="123456789",
        expected_run_attempt=1,
        expected_source_sha=SOURCE_SHA,
        allow_empty=True,
    )
    assert manifest.institution_ids == (INSTITUTION_B,)
    assert manifest.staging_ids == ()
    assert database.writes == []


def test_scheduled_noop_records_rotation_attempt_without_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    database = Mock()
    completed_at = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
    started_at = completed_at.timestamp() - 17.8

    harvester_module._record_scheduled_attempt(
        database,
        {"id": INSTITUTION_B},
        started_at=started_at,
        completed_at=completed_at,
    )

    database.patch_exact_one_raise.assert_called_once_with(
        "institutions",
        filters=f"id=eq.{INSTITUTION_B}",
        data={
            "last_harvest_at": completed_at.isoformat(),
            "last_harvest_duration_sec": 17,
        },
        expected_id=INSTITUTION_B,
    )


@pytest.mark.parametrize(
    ("stop_reason", "expected_result"),
    [
        (None, "no_op"),
        ("SourceBlocked", "blocked"),
        ("OriginDeferred", "deferred"),
    ],
)
def test_scheduled_harvester_noop_or_controlled_stop_updates_rotation_and_manifest_without_lot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    stop_reason: str | None,
    expected_result: str,
) -> None:
    institution = {"id": INSTITUTION_B, "name": "B"}
    cohort_path = tmp_path / "scheduled-cohort.json"
    initialize_manifest(
        cohort_path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[
            {
                "institution_id": INSTITUTION_B,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    database = Mock()

    class EmptyScheduleHarvester:
        def __init__(self, *_args, **kwargs) -> None:
            assert kwargs["controlled"] is True
            assert kwargs["scheduled_cohort"] is True
            assert kwargs["require_approved_lot"] is False
            assert kwargs["approved_lot_manifest"] is None
            self.profile = {"enabled": True}
            self.db = database
            self.site_type = "traditional_ssr"
            self.discovery_mode = "hardcoded_urls"
            self.requires_stealth = False
            self.warmup_url = None
            self.requires_cf_bypass = False
            self.circuit_open = False
            self.controlled_stop_reason = stop_reason
            self._discovery_fetch_attempts = 1
            self._discovery_fetch_successes = 1
            self.request_budget = SimpleNamespace(
                snapshot=lambda: {"http_requests": 1, "unique_urls": 1}
            )

        @staticmethod
        def _gate_enabled(_name: str) -> bool:
            return True

        @staticmethod
        async def discover_courses():
            return []

    class EmptyAsyncSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(harvester_module, "UniversalHarvester", EmptyScheduleHarvester)
    monkeypatch.setattr(harvester_module, "AsyncSession", EmptyAsyncSession)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456789")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", SOURCE_SHA)

    result = asyncio.run(
        harvester_module.main(
            [
                json.dumps(institution),
                "--scheduled-cohort",
                "--max-urls",
                "10",
                "--cohort-manifest",
                str(cohort_path),
            ]
        )
    )

    assert result == 0
    database.patch_exact_one_raise.assert_called_once()
    call_args, call_kwargs = database.patch_exact_one_raise.call_args
    assert call_args[0] == "institutions"
    assert call_kwargs["expected_id"] == INSTITUTION_B
    assert call_kwargs["data"]["last_harvest_duration_sec"] >= 0
    assert call_kwargs["data"]["last_harvest_at"]
    manifest = FG2CohortManifest.load(
        cohort_path,
        expected_run_id="123456789",
        expected_run_attempt=1,
        expected_source_sha=SOURCE_SHA,
        allow_empty=True,
    )
    assert manifest.payload["institutions"][0]["result"] == expected_result
    assert manifest.payload["entries"] == []


def test_scheduled_partial_harvest_preserves_successes_for_downstream_workers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    institution = {"id": INSTITUTION_B, "name": "B"}
    successful_url = URL_B
    failed_url = f"{URL_B}/later-404"
    cohort_path = tmp_path / "scheduled-partial-cohort.json"
    initialize_manifest(
        cohort_path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[
            {
                "institution_id": INSTITUTION_B,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    database = Mock()

    class PartialScheduleHarvester:
        def __init__(self, *_args, **kwargs) -> None:
            self.db = database
            self.cohort_manifest_path = kwargs["cohort_manifest"]
            self.profile = {"enabled": True}
            self.site_type = "traditional_ssr"
            self.discovery_mode = "hardcoded_urls"
            self.requires_stealth = False
            self.warmup_url = None
            self.requires_cf_bypass = False
            self.circuit_open = False
            self.controlled_stop_reason = None
            self._discovery_fetch_attempts = 2
            self._discovery_fetch_successes = 2
            self.request_budget = SimpleNamespace(
                snapshot=lambda: {"http_requests": 2, "unique_urls": 2}
            )

        @staticmethod
        def _gate_enabled(_name: str) -> bool:
            return True

        @staticmethod
        async def discover_courses():
            return [successful_url, failed_url]

        async def _scrape_http(self, _session, url):
            if url == failed_url:
                raise harvester_module.HarvesterPartialError("synthetic 404")
            return {"url": url, "content_hash": "d" * 64, "raw_html": "synthetic"}

        def _save_to_staging(self, item):
            append_manifest_discovery_row(
                self.cohort_manifest_path,
                {
                    "institution_id": INSTITUTION_B,
                    "staging_id": STAGING_B,
                    "url_sha256": url_sha256(item["url"]),
                    "initial_status": "discovered",
                    "kind": "new_discovery",
                    "course_id": None,
                },
            )
            append_manifest_entry(
                self.cohort_manifest_path,
                {
                    "institution_id": INSTITUTION_B,
                    "staging_id": STAGING_B,
                    "url_sha256": url_sha256(item["url"]),
                    "content_sha256": item["content_hash"],
                    "kind": "new_discovery",
                    "course_id": None,
                },
            )
            return {"id": STAGING_B, "url": item["url"], "status": "pending"}

    class SyntheticAsyncSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(harvester_module, "UniversalHarvester", PartialScheduleHarvester)
    monkeypatch.setattr(harvester_module, "AsyncSession", SyntheticAsyncSession)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456789")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", SOURCE_SHA)

    result = asyncio.run(
        harvester_module.main(
            [
                json.dumps(institution),
                "--scheduled-cohort",
                "--max-urls",
                "10",
                "--cohort-manifest",
                str(cohort_path),
            ]
        )
    )

    manifest = FG2CohortManifest.load(
        cohort_path,
        expected_run_id="123456789",
        expected_run_attempt=1,
        expected_source_sha=SOURCE_SHA,
    )
    assert result == 0
    assert manifest.payload["institutions"][0]["result"] == "partial"
    assert [entry["url_sha256"] for entry in manifest.payload["entries"]] == [
        url_sha256(successful_url)
    ]
    database.patch_exact_one_raise.assert_called_once()


def test_scheduled_cohort_rejects_non_main_before_database_or_worker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/desarrollo")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456789")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", SOURCE_SHA)
    monkeypatch.setattr(
        orchestrator,
        "_get_db",
        lambda: pytest.fail("non-main schedule must stop before database selection"),
    )
    monkeypatch.setattr(
        orchestrator,
        "run_script",
        lambda *_args, **_kwargs: pytest.fail("non-main schedule must not launch the harvester"),
    )

    result = orchestrator.main(
        [
            "--scheduled-cohort",
            "--skip-cleansing",
            "--limit",
            "10",
            "--max-urls",
            "10",
            "--cohort-manifest",
            str(tmp_path / "scheduled-cohort.json"),
        ]
    )

    assert result == 1


def test_approved_lot_rejects_a_newly_eligible_institution_ahead_of_its_rotation_slot() -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.profiles[0]["seed_urls"] = ["https://a.example/programs/"]

    with patch.object(orchestrator, "_get_db", return_value=database):
        with pytest.raises(orchestrator.InvalidControlledRun, match="eligible rotation prefix"):
            orchestrator.get_institutions(
                limit=10,
                controlled=True,
                approved_lot=approved,
                now=datetime(2026, 11, 9, tzinfo=timezone.utc),
            )

    assert database.writes == []


def test_approved_lot_passes_non_prefix_seed_subset_to_child_without_writes(tmp_path: Path) -> None:
    database = FakeDB()
    first_seed = "https://b.example/catalog/"
    selected_seed = "https://b.example/programs/"
    database.profiles[1]["seed_urls"] = [first_seed, selected_seed]
    approved = approved_lot(database, selected_seed_urls=[selected_seed])
    started: list[list[str]] = []

    def construct_child(_script, args, **_kwargs):
        started.append(list(args))
        child_institution = json.loads(args[0])

        def option(name: str) -> str:
            return args[args.index(name) + 1]

        with patch("scripts.core.universal_harvester.get_db_client", return_value=database):
            child = UniversalHarvester(
                child_institution,
                max_discovered_urls=10,
                controlled=True,
                cohort_manifest=option("--cohort-manifest"),
                approved_lot_manifest=option("--approved-lot-manifest"),
                approved_lot_reference=option("--approved-lot-reference"),
                approved_lot_sha256=option("--approved-lot-sha256"),
                require_approved_lot=True,
            )
        assert child.controlled_seed_urls == [selected_seed]
        return False

    result, payload, _raw, _digest, _approved_path, _cohort_path = run_approved_dispatch(
        database,
        tmp_path,
        source_runner=construct_child,
        approved=approved,
    )

    assert result == 1
    assert len(started) == 1
    child_institution = json.loads(started[0][0])
    assert child_institution["_controlled_seed_urls"] == [selected_seed]
    assert child_institution["_controlled_seed_sha256"] == payload["institutions"][0]["seed_sha256"]
    assert database.writes == []


def test_approved_non_prefix_seed_drift_fails_before_child_without_substitution(tmp_path: Path) -> None:
    database = FakeDB()
    selected_seed = "https://b.example/programs/"
    database.profiles[1]["seed_urls"] = ["https://b.example/catalog/", selected_seed]
    approved = approved_lot(database, selected_seed_urls=[selected_seed])
    database.profiles[1]["seed_urls"][1] = "https://b.example/changed/"
    started: list[list[str]] = []

    result, _payload, _raw, _digest, _approved_path, _cohort_path = run_approved_dispatch(
        database,
        tmp_path,
        source_runner=lambda _script, args, **_kwargs: started.append(list(args)) or True,
        approved=approved,
    )

    assert result == 1
    assert started == []
    assert database.writes == []


def test_controlled_selection_rejects_seed_on_different_origin_without_mutation() -> None:
    database = FakeDB()
    database.profiles[0]["seed_urls"] = ["https://elsewhere.example/programs/"]
    database.profiles[1]["seed_urls"] = []
    with patch.object(orchestrator, "_get_db", return_value=database):
        selected = orchestrator.get_institutions(
            limit=10,
            controlled=True,
            now=datetime(2026, 11, 9, tzinfo=timezone.utc),
        )

    assert selected == []
    assert database.writes == []


def test_controlled_orchestrator_stops_after_approved_institution_failure(tmp_path: Path) -> None:
    database = FakeDB()
    started: list[list[str]] = []
    result, _payload, _raw, _digest, _approved_path, _cohort_path = run_approved_dispatch(
        database,
        tmp_path,
        source_runner=lambda _path, args, **_kwargs: started.append(args) or False,
    )

    assert result == 1
    assert len(started) == 1
    assert "--controlled" in started[0]
    assert "--cohort-manifest" in started[0]
    assert "--approved-lot-reference" in started[0]


def test_controlled_child_arguments_and_output_are_redacted(caplog) -> None:
    private_url = "https://institution.example/program?token=fixture-secret"
    child = subprocess.CompletedProcess(
        args=["worker"],
        returncode=0,
        stdout=private_url,
        stderr=private_url,
    )
    with patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False), patch.object(
        orchestrator.subprocess, "run", return_value=child
    ) as run:
        assert orchestrator.run_script("scripts/core/universal_harvester.py", [private_url]) is True

    assert run.call_args.kwargs["capture_output"] is True
    assert "args=redacted" in caplog.text
    assert "STDOUT REDACTED" in caplog.text
    assert private_url not in caplog.text
    assert "fixture-secret" not in caplog.text


def test_sensitive_child_exit_is_structured_without_private_output(caplog) -> None:
    private_argument = "https://private.example/hidden/path?token=ARGUMENT_SENTINEL"
    private_stdout = "BODY_SENTINEL https://private.example/hidden\nsecond line"
    private_stderr = "SECRET_SENTINEL request body must stay private"
    child = subprocess.CompletedProcess(
        args=["worker"],
        returncode=1,
        stdout=private_stdout,
        stderr=private_stderr,
    )
    caplog.set_level(logging.INFO)

    with (
        patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False),
        patch.object(orchestrator.subprocess, "run", return_value=child) as run,
    ):
        assert orchestrator.run_script(
            "scripts/core/universal_harvester.py",
            [private_argument],
            timeout=30,
        ) is False

    message = caplog.text
    assert "[STAGE FAILURE]" in message
    assert "stage=harvester" in message
    assert "failure_class=child_process_exit" in message
    assert "exit_code=1" in message
    assert "stdout_lines=2" in message
    assert "stderr_lines=1" in message
    assert private_argument not in message
    assert "private.example" not in message
    assert "ARGUMENT_SENTINEL" not in message
    assert "BODY_SENTINEL" not in message
    assert "SECRET_SENTINEL" not in message
    assert run.call_args.kwargs["capture_output"] is True
    assert run.call_args.kwargs["text"] is True


def test_child_database_failure_emits_safe_phase_category_and_parent_preserves_it(
    capsys, caplog
) -> None:
    private_message = "DATABASE_SENTINEL https://private.example/path?token=SECRET_SENTINEL body=BODY_SENTINEL"
    failure = harvester_module.DatabaseAPIError(
        private_message,
        table="institution_site_profiles",
        status_code=400,
    )
    caplog.set_level(logging.INFO)

    with (
        patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False),
        patch.object(harvester_module, "validate_harvester_run_mode", return_value="controlled"),
        patch.object(harvester_module, "UniversalHarvester", side_effect=failure),
    ):
        child_exit = asyncio.run(
            harvester_module.main(
                [
                    json.dumps({"id": INSTITUTION_B, "name": "Synthetic"}),
                    "--controlled",
                    "--cohort-manifest",
                    "/private/cohort.json",
                ]
            )
        )

    child_stderr = capsys.readouterr().err
    assert child_exit == 1
    assert "[FG2_DIAGNOSTIC]" in child_stderr
    diagnostic_line = next(
        line for line in child_stderr.splitlines() if "[FG2_DIAGNOSTIC] " in line
    )
    diagnostic = json.loads(diagnostic_line.split("[FG2_DIAGNOSTIC] ", 1)[1])
    assert diagnostic["phase"] == "harvester_initialization"
    assert diagnostic["category"] == "database_api_error"
    assert diagnostic["table"] == "institution_site_profiles"
    assert diagnostic["http_status"] == 400

    completed = subprocess.CompletedProcess(
        args=["worker"],
        returncode=child_exit,
        stdout="",
        stderr=child_stderr,
    )
    with (
        patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False),
        patch.object(orchestrator.subprocess, "run", return_value=completed),
    ):
        assert orchestrator.run_script("scripts/core/universal_harvester.py", ["<redacted>"]) is False

    message = caplog.text
    assert "phase=harvester_initialization" in message
    assert "failure_class=database_api_error" in message
    assert "table=institution_site_profiles" in message
    assert "http_status=400" in message
    for sentinel in (
        "DATABASE_SENTINEL",
        "private.example",
        "SECRET_SENTINEL",
        "BODY_SENTINEL",
        "/private/cohort.json",
    ):
        assert sentinel not in child_stderr
        assert sentinel not in message


def test_browser_start_failure_reports_its_phase_without_exception_details(
    capsys, caplog
) -> None:
    private_message = "BROWSER_START_SENTINEL https://private.example/path?token=SECRET_SENTINEL"

    class BrowserStartHarvester:
        def __init__(self, *_args, **_kwargs):
            self.profile = {"enabled": True}
            self.site_type = "spa_js_heavy"
            self.discovery_mode = "hardcoded_urls"
            self.requires_stealth = False
            self.requires_cf_bypass = False
            self.warmup_url = None
            self.circuit_open = False

        @staticmethod
        def _gate_enabled(_name):
            return True

    with (
        patch.dict(os.environ, {"F10_PRODUCTION_CANARY_RUN_ID": "synthetic"}, clear=False),
        patch.object(harvester_module, "validate_harvester_run_mode", return_value="ordinary"),
        patch.object(harvester_module, "UniversalHarvester", BrowserStartHarvester),
        patch.object(harvester_module, "async_playwright", side_effect=RuntimeError(private_message)),
    ):
        result = asyncio.run(
            harvester_module.main(
                [json.dumps({"id": INSTITUTION_B, "name": "Synthetic"})]
            )
        )

    child_stderr = capsys.readouterr().err
    diagnostic_line = next(
        line for line in child_stderr.splitlines() if "[FG2_DIAGNOSTIC] " in line
    )
    diagnostic = json.loads(diagnostic_line.split("[FG2_DIAGNOSTIC] ", 1)[1])
    assert result == 1
    assert diagnostic == {
        "version": 1,
        "phase": "browser_initialization",
        "category": "unexpected_exception",
    }
    assert "BROWSER_START_SENTINEL" not in child_stderr
    assert "private.example" not in child_stderr
    assert "SECRET_SENTINEL" not in child_stderr
    assert private_message not in caplog.text


def test_module_startup_failure_emits_safe_phase_and_category(capsys) -> None:
    private_message = "STARTUP_SENTINEL https://private.example/path?token=SECRET_SENTINEL"

    with (
        patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False),
        patch.object(
            harvester_module,
            "setup_lima_logging",
            side_effect=RuntimeError(private_message),
        ),
    ):
        with pytest.raises(RuntimeError):
            harvester_module._initialize_module_runtime()

    child_stderr = capsys.readouterr().err
    diagnostic_line = next(
        line for line in child_stderr.splitlines() if "[FG2_DIAGNOSTIC] " in line
    )
    diagnostic = json.loads(diagnostic_line.split("[FG2_DIAGNOSTIC] ", 1)[1])
    assert diagnostic["phase"] == "module_initialization"
    assert diagnostic["category"] == "module_initialization_failed"
    assert orchestrator._parse_child_diagnostic("", child_stderr) == {
        "phase": "module_initialization",
        "category": "module_initialization_failed",
    }
    assert "STARTUP_SENTINEL" not in child_stderr
    assert "private.example" not in child_stderr
    assert "SECRET_SENTINEL" not in child_stderr


def test_sensitive_subprocess_start_failure_is_classified_without_error_text(caplog) -> None:
    caplog.set_level(logging.INFO)
    with (
        patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False),
        patch.object(
            orchestrator.subprocess,
            "run",
            side_effect=FileNotFoundError("START_SENTINEL https://private.example/path"),
        ),
    ):
        assert orchestrator.run_script("scripts/core/universal_harvester.py", ["SECRET_SENTINEL"]) is False

    message = caplog.text
    assert "phase=subprocess_start" in message
    assert "failure_class=process_start_failed" in message
    assert "error_class=FileNotFoundError" in message
    assert "START_SENTINEL" not in message
    assert "private.example" not in message
    assert "SECRET_SENTINEL" not in message


def test_sensitive_child_diagnostic_rejects_non_integer_version(caplog) -> None:
    private_output = (
        '[FG2_DIAGNOSTIC] {"version":true,"phase":"harvester_initialization",'
        '"category":"database_api_error","table":"courses",'
        '"http_status":400,"message":"DIAGNOSTIC_SENTINEL"}'
    )
    child = subprocess.CompletedProcess(
        args=["worker"],
        returncode=1,
        stdout="",
        stderr=private_output,
    )
    caplog.set_level(logging.INFO)

    with (
        patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False),
        patch.object(orchestrator.subprocess, "run", return_value=child),
    ):
        assert orchestrator.run_script("scripts/core/universal_harvester.py", ["<redacted>"]) is False

    message = caplog.text
    assert "phase=unknown" in message
    assert "failure_class=child_process_exit" in message
    assert "table=unknown" in message
    assert "http_status=unknown" in message
    assert "DIAGNOSTIC_SENTINEL" not in message


def test_parent_rejects_diagnostic_marker_inside_other_output() -> None:
    embedded_event = (
        'REMOTE_OUTPUT [FG2_DIAGNOSTIC] {"version":1,"phase":"harvester_initialization",'
        '"category":"database_api_error"}'
    )

    assert orchestrator._parse_child_diagnostic("", embedded_event) is None


def test_approved_lot_exact_match_starts_only_approved_institution_after_clean_preflight(tmp_path) -> None:
    database = FakeDB()
    started: list[list[str]] = []
    source_requests: list[str] = []

    def simulated_child(_script, args, **_kwargs):
        started.append(list(args))
        cohort_path = Path(args[args.index("--cohort-manifest") + 1])
        manifest = FG2CohortManifest.load(cohort_path, allow_empty=True)
        update_manifest_institution(
            cohort_path,
            institution_id=INSTITUTION_B,
            http_requests=1,
            unique_urls=1,
            result="complete",
        )
        append_manifest_discovery_row(
            cohort_path,
            {
                "institution_id": INSTITUTION_B,
                "staging_id": STAGING_B,
                "url_sha256": url_sha256(URL_B),
                "initial_status": "discovered",
                "kind": "refresh_existing",
                "course_id": COURSE_B,
            },
        )
        append_manifest_entry(
            cohort_path,
            {
                "institution_id": INSTITUTION_B,
                "staging_id": STAGING_B,
                "course_id": COURSE_B,
                "url_sha256": url_sha256(URL_B),
                "content_sha256": "e" * 64,
                "kind": "refresh_existing",
            },
        )
        assert manifest.institution_ids == (INSTITUTION_B,)
        return True

    result, payload, _raw, digest, approved_path, _cohort_path = run_approved_dispatch(
        database, tmp_path, source_runner=simulated_child
    )

    assert result == 0
    assert approved_path.exists()
    child_institution = json.loads(started[0][0])
    assert child_institution["id"] == INSTITUTION_B
    assert started[0][started[0].index("--approved-lot-manifest") + 1] == str(approved_path)
    assert started[0][started[0].index("--approved-lot-reference") + 1] == payload["reference"]
    assert started[0][started[0].index("--approved-lot-sha256") + 1] == digest
    verified = FG2ApprovedLotManifest.load(
        approved_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    assert [item["url"] for item in verified.scope_for_institution(INSTITUTION_B)] == [URL_B]
    assert len(started) == 1
    assert database.writes == []
    assert source_requests == []


def test_approved_lot_profile_drift_fails_before_harvester_without_substitution(tmp_path) -> None:
    database = FakeDB()
    approved = approved_lot(database)
    database.profiles[0]["seed_urls"] = ["https://a.example/programs/"]
    database.profiles[1]["seed_urls"] = ["https://b.example/changed/"]
    started: list[list[str]] = []

    result, _payload, _raw, _digest, _approved_path, _cohort_path = run_approved_dispatch(
        database,
        tmp_path,
        source_runner=lambda _script, args, **_kwargs: started.append(list(args)) or True,
        approved=approved,
    )

    assert result == 1
    assert started == []
    assert database.writes == []
    assert database.staging_rows[0]["status"] == "discovered"


@pytest.mark.parametrize(
    ("lot_reference", "lot_digest", "source_sha"),
    [
        ("H1REQ1-FG2-LOT-OTHER", None, SOURCE_SHA),
        (None, "0" * 64, SOURCE_SHA),
        (None, None, "b" * 40),
    ],
)
def test_dispatch_rejects_wrong_lot_reference_digest_or_candidate_before_selection(
    tmp_path,
    lot_reference,
    lot_digest,
    source_sha,
) -> None:
    database = FakeDB()
    approved = approved_lot(database)
    started: list[list[str]] = []

    with patch.object(orchestrator, "get_institutions", wraps=orchestrator.get_institutions) as select:
        result, _payload, _raw, _digest, approved_path, _cohort_path = run_approved_dispatch(
            database,
            tmp_path,
            source_runner=lambda _script, args, **_kwargs: started.append(list(args)) or True,
            approved=approved,
            lot_reference=lot_reference,
            lot_digest=lot_digest,
            source_sha=source_sha,
        )

    assert result == 1
    select.assert_not_called()
    assert started == []
    assert not approved_path.exists()
    assert database.writes == []


def test_approved_lot_staging_state_drift_fails_before_harvester(tmp_path) -> None:
    database = FakeDB()
    approved = approved_lot(database)
    database.staging_rows[0]["status"] = "processing"
    started: list[list[str]] = []

    result, _payload, _raw, _digest, _approved_path, _cohort_path = run_approved_dispatch(
        database,
        tmp_path,
        source_runner=lambda _script, args, **_kwargs: started.append(list(args)) or True,
        approved=approved,
    )

    assert result == 1
    assert started == []
    assert database.writes == []
    assert database.staging_rows[0]["status"] == "processing"


@pytest.mark.parametrize("alias_url", [f"{URL_B}/", "https://b.example/en/programs"])
def test_approved_lot_matches_canonical_url_aliases_to_the_exact_snapshot(alias_url: str) -> None:
    database = FakeDB()
    database.staging_rows[0]["url"] = alias_url
    database.course_rows[0]["url"] = alias_url
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )

    orchestrator.verify_approved_lot_scope(database, approved)


def test_prepared_curl_dns_pin_is_one_resolve_list_entry(monkeypatch) -> None:
    resolve_entry = "b.example:443:93.184.216.34"
    monkeypatch.setattr(
        harvester_module,
        "public_url_resolve_entry",
        lambda _url: resolve_entry,
    )

    assert harvester_module._prepare_controlled_request(URL_B) == {
        harvester_module.CurlOpt.RESOLVE: [resolve_entry]
    }


def test_curl_cffi_accepts_the_dns_resolve_list_without_network() -> None:
    from curl_cffi import Curl

    curl = Curl()
    try:
        curl.setopt(
            harvester_module.CurlOpt.RESOLVE,
            ["synthetic.example:443:93.184.216.34"],
        )
    finally:
        curl.close()


class BoundedReadDB(FakeDB):
    """Fake that exposes only the bounded, fail-closed lookup interface."""

    def __init__(self) -> None:
        super().__init__()
        self.scoped_reads: list[tuple[str, str, int | None]] = []
        self.request_urls: list[tuple[str, str]] = []
        self.course_result_ids: list[tuple[str, ...]] = []

    def select_all_pipeline(self, *_args, **_kwargs):
        raise AssertionError("approved-lot verification must not scan a full pipeline table")

    def select_all_service(self, *_args, **_kwargs):
        raise AssertionError("approved-lot verification must not scan the full courses table")

    def _select_scoped(self, table: str, rows: list[dict], **kwargs):
        filters = kwargs.get("filters") or ""
        limit = kwargs.get("limit")
        self.scoped_reads.append((table, filters, limit))
        request_url = f"{self.supabase_url}/rest/v1/{table}?select={kwargs.get('columns', '*')}"
        if filters:
            request_url += f"&{filters}"
        if kwargs.get("order"):
            request_url += f"&order={kwargs['order']}"
        if limit:
            request_url += f"&limit={limit}"
        self.request_urls.append((table, request_url))
        for clause in filters.split("&"):
            if clause.startswith("url=match."):
                pattern = unquote(clause.removeprefix("url=match."))
                rows = [row for row in rows if re.fullmatch(pattern, row.get("url", ""))]
            elif "=in.(" in clause:
                column, values = clause.split("=in.(", 1)
                ids = set(values.removesuffix(")").split(","))
                rows = [row for row in rows if str(row.get(column)) in ids]
            elif clause.startswith("institution_id=eq."):
                wanted = clause.removeprefix("institution_id=eq.").lower()
                rows = [row for row in rows if str(row.get("institution_id", "")).lower() == wanted]
            elif clause.startswith("id=eq."):
                wanted = clause.removeprefix("id=eq.").lower()
                rows = [row for row in rows if str(row.get("id", "")).lower() == wanted]
        if kwargs.get("order") == "id.asc":
            rows = sorted(rows, key=lambda row: str(row.get("id", "")))
        return rows[:limit] if limit is not None else rows

    def select_pipeline_raise(self, table: str, **kwargs):
        rows = {
            "institution_site_profiles": self.profiles,
            "staging_raw": self.staging_rows,
            "cleansed_programs": self.cleansed_rows,
            "enriched_programs": self.enriched_rows,
        }[table]
        return self._select_scoped(table, list(rows), **kwargs)

    def select_service_raise(self, table: str, **kwargs):
        rows = {"institutions": self.institutions, "courses": self.course_rows}[table]
        records = self._select_scoped(table, list(rows), **kwargs)
        if table == "courses":
            self.course_result_ids.append(tuple(row["id"] for row in records))
        return records


@pytest.mark.parametrize(
    "alias_url",
    [
        "https://B.EXAMPLE/en/programs/",
        "https://b.example/programs/",
    ],
)
def test_approved_lot_alias_validation_uses_bounded_url_reads(alias_url: str) -> None:
    database = BoundedReadDB()
    database.staging_rows[0]["url"] = alias_url
    database.course_rows[0]["url"] = alias_url
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )

    orchestrator.verify_approved_lot_scope(database, approved)

    assert database.scoped_reads
    assert all(filters and limit == 2 for _table, filters, limit in database.scoped_reads)
    assert {table for table, _filters, _limit in database.scoped_reads} >= {
        "staging_raw",
        "courses",
        "cleansed_programs",
        "enriched_programs",
    }


def test_approved_lot_course_alias_reads_obey_final_url_budget_and_cover_all_aliases() -> None:
    database = BoundedReadDB()
    urls = [f"https://b.example/programs/course-{index:02d}" for index in range(10)]
    approved = approved_lot_for_urls(database, urls)

    orchestrator.verify_approved_lot_scope(database, approved)

    course_reads = [
        (filters, limit)
        for table, filters, limit in database.scoped_reads
        if table == "courses"
    ]
    course_request_urls = [
        request_url
        for table, request_url in database.request_urls
        if table == "courses"
    ]
    assert len(course_reads) == 1
    assert all(limit == len(urls) + 1 for _filters, limit in course_reads)
    assert all(len(request_url) <= fg2_run.APPROVED_SNAPSHOT_MAX_URL_CHARS for request_url in course_request_urls)

    aliases = set()
    for url in urls:
        identity = fg2_run.course_identity_url(url)
        aliases.update((url, identity))
        for suffix in fg2_run._CLEANSING_URL_SUFFIXES:
            detail_alias = fg2_run._approved_scope_url(f"{identity.rstrip('/')}/{suffix}")
            if fg2_run.course_identity_url(detail_alias) == identity:
                aliases.add(detail_alias)
    patterns = [unquote(filters.removeprefix("url=match.")) for filters, _limit in course_reads]
    assert all(any(re.fullmatch(pattern, alias) for pattern in patterns) for alias in aliases)


def test_approved_lot_pipeline_url_alias_reads_obey_final_url_budget_and_cover_all_urls() -> None:
    database = BoundedReadDB()
    urls = []
    for index in range(10):
        prefix = f"https://b.example/programs/course-{index:02d}-"
        urls.append(prefix + "a" * (1100 - len(prefix)))
    approved = approved_lot_for_urls(database, urls)

    orchestrator.verify_approved_lot_scope(database, approved)

    for table in ("staging_raw", "cleansed_programs", "enriched_programs"):
        reads = [
            (filters, limit)
            for read_table, filters, limit in database.scoped_reads
            if read_table == table and filters.startswith("url=match.")
        ]
        request_urls = [
            request_url
            for request_table, request_url in database.request_urls
            if request_table == table and "&url=match." in request_url
        ]
        assert len(reads) == 1
        assert all(limit == len(urls) + 1 for _filters, limit in reads)
        assert all(len(request_url) <= fg2_run.APPROVED_SNAPSHOT_MAX_URL_CHARS for request_url in request_urls)

        patterns = [unquote(filters.removeprefix("url=match.")) for filters, _limit in reads]
        assert all(any(re.fullmatch(pattern, url) for pattern in patterns) for url in urls)


def test_long_course_aliases_compact_shared_paths_without_changing_matches() -> None:
    database = BoundedReadDB()
    base = "https://b.example/programs/course-"
    urls = [
        base + f"{index:02d}-" + "a" * (2048 - len(base) - len(f"{index:02d}-"))
        for index in range(10)
    ]
    candidates = fg2_run._course_url_alias_candidates(urls)
    filters = fg2_run.course_url_alias_filters(urls, client=database, limit=len(urls) + 1)
    request_urls = [
        f"{database.supabase_url}/rest/v1/courses?select={fg2_run._COURSE_LOOKUP_COLUMNS}"
        f"&{query_filter}&order=id.asc&limit={len(urls) + 1}"
        for query_filter in filters
    ]
    actual_patterns = [unquote(item.removeprefix("url=match.")) for item in filters]
    original_patterns = [fg2_run._approved_url_alias_pattern(url) for url in candidates]

    root_url = "https://b.example/"
    root_pattern = unquote(fg2_run.approved_url_alias_filter([root_url]).removeprefix("url=match."))
    reference_root_pattern = fg2_run._approved_url_alias_pattern(root_url)
    for variant in (
        root_url,
        "https://b.example//",
        "https://b.example/en/",
        "https://b.example/en//",
        "https://b.example/?source=fixture",
        "https://b.example/en/?source=fixture",
        "https://b.example/programs",
    ):
        assert bool(re.fullmatch(root_pattern, variant)) is bool(
            re.fullmatch(reference_root_pattern, variant)
        )

    assert len(filters) == 1
    assert all(len(request_url) <= fg2_run.APPROVED_SNAPSHOT_MAX_URL_CHARS for request_url in request_urls)
    for candidate in candidates:
        variants = (
            candidate,
            f"{candidate}/",
            f"{candidate}?source=fixture",
            f"{candidate}#section",
            candidate.replace("https://b.example", "HTTPS://B.EXAMPLE", 1),
            candidate.replace("/programs/", "/programs/en/", 1),
            f"{candidate}-not-approved",
        )
        for variant in variants:
            expected = any(re.fullmatch(pattern, variant) for pattern in original_patterns)
            actual = any(re.fullmatch(pattern, variant) for pattern in actual_patterns)
            assert actual is expected

    pipeline_tables = (
        ("staging_raw", "id,institution_id,url,status,content_hash"),
        ("cleansed_programs", "id,staging_id,institution_id,url,status"),
        ("enriched_programs", "id,cleansed_id,institution_id,url,status"),
    )
    for table, columns in pipeline_tables:
        pipeline_filters = fg2_run._bounded_url_alias_filters(
            urls,
            client=database,
            table=table,
            columns=columns,
            limit=len(urls) + 1,
        )
        assert len(pipeline_filters) == 1
        pipeline_url = (
            f"{database.supabase_url}/rest/v1/{table}?select={columns}"
            f"&{pipeline_filters[0]}&order=id.asc&limit={len(urls) + 1}"
        )
        assert len(pipeline_url) <= fg2_run.APPROVED_SNAPSHOT_MAX_URL_CHARS
        pipeline_pattern = unquote(pipeline_filters[0].removeprefix("url=match."))
        original_pipeline_patterns = [fg2_run._approved_url_alias_pattern(url) for url in urls]
        for url in urls:
            variants = (url, f"{url}/", f"{url}?source=fixture", url.replace("/programs/", "/programs/en/", 1))
            for variant in variants:
                expected = any(re.fullmatch(pattern, variant) for pattern in original_pipeline_patterns)
                assert bool(re.fullmatch(pipeline_pattern, variant)) is expected

    with pytest.raises(fg2_run.InvalidControlledRun, match="approved FG2 lot exceeds its size limit"):
        approved_lot_for_urls(BoundedReadDB(), urls)


def test_valid_long_url_lot_alias_reads_stay_bounded() -> None:
    base = "https://b.example/programs/course-"
    urls = [
        base + f"{index:02d}-" + "a" * (2048 - len(base) - len(f"{index:02d}-"))
        for index in range(6)
    ]
    database = BoundedReadDB()
    approved = approved_lot_for_urls(database, urls)
    orchestrator.verify_approved_lot_scope(database, approved)
    reads_by_table = {}
    for table, _filters, _limit in database.scoped_reads:
        reads_by_table[table] = reads_by_table.get(table, 0) + 1
    assert reads_by_table == {
        "staging_raw": 1,
        "courses": 1,
        "cleansed_programs": 1,
        "enriched_programs": 1,
    }

    high_entropy_base = "https://b.example/programs/"
    high_entropy_urls = [
        high_entropy_base
        + hashlib.shake_256(f"long-url-{index}".encode()).hexdigest(1024)[
            : 2048 - len(high_entropy_base)
        ]
        for index in range(6)
    ]
    high_entropy_database = BoundedReadDB()
    high_entropy_approved = approved_lot_for_urls(high_entropy_database, high_entropy_urls)
    orchestrator.verify_approved_lot_scope(high_entropy_database, high_entropy_approved)
    high_entropy_reads_by_table = {}
    for table, _filters, _limit in high_entropy_database.scoped_reads:
        high_entropy_reads_by_table[table] = high_entropy_reads_by_table.get(table, 0) + 1
    assert high_entropy_reads_by_table == {
        "staging_raw": 2,
        "courses": 2,
        "cleansed_programs": 2,
        "enriched_programs": 2,
    }
    assert all(
        len(request_url) <= fg2_run.APPROVED_SNAPSHOT_MAX_URL_CHARS
        for _table, request_url in high_entropy_database.request_urls
    )


def test_many_path_segments_use_iterative_alias_trie() -> None:
    high_entropy_base = "https://b.example/programs/"
    deep_segment_url = high_entropy_base + "a/" * 1010
    deep_segment_pattern = unquote(
        fg2_run.approved_url_alias_filter([deep_segment_url]).removeprefix("url=match.")
    )
    reference_deep_pattern = fg2_run._approved_url_alias_pattern(deep_segment_url)
    for variant in (
        deep_segment_url,
        deep_segment_url.rstrip("/"),
        deep_segment_url.replace("/programs/", "/programs/en/", 1),
        f"{deep_segment_url}?source=fixture",
    ):
        assert bool(re.fullmatch(deep_segment_pattern, variant)) is bool(
            re.fullmatch(reference_deep_pattern, variant)
        )


def test_approved_course_alias_rejects_single_filter_over_url_budget(monkeypatch) -> None:
    database = BoundedReadDB()
    monkeypatch.setattr(fg2_run, "APPROVED_SNAPSHOT_MAX_URL_CHARS", 300)
    long_url = f"https://b.example/programs/{'a' * 256}"

    with pytest.raises(
        fg2_run.InvalidControlledRun,
        match="approved course URL alias exceeds the bounded request URL size",
    ):
        fg2_run.course_url_alias_filters([long_url], client=database, limit=2)


def test_approved_lot_deduplicates_course_ids_repeated_across_alias_chunks(monkeypatch) -> None:
    database = BoundedReadDB()
    approved = approved_lot_for_urls(database, [URL_B])
    expected_course_id = database.course_rows[0]["id"]
    monkeypatch.setattr(fg2_run, "APPROVED_SNAPSHOT_MAX_URL_CHARS", 500)
    original_select = database.select_service_raise

    def repeat_course_match(table: str, **kwargs):
        if table != "courses":
            return original_select(table, **kwargs)
        database._select_scoped(table, [], **kwargs)
        database.course_result_ids.append((expected_course_id,))
        return [dict(database.course_rows[0])]

    monkeypatch.setattr(database, "select_service_raise", repeat_course_match)

    orchestrator.verify_approved_lot_scope(database, approved)

    repeated_ids = [row_id for batch in database.course_result_ids for row_id in batch]
    assert len(database.course_result_ids) > 1
    assert repeated_ids.count(expected_course_id) > 1


def test_approved_lot_detects_course_alias_ambiguity_across_chunks(monkeypatch) -> None:
    database = BoundedReadDB()
    detail_url = f"{URL_B}/presentacion"
    approved = approved_lot_for_urls(database, [detail_url])
    expected_course_id = database.course_rows[0]["id"]
    database.course_rows.append(
        {
            "id": "70000000-0000-0000-0000-000000000099",
            "institution_id": INSTITUTION_B,
            "url": URL_B,
            "is_active": True,
            "is_verified": True,
            "last_404_at": None,
        }
    )
    monkeypatch.setattr(fg2_run, "APPROVED_SNAPSHOT_MAX_URL_CHARS", 500)

    with pytest.raises(orchestrator.InvalidControlledRun, match="canonical course URL is ambiguous"):
        orchestrator.verify_approved_lot_scope(database, approved)

    returned_ids = {row_id for batch in database.course_result_ids for row_id in batch}
    assert len(database.course_result_ids) > 1
    assert returned_ids == {expected_course_id, "70000000-0000-0000-0000-000000000099"}


def test_approved_lot_preflight_error_label_separates_read_failure_from_snapshot_mismatch() -> None:
    read_error = orchestrator.DatabaseAPIError(
        "DB select failed for courses: HTTP 400",
        table="courses",
        status_code=400,
    )
    mismatch = fg2_run.InvalidControlledRun("approved FG2 lot state drift detected")

    assert _approved_lot_preflight_error_label(read_error) == (
        "database_read_failed table=courses http_status=400"
    )
    assert _approved_lot_preflight_error_label(mismatch) == (
        "snapshot_mismatch: InvalidControlledRun"
    )


def test_approved_lot_new_staging_alias_check_uses_bounded_url_read() -> None:
    database = BoundedReadDB()
    payload, raw, digest = approved_lot(database)
    payload["scope"][0]["snapshot"]["staging_rows"] = []
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.staging_rows = []
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.approved_lot = approved
    harvester.approved_lot_scope = {
        item["url"]: item for item in approved.scope_for_institution(INSTITUTION_B)
    }

    assert harvester._select_staging_rows_by_url(URL_B) == []
    assert len(database.scoped_reads) == 1
    table, filters, limit = database.scoped_reads[0]
    assert table == "staging_raw"
    assert filters.startswith(f"institution_id=eq.{INSTITUTION_B}&url=match.")
    assert limit == 2

    database.staging_rows.append(
        {
            "id": "70000000-0000-0000-0000-000000000098",
            "institution_id": INSTITUTION_A,
            "url": "https://b.example/en/programs/",
            "status": "discovered",
            "content_hash": "e" * 64,
        }
    )
    assert harvester._select_staging_rows_by_url(URL_B) == []

    database.staging_rows.append(
        {
            "id": STAGING_B,
            "institution_id": INSTITUTION_B,
            "url": "https://b.example/en/programs/",
            "status": "discovered",
            "content_hash": "f" * 64,
        }
    )
    with pytest.raises(HarvesterRunError, match="staging identity appeared after preflight"):
        harvester._select_staging_rows_by_url(URL_B)
    assert database.writes == []


def test_approved_lot_detects_new_query_alias_with_bounded_reads() -> None:
    database = BoundedReadDB()
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.course_rows.append(
        {
            "id": "70000000-0000-0000-0000-000000000099",
            "institution_id": INSTITUTION_B,
            "url": f"{URL_B}?source=late-alias",
            "is_active": True,
            "is_verified": True,
            "last_404_at": None,
        }
    )

    with pytest.raises(orchestrator.InvalidControlledRun, match="canonical course URL is ambiguous"):
        orchestrator.verify_approved_lot_scope(database, approved)


@pytest.mark.parametrize(
    ("table", "expected_message"),
    [
        ("courses", "canonical course URL is ambiguous"),
        ("staging_raw", "canonical staging URL is ambiguous"),
    ],
)
def test_approved_lot_rejects_canonical_alias_drift_before_harvester(
    tmp_path, table: str, expected_message: str
) -> None:
    database = FakeDB()
    approved = approved_lot(database)
    if table == "courses":
        database.course_rows.append(
            {
                "id": "70000000-0000-0000-0000-000000000099",
                "institution_id": INSTITUTION_B,
                "url": f"{URL_B}/",
                "is_active": True,
                "is_verified": True,
            }
        )
    else:
        database.staging_rows.append(
            {
                "id": "40000000-0000-0000-0000-000000000099",
                "institution_id": INSTITUTION_B,
                "url": f"{URL_B}/",
                "status": "discovered",
                "content_hash": "e" * 64,
            }
        )
    approved_manifest = FG2ApprovedLotManifest.from_bytes(
        approved[1],
        approved[0],
        expected_sha256=approved[2],
        expected_reference=approved[0]["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    with pytest.raises(orchestrator.InvalidControlledRun, match=expected_message):
        orchestrator.verify_approved_lot_scope(database, approved_manifest)

    started: list[list[str]] = []

    result, _payload, _raw, _digest, _approved_path, _cohort_path = run_approved_dispatch(
        database,
        tmp_path,
        source_runner=lambda _script, args, **_kwargs: started.append(list(args)) or False,
        approved=approved,
    )

    assert result == 1
    assert started == []
    assert database.writes == []


def test_harvester_reads_approved_course_and_staging_rows_by_exact_id() -> None:
    database = FakeDB()
    alias_url = f"{URL_B}/"
    database.staging_rows[0]["url"] = alias_url
    database.course_rows[0]["url"] = alias_url
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.approved_lot = approved
    harvester._discovered_rows_by_url = {}
    harvester.approved_lot_scope = {
        item["url"]: item for item in approved.scope_for_institution(INSTITUTION_B)
    }

    staging = harvester._select_staging_rows_by_url(URL_B)
    course = harvester._course_for_refresh(URL_B)

    assert staging == database.staging_rows
    assert staging[0]["url"] == alias_url
    assert course == {
        "kind": "refresh_existing",
        "course_id": COURSE_B,
        "course_is_active": True,
        "course_is_verified": True,
        "course_url": alias_url,
        "course_last_404_at": None,
    }
    harvester.controlled = True
    harvester.approved_lot_scope_verified_for_write = True
    harvester._preflight_approved_scope_before_write(URL_B, staging, course)
    raw_html = "<html><body>synthetic refreshed program</body></html>"
    item = {
        "url": URL_B,
        "institution_id": INSTITUTION_B,
        "status": "pending",
        "raw_html": raw_html,
        "raw_name": "Synthetic program",
        "content_hash": hashlib.sha256(raw_html.encode()).hexdigest(),
    }
    promoted = harvester._promote_discovered_to_pending(
        {"id": STAGING_B, "url": URL_B},
        item,
    )

    assert promoted["url"] == alias_url
    assert database.staging_rows[0]["url"] == alias_url
    assert database.staging_rows[0]["status"] == "pending"


def test_approved_lot_manifest_hash_matches_exact_alias_url_persisted_to_staging(tmp_path: Path) -> None:
    database = FakeDB()
    alias_url = "https://b.example/en/programs/"
    database.staging_rows[0]["url"] = alias_url
    database.course_rows[0]["url"] = alias_url
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    scope = approved.scope_for_institution(INSTITUTION_B)[0]
    cohort_path = tmp_path / "result-cohort.json"
    initialize_manifest(
        cohort_path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[
            {
                "institution_id": INSTITUTION_B,
                "profile_sha256": payload["institutions"][0]["profile_sha256"],
                "seed_sha256": payload["institutions"][0]["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "complete",
            }
        ],
        approved_lot_reference=payload["reference"],
        approved_lot_sha256=digest,
    )
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.controlled = True
    harvester.approved_lot = approved
    harvester.approved_lot_scope = {URL_B: scope}
    harvester.approved_lot_scope_verified_for_write = True
    harvester._discovered_rows_by_url = {
        URL_B: {
            "id": STAGING_B,
            "url": URL_B,
            "status": "discovered",
            "kind": "refresh_existing",
            "course_id": COURSE_B,
        }
    }
    harvester.cohort_manifest_path = cohort_path
    raw_html = "<html><body>synthetic refreshed program</body></html>"
    item = {
        "url": URL_B,
        "institution_id": INSTITUTION_B,
        "status": "pending",
        "raw_html": raw_html,
        "raw_name": "Synthetic program",
        "content_hash": hashlib.sha256(raw_html.encode()).hexdigest(),
    }

    promoted = harvester._save_to_staging(item)
    manifest = FG2CohortManifest.load(cohort_path, allow_empty=True)

    assert promoted["url"] == alias_url
    assert database.staging_rows[0]["status"] == "pending"
    assert database.staging_rows[0]["url"] == alias_url
    assert manifest.payload["entries"][0]["url_sha256"] == url_sha256(alias_url)


def test_failed_discovered_promotion_does_not_enter_controlled_manifest(tmp_path: Path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    scope = approved.scope_for_institution(INSTITUTION_B)[0]
    cohort_path = tmp_path / "result-cohort.json"
    initialize_manifest(
        cohort_path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[
            {
                "institution_id": INSTITUTION_B,
                "profile_sha256": payload["institutions"][0]["profile_sha256"],
                "seed_sha256": payload["institutions"][0]["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "complete",
            }
        ],
        approved_lot_reference=payload["reference"],
        approved_lot_sha256=digest,
    )
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.controlled = True
    harvester.approved_lot = approved
    harvester.approved_lot_scope = {URL_B: scope}
    harvester.approved_lot_scope_verified_for_write = True
    harvester._discovered_rows_by_url = {
        URL_B: {
            "id": STAGING_B,
            "url": URL_B,
            "status": "discovered",
            "kind": "refresh_existing",
            "course_id": COURSE_B,
        }
    }
    harvester.cohort_manifest_path = cohort_path
    database.patch_exact_one_raise = Mock(
        side_effect=HarvesterRunError("synthetic pending PATCH failure")
    )
    raw_html = "<html><body>synthetic refreshed program</body></html>"
    item = {
        "url": URL_B,
        "institution_id": INSTITUTION_B,
        "status": "pending",
        "raw_html": raw_html,
        "raw_name": "Synthetic program",
        "content_hash": hashlib.sha256(raw_html.encode()).hexdigest(),
    }

    with pytest.raises(HarvesterRunError, match="pending promotion result is ambiguous"):
        harvester._save_to_staging(item)

    database.patch_exact_one_raise.assert_called_once()
    manifest = FG2CohortManifest.load(cohort_path, allow_empty=True)
    assert manifest.payload["entries"] == []
    assert database.staging_rows[0]["status"] == "discovered"


def test_lost_promotion_response_reconciles_exact_pending_row_into_manifest(tmp_path: Path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    scope = approved.scope_for_institution(INSTITUTION_B)[0]
    cohort_path = tmp_path / "result-cohort.json"
    initialize_manifest(
        cohort_path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[
            {
                "institution_id": INSTITUTION_B,
                "profile_sha256": payload["institutions"][0]["profile_sha256"],
                "seed_sha256": payload["institutions"][0]["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "complete",
            }
        ],
        approved_lot_reference=payload["reference"],
        approved_lot_sha256=digest,
    )
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.controlled = True
    harvester.approved_lot = approved
    harvester.approved_lot_scope = {URL_B: scope}
    harvester.approved_lot_scope_verified_for_write = True
    harvester._discovered_rows_by_url = {
        URL_B: {
            "id": STAGING_B,
            "url": URL_B,
            "status": "discovered",
            "kind": "refresh_existing",
            "course_id": COURSE_B,
        }
    }
    harvester.cohort_manifest_path = cohort_path
    raw_html = "<html><body>synthetic refreshed program</body></html>"
    item = {
        "url": URL_B,
        "institution_id": INSTITUTION_B,
        "status": "pending",
        "raw_html": raw_html,
        "raw_name": "Synthetic program",
        "content_hash": hashlib.sha256(raw_html.encode()).hexdigest(),
    }

    def apply_patch_then_lose_response(table, _filters, data, expected_id):
        row = next(row for row in database.staging_rows if row["id"] == expected_id)
        row.update(data)
        database.writes.append((table, _filters, dict(data)))
        raise HarvesterRunError("synthetic response lost after PATCH applied")

    database.patch_exact_one_raise = Mock(side_effect=apply_patch_then_lose_response)
    original_select = database.select_pipeline_raise
    database.select_pipeline_raise = Mock(wraps=original_select)

    promoted = harvester._save_to_staging(item)
    manifest = FG2CohortManifest.load(cohort_path, allow_empty=True)

    assert promoted["id"] == STAGING_B
    assert promoted["url"] == URL_B
    assert promoted["status"] == "pending"
    assert promoted["institution_id"] == INSTITUTION_B
    assert promoted["content_hash"] == item["content_hash"]
    assert manifest.payload["entries"] == [
        {
            "institution_id": INSTITUTION_B,
            "staging_id": STAGING_B,
            "course_id": COURSE_B,
            "url_sha256": url_sha256(URL_B),
            "cleansed_url_sha256": cleansed_url_sha256_for_record(URL_B),
            "content_sha256": item["content_hash"],
            "kind": "refresh_existing",
        }
    ]
    database.select_pipeline_raise.assert_called_once_with(
        "staging_raw",
        filters=f"id=eq.{STAGING_B}",
        columns="id,url,status,institution_id,content_hash",
        limit=2,
    )


def test_schedule_refresh_resolves_cleansing_suffix_to_existing_course_id() -> None:
    database = FakeDB()
    alias_url = f"{URL_B}/presentacion"
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.approved_lot = None

    course = harvester._course_for_refresh(alias_url)

    assert course == {"kind": "refresh_existing", "course_id": COURSE_B}


def test_schedule_refresh_resolves_language_alias_to_existing_course_id() -> None:
    database = FakeDB()
    database.course_rows[0]["url"] = URL_B.replace("https://b.example/", "https://b.example/en/", 1)
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.approved_lot = None

    course = harvester._course_for_refresh(URL_B)

    assert course == {"kind": "refresh_existing", "course_id": COURSE_B}


@pytest.mark.parametrize("requested_url", [URL_B, f"{URL_B}/presentacion"])
def test_schedule_refresh_finds_existing_course_stored_as_detail_alias(requested_url: str) -> None:
    database = FakeDB()
    database.course_rows[0]["url"] = f"{URL_B}/presentacion"
    database.course_rows.append(
        {
            "id": "70000000-0000-0000-0000-000000000099",
            "institution_id": INSTITUTION_B,
            "url": f"{URL_B}/presentacion-extra",
            "is_active": True,
            "is_verified": True,
        }
    )
    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.approved_lot = None

    course = harvester._course_for_refresh(requested_url)

    assert course == {"kind": "refresh_existing", "course_id": COURSE_B}


def test_approved_lot_binds_detail_alias_to_existing_parent_course() -> None:
    database = FakeDB()
    alias_url = f"{URL_B}/presentacion"
    database.course_rows[0]["url"] = alias_url
    next(profile for profile in database.profiles if profile["institution_id"] == INSTITUTION_B)[
        "seed_urls"
    ] = [alias_url]
    payload, _raw, _digest = approved_lot(database)
    scope = payload["scope"][0]
    scope["url"] = alias_url
    scope["url_sha256"] = url_sha256(alias_url)
    scope["snapshot"]["staging_rows"] = []
    scope["snapshot"]["course_rows"][0]["url"] = alias_url
    database.staging_rows = []
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    approved = FG2ApprovedLotManifest.from_bytes(
        raw,
        payload,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )

    orchestrator.verify_approved_lot_scope(database, approved)

    harvester = object.__new__(UniversalHarvester)
    harvester.db = database
    harvester.institution = {"id": INSTITUTION_B}
    harvester.approved_lot = approved
    harvester.approved_lot_scope = {alias_url: approved.scope_for_institution(INSTITUTION_B)[0]}
    assert harvester._course_for_refresh(alias_url)["kind"] == "refresh_existing"
    assert harvester._course_for_refresh(alias_url)["course_id"] == COURSE_B


def test_approved_lot_rejects_two_urls_for_one_canonical_course_identity() -> None:
    database = FakeDB()
    payload, _raw, _digest = approved_lot(database)
    alias_url = f"{URL_B}/presentacion"
    alias_scope = json.loads(json.dumps(payload["scope"][0]))
    alias_scope["url"] = alias_url
    alias_scope["url_sha256"] = url_sha256(alias_url)
    payload["scope"].append(alias_scope)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()

    with pytest.raises(ValueError, match="repeats a canonical course identity"):
        FG2ApprovedLotManifest.from_bytes(
            raw,
            payload,
            expected_sha256=digest,
            expected_reference=payload["reference"],
            expected_source_sha=SOURCE_SHA,
        )


def test_scope_drift_after_harvest_stops_before_first_staging_write(tmp_path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    lot_path = tmp_path / "approved-lot.json"
    lot_path.write_bytes(raw)
    lot = FG2ApprovedLotManifest.load(
        lot_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.staging_rows[0]["status"] = "processed"
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
    harvester.db = database
    harvester.controlled = True
    harvester.approved_lot = lot
    harvester.approved_lot_scope = {URL_B: lot.scope_for_institution(INSTITUTION_B)[0]}
    harvester.approved_lot_scope_verified_for_write = False
    harvester._discovered_rows_by_url = {}
    harvester._recorded_discovery_ids = set()
    harvester._recorded_blocker_ids = set()
    harvester.cohort_manifest_path = tmp_path / "result-cohort.json"

    with pytest.raises(HarvesterRunError, match="approved FG2 lot staging row drifted"):
        harvester._save_discovered_url(URL_B)

    assert database.writes == []
    assert database.staging_rows[0]["status"] == "processed"


def test_refresh_scope_drift_after_source_contact_stops_before_first_patch(tmp_path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    lot_path = tmp_path / "approved-lot.json"
    lot_path.write_bytes(raw)
    lot = FG2ApprovedLotManifest.load(
        lot_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.staging_rows[0]["content_hash"] = "e" * 64
    database.patch_exact_one_raise = Mock()
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
    harvester.db = database
    harvester.controlled = True
    harvester.approved_lot = lot
    harvester.approved_lot_scope = {URL_B: lot.scope_for_institution(INSTITUTION_B)[0]}
    harvester.approved_lot_scope_verified_for_write = False
    harvester._discovered_rows_by_url = {}

    raw_html = "<html><body>new source content</body></html>"
    item = {
        "url": URL_B,
        "institution_id": INSTITUTION_B,
        "status": "pending",
        "raw_html": raw_html,
        "raw_name": "Program",
        "content_hash": harvester._generate_hash(raw_html),
    }
    row = {"id": STAGING_B, "url": URL_B, "status": "discovered"}

    with pytest.raises(HarvesterRunError, match="approved FG2 lot staging row drifted"):
        harvester._promote_discovered_to_pending(row, item)

    database.patch_exact_one_raise.assert_not_called()
    assert database.writes == []


@pytest.mark.parametrize(
    ("drift", "expected_message"),
    [
        ("course_state", "approved FG2 course row drifted"),
        ("downstream_reference", "approved FG2 lot state drifted before the first write"),
    ],
)
def test_course_or_downstream_snapshot_drift_stops_before_first_write(
    tmp_path, drift: str, expected_message: str
) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    lot_path = tmp_path / "approved-lot.json"
    lot_path.write_bytes(raw)
    lot = FG2ApprovedLotManifest.load(
        lot_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    if drift == "course_state":
        database.course_rows[0]["is_verified"] = False
    else:
        database.cleansed_rows.append(
            {
                "id": "50000000-0000-0000-0000-000000000002",
                "staging_id": STAGING_B,
                "institution_id": INSTITUTION_B,
                "url": URL_B,
                "status": "pending",
            }
        )
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
    harvester.db = database
    harvester.controlled = True
    harvester.approved_lot = lot
    harvester.approved_lot_scope = {URL_B: lot.scope_for_institution(INSTITUTION_B)[0]}
    harvester.approved_lot_scope_verified_for_write = False
    harvester._discovered_rows_by_url = {}
    harvester._recorded_blocker_ids = set()
    harvester._recorded_discovery_ids = set()
    harvester.cohort_manifest_path = tmp_path / "result-cohort.json"

    with pytest.raises(HarvesterRunError, match=expected_message):
        harvester._save_discovered_url(URL_B)

    assert database.writes == []


def test_unapproved_url_is_rejected_before_a_staging_write(tmp_path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    lot_path = tmp_path / "approved-lot.json"
    lot_path.write_bytes(raw)
    lot = FG2ApprovedLotManifest.load(
        lot_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
    harvester.db = database
    harvester.controlled = True
    harvester.approved_lot = lot
    harvester.approved_lot_scope = {URL_B: lot.scope_for_institution(INSTITUTION_B)[0]}

    with pytest.raises(HarvesterRunError, match="outside the reviewed FG2 lot"):
        harvester._save_discovered_url("https://b.example/unreviewed")

    assert database.writes == []


def test_profile_or_seed_drift_after_harvest_stops_before_first_staging_write(tmp_path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    lot_path = tmp_path / "approved-lot.json"
    lot_path.write_bytes(raw)
    lot = FG2ApprovedLotManifest.load(
        lot_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.profiles[1]["seed_urls"] = ["https://b.example/changed/"]
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
    harvester.db = database
    harvester.controlled = True
    harvester.approved_lot = lot
    harvester.approved_lot_scope = {URL_B: lot.scope_for_institution(INSTITUTION_B)[0]}
    harvester.approved_lot_scope_verified_for_write = False
    harvester._discovered_rows_by_url = {}
    harvester._recorded_discovery_ids = set()
    harvester._recorded_blocker_ids = set()
    harvester.cohort_manifest_path = tmp_path / "result-cohort.json"

    with pytest.raises(HarvesterRunError, match="institution, profile, or seeds drifted"):
        harvester._save_discovered_url(URL_B)

    assert database.writes == []
    assert database.staging_rows[0]["status"] == "discovered"


def test_profile_or_seed_drift_fails_before_first_source_request(tmp_path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    lot_path = tmp_path / "approved-lot.json"
    lot_path.write_bytes(raw)
    lot = FG2ApprovedLotManifest.load(
        lot_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.profiles[1]["seed_urls"] = ["https://b.example/changed/"]
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
    harvester.db = database
    harvester.controlled = True
    harvester.approved_lot = lot
    harvester.approved_lot_scope = {URL_B: lot.scope_for_institution(INSTITUTION_B)[0]}
    harvester.request_budget = SimpleNamespace(http_requests=0, get=AsyncMock())

    async def scenario():
        with pytest.raises(HarvesterRunError, match="institution, profile, or seeds drifted"):
            await harvester._safe_request(object(), URL_B)

    asyncio.run(scenario())

    harvester.request_budget.get.assert_not_awaited()
    assert database.writes == []


def test_controlled_browser_navigation_fails_before_playwright_request() -> None:
    harvester = object.__new__(UniversalHarvester)
    harvester.controlled = True
    page = SimpleNamespace(goto=AsyncMock())

    async def scenario() -> None:
        with pytest.raises(HarvesterRunError, match="outside the request budget"):
            await harvester._navigate_browser_page(page, URL_B, wait_until="domcontentloaded")

    asyncio.run(scenario())
    page.goto.assert_not_awaited()


def test_ordinary_browser_navigation_preserves_existing_page_goto_without_interceptor() -> None:
    class SyntheticPage:
        def __init__(self) -> None:
            self.goto = AsyncMock(return_value="loaded")
            self.route_calls = []

        async def route(self, pattern, handler):
            self.route_calls.append((pattern, handler))

    harvester = object.__new__(UniversalHarvester)
    harvester.controlled = False
    harvester._browser_guarded_page_ids = set()
    page = SyntheticPage()

    async def scenario() -> None:
        response = await harvester._navigate_browser_page(page, URL_B, wait_until="domcontentloaded")
        assert response == "loaded"

    asyncio.run(scenario())
    page.goto.assert_awaited_once()
    assert page.route_calls == []


def test_paginated_catalog_deduplicates_same_url_across_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    class SyntheticSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    response = SimpleNamespace(
        status_code=200,
        text='<a class="course" href="/program/course">Course</a>',
    )
    monkeypatch.setattr(harvester_module, "AsyncSession", SyntheticSession)
    harvester = object.__new__(UniversalHarvester)
    harvester.profile = {
        "catalog_url_patterns": ["https://synthetic.example/catalog?page={page}"],
    }
    harvester.catalog_max_pages = 2
    harvester.catalog_link_selector = "a.course"
    harvester.site_type = "traditional_ssr"
    harvester.controlled = False
    harvester._discovery_fetch_attempts = 0
    harvester._discovery_fetch_successes = 0
    harvester.course_urls = set()
    harvester.max_discovered_urls = None
    harvester.check_time_guard = lambda: False
    harvester._can_discover_more = lambda: True
    harvester._load_existing_urls = AsyncMock(return_value=set())
    harvester._safe_request = AsyncMock(return_value=response)
    harvester._is_valid_crawl_url = lambda _url: True
    queued = Mock(return_value={"status": "discovered"})
    harvester._queue_discovered_candidate = queued
    harvester._merge_resumable_urls = lambda urls: urls
    harvester._limit_urls = lambda urls: urls

    result = asyncio.run(harvester.discover_paginated_catalog())

    assert result == ["https://synthetic.example/program/course"]
    queued.assert_called_once_with("https://synthetic.example/program/course")


@pytest.mark.parametrize(
    "blocked_url",
    [
        "http://127.0.0.1/sitemap.xml",
        "http://10.0.0.9/sitemap.xml",
        "http://169.254.169.254/latest/meta-data/",
    ],
)
def test_ordinary_harvester_blocks_nonpublic_initial_request_before_transport(
    blocked_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    harvester = object.__new__(UniversalHarvester)
    harvester.controlled = False
    harvester.institution = {"name": "Synthetic", "website_url": URL_B}
    harvester.error_count = 0
    harvester.max_consecutive_errors = 3
    harvester.circuit_open = False
    monkeypatch.setattr(
        harvester_module,
        "public_url_resolve_entry",
        lambda _url: (_ for _ in ()).throw(UnsafePublicTarget("nonpublic fixture")),
    )
    monkeypatch.setattr(
        harvester_module,
        "AsyncSession",
        lambda **_kwargs: pytest.fail("nonpublic URL reached HTTP transport"),
    )

    result = asyncio.run(harvester._safe_request(object(), blocked_url))

    assert result is None


def test_ordinary_harvester_rejects_private_redirect_before_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    redirect_response = SimpleNamespace(
        status_code=302,
        url=URL_B,
        headers={"location": "http://169.254.169.254/latest/meta-data/"},
        close=Mock(),
    )

    class PinnedSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url: str, **_kwargs):
            calls.append(url)
            return redirect_response

    harvester = object.__new__(UniversalHarvester)
    harvester.controlled = False
    harvester.institution = {"name": "Synthetic", "website_url": URL_B}
    harvester.error_count = 0
    harvester.max_consecutive_errors = 3
    harvester.circuit_open = False
    harvester.impersonate = "chrome110"
    def validate_request(url: str, **_kwargs):
        if "169.254.169.254" in url:
            raise UnsafePublicTarget("private redirect fixture")
        return "https://b.example:443", "b.example:443:93.184.216.34"

    monkeypatch.setattr(harvester_module, "validate_public_request_url", validate_request)

    def validate_redirect(_current: str, location: str, **_kwargs):
        assert "169.254.169.254" in location
        raise UnsafePublicTarget("private redirect fixture")

    monkeypatch.setattr(harvester_module, "validate_public_redirect_target", validate_redirect)
    monkeypatch.setattr(harvester_module, "AsyncSession", lambda **_kwargs: PinnedSession())
    monkeypatch.setattr(harvester_module.asyncio, "sleep", AsyncMock())

    result = asyncio.run(harvester._safe_request(object(), URL_B))

    assert result is None
    assert calls == [URL_B]
    redirect_response.close.assert_called_once()


def test_ordinary_harvester_pins_each_public_redirect_with_a_resolve_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redirect_url = "https://b.example/programs/next"
    responses = [
        SimpleNamespace(
            status_code=302,
            url=URL_B,
            headers={"location": "/programs/next"},
            close=Mock(),
        ),
        SimpleNamespace(status_code=200, url=redirect_url, headers={}, close=Mock()),
    ]
    session_options: list[dict[str, Any]] = []
    request_urls: list[str] = []

    class PinnedSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url: str, **_kwargs):
            request_urls.append(url)
            return responses.pop(0)

    def create_session(**kwargs):
        session_options.append(kwargs)
        return PinnedSession()

    monkeypatch.setattr(
        harvester_module,
        "validate_public_request_url",
        lambda _url: ("https://b.example:443", "b.example:443:93.184.216.34"),
    )
    monkeypatch.setattr(
        harvester_module,
        "validate_public_redirect_target",
        lambda _current, _location: (
            redirect_url,
            "b.example:443:93.184.216.35",
        ),
    )
    monkeypatch.setattr(harvester_module, "AsyncSession", create_session)
    monkeypatch.setattr(harvester_module.asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(harvester_module.random, "uniform", lambda *_args: 0)

    harvester = object.__new__(UniversalHarvester)
    harvester.controlled = False
    harvester.institution = {"name": "Synthetic", "website_url": URL_B}
    harvester.error_count = 0
    harvester.max_consecutive_errors = 3
    harvester.circuit_open = False
    harvester.impersonate = "chrome110"

    result = asyncio.run(harvester._safe_request(object(), URL_B))

    assert result.status_code == 200
    assert request_urls == [URL_B, redirect_url]
    assert [
        options["curl_options"][harvester_module.CurlOpt.RESOLVE]
        for options in session_options
    ] == [
        ["b.example:443:93.184.216.34"],
        ["b.example:443:93.184.216.35"],
    ]


def test_all_direct_playwright_navigation_is_behind_the_controlled_mode_guard() -> None:
    source = Path(__file__).parents[1] / "scripts/core/universal_harvester.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    navigation_calls: list[str | None] = []

    class NavigationVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.function_name: str | None = None

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            previous = self.function_name
            self.function_name = node.name
            self.generic_visit(node)
            self.function_name = previous

        def visit_Call(self, node: ast.Call) -> None:
            function = node.func
            if (
                isinstance(function, ast.Attribute)
                and function.attr == "goto"
                and isinstance(function.value, ast.Name)
                and function.value.id == "page"
            ):
                navigation_calls.append(self.function_name)
            self.generic_visit(node)

    NavigationVisitor().visit(tree)
    assert navigation_calls == ["_navigate_browser_page"]


def test_staging_state_drift_fails_before_first_source_request(tmp_path) -> None:
    database = FakeDB()
    payload, raw, digest = approved_lot(database)
    lot_path = tmp_path / "approved-lot.json"
    lot_path.write_bytes(raw)
    lot = FG2ApprovedLotManifest.load(
        lot_path,
        expected_sha256=digest,
        expected_reference=payload["reference"],
        expected_source_sha=SOURCE_SHA,
    )
    database.staging_rows[0]["status"] = "processing"
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_B, "slug": "b", "website_url": "https://b.example"}
    harvester.db = database
    harvester.controlled = True
    harvester.approved_lot = lot
    harvester.approved_lot_scope = {URL_B: lot.scope_for_institution(INSTITUTION_B)[0]}
    harvester.request_budget = SimpleNamespace(http_requests=0, get=AsyncMock())

    async def scenario():
        with pytest.raises(HarvesterRunError, match="state drifted before the first source request"):
            await harvester._safe_request(object(), URL_B)

    asyncio.run(scenario())

    harvester.request_budget.get.assert_not_awaited()
    assert database.writes == []


@pytest.mark.parametrize("status", [200, 403, 429])
def test_controlled_stream_uses_pinned_curl_cffi_response_content(status: int) -> None:
    from curl_cffi.requests import Response

    class SyntheticCurlResponse(Response):
        def __init__(self) -> None:
            super().__init__()
            self.status_code = status
            self.chunks_read = 0
            self.closed_for_test = False

        async def aiter_content(self):
            self.chunks_read += 1
            yield b"<html>fixture</html>"

        async def aclose(self):
            self.closed_for_test = True

    class SyntheticSession:
        def __init__(self, response) -> None:
            self.response = response
            self.calls = 0

        async def get(self, *_args, **_kwargs):
            self.calls += 1
            return self.response

    response = SyntheticCurlResponse()
    session = SyntheticSession(response)

    async def scenario() -> None:
        if status in {403, 429}:
            with pytest.raises(harvester_module.SourceBlocked):
                await harvester_module._request_with_body_limit(
                    session, "https://fixture.invalid/", "chrome", 1
                )
            assert response.content == b""
            assert response.chunks_read == 0
            assert response.closed_for_test
        else:
            result = await harvester_module._request_with_body_limit(
                session, "https://fixture.invalid/", "chrome", 1
            )
            assert result is response
            assert response.content == b"<html>fixture</html>"
            assert response.chunks_read == 1
        assert session.calls == 1

    asyncio.run(scenario())
