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

    def test_f12_cannot_be_active_before_main_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "estado_del_proyecto.md"
            text = path.read_text(encoding="utf-8").replace("Subfase tecnica activa: `F10.11`", "Subfase tecnica activa: `F12.1`")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("EXECUTION_PHASE_MISMATCH") for error in validator.validate(root)))

    def test_active_wp_requires_matching_active_work_package(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "estado_del_proyecto.md"
            text = path.read_text(encoding="utf-8").replace("Work package activo: `WP-H2-001`", "Work package activo: `NONE`")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("UNAPPROVED_ACTIVE_WP") for error in validator.validate(root)))

    def test_plan_active_work_package_drift_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "operaciones" / "plan_maestro_sprint1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("active_work_package = WP-H2-001", "active_work_package = NONE")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("UNAPPROVED_ACTIVE_WP") for error in validator.validate(root)))

    def test_active_wp_requires_activation_metadata(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-H2-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data.pop("activated_at", None)
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("ACTIVATION_METADATA_REQUIRED") for error in validator.validate(root)))

    def test_inactive_wp_status_fails_after_activation(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-H2-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["status"] = "APPROVED"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("UNAPPROVED_ACTIVE_WP") for error in validator.validate(root)))

    def test_task_or_matrix_active_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            task = root / ".context" / "backlog_tareas" / "req_est_001_sprint_1" / "tarea_002_hito_2.md"
            task.write_text(task.read_text(encoding="utf-8").replace("BLOCKED_PENDING_OBSIDIAN_MAIN", "ACTIVE"), encoding="utf-8")
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
            text = path.read_text(encoding="utf-8").replace("Apruebo WP-GOV-CI-001", "Apruebo WP-H2-001", 1)
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

    def test_next_gate_must_prepare_gov_ci_r2(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            for path in (root / ".context" / "estado_del_proyecto.md", root / ".context" / "operaciones" / "plan_maestro_sprint1_h2_h5.md"):
                text = path.read_text(encoding="utf-8").replace("PREPARE_WP_GOV_CI_001_R2_APPROVAL", "EXECUTE_F12_1_LOCAL_CA2_R1")
                path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("NEXT_GATE_MISMATCH") for error in validator.validate(root)))

    def test_stale_gov_arch_gate_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "estado_del_proyecto.md"
            text = path.read_text(encoding="utf-8").replace("PREPARE_WP_GOV_CI_001_R2_APPROVAL", "PREPARE_WP_GOV_ARCH_R2_APPROVAL")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("NEXT_GATE_MISMATCH:stale GOV ARCH") for error in validator.validate(root)))

    def test_gov_infra_must_be_in_canonical_authority(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "estado_del_proyecto.md"
            text = path.read_text(encoding="utf-8").replace("WP-GOV-INFRA-001", "WP-GOV-INFRA-X")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("GOV_INFRA_WP_INVALID") for error in validator.validate(root)))

    def test_legacy_phase_prompt_as_authority_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "seguimiento" / "seguimiento_sprint_1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("Apruebo WP-GOV-CI-001", "Ejecuta las tareas pendientes de la Fase F12.1\nApruebo WP-GOV-CI-001")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("LEGACY_PHASE_PROMPT_AUTHORITY_DRIFT") for error in validator.validate(root)))

    def test_gov_ci_prompt_digest_required(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "seguimiento" / "seguimiento_sprint_1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("Apruebo WP-GOV-CI-001 de TASK-GOV-CI-001", "Apruebo WP-GOV-ARCH-001 de TASK-GOV-ARCH-001")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("NEXT_GATE_MISMATCH:GOV CI") for error in validator.validate(root)))

    def test_canonical_architecture_docs_missing_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            (root / ".context" / "arquitectura_pipeline.md").unlink()
            self.assertTrue(any(error.startswith("ARCHITECTURE_CANONICAL_MISSING") for error in validator.validate(root)))

    def test_obsidian_completed_before_main_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "estado_del_proyecto.md"
            text = path.read_text(encoding="utf-8").replace("DESARROLLO_MERGED_PENDING_HOMOLOGATION", "COMPLETED_OBSIDIAN_CONTEXT_GRAPH")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("OBSIDIAN_STAGE_MISMATCH") for error in validator.validate(root)))

    def test_canonical_evidence_missing_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "evidencias_cliente" / "req_est_001_sprint_1" / "evidencia_hito_002.md"
            text = path.read_text(encoding="utf-8").replace("Estado: `TEMPLATE_ONLY`. No acredita PASS funcional.", "Estado: `PASS`")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("EVIDENCE_STATUS_MISMATCH") for error in validator.validate(root)))

    def test_legacy_release_flow_as_authority_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "operaciones" / "flujo_release_minimo.md"
            text = path.read_text(encoding="utf-8").replace("SUPERSEDED_HISTORY", "ACTIVE")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("LEGACY_RELEASE_FLOW_AUTHORITY_DRIFT") for error in validator.validate(root)))

    def test_baseline_document_drift_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-H2-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["baseline"]["desarrollo_tree"] = "0000000000000000000000000000000000000000"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("BASELINE_DOCUMENT_DRIFT") for error in validator.validate(root)))

    def test_gov_hom_baseline_drift_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-GOV-HOM-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["baseline"]["candidate_tree"] = "0000000000000000000000000000000000000000"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("GOV_HOM_WP_INVALID:baseline") for error in validator.validate(root)))

    def test_gov_ci_baseline_drift_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-GOV-CI-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["baseline"]["candidate_tree"] = "0000000000000000000000000000000000000000"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("GOV_CI_WP_INVALID:baseline") for error in validator.validate(root)))

    def test_grouped_r3_grants_fail(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-GOV-HOM-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["homologation_grants"] = [{"id": "R3-GOV-HOM-001-O2-O5", "status": "TEMPLATE_ONLY_NOT_GRANTED", "single_use": True}]
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("GOV_HOM_GRANTS_INVALID") for error in validator.validate(root)))

    def test_missing_closure_predicate_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "work_packages" / "WP-GOV-HOM-001.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["closure_predicate"] = ["manual close"]
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("GOV_HOM_CLOSURE_PREDICATE_REQUIRED") for error in validator.validate(root)))

    def test_h2_started_prematurely_fails(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo_context(Path(tmp))
            path = root / ".context" / "seguimiento" / "seguimiento_sprint_1_h2_h5.md"
            text = path.read_text(encoding="utf-8").replace("`H2-CA2` | `BLOCKED_PENDING_HOMOLOGATION_AND_REBASE`", "`H2-CA2` | `ACTIVE`")
            path.write_text(text, encoding="utf-8")
            self.assertTrue(any(error.startswith("PREMATURE_ACCEPTANCE") for error in validator.validate(root)))

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
