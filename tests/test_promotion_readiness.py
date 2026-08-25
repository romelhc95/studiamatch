import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


VALID_SNAPSHOT = {
    "snapshot_source": "github-api",
    "environment": {"name": "Promotion", "can_admins_bypass": False, "prevent_self_review": True, "deployment_branch_policy": None, "reviewer": "romelhc95-approver", "reviewer_id": 306979205},
    "ruleset": {"name": "owner-only-protected-branch-updates", "enforcement": "active", "restrict_updates": True, "bypass_actor_count": 1, "bypass_actors_observable": True, "protected_refs": ["refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"], "bypass_user": "romelhc95", "excluded_user": "romelhc95-approver"},
    "active_promotions": ["500"],
    "current_pr": "500",
    "cloudflare_pages_app_id": 85455,
}


def load_readiness():
    path = ROOT / "scripts" / "security" / "validate_promotion_readiness.py"
    spec = importlib.util.spec_from_file_location("validate_promotion_readiness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromotionReadinessTests(unittest.TestCase):
    def test_readiness_rejects_empty_snapshot(self):
        readiness = load_readiness()
        errors = readiness.validate_readiness({}, root=ROOT)
        self.assertIn("READINESS_ENVIRONMENT_MISSING", errors)
        self.assertIn("READINESS_RULESET_MISSING", errors)
        self.assertIn("READINESS_ACTIVE_PROMOTIONS_MISSING", errors)

    def test_readiness_accepts_complete_remote_snapshot(self):
        readiness = load_readiness()
        self.assertEqual(readiness.validate_readiness(VALID_SNAPSHOT, root=ROOT), [])

    def test_readiness_rejects_admin_bypass(self):
        readiness = load_readiness()
        snapshot = {**VALID_SNAPSHOT, "environment": {"name": "Promotion", "can_admins_bypass": True, "prevent_self_review": True, "deployment_branch_policy": None, "reviewer": "romelhc95-approver", "reviewer_id": 306979205}}
        errors = readiness.validate_readiness(snapshot, root=ROOT)
        self.assertIn("READINESS_ENVIRONMENT_ADMIN_BYPASS_INVALID", errors)

    def test_readiness_rejects_wrong_cloudflare_app(self):
        readiness = load_readiness()
        snapshot = {**VALID_SNAPSHOT, "cloudflare_pages_app_id": 1}
        errors = readiness.validate_readiness(snapshot, root=ROOT)
        self.assertIn("READINESS_CLOUDFLARE_APP_INVALID", errors)

    def test_readiness_requires_o4_block(self):
        readiness = load_readiness()
        errors = readiness.validate_readiness(VALID_SNAPSHOT, root=ROOT)
        self.assertNotIn("READINESS_O4_NOT_BLOCKED", errors)

    def test_readiness_allows_unobservable_bypass_actors(self):
        readiness = load_readiness()
        snapshot = {**VALID_SNAPSHOT, "ruleset": {**VALID_SNAPSHOT["ruleset"], "bypass_actors_observable": False, "bypass_actor_count": "UNOBSERVABLE"}}
        self.assertEqual(readiness.validate_readiness(snapshot, root=ROOT), [])

    def test_readiness_o4_loads_real_o3_closure_gate(self):
        readiness = load_readiness()
        snapshot = {**VALID_SNAPSHOT, "current_pr_head_ref": "promote/gov-hom-012-o4-req2", "current_pr_source_sha": "f" * 40}
        with mock.patch.object(readiness, "load_o3_closure_artifact", return_value={"main_merge_sha": "f" * 40, "db_changed": False, "apply_executed": False}) as loader:
            self.assertEqual(readiness.validate_readiness(snapshot, root=ROOT), [])
        loader.assert_called_once_with("f" * 40)

    def test_readiness_o4_fails_without_o3_closure(self):
        readiness = load_readiness()
        snapshot = {**VALID_SNAPSHOT, "current_pr_head_ref": "promote/gov-hom-012-o4-req2", "current_pr_source_sha": "f" * 40}
        with mock.patch.object(readiness, "load_o3_closure_artifact", side_effect=RuntimeError("missing")):
            errors = readiness.validate_readiness(snapshot, root=ROOT)
        self.assertIn("READINESS_O4_O3_CLOSURE_UNAVAILABLE", errors)

    def test_readiness_rejects_persisted_pr_body(self):
        readiness = load_readiness()
        snapshot = {**VALID_SNAPSHOT, "current_pr_body": "## Promotion Attestation"}
        self.assertIn("READINESS_BODY_FORBIDDEN", readiness.validate_readiness(snapshot, root=ROOT))

    def test_readiness_rejects_frozen_prs(self):
        readiness = load_readiness()
        snapshot = {**VALID_SNAPSHOT, "active_promotions": ["447"], "current_pr": "447"}
        self.assertIn("READINESS_FROZEN_PR_INVALID", readiness.validate_readiness(snapshot, root=ROOT))


if __name__ == "__main__":
    unittest.main()
