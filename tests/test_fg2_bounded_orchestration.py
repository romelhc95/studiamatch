"""Offline tests for rotation and exact cohort selection in controlled FG2."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import base64
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import AsyncMock, Mock, patch
from types import SimpleNamespace
from urllib.parse import unquote

import pytest

from scripts.core import master_orchestrator as orchestrator
from scripts.core.universal_harvester import HarvesterRunError, UniversalHarvester
from scripts.core.fg2_bounded_run import (
    FG2ApprovedLotManifest,
    FG2CohortManifest,
    FG2_LIMITS,
    append_manifest_discovery_row,
    append_manifest_entry,
    stable_json_sha256,
    update_manifest_institution,
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
            return [
                row for row in self.profiles
                if not filters or str(row.get("institution_id", "")).lower() == institution_id
            ]
        if table == "staging_raw":
            return list(self.staging_rows)
        raise AssertionError(f"unexpected pipeline read: {table}")

    def select_service_raise(self, table: str, **kwargs):
        if table == "institutions":
            filters = kwargs.get("filters", "")
            institution_id = filters.removeprefix("id=eq.").lower()
            return [
                row for row in self.institutions
                if not filters or str(row.get("id", "")).lower() == institution_id
            ]
        if table == "courses":
            return list(self.course_rows)
        raise AssertionError(f"unexpected service read: {table}")

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


def approved_lot(database: FakeDB) -> tuple[dict, bytes, str]:
    institution = next(row for row in database.institutions if row["id"] == INSTITUTION_B)
    profile = next(row for row in database.profiles if row["institution_id"] == INSTITUTION_B)
    preflight = validate_controlled_profile(institution, profile)
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
