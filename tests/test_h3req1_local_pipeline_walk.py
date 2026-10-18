"""Synthetic end-to-end walk through the real H3 pipeline transforms.

The adapter below is deliberately local and deterministic. It records the
payloads emitted by the production workers without constructing a Supabase
client or opening a network connection; the resulting course payload is then
consumed by the separate PG17/Admin/public UAT fixture.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import integrity_ping as integrity_ping_module
from scripts.core import enrichment_worker as enrichment_module
from scripts.core import sync_vector_worker as sync_vector_module
from scripts.core import universal_harvester as harvester_module
from scripts.core.cleansing_worker import CleansingWorker
from scripts.core.enrichment_worker import EnrichmentWorker
from scripts.core.sync_vector_worker import SyncVectorWorker
from scripts.core.universal_harvester import UniversalHarvester
from scripts.shared.utils import normalize_url


INSTITUTION_ID = "00000000-0000-0000-0000-000000000001"
CATEGORY_ID = "10000000-0000-0000-0000-000000000001"
COURSE_ID = "70000000-0000-0000-0000-000000000091"
ENRICHED_ID = "60000000-0000-0000-0000-000000000091"
CLEANSED_ID = "50000000-0000-0000-0000-000000000091"
BASE_URL = "https://synthetic.h3.example"
COURSE_URL = f"{BASE_URL}/programs/analitica-aplicada"
COURSE_HTML = f"""<!doctype html>
<html><head><title>Analítica Aplicada | Synthetic Academy</title>
<meta property="og:title" content="Programa de Analítica Aplicada">
<meta name="description" content="Programa práctico de analítica aplicada para formación profesional.">
<link rel="canonical" href="{COURSE_URL}"></head>
<body><main><h1>Programa de Analítica Aplicada</h1>
<p>Duración: 6 meses. Modalidad online. Inversión total S/ 1,250.</p>
<h2>Objetivos</h2><p>Modelar datos y comunicar hallazgos verificables.</p>
<h2>Requisitos</h2><p>Conocimientos básicos de hojas de cálculo.</p>
<h2>Beneficios</h2><p>Proyecto práctico con datos sintéticos.</p></main></body></html>"""
SITEMAP = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{COURSE_URL}</loc></url>
  <url><loc>{COURSE_URL}</loc></url>
  <url><loc>{BASE_URL}/programs/brochure.pdf</loc></url>
  <url><loc>ftp://synthetic.h3.example/programs/non-web</loc></url>
  <url><loc>https://synthetic.h3.example.attacker.test/programs/external</loc></url>
</urlset>""".encode()


class SyntheticResponse:
    def __init__(self, url: str, body: str | bytes, content_type: str) -> None:
        self.url = url
        self.status_code = 200
        self.headers = {"content-type": content_type}
        self.content = body.encode() if isinstance(body, str) else body
        self.text = body.decode() if isinstance(body, bytes) else body


class SyntheticPipelineAdapter:
    """Small PostgREST-shaped adapter that only stores this test's records."""

    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        self.tables: dict[str, list[dict[str, Any]]] = {
            "staging_raw": [],
            "cleansed_programs": [],
            "enriched_programs": [],
            "courses": [],
        }
        self.status_events: list[dict[str, Any]] = []

    @staticmethod
    def _url_from_filter(filters: str) -> str | None:
        marker = "url=eq."
        if marker not in filters:
            return None
        return filters.split(marker, 1)[1].split("&", 1)[0]

    def select_pipeline_raise(self, table: str, filters: str = "", **_kwargs: Any) -> list[dict[str, Any]]:
        if table == "institution_site_profiles":
            return [self.profile]
        rows = self.tables.get(table, [])
        url = self._url_from_filter(filters)
        if url:
            from urllib.parse import unquote

            rows = [row for row in rows if row.get("url") == unquote(url)]
        if "status=eq.discovered" in filters:
            rows = [row for row in rows if row.get("status") == "discovered"]
        if "institution_id=eq." in filters:
            rows = [row for row in rows if row.get("institution_id") == INSTITUTION_ID]
        return [dict(row) for row in rows]

    def select_all_pipeline(self, table: str, **_kwargs: Any) -> list[dict[str, Any]]:
        return [dict(row) for row in self.tables.get(table, [])]

    def select_service_raise(self, table: str, filters: str = "", **_kwargs: Any) -> list[dict[str, Any]]:
        if table == "institutions":
            return [{"website_url": BASE_URL}]
        if table == "categories":
            return [{"id": CATEGORY_ID, "name": "Data"}]
        if table == "courses":
            url = self._url_from_filter(filters)
            return [dict(row) for row in self.tables[table] if not url or row.get("url") == url]
        if table == "course_editorial_state":
            return []
        return []

    def insert(self, table: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        row = dict(data)
        row.setdefault("id", "40000000-0000-0000-0000-000000000091")
        self.tables.setdefault(table, []).append(row)
        return [dict(row)]

    def patch_exact_one_raise(self, table: str, filters: str, data: dict[str, Any], expected_id: str) -> dict[str, Any]:
        rows = self.tables.get(table, [])
        match = next((row for row in rows if row.get("id") == expected_id), None)
        if match is None:
            raise AssertionError(f"synthetic adapter did not find {table}/{expected_id}")
        match.update(data)
        self.status_events.append({"table": table, "id": expected_id, "status": data.get("status")})
        return dict(match)

    def patch_raise(self, table: str, filters: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        marker = "id=eq."
        if marker not in filters:
            raise AssertionError(f"synthetic adapter expected exact id filter for {table}")
        row_id = filters.split(marker, 1)[1].split("&", 1)[0]
        return [self.patch_exact_one_raise(table, filters, data, row_id)]

    def rpc_raise(self, function: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        if function == "atomic_cleansing_promote":
            for payload in params["p_cleansed_data"]:
                row = dict(payload, id=CLEANSED_ID)
                self.tables["cleansed_programs"].append(row)
            for staging_id in params["p_staging_ids"]:
                self.patch_exact_one_raise("staging_raw", "", {"status": "processed"}, staging_id)
            return [{"success": True}]
        if function == "atomic_enrichment_promote":
            for payload in params["p_enriched_data"]:
                existing = next(
                    (
                        row
                        for row in self.tables["enriched_programs"]
                        if row.get("cleansed_id") == payload.get("cleansed_id")
                    ),
                    None,
                )
                if existing is None:
                    self.tables["enriched_programs"].append(
                        dict(payload, id=ENRICHED_ID, status="pending")
                    )
                else:
                    existing.update(dict(payload, status="pending"))
            self.patch_exact_one_raise(
                "cleansed_programs",
                "",
                {"status": "enriched"},
                params["p_cleansed_id"],
            )
            return [{"success": True}]
        if function == "h2_update_course_quality":
            self.status_events.append({"table": "course_editorial_state", "course_id": params["p_course_id"], "status": "quality-updated"})
            return [{"success": True}]
        raise AssertionError(f"unexpected local synthetic RPC: {function}")

    def upsert(self, table: str, data: dict[str, Any], **_kwargs: Any) -> list[dict[str, Any]]:
        if table != "courses":
            raise AssertionError(f"unexpected fallback upsert: {table}")
        row = next(
            (candidate for candidate in self.tables[table] if candidate.get("url") == data.get("url")),
            None,
        )
        if row is None:
            row = dict(data, id=COURSE_ID, category_id=CATEGORY_ID)
            self.tables[table].append(row)
        else:
            row.update(data)
        return [dict(row)]


class SyntheticPromotionError(RuntimeError):
    pass


class FailingCleansingPromotionAdapter(SyntheticPipelineAdapter):
    def __init__(self, profile: dict[str, Any]) -> None:
        super().__init__(profile)
        self.fail_cleansing_rpc = True
        self.cleansed_fallback_calls = 0

    def rpc_raise(self, function: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        if function == "atomic_cleansing_promote" and self.fail_cleansing_rpc:
            raise SyntheticPromotionError("synthetic transport failure")
        return super().rpc_raise(function, params)

    def upsert(self, table: str, data: dict[str, Any], **kwargs: Any) -> list[dict[str, Any]]:
        if table == "cleansed_programs":
            self.cleansed_fallback_calls += 1
        return super().upsert(table, data, **kwargs)


class FailingEnrichmentPromotionAdapter(SyntheticPipelineAdapter):
    def __init__(self, profile: dict[str, Any]) -> None:
        super().__init__(profile)
        self.fail_enrichment_rpc = True

    def rpc_raise(self, function: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        if function == "atomic_enrichment_promote" and self.fail_enrichment_rpc:
            raise SyntheticPromotionError("synthetic transport failure")
        return super().rpc_raise(function, params)


class FailingCourseUpsertAdapter(SyntheticPipelineAdapter):
    def __init__(self, profile: dict[str, Any]) -> None:
        super().__init__(profile)
        self.fail_course_upsert = True

    def upsert(self, table: str, data: dict[str, Any], **kwargs: Any) -> list[dict[str, Any]]:
        if table == "courses" and self.fail_course_upsert:
            raise SyntheticPromotionError("synthetic course upsert failure")
        return super().upsert(table, data, **kwargs)


def run_pipeline_walk() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "exclusion_patterns": ["/brochure.pdf"],
        "field_defaults": {"price_status": "publicado"},
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL},
            max_discovered_urls=5,
        )

    async def fake_request(_session: Any, url: str) -> SyntheticResponse | None:
        if url == f"{BASE_URL}/sitemap.xml":
            return SyntheticResponse(url, SITEMAP, "application/xml")
        if url == COURSE_URL:
            return SyntheticResponse(url, COURSE_HTML, "text/html; charset=utf-8")
        return None

    async def no_network_bfs(_start_url: str, _existing_urls: set[str]) -> None:
        return None

    harvester._safe_request = fake_request
    harvester._bfs_crawl = no_network_bfs
    discovered = asyncio.run(harvester.discover_courses())
    assert discovered == [COURSE_URL]
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["status"] == "discovered"
    discovered_row = harvester._save_discovered_url(COURSE_URL)
    pending = asyncio.run(harvester._scrape_http(None, COURSE_URL))
    assert pending is not None
    pending["id"] = discovered_row["id"]
    staged = harvester._save_to_staging(pending)
    assert staged["status"] == "pending"
    assert "Programa de Analítica Aplicada" in staged["raw_html"]
    assert staged["content_hash"] == hashlib.sha256(COURSE_HTML.encode()).hexdigest()

    cleanser = CleansingWorker(db_client=adapter)
    assert cleanser.process_batch([staged]) == 1
    cleansed = adapter.tables["cleansed_programs"][0]
    assert cleansed["id"] == CLEANSED_ID
    assert cleansed["clean_name"] == "Analítica Aplicada"
    assert cleansed["base_price"] == 1250.0
    assert adapter.tables["staging_raw"][0]["status"] == "processed"

    discarded_staging = {
        "id": "40000000-0000-0000-0000-000000000092",
        "institution_id": INSTITUTION_ID,
        "url": f"{BASE_URL}/programs/agradecimiento",
        "raw_name": "Agradecimiento",
        "raw_description": "Gracias por visitar el sitio",
        "raw_html": "<html><h1>Agradecimiento</h1><p>Gracias</p></html>",
        "status": "pending",
    }
    adapter.tables["staging_raw"].append(discarded_staging)
    assert cleanser.process_batch([discarded_staging]) == 0
    assert discarded_staging["status"] == "discarded"
    assert len(adapter.tables["cleansed_programs"]) == 1

    with patch.object(enrichment_module, "get_db_client", return_value=adapter):
        enricher = EnrichmentWorker()
    enricher._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    simulated = {
        "official_name": cleansed["clean_name"],
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": "S/ 1,250",
        "requirements": ["Conocimientos básicos de hojas de cálculo"],
        "graduate_profile": "Analista de datos inicial",
        "curriculum_summary": {"module": "Modelado y comunicación"},
        "target_audience": "Profesionales en transición",
        "objectives": "Modelar datos y comunicar hallazgos",
        "benefits": "Proyecto práctico",
        "certifications": "Constancia sintética",
        "modality": "online",
        "primary_campus": "Virtual",
        "degree_type": "Curso",
        "start_date": "2027-04-01",
        "categories": ["Data"],
        "difficulty_level": "intermediate",
        "ai_summary": "Formación aplicada en analítica con un proyecto basado en datos sintéticos.",
    }
    enricher._call_llm_for_pillars = lambda *_args, **_kwargs: (dict(simulated), "synthetic-provider")
    assert enricher.enrich_record(cleansed) is True
    enriched = adapter.tables["enriched_programs"][0]
    assert enriched["id"] == ENRICHED_ID
    assert enriched["is_mock_data"] is False
    assert enriched["provider_used"] == "synthetic-provider"
    assert enriched["duration_months"] == 6
    assert enriched["total_cost_est"] == 1250.0

    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()
    assert integrity_ping_module.is_safe_public_ip("127.0.0.1") is False
    with patch.object(integrity_ping_module, "resolve_public_host", return_value=["93.184.216.34"]):
        assert syncer.sync_to_production(enriched) is True
    course = adapter.tables["courses"][0]
    assert course["id"] == COURSE_ID
    assert course["institution_id"] == INSTITUTION_ID
    assert normalize_url(course["url"]) == normalize_url(COURSE_URL)
    assert course["is_active"] is True
    assert course["is_verified"] is True
    assert course["provider_used"] == "synthetic-provider"
    assert enriched["status"] == "synced"

    result = {
        "candidate_baseline": "4eb4d877a50b012bb630a129bd0c74482c33be9c",
        "synthetic_only": True,
        "network_access": "disabled; HTTP fixture response injected at request boundary",
        "staging": {
            "id": staged["id"],
            "status": adapter.tables["staging_raw"][0]["status"],
            "url": staged["url"],
            "content_sha256": staged["content_hash"],
        },
        "cleansed": {"id": cleansed["id"], "name": cleansed["clean_name"], "status": cleansed["status"], "price_pen": cleansed["base_price"]},
        "enriched": {"id": enriched["id"], "name": enriched["official_name"], "status": enriched["status"], "provider": enriched["provider_used"], "is_mock_data": enriched["is_mock_data"]},
        "course": course,
        "discarded": {"id": discarded_staging["id"], "status": discarded_staging["status"], "published": False},
        "same_identity_across_pipeline": all((
            normalize_url(staged["url"]) == normalize_url(cleansed["url"]) == normalize_url(enriched["url"]) == normalize_url(course["url"]),
            staged["institution_id"] == cleansed["institution_id"] == enriched["institution_id"] == course["institution_id"],
        )),
    }
    assert result["same_identity_across_pipeline"] is True
    output = os.environ.get("H3_LOCAL_PIPELINE_RESULT")
    if output:
        Path(output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def test_h3req1_local_pipeline_walk() -> None:
    run_pipeline_walk()


def test_cleansing_rpc_failure_preserves_pending_row_for_safe_recovery() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "website_url": BASE_URL,
    }
    adapter = FailingCleansingPromotionAdapter(profile)
    staging = {
        "id": "40000000-0000-0000-0000-000000000093",
        "institution_id": INSTITUTION_ID,
        "url": COURSE_URL,
        "raw_name": "Analítica Aplicada",
        "raw_description": "Programa práctico de analítica aplicada para formación profesional.",
        "raw_html": COURSE_HTML,
        "status": "pending",
    }
    adapter.tables["staging_raw"].append(staging)
    cleanser = CleansingWorker(db_client=adapter)

    failed_closed = False
    try:
        cleanser.process_batch([staging])
    except SyntheticPromotionError:
        failed_closed = True

    assert failed_closed is True
    assert staging["status"] == "pending"
    assert adapter.tables["cleansed_programs"] == []
    assert adapter.cleansed_fallback_calls == 0

    adapter.fail_cleansing_rpc = False
    assert cleanser.process_batch([staging]) == 1
    assert staging["status"] == "processed"
    assert len(adapter.tables["cleansed_programs"]) == 1


def test_enrichment_rpc_failure_is_recoverable_without_partial_promotion() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "website_url": BASE_URL,
    }
    adapter = FailingEnrichmentPromotionAdapter(profile)
    cleansed = {
        "id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "staging_id": "40000000-0000-0000-0000-000000000094",
        "url": COURSE_URL,
        "clean_name": "Analítica Aplicada",
        "clean_description": "Programa sintético de analítica aplicada.",
        "metadata": {"regex_price": 1250, "regex_start_date": "2027-04-01"},
        "status": "pending",
    }
    adapter.tables["cleansed_programs"].append(cleansed)
    with patch.object(enrichment_module, "get_db_client", return_value=adapter):
        enricher = EnrichmentWorker()
    enricher._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    result = {
        "official_name": "Analítica Aplicada",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": "S/ 1,250",
        "requirements": ["Conocimientos básicos"],
        "graduate_profile": "Analista inicial",
        "curriculum_summary": {"module": "Modelado"},
        "target_audience": "Profesionales",
        "objectives": "Modelar datos",
        "benefits": "Proyecto práctico",
        "certifications": "Constancia sintética",
        "modality": "online",
        "primary_campus": "Virtual",
        "degree_type": "Curso",
        "start_date": "2027-04-01",
        "categories": ["Data"],
        "difficulty_level": "intermediate",
        "ai_summary": "Curso sintético de analítica.",
    }
    enricher._call_llm_for_pillars = lambda *_args, **_kwargs: (dict(result), "synthetic-provider")

    failed_closed = False
    try:
        enricher.enrich_record(cleansed)
    except SyntheticPromotionError:
        failed_closed = True

    assert failed_closed is True
    assert adapter.tables["enriched_programs"] == []
    assert cleansed["status"] == "pending"

    adapter.fail_enrichment_rpc = False
    assert enricher.enrich_record(cleansed) is True
    assert len(adapter.tables["enriched_programs"]) == 1
    assert cleansed["status"] == "enriched"
    assert enricher.enrich_record(cleansed) is True
    assert len(adapter.tables["enriched_programs"]) == 1


def test_sync_upsert_failure_preserves_pending_row_and_recovers_idempotently() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "website_url": BASE_URL,
    }
    adapter = FailingCourseUpsertAdapter(profile)
    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": COURSE_URL,
        "official_name": "Analítica Aplicada",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": 1250.0,
        "requirements": "Conocimientos básicos",
        "graduate_profile": "Analista inicial",
        "curriculum_summary": {"module": "Modelado"},
        "target_audience": "Profesionales",
        "objectives": "Modelar datos",
        "benefits": "Proyecto práctico",
        "certifications": "Constancia sintética",
        "modality": "Remoto",
        "primary_campus": "Virtual",
        "degree_type": "Curso",
        "start_date": "2027-04-01",
        "categories": ["Data"],
        "difficulty_level": "intermediate",
        "ai_summary": "Curso sintético de analítica.",
        "provider_used": "synthetic-provider",
        "is_mock_data": False,
        "status": "pending",
        "metadata": {},
    }
    adapter.tables["enriched_programs"].append(enriched)
    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()

    failed_closed = False
    with patch.object(integrity_ping_module, "resolve_public_host", return_value=["93.184.216.34"]):
        try:
            syncer.sync_to_production(enriched)
        except SyntheticPromotionError:
            failed_closed = True

    assert failed_closed is True
    assert enriched["status"] == "pending"
    assert adapter.tables["courses"] == []

    adapter.fail_course_upsert = False
    with patch.object(integrity_ping_module, "resolve_public_host", return_value=["93.184.216.34"]):
        assert syncer.sync_to_production(enriched) is True
        first_course_id = adapter.tables["courses"][0]["id"]
        assert enriched["status"] == "synced"
        assert len(adapter.tables["courses"]) == 1

        assert syncer.sync_to_production(enriched) is True
    assert len(adapter.tables["courses"]) == 1
    assert adapter.tables["courses"][0]["id"] == first_course_id


def test_hardcoded_discovery_deduplicates_seeds_and_applies_url_boundary() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "seed_urls": [COURSE_URL, f"{COURSE_URL}#details", "ftp://synthetic.h3.example/program"],
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False

    discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [COURSE_URL]
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["url"] == COURSE_URL
    assert adapter.tables["staging_raw"][0]["status"] == "discovered"


def test_hardcoded_discovery_resumes_discovered_rows_without_reprocessing_pending() -> None:
    discovered_url = f"{BASE_URL}/programs/resume-discovered"
    pending_url = f"{BASE_URL}/programs/already-pending"
    new_url = f"{BASE_URL}/programs/new-seed"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "seed_urls": [discovered_url, pending_url, new_url],
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    adapter.tables["staging_raw"].extend(
        [
            {
                "id": "40000000-0000-0000-0000-000000000094",
                "institution_id": INSTITUTION_ID,
                "url": discovered_url,
                "status": "discovered",
            },
            {
                "id": "40000000-0000-0000-0000-000000000095",
                "institution_id": INSTITUTION_ID,
                "url": pending_url,
                "status": "pending",
            },
        ]
    )
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False

    discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [discovered_url, new_url]
    assert len(adapter.tables["staging_raw"]) == 3
    assert len({row["url"] for row in adapter.tables["staging_raw"]}) == 3
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == pending_url)["status"] == "pending"


def test_paginated_discovery_extracts_only_allowlisted_links() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "paginated_catalog",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "catalog_url_patterns": [f"{BASE_URL}/catalog?page={{page}}"],
        "catalog_link_selector": "a.program",
        "catalog_max_pages": 1,
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, **_kwargs):
            body = (
                '<a class="program" href="/programs/analitica-aplicada">course</a>'
                '<a class="program" href="https://outside.example/program">outside</a>'
                '<a class="program" href="/programs/brochure.pdf">pdf</a>'
            )
            return SyntheticResponse(url, body, "text/html")

    with patch.object(harvester_module, "AsyncSession", Session):
        discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [COURSE_URL]
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["status"] == "discovered"


def test_paginated_discovery_resumes_discovered_rows_without_reprocessing_pending() -> None:
    discovered_url = f"{BASE_URL}/programs/paginated-resume"
    pending_url = f"{BASE_URL}/programs/paginated-pending"
    new_url = f"{BASE_URL}/programs/paginated-new"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "paginated_catalog",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "catalog_url_patterns": [f"{BASE_URL}/catalog?page={{page}}"],
        "catalog_link_selector": "a.program",
        "catalog_max_pages": 1,
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    adapter.tables["staging_raw"].extend(
        [
            {"id": "40000000-0000-0000-0000-000000000096", "institution_id": INSTITUTION_ID, "url": discovered_url, "status": "discovered"},
            {"id": "40000000-0000-0000-0000-000000000097", "institution_id": INSTITUTION_ID, "url": pending_url, "status": "pending"},
        ]
    )
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, **_kwargs):
            body = (
                f'<a class="program" href="{discovered_url}">resume</a>'
                f'<a class="program" href="{pending_url}">pending</a>'
                f'<a class="program" href="{new_url}">new</a>'
            )
            return SyntheticResponse(url, body, "text/html")

    async def no_delay(_seconds):
        return None

    with patch.object(harvester_module, "AsyncSession", Session), patch.object(harvester_module.asyncio, "sleep", new=no_delay):
        discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [discovered_url, new_url]
    assert {row["url"] for row in adapter.tables["staging_raw"]} == {discovered_url, pending_url, new_url}
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == discovered_url)["status"] == "discovered"
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == pending_url)["status"] == "pending"
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == new_url)["status"] == "discovered"


def test_catalog_link_discovery_closes_page_and_filters_external_links() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "catalog_link_extraction",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "seed_urls": [],
        "catalog_link_selector": "a.program",
        "catalog_scroll_iterations": 1,
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False

    class Element:
        def __init__(self, href: str) -> None:
            self.href = href

        async def get_attribute(self, _name):
            return self.href

    class Page:
        closed = False

        async def goto(self, *_args, **_kwargs):
            return type("Response", (), {"status": 200})()

        async def evaluate(self, script):
            return False if "document.querySelector(\"footer\")" in script else None

        async def query_selector_all(self, _selector):
            return [
                Element("/programs/analitica-aplicada"),
                Element("https://outside.example/program"),
                Element("/programs/brochure.pdf"),
            ]

        async def close(self):
            self.closed = True

    class Browser:
        def __init__(self):
            self.page = Page()

        async def new_page(self, **_kwargs):
            return self.page

    browser = Browser()

    async def no_delay(_seconds):
        return None

    with patch.object(harvester_module.asyncio, "sleep", new=no_delay):
        discovered = asyncio.run(harvester.discover_courses(browser=browser))

    assert discovered == [COURSE_URL]
    assert browser.page.closed is True
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["status"] == "discovered"


def test_catalog_link_discovery_resumes_discovered_rows_without_reprocessing_pending() -> None:
    discovered_url = f"{BASE_URL}/programs/links-resume"
    pending_url = f"{BASE_URL}/programs/links-pending"
    new_url = f"{BASE_URL}/programs/links-new"
    catalog_url = f"{BASE_URL}/catalog"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "catalog_link_extraction",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "seed_urls": [catalog_url],
        "catalog_link_selector": "a.program",
        "catalog_scroll_iterations": 1,
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    adapter.tables["staging_raw"].extend(
        [
            {"id": "40000000-0000-0000-0000-000000000098", "institution_id": INSTITUTION_ID, "url": discovered_url, "status": "discovered"},
            {"id": "40000000-0000-0000-0000-000000000099", "institution_id": INSTITUTION_ID, "url": pending_url, "status": "pending"},
        ]
    )
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False

    class Element:
        def __init__(self, href: str) -> None:
            self.href = href

        async def get_attribute(self, _name):
            return self.href

    class Page:
        closed = False

        async def goto(self, *_args, **_kwargs):
            return type("Response", (), {"status": 200})()

        async def evaluate(self, script):
            return False if 'document.querySelector("footer")' in script else None

        async def query_selector_all(self, _selector):
            return [Element(discovered_url), Element(pending_url), Element(new_url)]

        async def close(self):
            self.closed = True

    class Browser:
        def __init__(self):
            self.page = Page()

        async def new_page(self, **_kwargs):
            return self.page

    browser = Browser()

    async def no_delay(_seconds):
        return None

    with patch.object(harvester_module.asyncio, "sleep", new=no_delay):
        discovered = asyncio.run(harvester.discover_courses(browser=browser))

    assert discovered == [discovered_url, new_url]
    assert browser.page.closed is True
    assert {row["url"] for row in adapter.tables["staging_raw"]} == {discovered_url, pending_url, new_url}
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == discovered_url)["status"] == "discovered"
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == pending_url)["status"] == "pending"
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == new_url)["status"] == "discovered"


def test_paginated_discovery_preserves_and_resumes_results_after_later_page_failure() -> None:
    first_url = f"{BASE_URL}/programs/page-one"
    recovered_url = f"{BASE_URL}/programs/page-two-recovered"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "paginated_catalog",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "catalog_url_patterns": [f"{BASE_URL}/catalog?page={{page}}"],
        "catalog_link_selector": "a.program",
        "catalog_max_pages": 2,
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False
    phase = {"name": "partial"}
    requests: list[str] = []

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, **_kwargs):
            page_num = url.rsplit("=", 1)[-1]
            requests.append(f"{phase['name']}:{page_num}")
            if page_num == "2" and phase["name"] == "partial":
                response = SyntheticResponse(url, "", "text/html")
                response.status_code = 503
                return response
            hrefs = [first_url] if page_num == "1" else [recovered_url]
            body = "".join(f'<a class="program" href="{href}">course</a>' for href in hrefs)
            return SyntheticResponse(url, body, "text/html")

    async def no_delay(_seconds):
        return None

    with patch.object(harvester_module, "AsyncSession", Session), patch.object(harvester_module.asyncio, "sleep", new=no_delay):
        partial = asyncio.run(harvester.discover_courses())
        phase["name"] = "recovery"
        recovered = asyncio.run(harvester.discover_courses())

    assert partial == [first_url]
    assert recovered == [first_url, recovered_url]
    assert requests == ["partial:1", "partial:2", "recovery:1", "recovery:2"]
    assert {row["url"] for row in adapter.tables["staging_raw"]} == {first_url, recovered_url}
    assert len(adapter.tables["staging_raw"]) == 2
    assert all(row["status"] == "discovered" for row in adapter.tables["staging_raw"])


def test_catalog_scroll_keeps_discovered_links_when_a_later_scroll_fails() -> None:
    first_url = f"{BASE_URL}/programs/scroll-one"
    recovered_url = f"{BASE_URL}/programs/scroll-two-recovered"
    catalog_url = f"{BASE_URL}/catalog-scroll"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "catalog_link_extraction",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "seed_urls": [catalog_url],
        "catalog_link_selector": "a.program",
        "catalog_scroll_iterations": 2,
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": catalog_url}
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(institution, max_discovered_urls=5)
    harvester.check_time_guard = lambda: False
    phase = {"name": "partial"}
    query_counts = {"partial": 0, "recovery": 0}

    class Element:
        def __init__(self, href: str) -> None:
            self.href = href

        async def get_attribute(self, _name):
            return self.href

    class Page:
        def __init__(self):
            self.closed = False

        async def goto(self, *_args, **_kwargs):
            return type("Response", (), {"status": 200})()

        async def evaluate(self, script):
            return False if 'document.querySelector("footer")' in script else None

        async def query_selector_all(self, _selector):
            query_counts[phase["name"]] += 1
            if phase["name"] == "partial" and query_counts["partial"] == 2:
                raise RuntimeError("synthetic later-scroll failure")
            hrefs = [first_url] if phase["name"] == "partial" else [first_url, recovered_url]
            return [Element(href) for href in hrefs]

        async def close(self):
            self.closed = True

    class Browser:
        def __init__(self):
            self.pages = []

        async def new_page(self, **_kwargs):
            page = Page()
            self.pages.append(page)
            return page

    browser = Browser()

    async def no_delay(_seconds):
        return None

    with patch.object(harvester_module.asyncio, "sleep", new=no_delay):
        partial = asyncio.run(harvester.discover_courses(browser=browser))
        phase["name"] = "recovery"
        recovered = asyncio.run(harvester.discover_courses(browser=browser))

    assert partial == [first_url]
    assert recovered == [first_url, recovered_url]
    assert query_counts == {"partial": 2, "recovery": 2}
    assert len(browser.pages) == 2 and all(page.closed for page in browser.pages)
    assert {row["url"] for row in adapter.tables["staging_raw"]} == {first_url, recovered_url}
    assert len(adapter.tables["staging_raw"]) == 2
    assert all(row["status"] == "discovered" for row in adapter.tables["staging_raw"])


if __name__ == "__main__":
    run_pipeline_walk()
