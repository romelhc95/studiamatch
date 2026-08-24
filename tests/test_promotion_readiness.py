import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


VALID_SNAPSHOT = {
    "snapshot_source": "github-api",
    "environment": {"name": "Promotion", "can_admins_bypass": False, "reviewer": "romelhc95-approver"},
    "ruleset": {"name": "owner-only-protected-branch-updates", "enforcement": "active", "restrict_updates": True, "bypass_actor_count": 1, "protected_refs": ["refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"], "bypass_user": "romelhc95", "excluded_user": "romelhc95-approver"},
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
        snapshot = {**VALID_SNAPSHOT, "environment": {"name": "Promotion", "can_admins_bypass": True, "reviewer": "romelhc95-approver"}}
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


if __name__ == "__main__":
    unittest.main()
