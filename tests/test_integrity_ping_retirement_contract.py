from datetime import datetime, timedelta, timezone
import socket
import ssl
from unittest import TestCase
from unittest.mock import Mock, patch
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


def run_with_http_sequence(
    course,
    events,
    write_error=None,
    sleep_error=None,
    monotonic_error=None,
):
    db = FakeDb(course, write_error=write_error)
    requests = []
    event_queue = list(events)
    logger = Mock()
    sleeper = Mock(side_effect=sleep_error)

    def request(url, method='HEAD', timeout=10, budget=None):
        requests.append((method, url))
        if not event_queue:
            raise AssertionError("unexpected extra HTTP request")
        event = event_queue.pop(0)
        if isinstance(event, BaseException):
            raise event
        if isinstance(event, tuple):
            status_code, headers = event
        else:
            status_code, headers = event, {}
        return integrity_ping.PinnedHTTPResponse(status_code, headers, url)

    with (
        patch.object(integrity_ping, "get_db_client", return_value=db),
        patch.object(integrity_ping, "TimeGuard", FakeTimeGuard),
        patch.object(integrity_ping, "is_safe_public_url", return_value=True),
        patch.object(integrity_ping, "request_pinned_public_url", side_effect=request),
        patch.object(integrity_ping.time, "sleep", sleeper),
        patch.object(integrity_ping, "logger", logger),
    ):
        if monotonic_error is None:
            result = integrity_ping.run_integrity_ping()
        else:
            with patch.object(
                integrity_ping.time,
                "monotonic",
                side_effect=monotonic_error,
            ):
                result = integrity_ping.run_integrity_ping()

    log_lines = []
    for level in ("info", "warning", "error"):
        for call in getattr(logger, level).call_args_list:
            template, *args = call.args
            log_lines.append(template % tuple(args) if args else str(template))
    logs = "\n".join(log_lines)
    return result, db, requests, logs, sleeper


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
        self.assertEqual(db.transitions[0]["p_course_id"], "synthetic-course")
        self.assertEqual(db.transitions[0]["p_institution_id"], "synthetic-institution")
        self.assertEqual(db.transitions[0]["p_url"], "https://institution.example/course")
        self.assertIsNone(db.transitions[0]["p_observed_last_404_at"])


class IntegrityPingWpRem07Contract(TestCase):
    def course(self, last_404_at=None):
        return {
            "id": "synthetic-course-id",
            "institution_id": "synthetic-institution-id",
            "name": "Synthetic public course",
            "url": "https://institution.example/course",
            "last_404_at": last_404_at,
            "is_active": True,
            "is_verified": True,
            "syllabus": "Published syllabus stays unchanged",
            "objectives": "Published objectives stay unchanged",
        }

    def test_head_403_get_fallback_persistent_403_is_inconclusive_and_has_zero_writes(self):
        result, db, requests, logs, _ = run_with_http_sequence(self.course(), [403, 403])

        self.assertEqual([method for method, _ in requests], ["HEAD", "GET"])
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertIn("course_id=synthetic-course-id", logs)
        self.assertIn("http_status_inconclusive", logs)
        self.assertIn("http_status=403", logs)

    def test_head_404_requires_get_confirmation_before_any_transition(self):
        result, db, requests, logs, _ = run_with_http_sequence(self.course(), [404, 200])

        self.assertEqual([method for method, _ in requests], ["HEAD", "GET"])
        self.assertEqual(result, 0)
        self.assertFalse(db.transitions)

        result, db, requests, logs, _ = run_with_http_sequence(self.course(), [404, 403])
        self.assertEqual([method for method, _ in requests], ["HEAD", "GET"])
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertIn("http_status_inconclusive", logs)

    def test_head_404_get_404_records_transition_by_id(self):
        result, db, requests, logs, _ = run_with_http_sequence(self.course(), [404, 404])

        self.assertEqual([method for method, _ in requests], ["HEAD", "GET"])
        self.assertEqual(result, 0)
        self.assertEqual(len(db.transitions), 1)
        self.assertEqual(db.transitions[0]["p_action"], "start_404_grace")
        self.assertIn("course_id=synthetic-course-id", logs)
        self.assertIn("action=start_404_grace", logs)

    def test_head_410_get_410_confirms_only_after_existing_grace(self):
        old_marker = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        result, db, requests, logs, _ = run_with_http_sequence(
            self.course(old_marker), [410, 410]
        )

        self.assertEqual([method for method, _ in requests], ["HEAD", "GET"])
        self.assertEqual(result, 0)
        self.assertEqual(db.transitions[0]["p_action"], "deactivate_after_grace")
        self.assertFalse(db.base_courses[0]["is_active"])
        self.assertIn("action=deactivate_after_grace", logs)

    def test_405_and_501_keep_bounded_get_fallback(self):
        for status in (405, 501):
            with self.subTest(status=status):
                result, db, requests, _, _ = run_with_http_sequence(self.course(), [status, 200])
                self.assertEqual([method for method, _ in requests], ["HEAD", "GET"])
                self.assertEqual(result, 0)
                self.assertFalse(db.transitions)

        result, db, requests, _, _ = run_with_http_sequence(
            self.course(), [501, 501, 200]
        )
        self.assertEqual([method for method, _ in requests], ["HEAD", "GET", "GET"])
        self.assertEqual(result, 0)
        self.assertFalse(db.transitions)

    def test_retryable_statuses_share_three_http_attempt_budget(self):
        result, db, requests, logs, sleeper = run_with_http_sequence(
            self.course(), [503, 429, 503]
        )

        self.assertEqual([method for method, _ in requests], ["HEAD", "HEAD", "HEAD"])
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertEqual([call.args[0] for call in sleeper.call_args_list], [1, 2])
        self.assertIn("attempts_exhausted", logs)

    def test_unlisted_server_5xx_is_still_retried(self):
        result, db, requests, _, _ = run_with_http_sequence(self.course(), [507, 200])

        self.assertEqual([method for method, _ in requests], ["HEAD", "HEAD"])
        self.assertEqual(result, 0)
        self.assertFalse(db.transitions)

    def test_runtime_error_in_backoff_keeps_phase_and_sanitizes_exception(self):
        result, db, requests, logs, _ = run_with_http_sequence(
            self.course(),
            [503],
            sleep_error=RuntimeError("BACKOFF_SENTINEL private details"),
        )

        self.assertEqual([method for method, _ in requests], ["HEAD"])
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertIn("phase=retry_backoff", logs)
        self.assertIn("category=unexpected_runtime_error", logs)
        self.assertNotIn("BACKOFF_SENTINEL", logs)
        self.assertNotIn("private details", logs)

    def test_runtime_error_reading_time_budget_has_time_budget_phase(self):
        result, db, requests, logs, _ = run_with_http_sequence(
            self.course(),
            [],
            monotonic_error=RuntimeError("TIME_SENTINEL private details"),
        )

        self.assertEqual(requests, [])
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertIn("phase=time_budget", logs)
        self.assertIn("category=unexpected_runtime_error", logs)
        self.assertNotIn("TIME_SENTINEL", logs)
        self.assertNotIn("private details", logs)

    def test_retry_after_delay_uses_a_total_per_url_delay_budget(self):
        result, db, requests, logs, sleeper = run_with_http_sequence(
            self.course(),
            [(429, {"Retry-After": "20"}), (503, {"Retry-After": "20"})],
        )

        self.assertEqual([method for method, _ in requests], ["HEAD", "HEAD"])
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertEqual([call.args[0] for call in sleeper.call_args_list], [20])
        self.assertIn("retry_after_budget_exhausted", logs)

    def test_dns_failure_retries_with_sanitized_id_level_diagnostic(self):
        result, db, requests, logs, _ = run_with_http_sequence(
            self.course(), [socket.gaierror("DNS_SENTINEL private.example"), 200]
        )

        self.assertEqual([method for method, _ in requests], ["HEAD", "HEAD"])
        self.assertEqual(result, 0)
        self.assertFalse(db.transitions)
        self.assertIn("course_id=synthetic-course-id", logs)
        self.assertIn("dns_resolution:dns_failure", logs)
        self.assertNotIn("DNS_SENTINEL", logs)
        self.assertNotIn("private.example", logs)

    def test_dns_runtime_error_keeps_dns_phase_and_sanitizes_exception(self):
        db = FakeDb(self.course())
        logger = Mock()
        with (
            patch.object(integrity_ping, "get_db_client", return_value=db),
            patch.object(integrity_ping, "TimeGuard", FakeTimeGuard),
            patch.object(integrity_ping, "logger", logger),
            patch.object(
                integrity_ping.socket,
                "getaddrinfo",
                side_effect=RuntimeError("DNS_RUNTIME_SENTINEL private body"),
            ),
        ):
            result = integrity_ping.run_integrity_ping()

        logs = "\n".join(
            call.args[0] % call.args[1:] if call.args[1:] else str(call.args[0])
            for call in logger.warning.call_args_list
        )
        self.assertEqual(result, 1)
        self.assertIn("course_id=synthetic-course-id", logs)
        self.assertIn("phase=dns_resolution", logs)
        self.assertIn("category=unexpected_runtime_error", logs)
        self.assertNotIn("DNS_RUNTIME_SENTINEL", logs)
        self.assertNotIn("private body", logs)

    def test_tls_failure_retries_with_phase_and_category(self):
        result, db, requests, logs, _ = run_with_http_sequence(
            self.course(), [ssl.SSLError("TLS_SENTINEL"), 200]
        )

        self.assertEqual([method for method, _ in requests], ["HEAD", "HEAD"])
        self.assertEqual(result, 0)
        self.assertFalse(db.transitions)
        self.assertIn("tls_handshake:tls_failure", logs)
        self.assertIn("retry_backoff:exponential_backoff", logs)
        self.assertNotIn("TLS_SENTINEL", logs)

    def test_unclassified_runtime_error_is_diagnostic_without_exception_text(self):
        course = self.course()
        course["url"] = "https://private-sentinel.example/course?token=URL_SENTINEL"
        result, db, requests, logs, _ = run_with_http_sequence(
            course,
            [RuntimeError("RUNTIME_SENTINEL credential and body must stay private")],
        )

        self.assertEqual([method for method, _ in requests], ["HEAD"])
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertIn("phase=http_request", logs)
        self.assertIn("category=unexpected_runtime_error", logs)
        self.assertIn("course_id=synthetic-course-id", logs)
        for sentinel in ("RUNTIME_SENTINEL", "URL_SENTINEL", "private-sentinel.example", "credential"):
            self.assertNotIn(sentinel, logs)

    def test_redirect_requests_consume_the_same_total_attempt_budget(self):
        redirects = [
            (302, {"Location": "https://institution.example/one"}),
            (302, {"Location": "https://institution.example/two"}),
            (302, {"Location": "https://institution.example/three"}),
        ]
        result, db, requests, logs, _ = run_with_http_sequence(self.course(), redirects)

        self.assertEqual(len(requests), 3)
        self.assertEqual(result, 1)
        self.assertFalse(db.transitions)
        self.assertIn("redirect_limit", logs)

    def test_redirect_to_private_address_is_rejected_before_following(self):
        response = integrity_ping.PinnedHTTPResponse(
            302,
            {"Location": "https://127.0.0.1/private"},
            "https://institution.example/course",
        )
        with patch.object(
            integrity_ping, "request_pinned_public_url", return_value=response
        ) as request:
            with self.assertRaises(integrity_ping.ProbeFailure) as raised:
                integrity_ping.fetch_public_url("https://institution.example/course")

        self.assertEqual(request.call_count, 1)
        self.assertEqual(raised.exception.phase, "redirect_validation")
        self.assertEqual(raised.exception.category, "unsafe_target")

    def test_userinfo_target_is_rejected_before_request(self):
        with patch.object(integrity_ping, "request_pinned_public_url") as request:
            with self.assertRaises(integrity_ping.ProbeFailure) as raised:
                integrity_ping.fetch_public_url(
                    "https://credential-sentinel@institution.example/course"
                )

        self.assertEqual(raised.exception.category, "unsafe_target")
        request.assert_not_called()

    def test_expired_total_budget_stops_before_http_request(self):
        trace = integrity_ping.ProbeTrace(
            started_at=integrity_ping.time.monotonic() - integrity_ping.MAX_URL_PROBE_SECONDS
        )
        with patch.object(integrity_ping, "request_pinned_public_url") as request:
            with self.assertRaises(integrity_ping.ProbeFailure) as raised:
                integrity_ping.fetch_public_url(
                    "https://institution.example/course", budget=trace
                )

        self.assertEqual(raised.exception.category, "time_budget_exhausted")
        self.assertEqual(raised.exception.phase, "time_budget")
        request.assert_not_called()

    def test_unknown_write_result_is_never_retried(self):
        result, db, requests, logs, _ = run_with_http_sequence(
            self.course(),
            [404, 404],
            write_error=integrity_ping.DatabaseWriteOutcomeUnknown("WRITE_SENTINEL"),
        )

        self.assertEqual([method for method, _ in requests], ["HEAD", "GET"])
        self.assertEqual(result, 1)
        self.assertEqual(len(db.transitions), 1)
        self.assertIn("course_id=synthetic-course-id", logs)
        self.assertNotIn("WRITE_SENTINEL", logs)

    def test_runtime_error_during_write_stops_batch_without_retrying(self):
        second = self.course()
        second.update({
            "id": "second-course-id",
            "url": "https://institution.example/second",
        })
        db = FakeDb(
            self.course(),
            extra_base_courses=[second],
            extra_public_courses=[second],
            write_error=RuntimeError("WRITE_RUNTIME_SENTINEL"),
        )
        responses = [
            integrity_ping.PinnedHTTPResponse(404, {}, "https://institution.example/course"),
            integrity_ping.PinnedHTTPResponse(404, {}, "https://institution.example/course"),
        ]
        logger = Mock()
        with (
            patch.object(integrity_ping, "get_db_client", return_value=db),
            patch.object(integrity_ping, "TimeGuard", FakeTimeGuard),
            patch.object(integrity_ping, "is_safe_public_url", return_value=True),
            patch.object(integrity_ping, "fetch_public_url", side_effect=responses),
            patch.object(integrity_ping, "logger", logger),
        ):
            result = integrity_ping.run_integrity_ping()

        self.assertEqual(result, 1)
        self.assertEqual(len(db.transitions), 1)
        self.assertNotIn("WRITE_RUNTIME_SENTINEL", str(logger.warning.call_args_list))


if __name__ == "__main__":
    import unittest

    unittest.main()
