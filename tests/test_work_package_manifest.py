import copy
import hashlib
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
        self.assertEqual([path.stem for path in manifests], ["WP-GOV-ARCH-001", "WP-GOV-CI-001", "WP-GOV-CI-002", "WP-GOV-CI-003", "WP-GOV-CI-004", "WP-GOV-CI-005", "WP-GOV-CI-006", "WP-GOV-CI-007", "WP-GOV-CI-008", "WP-GOV-CI-009", "WP-GOV-CI-010", "WP-GOV-CI-011", "WP-GOV-CI-012", "WP-GOV-HOM-001", "WP-GOV-INFRA-001", "WP-GOV-OBS-001", "WP-H2-001", "WP-H3-001", "WP-H4-001", "WP-H5-001"])
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

    def test_gov_ci3_manifest_bootstrap_is_static(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-CI-003.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertEqual(data["baseline"]["candidate_commit"], "1ac74f78fec6290e214444e9d2f18619ae3fd3b6")
        self.assertEqual(data["baseline"]["candidate_tree"], "8191790192580f2e9fb1ddb48d85ab28714720f9")
        self.assertEqual(data["supersedes_digest"], "30bc9a2e7b201438e7398a46f42e6a719e0e5bb41d46c95c71b02234c9091d04")
        bootstrap = data["promotion_request_bootstrap"]
        self.assertEqual(bootstrap["final_wp"], "WP-GOV-CI-003")
        self.assertEqual(bootstrap["static_request_status"], "REQUESTED_JIT_SINGLE_USE")
        self.assertEqual(bootstrap["symbolic_bindings"]["candidate_sha_binding"], "pull_request.head.sha")
        self.assertEqual(len(bootstrap["grant_request_ids"]), 4)
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])

    def test_gov_ci4_manifest_uses_promotion_environment(self):
        validator = load_validator()
        path = MANIFEST_DIR / "WP-GOV-CI-004.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_level"], "R2")
        self.assertEqual(data["baseline"]["candidate_commit"], "235c2329eb5fd8903c31785640a63466b23f0dd8")
        self.assertEqual(data["baseline"]["candidate_tree"], "cc774746d21cb6649f7018da3049fc811a3f294b")
        self.assertEqual(data["supersedes_digest"], "60c1fc0978208742597f17ef6f4c1fe5741f59b5de0739accbce24fa613ab9c7")
        self.assertEqual(data["promotion_environment_remediation"]["environment"], "Promotion")
        self.assertEqual(data["promotion_environment_remediation"]["failed_pr"], 431)
        self.assertEqual(data["promotion_environment_remediation"]["consumed_grant"], "R3-GOV-HOM-003-O2-REQ1")
        self.assertEqual(data["promotion_request_bootstrap"]["final_wp"], "WP-GOV-CI-004")
        self.assertEqual(data["promotion_request_bootstrap"]["grant_request_ids"][0], "R3-GOV-HOM-004-O2-REQ1")
        self.assertEqual(validator.validate_manifest(path, root=ROOT), [])

    def test_static_promotion_requests_have_no_self_reference(self):
        validator = load_validator()
        self.assertEqual(validator.validate_static_promotion_requests(root=ROOT), [])
        for path in sorted((ROOT / ".context" / "r3_grants").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for forbidden in ("base_sha", "candidate_sha", "d_final", "t_final", "approval_reference", "approval_expiry", "approval_level", "consumed", "Base-SHA", "Candidate-SHA", "D_FINAL", "T_FINAL", "Approval-Reference", "Approval-Expiry", "Approval-Level"):
                self.assertNotIn(forbidden, data)
            if data["id"] in validator.PROMOTION_CONSUMED_GRANTS:
                self.assertIn(data["status"], {"REQUESTED_JIT_SINGLE_USE", "CONSUMED_BY_FAILURE"})
            elif data["id"] in validator.PROMOTION_SUPERSEDED_GRANTS:
                self.assertIn(data["status"], {"REQUESTED_JIT_SINGLE_USE", "SUPERSEDED_NOT_USABLE"})
            else:
                self.assertEqual(data["status"], "REQUESTED_JIT_SINGLE_USE")
            self.assertEqual(data["candidate_sha_binding"], "pull_request.head.sha")
            if data["id"].startswith(("R3-GOV-HOM-006-", "R3-GOV-HOM-007-", "R3-GOV-HOM-008-", "R3-GOV-HOM-009-", "R3-GOV-HOM-010-", "R3-GOV-HOM-011-", "R3-GOV-HOM-012-")):
                self.assertEqual(data["t_final_binding"], "tree(promotion_attestation.Source-SHA)")
                self.assertEqual(data["candidate_tree_binding"], "tree(pull_request.head.sha)")
            else:
                self.assertEqual(data["t_final_binding"], "tree(pull_request.head.sha)")
            if data["id"].startswith(("R3-GOV-HOM-007-", "R3-GOV-HOM-008-", "R3-GOV-HOM-009-", "R3-GOV-HOM-010-", "R3-GOV-HOM-011-", "R3-GOV-HOM-012-")):
                self.assertEqual(data["required_merger"], "romelhc95")
                self.assertEqual(data["required_reviewer"], "romelhc95-approver")
                self.assertIs(data["merger_reviewer_distinct"], True)

    def test_static_promotion_request_rejects_bad_binding(self):
        validator = load_validator()
        grant = json.loads((ROOT / ".context" / "r3_grants" / "R3-GOV-HOM-004-O2-REQ1.json").read_text(encoding="utf-8"))
        grant["candidate_sha_binding"] = "literal-sha"
        errors = validator.validate_static_promotion_request(
            grant,
            grant_id="R3-GOV-HOM-004-O2-REQ1",
            operation="O2 desarrollo -> certificacion",
            repo_name="romelhc95/studiamatch",
            base_ref="certificacion",
            head_ref="desarrollo",
            final_wp_id="WP-GOV-CI-004",
            d_final="a" * 64,
        )
        self.assertIn("PROMOTION_GRANT_MISMATCH:candidate_sha_binding", errors)

    def test_static_promotion_request_rejects_attestation_fields(self):
        validator = load_validator()
        grant = json.loads((ROOT / ".context" / "r3_grants" / "R3-GOV-HOM-004-O2-REQ1.json").read_text(encoding="utf-8"))
        grant["D_FINAL"] = "a" * 64
        errors = validator.validate_static_promotion_request(
            grant,
            grant_id="R3-GOV-HOM-004-O2-REQ1",
            operation="O2 desarrollo -> certificacion",
            repo_name="romelhc95/studiamatch",
            base_ref="certificacion",
            head_ref="desarrollo",
            final_wp_id="WP-GOV-CI-004",
            d_final="a" * 64,
        )
        self.assertIn("PROMOTION_GRANT_SELF_REFERENCE:D_FINAL", errors)

    def test_static_promotion_request_rejects_unknown_approval_metadata(self):
        validator = load_validator()
        grant = json.loads((ROOT / ".context" / "r3_grants" / "R3-GOV-HOM-004-O2-REQ1.json").read_text(encoding="utf-8"))
        grant["approved_by"] = "reviewer"
        errors = validator.validate_static_promotion_request(
            grant,
            grant_id="R3-GOV-HOM-004-O2-REQ1",
            operation="O2 desarrollo -> certificacion",
            repo_name="romelhc95/studiamatch",
            base_ref="certificacion",
            head_ref="desarrollo",
            final_wp_id="WP-GOV-CI-004",
            d_final="a" * 64,
        )
        self.assertTrue(any(error.startswith("PROMOTION_GRANT_UNKNOWN_FIELDS") for error in errors))

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

    def test_gov_ci3_transition_allows_exact_scope_and_rejects_consumed_manifests(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", "scripts/security/validate_work_package.py"),
            ("A", ".context/work_packages/WP-GOV-CI-003.json"),
            ("A", ".context/r3_grants/R3-GOV-HOM-003-O2-REQ1.json"),
        ], [data], active_work_package="WP-H2-001", gov_ci3_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", ".context/work_packages/WP-GOV-ARCH-001.json", ".context/work_packages/WP-GOV-HOM-001.json", ".context/work_packages/WP-GOV-CI-001.json", ".context/work_packages/WP-GOV-CI-002.json"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_ci3_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_ci4_transition_allows_exact_scope_and_rejects_consumed_manifests(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", ".github/workflows/security-audit.yml"),
            ("M", "scripts/security/validate_work_package.py"),
            ("A", ".context/work_packages/WP-GOV-CI-004.json"),
            ("A", ".context/r3_grants/R3-GOV-HOM-004-O2-REQ1.json"),
        ], [data], active_work_package="WP-H2-001", gov_ci4_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", ".context/work_packages/WP-GOV-ARCH-001.json", ".context/work_packages/WP-GOV-HOM-001.json", ".context/work_packages/WP-GOV-CI-001.json", ".context/work_packages/WP-GOV-CI-002.json", ".context/work_packages/WP-GOV-CI-003.json"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_ci4_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_ci5_transition_allows_exact_scope_and_rejects_consumed_manifests(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", ".github/workflows/security-audit.yml"),
            ("M", "scripts/security/validate_work_package.py"),
            ("A", ".context/work_packages/WP-GOV-CI-005.json"),
            ("A", ".context/r3_grants/R3-GOV-HOM-005-O2-REQ1.json"),
        ], [data], active_work_package="WP-H2-001", gov_ci5_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", ".context/work_packages/WP-GOV-ARCH-001.json", ".context/work_packages/WP-GOV-HOM-001.json", ".context/work_packages/WP-GOV-CI-001.json", ".context/work_packages/WP-GOV-CI-002.json", ".context/work_packages/WP-GOV-CI-003.json", ".context/work_packages/WP-GOV-CI-004.json"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_ci5_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_ci6_transition_allows_exact_scope_and_rejects_consumed_manifests(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", ".github/workflows/security-audit.yml"),
            ("M", ".github/workflows/f9-7-contract.yml"),
            ("M", "scripts/security/validate_work_package.py"),
            ("A", ".context/work_packages/WP-GOV-CI-006.json"),
            ("A", ".context/r3_grants/R3-GOV-HOM-006-O2-REQ1.json"),
        ], [data], active_work_package="WP-H2-001", gov_ci6_transition=True)
        self.assertEqual(allowed, [])
        for path in ("db/migrations/20260821_h2.sql", "web/app/page.tsx", ".context/work_packages/WP-GOV-CI-001.json", ".context/work_packages/WP-GOV-CI-002.json", ".context/work_packages/WP-GOV-CI-003.json", ".context/work_packages/WP-GOV-CI-004.json", ".context/work_packages/WP-GOV-CI-005.json"):
            errors = validator.validate_changed_paths([("M", path)], [data], active_work_package="WP-H2-001", gov_ci6_transition=True)
            self.assertTrue(any(error.startswith("DENIED_PATH") or error.startswith("CHANGED_PATH_NOT_ALLOWED") for error in errors), path)

    def test_gov_ci12_transition_allows_readiness_remediation_controls(self):
        validator = load_validator()
        data = load_h2()
        allowed = validator.validate_changed_paths([
            ("M", "scripts/security/github_promotion_snapshot.py"),
            ("M", "scripts/security/validate_promotion_readiness.py"),
            ("M", "scripts/security/validate_work_package.py"),
            ("M", "tests/test_promotion_api_adapter.py"),
            ("M", "tests/test_promotion_readiness.py"),
            ("M", "tests/test_work_package_manifest.py"),
        ], [data], active_work_package="WP-H2-001", gov_ci12_transition=True)
        self.assertEqual(allowed, [])

    def promotion_event_fixture(self, *, operation="O2 desarrollo -> certificacion", grant_id="R3-GOV-HOM-012-O2-REQ2", action="opened", number=500, base_ref="certificacion", source_ref="desarrollo", head_ref="promote/gov-hom-012-o2-req2", consumed=False):
        digest = "a" * 64
        tree = "b" * 40
        base_sha = "c" * 40
        head_sha = "d" * 40
        source_sha = "e" * 40
        repo = "romelhc95/studiamatch"
        event = {
            "action": action,
            "number": number,
            "pull_request": {
                "number": number,
                "body": "\n".join([
                    "## Promotion Attestation",
                     f"Operation: {operation}",
                    f"Grant-ID: {grant_id}",
                    f"Base-Ref: {base_ref}",
                    f"Base-SHA: {base_sha}",
                    f"Source-Ref: {source_ref}",
                    f"Source-SHA: {source_sha}",
                    f"Candidate-SHA: {head_sha}",
                    f"Candidate-Tree: {tree}",
                    "Final-WP: WP-GOV-CI-012",
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
            "status": "REQUESTED_JIT_SINGLE_USE",
            "operation": operation,
            "repository": repo,
            "base_ref": base_ref,
            "head_ref": head_ref,
            "source_ref": source_ref,
            "candidate_branch": head_ref,
            "final_wp": "WP-GOV-CI-012",
            "base_sha_binding": "pull_request.base.sha",
            "source_sha_binding": "promotion_attestation.Source-SHA",
            "candidate_sha_binding": "pull_request.head.sha",
            "candidate_tree_binding": "tree(pull_request.head.sha)",
            "t_final_binding": "tree(promotion_attestation.Source-SHA)",
            "d_final_binding": "manifest.candidate_digest",
            "event_action": "opened",
            "run_attempt": 1,
            "single_use": True,
            "external_consumption_required": True,
            "required_merger": "romelhc95",
            "required_reviewer": "romelhc95-approver",
            "merger_reviewer_distinct": True,
            "approval_envelope_schema": "promotion-jit-envelope-v3",
            "allowed_side_effects": ["certification_branch_update"],
        }
        if operation.startswith("O3"):
            grant.update({"allowed_side_effects": ["main_branch_update", "cloudflare_pages_production_rebuild", "db_sync_detect_only"], "cloudflare_pages_production_rebuild_expected": True, "db_sync_detect_only_required": True, "db_sync_expected_result": "NO_DB_CHANGES"})
        if operation.startswith("O4"):
            grant["allowed_side_effects"] = ["certification_branch_update"]
            grant["blocked_until_o3_closed"] = True
        if operation.startswith("O5"):
            grant["allowed_side_effects"] = ["development_branch_update"]
        if consumed:
            grant["consumed"] = True
        return event, grant, digest, tree

    def run_promotion_validation(self, event, grant, *, run_attempt="1"):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            grant_dir = Path(tmp) / ".context" / "r3_grants"
            grant_dir.mkdir(parents=True)
            digest = "a" * 64
            tree = "b" * 40
            (grant_dir / f"{grant['id']}.json").write_text(json.dumps(grant), encoding="utf-8")
            path.write_text(json.dumps(event), encoding="utf-8")
            base_sha = event["pull_request"]["base"]["sha"]
            head_sha = event["pull_request"]["head"]["sha"]
            fields = load_validator().parse_attestation_fields(event["pull_request"]["body"])
            source_sha = fields["Source-SHA"]
            protected_env = {"GITHUB_RUN_ID": "1000", "PROMOTION_RULESET_DIGEST": "sha256:" + "1" * 64, "R3_JIT_APPROVAL_ENVELOPE": json.dumps({"schema": "promotion-jit-envelope-v3", "transaction_id": "tx-hom012-test", "approval_id": "human-jit-o2-20260822", "grant_id": grant["id"], "repository_id": 1, "repository": "romelhc95/studiamatch", "operation": fields["Operation"], "pr_number": event["pull_request"]["number"], "pr_node_id": "PR_kw_test", "premerge_run_id": 1000, "premerge_run_attempt": 1, "event_name": "pull_request", "event_action": "opened", "base_ref": event["pull_request"]["base"]["ref"], "base_sha": base_sha, "source_ref": fields["Source-Ref"], "source_sha": source_sha, "candidate_ref": event["pull_request"]["head"]["ref"], "candidate_sha": head_sha, "candidate_tree": tree, "final_wp": "WP-GOV-CI-012", "final_digest": digest, "final_tree": tree, "required_reviewer": "romelhc95-approver", "required_reviewer_id": 306979205, "required_merger": "romelhc95", "required_merger_id": 18040405, "allowed_side_effects": grant["allowed_side_effects"], "environment": "Promotion", "environment_id": 10, "ruleset_id": 21255108, "ruleset_digest": "sha256:" + "1" * 64, "issued_at": "2026-08-22T00:00:00Z", "expires_at": "2026-08-23T00:00:00Z", "nonce": "nonce-hom012-test"})}
            def fake_git_sha(args, root=ROOT):
                if args[:3] == ["show", "-s", "--format=%P"]:
                    return f"{base_sha} {source_sha}"
                if args[:2] == ["rev-parse", f"origin/{fields['Source-Ref']}"]:
                    return source_sha
                if args[:2] == ["rev-parse", f"{head_sha}^{{tree}}"]:
                    return tree
                if args[:2] == ["rev-parse", f"{source_sha}^{{tree}}"]:
                    return tree
                if args[:2] == ["rev-parse", "HEAD^{tree}"]:
                    return tree
                return tree
            with mock.patch.dict("os.environ", protected_env, clear=False), \
                 mock.patch.object(validator, "load_manifest_by_id", return_value={"candidate_digest": digest}), \
                 mock.patch.object(validator, "compute_digest", return_value=digest), \
                 mock.patch.object(validator, "git_sha", side_effect=fake_git_sha), \
                 mock.patch.object(validator, "git_is_ancestor", return_value=True):
                return validator.validate_promotion_event(str(path), event_name="pull_request", run_attempt=run_attempt, now=datetime(2026, 8, 22, tzinfo=UTC), root=Path(tmp))

    def test_promotion_event_requires_protected_approval_env(self):
        validator = load_validator()
        event, grant, digest, tree = self.promotion_event_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            grant_dir = Path(tmp) / ".context" / "r3_grants"
            grant_dir.mkdir(parents=True)
            (grant_dir / f"{grant['id']}.json").write_text(json.dumps(grant), encoding="utf-8")
            path.write_text(json.dumps(event), encoding="utf-8")
            with mock.patch.dict("os.environ", {
                "R3_JIT_APPROVAL_ENVELOPE": "",
            }, clear=False), \
                 mock.patch.object(validator, "load_manifest_by_id", return_value={"candidate_digest": digest}), \
                 mock.patch.object(validator, "compute_digest", return_value=digest), \
                 mock.patch.object(validator, "git_sha", return_value=tree), \
                 mock.patch.object(validator, "git_is_ancestor", return_value=True):
                errors = validator.validate_promotion_event(str(path), event_name="pull_request", run_attempt="1", now=datetime(2026, 8, 22, tzinfo=UTC), root=Path(tmp))
        self.assertIn("PROMOTION_APPROVAL_ENVELOPE_REQUIRED", errors)

    def test_promotion_event_validates_structural_attestation(self):
        event, grant, _, _ = self.promotion_event_fixture()
        self.assertEqual(self.run_promotion_validation(event, grant), [])

    def test_promotion_event_rejects_pr_428_even_with_valid_grant(self):
        event, grant, _, _ = self.promotion_event_fixture(number=428)
        self.assertIn("PROMOTION_PR_BLOCKED:428", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_pr_431_even_with_valid_grant(self):
        event, grant, _, _ = self.promotion_event_fixture(number=431)
        self.assertIn("PROMOTION_PR_BLOCKED:431", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_replay_actions(self):
        for action in ("reopened", "edited", "synchronize", "ready_for_review"):
            event, grant, _, _ = self.promotion_event_fixture(action=action)
            self.assertIn("PROMOTION_ACTION_INVALID", self.run_promotion_validation(event, grant), action)

    def test_promotion_event_rejects_rerun_attempts(self):
        event, grant, _, _ = self.promotion_event_fixture()
        self.assertIn("PROMOTION_RUN_ATTEMPT_INVALID", self.run_promotion_validation(event, grant, run_attempt="2"))

    def test_promotion_event_rejects_consumed_grant(self):
        event, grant, _, _ = self.promotion_event_fixture(consumed=True)
        self.assertIn("PROMOTION_GRANT_SELF_REFERENCE:consumed", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_consumed_o2_grant_id(self):
        event, grant, _, _ = self.promotion_event_fixture(grant_id="R3-GOV-HOM-003-O2-REQ1")
        grant["id"] = "R3-GOV-HOM-003-O2-REQ1"
        self.assertIn("PROMOTION_GRANT_CONSUMED", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_consumed_hom004_o2_grant_id(self):
        event, grant, _, _ = self.promotion_event_fixture(grant_id="R3-GOV-HOM-004-O2-REQ1")
        grant["id"] = "R3-GOV-HOM-004-O2-REQ1"
        self.assertIn("PROMOTION_GRANT_CONSUMED", self.run_promotion_validation(event, grant))

    def test_promotion_event_rejects_repository_mismatch(self):
        event, grant, _, _ = self.promotion_event_fixture()
        grant["repository"] = "romelhc95/other"
        self.assertIn("PROMOTION_GRANT_MISMATCH:repository", self.run_promotion_validation(event, grant))

    def test_promotion_event_requires_hom010_identity_contract(self):
        event, grant, _, _ = self.promotion_event_fixture()
        grant.pop("required_merger")
        self.assertIn("PROMOTION_GRANT_MISMATCH:required_merger", self.run_promotion_validation(event, grant))

    def test_promotion_event_covers_o2_o5_pairs(self):
        cases = [
            ("O2 desarrollo -> certificacion", "R3-GOV-HOM-012-O2-REQ2", "certificacion", "desarrollo", "promote/gov-hom-012-o2-req2"),
            ("O3 certificacion -> main", "R3-GOV-HOM-012-O3-REQ2", "main", "certificacion", "promote/gov-hom-012-o3-req2"),
            ("O4 main -> certificacion", "R3-GOV-HOM-012-O4-REQ2", "certificacion", "main", "promote/gov-hom-012-o4-req2"),
            ("O5 certificacion -> desarrollo", "R3-GOV-HOM-012-O5-REQ2", "desarrollo", "certificacion", "promote/gov-hom-012-o5-req2"),
        ]
        for operation, grant_id, base_ref, source_ref, head_ref in cases:
            event, grant, _, _ = self.promotion_event_fixture(operation=operation, grant_id=grant_id, base_ref=base_ref, source_ref=source_ref, head_ref=head_ref)
            self.assertEqual(self.run_promotion_validation(event, grant), [], operation)

    def test_promotion_event_rejects_wrong_pair(self):
        event, grant, _, _ = self.promotion_event_fixture(base_ref="main")
        errors = self.run_promotion_validation(event, grant)
        self.assertIn("PROMOTION_PAIR_INVALID", errors)

    def post_merge_fixture(self, *, operation="O2 desarrollo -> certificacion", base_ref="certificacion", source_ref="desarrollo", head_ref="promote/gov-hom-012-o2-req2", fork=False, pair_override=None, parents=None, candidate_parents=None, checks=True, reviewer="romelhc95-approver", review_state="APPROVED", merger="romelhc95", final_wp="WP-GOV-CI-012", pr_created_at="2026-08-23T01:00:00Z", pr_merged_at="2026-08-23T01:20:00Z", check_completed_at="2026-08-23T01:05:00Z", grant_id="R3-GOV-HOM-012-O2-REQ2", approval_expiry="2026-08-29T23:59:59Z", pull_requests=None):
        before = "a" * 40
        after = "b" * 40
        head_sha = "c" * 40
        source_sha = "f" * 40
        tree = "d" * 40
        repo = "romelhc95/studiamatch"
        actual_base, actual_source, actual_head = pair_override or (base_ref, source_ref, head_ref)
        event = {"before": before, "after": after, "ref": f"refs/heads/{actual_base}", "head_commit": {"timestamp": "2026-08-23T01:30:00Z"}}
        body = "\n".join([
            "## Promotion Attestation",
            f"Operation: {operation}",
            f"Grant-ID: {grant_id}",
            f"Base-Ref: {actual_base}",
            f"Base-SHA: {before}",
            f"Source-Ref: {actual_source}",
            f"Source-SHA: {source_sha}",
            f"Candidate-SHA: {head_sha}",
            f"Candidate-Tree: {tree}",
            f"Final-WP: {final_wp}",
            "D_FINAL: " + "e" * 64,
            f"T_FINAL: {tree}",
            "Approval-Level: R3 JIT single-use",
            "Approval-Reference: human-jit-o2",
            f"Approval-Expiry: {approval_expiry}",
        ])
        pr = {
            "number": 500,
            "merged": True,
            "merge_commit_sha": after,
            "body": body,
            "created_at": pr_created_at,
            "merged_at": pr_merged_at,
            "updated_at": pr_merged_at,
            "merged_by": {"login": merger, "id": 18040405 if merger == "romelhc95" else 306979205},
            "base": {"ref": actual_base, "sha": before, "repo": {"full_name": repo}},
            "head": {"ref": actual_head, "sha": head_sha, "repo": {"full_name": "other/repo" if fork else repo}},
        }
        associated_prs = [{"number": 500}] if pull_requests is None else pull_requests
        envelope_summary = {"schema": "promotion-jit-envelope-v3", "transaction_id": "tx-hom012-post", "approval_id_sha256": hashlib.sha256(b"human-jit-o2").hexdigest(), "grant_id": grant_id, "repository_id": 1, "repository": repo, "operation": operation, "pr_number": 500, "pr_node_id": "PR_kw_post", "premerge_run_id": 1000, "premerge_run_attempt": 1, "event_name": "pull_request", "event_action": "opened", "base_ref": actual_base, "base_sha": before, "source_ref": actual_source, "source_sha": source_sha, "candidate_ref": actual_head, "candidate_sha": head_sha, "candidate_tree": tree, "final_wp": final_wp, "final_digest": "e" * 64, "final_tree": tree, "required_reviewer": "romelhc95-approver", "required_reviewer_id": 306979205, "required_merger": "romelhc95", "required_merger_id": 18040405, "allowed_side_effects": ["certification_branch_update"], "environment": "Promotion", "environment_id": 10, "ruleset_id": 21255108, "ruleset_digest": "sha256:" + "1" * 64, "issued_at": "2026-08-23T01:01:00Z", "expires_at": approval_expiry}
        evidence = {
            "pull_request": pr,
            "checks": [
                {"id": 1, "name": "Promotion Boundary", "status": "completed", "conclusion": "success" if checks else "failure", "head_sha": head_sha, "started_at": "2026-08-23T01:04:00Z", "completed_at": check_completed_at, "updated_at": check_completed_at, "pull_requests": associated_prs, "app": {"id": 15368}, "details_url": "https://github.com/romelhc95/studiamatch/actions/runs/1000/job/1"},
                {"id": 2, "name": "security-audit", "status": "completed", "conclusion": "success" if checks else "failure", "head_sha": head_sha, "started_at": "2026-08-23T01:04:00Z", "completed_at": check_completed_at, "updated_at": check_completed_at, "pull_requests": associated_prs, "app": {"id": 15368}, "details_url": "https://github.com/romelhc95/studiamatch/actions/runs/1000/job/2"},
            ],
            "workflow_runs": {"1000": {"id": 1000, "repository": {"full_name": repo}, "event": "pull_request", "head_sha": head_sha, "head_branch": actual_head, "run_attempt": 1, "path": ".github/workflows/security-audit.yml", "status": "completed", "conclusion": "success", "created_at": "2026-08-23T01:03:00Z", "updated_at": "2026-08-23T01:06:00Z"}},
            "reviews": [{"id": 1, "submitted_at": "2026-08-23T01:07:00Z", "user": {"login": reviewer, "id": 306979205 if reviewer == "romelhc95-approver" else 18040405}, "state": review_state, "commit_id": head_sha}],
            "timeline": [],
            "protected_approval": {"envelope_summary": envelope_summary},
        }
        if operation.startswith("O3"):
            evidence["db_changed"] = False
            evidence["checks"].extend([
                {"id": 3, "name": "Cloudflare Pages", "status": "completed", "conclusion": "success", "head_sha": after, "started_at": "2026-08-23T01:21:00Z", "completed_at": "2026-08-23T01:22:00Z", "updated_at": "2026-08-23T01:22:00Z", "pull_requests": [], "app": {"id": 85455}, "details_url": "https://github.com/apps/cloudflare-workers-and-pages"},
                {"id": 4, "name": "DB Sync Detect Only", "status": "completed", "conclusion": "success", "head_sha": after, "started_at": "2026-08-23T01:23:00Z", "completed_at": "2026-08-23T01:24:00Z", "updated_at": "2026-08-23T01:24:00Z", "pull_requests": [], "app": {"id": 15368}, "details_url": "https://github.com/romelhc95/studiamatch/actions/runs/1001/job/4", "output": {"summary": "NO_DB_CHANGES"}},
            ])
            evidence["protected_approval"]["envelope_summary"]["allowed_side_effects"] = ["main_branch_update", "cloudflare_pages_production_rebuild", "db_sync_detect_only"]
        if operation.startswith("O4"):
            evidence["protected_approval"]["envelope_summary"]["allowed_side_effects"] = ["certification_branch_update"]
        if operation.startswith("O5"):
            evidence["protected_approval"]["envelope_summary"]["allowed_side_effects"] = ["development_branch_update"]
        return event, evidence, parents or [before, head_sha], candidate_parents or [before, source_sha], tree

    def run_post_merge_validation(self, event, evidence, parents, candidate_parents, tree):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            pr = evidence.get("pull_request") or {}
            fields = validator.parse_attestation_fields(str(pr.get("body") or ""))
            grant = {
                "id": fields.get("Grant-ID", "R3-GOV-HOM-012-O2-REQ2"),
                "status": "REQUESTED_JIT_SINGLE_USE",
                "operation": fields.get("Operation", "O2 desarrollo -> certificacion"),
                "repository": "romelhc95/studiamatch",
                "base_ref": (pr.get("base") or {}).get("ref", "certificacion"),
                "head_ref": (pr.get("head") or {}).get("ref", "desarrollo"),
                "source_ref": fields.get("Source-Ref", "desarrollo"),
                "candidate_branch": (pr.get("head") or {}).get("ref", "promote/gov-hom-012-o2-req2"),
                "final_wp": fields.get("Final-WP", "WP-GOV-CI-012"),
                "base_sha_binding": "pull_request.base.sha",
                "source_sha_binding": "promotion_attestation.Source-SHA",
                "candidate_sha_binding": "pull_request.head.sha",
                "candidate_tree_binding": "tree(pull_request.head.sha)",
                "t_final_binding": "tree(promotion_attestation.Source-SHA)",
                "d_final_binding": "manifest.candidate_digest",
                "event_action": "opened",
                "run_attempt": 1,
                "single_use": True,
                "external_consumption_required": True,
                "required_merger": "romelhc95",
                "required_reviewer": "romelhc95-approver",
                "merger_reviewer_distinct": True,
                "approval_envelope_schema": "promotion-jit-envelope-v3",
                "allowed_side_effects": ["certification_branch_update"],
            }
            if fields.get("Operation", "").startswith("O3"):
                grant.update({"allowed_side_effects": ["main_branch_update", "cloudflare_pages_production_rebuild", "db_sync_detect_only"], "cloudflare_pages_production_rebuild_expected": True, "db_sync_detect_only_required": True, "db_sync_expected_result": "NO_DB_CHANGES"})
            if fields.get("Operation", "").startswith("O4"):
                grant["allowed_side_effects"] = ["certification_branch_update"]
                grant["blocked_until_o3_closed"] = True
            if fields.get("Operation", "").startswith("O5"):
                grant["allowed_side_effects"] = ["development_branch_update"]
            def fake_git_sha(args, root=ROOT):
                if args[:3] == ["show", "-s", "--format=%P"]:
                    ref = args[3]
                    if ref == event["after"]:
                        return " ".join(parents)
                    return " ".join(candidate_parents)
                if args[:2] == ["rev-parse", f"{event['after']}^{{tree}}"]:
                    return tree
                return tree
            with mock.patch.object(validator, "load_post_merge_evidence", return_value=evidence), \
                 mock.patch.object(validator, "load_o3_closure_artifact", return_value={"schema": "o3-closure-evidence-v1", "status": "CLOSED", "main_merge_sha": fields.get("Source-SHA", "f" * 40), "cloudflare_pages_app_id": 85455, "db_sync_app_id": 15368, "db_sync_result": "NO_DB_CHANGES", "db_changed": False, "apply_executed": False, "db_sync_artifact_head_sha": fields.get("Source-SHA", "f" * 40), "payload_sha256": "0" * 64}), \
                 mock.patch.object(validator, "load_manifest_by_id", return_value={"candidate_digest": "e" * 64}), \
                 mock.patch.object(validator, "load_promotion_grant", return_value=grant), \
                 mock.patch.object(validator, "compute_digest", return_value="e" * 64), \
                 mock.patch.object(validator, "git_sha", side_effect=fake_git_sha), \
                 mock.patch.object(validator, "git_is_ancestor", return_value=True):
                return validator.validate_post_merge_promotion_push(str(event_path), root=ROOT)

    def test_post_merge_promotion_push_accepts_o2_regression_shape(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        self.assertEqual(self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree), [])

    def test_post_merge_promotion_push_accepts_o2_o5_pairs(self):
        cases = [
            ("O2 desarrollo -> certificacion", "certificacion", "desarrollo", "promote/gov-hom-012-o2-req2"),
            ("O3 certificacion -> main", "main", "certificacion", "promote/gov-hom-012-o3-req2"),
            ("O4 main -> certificacion", "certificacion", "main", "promote/gov-hom-012-o4-req2"),
            ("O5 certificacion -> desarrollo", "desarrollo", "certificacion", "promote/gov-hom-012-o5-req2"),
        ]
        for operation, base_ref, source_ref, head_ref in cases:
            event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(operation=operation, base_ref=base_ref, source_ref=source_ref, head_ref=head_ref)
            self.assertEqual(self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree), [], operation)

    def test_post_merge_promotion_push_rejects_invalid_shapes(self):
        cases = [
            ({"parents": ["a" * 40]}, "POST_MERGE_NOT_MERGE_COMMIT"),
            ({"parents": ["0" * 40, "c" * 40]}, "POST_MERGE_FIRST_PARENT_MISMATCH"),
            ({"parents": ["a" * 40, "0" * 40]}, "POST_MERGE_SECOND_PARENT_MISMATCH"),
            ({"fork": True}, "POST_MERGE_REPOSITORY_INVALID"),
            ({"pair_override": ("main", "desarrollo", "promote/gov-hom-006-o2-req1")}, "POST_MERGE_PROMOTION_BRANCH_SUPERSEDED"),
            ({"checks": False}, "POST_MERGE_REQUIRED_CHECK_MISSING"),
            ({"merger": "romelhc95-approver"}, "POST_MERGE_MERGER_INVALID"),
            ({"reviewer": "romelhc95"}, "POST_MERGE_REVIEW_MISSING"),
            ({"final_wp": "WP-GOV-CI-006"}, "POST_MERGE_ATTESTATION_MISMATCH"),
            ({"grant_id": "R3-GOV-HOM-006-O2-REQ1"}, "POST_MERGE_GRANT_CONSUMED"),
            ({"approval_expiry": "2020-01-01T00:00:00Z"}, "POST_MERGE_APPROVAL_EXPIRED"),
        ]
        for kwargs, expected in cases:
            event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(**kwargs)
            self.assertIn(expected, self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree), kwargs)

    def test_post_merge_promotion_push_requires_protected_approval_values(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence.pop("protected_approval")
        self.assertIn("POST_MERGE_APPROVAL_ARTIFACT_INVALID", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_promotion_push_rejects_protected_approval_mismatch(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence["protected_approval"]["envelope_summary"]["approval_id_sha256"] = hashlib.sha256(b"other-jit").hexdigest()
        self.assertIn("POST_MERGE_APPROVAL_REFERENCE_MISMATCH", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_promotion_push_rejects_unassociated_check_runs(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        for check in evidence["checks"]:
            check["pull_requests"] = []
        self.assertEqual(self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree), [])

    def test_post_merge_promotion_push_requires_latest_associated_check_success(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence["checks"].append({"id": 3, "name": "Promotion Boundary", "status": "completed", "conclusion": "failure", "head_sha": "c" * 40, "started_at": "2026-08-23T01:09:00Z", "completed_at": "2026-08-23T01:10:00Z", "updated_at": "2026-08-23T01:10:00Z", "pull_requests": [{"number": 500}], "app": {"id": 15368}, "details_url": "https://github.com/romelhc95/studiamatch/actions/runs/1000/job/3"})
        self.assertIn("POST_MERGE_REQUIRED_CHECK_MISSING", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_pr437_merger_failure_is_explicit(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(merger="romelhc95-approver", pull_requests=[])
        evidence["pull_request"]["number"] = 437
        self.assertIn("POST_MERGE_MERGER_INVALID", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_corrected_pr437_shape_validates(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(merger="romelhc95", pull_requests=[])
        self.assertEqual(self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree), [])

    def raw_replay_fixture(self, name):
        return json.loads((ROOT / "tests" / "fixtures" / "governance" / "gov-ci12" / name).read_text(encoding="utf-8"))

    def test_replay_pr440_detects_invalid_merger_before_closure(self):
        raw = self.raw_replay_fixture("pr_440_raw.json")
        pr = raw["pull_request"]
        event = {"before": pr["base"]["sha"], "after": pr["merge_commit_sha"], "ref": "refs/heads/certificacion", "head_commit": {"timestamp": pr["merged_at"]}}
        evidence = {"pull_request": pr, "checks": raw["check_runs"], "reviews": raw["reviews"], "timeline": raw["timeline"], "workflow_runs": {}}
        parents = [pr["base"]["sha"], pr["head"]["sha"]]
        candidate_parents = [pr["base"]["sha"], "1bc36ae6a4381c5ceac5e30c3970c39099965bc3"]
        tree = "7df05c52da47855d62c082f7cfbd12ee1e38b965"
        self.assertIn("POST_MERGE_MERGER_INVALID", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_replay_pr443_is_frozen_without_mutation(self):
        raw = self.raw_replay_fixture("pr_443_raw.json")
        event = {"action": "reopened", "repository": {"full_name": "romelhc95/studiamatch", "id": 1}, "pull_request": raw["pull_request"]}
        grant = {"id": "R3-GOV-HOM-010-O2-REQ1", "operation": "O2 desarrollo -> certificacion", "base_ref": "certificacion", "source_ref": "desarrollo", "candidate_branch": "promote/gov-hom-010-o2-req1", "final_wp": "WP-GOV-CI-010", "approval_envelope_schema": "promotion-jit-envelope-v2", "allowed_side_effects": ["certification_branch_update"], "status": "REQUESTED_JIT_SINGLE_USE"}
        errors = self.run_promotion_validation(event, grant)
        self.assertIn("PROMOTION_PR_BLOCKED:443", errors)
        self.assertIn("PROMOTION_ACTION_INVALID", errors)

    def test_replay_pr445_is_frozen_and_hom011_consumed(self):
        raw = self.raw_replay_fixture("pr_445_raw.json")
        event = {"action": "opened", "repository": {"full_name": "romelhc95/studiamatch", "id": 1}, "pull_request": raw["pull_request"]}
        grant = {"id": "R3-GOV-HOM-011-O2-REQ1", "operation": "O2 desarrollo -> certificacion", "base_ref": "certificacion", "source_ref": "desarrollo", "candidate_branch": "promote/gov-hom-011-o2-req1", "final_wp": "WP-GOV-CI-011", "approval_envelope_schema": "promotion-jit-envelope-v1", "allowed_side_effects": ["certification_branch_update"], "status": "REQUESTED_JIT_SINGLE_USE"}
        errors = self.run_promotion_validation(event, grant)
        self.assertIn("PROMOTION_PR_BLOCKED:445", errors)
        self.assertIn("PROMOTION_GRANT_CONSUMED", errors)
        self.assertIn("PROMOTION_CANDIDATE_BRANCH_INVALID", errors)

    def test_post_merge_pr438_ordinary_desarrollo_merge_is_not_applicable(self):
        validator = load_validator()
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(base_ref="desarrollo", head_ref="governance/gov-ci-007")
        evidence["pull_request"]["body"] = """## Governance Attestation
Base-SHA: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Candidate-SHA: cccccccccccccccccccccccccccccccccccccccc
Approval-Level: R2
Approval-Expiry: 2026-08-25T23:59:59Z
"""
        event["ref"] = "refs/heads/desarrollo"
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            with mock.patch.object(validator, "load_post_merge_evidence", return_value=evidence), \
                 mock.patch.object(validator, "git_sha", return_value=" ".join(parents)):
                state, errors = validator.classify_post_merge_promotion_push(str(event_path), root=ROOT)
        self.assertEqual(state, "NOT_APPLICABLE")
        self.assertEqual(errors, ["POST_MERGE_NORMAL_PR_NOT_PROMOTION"])

    def test_post_merge_pr441_real_template_body_is_not_applicable(self):
        validator = load_validator()
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(base_ref="desarrollo", head_ref="governance/gov-ci-009")
        event["after"] = "17d383291a5f2877074b54b66f2a0ff48a643667"
        event["ref"] = "refs/heads/desarrollo"
        evidence["pull_request"].update({
            "number": 441,
            "merge_commit_sha": event["after"],
            "body": """## Governance Attestation

Completar solo para PR R1/R2 normales hacia `desarrollo`. En PR O2-O5, dejar esta seccion sin valores o removerla; `security-audit` solo valida una seccion por tipo de PR.

Base-SHA: 1bc36ae6a4381c5ceac5e30c3970c39099965bc3
Candidate-SHA: 4d2452ff868819f53385c5b0a4b71c530a309f9d
Estado-Snapshot: SNAPSHOT-2026-08-23-GOV-CI9-R1-CANDIDATE
Requerimiento: REQ-EST-001
Hito: GOV-CI9
TASK: TASK-GOV-CI-009
WP: WP-GOV-CI-009
WP-Digest: 6f9d309d50b90c18a2703cd6b9170af9af9048f7d80ef749a22a95e8dd8a32ef
Approval-Level: R2
Approval-Expiry: 2026-09-04T23:59:59Z
Architecture-Snapshot: desarrollo@1bc36ae6a4381c5ceac5e30c3970c39099965bc3
Data-Architecture-Snapshot: desarrollo@1bc36ae6a4381c5ceac5e30c3970c39099965bc3
Adoption-Matrix-Snapshot: desarrollo@1bc36ae6a4381c5ceac5e30c3970c39099965bc3
Architecture-Impact: updated
Architecture-Impact-Reason: GOV-CI9 owner-only branch update governance and workflow documentation.
Data-Impact: updated
Data-Impact-Reason: No DB schema or Supabase changes; DB adoption matrix updated for no-change governance state.
Security-Auditor: clean

## Promotion Attestation

Completar solo para promociones O2-O5 con ramas runtime `promote/gov-hom-009-oN`. En PR R1/R2 normales, dejar esta seccion sin valores o removerla; sus campos no deben contaminar la Governance Attestation.

Operation:
Grant-ID: nuevo-unico-no-consumido
Base-Ref:
Base-SHA:
Source-Ref:
Source-SHA:
Candidate-SHA:
Candidate-Tree:
Final-WP:
D_FINAL:
T_FINAL:
Approval-Level:
Approval-Reference:
Approval-Expiry:
""",
            "base": {"ref": "desarrollo", "sha": "1bc36ae6a4381c5ceac5e30c3970c39099965bc3", "repo": {"full_name": "romelhc95/studiamatch"}},
            "head": {"ref": "governance/gov-ci-009", "sha": "4d2452ff868819f53385c5b0a4b71c530a309f9d", "repo": {"full_name": "romelhc95/studiamatch"}},
        })
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            with mock.patch.object(validator, "load_post_merge_evidence", return_value=evidence), \
                 mock.patch.object(validator, "git_sha", return_value=" ".join(parents)):
                state, errors = validator.classify_post_merge_promotion_push(str(event_path), root=ROOT)
        self.assertEqual(state, "NOT_APPLICABLE")
        self.assertEqual(errors, ["POST_MERGE_NORMAL_PR_NOT_PROMOTION"])

    def test_post_merge_direct_push_is_blocked_even_with_one_parent(self):
        validator = load_validator()
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        event["ref"] = "refs/heads/desarrollo"
        parents = ["a" * 40]
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            with mock.patch.object(validator, "load_post_merge_evidence", return_value={}), \
                 mock.patch.object(validator, "git_sha", return_value=" ".join(parents)):
                state, errors = validator.classify_post_merge_promotion_push(str(event_path), root=ROOT)
        self.assertEqual(state, "BLOCKED")
        self.assertEqual(errors, ["POST_MERGE_PR_MISMATCH"])

    def test_post_merge_ordinary_upper_branch_pr_is_blocked(self):
        validator = load_validator()
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(base_ref="main", head_ref="governance/gov-ci-007")
        evidence["pull_request"]["body"] = "ordinary governance PR"
        event["ref"] = "refs/heads/main"
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            with mock.patch.object(validator, "load_post_merge_evidence", return_value=evidence), \
                 mock.patch.object(validator, "git_sha", return_value=" ".join(parents)):
                state, errors = validator.classify_post_merge_promotion_push(str(event_path), root=ROOT)
        self.assertEqual(state, "BLOCKED")
        self.assertEqual(errors, ["POST_MERGE_PROTECTED_BRANCH_NON_PROMOTION"])

    def test_post_merge_superseded_hom007_branch_is_blocked(self):
        validator = load_validator()
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(head_ref="promote/gov-hom-007-o2-req1")
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            with mock.patch.object(validator, "load_post_merge_evidence", return_value=evidence), \
                 mock.patch.object(validator, "git_sha", return_value=" ".join(parents)):
                state, errors = validator.classify_post_merge_promotion_push(str(event_path), root=ROOT)
        self.assertEqual(state, "BLOCKED")
        self.assertEqual(errors, ["POST_MERGE_PROMOTION_BRANCH_SUPERSEDED"])

    def test_post_merge_blocks_wrong_app_id_and_pr_association(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence["checks"][0]["app"] = {"id": 1}
        self.assertIn("POST_MERGE_REQUIRED_CHECK_MISSING", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(pull_requests=[{"number": 501}])
        self.assertIn("POST_MERGE_CHECK_PR_ASSOCIATION_INVALID", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_rejects_workflow_run_mismatch_and_freshness(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence["workflow_runs"]["1000"]["event"] = "push"
        self.assertIn("POST_MERGE_WORKFLOW_EVENT_INVALID", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence["timeline"] = [{"event": "edited", "created_at": "2026-08-23T01:10:00Z", "changes": {"body": {"from": "old"}}}]
        self.assertIn("POST_MERGE_ATTESTATION_STALE", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_rejects_latest_review_state(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture(review_state="CHANGES_REQUESTED")
        self.assertIn("POST_MERGE_REVIEW_STATE_INVALID", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence["reviews"][0].pop("commit_id")
        self.assertIn("POST_MERGE_REVIEW_COMMIT_INVALID", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_promotion_push_rejects_missing_associated_pr(self):
        event, evidence, parents, candidate_parents, tree = self.post_merge_fixture()
        evidence["pull_request"] = {}
        self.assertIn("POST_MERGE_PR_MISMATCH", self.run_post_merge_validation(event, evidence, parents, candidate_parents, tree))

    def test_post_merge_evidence_loads_full_pull_request(self):
        validator = load_validator()
        calls = []
        def fake_api(path, **kwargs):
            calls.append(path)
            if path.startswith("commits/") and "pulls" in path:
                return [{"number": 500, "head": {"sha": "summary"}}]
            if path == "pulls/500":
                return {"number": 500, "merged": True, "head": {"sha": "c" * 40}}
            if path.startswith("commits/") and "check-runs" in path:
                return [{"name": "Promotion Boundary"}]
            if path == "pulls/500/reviews?per_page=100":
                return []
            if path == "issues/500/timeline?per_page=100":
                return []
            raise AssertionError(path)
        with mock.patch.object(validator, "github_api_json", side_effect=fake_api):
            evidence = validator.load_post_merge_evidence("b" * 40)
        self.assertTrue(evidence["pull_request"]["merged"])
        self.assertIn("pulls/500", calls)

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
