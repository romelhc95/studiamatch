import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HitoGovernanceTests(unittest.TestCase):
    def test_unconfigured_hito_scope_fails_closed(self):
        validator = load_module("validate_hito_close", ROOT / "scripts/maintenance/validate_hito_close.py")
        self.assertFalse(validator.is_allowed_staged_file("scripts/core/anything.py", 2))

    def test_report_uses_single_timestamp(self):
        validator = load_module("validate_hito_report", ROOT / "scripts/maintenance/validate_hito_close.py")
        now = datetime(2026, 7, 18, 10, 11, 12, tzinfo=timezone.utc)
        with patch.object(validator, "staged_scope_hash", return_value="a" * 64):
            report = validator.build_report(1, validator.Gate(), "validator --hito 1", now)
        self.assertIn("2026-07-18T10:11:12+00:00", report)
        self.assertIn(f"`{'a' * 64}`", report)

    def test_scope_hash_binds_narrative_report_references(self):
        validator = load_module("validate_hito_scope_hash", ROOT / "scripts/maintenance/validate_hito_close.py")
        evidence_path = ".context/evidencias/hito_1_informe_cumplimiento.md"
        with patch.object(validator, "git_lines", return_value=[evidence_path]):
            with patch.object(validator, "read_text", return_value="resultado OK hito_1_qa_gate_report_20260718_101010.md"):
                first = validator.staged_scope_hash(1)
            with patch.object(validator, "read_text", return_value="resultado OK hito_1_qa_gate_report_20260719_202020.md"):
                same_link_change = validator.staged_scope_hash(1)
            with patch.object(validator, "read_text", return_value="resultado observado hito_1_qa_gate_report_20260719_202020.md"):
                evidence_change = validator.staged_scope_hash(1)
        self.assertNotEqual(first, same_link_change)
        self.assertNotEqual(first, evidence_change)

    def test_first_report_link_does_not_stale_candidate_hash(self):
        validator = load_module("validate_hito_first_report", ROOT / "scripts/maintenance/validate_hito_close.py")
        evidence_path = ".context/evidencias/hito_1_informe_cumplimiento.md"
        with patch.object(validator, "git_lines", return_value=[evidence_path]):
            with patch.object(validator, "read_text", return_value="resultado OK"):
                before_link = validator.staged_scope_hash(1)
            linked = "resultado OK\n| QA Gate obligatorio | GO | `.context/evidencias/hito_1_qa_gate_report_20260718_101010.md` |"
            with patch.object(validator, "read_text", return_value=linked):
                after_link = validator.staged_scope_hash(1)
        self.assertEqual(before_link, after_link)

    def test_non_link_qa_evidence_remains_bound(self):
        validator = load_module("validate_hito_qa_evidence", ROOT / "scripts/maintenance/validate_hito_close.py")
        evidence_path = ".context/evidencias/hito_1_informe_cumplimiento.md"
        with patch.object(validator, "git_lines", return_value=[evidence_path]):
            with patch.object(validator, "read_text", return_value="QA Gate revisado sin hallazgos"):
                first = validator.staged_scope_hash(1)
            with patch.object(validator, "read_text", return_value="QA Gate observado con hallazgos"):
                changed = validator.staged_scope_hash(1)
        self.assertNotEqual(first, changed)

    def test_staged_deletion_is_represented_in_scope_hash(self):
        validator = load_module("validate_hito_deletion", ROOT / "scripts/maintenance/validate_hito_close.py")
        with patch.object(validator, "git_lines", return_value=["scripts/core/deleted.py"]):
            with patch.object(validator, "run_git", return_value=SimpleNamespace(stdout="")):
                deletion_hash = validator.staged_scope_hash(1)
        with patch.object(validator, "git_lines", return_value=[]):
            empty_hash = validator.staged_scope_hash(1)
        self.assertNotEqual(deletion_hash, empty_hash)

    def test_ca_placeholders_and_unchecked_delivery_fail(self):
        validator = load_module("validate_hito_ca", ROOT / "scripts/maintenance/validate_hito_close.py")
        task = 'cas: "CA1"\n## Matriz CA -> pruebas/evidencia\n| CA1 | Por definir |\n## Resultado\n'
        evidence = "## 5. Matriz De Pruebas Por Criterio De Aceptacion\n| CA1 | prueba | pendiente |\n## 9. Estado Para Entrega\n- [ ] pendiente\n"
        gate = validator.Gate()
        validator.check_ca_execution(gate, task, evidence)
        self.assertGreaterEqual(len(gate.errors), 2)

    def test_task_generator_creates_test_row_per_ca(self):
        creator = load_module("crear_tarea", ROOT / ".context/crear_tarea.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            backlog = Path(temp_dir)
            with patch.object(creator, "BACKLOG_DIR", backlog):
                path = creator.crear_tarea("EST-001", "1", "Gate", hito="Hito 1", cas="CA1, CA2")
                text = path.read_text(encoding="utf-8")
        self.assertIn("| CA1 | Definir antes de ejecutar |", text)
        self.assertIn("| CA2 | Definir antes de ejecutar |", text)

    def test_completar_is_not_an_automatic_bypass(self):
        creator = load_module("crear_tarea_completion", ROOT / ".context/crear_tarea.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(creator, "BACKLOG_DIR", Path(temp_dir)):
                self.assertIsNone(creator.completar_tarea("TAREA-001"))


if __name__ == "__main__":
    unittest.main()
