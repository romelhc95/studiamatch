from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import patch

from scripts.core import integrity_ping


class FakeTimeGuard:
    should_exit = False
    elapsed_hours = 0

    def __init__(self, *args, **kwargs):
        pass

    def tick(self, *args, **kwargs):
        pass


class FakeDb:
    def __init__(self, course):
        self.course = course
        self.patches = []
        self.filters = []

    def count_service_raise(self, table):
        return 1

    def select_service_raise(self, table, filters, **kwargs):
        self.filters.append(filters)
        if "or=(syllabus.is.null,objectives.is.null)" in filters:
            return []
        raise AssertionError(f"unexpected bounded select: {filters}")

    def select_all_service(self, table, filters, **kwargs):
        self.filters.append(filters)
        return [self.course]

    def patch_exact_one_raise(self, table, filters, data, expected_id):
        self.patches.append((table, filters, data, expected_id))
        return [{"id": expected_id}]


def run_with(course, status):
    db = FakeDb(course)
    response = integrity_ping.PinnedHTTPResponse(status, {}, course["url"])
    with (
        patch.object(integrity_ping, "get_db_client", return_value=db),
        patch.object(integrity_ping, "TimeGuard", FakeTimeGuard),
        patch.object(integrity_ping, "is_safe_public_url", return_value=True),
        patch.object(integrity_ping, "fetch_public_url", return_value=response),
    ):
        result = integrity_ping.run_integrity_ping()
    return result, db


class IntegrityPingRetirementContract(TestCase):
    def course(self, last_404_at=None):
        return {
            "id": "synthetic-course",
            "name": "Synthetic editorial course",
            "url": "https://institution.example/course",
            "last_404_at": last_404_at,
            # These values are intentionally irrelevant to FG3 retirement.
            "start_date": "2025-01-01",
            "availability_status": "unknown",
            "availability_valid_until": "2025-01-01T00:00:00+00:00",
        }

    def test_old_date_expired_enrollment_and_transient_http_do_not_deactivate(self):
        result, db = run_with(self.course(), 503)

        self.assertEqual(result, 1)
        self.assertFalse(any(data.get("is_active") is False for _, _, data, _ in db.patches))
        self.assertFalse(any("start_date" in filters for filters in db.filters))
        self.assertFalse(any("availability" in filters for filters in db.filters))

    def test_http_200_alone_does_not_claim_catalog_membership_or_deactivate(self):
        result, db = run_with(self.course(), 200)

        self.assertEqual(result, 0)
        self.assertFalse(any(data.get("is_active") is False for _, _, data, _ in db.patches))

    def test_transient_failure_does_not_confirm_removal_even_after_grace(self):
        old_marker = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        result, db = run_with(self.course(old_marker), 503)

        self.assertEqual(result, 1)
        self.assertFalse(any(data.get("is_active") is False for _, _, data, _ in db.patches))
        self.assertFalse(any(data.get("last_404_at") is None for _, _, data, _ in db.patches))

    def test_first_404_only_starts_grace_and_persistent_410_confirms_removal(self):
        _, first_observation = run_with(self.course(), 404)
        self.assertEqual(len(first_observation.patches), 1)
        self.assertIn("last_404_at", first_observation.patches[0][2])
        self.assertFalse(any(data.get("is_active") is False for _, _, data, _ in first_observation.patches))

        old_marker = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        _, confirmed = run_with(self.course(old_marker), 410)
        self.assertEqual(len(confirmed.patches), 1)
        self.assertEqual(confirmed.patches[0][2], {"is_active": False})


if __name__ == "__main__":
    import unittest

    unittest.main()
