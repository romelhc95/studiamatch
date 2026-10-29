#!/usr/bin/env python3
"""Run only the focused V8 expression-probe tests and emit a fixed marker."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import sys
from collections.abc import Iterable
from pathlib import Path


TEST_FILE = "test_template_expression_probe_v8.py"
TEST_SHA256 = "555b9557c6969d414412cdf4a7a68a68105c956a876eda15fe5feb72cac57ff0"
PROBE_FILE = "template_expression_probe_v8.py"
PROBE_SHA256 = "ef7d8bf086335b07374186043dfe74964536ca9194df773d889cd7df5f23ab72"
V5_FILE = "f1_read_failure_classification_v5_once.py"
V5_SHA256 = "2f47ebed1977d360df8aa5905a3a1cf3fa0a813f606e1c3aa583c56d26330c51"
EXPECTED_CASES = {
    "test_v8_splits_the_pinned_template_into_all_allowlisted_fields",
    "test_v8_rejects_changed_or_malformed_template_shape",
    "test_v8_classifies_template_execution_without_retaining_stderr",
    "test_v8_classifies_transport_errors_with_closed_codes",
    "test_v8_closes_unknown_errors_and_phase_names",
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
            _verify_source(TEST_FILE, TEST_SHA256),
            _verify_source(PROBE_FILE, PROBE_SHA256),
            _verify_source(V5_FILE, V5_SHA256),
        )
    ):
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_SOURCE_MISMATCH\n")
        return 0
    try:
        if importlib.util.find_spec("pytest") is None:
            sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_PYTEST_UNAVAILABLE\n")
            return 0
        import pytest
    except Exception:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_PYTEST_UNAVAILABLE\n")
        return 0

    plugin = _ResultPlugin()
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            result = pytest.main(["-q", "-p", "no:cacheprovider", TEST_FILE], plugins=[plugin])
    except Exception:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_RUNNER_FAILED\n")
        return 0
    if plugin.passed_all(int(result)):
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_PASS\n")
    elif plugin.phase_failure:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_PHASE_FAILED\n")
    elif plugin.collected != EXPECTED_CASES:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_COLLECTION_FAILED\n")
    elif plugin.skipped:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_SKIPPED\n")
    elif plugin.failed:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_CASE_FAILED\n")
    else:
        sys.stdout.write("TEMPLATE_PROBE_TESTS_V8_INCOMPLETE\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
