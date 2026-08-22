import importlib.util
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9"
HEAD_SHA = "2eb8fcdda1224146c8013d6a050f56edf4e63194"
SYNTHETIC_MERGE_SHA = "3" * 40
VALID_BODY = """Base-SHA: 96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9
Estado-Snapshot: SNAPSHOT-2026-08-22-GOV-ARCH-R2-PENDING
Requerimiento: REQ-EST-001
Hito: GOV-ARCH
TASK: TASK-GOV-ARCH-001
WP: WP-GOV-ARCH-001
WP-Digest: 0000000000000000000000000000000000000000000000000000000000000000
Approval-Level: R2
Approval-Expiry: 2026-08-28T23:59:59Z
Architecture-Snapshot: desarrollo@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9
Data-Architecture-Snapshot: desarrollo@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9
Adoption-Matrix-Snapshot: desarrollo@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9
Architecture-Impact: updated
Architecture-Impact-Reason: Canonical docs updated.
Data-Impact: updated
Data-Impact-Reason: Data architecture docs updated.
Security-Auditor: clean
"""


def load_validator():
    path = ROOT / "scripts" / "security" / "validate_change_governance.py"
    spec = importlib.util.spec_from_file_location("validate_change_governance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChangeGovernanceTests(unittest.TestCase):
    def run_validate(self, body=VALID_BODY, base_ref="desarrollo", head_ref="governance/gov-arch-001", paths=None, head_sha=HEAD_SHA, pr_head_sha=HEAD_SHA, ancestry=True, base_for_diff=BASE_SHA):
        validator = load_validator()
        manifest = validator.load_manifest("WP-GOV-ARCH-001")
        body = body.replace("0" * 64, manifest["candidate_digest"])
        with patch.object(validator, "changed_paths", return_value=paths or [".context/arquitectura_pipeline.md", ".context/sistema_db_supabase.md", ".context/operaciones/matriz_adopcion_db.md"]) as changed, patch.object(validator, "git_sha", return_value=head_sha), patch.object(validator, "git_is_ancestor", return_value=ancestry):
            errors = validator.validate(
                body=body,
                base_ref=base_ref,
                head_ref=head_ref,
                base_sha=BASE_SHA,
                base_for_diff=base_for_diff,
                pr_head_sha=pr_head_sha,
                now=datetime(2026, 8, 22, tzinfo=UTC),
            )
        if pr_head_sha and all(c in "0123456789abcdef" for c in pr_head_sha) and len(pr_head_sha) == 40 and base_for_diff == BASE_SHA:
            changed.assert_called_with(BASE_SHA, pr_head_sha, root=validator.ROOT)
        return errors

    def run_validate_with_module(self, body=VALID_BODY, base_ref="desarrollo", head_ref="governance/gov-arch-001", paths=None, head_sha=HEAD_SHA, pr_head_sha=HEAD_SHA, ancestry=True, base_for_diff=BASE_SHA):
        validator = load_validator()
        manifest = validator.load_manifest("WP-GOV-ARCH-001")
        body = body.replace("0" * 64, manifest["candidate_digest"])
        with patch.object(validator, "changed_paths", return_value=paths or [".context/arquitectura_pipeline.md", ".context/sistema_db_supabase.md", ".context/operaciones/matriz_adopcion_db.md"]), patch.object(validator, "git_sha", return_value=head_sha), patch.object(validator, "git_is_ancestor", return_value=ancestry):
            return validator.validate(
                body=body,
                base_ref=base_ref,
                head_ref=head_ref,
                base_sha=BASE_SHA,
                base_for_diff=BASE_SHA,
                pr_head_sha=pr_head_sha,
                now=datetime(2026, 8, 22, tzinfo=UTC),
            )

    def test_valid_attestation_passes(self):
        self.assertEqual(self.run_validate(), [])

    def test_missing_field_fails(self):
        body = VALID_BODY.replace("TASK: TASK-GOV-ARCH-001", "TASK:")
        self.assertTrue(any(error.startswith("GOVERNANCE_PREFLIGHT_FIELD_REQUIRED:TASK") for error in self.run_validate(body=body)))

    def test_bad_digest_fails(self):
        body = VALID_BODY.replace("0" * 64, "1" * 64)
        self.assertTrue(any(error.startswith("GOVERNANCE_WP_DIGEST_MISMATCH") for error in self.run_validate(body=body)))

    def test_unknown_wp_fails(self):
        body = VALID_BODY.replace("WP: WP-GOV-ARCH-001", "WP: WP-UNKNOWN-001")
        self.assertTrue(any(error.startswith("GOVERNANCE_WP_NOT_FOUND") for error in self.run_validate(body=body)))

    def test_expired_approval_fails(self):
        body = VALID_BODY.replace("2026-08-28T23:59:59Z", "2020-01-01T00:00:00Z")
        self.assertTrue(any(error.startswith("GOVERNANCE_APPROVAL_EXPIRED") for error in self.run_validate(body=body)))

    def test_non_desarrollo_base_fails(self):
        self.assertTrue(any(error.startswith("GOVERNANCE_BASE_REF_INVALID") for error in self.run_validate(base_ref="main")))

    def test_bad_branch_fails(self):
        self.assertTrue(any(error.startswith("GOVERNANCE_BRANCH_INVALID") for error in self.run_validate(head_ref="tmp/work")))

    def test_db_change_requires_data_docs(self):
        body = VALID_BODY.replace("Data-Impact: updated", "Data-Impact: none").replace("Data-Impact-Reason: Data architecture docs updated.", "Data-Impact-Reason:")
        errors = self.run_validate(body=body, paths=["db/migrations/20260822.sql"])
        self.assertTrue(any(error.startswith("GOVERNANCE_DATA_COCHANGE_REQUIRED") for error in errors))

    def test_workflow_change_requires_architecture(self):
        body = VALID_BODY.replace("Architecture-Impact: updated", "Architecture-Impact: none").replace("Architecture-Impact-Reason: Canonical docs updated.", "Architecture-Impact-Reason:")
        errors = self.run_validate(body=body, paths=[".github/workflows/production_pipeline.yml"])
        self.assertTrue(any(error.startswith("GOVERNANCE_ARCHITECTURE_COCHANGE_REQUIRED") for error in errors))

    def test_web_change_requires_architecture(self):
        body = VALID_BODY.replace("Architecture-Impact: updated", "Architecture-Impact: none").replace("Architecture-Impact-Reason: Canonical docs updated.", "Architecture-Impact-Reason:")
        errors = self.run_validate(body=body, paths=["web/src/app/page.tsx"])
        self.assertTrue(any(error.startswith("GOVERNANCE_ARCHITECTURE_COCHANGE_REQUIRED") for error in errors))

    def test_comment_only_exception_does_not_bypass_runtime_path(self):
        body = VALID_BODY.replace("Architecture-Impact: updated", "Architecture-Impact: none")
        body = body.replace("Architecture-Impact-Reason: Canonical docs updated.", "Architecture-Impact-Reason: Comment-only change does not alter runtime.")
        self.assertTrue(any(error.startswith("GOVERNANCE_ARCHITECTURE_COCHANGE_REQUIRED") for error in self.run_validate(body=body, paths=["web/src/app/page.tsx"])))

    def test_stale_branch_fails(self):
        validator = load_validator()
        manifest = validator.load_manifest("WP-GOV-ARCH-001")
        body = VALID_BODY.replace("0" * 64, manifest["candidate_digest"])
        with patch.object(validator, "changed_paths", return_value=[".context/arquitectura_pipeline.md"]), patch.object(validator, "git_sha", return_value=HEAD_SHA), patch.object(validator, "git_is_ancestor", return_value=False):
            errors = validator.validate(body=body, base_ref="desarrollo", head_ref="governance/gov-arch-001", base_sha=BASE_SHA, base_for_diff=BASE_SHA, pr_head_sha=HEAD_SHA, now=datetime(2026, 8, 22, tzinfo=UTC))
        self.assertTrue(any(error.startswith("GOVERNANCE_BRANCH_NOT_BASED_ON_DECLARED_BASE") for error in errors))

    def test_synthetic_merge_checkout_fails(self):
        errors = self.run_validate(head_sha=SYNTHETIC_MERGE_SHA, pr_head_sha=HEAD_SHA)
        self.assertTrue(any(error.startswith("GOVERNANCE_HEAD_SHA_MISMATCH") for error in errors))

    def test_invalid_head_sha_fails_closed(self):
        errors = self.run_validate(pr_head_sha="")
        self.assertTrue(any(error.startswith("GOVERNANCE_HEAD_SHA_INVALID") for error in errors))

    def test_diff_base_must_match_event_base(self):
        errors = self.run_validate(base_for_diff="a" * 40)
        self.assertTrue(any(error.startswith("GOVERNANCE_DIFF_BASE_MISMATCH") for error in errors))

    def test_git_ancestry_error_fails_closed(self):
        errors = self.run_validate(ancestry=None)
        self.assertTrue(any(error.startswith("GOVERNANCE_GIT_VALIDATION_FAILED") for error in errors))

    def test_required_human_review_fails_without_review(self):
        validator = load_validator()
        manifest = validator.load_manifest("WP-GOV-ARCH-001")
        body = VALID_BODY.replace("0" * 64, manifest["candidate_digest"])
        with patch.object(validator, "changed_paths", return_value=[".context/arquitectura_pipeline.md"]), patch.object(validator, "git_sha", return_value=HEAD_SHA), patch.object(validator, "git_is_ancestor", return_value=True), patch.object(validator, "latest_human_approval", return_value=None):
            errors = validator.validate(body=body, base_ref="desarrollo", head_ref="governance/gov-arch-001", base_sha=BASE_SHA, base_for_diff=BASE_SHA, pr_head_sha=HEAD_SHA, now=datetime(2026, 8, 22, tzinfo=UTC), event_path="event.json", require_approved_review=True)
        self.assertTrue(any(error.startswith("GOVERNANCE_HUMAN_APPROVAL_REVIEW_REQUIRED") for error in errors))

    def test_review_must_match_digest_head_and_actor(self):
        validator = load_validator()
        digest = validator.load_manifest("WP-GOV-ARCH-001")["candidate_digest"]
        valid = {"state": "APPROVED", "commit_id": HEAD_SHA, "body": f"approved {digest}", "user": {"login": "reviewer"}}
        self.assertTrue(validator.review_is_valid(valid, author="author", digest=digest, head_sha=HEAD_SHA))
        invalid_cases = [
            {**valid, "state": "DISMISSED"},
            {**valid, "commit_id": "a" * 40},
            {**valid, "body": "approved wrong digest"},
            {**valid, "user": {"login": "author"}},
            {**valid, "user": {"login": "bot[bot]"}},
        ]
        for review in invalid_cases:
            self.assertFalse(validator.review_is_valid(review, author="author", digest=digest, head_sha=HEAD_SHA))

    def test_workflow_scopes_preflight_to_desarrollo(self):
        workflow = (ROOT / ".github" / "workflows" / "security-audit.yml").read_text(encoding="utf-8")
        self.assertIn("github.event.pull_request.base.ref == 'desarrollo'", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha }}", workflow)
        self.assertIn("pull_request:desarrollo|pull_request_review:desarrollo", workflow)
        self.assertIn("pull_request:certificacion|pull_request:main|pull_request_review:certificacion|pull_request_review:main|push:", workflow)

    def test_r3_level_requires_separate_jit(self):
        body = VALID_BODY.replace("Approval-Level: R2", "Approval-Level: R3")
        errors = self.run_validate(body=body)
        self.assertTrue(any(error.startswith("GOVERNANCE_R3_JIT_NOT_SUPPORTED_BY_PREFLIGHT") for error in errors))

    def test_lower_approval_level_does_not_satisfy_r2_gate(self):
        body = VALID_BODY.replace("Approval-Level: R2", "Approval-Level: R1")
        errors = self.run_validate(body=body)
        self.assertTrue(any(error.startswith("GOVERNANCE_APPROVAL_LEVEL_MISMATCH") for error in errors))

    def test_latest_human_approval_returns_reviewer_login(self):
        validator = load_validator()
        digest = validator.load_manifest("WP-GOV-ARCH-001")["candidate_digest"]
        event_path = ROOT / "tests" / "tmp_event.json"
        event_path.write_text('{"pull_request":{"number":1,"user":{"login":"author"}}}', encoding="utf-8")

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return ('[{"state":"APPROVED","commit_id":"' + HEAD_SHA + '","body":"' + digest + '","user":{"login":"reviewer"}}]').encode("utf-8")

        try:
            with patch.dict("os.environ", {"GITHUB_TOKEN": "token", "GITHUB_REPOSITORY": "owner/repo"}), patch.object(validator.urllib.request, "urlopen", return_value=Response()):
                self.assertEqual(validator.latest_human_approval(str(event_path), digest=digest, head_sha=HEAD_SHA), "reviewer")
        finally:
            event_path.unlink(missing_ok=True)

    def test_legacy_phase_prompt_fails(self):
        body = VALID_BODY + "\nEjecuta las tareas pendientes de la Fase F12.1\n"
        self.assertTrue(any(error.startswith("GOVERNANCE_LEGACY_PHASE_AUTHORIZATION") for error in self.run_validate(body=body)))


if __name__ == "__main__":
    unittest.main()
