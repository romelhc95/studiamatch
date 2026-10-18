#!/usr/bin/env python3
"""Run the pinned V8 and V9 focused tests, exposing only one fixed marker."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import sys
from collections.abc import Iterable
from pathlib import Path


V8_TEST = "test_template_expression_probe_v8.py"
V8_TEST_SHA256 = "555b9557c6969d414412cdf4a7a68a68105c956a876eda15fe5feb72cac57ff0"
V8_HELPER = "template_expression_probe_v8.py"
V8_HELPER_SHA256 = "ef7d8bf086335b07374186043dfe74964536ca9194df773d889cd7df5f23ab72"
V9_TEST = "test_template_expression_probe_v9.py"
V9_TEST_SHA256 = "d92f7d37bec04469f8be017be9dfff63f80dfcb810ccee052aa4eebf4a3796c1"
V9_HELPER = "template_expression_probe_v9.py"
V9_HELPER_SHA256 = "19189d5012290dc971fab501c37a01390af49fc89a549653ab8e3cd44826b9b8"
V5_SOURCE = "f1_read_failure_classification_v5_once.py"
V5_SHA256 = "2f47ebed1977d360df8aa5905a3a1cf3fa0a813f606e1c3aa583c56d26330c51"
EXPECTED_CASES = {
    "test_v8_splits_the_pinned_template_into_all_allowlisted_fields",
    "test_v8_rejects_changed_or_malformed_template_shape",
    "test_v8_classifies_template_execution_without_retaining_stderr",
    "test_v8_classifies_transport_errors_with_closed_codes",
    "test_v8_closes_unknown_errors_and_phase_names",
    "test_v9_classifies_missing_synthetic_image_without_echoing_reference",
    "test_v9_classifies_image_inspect_access_denied",
    "test_v9_classifies_image_inspect_engine_unavailable",
    "test_v9_classifies_image_inspect_template_error",
    "test_v9_uses_closed_fallback_and_sanitized_line",
    "test_v9_rejects_any_image_inspect_argv_change_before_process_start",
    "test_v9_bounds_synthetic_image_inspect_stdout",
    "test_v9_bounds_synthetic_image_inspect_stderr",
    "test_v9_timeout_kills_process_and_closes_pipe_streams",
}


def _case_names(nodeids: Iterable[str]) -> set[str]:
    return {nodeid.rsplit("::", 1)[-1] for nodeid in nodeids}


class _ResultPlugin:
    def __init__(self) -> None:
        self.collected: set[str] = set()
        self.passed: set[str] = set()
        self.skipped: set[str] = set()
        self.failed = False
        self.phase_failure = False

    def pytest_collection_finish(self, session) -> None:
        self.collected = _case_names(item.nodeid for item in session.items)

    def pytest_runtest_logreport(self, report) -> None:
        case = report.nodeid.rsplit("::", 1)[-1]
        if report.skipped:
            self.skipped.add(case)
        elif report.when != "call":
            self.phase_failure |= bool(report.failed)
        elif report.passed:
            self.passed.add(case)
        elif report.failed:
            self.failed = True

    def passed_all(self, exit_code: int) -> bool:
        return (
            not self.phase_failure
            and not self.failed
            and not self.skipped
            and self.collected == EXPECTED_CASES
            and self.passed == EXPECTED_CASES
            and int(exit_code) == 0
        )


def _verify_source(name: str, expected: str) -> bool:
    path = Path(name)
    try:
        return path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
    except OSError:
        return False


def main() -> int:
    if not all(
        (
            _verify_source(V8_TEST, V8_TEST_SHA256),
            _verify_source(V8_HELPER, V8_HELPER_SHA256),
            _verify_source(V5_SOURCE, V5_SHA256),
            _verify_source(V9_TEST, V9_TEST_SHA256),
            _verify_source(V9_HELPER, V9_HELPER_SHA256),
        )
    ):
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_SOURCE_MISMATCH\n")
        return 0
    try:
        if importlib.util.find_spec("pytest") is None:
            sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_PYTEST_UNAVAILABLE\n")
            return 0
        import pytest
    except Exception:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_PYTEST_UNAVAILABLE\n")
        return 0

    plugin = _ResultPlugin()
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            result = pytest.main(["-q", "-p", "no:cacheprovider", V8_TEST, V9_TEST], plugins=[plugin])
    except Exception:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_RUNNER_FAILED\n")
        return 0
    if plugin.passed_all(int(result)):
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_PASS\n")
    elif plugin.phase_failure:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_PHASE_FAILED\n")
    elif plugin.collected != EXPECTED_CASES:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_COLLECTION_FAILED\n")
    elif plugin.skipped:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_SKIPPED\n")
    elif plugin.failed:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_CASE_FAILED\n")
    else:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V9_INCOMPLETE\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
