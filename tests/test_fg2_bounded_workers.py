"""Synthetic queue isolation contracts for every downstream FG2 stage."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

core_script_dir = str(Path(__file__).resolve().parents[1] / "scripts" / "core")
if core_script_dir not in sys.path:
    sys.path.insert(0, core_script_dir)

from scripts.core.cleansing_worker import CleansingWorker
from scripts.core.enrichment_worker import EnrichmentWorker
from scripts.core.fg2_bounded_run import (
    FG2CohortManifest,
    InvalidControlledRun,
    FG2_LIMITS,
    url_sha256,
)
from scripts.core.sync_vector_worker import SyncVectorWorker


INSTITUTION_ID = "00000000-0000-0000-0000-000000000001"
RAW_ID = "40000000-0000-0000-0000-000000000001"
CLEANSED_ID = "50000000-0000-0000-0000-000000000001"
ENRICHED_ID = "60000000-0000-0000-0000-000000000001"
URL = "https://synthetic.example/program/known"
RAW_HTML = "<!doctype html><html><title>Known Program</title><body>synthetic fixture</body></html>"
CONTENT_SHA = hashlib.sha256(RAW_HTML.encode()).hexdigest()


def cohort_manifest() -> FG2CohortManifest:
    return FG2CohortManifest.from_payload(
        {
            "schema_version": 1,
            "run_id": "123456789",
            "run_attempt": 1,
            "source_sha": "a" * 40,
            "limits": dict(FG2_LIMITS),
            "institutions": [
                {
                    "institution_id": INSTITUTION_ID,
                    "profile_sha256": "b" * 64,
                    "seed_sha256": "c" * 64,
                    "http_requests": 2,
                    "unique_urls": 1,
                    "result": "complete",
                }
            ],
            "entries": [
                {
                    "institution_id": INSTITUTION_ID,
                    "staging_id": RAW_ID,
                    "course_id": "70000000-0000-0000-0000-000000000001",
                    "url_sha256": url_sha256(URL),
                    "content_sha256": CONTENT_SHA,
                    "kind": "refresh_existing",
                }
            ],
            "blocked_staging_rows": [],
        }
    )


class SelectAdapter:
    def __init__(self, responses: dict[str, list[dict]], profiles: list[dict] | None = None) -> None:
        self.responses = responses
        self.profiles = profiles or [
            {"institution_id": INSTITUTION_ID, "pipeline_enabled": True, "exclusion_patterns": []}
        ]
        self.calls: list[tuple[str, str]] = []

    def select_pipeline_raise(self, table: str, **_kwargs):
        if table == "institution_site_profiles":
            return [dict(row) for row in self.profiles]
        return [dict(row) for row in self.responses.get(table, [])]

    def select_all_pipeline(self, table: str, filters: str = "", **_kwargs):
        self.calls.append((table, filters))
        return [dict(row) for row in self.responses.get(table, [])]


def raw_row() -> dict:
    return {
        "id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "content_hash": CONTENT_SHA,
        "raw_html": RAW_HTML,
        "status": "pending",
    }


def test_cleansing_reads_only_manifest_staging_ids_and_rejects_queue_leak() -> None:
    manifest = cohort_manifest()
    database = SelectAdapter({"staging_raw": [raw_row()]})
    worker = CleansingWorker(db_client=database)
    rows = list(worker.stream_pending_staging(cohort_manifest=manifest))
    assert [row["id"] for row in rows] == [RAW_ID]
    assert database.calls == [("staging_raw", f"id=in.({RAW_ID})")]

    database.responses["staging_raw"].append(
        dict(raw_row(), id="40000000-0000-0000-0000-000000000099")
    )
    with pytest.raises(InvalidControlledRun, match="outside the frozen cohort"):
        list(worker.stream_pending_staging(cohort_manifest=manifest))


def test_enrichment_reads_only_cleansed_children_of_manifest_raw_ids() -> None:
    manifest = cohort_manifest()
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed]})
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}

    assert worker.get_pending_cleansed(cohort_manifest=manifest) == [cleansed]
    assert database.calls == [
        ("cleansed_programs", f"status=eq.pending&staging_id=in.({RAW_ID})")
    ]

    database.responses["cleansed_programs"].append(
        dict(cleansed, id="50000000-0000-0000-0000-000000000099", staging_id="40000000-0000-0000-0000-000000000099")
    )
    with pytest.raises(InvalidControlledRun, match="outside the frozen cohort"):
        worker.get_pending_cleansed(cohort_manifest=manifest)


def test_sync_reads_only_enriched_children_of_manifest_cleansed_ids() -> None:
    manifest = cohort_manifest()
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "status": "enriched",
    }
    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed], "enriched_programs": [enriched]})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}

    assert worker.get_pending_enriched(cohort_manifest=manifest) == [
        dict(enriched, _fg2_approved_course_id="70000000-0000-0000-0000-000000000001")
    ]
    assert database.calls == [
        ("cleansed_programs", f"staging_id=in.({RAW_ID})"),
        ("enriched_programs", f"status=eq.pending&cleansed_id=in.({CLEANSED_ID})"),
    ]

    database.responses["enriched_programs"].append(
        dict(enriched, id="60000000-0000-0000-0000-000000000099", cleansed_id="50000000-0000-0000-0000-000000000099")
    )
    with pytest.raises(InvalidControlledRun, match="outside the frozen cohort"):
        worker.get_pending_enriched(cohort_manifest=manifest)
