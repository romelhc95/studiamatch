from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import unquote

import pytest

from scripts.shared.f10_9_fg3_atomic import CourseState, probe_course, run_fg3_atomic
from scripts.shared.safe_http import UnsafeURL


NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def response(status: int, **headers: str) -> SimpleNamespace:
    return SimpleNamespace(status_code=status, headers=headers)


def row(
    course_id: str,
    *,
    url: str | None = None,
    active: bool = True,
    last_404_at: str | None = None,
    start_date: str | None = None,
) -> dict[str, object]:
    return {
        "id": course_id,
        "url": url or f"https://{course_id}.sentinel.invalid/program?payload=secret",
        "is_active": active,
        "last_404_at": last_404_at,
        "start_date": start_date,
    }


class FakeDB:
    def __init__(self, rows: list[dict[str, object]]):
        self.rows = {str(item["id"]): deepcopy(item) for item in rows}
        self.collection_rows = deepcopy(rows)
        self.patch_calls: list[dict[str, object]] = []
        self.select_all_calls: list[dict[str, object]] = []
        self.patch_behaviors: list[str] = []
        self.read_override = None
        self.collection_error = False

    def count_service_raise(self, table, *, filters):
        if self.collection_error:
            raise RuntimeError("sensitive count failure")
        return sum(1 for item in self.rows.values() if item["is_active"])

    def select_all_service(self, table, **kwargs):
        self.select_all_calls.append({"table": table, **kwargs})
        if self.collection_error:
            raise RuntimeError("sensitive collection failure")
        return [deepcopy(item) for item in self.rows.values() if item["is_active"]]

    def select_service_raise(self, table, *, filters, columns, limit, order):
        course_id = unquote(filters.split("id=eq.", 1)[1].split("&", 1)[0])
        if self.read_override is not None:
            override = self.read_override(course_id)
            if override is not None:
                return deepcopy(override)
        item = self.rows.get(course_id)
        if item is None:
            return []
        return [
            {
                "id": item["id"],
                "is_active": item["is_active"],
                "last_404_at": item["last_404_at"],
                "url": item["url"],
                "start_date": item["start_date"],
            }
        ]

    def patch_exact_one_raise(self, table, *, filters, data, expected_id):
        self.patch_calls.append(
            {"table": table, "filters": filters, "data": deepcopy(data), "expected_id": expected_id}
        )
        behavior = self.patch_behaviors.pop(0) if self.patch_behaviors else "apply"
        item = self.rows[str(expected_id)]
        expected_active = "is_active=eq.true" in filters
        expected_last = item["last_404_at"]
        if "last_404_at=is.null" in filters:
            filter_matches_last = expected_last is None
        else:
            encoded = filters.split("last_404_at=eq.", 1)[1].split("&", 1)[0]
            filter_matches_last = str(expected_last) == unquote(encoded)
        if item["is_active"] != expected_active or not filter_matches_last:
            raise RuntimeError("DB patch expected exactly one row for courses, got 0")
        expected_url = unquote(filters.split("url=eq.", 1)[1].split("&", 1)[0])
        if item["url"] != expected_url:
            raise RuntimeError("DB patch expected exactly one row for courses, got 0")
        if "start_date=is.null" in filters:
            filter_matches_start = item["start_date"] is None
        else:
            expected_start = unquote(filters.split("start_date=eq.", 1)[1].split("&", 1)[0])
            filter_matches_start = item["start_date"] == expected_start
        if not filter_matches_start:
            raise RuntimeError("DB patch expected exactly one row for courses, got 0")
        if behavior == "unchanged_zero":
            raise RuntimeError("DB patch expected exactly one row for courses, got 0")
        if behavior == "conflict":
            item["last_404_at"] = "2026-01-01T00:00:00Z"
            raise RuntimeError("DB patch expected exactly one row for courses, got 0")
        if behavior == "url_conflict":
            item["url"] = "https://changed.invalid/program"
            raise RuntimeError("DB patch expected exactly one row for courses, got 0")
        item.update(data)
        if behavior == "unknown_after_apply":
            raise RuntimeError("DB_MUTATION_OUTCOME_UNKNOWN")
        return deepcopy(item)


class DuplicateDB(FakeDB):
    def count_service_raise(self, table, *, filters):
        return len(self.collection_rows)

    def select_all_service(self, table, **kwargs):
        self.select_all_calls.append({"table": table, **kwargs})
        return deepcopy(self.collection_rows)


class SequenceGuard:
    def __init__(self, values: list[bool]):
        self.values = list(values)

    @property
    def should_exit(self):
        return self.values.pop(0) if self.values else False


def no_sleep(_seconds: float) -> None:
    return None


def test_head_2xx_is_healthy_without_get_and_recovery_second_run_is_noop():
    db = FakeDB([row("course-a", last_404_at="2026-08-09T00:00:00Z")])
    calls = {"head": 0, "get": 0}

    def head(_url, **_kwargs):
        calls["head"] += 1
        return response(204)

    def get(_url, **_kwargs):
        calls["get"] += 1
        raise AssertionError("GET must not follow healthy HEAD")

    first = run_fg3_atomic(db, head=head, get=get, sleeper=no_sleep, now=NOW)
    second = run_fg3_atomic(db, head=head, get=get, sleeper=no_sleep, now=NOW)

    assert first.exit_code == 0
    assert first.result == "APPLIED_VERIFIED"
    assert db.rows["course-a"]["last_404_at"] is None
    assert second.result == "NOOP"
    assert len(db.patch_calls) == 1
    assert calls == {"head": 2, "get": 0}


@pytest.mark.parametrize("head_status", [403, 405, 501, 404, 410])
def test_head_statuses_requiring_get_are_bounded(head_status):
    calls = []
    course = CourseState("opaque", "https://sentinel.invalid", True, None, None)

    result = probe_course(
        course,
        head=lambda *_args, **_kwargs: calls.append("HEAD") or response(head_status),
        get=lambda *_args, **_kwargs: calls.append("GET") or response(200),
        sleeper=no_sleep,
    )

    assert result.classification == "HEALTHY"
    assert result.attempts == 2
    assert calls == ["HEAD", "GET"]


@pytest.mark.parametrize("gone", [404, 410])
def test_gone_mutates_only_after_get_confirms_gone(gone):
    db = FakeDB([row("course-gone")])
    calls = []

    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: calls.append("HEAD") or response(gone),
        get=lambda *_args, **_kwargs: calls.append("GET") or response(gone),
        sleeper=no_sleep,
        now=NOW,
    )

    assert result.result == "APPLIED_VERIFIED"
    assert calls == ["HEAD", "GET"]
    assert db.rows["course-gone"]["last_404_at"] == "2026-08-10T12:00:00Z"
    assert db.patch_calls[0]["data"] == {"last_404_at": "2026-08-10T12:00:00Z"}


def test_head_gone_get_healthy_does_not_mutate():
    db = FakeDB([row("course-a")])
    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: response(404),
        get=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.result == "NOOP"
    assert db.patch_calls == []


def test_invalid_persisted_gone_timestamp_stops_before_apply():
    db = FakeDB([row("course-a", last_404_at="not-a-timestamp")])
    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: response(404),
        get=lambda *_args, **_kwargs: response(410),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.exit_code == 1
    assert result.result == "AGGREGATE_ERROR"
    assert db.patch_calls == []


def test_403_persistent_is_globally_inconclusive_and_expiration_is_not_written_early():
    db = FakeDB(
        [
            row("course-expired", start_date="2020-01-01"),
            row("course-blocked"),
        ]
    )

    def head(url, **_kwargs):
        return response(403) if "blocked" in url else response(200)

    result = run_fg3_atomic(
        db,
        head=head,
        get=lambda *_args, **_kwargs: response(403),
        sleeper=no_sleep,
        now=NOW,
    )

    assert result.exit_code == 1
    assert result.result == "INCONCLUSIVE"
    assert db.patch_calls == []
    assert db.rows["course-expired"]["is_active"] is True
    assert result.manifest["aggregate"]["planned"] == 0


@pytest.mark.parametrize("status", [408, 425, 429, 500, 503])
def test_transient_http_has_three_attempt_budget_and_injected_backoff(status):
    calls = []
    sleeps = []
    result = probe_course(
        CourseState("opaque", "https://sentinel.invalid", True, None, None),
        head=lambda *_args, **_kwargs: calls.append(status) or response(status),
        get=lambda *_args, **_kwargs: pytest.fail("unexpected GET"),
        sleeper=sleeps.append,
    )
    assert result.classification == "INCONCLUSIVE"
    assert result.attempts == 3
    assert calls == [status, status, status]
    assert len(sleeps) == 2
    assert max(sleeps) <= 1.0


@pytest.mark.parametrize(
    "reason",
    ["SAFE_TOTAL_TIMEOUT", "SAFE_DNS_FAILURE", "SAFE_TLS_VERIFY", "SAFE_TRANSPORT_FAILURE"],
)
def test_transient_safe_http_errors_retry_three_times(reason):
    calls = []

    def failing(*_args, **_kwargs):
        calls.append(reason)
        raise UnsafeURL(reason)

    result = probe_course(
        CourseState("opaque", "https://sentinel.invalid", True, None, None),
        head=failing,
        get=failing,
        sleeper=no_sleep,
    )
    assert result.attempts == 3
    assert result.reason == "HTTP_TRANSIENT_EXHAUSTED"
    assert len(calls) == 3


def test_unsafe_redirect_is_not_retried_and_blocks_all_writes():
    db = FakeDB([row("course-expired", start_date="2020-01-01")])
    calls = []

    def unsafe(*_args, **_kwargs):
        calls.append(1)
        raise UnsafeURL("SAFE_REDIRECT_DOWNGRADE")

    result = run_fg3_atomic(db, head=unsafe, get=unsafe, sleeper=no_sleep, now=NOW)
    assert result.exit_code == 1
    assert result.result == "INCONCLUSIVE"
    assert len(calls) == 1
    assert db.patch_calls == []


def test_duplicate_id_and_collection_error_fail_before_probe_or_patch():
    duplicate = DuplicateDB([row("duplicate"), row("duplicate", url="https://other.invalid")])
    probes = []
    duplicate_result = run_fg3_atomic(
        duplicate,
        head=lambda *_args, **_kwargs: probes.append(1) or response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert duplicate_result.result == "DUPLICATE_ID"
    assert probes == []
    assert duplicate.patch_calls == []

    failed = FakeDB([row("course-a")])
    failed.collection_error = True
    collection_result = run_fg3_atomic(
        failed,
        head=lambda *_args, **_kwargs: probes.append(1) or response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert collection_result.result == "COLLECTION_ERROR"
    assert failed.patch_calls == []


def test_count_drift_and_partial_pagination_fail_before_probe_or_patch():
    class CountDriftDB(FakeDB):
        def __init__(self, rows):
            super().__init__(rows)
            self.counts = [1, 2]

        def count_service_raise(self, table, *, filters):
            return self.counts.pop(0)

    drift = CountDriftDB([row("course-a")])
    probes = []
    result = run_fg3_atomic(
        drift,
        head=lambda *_args, **_kwargs: probes.append(1) or response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.result == "COLLECTION_ERROR"
    assert probes == []
    assert drift.patch_calls == []

    class PartialDB(FakeDB):
        def select_all_service(self, table, **kwargs):
            return []

    partial = PartialDB([row("course-a")])
    result = run_fg3_atomic(
        partial,
        head=lambda *_args, **_kwargs: probes.append(1) or response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.result == "COLLECTION_ERROR"
    assert probes == []
    assert partial.patch_calls == []


def test_time_guard_during_probe_and_immediately_before_apply_produce_zero_patches():
    during = FakeDB([row("a"), row("b")])
    during_result = run_fg3_atomic(
        during,
        head=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
        guard=SequenceGuard([False, True]),
    )
    assert during_result.result == "TIME_GUARD"
    assert during.patch_calls == []

    before = FakeDB([row("expired", start_date="2020-01-01")])
    before_result = run_fg3_atomic(
        before,
        head=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
        guard=SequenceGuard([False, True]),
    )
    assert before_result.result == "TIME_GUARD_BEFORE_APPLY"
    assert before.patch_calls == []
    assert before.rows["expired"]["is_active"] is True
    assert before_result.manifest["aggregate"]["planned"] == 1


def test_conditional_exact_one_reconciles_already_applied_without_retry():
    db = FakeDB([row("course-a", last_404_at="2026-08-09T00:00:00Z")])
    db.patch_behaviors = ["unknown_after_apply"]
    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.result == "APPLIED_VERIFIED"
    assert result.manifest["apply"]["outcomes"] == {"ALREADY_APPLIED": 1}
    assert len(db.patch_calls) == 1
    assert "is_active=eq.true" in db.patch_calls[0]["filters"]
    assert "last_404_at=eq." in db.patch_calls[0]["filters"]
    assert "url=eq." in db.patch_calls[0]["filters"]
    assert "start_date=is.null" in db.patch_calls[0]["filters"]


@pytest.mark.parametrize("behavior,expected_outcome", [("unchanged_zero", "OUTCOME_UNKNOWN"), ("conflict", "CONFLICT")])
def test_zero_row_reconciliation_never_retries_mutation(behavior, expected_outcome):
    db = FakeDB([row("course-a", last_404_at="2026-08-09T00:00:00Z")])
    db.patch_behaviors = [behavior]
    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.result == "PARTIAL_APPLY_STOP"
    assert result.manifest["apply"]["outcomes"] == {expected_outcome: 1}
    assert len(db.patch_calls) == 1


def test_mid_apply_failure_is_partial_apply_stop_and_never_success():
    db = FakeDB(
        [
            row("a", last_404_at="2026-08-09T00:00:00Z"),
            row("b", last_404_at="2026-08-09T00:00:00Z"),
            row("c", last_404_at="2026-08-09T00:00:00Z"),
        ]
    )
    db.patch_behaviors = ["apply", "unchanged_zero", "apply"]
    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.exit_code == 1
    assert result.result == "PARTIAL_APPLY_STOP"
    assert len(db.patch_calls) == 2
    assert db.rows["a"]["last_404_at"] is None
    assert db.rows["b"]["last_404_at"] is not None
    assert db.rows["c"]["last_404_at"] is not None
    assert result.manifest["transactionality"] == "CONDITIONAL_EXACT_ONE_NOT_GLOBAL_DB_TRANSACTION"


def test_concurrent_url_change_is_conflict_and_never_applied_from_stale_probe():
    db = FakeDB([row("course-a", last_404_at="2026-08-09T00:00:00Z")])
    db.patch_behaviors = ["url_conflict"]
    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.result == "PARTIAL_APPLY_STOP"
    assert result.manifest["apply"]["outcomes"] == {"CONFLICT": 1}
    assert len(db.patch_calls) == 1


def test_persistent_gone_deactivation_and_expiration_are_verified_then_noop():
    old_gone = (NOW - timedelta(days=4)).isoformat().replace("+00:00", "Z")
    db = FakeDB(
        [
            row("gone", last_404_at=old_gone),
            row("expired", start_date="2020-01-01"),
        ]
    )

    def head(url, **_kwargs):
        return response(404) if "gone" in url else response(200)

    first = run_fg3_atomic(
        db,
        head=head,
        get=lambda *_args, **_kwargs: response(410),
        sleeper=no_sleep,
        now=NOW,
    )
    second = run_fg3_atomic(
        db,
        head=head,
        get=lambda *_args, **_kwargs: response(410),
        sleeper=no_sleep,
        now=NOW,
    )
    assert first.result == "APPLIED_VERIFIED"
    assert first.manifest["verify"]["desired_states_verified"] == 2
    assert db.rows["gone"]["is_active"] is False
    assert db.rows["expired"]["is_active"] is False
    assert second.result == "NOOP"


def test_more_than_1000_rows_use_paginated_adapter_and_complete_offline():
    db = FakeDB([row(f"course-{index:04d}") for index in range(1001)])
    result = run_fg3_atomic(
        db,
        head=lambda *_args, **_kwargs: response(200),
        sleeper=no_sleep,
        now=NOW,
    )
    assert result.result == "NOOP"
    assert result.manifest["collection"]["rows"] == 1001
    assert result.manifest["probe"]["attempts"] == 1001
    assert db.select_all_calls[0]["batch_size"] == 1000
    assert db.select_all_calls[0]["order"] == "id.asc"


def test_manifest_is_deterministic_and_contains_no_sensitive_locators():
    sensitive_id = "sensitive-course-uuid"
    sensitive_url = "https://private-host.example/program?payload=secret-name"
    db = FakeDB([row(sensitive_id, url=sensitive_url)])
    kwargs = {
        "head": lambda *_args, **_kwargs: response(200),
        "sleeper": no_sleep,
        "now": NOW,
    }
    first = run_fg3_atomic(db, **kwargs)
    second = run_fg3_atomic(db, **kwargs)
    rendered = json.dumps(first.manifest, sort_keys=True)
    assert first.manifest == second.manifest
    for forbidden in (
        sensitive_id,
        sensitive_url,
        "private-host",
        "secret-name",
        "payload",
        "url",
        "host",
        "name",
    ):
        assert forbidden not in rendered.lower()
