import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Keep these unit tests runnable in the minimal development container without
# installing packages or touching package registries. Production dependencies
# are used normally whenever they are available.
if importlib.util.find_spec("dotenv") is None:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: False
    sys.modules["dotenv"] = dotenv_stub

if importlib.util.find_spec("requests") is None:
    requests_stub = types.ModuleType("requests")

    class _RequestError(Exception):
        pass

    requests_stub.exceptions = types.SimpleNamespace(
        ConnectionError=_RequestError,
        DNSResolutionError=_RequestError,
        Timeout=_RequestError,
    )
    sys.modules["requests"] = requests_stub

if importlib.util.find_spec("bs4") is None:
    bs4_stub = types.ModuleType("bs4")
    bs4_stub.BeautifulSoup = object
    sys.modules["bs4"] = bs4_stub

if importlib.util.find_spec("PyPDF2") is None:
    pypdf_stub = types.ModuleType("PyPDF2")
    pypdf_stub.PdfReader = object
    sys.modules["PyPDF2"] = pypdf_stub

from scripts.core import cleansing_worker, enrichment_worker, sync_vector_worker


class FakeCleansingDB:
    def __init__(
        self,
        rpc_result=None,
        rpc_error=None,
        upsert_result=None,
        upsert_error=None,
        patch_error=None,
    ):
        self.rpc_result = [{"id": "cleansed-id"}] if rpc_result is None else rpc_result
        self.rpc_error = rpc_error
        self.upsert_result = [{"id": "cleansed-id"}] if upsert_result is None else upsert_result
        self.upsert_error = upsert_error
        self.patch_error = patch_error
        self.rpc_calls = []
        self.upserts = []
        self.patches = []

    def rpc_raise(self, function_name, params=None):
        self.rpc_calls.append((function_name, params))
        if self.rpc_error:
            raise self.rpc_error
        return self.rpc_result

    def upsert(self, table, data, on_conflict=None):
        self.upserts.append((table, data, on_conflict))
        if self.upsert_error:
            raise self.upsert_error
        return self.upsert_result

    def patch_raise(self, table, filters=None, data=None):
        self.patches.append((table, filters, data))
        if self.patch_error:
            raise self.patch_error
        return {"status": "success"}


def _cleansing_record():
    return {
        "id": "staging-id",
        "institution_id": "institution-id",
        "url": "https://example.edu/programa-datos",
        "raw_name": "Programa Profesional de Datos",
        "raw_description": "Programa profesional con una descripción suficientemente extensa.",
        "raw_html": "<html><body><h1>Programa Profesional de Datos</h1></body></html>",
    }


def _cleansing_worker(database):
    worker = cleansing_worker.CleansingWorker.__new__(cleansing_worker.CleansingWorker)
    cleansing_worker.aggressive_html_clean = lambda raw_html: "Contenido limpio"
    worker.db = database
    worker.profiles = []
    worker.exclusions = []
    worker.default_noise_name_patterns = []
    worker.hub_patterns = []
    worker.is_invalid_course = lambda *args, **kwargs: None
    worker.is_hub_page = lambda url: False
    worker._get_profile_for_inst = lambda inst_id: {}
    worker._extract_price_with_regex = lambda text, profile: (None, "consultar")
    return worker


class CleansingWorkerTests(unittest.TestCase):
    def test_rpc_success_returns_persisted_count_without_fallback(self):
        database = FakeCleansingDB()
        worker = _cleansing_worker(database)

        self.assertEqual(worker.process_batch([_cleansing_record()]), 1)
        self.assertEqual(database.rpc_calls[0][0], "atomic_cleansing_promote")
        self.assertEqual(database.upserts, [])
        self.assertEqual(database.patches, [])

    def test_falsey_rpc_uses_proven_fallback(self):
        database = FakeCleansingDB(rpc_result=[])
        worker = _cleansing_worker(database)

        self.assertEqual(worker.process_batch([_cleansing_record()]), 1)
        self.assertEqual(database.upserts[0][0], "cleansed_programs")
        self.assertEqual(database.upserts[0][2], "url")
        self.assertEqual(database.patches[0][0], "staging_raw")
        self.assertEqual(database.patches[0][2]["status"], "processed")

    def test_rpc_exception_fails_closed_without_fallback(self):
        database = FakeCleansingDB(rpc_error=RuntimeError("rpc unavailable"))
        worker = _cleansing_worker(database)

        with self.assertRaisesRegex(RuntimeError, "rpc unavailable"):
            worker.process_batch([_cleansing_record()])
        self.assertEqual(database.upserts, [])

    def test_fallback_failure_fails_closed(self):
        failures = {
            "upsert_exception": {"upsert_error": RuntimeError("upsert failed")},
            "upsert_falsey": {"upsert_result": []},
            "patch_exception": {"patch_error": RuntimeError("patch failed")},
        }
        for failure, failure_kwargs in failures.items():
            with self.subTest(failure=failure):
                database = FakeCleansingDB(rpc_result=[], **failure_kwargs)
                worker = _cleansing_worker(database)

                with self.assertRaises(RuntimeError):
                    worker.process_batch([_cleansing_record()])


class FakeEnrichmentDB:
    def __init__(
        self,
        rpc_result=None,
        rpc_error=None,
        upsert_result=None,
        upsert_error=None,
        patch_error=None,
    ):
        self.rpc_result = [{"id": "enriched-id"}] if rpc_result is None else rpc_result
        self.rpc_error = rpc_error
        self.upsert_result = [{"id": "enriched-id"}] if upsert_result is None else upsert_result
        self.upsert_error = upsert_error
        self.patch_error = patch_error
        self.rpc_calls = []
        self.upserts = []
        self.patches = []

    def select(self, table, filters=None, columns="*", limit=None, order=None):
        return []

    def rpc_raise(self, function_name, params=None):
        self.rpc_calls.append((function_name, params))
        if self.rpc_error:
            raise self.rpc_error
        return self.rpc_result

    def upsert(self, table, data, on_conflict=None):
        self.upserts.append((table, data, on_conflict))
        if self.upsert_error:
            raise self.upsert_error
        return self.upsert_result

    def patch_raise(self, table, filters=None, data=None):
        self.patches.append((table, filters, data))
        if self.patch_error:
            raise self.patch_error
        return {"status": "success"}


def _cleansed_record():
    return {
        "id": "cleansed-id",
        "staging_id": "staging-id",
        "institution_id": "institution-id",
        "url": "https://example.edu/programa-datos",
        "clean_name": "Programa Profesional de Datos",
        "clean_description": "Programa profesional con una descripción suficientemente extensa.",
        "metadata": {},
    }


def _enrichment_worker(database):
    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = database
    brochure_url = "https://example.edu/programa-datos.pdf"
    worker._fetch_sr_enrichment_data = lambda *args, **kwargs: (
        {},
        {
            "brochure_url": brochure_url,
            "extraction_trace": [{"field": "duration_text", "source": "css:.duration"}],
        },
        {"program_family": "analytics"},
    )
    worker._call_llm_for_pillars = lambda *args, **kwargs: (
        {
            "official_name": "Programa Profesional de Datos",
            "duration_text": "6 meses",
            "duration_months": 6,
            "total_cost_est": 1200,
            "requirements": ["Experiencia básica"],
            "graduate_profile": "Analista",
            "curriculum_summary": {"pilares": ["Datos"]},
            "modality": "Remoto",
            "primary_campus": "Lima",
            "degree_type": "Curso",
            "start_date": None,
            "categories": [],
            "difficulty_level": "Intermedio",
            "ai_summary": "Resumen",
        },
        "test-provider",
    )
    return worker


class EnrichmentWorkerTests(unittest.TestCase):
    def test_rpc_success_returns_true_without_fallback(self):
        database = FakeEnrichmentDB()
        worker = _enrichment_worker(database)

        self.assertIs(worker.enrich_record(_cleansed_record()), True)
        self.assertEqual(database.rpc_calls[0][0], "atomic_enrichment_promote")
        self.assertEqual(database.upserts, [])
        self.assertEqual(database.patches, [])

    def test_falsey_rpc_preserves_metadata_and_brochure_in_fallback(self):
        database = FakeEnrichmentDB(rpc_result=[])
        worker = _enrichment_worker(database)

        self.assertIs(worker.enrich_record(_cleansed_record()), True)
        rpc_row = database.rpc_calls[0][1]["p_enriched_data"][0]
        fallback_row = database.upserts[0][1]
        self.assertEqual(rpc_row["brochure_url"], fallback_row["brochure_url"])
        expected_metadata = {
            "extraction_trace": [
                {"field": "duration_text", "source": "css:.duration"}
            ],
            "program_family": "analytics",
        }
        self.assertEqual(rpc_row["metadata"], expected_metadata)
        self.assertEqual(fallback_row["metadata"], expected_metadata)
        self.assertEqual(database.patches[0][2], {"status": "enriched"})

    def test_empty_metadata_is_an_object_in_rpc_and_fallback(self):
        database = FakeEnrichmentDB(rpc_result=[])
        worker = _enrichment_worker(database)
        worker._fetch_sr_enrichment_data = lambda *args, **kwargs: ({}, {}, {})

        self.assertIs(worker.enrich_record(_cleansed_record()), True)
        rpc_row = database.rpc_calls[0][1]["p_enriched_data"][0]
        fallback_row = database.upserts[0][1]
        self.assertEqual(rpc_row["metadata"], {})
        self.assertEqual(fallback_row["metadata"], {})

    def test_rpc_exception_fails_closed_without_fallback(self):
        database = FakeEnrichmentDB(rpc_error=RuntimeError("rpc unavailable"))
        worker = _enrichment_worker(database)

        with self.assertRaisesRegex(RuntimeError, "rpc unavailable"):
            worker.enrich_record(_cleansed_record())
        self.assertEqual(database.upserts, [])

    def test_fallback_exception_fails_closed(self):
        database = FakeEnrichmentDB(
            rpc_result=[], patch_error=RuntimeError("status patch failed")
        )
        worker = _enrichment_worker(database)

        with self.assertRaisesRegex(RuntimeError, "status patch failed"):
            worker.enrich_record(_cleansed_record())
        self.assertEqual(len(database.upserts), 1)

    def test_count_includes_only_proven_successes(self):
        class FakeWorker:
            def enrich_record(self, record):
                return record["persisted"]

        successful = enrichment_worker.process_enrichment_records(
            FakeWorker(),
            [
                {"id": "one", "persisted": True},
                {"id": "two", "persisted": True},
            ],
        )
        self.assertEqual(successful, 2)

        with self.assertRaisesRegex(RuntimeError, "not proven"):
            enrichment_worker.process_enrichment_records(
                FakeWorker(), [{"id": "failed", "persisted": False}]
            )


class FakeSyncDB:
    def __init__(self):
        self.upserts = []
        self.patches = []

    def select_service_raise(self, table, filters=None, columns="*", limit=None, order=None):
        return [{
            "id": "course-id",
            "is_active": True,
            "publication_status": "publicado",
            "manual_updated_at": None,
        }]

    def upsert(self, table, data, on_conflict=None):
        self.upserts.append((table, data, on_conflict))
        return [{"id": "course-id"}]

    def patch_raise(self, table, filters=None, data=None):
        self.patches.append((table, filters, data))
        return {"status": "success"}


def _sync_worker(database):
    worker = sync_vector_worker.SyncVectorWorker.__new__(sync_vector_worker.SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {"institution-id"}
    worker._get_noise_patterns_for_inst = lambda inst_id: []
    worker._get_profile = lambda inst_id: {
        "production_enabled": True,
        "field_defaults": {},
        "section_mode_map": {},
    }
    return worker


class SyncVectorWorkerTests(unittest.TestCase):
    def test_mock_does_not_overwrite_existing_published_course(self):
        database = FakeSyncDB()
        worker = _sync_worker(database)
        metadata = {"provider": "mock", "quality": "unverified"}
        record = {
            "id": "enriched-id",
            "institution_id": "institution-id",
            "official_name": "Programa Profesional de Datos",
            "url": "https://example.edu/programa-datos",
            "categories": [],
            "is_mock_data": True,
            "metadata": metadata,
        }

        with patch.object(
            sync_vector_worker, "parse_start_date", return_value=(None, False)
        ), patch.object(
            sync_vector_worker, "duration_months_to_hours", return_value=None
        ), patch.object(
            sync_vector_worker, "infer_seniority", return_value="Junior"
        ):
            self.assertIs(worker.sync_to_production(record), True)

        self.assertEqual(database.upserts, [])
        self.assertEqual(
            database.patches,
            [("enriched_programs", "id=eq.enriched-id", {"status": "synced"})],
        )
        self.assertEqual(record["metadata"], metadata)


if __name__ == "__main__":
    unittest.main()
