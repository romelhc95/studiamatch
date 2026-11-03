#!/usr/bin/env python3
"""Run the bounded V7 split-pair tests and emit only a fixed result marker."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path


TEST_FILE = Path("test_f1_read_failure_classification_v7_split_pair.py")
TEST_SHA256 = "c357175e1a72638db7ac494e5ef4ad86b4a4f107863cba49deb3692ee473fef2"
EXPECTED_CASES = {
    "test_split_contract_keeps_the_23_field_remainder_and_isolates_only_pair",
    "test_split_projection_preserves_present_and_absent_policy_maps",
    "test_split_projection_rejects_shape_and_unbounded_field_outputs_closed",
    "test_split_container_restores_projection_after_success_and_failure",
}


class ResultPlugin:
    def __init__(self) -> None:
        self.collected: set[str] = set()
        self.passed: set[str] = set()
        self.skipped: set[str] = set()
        self.failed: set[str] = set()
        self.phase_failed = False

    def pytest_collection_finish(self, session) -> None:
        self.collected = {item.nodeid.rsplit("::", 1)[-1] for item in session.items}

    def pytest_runtest_logreport(self, report) -> None:
        name = report.nodeid.rsplit("::", 1)[-1]
        if report.skipped:
            self.skipped.add(name)
        elif report.when != "call":
            if report.failed:
                self.phase_failed = True
        elif report.passed:
            self.passed.add(name)
        elif report.failed:
            self.failed.add(name)


def main() -> int:
    try:
        if TEST_FILE.is_symlink() or not TEST_FILE.is_file():
            return 1
        if hashlib.sha256(TEST_FILE.read_bytes()).hexdigest() != TEST_SHA256:
            return 1
        if importlib.util.find_spec("pytest") is None:
            return 1
        import pytest
    except Exception:
        return 1

    plugin = ResultPlugin()
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            result = pytest.main(
                ["-q", "-p", "no:cacheprovider", str(TEST_FILE)],
                plugins=[plugin],
            )
    except Exception:
        return 1
    if (
        int(result) != 0
        or plugin.phase_failed
        or plugin.collected != EXPECTED_CASES
        or plugin.passed != EXPECTED_CASES
        or plugin.skipped
        or plugin.failed
    ):
        return 1
    print("CLASSIFIER_TESTS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
