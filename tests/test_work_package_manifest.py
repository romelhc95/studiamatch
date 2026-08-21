import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path


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


class WorkPackageManifestTests(unittest.TestCase):
    def test_sprint1_work_packages_validate(self):
        validator = load_validator()
        manifests = sorted(MANIFEST_DIR.glob("WP-H*-001.json"))
        self.assertEqual([path.stem for path in manifests], ["WP-H2-001", "WP-H3-001", "WP-H4-001", "WP-H5-001"])
        for path in manifests:
            self.assertEqual(validator.validate_manifest(path, root=ROOT), [])

    def test_h2_manifest_rebased_to_homologated_tree(self):
        data = load_h2()
        self.assertEqual(data["task_id"], "TASK-H2-001")
        self.assertEqual(data["phase_trace"], "F10.11")
        self.assertEqual(data["lifecycle_stage"], "AWAITING_DIGEST")
        self.assertEqual(data["gate_status"], "READY_FOR_DIGEST_APPROVAL")
        self.assertEqual(data["approval_target_lifecycle_stage"], "APPROVED_NOT_ACTIVE")
        self.assertEqual(data["approval_target_gate_status"], "APPROVED_R1")
        self.assertEqual(data["approval_target_level"], "R1")
        self.assertEqual(data["criteria_contract"], ["H2-CA2", "H2-CA3"])
        self.assertEqual(data["implementation_status"], "PLANNED_NOT_ACTIVE")
        self.assertEqual(data["criteria_status"], {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"})
        self.assertEqual(data["environment_scope"], ["local", "development"])
        self.assertIn("supabase-free", data["denied_without_jit"])
        self.assertIn("certification", data["denied_without_jit"])

    def test_proposed_manifest_cannot_include_approval_fields(self):
        validator = load_validator()
        data = load_h2()
        data["approval_digest"] = data["candidate_digest"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("WP_PROPOSED_APPROVAL_FIELDS") for error in errors))

    def test_proposed_manifest_cannot_include_approved_level(self):
        validator = load_validator()
        data = load_h2()
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
        data = load_h2()
        data["approval_target_level"] = "R2"
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("APPROVAL_TARGET_INVALID") for error in errors))

    def test_unknown_top_level_field_fails_for_h2_schema(self):
        validator = load_validator()
        data = load_h2()
        data["unexpected"] = "value"
        data["candidate_digest"] = validator.compute_digest(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, root=ROOT)
        self.assertTrue(any(error.startswith("WP_UNKNOWN_FIELDS") for error in errors))

    def test_approved_requires_metadata_and_matching_digest(self):
        validator = load_validator()
        data = load_h2()
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
                "approved_candidate_commit": "fef4596dd731d50e16f6752e6390516c6d49f87e",
                "approval_evidence_sha256": "a" * 64,
            })
            path.write_text(json.dumps(data), encoding="utf-8")
            approval_errors = [error for error in validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT) if error.startswith("APPROVAL")]
        self.assertEqual(approval_errors, [])

    def test_active_requires_activation_metadata(self):
        validator = load_validator()
        data = load_h2()
        data.update({
            "status": "ACTIVE",
            "lifecycle_stage": "ACTIVE",
            "gate_status": "APPROVED_R1",
            "approval_digest": data["candidate_digest"],
            "approved_by": "human-reviewer",
            "approved_at": "2026-08-21T12:00:00Z",
            "approval_reference": "manual-session",
            "approved_level": "R1",
            "approved_candidate_commit": "fef4596dd731d50e16f6752e6390516c6d49f87e",
            "approval_evidence_sha256": "a" * 64,
        })
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
        data = load_h2()
        original = data["candidate_digest"]
        data["approval_target_gate_status"] = "APPROVED_R2"
        self.assertNotEqual(validator.compute_digest(data), original)
        data = load_h2()
        data["metrics"]["last_validation_at"] = "2026-08-21T12:00:00Z"
        self.assertEqual(validator.compute_digest(data), original)

    def test_approval_envelope_preserves_canonical_payload(self):
        validator = load_validator()
        data = load_h2()
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
            "approved_candidate_commit": "fef4596dd731d50e16f6752e6390516c6d49f87e",
            "approval_evidence_sha256": "a" * 64,
        })
        self.assertEqual(validator.canonical_payload(data), before)
        self.assertEqual(validator.compute_digest(data), data["candidate_digest"])

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
        manifests = [load_h2()]
        errors = validator.validate_changed_paths([("M", "web/app/page.tsx")], manifests)
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))
        errors = validator.validate_changed_paths([("M", ".context/hitos/hito_002.md")], manifests)
        self.assertEqual(errors, [])

    def test_active_wp_uses_manifest_allowlist_without_governance_deny(self):
        validator = load_validator()
        data = load_h2()
        data["status"] = "ACTIVE"
        data["lifecycle_stage"] = "ACTIVE"
        data["gate_status"] = "APPROVED_R1"
        data["approval_digest"] = data["candidate_digest"]
        data["approved_by"] = "human-reviewer"
        data["approved_at"] = "2026-08-21T12:00:00Z"
        data["approval_reference"] = "manual-session"
        data["approved_level"] = "R1"
        data["approved_candidate_commit"] = "fef4596dd731d50e16f6752e6390516c6d49f87e"
        data["approval_evidence_sha256"] = "a" * 64
        data["activated_at"] = "2026-08-21T12:05:00Z"
        errors = validator.validate_changed_paths([("M", "db/migrations/20260821_h2.sql")], [data], active_work_package="WP-H2-001")
        self.assertEqual(errors, [])
        errors = validator.validate_changed_paths([("M", ".env.local")], [data], active_work_package="WP-H2-001")
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))
        errors = validator.validate_changed_paths([("M", "db/migrations/20260821_h2.sql")], [data], active_work_package="NONE")
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))

    def test_approved_wp_does_not_unlock_functional_paths(self):
        validator = load_validator()
        data = load_h2()
        data["status"] = "APPROVED"
        data["lifecycle_stage"] = "APPROVED_NOT_ACTIVE"
        data["gate_status"] = "APPROVED_R1"
        data["approval_digest"] = data["candidate_digest"]
        data["approved_by"] = "human-reviewer"
        data["approved_at"] = "2026-08-21T12:00:00Z"
        data["approval_reference"] = "manual-session"
        data["approved_level"] = "R1"
        data["approved_candidate_commit"] = "fef4596dd731d50e16f6752e6390516c6d49f87e"
        data["approval_evidence_sha256"] = "a" * 64
        errors = validator.validate_changed_paths([("M", "db/migrations/20260821_h2.sql")], [data])
        self.assertTrue(any(error.startswith("DENIED_PATH") for error in errors))

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
        data["approved_candidate_commit"] = "fef4596dd731d50e16f6752e6390516c6d49f87e"
        data["approval_evidence_sha256"] = "a" * 64
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WP-H2-001.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate_manifest(path, now=datetime(2026, 8, 21, tzinfo=UTC), root=ROOT)
        self.assertTrue(any(error.startswith("APPROVAL_LEVEL_INVALID") for error in errors))


if __name__ == "__main__":
    unittest.main()
