"""Offline tests for rotation and exact cohort selection in controlled FG2."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

from scripts.core import master_orchestrator as orchestrator


INSTITUTION_A = "00000000-0000-0000-0000-000000000001"
INSTITUTION_B = "00000000-0000-0000-0000-000000000002"


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
        self.writes: list[tuple] = []

    def select_service_raise(self, table: str, **kwargs):
        assert table == "institutions"
        assert kwargs["order"] == "last_harvest_at.asc.nullsfirst"
        return list(self.institutions)

    def select_pipeline_raise(self, table: str, **kwargs):
        assert table == "institution_site_profiles"
        return list(self.profiles)

    def count_pipeline_raise(self, *_args, **_kwargs):
        return 0

    def patch(self, *args, **kwargs):
        self.writes.append((args, kwargs))


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


def test_controlled_orchestrator_stops_after_child_failure_before_next_source(tmp_path: Path) -> None:
    institutions = [
        {
            "id": institution_id,
            "name": slug.upper(),
            "slug": slug,
            "website_url": f"https://{slug}.example/",
            "_controlled_profile_sha256": ("b" if index == 0 else "c") * 64,
            "_controlled_seed_sha256": ("d" if index == 0 else "e") * 64,
        }
        for index, (institution_id, slug) in enumerate(
            ((INSTITUTION_A, "a"), (INSTITUTION_B, "b"))
        )
    ]
    started: list[list[str]] = []
    manifest_path = tmp_path / "controlled.json"
    env = {
        "GITHUB_RUN_ID": "123456789",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_REF": "refs/heads/main",
    }
    with (
        patch.dict(os.environ, env, clear=False),
        patch.object(orchestrator, "get_institutions", return_value=institutions),
        patch.object(orchestrator, "run_script", side_effect=lambda _path, args, **_kwargs: started.append(args) or False),
    ):
        result = orchestrator.main(
            ["--controlled-first-run", "--cohort-manifest", str(manifest_path)]
        )

    assert result == 1
    assert len(started) == 1
    assert "--controlled" in started[0]
    assert "--cohort-manifest" in started[0]


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
