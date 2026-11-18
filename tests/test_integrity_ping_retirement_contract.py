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
    def __init__(
        self,
        course,
        extra_base_courses=None,
        extra_public_courses=None,
        concurrent_change=False,
        revoke_public_on_recheck=False,
        write_error=None,
    ):
        self.base_courses = [dict(course)] + [dict(row) for row in extra_base_courses or []]
        self.public_courses = [
            {key: course[key] for key in ("id", "institution_id", "name", "url")}
        ] + [
            {key: row[key] for key in ("id", "institution_id", "name", "url")}
            for row in extra_public_courses or []
        ]
        self.patches = []
        self.filters = []
        self.selects = []
        self.transitions = []
        self.concurrent_change = concurrent_change
        self.revoke_public_on_recheck = revoke_public_on_recheck
        self.write_error = write_error

    def count_service_raise(self, table, filters=None):
        assert table == "courses_public_effective"
        assert "or=(syllabus.is.null,objectives.is.null)" in filters
        return 0

    def select_service_raise(self, table, filters, **kwargs):
        self.filters.append(filters)
        self.selects.append((table, filters, kwargs))
        if table == "courses_public_effective":
            assert filters.startswith("id=eq.")
            if self.revoke_public_on_recheck:
                return []
            course_id = filters.removeprefix("id=eq.")
            return [row.copy() for row in self.public_courses if row["id"] == course_id]

        assert table == "courses"
        assert filters.startswith("id=in.(")
        selected_ids = set(filters.removeprefix("id=in.(").removesuffix(")").split(","))
        return [row.copy() for row in self.base_courses if row["id"] in selected_ids]

    def select_all_service(self, table, filters, **kwargs):
        self.filters.append(filters)
        self.selects.append((table, filters, kwargs))
        assert table == "courses_public_effective"
        return [dict(row) for row in self.public_courses]

    def rpc_once_raise(self, function_name, params):
        assert function_name == "fg3_apply_public_course_transition"
        self.transitions.append(dict(params))
        if self.write_error is not None:
            raise self.write_error
        if self.concurrent_change or self.revoke_public_on_recheck:
            return [{"outcome": "stale", "resulting_last_404_at": None}]

        row = next(row for row in self.base_courses if row["id"] == params["p_course_id"])
        if params["p_action"] == "start_404_grace":
            row["last_404_at"] = "database-generated-observation"
        elif params["p_action"] == "clear_404_grace":
            row["last_404_at"] = None
        elif params["p_action"] == "deactivate_after_grace":
            row["is_active"] = False
        else:
            raise AssertionError(f"unexpected transition action: {params['p_action']}")
        self.patches.append(("courses", dict(params)))
        return [{
            "outcome": "applied",
            "resulting_last_404_at": row.get("last_404_at"),
            "resulting_is_active": row.get("is_active"),
        }]


def run_with(
    course,
    status,
    extra_base_courses=None,
    extra_public_courses=None,
    concurrent_change=False,
    revoke_public_on_recheck=False,
    write_error=None,
):
    db = FakeDb(
        course,
        extra_base_courses,
        extra_public_courses,
        concurrent_change,
        revoke_public_on_recheck,
        write_error,
    )
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
            "institution_id": "synthetic-institution",
            "name": "Synthetic editorial course",
            "url": "https://institution.example/course",
            "last_404_at": last_404_at,
            "is_active": True,
            "is_verified": True,
            "syllabus": "Published syllabus stays unchanged",
            "objectives": "Published objectives stay unchanged",
            "start_date": "2025-01-01",
            # These values are intentionally irrelevant to FG3 retirement.
            "availability_status": "unknown",
            "availability_valid_until": "2025-01-01T00:00:00+00:00",
        }

    def test_old_date_expired_enrollment_and_transient_http_do_not_deactivate(self):
        result, db = run_with(self.course(), 503)

        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertFalse(any("start_date" in filters for filters in db.filters))
        self.assertFalse(any("availability" in filters for filters in db.filters))

    def test_http_200_alone_does_not_claim_catalog_membership_or_deactivate(self):
        result, db = run_with(self.course(), 200)

        self.assertEqual(result, 0)
        self.assertFalse(db.transitions)

    def test_transient_failure_does_not_confirm_removal_even_after_grace(self):
        old_marker = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        result, db = run_with(self.course(old_marker), 503)

        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)

    def test_first_404_only_starts_grace_and_persistent_410_confirms_removal(self):
        original = self.course()
        _, first_observation = run_with(original, 404)
        self.assertEqual(len(first_observation.patches), 1)
        self.assertEqual(first_observation.transitions[0]["p_action"], "start_404_grace")
        self.assertEqual(first_observation.transitions[0]["p_http_status"], 404)
        self.assertEqual(first_observation.transitions[0]["p_observed_last_404_at"], None)
        for field in ("name", "syllabus", "objectives", "start_date"):
            self.assertEqual(first_observation.base_courses[0][field], original[field])
        self.assertTrue(first_observation.base_courses[0]["is_active"])

        old_marker = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        _, confirmed = run_with(self.course(old_marker), 410)
        self.assertEqual(len(confirmed.patches), 1)
        self.assertEqual(confirmed.transitions[0]["p_action"], "deactivate_after_grace")
        self.assertEqual(confirmed.transitions[0]["p_http_status"], 410)
        self.assertFalse(confirmed.base_courses[0]["is_active"])
        for field in ("name", "syllabus", "objectives", "start_date"):
            self.assertEqual(confirmed.base_courses[0][field], self.course(old_marker)[field])

    def test_selects_public_view_and_reads_base_state_only_for_selected_ids(self):
        private_course = self.course()
        private_course.update({
            "id": "private-course",
            "url": "https://institution.example/private",
            "is_verified": False,
        })
        _, db = run_with(self.course(), 200, extra_base_courses=[private_course])

        self.assertEqual(db.selects[0][0], "courses_public_effective")
        self.assertEqual(len(db.selects), 2)
        self.assertEqual(db.selects[1][0], "courses")
        self.assertEqual(db.selects[1][1], "id=in.(synthetic-course)")
        self.assertNotIn("private-course", db.selects[1][1])
        self.assertFalse(db.transitions)

    def test_success_after_prior_404_clears_only_the_removal_marker(self):
        old_marker = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        original = self.course(old_marker)
        _, db = run_with(original, 200)

        self.assertEqual(len(db.transitions), 1)
        self.assertEqual(db.transitions[0]["p_action"], "clear_404_grace")
        self.assertEqual(db.transitions[0]["p_http_status"], 200)
        self.assertEqual(db.transitions[0]["p_observed_last_404_at"], old_marker)
        self.assertIsNone(db.base_courses[0]["last_404_at"])
        for field in ("name", "syllabus", "objectives", "start_date"):
            self.assertEqual(db.base_courses[0][field], original[field])

    def test_concurrent_base_change_makes_atomic_transition_a_no_op(self):
        result, db = run_with(self.course(), 404, concurrent_change=True)

        self.assertEqual(result, 0)
        self.assertEqual(len(db.transitions), 1)
        self.assertFalse(db.patches)
        self.assertEqual(db.transitions[0]["p_course_id"], "synthetic-course")
        self.assertEqual(db.transitions[0]["p_institution_id"], "synthetic-institution")
        self.assertEqual(db.transitions[0]["p_url"], "https://institution.example/course")
        self.assertIsNone(db.transitions[0]["p_observed_last_404_at"])

    def test_public_view_revocation_inside_atomic_transition_causes_zero_write(self):
        result, db = run_with(self.course(), 404, revoke_public_on_recheck=True)

        self.assertEqual(result, 0)
        self.assertEqual(len(db.transitions), 1)
        self.assertFalse(db.patches)
        self.assertEqual(db.transitions[0]["p_action"], "start_404_grace")

    def test_rejected_atomic_write_stops_the_remaining_batch(self):
        second = self.course()
        second.update({
            "id": "second-course",
            "url": "https://institution.example/second",
        })
        result, db = run_with(
            self.course(),
            404,
            extra_base_courses=[second],
            extra_public_courses=[second],
            write_error=integrity_ping.DatabaseAPIError("synthetic HTTP 400"),
        )

        self.assertEqual(result, 1)
        self.assertEqual(len(db.transitions), 1)
        self.assertFalse(db.patches)


if __name__ == "__main__":
    import unittest

    unittest.main()
