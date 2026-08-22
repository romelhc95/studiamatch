import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / ".context" / "work_packages"


def load_validator():
    path = ROOT / "scripts" / "security" / "validate_work_package.py"
    spec = importlib.util.spec_from_file_location("validate_work_package", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_h2():
    return json.loads((MANIFEST_DIR / "WP-H2-001.json").read_text(encoding="utf-8"))


def proposed_h2():
    data = load_h2()
    data.update({"status": "PROPOSED", "lifecycle_stage": "AWAITING_DIGEST", "gate_status": "READY_FOR_DIGEST_APPROVAL", "implementation_status": "PLANNED_NOT_ACTIVE"})
    for key in ("approval_digest", "approved_by", "approved_at", "approval_reference", "approved_level", "approved_candidate_commit", "approval_evidence_sha256", "activated_at"):
        data.pop(key, None)
    return data


def approved_h2():
    data = load_h2()
    data.update({"status": "APPROVED", "lifecycle_stage": "APPROVED_NOT_ACTIVE", "gate_status": "APPROVED_R1", "implementation_status": "PLANNED_NOT_ACTIVE"})
    data.pop("activated_at", None)
    return data


class WorkPackageManifestTests(unittest.TestCase):
    def test_sprint1_work_packages_validate(self):
        validator = load_validator()
        manifests = sorted(MANIFEST_DIR.glob("WP-*.json"))
        self.assertEqual([path.stem for path in manifests], ["WP-GOV-ARCH-001", "WP-GOV-CI-001", "WP-GOV-CI-002", "WP-GOV-HOM-001", "WP-GOV-INFRA-001", "WP-GOV-OBS-001", "WP-H2-001", "WP-H3-001", "WP-H4-001", "WP-H5-001"])
        for path in manifests:
            self.assertEqual(validator.validate_manifest(path, root=ROOT), [])

    def test_h2_manifest_rebased_to_homologated_tree(self):
        data = load_h2()
        self.assertEqual(data["task_id"], "TASK-H2-001")
        self.assertEqual(data["phase_trace"], "F10.11")
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["lifecycle_stage"], "ACTIVE")
        self.assertEqual(data["gate_status"], "APPROVED_R1")
        self.assertEqual(data["approval_digest"], data["candidate_digest"])
        self.assertEqual(data["approved_level"], "R1")
        self.assertEqual(data["approved_candidate_commit"], "c8e4596b153c10721ed335369863a07154eb2b43")
        self.assertEqual(data["activated_at"], "2026-08-21T22:52:20Z")
        self.assertEqual(data["approval_target_lifecycle_stage"], "APPROVED_NOT_ACTIVE")
        self.assertEqual(data["approval_target_gate_status"], "APPROVED_R1")
        self.assertEqual(data["approval_target_level"], "R1")
        self.assertEqual(data["criteria_contract"], ["H2-CA2", "H2-CA3"])
        self.assertEqual(data["implementation_status"], "BLOCKED_PENDING_OBSIDIAN_MAIN")
        self.assertEqual(data["criteria_status"], {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"})
        self.assertEqual(data["environment_scope"], ["local", "development"])
        self.assertIn("supabase-free", data["denied_without_jit"])
        self.assertIn("certification", data["denied_without_jit"])

    def test_proposed_manifest_cannot_include_approval_fields(self):
        validator = load_validator()
        data = proposed_h2()
        data["approval_digest"] = data["candidate_digest"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("WP_PROPOSED_APPROVAL_FIELDS") for error in errors))

    def test_proposed_manifest_cannot_include_approved_level(self):
        validator = load_validator()
        data = proposed_h2()
        data["approved_level"] = "R1"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("WP_PROPOSED_APPROVAL_FIELDS") for error in errors))

    def test_h2_manifest_gate_and_acceptance_are_required(self):
        validator = load_validator()
        for field in ("gate_status", "acceptance_status"):
            data = load_h2()
            data.pop(field)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "WP-H2-001.json"
                path.write_text(json.dumps(data), encoding="utf-8")
                errors = validator.validate_manifest(path, root=ROOT)
            self.assertTrue(any(error.startswith("LIFECYCLE_MISMATCH") for error in errors), field)

    def test_h2_approval_targets_are_required_and_r1_only(self):
        validator = load_validator()
        for field in ("approval_target_lifecycle_stage", "approval_target_gate_status", "approval_target_level"):
            data = load_h2()
            data.pop(field)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "WP-H2-001.json"
                path.write_text(json.dumps(data), encoding="utf-8")
                errors = validator.validate_manifest(path, root=ROOT)
            self.assertTrue(any(error.startswith("WP_SIGNED_FIELDS_MISSING") or error.startswith("APPROVAL_TARGET_INVALID") for error in errors), field)
        data = proposed_h2()
        data["approval_target_level"] = "R2"
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("APPROVAL_TARGET_INVALID") for error in errors))

    def test_unknown_top_level_field_fails_for_h2_schema(self):
        validator = load_validator()
        data = proposed_h2()
        data["unexpected"] = "value"
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("WP_UNKNOWN_FIELDS") for error in errors))

    def test_approved_requires_metadata_and_matching_digest(self):
        validator = load_validator()
        data = proposed_h2()
        data["status"] = "APPROVED"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
            self.assertTrue(any(error.startswith("APPROVAL_METADATA_REQUIRED") for error in errors))
            data.update({
                "lifecycle_stage": "APPROVED_NOT_ACTIVE",
                "gate_status": "APPROVED_R1",
                "approval_digest": data["candidate_digest"],
                "approved_by": "human-reviewer",
                "approved_at": "2026-08-21T12:00:00Z",
                "approval_reference": "manual-session",
                "approved_level": "R1",
                "approved_candidate_commit": "c8e4596b153c10721ed335369863a07154eb2b43",
                "approval_evidence_sha256": "a" * 64,
            })
            path.write_text(json.dumps(data), encoding="utf-8")
            approval_errors = [error for error in validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT) if error.startswith("APPROVAL")]
        self.assertEqual(approval_errors, [])

    def test_active_requires_activation_metadata(self):
        validator = load_validator()
        data = approved_h2()
        data.update({"status": "ACTIVE", "lifecycle_stage": "ACTIVE"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("ACTIVATION_METADATA_REQUIRED") for error in errors))

    def test_expired_or_non_timestamp_expiry_fails(self):
        validator = load_validator()
        data = load_h2()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            data["expires_at"] = "never"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("WP_EXPIRES_FORMAT") for error in validator.validate_manifest(path, root=ROOT)))
            data["expires_at"] = "2020-01-01T00:00:00Z"
            data["candidate_digest"] = validator.compute_digest(data)
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any(error.startswith("WP_EXPIRED") for error in validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT)))

    def test_digest_changes_when_baseline_changes(self):
        validator = load_validator()
        data = load_h2()
        original = data["candidate_digest"]
        data["baseline"]["desarrollo_commit"] = "0000000000000000000000000000000000000000"
        self.assertNotEqual(validator.compute_digest(data), original)

    def test_target_changes_affect_digest_but_runtime_does_not(self):
        validator = load_validator()
        data = proposed_h2()
        original = data["candidate_digest"]
        data["approval_target_gate_status"] = "APPROVED_R2"
        self.assertNotEqual(validator.compute_digest(data), original)
        data = proposed_h2()
        data["metrics"]["last_validation_at"] = "2026-08-21T12:00:00Z"
        self.assertEqual(validator.compute_digest(data), original)

    def test_approval_envelope_preserves_canonical_payload(self):
        validator = load_validator()
        data = proposed_h2()
        before = validator.canonical_payload(data)
        data.update({
            "status": "APPROVED",
            "lifecycle_stage": "APPROVED_NOT_ACTIVE",
            "gate_status": "APPROVED_R1",
            "approval_digest": data["candidate_digest"],
            "approved_by": "human-reviewer",
            "approved_at": "2026-08-21T12:00:00Z",
            "approval_reference": "manual-session",
            "approved_level": "R1",
            "approved_candidate_commit": "c8e4596b153c10721ed335369863a07154eb2b43",
            "approval_evidence_sha256": "a" * 64,
        })
        self.assertEqual(validator.canonical_payload(data), before)
        self.assertEqual(validator.compute_digest(data), data["candidate_digest"])

    def test_approved_manifest_rejects_invalid_candidate_commit_or_evidence(self):
        validator = load_validator()
        cases = (
            ("approved_candidate_commit", "0" * 40, "APPROVAL_CANDIDATE_COMMIT_MISMATCH"),
            ("approved_candidate_commit", "not-a-commit", "APPROVAL_CANDIDATE_COMMIT_INVALID"),
            ("approval_evidence_sha256", "not-a-sha", "APPROVAL_EVIDENCE_INVALID"),
        )
        for field, value, prefix in cases:
            data = load_h2()
            data[field] = value
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "WP-H2-001.json"
                path.write_text(json.dumps(data), encoding="utf-8")
                errors = validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT)
            self.assertTrue(any(error.startswith(prefix) for error in errors), field)

    def test_approved_manifest_rejects_activation_metadata(self):
        validator = load_validator()
        data = approved_h2()
        data["activated_at"] = "2026-08-21T12:05:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT)
        self.assertTrue(any(error.startswith("ACTIVATION_PREMATURE") for error in errors))

    def test_active_manifest_preserves_approval_and_planned_criteria(self):
        data = load_h2()
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["approval_digest"], data["candidate_digest"])
        self.assertEqual(data["approved_candidate_commit"], "c8e4596b153c10721ed335369863a07154eb2b43")
        self.assertEqual(data["approved_level"], "R1")
        self.assertEqual(data["implementation_status"], "BLOCKED_PENDING_OBSIDIAN_MAIN")
        self.assertEqual(data["criteria_status"], {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"})
        self.assertEqual(data["acceptance_status"], "NOT_STARTED")

    def test_active_manifest_runtime_status_does_not_change_digest(self):
        validator = load_validator()
        data = load_h2()
        self.assertEqual(validator.compute_digest(data), "2dc7f7864ffb766282f33b52dd5f0dc54e45c3b52a18d91f528ef1a44901a933")

    def test_gov_obs_manifest_is_r2_only_candidate(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-OBS-001.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertEqual(data["candidate_digest"], "6a2adee53c4aba66ca9f344f67319b72e624ce17408f73928947b9cc404c5060")
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])
        self.assertIn("certification", data["denied_without_jit"])
        self.assertIn("main", data["denied_without_jit"])

    def test_gov_infra_manifest_is_r2_only_candidate(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-INFRA-001.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertEqual(data["candidate_digest"], "37ab7416071d6438bfeb91c876d683360ac7a58afd8f22744584f516f2b9fe58")
        self.assertEqual(data["allowed_paths"], [".github/workflows/security-audit.yml", "docker-compose.h2-test.yml", "scripts/security/run_h2_r1_tests.sh"])
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])
        self.assertIn("certification", data["denied_without_jit"])
        self.assertIn("main", data["denied_without_jit"])

    def test_gov_arch_manifest_is_r2_only_candidate(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-ARCH-001.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertIn(".context/arquitectura_pipeline.md", data["allowed_paths"])
        self.assertIn(".context/sistema_db_supabase.md", data["allowed_paths"])
        self.assertIn(".context/operaciones/matriz_adopcion_db.md", data["allowed_paths"])
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])
        self.assertIn("certification", data["denied_without_jit"])
        self.assertIn("main", data["denied_without_jit"])

    def test_gov_hom_manifest_is_r2_only_candidate(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-HOM-001.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertEqual(data["baseline"]["candidate_commit"], "4cce43a743de5860c4da86eecf1782efab91d26b")
        self.assertEqual(data["baseline"]["candidate_tree"], "ac16b545b74a03b149aac538062def20101187fb")
        self.assertEqual(len(data["homologation_grants"]), 4)
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])
        self.assertIn("certification", data["denied_without_jit"])
        self.assertIn("main", data["denied_without_jit"])

    def test_gov_ci_manifest_is_r2_only_candidate(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-CI-001.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertEqual(data["baseline"]["candidate_commit"], "fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1")
        self.assertEqual(data["baseline"]["candidate_tree"], "5e7d087ac45457264ea29dfc1aa7373efd909290")
        self.assertFalse(data["ci_review_decoupling"]["reviews_trigger_ci"])
        self.assertFalse(data["ci_review_decoupling"]["reviews_api_used"])
        self.assertFalse(data["ci_review_decoupling"]["manual_rerun_required_for_review"])
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])
        self.assertIn("certification", data["denied_without_jit"])
        self.assertIn("main", data["denied_without_jit"])

    def test_gov_ci2_manifest_is_r2_only_candidate(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-CI-002.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertEqual(data["baseline"]["candidate_commit"], "b878c5764e55cb2646b60c4777e363489fe48e8b")
        self.assertEqual(data["baseline"]["candidate_tree"], "174c18efd840fff6ce27fce9fe1dc4edcd65abe8")
        self.assertEqual(data["candidate_digest"], "30bc9a2e7b201438e7398a46f42e6a719e0e5bb41d46c95c71b02234c9091d04")
        self.assertTrue(data["promotion_boundary"]["incremental_boundary_preserved"])
        self.assertEqual(len(data["promotion_boundary"]["structural_pairs"]), 4)
        self.assertEqual(data["promotion_boundary"]["blocked_pr_numbers"], [428])
        self.assertEqual(data["promotion_boundary"]["accepted_event_action"], "opened")
        self.assertEqual(data["promotion_boundary"]["accepted_run_attempt"], 1)
        self.assertIn("R3-GOV-HOM-001-O2", data["promotion_boundary"]["consumed_grants_blocked"])
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])
        self.assertIn("certification", data["denied_without_jit"])
        self.assertIn("main", data["denied_without_jit"])

    def test_gov_ci2_manifest_replay_guards_are_fixed(self):
        validator = load_validator()
        data = json.loads((MANIFEST_DIR / "WP-GOV-CI-002.json").read_text(encoding="utf-8"))
        data["promotion_boundary"]["accepted_run_attempt"] = 2
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-GOV-CI-002.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertIn("GOV_CI2_PROMOTION_REPLAY_GUARDS_INVALID:WP-GOV-CI-002.json", errors)

    def test_gov_hom_rejects_grouped_grants(self):
        validator = load_validator()
        data = json.loads((MANIFEST_DIR / "WP-GOV-HOM-001.json").read_text(encoding="utf-8"))
        data["homologation_grants"] = [{"id": "R3-GOV-HOM-001-O2-O5", "status": "TEMPLATE_ONLY_NOT_GRANTED", "single_use": True}]
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-GOV-HOM-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("GOV_HOM_GRANTS_INVALID") for error in errors))

    def test_gov_hom_rejects_missing_closure_predicate(self):
        validator = load_validator()
        data = json.loads((MANIFEST_DIR / "WP-GOV-HOM-001.json").read_text(encoding="utf-8"))
        data["closure_predicate"] = ["manual close"]
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-GOV-HOM-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("GOV_HOM_CLOSURE_PREDICATE_REQUIRED") for error in errors))

    def test_gov_hom_rejects_wrong_baseline_tree(self):
        validator = load_validator()
        data = json.loads((MANIFEST_DIR / "WP-GOV-HOM-001.json").read_text(encoding="utf-8"))
        data["baseline"]["candidate_tree"] = "0000000000000000000000000000000000000000"
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-GOV-HOM-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("GOV_HOM_BASELINE_INVALID") for error in errors))

    def test_active_manifest_rejects_bad_activation_timestamp(self):
        validator = load_validator()
        for activated_at, prefix in (("not-a-date", "ACTIVATION_METADATA_REQUIRED"), ("2026-08-21T22:00:00Z", "ACTIVATION_TIMESTAMP_INVALID")):
            data = load_h2()
            data["activated_at"] = activated_at
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "WP-H2-001.json"
                path.write_text(json.dumps(data), encoding="utf-8")
                errors = validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT)
            self.assertTrue(any(error.startswith(prefix) for error in errors), activated_at)

    def test_unsafe_allowlist_patterns_fail(self):
        validator = load_validator()
        data = load_h2()
        for bad in ("*", "**", "../secret", "/absolute", "web\\x", ".env*", "supabase/**"):
            mutated = copy.deepcopy(data)
            mutated["allowed_paths"] = [bad]
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "WP-H2-001.json"
                path.write_text(json.dumps(mutated), encoding="utf-8")
                errors = validator.validate_manifest(path, root=ROOT)
            self.assertTrue(any("UNSAFE_PATH_PATTERN" in error or "UNBOUNDED_ALLOWLIST" in error or "ALLOW_DENY_OVERLAP" in error for error in errors), bad)

    def test_changed_path_boundary_rejects_product_without_active_wp(self):
        validator = load_validator()
        manifests = [approved_h2()]
        errors = validator.validate_changed_paths([("M", "web/app/page.tsx")], manifests)
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))
        errors = validator.validate_changed_paths([("M", ".context/hitos/hito_002.md")], manifests)
        self.assertEqual(errors, [])

    def test_active_wp_uses_manifest_allowlist_without_governance_deny(self):
        validator = load_validator()
        data = load_h2()
        errors = validator.validate_changed_paths([("M", "db/migrations/20260821_h2.sql")], [data], active_work_package="WP-H2-001")
        self.assertEqual(errors, [])
        errors = validator.validate_changed_paths([("M", ".env.local")], [data], active_work_package="WP-H2-001")
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))
        errors = validator.validate_changed_paths([("M", "db/migrations/20260821_h2.sql")], [data], active_work_package="NONE")
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))

    def test_approved_wp_does_not_unlock_functional_paths(self):
        validator = load_validator()
        data = approved_h2()
        errors = validator.validate_changed_paths([("M", "db/migrations/20260821_h2.sql")], [data])
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))

    def test_activation_transition_rejects_functional_paths(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([("M", ".context/work_packages/WP-H2-001.json")], [data], active_work_package="WP-H2-001", activation_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", "scripts/core/cleansing_worker.py", "scripts/maintenance/h2_backfill.py"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", activation_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_obsidian_transition_rejects_functional_paths(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([("M", ".context/estado_del_proyecto.md"), ("M", "AGENTS.md")], [data], active_work_package="WP-H2-001", obsidian_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", "scripts/core/sync_vector_worker.py", "scripts/maintenance/h2_backfill.py", ".github/workflows/unapproved.yml"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", obsidian_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_obs_transition_rejects_functional_paths(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([("M", ".context/estado_del_proyecto.md"), ("M", "AGENTS.md")], [data], active_work_package="WP-H2-001", gov_obs_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", "scripts/core/sync_vector_worker.py", "scripts/maintenance/h2_backfill.py", ".github/workflows/unapproved.yml"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_obs_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_obs_transition_allows_explicit_infra_guardrails(self):
        validator = load_validator()
        data = load_h2()
        changed = [
            ("M", ".context/estado_del_proyecto.md"),
            ("M", "AGENTS.md"),
            ("M", ".github/workflows/security-audit.yml"),
            ("A", "docker-compose.h2-test.yml"),
            ("A", "scripts/security/run_h2_r1_tests.sh"),
        ]
        self.assertEqual(validator.validate_changed_paths(changed, [data], active_work_package="WP-H2-001", gov_obs_transition=True), [])

    def test_gov_hom_transition_rejects_functional_paths_and_arch_mutation(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", ".context/estado_del_proyecto.md"),
            ("A", ".context/work_packages/WP-GOV-HOM-001.json"),
        ], [data], active_work_package="WP-H2-001", gov_hom_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", "scripts/core/sync_vector_worker.py", ".context/work_packages/WP-GOV-ARCH-001.json"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_hom_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_ci_transition_allows_exact_scope_and_rejects_consumed_manifests(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", ".github/workflows/security-audit.yml"),
            ("M", "scripts/security/validate_change_governance.py"),
            ("A", ".context/work_packages/WP-GOV-CI-001.json"),
        ], [data], active_work_package="WP-H2-001", gov_ci_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", ".context/work_packages/WP-GOV-ARCH-001.json", ".context/work_packages/WP-GOV-HOM-001.json"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_ci_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_ci2_transition_allows_exact_scope_and_rejects_consumed_manifests(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", ".github/workflows/security-audit.yml"),
            ("M", "scripts/security/validate_work_package.py"),
            ("A", ".context/work_packages/WP-GOV-CI-002.json"),
        ], [data], active_work_package="WP-H2-001", gov_ci2_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", ".context/work_packages/WP-GOV-ARCH-001.json", ".context/work_packages/WP-GOV-HOM-001.json", ".context/work_packages/WP-GOV-CI-001.json"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_ci2_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def promotion_event_fixture(self, *, operation="O2 desarrollo -> certificacion", grant_id="R3-GOV-HOM-002-O2-20260822A", action="opened", number=429, base_ref="certificacion", head_ref="desarrollo", consumed=False):
        digest = "a" * 64
        tree = "b" * 40
        base_sha = "c" * 40
        head_sha = "d" * 40
        repo = "romelhc95/studiamatch"
        event = {
            "action": action,
            "number": number,
            "pull_request": {
                "number": number,
                "body": "\n".join([
                    f"Operation: {operation}",
                    f"Grant-ID: {grant_id}",
                    f"Base-SHA: {base_sha}",
                    f"Candidate-SHA: {head_sha}",
                    "Final-WP: WP-GOV-CI-002",
                    f"D_FINAL: {digest}",
                    f"T_FINAL: {tree}",
                    "Approval-Level: R3 JIT single-use",
                    "Approval-Reference: human-jit-o2-20260822",
                    "Approval-Expiry: 2026-08-23T00:00:00Z",
                ]),
                "base": {"ref": base_ref, "sha": base_sha, "repo": {"full_name": repo}},
                "head": {"ref": head_ref, "sha": head_sha, "repo": {"full_name": repo}},
            },
            "repository": {"full_name": repo},
        }
        grant = {
            "id": grant_id,
            "status": "APPROVED_JIT_SINGLE_USE",
            "operation": operation,
            "repository": repo,
            "base_ref": base_ref,
            "head_ref": head_ref,
            "base_sha": base_sha,
            "candidate_sha": head_sha,
            "final_wp": "WP-GOV-CI-002",
            "d_final": digest,
            "t_final": tree,
            "approval_level": "R3 JIT single-use",
            "approval_reference": "human-jit-o2-20260822",
            "approval_expiry": "2026-08-23T00:00:00Z",
            "event_action": "opened",
            "run_attempt": 1,
            "single_use": True,
            "consumed": consumed,
        }
        return event, grant, digest, tree

    def run_promotion_validation(self, event, grant, *, run_attempt="1"):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            grant_dir = Path(tmp) / ".context" / "r3_grants"
            grant_dir.mkdir(parents=True)
            (grant_dir / f"{grant['id']}.json").write_text(json.dumps(grant), encoding="utf-8")
            path.write_text(json.dumps(event), encoding="utf-8")
            with mock.patch.object(validator, "load_manifest_by_id", return_value={"candidate_digest": grant["d_final"]}), \
                 mock.patch.object(validator, "compute_digest", return_value=grant["d_final"]), \
                 mock.patch.object(validator, "git_sha", return_value=grant["t_final"]), \
                 mock.patch.object(validator, "git_is_ancestor", return_value=True):
                return validator.validate_promotion_event(str(path), event_name="pull_request", run_attempt=run_attempt, now=datetime(2026, 8, 22, tzinfo=UTC), root=Path(tmp))

    def test_promotion_event_validates_structural_attestation(self):
        event, grant, _, _ = self.promotion_event_fixture()
        self.assertEqual(self.run_promotion_validation(event, grant), [])

    def test_promotion_event_rejects_pr_428_even_with_valid_grant(self):
        event, grant, _, _ = self.promotion_event_fixture(number=428)
        self.assertIn("PROMOTION_PR_BLOCKED:428", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_replay_actions(self):
        for action in ("reopened", "edited", "synchronize", "ready_for_review"):
            event, grant, _, _ = self.promotion_event_fixture(action=action)
            self.assertIn("PROMOTION_ACTION_INVALID", self.run_promotion_validation(event, grant), action)

    def test_promotion_event_rejects_rerun_attempts(self):
        event, grant, _, _ = self.promotion_event_fixture()
        self.assertIn("PROMOTION_RUN_ATTEMPT_INVALID", self.run_promotion_validation(event, grant, run_attempt="2"))

    def test_promotion_event_rejects_consumed_grant(self):
        event, grant, _, _ = self.promotion_event_fixture(consumed=True)
        self.assertIn("PROMOTION_GRANT_MISMATCH:consumed", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_consumed_o2_grant_id(self):
        event, grant, _, _ = self.promotion_event_fixture(grant_id="R3-GOV-HOM-001-O2")
        grant["id"] = "R3-GOV-HOM-001-O2"
        self.assertIn("PROMOTION_GRANT_CONSUMED", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_repository_mismatch(self):
        event, grant, _, _ = self.promotion_event_fixture()
        grant["repository"] = "romelhc95/other"
        self.assertIn("PROMOTION_GRANT_MISMATCH:repository", self.run_promotion_validation(event, grant))

    def test_promotion_event_covers_o2_o5_pairs(self):
        cases = [
            ("O2 desarrollo -> certificacion", "R3-GOV-HOM-002-O2-20260822A", "certificacion", "desarrollo"),
            ("O3 certificacion -> main", "R3-GOV-HOM-002-O3-20260822A", "main", "certificacion"),
            ("O4 main -> certificacion", "R3-GOV-HOM-002-O4-20260822A", "certificacion", "main"),
            ("O5 certificacion -> desarrollo", "R3-GOV-HOM-002-O5-20260822A", "desarrollo", "certificacion"),
        ]
        for operation, grant_id, base_ref, head_ref in cases:
            event, grant, _, _ = self.promotion_event_fixture(operation=operation, grant_id=grant_id, base_ref=base_ref, head_ref=head_ref)
            self.assertEqual(self.run_promotion_validation(event, grant), [], operation)

    def test_promotion_event_rejects_wrong_pair(self):
        event, grant, _, _ = self.promotion_event_fixture(base_ref="main")
        errors = self.run_promotion_validation(event, grant)
        self.assertIn("PROMOTION_PAIR_INVALID", errors)

    def test_resolve_git_ref_normalizes_abbreviated_sha(self):
        validator = load_validator()
        self.assertEqual(validator.resolve_git_ref("974f9d4", root=ROOT), "974f9d4bde6d79230afde5c5a86ba7a3894233c6")

    def test_multiple_active_work_packages_fail(self):
        validator = load_validator()
        data = load_h2()
        errors = validator.validate_changed_paths([("M", ".context/work_packages/WP-H2-001.json")], [data, copy.deepcopy(data)], active_work_package="WP-H2-001")
        self.assertTrue(any(error.startswith("MULTIPLE_ACTIVE_WORK_PACKAGES") for error in errors))

    def test_h2_approval_level_cannot_exceed_r1(self):
        validator = load_validator()
        data = load_h2()
        data["status"] = "APPROVED"
        data["lifecycle_stage"] = "APPROVED_NOT_ACTIVE"
        data["gate_status"] = "APPROVED_R1"
        data["approval_digest"] = data["candidate_digest"]
        data["approved_by"] = "human-reviewer"
        data["approved_at"] = "2026-08-21T12:00:00Z"
        data["approval_reference"] = "manual-session"
        data["approved_level"] = "R2"
        data["approved_candidate_commit"] = "c8e4596b153c10721ed335369863a07154eb2b43"
        data["approval_evidence_sha256"] = "a" * 64
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT)
        self.assertTrue(any(error.startswith("APPROVAL_LEVEL_INVALID") for error in errors))


if __name__ == "__main__":
    unittest.main()
