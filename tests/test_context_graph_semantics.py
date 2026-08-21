import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "security" / "validate_context_graph.py"
    spec = importlib.util.spec_from_file_location("validate_context_graph", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_repo_context(tmp_path: Path):
    target = tmp_path / "repo"
    shutil.copytree(ROOT / ".context", target / ".context")
    shutil.copytree(ROOT / "scripts", target / "scripts")
    return target


class ContextGraphSemanticsTests(unittest.TestCase):
    def test_context_graph_validates_current_state(self):
        validator = load_validator()
        self.assertEqual(validator.validate(ROOT), [])

    def test_graph_id_mismatch_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "estado_del_proyecto.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("[HITO-002](hitos/hito_002.md)", "[HITO-001](hitos/hito_001.md)"), encoding="utf-8")
            self.assertTrue(any(error.startswith("GRAPH_ID_MISMATCH") for error in validator.validate(root)))

    def test_criteria_set_mismatch_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "matrices" / "matriz_hito_002.md"
            path.write_text(path.read_text(encoding="utf-8").replace("H2-CA3", "H2-CAX"), encoding="utf-8")
            self.assertTrue(any(error.startswith("CRITERIA_SET_MISMATCH") for error in validator.validate(root)))

    def test_missing_state_lifecycle_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "estado_del_proyecto.md"
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("- Lifecycle stage:")]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertTrue(any(error.startswith("LIFECYCLE_MISMATCH:state missing Lifecycle stage") for error in validator.validate(root)))

    def test_unapproved_active_wp_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-H2-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["status"] = "ACTIVE"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("UNAPPROVED_ACTIVE_WP") for error in validator.validate(root)))

    def test_task_or_matrix_active_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            task = root / ".context" / "backlog_tareas" / "req_est_001_sprint_1" / "tarea_002_hito_2.md"
            task.write_text(task.read_text(encoding="utf-8").replace("PLANNED_NOT_ACTIVE", "ACTIVE"), encoding="utf-8")
            self.assertTrue(any(error.startswith("LIFECYCLE_MISMATCH") for error in validator.validate(root)))

    def test_homologation_stale_status_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "operaciones" / "plan_maestro_sprint1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("O3 = COMPLETED", "O3 = BLOCKED")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("HOMOLOGATION_GATE_STALE") for error in validator.validate(root)))

    def test_o1_stale_status_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "operaciones" / "plan_maestro_sprint1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("O1 = COMPLETED", "O1 = PENDING")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("HOMOLOGATION_GATE_STALE") for error in validator.validate(root)))

    def test_first_h2_prompt_cannot_grant_r2(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "seguimiento" / "seguimiento_sprint_1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("ejecutar solo R1 aprobado", "ejecutar solo R1/R2 permitido")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("NEXT_GATE_MISMATCH") for error in validator.validate(root)))

    def test_first_h2_prompt_must_deny_supabase_free(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "seguimiento" / "seguimiento_sprint_1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("Supabase Free, ", "")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("NEXT_GATE_MISMATCH") for error in validator.validate(root)))

    def test_baseline_document_drift_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-H2-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["baseline"]["desarrollo_tree"] = "0000000000000000000000000000000000000000"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("BASELINE_DOCUMENT_DRIFT") for error in validator.validate(root)))

    def test_approval_target_drift_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-H2-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["approval_target_gate_status"] = "APPROVED_R2"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("APPROVAL_TARGET_INVALID") for error in validator.validate(root)))


if __name__ == "__main__":
    unittest.main()
