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
from scripts.core.enrichment_worker import ControlledEnrichmentUnavailable, EnrichmentWorker
from scripts.core.fg2_bounded_run import (
    FG2CohortManifest,
    InvalidControlledRun,
    FG2_LIMITS,
    cleanse_course_url,
    cleansed_url_sha256,
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


def cohort_manifest(result: str = "complete") -> FG2CohortManifest:
    payload = {
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
                "result": result,
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
    return FG2CohortManifest.from_payload(payload)


class SelectAdapter:
    def __init__(self, responses: dict[str, list[dict]], profiles: list[dict] | None = None) -> None:
        self.responses = responses
        self.profiles = profiles or [
            {"institution_id": INSTITUTION_ID, "pipeline_enabled": True, "exclusion_patterns": []}
        ]
        self.calls: list[tuple[str, str]] = []
        self.writes: list[tuple[str, str, dict]] = []

    def select_pipeline_raise(self, table: str, **_kwargs):
        if table == "institution_site_profiles":
            return [dict(row) for row in self.profiles]
        return [dict(row) for row in self.responses.get(table, [])]

    def select_all_pipeline(self, table: str, filters: str = "", **_kwargs):
        self.calls.append((table, filters))
        return [dict(row) for row in self.responses.get(table, [])]

    def upsert(self, table: str, data: dict, **_kwargs):
        self.writes.append(("upsert", table, data))
        return {"id": data.get("id")}

    def patch(self, table: str, filters: str, data: dict, **_kwargs):
        self.writes.append(("patch", table, data))
        return True


def raw_row() -> dict:
    return {
        "id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "content_hash": CONTENT_SHA,
        "raw_html": RAW_HTML,
        "status": "pending",
    }


@pytest.mark.parametrize("result", ["complete", "partial"])
def test_cleansing_reads_only_manifest_staging_ids_and_rejects_queue_leak(result: str) -> None:
    manifest = cohort_manifest(result)
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


def test_empty_schedule_manifest_never_falls_back_to_global_worker_queues() -> None:
    payload = dict(cohort_manifest().payload)
    payload["entries"] = []
    manifest = FG2CohortManifest.from_payload(payload, allow_empty=True)
    database = SelectAdapter(
        {
            "staging_raw": [raw_row()],
            "cleansed_programs": [
                {
                    "id": CLEANSED_ID,
                    "staging_id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                }
            ],
            "enriched_programs": [
                {
                    "id": ENRICHED_ID,
                    "cleansed_id": CLEANSED_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                }
            ],
        }
    )
    cleansing = CleansingWorker(db_client=database)
    enrichment = EnrichmentWorker.__new__(EnrichmentWorker)
    enrichment.db = database
    enrichment.ready_inst_ids = {INSTITUTION_ID}
    sync = SyncVectorWorker.__new__(SyncVectorWorker)
    sync.db = database
    sync.ready_inst_ids = {INSTITUTION_ID}

    assert list(cleansing.stream_pending_staging(cohort_manifest=manifest)) == []
    assert enrichment.get_pending_cleansed(cohort_manifest=manifest) == []
    assert sync.get_pending_enriched(cohort_manifest=manifest) == []
    assert database.calls == []
    assert database.writes == []


@pytest.mark.parametrize("result", ["complete", "partial"])
def test_enrichment_reads_only_cleansed_children_of_manifest_raw_ids(result: str) -> None:
    manifest = cohort_manifest(result)
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed]})
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}

    expected_cleansed = dict(
        cleansed,
        _fg2_expected_url_sha256=url_sha256(URL),
        _fg2_expected_raw_url_sha256=url_sha256(URL),
        _fg2_manifest_staging_id=RAW_ID,
        _fg2_manifest_content_sha256=CONTENT_SHA,
    )
    assert worker.get_pending_cleansed(cohort_manifest=manifest) == [expected_cleansed]
    assert database.calls == [
        ("cleansed_programs", f"status=eq.pending&staging_id=in.({RAW_ID})")
    ]

    database.responses["cleansed_programs"].append(
        dict(cleansed, id="50000000-0000-0000-0000-000000000099", staging_id="40000000-0000-0000-0000-000000000099")
    )
    with pytest.raises(InvalidControlledRun, match="outside the frozen cohort"):
        worker.get_pending_cleansed(cohort_manifest=manifest)


def test_enrichment_rejects_url_substitution_after_selection_before_provider_or_write() -> None:
    manifest = cohort_manifest()
    changed_url = "https://synthetic.example/program/substituted"
    row = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
    }
    database = SelectAdapter(
        {
            "cleansed_programs": [row],
            "staging_raw": [
                {
                    "id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "processed",
                    "content_hash": CONTENT_SHA,
                }
            ],
        }
    )
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}
    selected = worker.get_pending_cleansed(cohort_manifest=manifest)
    assert len(selected) == 1
    database.responses["cleansed_programs"][0]["url"] = changed_url
    database.responses["staging_raw"][0]["url"] = changed_url
    worker._fetch_sr_enrichment_data = lambda *_args: pytest.fail(
        "URL drift must stop before source lookup/provider work"
    )

    with pytest.raises(InvalidControlledRun, match="URL identity changed"):
        worker.enrich_record(selected[0])
    assert database.writes == []


@pytest.mark.parametrize("result", ["complete", "partial"])
def test_sync_reads_only_enriched_children_of_manifest_cleansed_ids(result: str) -> None:
    manifest = cohort_manifest(result)
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "enriched",
    }
    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed], "enriched_programs": [enriched]})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}

    assert worker.get_pending_enriched(cohort_manifest=manifest) == [
        dict(
            enriched,
            _fg2_approved_course_id="70000000-0000-0000-0000-000000000001",
            _fg2_expected_url_sha256=url_sha256(URL),
            _fg2_expected_raw_url_sha256=url_sha256(URL),
            _fg2_manifest_staging_id=RAW_ID,
            _fg2_manifest_cleansed_id=CLEANSED_ID,
            _fg2_manifest_content_sha256=CONTENT_SHA,
        )
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


def test_sync_rejects_url_substitution_after_selection_before_course_writer() -> None:
    manifest = cohort_manifest()
    changed_url = "https://synthetic.example/program/substituted"
    database = SelectAdapter(
        {
            "staging_raw": [
                {
                    "id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "processed",
                    "content_hash": CONTENT_SHA,
                }
            ],
            "cleansed_programs": [
                {
                    "id": CLEANSED_ID,
                    "staging_id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "enriched",
                }
            ],
            "enriched_programs": [
                {
                    "id": ENRICHED_ID,
                    "cleansed_id": CLEANSED_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                }
            ],
        }
    )
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}
    selected = worker.get_pending_enriched(cohort_manifest=manifest)
    assert len(selected) == 1
    database.responses["staging_raw"][0]["url"] = changed_url
    database.responses["cleansed_programs"][0]["url"] = changed_url
    database.responses["enriched_programs"][0]["url"] = changed_url
    with pytest.raises(InvalidControlledRun, match="URL identity changed"):
        worker.sync_to_production(selected[0])
    assert database.writes == []


def test_manifest_identity_accepts_cleansing_url_normalization_and_still_checks_raw_url() -> None:
    raw_url = "https://synthetic.example/program/presentacion/"
    cleansed_url = cleanse_course_url(raw_url)
    payload = dict(cohort_manifest().payload)
    payload["entries"] = [
        dict(
            payload["entries"][0],
            url_sha256=url_sha256(raw_url),
            cleansed_url_sha256=cleansed_url_sha256(raw_url),
        )
    ]
    manifest = FG2CohortManifest.from_payload(payload)
    raw = dict(raw_row(), url=raw_url, status="processed")
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": cleansed_url,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed], "staging_raw": [raw]})
    enrichment = EnrichmentWorker.__new__(EnrichmentWorker)
    enrichment.db = database
    enrichment.ready_inst_ids = {INSTITUTION_ID}

    selected_cleansed = enrichment.get_pending_cleansed(cohort_manifest=manifest)
    assert selected_cleansed[0]["url"] == cleansed_url
    enrichment._verify_fg2_manifest_url_identity(selected_cleansed[0])

    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": cleansed_url,
        "status": "pending",
    }
    database.responses["cleansed_programs"][0]["status"] = "enriched"
    database.responses["enriched_programs"] = [enriched]
    sync = SyncVectorWorker.__new__(SyncVectorWorker)
    sync.db = database
    sync.ready_inst_ids = {INSTITUTION_ID}

    selected_enriched = sync.get_pending_enriched(cohort_manifest=manifest)
    assert selected_enriched[0]["url"] == cleansed_url
    sync._verify_fg2_manifest_url_identity(selected_enriched[0])

    database.responses["staging_raw"][0]["url"] = "https://synthetic.example/changed/"
    with pytest.raises(InvalidControlledRun, match="URL identity changed"):
        enrichment._verify_fg2_manifest_url_identity(selected_cleansed[0])


def test_controlled_sync_rejects_mock_enrichment_before_any_write() -> None:
    manifest = cohort_manifest()
    database = SelectAdapter(
        {
            "staging_raw": [dict(raw_row(), status="processed")],
            "cleansed_programs": [
                {
                    "id": CLEANSED_ID,
                    "staging_id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "enriched",
                }
            ],
            "enriched_programs": [
                {
                    "id": ENRICHED_ID,
                    "cleansed_id": CLEANSED_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                    "official_name": "Synthetic Program",
                    "is_mock_data": True,
                }
            ],
        }
    )
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}
    selected = worker.get_pending_enriched(cohort_manifest=manifest)

    assert len(selected) == 1
    assert worker.sync_to_production(selected[0]) is False
    assert database.writes == []


def test_sync_rejects_unbounded_mock_enrichment_without_provider_flag(monkeypatch) -> None:
    monkeypatch.delenv("FG2_REQUIRE_REAL_PROVIDER", raising=False)
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "mock",
            "is_mock_data": True,
        }
    ) is False
    assert database.writes == []


def test_sync_rejects_mock_provider_label_without_provider_flag(monkeypatch) -> None:
    monkeypatch.delenv("FG2_REQUIRE_REAL_PROVIDER", raising=False)
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "smart-mock",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_sync_rejects_unbounded_unknown_provider_without_provider_flag(monkeypatch) -> None:
    monkeypatch.delenv("FG2_REQUIRE_REAL_PROVIDER", raising=False)
    monkeypatch.delattr(SyncVectorWorker, "_fg2_fixture_provider_allowed", raising=False)
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "fixture-provider",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_production_sync_rejects_mock_provider_even_when_flag_claims_real(monkeypatch) -> None:
    monkeypatch.setenv("FG2_REQUIRE_REAL_PROVIDER", "true")
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "mock",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_production_sync_rejects_unknown_provider_provenance_before_any_write(monkeypatch) -> None:
    monkeypatch.setenv("FG2_REQUIRE_REAL_PROVIDER", "true")
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "fixture-provider",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_sync_provenance_allowlist_accepts_openai_identity() -> None:
    from scripts.core.sync_vector_worker import REAL_ENRICHMENT_PROVIDERS

    assert "openai" in REAL_ENRICHMENT_PROVIDERS


def test_enrichment_persists_openai_provider_identity_without_mock_provenance(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    enriched = {
        "official_name": "Synthetic OpenAI course",
        "duration_text": None,
        "duration_months": None,
        "total_cost_est": None,
        "requirements": [],
        "graduate_profile": None,
        "target_audience": None,
        "objectives": None,
        "benefits": None,
        "certification": None,
        "curriculum_summary": {"pilares": []},
        "modality": None,
        "primary_campus": None,
        "degree_type": None,
        "start_date": None,
        "categories": [],
        "difficulty_level": None,
        "ai_summary": None,
    }
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.require_real_provider = True
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    worker._call_llm_for_pillars = lambda *_args, **_kwargs: (dict(enriched), "OpenAI")
    worker._merge_pre_extracted = lambda result, _pre_extracted: result
    worker._ensure_canary_enriched_metadata = lambda *_args: None
    worker._verify_canary_enriched_row = lambda *_args: None
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    assert worker.enrich_record({
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "clean_name": "Synthetic OpenAI course",
        "clean_description": "Synthetic public course fixture",
    }) is True

    function, params = worker.db.writes[0]
    assert function == "atomic_enrichment_promote"
    assert params["p_enriched_data"][0]["provider_used"] == "OpenAI"
    assert params["p_enriched_data"][0]["is_mock_data"] is False


def test_sync_accepts_openai_provenance_and_preserves_nonpublic_new_course(monkeypatch) -> None:
    from scripts.core import sync_vector_worker

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def select_service_raise(self, table, **_kwargs):
            return []

        def select_all_service(self, _table, **_kwargs):
            return []

        def upsert(self, table, data, **_kwargs):
            self.writes.append(("upsert", table, dict(data)))
            return [{"id": "70000000-0000-0000-0000-000000000001", "url": data["url"], **data}]

        def rpc_raise(self, function, params):
            self.writes.append(("rpc", function, params))
            return [{"success": True}]

        def patch_exact_one_raise(self, table, filters, data, expected_id):
            self.writes.append(("patch", table, dict(data)))
            return {"id": expected_id, **data}

    database = FixtureDB()
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.profiles = [{
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": False,
        "noise_patterns": [],
    }]
    worker.ready_inst_ids = {INSTITUTION_ID}
    worker.default_noise_patterns = []
    worker._fg2_course_inventory = None
    monkeypatch.setattr(sync_vector_worker, "is_safe_public_url", lambda _url: True)

    assert worker.sync_to_production({
        "id": ENRICHED_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "official_name": "Synthetic OpenAI course",
        "provider_used": "OpenAI",
        "is_mock_data": False,
        "degree_type": "Curso",
        "duration_months": 6,
        "categories": ["Data"],
    }) is True

    course_write = next(payload for operation, table, payload in database.writes if operation == "upsert" and table == "courses")
    assert course_write["provider_used"] == "OpenAI"
    assert course_write["is_mock_data"] is False
    assert course_write["is_active"] is False


def test_controlled_enrichment_rejects_mock_provider_name() -> None:
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker._mock_only = False
    worker.require_real_provider = True

    class MockNamedProvider:
        @staticmethod
        def call_with_fallback(_prompt, _clean_fn, validate_fn=None):
            return ({"official_name": "Synthetic program"}, "smart-mock")

    worker.orchestrator = MockNamedProvider()

    with pytest.raises(ControlledEnrichmentUnavailable):
        worker._call_llm_for_pillars("Synthetic program", "Synthetic description")


@pytest.mark.parametrize(
    "cloudflare_payload",
    ["{}", "[]", '{"official_name":"X","duration_months":"six"}',
     '{"official_name":"X","unexpected":"field"}'],
)
def test_invalid_provider_schema_aborts_controlled_enrichment_before_writes(
    cloudflare_payload: str,
) -> None:
    import logging

    from scripts.core import enrichment_worker

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def rpc_raise(self, function, _params):
            self.writes.append(function)
            return [{"success": True}]

    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = FixtureDB()
    worker.require_real_provider = True
    worker._mock_only = False
    worker.profiles = []
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    providers = [
        enrichment_worker.LLMProvider("OpenAI", lambda _prompt: "{}", lambda: True),
        enrichment_worker.LLMProvider(
            "Cloudflare", lambda _prompt: cloudflare_payload, lambda: True
        ),
    ]
    worker.orchestrator = enrichment_worker.ProviderOrchestrator(
        providers, logging.getLogger("fg2-invalid-provider-schema-test")
    )
    worker.orchestrator.run_health_checks()

    with pytest.raises(ControlledEnrichmentUnavailable):
        worker.enrich_record({
            "id": CLEANSED_ID,
            "staging_id": None,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "clean_name": "Synthetic course",
            "clean_description": "Synthetic description",
        })

    assert worker.db.writes == []
