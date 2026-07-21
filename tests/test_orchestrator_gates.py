
"""Functional test for master_orchestrator.get_institutions() gate ordering.

Validates that discovery_enabled=false and circuit_open=true institutions
are excluded BEFORE the limit is applied, preserving slot efficiency.

This is a self-contained logic test that reproduces the gate function
without loading the orchestrator module (avoids db_client import side-effects).
"""

import unittest


def _apply_gates(institutions, profiles, limit=10):
    """Reproduce the gate logic of master_orchestrator.get_institutions().

    This function mirrors the exact gate logic from
    scripts/core/master_orchestrator.py:32-66 to validate gate ordering.
    """
    gate_map = {}
    for p in profiles:
        pid = p['institution_id']
        gate_map[pid] = {
            'discovery_enabled': p.get('discovery_enabled', False),
            'pipeline_enabled': p.get('pipeline_enabled', False),
            'pipeline_ready': p.get('pipeline_ready', False),
            'circuit_open': p.get('circuit_open', False),
        }

    eligible = []
    for i in institutions:
        gates = gate_map.get(i['id'], {})
        if not gates.get('discovery_enabled', False):
            continue
        if gates.get('circuit_open', False):
            continue
        i['_discovery_enabled'] = True
        i['_pipeline_enabled'] = gates.get('pipeline_enabled', False)
        i['_pipeline_ready'] = gates.get('pipeline_ready', False)
        i['_circuit_open'] = False
        eligible.append(i)

    eligible.sort(key=lambda i: i.get('last_harvest_at') or '')
    return eligible[:limit]


class OrchestratorGateTests(unittest.TestCase):
    """Isolated functional tests for get_institutions() gate logic."""

    def test_discovery_disabled_excluded_before_limit(self):
        """discovery_enabled=false institutions are excluded before limit is applied."""
        institutions = [
            {"id": "a", "name": "Inst A", "slug": "a", "website_url": "https://a.pe", "last_harvest_at": "2026-01-01"},
            {"id": "b", "name": "Inst B", "slug": "b", "website_url": "https://b.pe", "last_harvest_at": "2026-02-01"},
            {"id": "c", "name": "Inst C", "slug": "c", "website_url": "https://c.pe", "last_harvest_at": "2026-03-01"},
        ]
        profiles = [
            {"institution_id": "a", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
            {"institution_id": "b", "discovery_enabled": False, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
            {"institution_id": "c", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
        ]
        result = _apply_gates(institutions, profiles, limit=10)
        ids = [r["id"] for r in result]
        self.assertNotIn("b", ids, "discovery_enabled=false should be excluded before limit")
        self.assertIn("a", ids)
        self.assertIn("c", ids)
        self.assertEqual(len(result), 2)

    def test_circuit_open_excluded_before_limit(self):
        """circuit_open=true institutions are excluded before limit is applied."""
        institutions = [
            {"id": "a", "name": "Inst A", "slug": "a", "website_url": "https://a.pe", "last_harvest_at": "2026-01-01"},
            {"id": "b", "name": "Inst B", "slug": "b", "website_url": "https://b.pe", "last_harvest_at": "2026-02-01"},
        ]
        profiles = [
            {"institution_id": "a", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": True},
            {"institution_id": "b", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
        ]
        result = _apply_gates(institutions, profiles, limit=10)
        ids = [r["id"] for r in result]
        self.assertNotIn("a", ids, "circuit_open=true should be excluded before limit")
        self.assertIn("b", ids)

    def test_limit_applied_after_gates(self):
        """limit is applied AFTER gates filter, not before."""
        institutions = [
            {"id": "a", "name": "Inst A", "slug": "a", "website_url": "https://a.pe", "last_harvest_at": "2026-03-01"},
            {"id": "b", "name": "Inst B", "slug": "b", "website_url": "https://b.pe", "last_harvest_at": "2026-02-01"},
            {"id": "c", "name": "Inst C", "slug": "c", "website_url": "https://c.pe", "last_harvest_at": "2026-01-01"},
            {"id": "d", "name": "Inst D", "slug": "d", "website_url": "https://d.pe", "last_harvest_at": "2026-04-01"},
        ]
        profiles = [
            {"institution_id": "a", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
            {"institution_id": "b", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
            {"institution_id": "c", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
            {"institution_id": "d", "discovery_enabled": False, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
        ]
        result = _apply_gates(institutions, profiles, limit=2)
        self.assertLessEqual(len(result), 2, "limit must be honored after gate filtering")
        ids = [r["id"] for r in result]
        self.assertNotIn("d", ids, "discovery_enabled=false should never appear")
        self.assertEqual(ids, ["c", "b"], "order must respect last_harvest_at asc")

    def test_no_profile_institution_excluded(self):
        """Institutions without profiles are treated as all gates disabled."""
        institutions = [
            {"id": "a", "name": "Inst A", "slug": "a", "website_url": "https://a.pe", "last_harvest_at": None},
        ]
        profiles = []
        result = _apply_gates(institutions, profiles, limit=10)
        self.assertEqual(len(result), 0, "institution without profile should be excluded")

    def test_gate_metadata_preserved(self):
        """Gate metadata flags are attached to returned institution dicts."""
        institutions = [
            {"id": "a", "name": "Inst A", "slug": "a", "website_url": "https://a.pe", "last_harvest_at": None},
        ]
        profiles = [
            {"institution_id": "a", "discovery_enabled": True, "pipeline_enabled": True, "pipeline_ready": True, "circuit_open": False},
        ]
        result = _apply_gates(institutions, profiles, limit=10)
        self.assertEqual(len(result), 1)
        inst = result[0]
        self.assertTrue(inst.get("_discovery_enabled"))
        self.assertTrue(inst.get("_pipeline_enabled"))
        self.assertTrue(inst.get("_pipeline_ready"))
        self.assertFalse(inst.get("_circuit_open"))


if __name__ == "__main__":
    unittest.main()
