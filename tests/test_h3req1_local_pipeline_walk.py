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
import subprocess
import sys
import threading
import time
import pytest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from unittest.mock import Mock, patch

# Workers import sibling modules by script path; mirror that runtime context
# without depending on an unconfigured runner-wide PYTHONPATH.
core_script_dir = str(Path(__file__).resolve().parents[1] / "scripts" / "core")
if core_script_dir not in sys.path:
    sys.path.insert(0, core_script_dir)

import integrity_ping as integrity_ping_module
from scripts.core import enrichment_worker as enrichment_module
from scripts.core import sync_vector_worker as sync_vector_module
from scripts.core import universal_harvester as harvester_module
from scripts.shared import site_diagnostics as site_diagnostics_module
from scripts.core.cleansing_worker import CleansingWorker
from scripts.core.enrichment_worker import EnrichmentWorker
from scripts.core.sync_vector_worker import SyncVectorWorker
from scripts.core.universal_harvester import UniversalHarvester
from scripts.core.fg2_bounded_run import (
    FG2CohortManifest,
    FG2RequestBudget,
    InvalidControlledRun,
    RunBudgetExceeded,
    SourceBlocked,
    cleansed_url_sha256,
    initialize_manifest,
    update_manifest_institution,
    url_sha256,
    validate_controlled_profile,
)
from scripts.shared.utils import normalize_url


INSTITUTION_ID = "00000000-0000-0000-0000-000000000001"
CATEGORY_ID = "10000000-0000-0000-0000-000000000001"
STAGING_ID = "40000000-0000-0000-0000-000000000091"
COURSE_ID = "70000000-0000-0000-0000-000000000091"
ENRICHED_ID = "60000000-0000-0000-0000-000000000091"
CLEANSED_ID = "50000000-0000-0000-0000-000000000091"
BASE_URL = "https://synthetic.h3.example"
COURSE_URL = f"{BASE_URL}/programs/analitica-aplicada"
SYNTHETIC_RESOLVE_ENTRY = "synthetic.h3.example:443:93.184.216.34"


def synthetic_public_request_binding(url: str, **_kwargs: Any) -> tuple[str, str]:
    return url, SYNTHETIC_RESOLVE_ENTRY


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


class SyntheticStreamingResponse:
    def __init__(self, url: str, chunks: list[bytes], content_type: str = "text/html") -> None:
        self.url = url
        self.status_code = 200
        self.headers = {"content-type": content_type}
        self.content = b""
        self.chunks = chunks
        self.prefetched_bytes = 0
        self.yielded_bytes = 0
        self.closed = False

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")

    async def aiter_content(self, chunk_size: int | None = None):
        assert chunk_size is None or chunk_size > 0
        for chunk in self.chunks:
            self.yielded_bytes += len(chunk)
            yield chunk
        self.closed = True

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.closed = True


class SyntheticBrowserPage:
    def __init__(self) -> None:
        self.closed = False
        self.navigated_urls: list[str] = []

    async def goto(self, url: str, **_kwargs):
        self.navigated_urls.append(url)
        return type("Response", (), {"status": 200})()


class SyntheticTransferAborted(RuntimeError):
    def __init__(self, message: str, response: SyntheticStreamingResponse) -> None:
        super().__init__(message)
        self.response = response


async def synthetic_response_via_content_callback(
    response: SyntheticStreamingResponse, kwargs: dict[str, Any]
) -> SyntheticStreamingResponse:
    """Model controlled streaming responses without external I/O."""
    response.content = b""
    if kwargs.get("stream") is True:
        # curl_cffi wakes the awaiting request when the stream's first body
        # chunk enters its queue; status handling can still close before the
        # application iterates or materializes that queued chunk.
        if response.chunks:
            response.prefetched_bytes = len(response.chunks[0])
        return response
    callback = kwargs.get("content_callback")
    assert callable(callback)
    for chunk in response.chunks:
        response.yielded_bytes += len(chunk)
        accepted = callback(chunk)
        if accepted != len(chunk):
            response.closed = True
            raise SyntheticTransferAborted(
                "synthetic curl write callback aborted", response
            )
    response.closed = True
    return response


class SyntheticControlledTransport:
    def prepare(self, url: str) -> dict[str, str]:
        return {"synthetic-origin": urlparse(url).netloc}

    async def request(self, session, url, prepared, impersonate, timeout):
        assert prepared == {"synthetic-origin": urlparse(url).netloc}
        return await session.get(
            url,
            impersonate=impersonate,
            timeout=timeout,
            allow_redirects=False,
        )


class SyntheticPipelineAdapter:
    """Small PostgREST-shaped adapter that only stores this test's records."""

    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        self.tables: dict[str, list[dict[str, Any]]] = {
            "staging_raw": [],
            "cleansed_programs": [],
            "enriched_programs": [],
            "courses": [],
            "course_editorial_state": [],
        }
        self.status_events: list[dict[str, Any]] = []
        self.upsert_calls: list[dict[str, Any]] = []
        self.select_all_service_calls: list[str] = []

    @staticmethod
    def _url_from_filter(filters: str) -> str | None:
        marker = "url=eq."
        if marker not in filters:
            return None
        from urllib.parse import unquote

        return unquote(filters.split(marker, 1)[1].split("&", 1)[0])

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

    def select_all_service(self, table: str, **_kwargs: Any) -> list[dict[str, Any]]:
        self.select_all_service_calls.append(table)
        return [dict(row) for row in self.tables.get(table, [])]

    def select_service_raise(self, table: str, filters: str = "", **_kwargs: Any) -> list[dict[str, Any]]:
        if table == "institutions":
            return [{"website_url": BASE_URL}]
        if table == "categories":
            return [{"id": CATEGORY_ID, "name": "Data"}]
        if table == "courses":
            id_marker = "id=eq."
            if id_marker in filters:
                course_id = filters.split(id_marker, 1)[1].split("&", 1)[0]
                return [dict(row) for row in self.tables[table] if row.get("id") == course_id]
            url = self._url_from_filter(filters)
            return [dict(row) for row in self.tables[table] if not url or row.get("url") == url]
        if table == "course_editorial_state":
            marker = "course_id=eq."
            course_id = filters.split(marker, 1)[1].split("&", 1)[0] if marker in filters else None
            return [dict(row) for row in self.tables[table] if course_id is None or row.get("course_id") == course_id]
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
            self.status_events.append({
                "table": "course_editorial_state",
                "course_id": params["p_course_id"],
                "status": "quality-updated",
                "field_sources": dict(params.get("p_field_sources") or {}),
                "field_timestamps": dict(params.get("p_field_timestamps") or {}),
            })
            return [{"success": True}]
        raise AssertionError(f"unexpected local synthetic RPC: {function}")

    def upsert(self, table: str, data: dict[str, Any], **_kwargs: Any) -> list[dict[str, Any]]:
        self.upsert_calls.append(dict(data))
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


def test_controlled_refresh_of_known_course_creates_manifest_entry_and_keeps_editorial_override(tmp_path: Path) -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "circuit_open": False,
        "seed_urls": [COURSE_URL],
        "exclusion_patterns": [],
        "field_defaults": {},
    }
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    adapter = SyntheticPipelineAdapter(profile)
    existing_staging = {
        "id": "40000000-0000-0000-0000-000000000095",
        "institution_id": INSTITUTION_ID,
        "url": COURSE_URL,
        "status": "discovered",
        "content_hash": hashlib.sha256(b"previous synthetic source body").hexdigest(),
    }
    adapter.tables["staging_raw"].append(existing_staging)
    adapter.tables["courses"].append(
        {
            "id": COURSE_ID,
            "institution_id": INSTITUTION_ID,
            "url": COURSE_URL,
            "name": "Old pipeline title",
            "last_404_at": None,
            "is_active": True,
        }
    )
    manual_state = {
        "course_id": COURSE_ID,
        "manual_overrides": {"name": "Nombre editorial vigente"},
        "field_sources": {"name": "manual_override"},
        "field_timestamps": {"name": "2026-10-30T12:00:00+00:00"},
        "manual_updated_at": "2026-10-30T12:00:00+00:00",
        "editorial_status": "active",
    }
    adapter.tables["course_editorial_state"].append(manual_state)
    preflight = validate_controlled_profile(institution, profile)
    manifest_path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": preflight["profile_sha256"],
                "seed_sha256": preflight["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    with patch.dict(
        os.environ,
        {"GITHUB_RUN_ID": "123456789", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40},
    ), patch.object(harvester_module, "get_db_client", return_value=adapter):
        controlled_institution = dict(
            institution,
            _controlled_profile_sha256=preflight["profile_sha256"],
            _controlled_seed_sha256=preflight["seed_sha256"],
        )
        harvester = UniversalHarvester(
            controlled_institution,
            max_discovered_urls=10,
            controlled=True,
            cohort_manifest=str(manifest_path),
            _controlled_transport=SyntheticControlledTransport(),
        )

    discovered = asyncio.run(harvester.discover_courses())
    assert discovered == [COURSE_URL]
    assert existing_staging["status"] == "discovered"
    assert harvester._discovered_rows_by_url[COURSE_URL]["kind"] == "refresh_existing"
    assert harvester._discovered_rows_by_url[COURSE_URL]["course_id"] == COURSE_ID
    assert harvester._discovered_rows_by_url[COURSE_URL]["id"] == existing_staging["id"]

    class CourseSession:
        async def get(self, url: str, **_kwargs: Any) -> SyntheticResponse:
            assert url == COURSE_URL
            return SyntheticResponse(url, COURSE_HTML, "text/html; charset=utf-8")

    pending = asyncio.run(harvester._scrape_http(CourseSession(), COURSE_URL))
    assert pending is not None
    staged = harvester._save_to_staging(pending)
    assert staged["id"] == existing_staging["id"]
    assert len(adapter.tables["staging_raw"]) == 1
    assert existing_staging["status"] == "pending"
    assert staged["status"] == "pending"
    assert staged["content_hash"] == hashlib.sha256(COURSE_HTML.encode()).hexdigest()

    budget_snapshot = harvester.request_budget.snapshot()
    assert budget_snapshot == {"http_requests": 1, "unique_urls": 1}
    update_manifest_institution(manifest_path, institution_id=INSTITUTION_ID, **budget_snapshot, result="complete")
    manifest = FG2CohortManifest.load(manifest_path, allow_empty=False)
    assert manifest.payload["entries"] == [
        {
            "institution_id": INSTITUTION_ID,
            "staging_id": staged["id"],
            "course_id": COURSE_ID,
            "url_sha256": hashlib.sha256(COURSE_URL.encode()).hexdigest(),
            "cleansed_url_sha256": cleansed_url_sha256(COURSE_URL),
            "content_sha256": staged["content_hash"],
            "kind": "refresh_existing",
        }
    ]

    cleanser = CleansingWorker(db_client=adapter)
    assert cleanser.process_batch([staged]) == 1
    assert existing_staging["status"] == "processed"
    assert manual_state["manual_overrides"]["name"] == "Nombre editorial vigente"

    cleansed = adapter.tables["cleansed_programs"][0]
    with patch.object(enrichment_module, "get_db_client", return_value=adapter):
        enricher = EnrichmentWorker()
    enricher._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    simulated = {
        "official_name": cleansed["clean_name"],
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": "S/ 1,250",
        "requirements": ["Requisitos sintéticos"],
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
        "ai_summary": "Refresh sintético de un curso ya publicado.",
    }
    enricher._call_llm_for_pillars = lambda *_args, **_kwargs: (dict(simulated), "synthetic-provider")
    assert enricher.enrich_record(cleansed) is True
    enriched = adapter.tables["enriched_programs"][0]

    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()
    with patch.object(integrity_ping_module, "resolve_public_host", return_value=["93.184.216.34"]):
        assert syncer.sync_to_production(enriched) is True
    quality = next(event for event in adapter.status_events if event["status"] == "quality-updated")
    assert quality["field_sources"]["name"] == "manual_override"
    assert manual_state["manual_overrides"]["name"] == "Nombre editorial vigente"
    assert enriched["status"] == "synced"
    assert adapter.tables["courses"][0]["id"] == COURSE_ID


def test_default_controlled_transport_pins_dns_and_disables_environment_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[dict[str, Any]] = []
    calls: list[tuple[str, dict[str, Any]]] = []
    body = b"<html>synthetic</html>"
    response_fixture = SyntheticStreamingResponse(
        "https://synthetic.example/program", [body]
    )
    monkeypatch.setattr(
        harvester_module,
        "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES",
        len(body),
        raising=False,
    )

    class CapturedSession:
        def __init__(self, **kwargs: Any) -> None:
            created.append(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            calls.append((url, kwargs))
            return await synthetic_response_via_content_callback(response_fixture, kwargs)

    pin = {harvester_module.CurlOpt.RESOLVE: ["synthetic.example:443:93.184.216.34"]}
    with patch.object(harvester_module, "AsyncSession", CapturedSession):
        response = asyncio.run(
            harvester_module._send_controlled_request(
                object(),
                "https://synthetic.example/program",
                pin,
                "chrome110",
                25,
            )
        )

    assert response.status_code == 200
    assert created == [
        {
            "trust_env": False,
            "proxies": {},
            "curl_options": pin,
            "verify": True,
            "allow_redirects": False,
            "max_redirects": 0,
            "retry": 0,
        }
    ]
    assert calls[0][0] == "https://synthetic.example/program"
    assert calls[0][1]["allow_redirects"] is False
    assert calls[0][1]["verify"] is True
    assert calls[0][1]["proxies"] == {}
    assert calls[0][1]["stream"] is True
    assert "content_callback" not in calls[0][1]
    assert response.content == body
    assert response.text == body.decode()
    assert response_fixture.closed is True
    assert response_fixture.prefetched_bytes == len(body)
    assert response_fixture.yielded_bytes == len(body)


def test_controlled_transport_closes_and_rejects_body_over_limit_without_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        harvester_module, "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES", 4, raising=False
    )
    response_fixture = SyntheticStreamingResponse(
        "https://synthetic.example/program", [b"abcd", b"e"]
    )
    calls: list[dict[str, Any]] = []

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, _url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            calls.append(kwargs)
            return await synthetic_response_via_content_callback(response_fixture, kwargs)

    with patch.object(harvester_module, "AsyncSession", CapturedSession):
        with pytest.raises(RuntimeError, match="controlled response body exceeds"):
            asyncio.run(
                harvester_module._send_controlled_request(
                    object(),
                    "https://synthetic.example/program",
                    {},
                    "chrome110",
                    25,
                )
            )

    assert calls[0]["stream"] is True
    assert "content_callback" not in calls[0]
    assert "content-length" not in response_fixture.headers
    assert response_fixture.prefetched_bytes == 4
    assert response_fixture.yielded_bytes == 5
    assert response_fixture.closed is True
    assert response_fixture.content == b""


@pytest.mark.parametrize("status", [403, 429])
def test_oversized_block_response_stops_origin_without_retry(
    status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        harvester_module, "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES", 4, raising=False
    )
    response = SyntheticStreamingResponse(
        "https://synthetic.example/course", [b"abcd", b"e"]
    )
    response.status_code = status
    response.headers["Retry-After"] = "0"
    requests: list[str] = []

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            requests.append(url)
            return await synthetic_response_via_content_callback(response, kwargs)

    budget = FG2RequestBudget(
        max_unique_urls=10,
        max_http_requests=20,
        min_interval_seconds=0,
        max_retry_after_seconds=30,
        max_attempts_per_url=3,
        request_preparer=lambda _url: {},
        requester=harvester_module._send_controlled_request,
    )
    with patch.object(harvester_module, "AsyncSession", CapturedSession):
        with pytest.raises(SourceBlocked):
            asyncio.run(
                budget.get(
                    object(),
                    "https://synthetic.example/course",
                    allowed_origin="https://synthetic.example",
                )
            )
        with pytest.raises(SourceBlocked):
            asyncio.run(
                budget.get(
                    object(),
                    "https://synthetic.example/another",
                    allowed_origin="https://synthetic.example",
                )
            )

    assert requests == ["https://synthetic.example/course"]
    assert response.closed is True
    assert response.prefetched_bytes == 4
    assert response.yielded_bytes == 0
    assert response.content == b""
    assert budget.http_requests == 1


def test_oversized_redirect_body_preserves_redirect_and_http_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        harvester_module, "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES", 16, raising=False
    )
    first_url = "https://synthetic.example/catalog"
    final_url = "https://synthetic.example/program"
    redirect = SyntheticStreamingResponse(first_url, [b"x" * 16, b"redirect"])
    redirect.status_code = 302
    redirect.headers["Location"] = "/program"
    final = SyntheticStreamingResponse(final_url, [b"<html></html>"])
    responses = {first_url: redirect, final_url: final}
    requests: list[str] = []

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            requests.append(url)
            return await synthetic_response_via_content_callback(responses[url], kwargs)

    budget = FG2RequestBudget(
        max_unique_urls=10,
        max_http_requests=20,
        min_interval_seconds=0,
        max_retry_after_seconds=30,
        max_attempts_per_url=2,
        request_preparer=lambda _url: {},
        requester=harvester_module._send_controlled_request,
    )
    with patch.object(harvester_module, "AsyncSession", CapturedSession):
        result = asyncio.run(
            budget.get(
                object(), first_url, allowed_origin="https://synthetic.example"
            )
        )

    assert result.status_code == 200
    assert requests == [first_url, final_url]
    assert redirect.closed is True
    assert redirect.yielded_bytes == 16 + len(b"redirect")
    assert budget.snapshot() == {"http_requests": 2, "unique_urls": 2}


@pytest.mark.parametrize("status", [403, 429])
def test_controlled_block_status_closes_before_application_body_read_without_retry(
    status: int,
) -> None:
    response = SyntheticStreamingResponse(
        "https://synthetic.example/course",
        [b"x" * 16 * 1024, b"x" * (1024 * 1024 - 16 * 1024)],
    )
    response.status_code = status
    requests: list[str] = []

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            requests.append(url)
            return await synthetic_response_via_content_callback(response, kwargs)

    budget = FG2RequestBudget(
        max_unique_urls=10,
        max_http_requests=20,
        min_interval_seconds=0,
        max_retry_after_seconds=30,
        max_attempts_per_url=3,
        request_preparer=lambda _url: {},
        requester=harvester_module._send_controlled_request,
    )
    with patch.object(harvester_module, "AsyncSession", CapturedSession):
        for url in (
            "https://synthetic.example/course",
            "https://synthetic.example/another",
        ):
            with pytest.raises(SourceBlocked):
                asyncio.run(
                    budget.get(
                        object(),
                        url,
                        allowed_origin="https://synthetic.example",
                    )
                )

    assert requests == ["https://synthetic.example/course"]
    assert response.prefetched_bytes == 16 * 1024
    assert response.yielded_bytes == 0
    assert response.content == b""
    assert budget.http_requests == 1


def test_noncontrolled_harvester_uses_dns_pinned_get_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    xml_body = (
        f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{COURSE_URL}</loc></url></urlset>"
    ).encode()
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "seed_urls": [sitemap_url],
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
            max_discovered_urls=5,
        )
    harvester.check_time_guard = lambda: False
    response = SyntheticStreamingResponse(sitemap_url, [xml_body], "application/xml")
    response.content = xml_body
    calls: list[dict[str, Any]] = []
    session_options: list[dict[str, Any]] = []

    class CapturedSession:
        def __init__(self, **kwargs: Any) -> None:
            session_options.append(kwargs)

        async def __aenter__(self) -> "CapturedSession":
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, _url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            calls.append(kwargs)
            return response

    monkeypatch.setattr(harvester_module, "validate_public_request_url", synthetic_public_request_binding)
    monkeypatch.setattr(harvester_module, "AsyncSession", lambda **kwargs: CapturedSession(**kwargs))
    assert asyncio.run(harvester._fetch_sitemap(object(), sitemap_url)) == [COURSE_URL]
    assert session_options[0]["curl_options"][harvester_module.CurlOpt.RESOLVE] == [
        SYNTHETIC_RESOLVE_ENTRY
    ]
    assert calls[0]["allow_redirects"] is False
    assert "content_callback" not in calls[0]
    assert "stream" not in calls[0]
    assert response.content == xml_body
    assert adapter.tables["staging_raw"] == []


def test_controlled_scheduled_sitemap_keeps_partial_candidates_for_next_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "seed_urls": [f"{BASE_URL}/sitemap.xml"],
        "exclusion_patterns": [],
        "allowed_url_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    manifest_path = tmp_path / "fg2-partial-sitemap-manifest.json"

    class NoopSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    def new_scheduled_harvester():
        with patch.object(harvester_module, "get_db_client", return_value=adapter):
            current = UniversalHarvester(
                {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
                max_discovered_urls=10,
                scheduled_cohort=True,
            )
        current.controlled = True
        current.approved_lot = None
        current.approved_lot_scope = None
        current.controlled_seed_urls = [f"{BASE_URL}/sitemap.xml"]
        current.cohort_manifest_path = str(manifest_path)
        current._course_for_refresh = lambda _url: {
            "kind": "new_discovery",
            "course_id": None,
        }
        return current

    def write_manifest(run_id: str) -> None:
        initialize_manifest(
            manifest_path,
            run_id=run_id,
            run_attempt=1,
            source_sha="a" * 40,
            institutions=[
                {
                    "institution_id": INSTITUTION_ID,
                    "profile_sha256": "b" * 64,
                    "seed_sha256": "c" * 64,
                    "http_requests": 2,
                    "unique_urls": 2,
                    "result": "deferred",
                }
            ],
        )

    monkeypatch.setattr(harvester_module, "AsyncSession", lambda: NoopSession())

    first_run = new_scheduled_harvester()
    assert first_run.scheduled_cohort is True

    async def stop_after_partial_sitemap(_session, _sitemap_url):
        first_run.controlled_stop_reason = "RunBudgetExceeded"
        return [COURSE_URL]

    first_run._fetch_sitemap = stop_after_partial_sitemap
    write_manifest("123456789")
    first_result = asyncio.run(first_run.discover_courses())

    assert first_result == [COURSE_URL]
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["url"] == COURSE_URL
    assert adapter.tables["staging_raw"][0]["status"] == "discovered"
    first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert first_manifest["entries"] == []
    assert len(first_manifest["discovery_rows"]) == 1
    assert FG2CohortManifest.load(manifest_path, allow_empty=True).staging_ids == ()

    second_run = new_scheduled_harvester()

    async def recover_same_link(_session, _sitemap_url):
        return [COURSE_URL]

    second_run._fetch_sitemap = recover_same_link
    write_manifest("123456790")
    second_result = asyncio.run(second_run.discover_courses())

    assert second_result == [COURSE_URL]
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["status"] == "discovered"
    second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert second_manifest["entries"] == []
    assert len(second_manifest["discovery_rows"]) == 1


def test_controlled_sitemap_index_returns_links_read_before_request_budget_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_url = f"{BASE_URL}/sitemap.xml"
    child_one = f"{BASE_URL}/sitemap-one.xml"
    child_two = f"{BASE_URL}/sitemap-two.xml"
    child_three = f"{BASE_URL}/sitemap-three.xml"
    first_course = f"{BASE_URL}/programs/first"
    direct_course = f"{BASE_URL}/programs/direct"
    root_xml = f"""<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>{child_one}</loc></sitemap>
      <sitemap><loc>{child_two}</loc></sitemap>
      <sitemap><loc>{child_three}</loc></sitemap>
      <url><loc>{direct_course}</loc></url>
    </sitemapindex>"""
    child_xml = f"""<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{first_course}</loc></url>
    </urlset>"""

    harvester = object.__new__(UniversalHarvester)
    harvester.controlled = True
    harvester.controlled_stop_reason = None
    harvester._discovery_fetch_attempts = 0
    harvester._discovery_fetch_successes = 0
    harvester.check_time_guard = lambda: False
    calls: list[str] = []

    async def fake_safe_request(_session: Any, url: str) -> SyntheticResponse:
        calls.append(url)
        if url == child_two:
            harvester.controlled_stop_reason = "RunBudgetExceeded"
            raise RunBudgetExceeded("synthetic request budget exhausted")
        if url == root_url:
            return SyntheticResponse(url, root_xml, "application/xml")
        if url == child_one:
            return SyntheticResponse(url, child_xml, "application/xml")
        raise AssertionError("no request may start after the budget stop")

    harvester._safe_request = fake_safe_request
    monkeypatch.setattr(harvester_module, "logger", Mock())

    links = asyncio.run(harvester._fetch_sitemap(object(), root_url))

    assert calls == [root_url, child_one, child_two]
    assert links == [first_course, direct_course]
    assert harvester.controlled_stop_reason == "RunBudgetExceeded"


def test_controlled_compressed_sitemap_is_rejected_before_request() -> None:
    harvester = object.__new__(UniversalHarvester)
    harvester.controlled = True
    harvester.controlled_stop_reason = None
    harvester.check_time_guard = lambda: False
    request = Mock(side_effect=AssertionError("compressed sitemap must not be requested"))
    harvester._safe_request = request

    result = asyncio.run(
        harvester._fetch_sitemap(object(), f"{BASE_URL}/sitemap.xml.gz")
    )

    assert result == []
    assert harvester.controlled_stop_reason == "UnsupportedCompressedSitemap"
    request.assert_not_called()


def test_noncontrolled_sitemap_does_not_apply_controlled_body_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "seed_urls": [sitemap_url],
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
            max_discovered_urls=5,
        )
    harvester.check_time_guard = lambda: False
    response = SyntheticStreamingResponse(
        sitemap_url,
        [b"<urlset>", b"x"],
        "application/xml",
    )
    response.content = b"<urlset>x"

    class CapturedSession:
        async def __aenter__(self) -> "CapturedSession":
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, _url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            assert "content_callback" not in kwargs
            return response

    monkeypatch.setattr(
        harvester_module,
        "validate_public_request_url",
        lambda _url, **_kwargs: (
            "https://synthetic.h3.example:443",
            "synthetic.h3.example:443:93.184.216.34",
        ),
    )
    monkeypatch.setattr(harvester_module, "AsyncSession", lambda **_kwargs: CapturedSession())
    with patch.object(harvester_module.ET, "fromstring") as parse_xml:
        assert asyncio.run(harvester._fetch_sitemap(object(), sitemap_url)) == []

    assert "content-length" not in response.headers
    assert response.yielded_bytes == 0
    assert response.closed is False
    assert response.content == b"<urlset>x"
    parse_xml.assert_called_once()
    assert adapter.tables["staging_raw"] == []
    assert adapter.upsert_calls == []


def test_noncontrolled_course_get_does_not_apply_controlled_body_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "seed_urls": [COURSE_URL],
        "exclusion_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
            max_discovered_urls=5,
        )
    response = SyntheticStreamingResponse(COURSE_URL, [b"<html>xx", b"x"])
    response.content = b"<html>xxx"
    calls: list[dict[str, Any]] = []

    class CapturedSession:
        async def __aenter__(self) -> "CapturedSession":
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, _url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            calls.append(kwargs)
            return response

    async def no_delay(_seconds: float) -> None:
        return None

    monkeypatch.setattr(harvester_module, "validate_public_request_url", synthetic_public_request_binding)
    monkeypatch.setattr(harvester_module, "AsyncSession", lambda **_kwargs: CapturedSession())
    monkeypatch.setattr(harvester_module.random, "uniform", lambda *_args: 0)
    with patch.object(harvester_module.asyncio, "sleep", new=no_delay):
        result = asyncio.run(harvester._safe_request(CapturedSession(), COURSE_URL))

    assert result is response
    assert response.content == b"<html>xxx"
    assert calls and "content_callback" not in calls[0]
    assert adapter.tables["staging_raw"] == []
    assert adapter.upsert_calls == []


def test_site_diagnostics_streams_and_rejects_oversized_html_before_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SyntheticRequestsResponse:
        status_code = 200
        url = f"{BASE_URL}/"
        encoding = "utf-8"

        def __init__(self, chunks: list[bytes], status_code: int = 200, location: str | None = None) -> None:
            self.chunks = chunks
            self.yielded_bytes = 0
            self.closed = False
            self.status_code = status_code
            self.headers = {"location": location} if location else {}
            self._content: bytes | None = None

        @property
        def text(self) -> str:
            if self._content is None:
                raise AssertionError("response.text must wait for bounded body materialization")
            return self._content.decode(self.encoding)

        def iter_content(self, chunk_size: int):
            assert chunk_size > 0
            for chunk in self.chunks:
                self.yielded_bytes += len(chunk)
                yield chunk

        def close(self) -> None:
            self.closed = True

    class CapturedSession:
        max_redirects = 30

        def __init__(self, responses: list[SyntheticRequestsResponse]) -> None:
            self.responses = list(responses)
            self.calls: list[tuple[str, dict[str, Any]]] = []
            self.closed = False

        def get(self, url: str, **kwargs: Any) -> SyntheticRequestsResponse:
            self.calls.append((url, kwargs))
            assert kwargs["stream"] is True
            assert kwargs["allow_redirects"] is False
            return self.responses.pop(0)

        def close(self) -> None:
            self.closed = True

    good_body = b"<html><title>Synthetic Academy</title><body>Cursos</body></html>"
    good_response = SyntheticRequestsResponse([good_body])
    good_session = CapturedSession([good_response])
    good_session_options: list[dict[str, Any]] = []
    monkeypatch.setattr(
        site_diagnostics_module, "MAX_RESPONSE_BODY_BYTES", len(good_body), raising=False
    )
    monkeypatch.setattr(
        site_diagnostics_module,
        "validate_public_request_url",
        lambda _url, **_kwargs: ("https://synthetic.h3.example:443", "synthetic.h3.example:443:93.184.216.34"),
    )
    monkeypatch.setattr(
        site_diagnostics_module,
        "CurlSession",
        lambda **kwargs: good_session_options.append(kwargs) or good_session,
    )
    result = site_diagnostics_module.diagnose_site(f"{BASE_URL}/")

    assert "institution_site_profile" in result
    assert good_response.closed is True
    assert good_session.calls[0][0] == f"{BASE_URL}/"
    assert good_session.closed is True
    assert good_session_options[0]["curl_options"][site_diagnostics_module.CurlOpt.RESOLVE] == [
        "synthetic.h3.example:443:93.184.216.34"
    ]

    body_limit = 8
    oversized_response = SyntheticRequestsResponse([b"<html>", b"xxx"])
    oversized_session = CapturedSession([oversized_response])
    monkeypatch.setattr(
        site_diagnostics_module, "MAX_RESPONSE_BODY_BYTES", body_limit, raising=False
    )
    monkeypatch.setattr(
        site_diagnostics_module, "CurlSession", lambda **_kwargs: oversized_session
    )
    with patch.object(site_diagnostics_module, "detect_cms") as parse_html:
        result = site_diagnostics_module.diagnose_site(f"{BASE_URL}/")

    assert "error" in result
    assert "content-length" not in oversized_response.headers
    assert oversized_response.yielded_bytes == body_limit + 1
    assert oversized_response.closed is True
    assert oversized_session.closed is True
    parse_html.assert_not_called()


def test_detect_noise_patterns_uses_the_shared_catalog_filter() -> None:
    html = (
        '<a href="/blog/actualidad">Noticia</a>'
        '<a href="/programas/analitica">Programa</a>'
    )

    noise_links = site_diagnostics_module.detect_noise_patterns(html, BASE_URL)

    assert noise_links == [f"{BASE_URL}/blog/actualidad"]


def test_site_diagnostics_preserves_redirect_following_without_reading_redirect_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SyntheticRequestsResponse:
        encoding = "utf-8"

        def __init__(self, url: str, status_code: int, chunks: list[bytes], location: str | None = None) -> None:
            self.url = url
            self.status_code = status_code
            self.chunks = chunks
            self.yielded_bytes = 0
            self.closed = False
            self.headers = {"location": location} if location else {}
            self._content: bytes | None = None

        @property
        def text(self) -> str:
            if self._content is None:
                raise AssertionError("response.text must wait for bounded body materialization")
            return self._content.decode(self.encoding)

        def iter_content(self, chunk_size: int):
            assert chunk_size > 0
            for chunk in self.chunks:
                self.yielded_bytes += len(chunk)
                yield chunk

        def close(self) -> None:
            self.closed = True

    class CapturedSession:
        max_redirects = 30

        def __init__(self, responses: list[SyntheticRequestsResponse]) -> None:
            self.responses = list(responses)
            self.calls: list[tuple[str, dict[str, Any]]] = []
            self.closed = False

        def get(self, url: str, **kwargs: Any) -> SyntheticRequestsResponse:
            self.calls.append((url, kwargs))
            assert kwargs["stream"] is True
            assert kwargs["allow_redirects"] is False
            return self.responses.pop(0)

        def close(self) -> None:
            self.closed = True

    root = f"{BASE_URL}/"
    final_url = f"{BASE_URL}/catalog"
    redirect = SyntheticRequestsResponse(root, 302, [b"unread redirect body"], "/catalog")
    final = SyntheticRequestsResponse(
        final_url, 200, [b"<html><title>Synthetic Academy</title><body>Cursos</body></html>"]
    )
    session = CapturedSession([redirect, final])
    session_options: list[dict[str, Any]] = []
    monkeypatch.setattr(
        site_diagnostics_module, "MAX_RESPONSE_BODY_BYTES", 1024, raising=False
    )

    monkeypatch.setattr(
        site_diagnostics_module,
        "validate_public_request_url",
        lambda _url, **_kwargs: ("https://synthetic.h3.example:443", "synthetic.h3.example:443:93.184.216.34"),
    )
    monkeypatch.setattr(
        site_diagnostics_module,
        "validate_public_redirect_target",
        lambda _current, location, **_kwargs: (
            f"https://synthetic.h3.example{location}",
            "synthetic.h3.example:443:93.184.216.34",
        ),
    )
    monkeypatch.setattr(
        site_diagnostics_module,
        "CurlSession",
        lambda **kwargs: session_options.append(kwargs) or session,
    )
    result = site_diagnostics_module.diagnose_site(root)

    assert "institution_site_profile" in result
    assert [url for url, _kwargs in session.calls[:2]] == [root, final_url]
    assert len(session_options) >= 2
    assert all(
        options["curl_options"][site_diagnostics_module.CurlOpt.RESOLVE]
        == ["synthetic.h3.example:443:93.184.216.34"]
        for options in session_options
    )
    assert redirect.closed is True
    assert redirect.yielded_bytes == 0
    assert final.closed is True
    assert session.closed is True


def test_site_diagnostics_blocks_private_redirect_before_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SyntheticResponse:
        status_code = 302
        url = f"{BASE_URL}/"
        headers = {"location": "http://169.254.169.254/latest/meta-data/"}
        closed = False

        def close(self) -> None:
            self.closed = True

    class CapturedSession:
        def __init__(self) -> None:
            self.calls: list[str] = []
            self.closed = False

        def get(self, url: str, **_kwargs: Any) -> SyntheticResponse:
            self.calls.append(url)
            return response

        def close(self) -> None:
            self.closed = True

    response = SyntheticResponse()
    session = CapturedSession()
    monkeypatch.setattr(
        site_diagnostics_module,
        "validate_public_request_url",
        lambda _url, **_kwargs: ("https://synthetic.h3.example:443", "synthetic.h3.example:443:93.184.216.34"),
    )

    def reject_private_redirect(_current: str, location: str, **_kwargs: Any):
        assert "169.254.169.254" in location
        raise site_diagnostics_module.UnsafePublicTarget("private redirect fixture")

    monkeypatch.setattr(
        site_diagnostics_module, "validate_public_redirect_target", reject_private_redirect
    )
    monkeypatch.setattr(
        site_diagnostics_module, "CurlSession", lambda **_kwargs: session
    )

    with pytest.raises(site_diagnostics_module.UnsafePublicTarget):
        site_diagnostics_module._bounded_get(f"{BASE_URL}/", timeout=5)

    assert session.calls == [f"{BASE_URL}/"]
    assert response.closed is True
    assert session.closed is True


def test_controlled_transport_aborts_chunked_loopback_response_at_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        harvester_module,
        "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES",
        4096,
        raising=False,
    )

    class ChunkedFixtureHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            chunk = b"x" * 4096
            for _ in range(3000):
                try:
                    self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
                    self.wfile.flush()
                    self.server.chunks_sent += 1
                except OSError:
                    self.server.client_disconnected = True
                    return
                time.sleep(0.001)
            self.server.completed = True

        def log_message(self, *_args: Any) -> None:
            return None

    server = ThreadingHTTPServer(("127.0.0.1", 0), ChunkedFixtureHandler)
    server.chunks_sent = 0
    server.client_disconnected = False
    server.completed = False
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()
    fixture_url = f"http://127.0.0.1:{server.server_port}/fixture"
    try:
        with pytest.raises(RuntimeError, match="controlled response body exceeds"):
            asyncio.run(
                harvester_module._send_controlled_request(
                    object(), fixture_url, {}, "chrome110", 5
                )
            )
    finally:
        server.shutdown()
        server.server_close()
        serving.join(timeout=2)

    assert server.client_disconnected is True
    assert server.completed is False
    assert server.chunks_sent < 3000


@pytest.mark.parametrize("status", [403, 429])
def test_controlled_block_status_closes_chunked_loopback_without_retry(
    status: int,
) -> None:
    class ChunkedBlockFixtureHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            chunk = b"x" * 4096
            for _ in range(3000):
                try:
                    self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
                    self.wfile.flush()
                    self.server.chunks_sent += 1
                except OSError:
                    self.server.client_disconnected = True
                    return
                time.sleep(0.001)
            self.server.completed = True

        def log_message(self, *_args: Any) -> None:
            return None

    server = ThreadingHTTPServer(("127.0.0.1", 0), ChunkedBlockFixtureHandler)
    server.chunks_sent = 0
    server.client_disconnected = False
    server.completed = False
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()
    fixture_url = f"http://127.0.0.1:{server.server_port}/blocked"
    try:
        with pytest.raises(SourceBlocked):
            asyncio.run(
                harvester_module._send_controlled_request(
                    object(), fixture_url, {}, "chrome110", 5
                )
            )
    finally:
        server.shutdown()
        server.server_close()
        serving.join(timeout=2)

    assert server.client_disconnected is True
    assert server.completed is False
    assert server.chunks_sent < 3000


def test_oversized_controlled_body_defers_origin_without_staging_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body_limit = 64
    monkeypatch.setattr(
        harvester_module,
        "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES",
        body_limit,
        raising=False,
    )
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "exclusion_patterns": [],
        "allowed_url_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
            max_discovered_urls=10,
        )
    manifest_path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )

    harvester.controlled = True
    harvester.cohort_manifest_path = str(manifest_path)
    harvester.approved_lot = None
    harvester.approved_lot_scope = None
    harvester.request_budget = FG2RequestBudget(
        min_interval_seconds=0,
        max_attempts_per_url=1,
        request_preparer=lambda _url: {"fixture": True},
        requester=harvester_module._send_controlled_request,
    )
    linked_page = b"<html><a href='/programs/should-not-stage'>Course</a></html>"
    response_fixture = SyntheticStreamingResponse(
        f"{BASE_URL}/catalog",
        [linked_page, b"x" * (body_limit + 1)],
    )
    contacted: list[str] = []

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            contacted.append(url)
            return await synthetic_response_via_content_callback(response_fixture, kwargs)

    save_discovered = Mock(wraps=harvester._save_discovered_url)
    harvester._save_discovered_url = save_discovered
    with patch.object(harvester_module, "AsyncSession", CapturedSession):
        asyncio.run(harvester._bfs_crawl(f"{BASE_URL}/catalog", set()))

    assert contacted == [f"{BASE_URL}/catalog"]
    assert response_fixture.closed is True
    assert harvester.controlled_stop_reason == "ResponseBodyTooLarge"
    assert harvester.request_budget.snapshot() == {"http_requests": 1, "unique_urls": 1}
    assert adapter.tables["staging_raw"] == []
    assert adapter.upsert_calls == []
    save_discovered.assert_not_called()

    with pytest.raises(RuntimeError, match="origin deferred"):
        asyncio.run(harvester._safe_request(object(), f"{BASE_URL}/programs/next"))
    assert contacted == [f"{BASE_URL}/catalog"]


def test_oversized_controlled_hardcoded_seed_does_not_write_discovered_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body_limit = 64
    monkeypatch.setattr(
        harvester_module,
        "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES",
        body_limit,
        raising=False,
    )
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "seed_urls": [COURSE_URL],
        "exclusion_patterns": [],
        "allowed_url_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
            max_discovered_urls=10,
        )

    manifest_path = tmp_path / "fg2_hardcoded_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    harvester.controlled = True
    harvester.cohort_manifest_path = str(manifest_path)
    harvester.approved_lot = object()
    harvester.approved_lot_scope = {
        normalize_url(COURSE_URL): {
            "institution_id": INSTITUTION_ID,
            "snapshot": {"staging_rows": [], "course_rows": []}
        }
    }
    harvester._verify_approved_institution_binding = Mock()
    harvester._course_for_refresh = Mock(
        return_value={"kind": "new_discovery", "course_id": None}
    )
    harvester.request_budget = FG2RequestBudget(
        min_interval_seconds=0,
        max_attempts_per_url=1,
        allowed_urls=[COURSE_URL],
        request_preparer=lambda _url: {"fixture": True},
        requester=harvester_module._send_controlled_request,
    )
    fixture = SyntheticStreamingResponse(
        COURSE_URL,
        [b"<html>synthetic, but too large</html>", b"x" * body_limit],
    )
    save_discovered = Mock(wraps=harvester._save_discovered_url)
    harvester._save_discovered_url = save_discovered

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, _url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            return await synthetic_response_via_content_callback(fixture, kwargs)

    with patch.object(harvester_module, "AsyncSession", CapturedSession), patch.object(
        harvester_module, "verify_approved_lot_scope", return_value=None
    ):
        urls = asyncio.run(harvester.discover_courses())
        assert urls == [COURSE_URL]
        with pytest.raises(harvester_module.ResponseBodyTooLarge):
            asyncio.run(harvester._safe_request(object(), COURSE_URL))

    assert fixture.closed is True
    assert fixture.yielded_bytes > body_limit
    assert harvester.controlled_stop_reason == "ResponseBodyTooLarge"
    assert harvester.request_budget.snapshot() == {"http_requests": 1, "unique_urls": 1}
    assert adapter.tables["staging_raw"] == []
    save_discovered.assert_not_called()


def test_controlled_hardcoded_seed_writes_after_valid_bounded_response(
    tmp_path: Path,
) -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "seed_urls": [COURSE_URL],
        "exclusion_patterns": [],
        "allowed_url_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
            max_discovered_urls=10,
        )

    manifest_path = tmp_path / "fg2_valid_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    harvester.controlled = True
    harvester.cohort_manifest_path = str(manifest_path)
    harvester.approved_lot = object()
    harvester.approved_lot_scope = {
        normalize_url(COURSE_URL): {
            "institution_id": INSTITUTION_ID,
            "snapshot": {"staging_rows": [], "course_rows": []}
        }
    }
    harvester._verify_approved_institution_binding = Mock()
    harvester._course_for_refresh = Mock(
        return_value={"kind": "new_discovery", "course_id": None}
    )
    harvester.request_budget = FG2RequestBudget(
        min_interval_seconds=0,
        max_attempts_per_url=1,
        allowed_urls=[COURSE_URL],
        request_preparer=lambda _url: {"fixture": True},
        requester=harvester_module._send_controlled_request,
    )
    fixture = SyntheticStreamingResponse(COURSE_URL, [COURSE_HTML.encode()])

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, _url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            return await synthetic_response_via_content_callback(fixture, kwargs)

    with patch.object(harvester_module, "AsyncSession", CapturedSession), patch.object(
        harvester_module, "verify_approved_lot_scope", return_value=None
    ):
        urls = asyncio.run(harvester.discover_courses())
        assert urls == [COURSE_URL]
        assert adapter.tables["staging_raw"] == []
        item = asyncio.run(harvester._scrape_http(object(), COURSE_URL))
        assert item is not None
        staged = harvester._save_to_staging(item)

    assert staged["status"] == "pending"
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["status"] == "pending"
    assert harvester.request_budget.snapshot() == {"http_requests": 1, "unique_urls": 1}
    update_manifest_institution(
        manifest_path,
        institution_id=INSTITUTION_ID,
        http_requests=1,
        unique_urls=1,
        result="complete",
    )
    manifest = FG2CohortManifest.load(manifest_path, allow_empty=False)
    assert manifest.payload["entries"][0]["url_sha256"] == hashlib.sha256(
        COURSE_URL.encode()
    ).hexdigest()


def test_oversized_controlled_sitemap_detail_does_not_persist_discovered_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body_limit = 512
    monkeypatch.setattr(
        harvester_module,
        "CONTROLLED_RESPONSE_BODY_LIMIT_BYTES",
        body_limit,
        raising=False,
    )
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "website_url": BASE_URL,
        "seed_urls": [sitemap_url],
        "exclusion_patterns": [],
        "allowed_url_patterns": [],
    }
    adapter = SyntheticPipelineAdapter(profile)
    with patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            {"id": INSTITUTION_ID, "name": "Synthetic Academy", "website_url": BASE_URL},
            max_discovered_urls=10,
        )

    manifest_path = tmp_path / "fg2_sitemap_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    harvester.controlled = True
    harvester.cohort_manifest_path = str(manifest_path)
    harvester.controlled_seed_urls = [sitemap_url]
    harvester.approved_lot = object()
    harvester.approved_lot_scope = {
        normalize_url(COURSE_URL): {
            "snapshot": {"staging_rows": [], "course_rows": []}
        }
    }
    harvester._verify_approved_institution_binding = Mock()
    harvester._course_for_refresh = Mock(
        return_value={"kind": "new_discovery", "course_id": None}
    )
    harvester.request_budget = FG2RequestBudget(
        min_interval_seconds=0,
        max_attempts_per_url=1,
        allowed_urls=[sitemap_url, COURSE_URL],
        request_preparer=lambda _url: {"fixture": True},
        requester=harvester_module._send_controlled_request,
    )
    sitemap_response = SyntheticStreamingResponse(
        sitemap_url, [SITEMAP], "application/xml"
    )
    detail_response = SyntheticStreamingResponse(
        COURSE_URL,
        [b"<html>synthetic page body</html>", b"x" * body_limit],
    )
    requests: list[str] = []

    class CapturedSession:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> SyntheticStreamingResponse:
            requests.append(url)
            response = sitemap_response if url == sitemap_url else detail_response
            return await synthetic_response_via_content_callback(response, kwargs)

    save_discovered = Mock(wraps=harvester._save_discovered_url)
    harvester._save_discovered_url = save_discovered
    with patch.object(harvester_module, "AsyncSession", CapturedSession), patch.object(
        harvester_module, "verify_approved_lot_scope", return_value=None
    ):
        urls = asyncio.run(harvester.discover_courses())
        assert urls == [COURSE_URL]
        assert adapter.tables["staging_raw"] == []
        with pytest.raises(harvester_module.HarvesterPartialError):
            asyncio.run(harvester._scrape_http(object(), COURSE_URL))

    assert requests == [sitemap_url, COURSE_URL]
    assert sitemap_response.closed is True
    assert detail_response.closed is True
    assert harvester.controlled_stop_reason == "ResponseBodyTooLarge"
    assert harvester.request_budget.snapshot() == {"http_requests": 2, "unique_urls": 2}
    assert adapter.tables["staging_raw"] == []
    save_discovered.assert_not_called()


def test_fg2_controlled_logs_redact_urls_and_profiles() -> None:
    secret_url = "https://synthetic.example/program?token=fixture-secret"
    with patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": "true"}, clear=False):
        assert harvester_module._safe_url_label(secret_url) == "source_url=redacted"
        assert harvester_module._safe_institution_label("private fixture institution") == "canary_cohort=redacted"
        assert harvester_module._safe_error_label(RuntimeError(secret_url)) == "RuntimeError"


def test_direct_controlled_harvester_entrypoint_enables_redaction_before_validation() -> None:
    with patch.dict(os.environ, {"FG2_CONTROLLED_FIRST_RUN": ""}, clear=False), patch.object(
        sys,
        "argv",
        ["universal_harvester.py", "{}", "--controlled"],
    ):
        result = asyncio.run(harvester_module.main())

        assert result == 1
        assert os.environ["FG2_CONTROLLED_FIRST_RUN"] == "true"
        assert harvester_module._safe_url_label("https://synthetic.example/?token=secret") == "source_url=redacted"


def test_controlled_harvest_shares_pacing_across_institutions_with_same_origin(tmp_path: Path) -> None:
    second_institution_id = "00000000-0000-0000-0000-000000000002"
    profiles = [
        {
            "institution_id": institution_id,
            "site_type": "traditional_ssr",
            "discovery_mode": "hardcoded_urls",
            "discovery_enabled": True,
            "pipeline_enabled": True,
            "production_enabled": True,
            "circuit_open": False,
            "seed_urls": [f"{BASE_URL}/programs/{slug}"],
            "exclusion_patterns": [],
        }
        for institution_id, slug in ((INSTITUTION_ID, "a"), (second_institution_id, "b"))
    ]
    institutions = [
        {
            "id": profile["institution_id"],
            "name": f"Synthetic {profile['institution_id'][-1]}",
            "slug": f"synthetic-{profile['institution_id'][-1]}",
            "website_url": BASE_URL,
        }
        for profile in profiles
    ]
    preflights = [
        validate_controlled_profile(institution, profile)
        for institution, profile in zip(institutions, profiles)
    ]
    manifest_path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": institution["id"],
                "profile_sha256": preflight["profile_sha256"],
                "seed_sha256": preflight["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
            for institution, preflight in zip(institutions, preflights)
        ],
    )

    class FakeClock:
        def __init__(self) -> None:
            self.now = 0.0

        def monotonic(self) -> float:
            return self.now

        def utcnow(self):
            from datetime import datetime, timezone

            return datetime(2026, 11, 9, tzinfo=timezone.utc)

        async def sleep(self, seconds: float) -> None:
            self.now += seconds
            await asyncio.sleep(0)

    class RecordingSession:
        def __init__(self, clock: FakeClock) -> None:
            self.clock = clock
            self.starts: list[float] = []

        async def get(self, url: str, **_kwargs: Any) -> SyntheticResponse:
            self.starts.append(self.clock.monotonic())
            return SyntheticResponse(url, "<html><body>synthetic</body></html>", "text/html")

    clock = FakeClock()
    real_budget_class = FG2RequestBudget

    def controlled_budget(**kwargs: Any) -> FG2RequestBudget:
        return real_budget_class(
            **kwargs,
            monotonic=clock.monotonic,
            sleeper=clock.sleep,
            utcnow=clock.utcnow,
        )

    with patch.dict(
        os.environ,
        {"GITHUB_RUN_ID": "123456789", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40},
    ), patch.object(harvester_module, "get_db_client", side_effect=[
        SyntheticPipelineAdapter(profiles[0]), SyntheticPipelineAdapter(profiles[1])
    ]), patch.object(harvester_module, "FG2RequestBudget", side_effect=controlled_budget):
        first_harvester = UniversalHarvester(
            dict(
                institutions[0],
                _controlled_profile_sha256=preflights[0]["profile_sha256"],
                _controlled_seed_sha256=preflights[0]["seed_sha256"],
            ),
            max_discovered_urls=10,
            controlled=True,
            cohort_manifest=str(manifest_path),
            _controlled_transport=SyntheticControlledTransport(),
        )
        first_session = RecordingSession(clock)
        asyncio.run(first_harvester._safe_request(first_session, profiles[0]["seed_urls"][0]))

        second_harvester = UniversalHarvester(
            dict(
                institutions[1],
                _controlled_profile_sha256=preflights[1]["profile_sha256"],
                _controlled_seed_sha256=preflights[1]["seed_sha256"],
            ),
            max_discovered_urls=10,
            controlled=True,
            cohort_manifest=str(manifest_path),
            _controlled_transport=SyntheticControlledTransport(),
        )
        second_session = RecordingSession(clock)
        asyncio.run(second_harvester._safe_request(second_session, profiles[1]["seed_urls"][0]))

    assert second_session.starts[0] - first_session.starts[0] >= 5
    manifest = FG2CohortManifest.load(manifest_path, allow_empty=True)
    assert len(manifest.payload["origin_state"]) == 1
    assert "synthetic.h3.example" not in manifest_path.read_text(encoding="utf-8")


def test_controlled_harvest_never_resumes_discovered_rows_outside_current_seeds(tmp_path: Path) -> None:
    unrelated_url = f"{BASE_URL}/programs/not-in-current-seeds"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "circuit_open": False,
        "seed_urls": [COURSE_URL],
        "exclusion_patterns": [],
    }
    institution = {
        "id": INSTITUTION_ID,
        "name": "Synthetic Academy",
        "slug": "synthetic",
        "website_url": BASE_URL,
    }
    adapter = SyntheticPipelineAdapter(profile)
    historical_discovered = {
        "id": "40000000-0000-0000-0000-000000000092",
        "institution_id": INSTITUTION_ID,
        "url": unrelated_url,
        "status": "discovered",
        "content_hash": None,
    }
    adapter.tables["staging_raw"].append(historical_discovered)
    preflight = validate_controlled_profile(institution, profile)
    manifest_path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": preflight["profile_sha256"],
                "seed_sha256": preflight["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    with patch.dict(
        os.environ,
        {"GITHUB_RUN_ID": "123456789", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40},
    ), patch.object(harvester_module, "get_db_client", return_value=adapter):
        harvester = UniversalHarvester(
            dict(
                institution,
                _controlled_profile_sha256=preflight["profile_sha256"],
                _controlled_seed_sha256=preflight["seed_sha256"],
            ),
            max_discovered_urls=10,
            controlled=True,
            cohort_manifest=str(manifest_path),
            _controlled_transport=SyntheticControlledTransport(),
        )

    discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [COURSE_URL]
    assert historical_discovered["status"] == "discovered"
    assert all(url != unrelated_url for url in discovered)
    manifest = FG2CohortManifest.load(manifest_path, allow_empty=True)
    assert manifest.payload["entries"] == []
    assert [row["staging_id"] for row in manifest.payload["discovery_rows"]] == [
        "40000000-0000-0000-0000-000000000091"
    ]
    assert manifest.payload["discovery_rows"][0]["url_sha256"] == hashlib.sha256(COURSE_URL.encode()).hexdigest()

    class BlockedResponse:
        status_code = 429
        headers = {"Retry-After": "0"}
        url = COURSE_URL

    class BlockingSession:
        def __init__(self) -> None:
            self.calls = 0

        async def get(self, _url: str, **_kwargs: Any) -> BlockedResponse:
            self.calls += 1
            return BlockedResponse()

    session = BlockingSession()
    with pytest.raises(SourceBlocked):
        asyncio.run(harvester._safe_request(session, COURSE_URL))
    with pytest.raises(SourceBlocked):
        asyncio.run(harvester._safe_request(session, COURSE_URL))
    assert session.calls == 1
    assert harvester.controlled_stop_reason == "SourceBlocked"
    assert adapter.tables["staging_raw"][1]["status"] == "discovered"


def test_controlled_sitemap_resumes_discovered_rows_only_when_present_in_current_sitemap(tmp_path: Path) -> None:
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "circuit_open": False,
        "seed_urls": [sitemap_url],
        "exclusion_patterns": [],
    }
    institution = {
        "id": INSTITUTION_ID,
        "name": "Synthetic Academy",
        "slug": "synthetic",
        "website_url": BASE_URL,
    }
    adapter = SyntheticPipelineAdapter(profile)
    existing_discovered = {
        "id": "40000000-0000-0000-0000-000000000093",
        "institution_id": INSTITUTION_ID,
        "url": COURSE_URL,
        "status": "discovered",
        "content_hash": None,
    }
    outside_sitemap = {
        "id": "40000000-0000-0000-0000-000000000094",
        "institution_id": INSTITUTION_ID,
        "url": f"{BASE_URL}/programs/old-not-listed",
        "status": "discovered",
        "content_hash": None,
    }
    adapter.tables["staging_raw"].extend([existing_discovered, outside_sitemap])
    preflight = validate_controlled_profile(institution, profile)
    manifest_path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": preflight["profile_sha256"],
                "seed_sha256": preflight["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )

    class FakeSitemapSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **_kwargs: Any) -> SyntheticResponse:
            assert url == sitemap_url
            return SyntheticResponse(url, SITEMAP, "application/xml")

    with patch.dict(
        os.environ,
        {"GITHUB_RUN_ID": "123456789", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40},
    ), patch.object(harvester_module, "get_db_client", return_value=adapter), patch.object(
        harvester_module, "AsyncSession", FakeSitemapSession
    ):
        harvester = UniversalHarvester(
            dict(
                institution,
                _controlled_profile_sha256=preflight["profile_sha256"],
                _controlled_seed_sha256=preflight["seed_sha256"],
            ),
            max_discovered_urls=10,
            controlled=True,
            cohort_manifest=str(manifest_path),
            _controlled_transport=SyntheticControlledTransport(),
        )
        discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [COURSE_URL]
    assert existing_discovered["status"] == "discovered"
    assert outside_sitemap["status"] == "discovered"
    manifest = FG2CohortManifest.load(manifest_path, allow_empty=True)
    assert manifest.payload["blocked_staging_rows"] == []
    assert [row["staging_id"] for row in manifest.payload["discovery_rows"]] == [
        existing_discovered["id"]
    ]


def test_manual_approved_page_seed_in_sitemap_mode_is_not_parsed_as_xml() -> None:
    page_seed = f"{BASE_URL}/catalog/program-one"
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"id": INSTITUTION_ID, "website_url": BASE_URL}
    harvester.profile = {"discovery_mode": "sitemap_bfs"}
    harvester.controlled = True
    harvester.scheduled_cohort = False
    harvester.controlled_seed_urls = [page_seed]
    harvester.approved_lot = object()
    harvester.approved_lot_scope = {page_seed: {"snapshot": {"staging_rows": [], "course_rows": []}}}
    harvester.course_urls = set()
    harvester.check_time_guard = lambda: False
    harvester._can_discover_more = lambda: True
    harvester._load_existing_urls = lambda: asyncio.sleep(0, result=set())
    harvester._is_valid_crawl_url = lambda _url: True
    harvester._mark_controlled_url_examined = lambda _url: True
    harvester._queue_discovered_candidate = lambda _url: {"status": "discovered"}
    harvester._merge_resumable_urls = lambda urls: list(urls)
    harvester._limit_urls = lambda urls: list(urls)

    async def unexpected_sitemap_parse(_session, _seed):
        raise AssertionError("approved page seed must not be parsed as an XML sitemap")

    harvester._fetch_sitemap = unexpected_sitemap_parse

    class NoNetworkSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    with patch.object(harvester_module, "AsyncSession", NoNetworkSession):
        discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [page_seed]


def test_controlled_refresh_records_processed_staging_as_blocked_without_reopening(tmp_path: Path) -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "hardcoded_urls",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "circuit_open": False,
        "seed_urls": [COURSE_URL],
        "exclusion_patterns": [],
    }
    institution = {"id": INSTITUTION_ID, "name": "Synthetic Academy", "slug": "synthetic", "website_url": BASE_URL}
    adapter = SyntheticPipelineAdapter(profile)
    protected = {
        "id": "40000000-0000-0000-0000-000000000098",
        "institution_id": INSTITUTION_ID,
        "url": COURSE_URL,
        "status": "processed",
        "content_hash": "f" * 64,
    }
    adapter.tables["staging_raw"].append(protected)
    preflight = validate_controlled_profile(institution, profile)
    manifest_path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": preflight["profile_sha256"],
                "seed_sha256": preflight["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    with patch.dict(
        os.environ,
        {"GITHUB_RUN_ID": "123456789", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40},
    ), patch.object(harvester_module, "get_db_client", return_value=adapter):
        controlled_institution = dict(
            institution,
            _controlled_profile_sha256=preflight["profile_sha256"],
            _controlled_seed_sha256=preflight["seed_sha256"],
        )
        harvester = UniversalHarvester(
            controlled_institution,
            max_discovered_urls=10,
            controlled=True,
            cohort_manifest=str(manifest_path),
        )

    assert asyncio.run(harvester.discover_courses()) == []
    assert protected["status"] == "processed"
    manifest = FG2CohortManifest.load(manifest_path, allow_empty=True)
    assert manifest.payload["entries"] == []
    assert manifest.payload["blocked_staging_rows"] == [
        {
            "institution_id": INSTITUTION_ID,
            "staging_id": protected["id"],
            "url_sha256": hashlib.sha256(COURSE_URL.encode()).hexdigest(),
            "content_sha256": "f" * 64,
            "status": "processed",
            "reason": "historical_staging_state_protected",
        }
    ]


def test_controlled_sitemap_skips_protected_prefix_before_applying_url_cap(tmp_path: Path) -> None:
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    profile = {
        "institution_id": INSTITUTION_ID,
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": True,
        "circuit_open": False,
        "seed_urls": [sitemap_url],
        "exclusion_patterns": [],
    }
    institution = {
        "id": INSTITUTION_ID,
        "name": "Synthetic Academy",
        "slug": "synthetic",
        "website_url": BASE_URL,
    }
    adapter = SyntheticPipelineAdapter(profile)
    protected_rows = [
        {
            "id": f"40000000-0000-0000-0000-{index:012d}",
            "institution_id": INSTITUTION_ID,
            "url": f"{BASE_URL}/programs/protected-{index}",
            "status": "processed",
            "content_hash": hashlib.sha256(f"protected-{index}".encode()).hexdigest(),
        }
        for index in range(1, 13)
    ]
    candidate_urls = [
        f"{BASE_URL}/programs/new-{index}"
        for index in range(1, 11)
    ]
    adapter.tables["staging_raw"].extend(protected_rows)
    preflight = validate_controlled_profile(institution, profile)
    manifest_path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        manifest_path,
        run_id="123456789",
        run_attempt=1,
        source_sha="a" * 40,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": preflight["profile_sha256"],
                "seed_sha256": preflight["seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{row['url']}</loc></url>" for row in protected_rows)
        + "".join(f"<url><loc>{url}</loc></url>" for url in candidate_urls)
        + "</urlset>"
    )

    class FakeSitemapSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def get(self, url: str, **_kwargs: Any) -> SyntheticResponse:
            assert url == sitemap_url
            return SyntheticResponse(url, sitemap, "application/xml")

    with patch.dict(
        os.environ,
        {"GITHUB_RUN_ID": "123456789", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40},
    ), patch.object(harvester_module, "get_db_client", return_value=adapter), patch.object(
        harvester_module, "AsyncSession", FakeSitemapSession
    ):
        harvester = UniversalHarvester(
            dict(
                institution,
                _controlled_profile_sha256=preflight["profile_sha256"],
                _controlled_seed_sha256=preflight["seed_sha256"],
            ),
            max_discovered_urls=10,
            controlled=True,
            cohort_manifest=str(manifest_path),
            _controlled_transport=SyntheticControlledTransport(),
        )
        queued_urls: list[str] = []

        def queue_candidate(url: str) -> dict[str, Any]:
            queued_urls.append(url)
            return {"id": f"synthetic-{len(queued_urls)}", "url": url, "status": "discovered"}

        harvester._queue_discovered_candidate = queue_candidate
        discovered_urls = asyncio.run(harvester.discover_courses())
        assert set(discovered_urls) == set(candidate_urls)
        assert len(discovered_urls) == len(candidate_urls)

    manifest = FG2CohortManifest.load(manifest_path, allow_empty=True)
    blockers = manifest.payload["blocked_staging_rows"]
    assert len(blockers) == 10
    assert {row["staging_id"] for row in blockers} == {
        row["id"] for row in protected_rows[:10]
    }
    assert queued_urls == candidate_urls
    assert len(harvester._controlled_examined_urls) == 10
    assert [row["status"] for row in protected_rows] == ["processed"] * 12


def test_diagnostic_cli_imports_from_its_documented_entrypoint_without_pythonpath() -> None:
    repository = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, str(repository / "scripts/maintenance/diagnose_institution.py")],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert completed.returncode == 1
    assert "Uso:" in completed.stdout
    assert "ModuleNotFoundError" not in completed.stderr


@pytest.mark.parametrize(
    "stored_course_url",
    [f"{COURSE_URL}/", f"{COURSE_URL}/presentacion/"],
)
def test_course_sync_fg2_course_id_refresh_handles_url_alias_and_retains_manual_override(
    stored_course_url: str,
) -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": True,
        "pipeline_ready": True,
        "website_url": BASE_URL,
    }
    adapter = SyntheticPipelineAdapter(profile)
    adapter.tables["courses"].append(
        {
            "id": COURSE_ID,
            "institution_id": INSTITUTION_ID,
            "url": stored_course_url,
            "name": "Título anterior",
            "last_404_at": None,
            "is_active": True,
        }
    )
    manual_state = {
        "course_id": COURSE_ID,
        "manual_overrides": {"name": "Nombre editorial vigente"},
        "field_sources": {"name": "manual_override"},
        "field_timestamps": {"name": "2026-10-30T12:00:00+00:00"},
        "manual_updated_at": "2026-10-30T12:00:00+00:00",
        "editorial_status": "active",
    }
    adapter.tables["course_editorial_state"].append(manual_state)
    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": COURSE_URL,
        "official_name": "Nombre detectado en refresh",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": 1250.0,
        "requirements": "Requisitos sintéticos",
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
        "ai_summary": "Resumen sintético.",
        "provider_used": "synthetic-provider",
        "is_mock_data": False,
        "status": "pending",
        "metadata": {},
        "_fg2_approved_course_id": COURSE_ID,
    }
    adapter.tables["enriched_programs"].append(enriched)
    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()

    with patch.object(integrity_ping_module, "resolve_public_host", return_value=["93.184.216.34"]):
        assert syncer.sync_to_production(enriched) is True

    quality = next(event for event in adapter.status_events if event["status"] == "quality-updated")
    assert quality["field_sources"]["name"] == "manual_override"
    assert manual_state["manual_overrides"]["name"] == "Nombre editorial vigente"
    refreshed_course = next(row for row in adapter.tables["courses"] if row["id"] == COURSE_ID)
    assert refreshed_course["name"] == "Nombre detectado en refresh"


def test_sync_cohort_carries_the_approved_course_id_to_the_writer() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": True,
        "pipeline_ready": True,
    }
    adapter = SyntheticPipelineAdapter(profile)
    adapter.tables["cleansed_programs"].append(
        {
            "id": CLEANSED_ID,
            "staging_id": STAGING_ID,
            "institution_id": INSTITUTION_ID,
            "url": COURSE_URL,
            "status": "enriched",
        }
    )
    adapter.tables["enriched_programs"].append(
        {
            "id": ENRICHED_ID,
            "cleansed_id": CLEANSED_ID,
            "institution_id": INSTITUTION_ID,
            "url": COURSE_URL,
            "status": "pending",
        }
    )

    class ApprovedCohort:
        staging_ids = [STAGING_ID]
        payload = {
            "entries": [
                {
                    "staging_id": STAGING_ID,
                    "institution_id": INSTITUTION_ID,
                    "course_id": COURSE_ID,
                    "url_sha256": url_sha256(COURSE_URL),
                    "content_sha256": "f" * 64,
                }
            ]
        }

        @staticmethod
        def assert_related_stage_records(records, *, foreign_key, allowed_ids, stage):
            assert all(row[foreign_key] in allowed_ids for row in records), stage

    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()

    records = syncer.get_pending_enriched(cohort_manifest=ApprovedCohort())

    assert len(records) == 1
    assert records[0]["_fg2_approved_course_id"] == COURSE_ID


def test_sync_course_alias_inventory_is_loaded_once_per_worker_run() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": True,
        "pipeline_ready": True,
    }
    adapter = SyntheticPipelineAdapter(profile)
    adapter.tables["courses"].append(
        {
            "id": COURSE_ID,
            "institution_id": INSTITUTION_ID,
            "url": COURSE_URL,
            "is_active": True,
            "last_404_at": None,
        }
    )
    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()

    first = syncer._load_fg2_course_inventory()
    second = syncer._load_fg2_course_inventory()

    assert first is second
    assert len(first) == 1
    assert adapter.select_all_service_calls == ["courses"]

    new_course = {
        "id": "70000000-0000-0000-0000-000000000092",
        "institution_id": INSTITUTION_ID,
        "url": f"{BASE_URL}/programs/new-course",
        "is_active": True,
        "last_404_at": None,
    }
    syncer._remember_fg2_course(new_course)
    assert any(row["id"] == new_course["id"] for row in syncer._load_fg2_course_inventory())
    assert adapter.select_all_service_calls == ["courses"]


@pytest.mark.parametrize(
    ("approved_course_id", "message"),
    [
        (COURSE_ID, "canonical course URL is ambiguous"),
        (None, "approved FG2 new-discovery URL now resolves to a course"),
    ],
)
def test_course_sync_stops_if_a_canonical_alias_appears_after_preflight(
    approved_course_id: str | None, message: str
) -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": True,
        "pipeline_ready": True,
        "website_url": BASE_URL,
    }
    adapter = SyntheticPipelineAdapter(profile)
    adapter.tables["courses"].extend(
        [
            {
                "id": COURSE_ID,
                "institution_id": INSTITUTION_ID,
                "url": f"{COURSE_URL}/",
                "last_404_at": None,
                "is_active": True,
            },
            {
                "id": "70000000-0000-0000-0000-000000000099",
                "institution_id": INSTITUTION_ID,
                "url": f"{BASE_URL}/en/programs/analitica-aplicada",
                "last_404_at": None,
                "is_active": True,
            },
        ]
    )
    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": COURSE_URL,
        "official_name": "Nombre detectado en refresh",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": 1250.0,
        "requirements": "Requisitos sintéticos",
        "graduate_profile": "Analista inicial",
        "degree_type": "Curso",
        "start_date": "2027-04-01",
        "categories": ["Data"],
        "ai_summary": "Resumen sintético.",
        "provider_used": "synthetic-provider",
        "is_mock_data": False,
        "status": "pending",
        "metadata": {},
        "_fg2_approved_course_id": approved_course_id,
    }
    adapter.tables["enriched_programs"].append(enriched)
    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()

    with patch.object(integrity_ping_module, "resolve_public_host", return_value=["93.184.216.34"]):
        with pytest.raises(InvalidControlledRun, match=message):
            syncer.sync_to_production(enriched)

    assert adapter.upsert_calls == []
    assert len(adapter.tables["courses"]) == 2


def test_fg2_new_discovery_does_not_reuse_first_unrelated_course_as_sync_target() -> None:
    profile = {
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": True,
        "pipeline_ready": True,
        "website_url": BASE_URL,
    }
    adapter = SyntheticPipelineAdapter(profile)
    unrelated_course = {
        "id": "70000000-0000-0000-0000-000000000099",
        "institution_id": INSTITUTION_ID,
        "url": f"{BASE_URL}/programs/already-published",
        "name": "Curso publicado sin relación",
        "is_active": True,
        "last_404_at": None,
    }
    adapter.tables["courses"].append(dict(unrelated_course))
    raw_html = "<html><body>synthetic new discovery</body></html>"
    content_sha = hashlib.sha256(raw_html.encode()).hexdigest()
    fresh_url = f"{BASE_URL}/programs/new-discovery"
    adapter.tables["staging_raw"].append({
        "id": STAGING_ID,
        "institution_id": INSTITUTION_ID,
        "url": fresh_url,
        "status": "processed",
        "content_hash": content_sha,
    })
    adapter.tables["cleansed_programs"].append({
        "id": CLEANSED_ID,
        "staging_id": STAGING_ID,
        "institution_id": INSTITUTION_ID,
        "url": fresh_url,
        "status": "enriched",
    })
    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": fresh_url,
        "official_name": "Curso nuevo de descubrimiento",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": 1250.0,
        "requirements": "Requisitos sintéticos",
        "graduate_profile": "Analista inicial",
        "degree_type": "Curso",
        "start_date": "2027-04-01",
        "categories": ["Data"],
        "ai_summary": "Resumen del curso nuevo, con datos sintéticos.",
        "provider_used": "synthetic-provider",
        "is_mock_data": False,
        "status": "pending",
        "metadata": {},
        "_fg2_approved_course_id": None,
        "_fg2_expected_url_sha256": url_sha256(fresh_url),
        "_fg2_expected_raw_url_sha256": url_sha256(fresh_url),
        "_fg2_manifest_staging_id": STAGING_ID,
        "_fg2_manifest_cleansed_id": CLEANSED_ID,
        "_fg2_manifest_content_sha256": content_sha,
    }
    adapter.tables["enriched_programs"].append(dict(enriched))
    with patch.object(sync_vector_module, "get_db_client", return_value=adapter):
        syncer = SyncVectorWorker()

    with patch.object(integrity_ping_module, "resolve_public_host", return_value=["93.184.216.34"]):
        assert syncer.sync_to_production(enriched) is True

    assert len(adapter.upsert_calls) == 1
    assert adapter.upsert_calls[0]["url"] == fresh_url
    assert next(row for row in adapter.tables["courses"] if row["id"] == unrelated_course["id"]) == unrelated_course


def test_paginated_discovery_extracts_only_allowlisted_links(monkeypatch: pytest.MonkeyPatch) -> None:
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
        def __init__(self, **_kwargs):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, **kwargs):
            body = (
                '<a class="program" href="/programs/analitica-aplicada">course</a>'
                '<a class="program" href="https://outside.example/program">outside</a>'
                '<a class="program" href="/programs/brochure.pdf">pdf</a>'
            )
            response = SyntheticStreamingResponse(url, [body.encode()], "text/html")
            response.content = body.encode()
            return response

    monkeypatch.setattr(harvester_module, "validate_public_request_url", synthetic_public_request_binding)
    with patch.object(harvester_module, "AsyncSession", Session):
        discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [COURSE_URL]
    assert len(adapter.tables["staging_raw"]) == 1
    assert adapter.tables["staging_raw"][0]["status"] == "discovered"


def test_paginated_discovery_resumes_discovered_rows_without_reprocessing_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        def __init__(self, **_kwargs):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, **kwargs):
            body = (
                f'<a class="program" href="{discovered_url}">resume</a>'
                f'<a class="program" href="{pending_url}">pending</a>'
                f'<a class="program" href="{new_url}">new</a>'
            )
            response = SyntheticStreamingResponse(url, [body.encode()], "text/html")
            response.content = body.encode()
            return response

    async def no_delay(_seconds):
        return None

    monkeypatch.setattr(harvester_module, "validate_public_request_url", synthetic_public_request_binding)
    with patch.object(harvester_module, "AsyncSession", Session), patch.object(harvester_module.asyncio, "sleep", new=no_delay):
        discovered = asyncio.run(harvester.discover_courses())

    assert discovered == [discovered_url, new_url]
    assert {row["url"] for row in adapter.tables["staging_raw"]} == {discovered_url, pending_url, new_url}
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == discovered_url)["status"] == "discovered"
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == pending_url)["status"] == "pending"
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == new_url)["status"] == "discovered"


def test_catalog_link_discovery_preserves_navigation_and_filters_external_links() -> None:
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

    class Page(SyntheticBrowserPage):
        def __init__(self) -> None:
            super().__init__()
            self.query_count = 0

        async def evaluate(self, script):
            return False if "document.querySelector(\"footer\")" in script else None

        async def query_selector_all(self, _selector):
            self.query_count += 1
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

    expected_url = f"{BASE_URL}/programs/analitica-aplicada"
    assert discovered == [expected_url]
    assert browser.page.closed is True
    assert browser.page.navigated_urls == [BASE_URL]
    assert browser.page.query_count == 1
    assert [row["url"] for row in adapter.tables["staging_raw"]] == [expected_url]
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

    class Page(SyntheticBrowserPage):
        def __init__(self) -> None:
            super().__init__()
            self.query_count = 0

        async def evaluate(self, script):
            return False if 'document.querySelector("footer")' in script else None

        async def query_selector_all(self, _selector):
            self.query_count += 1
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
    assert browser.page.navigated_urls == [catalog_url, BASE_URL]
    assert browser.page.query_count == 2
    assert {row["url"] for row in adapter.tables["staging_raw"]} == {discovered_url, pending_url, new_url}
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == discovered_url)["status"] == "discovered"
    assert next(row for row in adapter.tables["staging_raw"] if row["url"] == pending_url)["status"] == "pending"


def test_paginated_discovery_preserves_and_resumes_results_after_later_page_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        def __init__(self, **_kwargs):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, **kwargs):
            page_num = url.rsplit("=", 1)[-1]
            requests.append(f"{phase['name']}:{page_num}")
            if page_num == "2" and phase["name"] == "partial":
                response = SyntheticStreamingResponse(url, [b""], "text/html")
                response.status_code = 503
                return response
            hrefs = [first_url] if page_num == "1" else [recovered_url]
            body = "".join(f'<a class="program" href="{href}">course</a>' for href in hrefs)
            response = SyntheticStreamingResponse(url, [body.encode()], "text/html")
            response.content = body.encode()
            return response

    async def no_delay(_seconds):
        return None

    monkeypatch.setattr(harvester_module, "validate_public_request_url", synthetic_public_request_binding)
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

    class Page(SyntheticBrowserPage):
        def __init__(self):
            super().__init__()
            self.query_count = 0

        async def evaluate(self, script):
            return False if 'document.querySelector("footer")' in script else None

        async def query_selector_all(self, _selector):
            self.query_count += 1
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
    assert all(page.navigated_urls == [catalog_url] for page in browser.pages)
    assert {row["url"] for row in adapter.tables["staging_raw"]} == {first_url, recovered_url}


def test_profile_regex_safety_scan_rejects_nested_quantifiers_linearly() -> None:
    unsafe_patterns = ["(a+)+", "(a*){1,2}", "(a{1,3})+", "((a+))+"]
    safe_patterns = ["a+", "(?:program|course)+", "[*+]+", r"\(a+\)+"]

    assert all(harvester_module._has_nested_quantified_group(pattern) for pattern in unsafe_patterns)
    assert all(not harvester_module._has_nested_quantified_group(pattern) for pattern in safe_patterns)
    assert all(not UniversalHarvester._is_safe_profile_regex(pattern) for pattern in unsafe_patterns)


def test_profile_regex_search_fails_closed_without_bounded_regex_dependency() -> None:
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"website_url": BASE_URL}
    harvester.exclusions = [("re", "blocked")]
    harvester.profile = None

    with patch.object(harvester_module, "safe_regex", None):
        assert UniversalHarvester._safe_profile_search("blocked", "/blocked") is None
        assert not harvester._is_valid_crawl_url(f"{BASE_URL}/blocked")

        harvester.exclusions = []
        harvester.profile = {"allowed_url_patterns": ["re:program"]}
        assert not harvester._is_valid_crawl_url(f"{BASE_URL}/program")


def test_profile_regex_timeout_fails_closed() -> None:
    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"website_url": BASE_URL}
    harvester.exclusions = [("re", "blocked")]
    harvester.profile = None
    bounded_regex = Mock()
    bounded_regex.IGNORECASE = harvester_module.re.IGNORECASE
    bounded_regex.search.side_effect = TimeoutError("synthetic bounded-regex timeout")

    with patch.object(harvester_module, "safe_regex", bounded_regex):
        assert not harvester._is_valid_crawl_url(f"{BASE_URL}/blocked")

    bounded_regex.search.assert_called_once_with(
        "blocked",
        f"{BASE_URL}/blocked",
        bounded_regex.IGNORECASE,
        timeout=0.05,
    )


if __name__ == "__main__":
    run_pipeline_walk()
