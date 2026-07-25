import ast
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "scripts" / "core" / "enrichment_worker.py"


def _load_enrichment_worker():
    logger = types.SimpleNamespace(
        debug=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
    )

    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: False

    requests_stub = types.ModuleType("requests")

    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object

    shared_stub = types.ModuleType("shared")
    shared_stub.__path__ = []

    utils_stub = types.ModuleType("shared.utils")
    utils_stub.infer_course_type = lambda *args, **kwargs: None
    utils_stub.standardize_mode = lambda value: value
    utils_stub.standardize_category = lambda value: value
    utils_stub.setup_lima_logging = lambda name: logger
    utils_stub.TimeGuard = object
    utils_stub.LLMProvider = object
    utils_stub.ProviderOrchestrator = object

    db_client_module = "shared." + "db_client"
    db_client_stub = types.ModuleType(db_client_module)
    setattr(db_client_stub, "get_" + "db_client", lambda: None)

    stubs = {
        "dotenv": dotenv_stub,
        "openai": openai_stub,
        "requests": requests_stub,
        "shared": shared_stub,
        "shared.utils": utils_stub,
        db_client_module: db_client_stub,
    }
    module_name = "_fase09_enrichment_worker"
    spec = importlib.util.spec_from_file_location(module_name, WORKER_PATH)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


class RecordingWorker:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def enrich_record(self, record):
        self.calls.append(record["id"])
        if self.failure is not None:
            raise self.failure
        return True


class EnrichmentSessionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_enrichment_worker()

    def test_worker_loop_has_no_legacy_three_attempt_bookkeeping(self):
        source = WORKER_PATH.read_text(encoding="utf-8")
        worker_loop = source[source.index('if __name__ == "__main__":'):]
        loop_tree = ast.parse(worker_loop)
        names = {
            node.id for node in ast.walk(loop_tree) if isinstance(node, ast.Name)
        }

        self.assertTrue(
            {"attempted_counts", "current_attempts", "max_attempts"}.isdisjoint(names)
        )
        normalized_loop = worker_loop.casefold()
        self.assertNotIn("reintent", normalized_loop)
        self.assertNotIn("retrying", normalized_loop)
        self.assertNotRegex(
            normalized_loop, r"\b(?:3|tres)\s+(?:intentos?|attempts?)\b"
        )
        session_calls = [
            node
            for node in ast.walk(loop_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "process_enrichment_records"
            and len(node.args) == 3
            and isinstance(node.args[2], ast.Name)
            and node.args[2].id == "attempted_ids"
        ]
        self.assertEqual(len(session_calls), 1)

    def test_duplicate_ids_are_attempted_at_most_once_per_session(self):
        worker = RecordingWorker()
        attempted_ids = set()
        records = [{"id": "duplicate"}, {"id": "duplicate"}]

        first_count = self.module.process_enrichment_records(
            worker, records, attempted_ids
        )
        second_count = self.module.process_enrichment_records(
            worker, [{"id": "duplicate"}], attempted_ids
        )

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 0)
        self.assertEqual(worker.calls, ["duplicate"])

    def test_persistence_exception_aborts_immediately_without_counting(self):
        error = RuntimeError("persistence unavailable")
        worker = RecordingWorker(failure=error)
        total_processed = 0

        with self.assertRaisesRegex(RuntimeError, "persistence unavailable"):
            total_processed += self.module.process_enrichment_records(
                worker,
                [{"id": "failed"}, {"id": "must-not-run"}],
                set(),
            )

        self.assertEqual(total_processed, 0)
        self.assertEqual(worker.calls, ["failed"])

    def test_successful_record_counts_once(self):
        worker = RecordingWorker()

        successful = self.module.process_enrichment_records(
            worker, [{"id": "successful"}], set()
        )

        self.assertEqual(successful, 1)
        self.assertEqual(worker.calls, ["successful"])


if __name__ == "__main__":
    unittest.main()
