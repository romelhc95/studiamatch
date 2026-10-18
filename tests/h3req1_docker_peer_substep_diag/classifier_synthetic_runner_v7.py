#!/usr/bin/env python3
"""Check old-suite inputs, then run only the focused V7 classifier tests."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import sys
from collections.abc import Iterable
from pathlib import Path


TEST_FILE = "test_f1_template_smoke_v7_once.py"
TEST_FILE_SHA256 = "548d65701def7cb7450cea1761063d992d39f2edac66d86269101cd431f52fa7"
CLASSIFIER_FILE = "template_inspect_classifier_v7.py"
CLASSIFIER_FILE_SHA256 = "432295368a96b7ba8329e3a83aede3bfbba872400331b19127c334d06ca3d58d"
V4_TEST_FILE = "test_f1_read_failure_classification_once.py"
V4_TEST_FILE_SHA256 = "369382daa3445999704d85278a482edf78648a61a8e1ef3703ace37a2b923199"
V5_TEST_FILE = "test_f1_read_failure_classification_v5_once.py"
V5_TEST_FILE_SHA256 = "f8880ccb9d6bf2324e5f7982712ce08f6508d09df68b3c087b91b3753e51219f"
V6_TEST_FILE = "test_f1_read_failure_classification_v6_once.py"
V6_TEST_FILE_SHA256 = "a5921c5291a207178f368c64184b7b4869ceeb010b006bb2618038c3cb8516c4"
V6_TEST_RUNNER_FILE = "classifier_synthetic_runner_v6.py"
V6_TEST_RUNNER_SHA256 = "baf6d4873d6229b40db994c65305be527f61f310306e6ae904c1b8cd3b76380d"
V6_CLASSIFIER_FILE = "f1_read_failure_classification_v6_once.py"
V6_CLASSIFIER_SHA256 = "b17266a33559b16b28cdf1b619f9b5d7dae666203f6d9a357b046ed7ae809128"
EXPECTED_CASES = {
    "test_template_smoke_v7_keeps_allowlisted_field_errors",
    "test_template_smoke_v7_classifies_captured_go_template_error",
    "test_template_smoke_v7_closes_unknown_inspect_codes",
    "test_template_smoke_v7_preserves_bounded_runner_failures",
}
CASE_FAILURE_CODES = {
    "test_template_smoke_v7_keeps_allowlisted_field_errors": "V7_TEMPLATE_ERROR_CLASSIFICATION_FAILED",
    "test_template_smoke_v7_classifies_captured_go_template_error": "V7_TEMPLATE_CAPTURE_CLASSIFICATION_FAILED",
    "test_template_smoke_v7_closes_unknown_inspect_codes": "V7_TEMPLATE_GENERIC_FALLBACK_FAILED",
    "test_template_smoke_v7_preserves_bounded_runner_failures": "V7_TEMPLATE_BOUNDED_CODE_FAILED",
}


def _case_names(nodeids: Iterable[str]) -> set[str]:
    return {nodeid.rsplit("::", 1)[-1] for nodeid in nodeids}


class _ResultPlugin:
    def __init__(self) -> None:
        self.collected: set[str] = set()
        self.passed: set[str] = set()
        self.skipped: set[str] = set()
        self.failures: set[str] = set()
        self.phase_failure = False

    def pytest_collection_finish(self, session) -> None:
        self.collected = _case_names(item.nodeid for item in session.items)

    def pytest_runtest_logreport(self, report) -> None:
        case = report.nodeid.rsplit("::", 1)[-1]
        if report.skipped:
            self.skipped.add(case)
            return
        if report.when != "call":
            if report.failed:
                self.phase_failure = True
            return
        if report.passed:
            self.passed.add(case)
        elif report.failed:
            self.failures.add(CASE_FAILURE_CODES.get(case, "V7_TEST_FAILURE_UNCLASSIFIED"))

    def result_codes(self, exit_code: int) -> tuple[str, ...]:
        if self.phase_failure:
            return ("V7_TEST_PHASE_FAILED",)
        if self.collected != EXPECTED_CASES:
            return ("V7_TEST_COLLECTION_FAILED",)
        if self.failures:
            return tuple(sorted(self.failures))
        if self.skipped:
            return ("V7_TEST_SKIPPED",)
        if int(exit_code) != 0:
            return ("V7_TEST_RUNNER_FAILED",)
        if self.passed != EXPECTED_CASES:
            return ("V7_TEST_RESULT_INCOMPLETE",)
        return ("PASS",)


def _emit(code: str) -> int:
    sys.stdout.write(f"CLASSIFIER_TESTS_{code}\n")
    sys.stdout.flush()
    return 0


def _verify_source(name: str, expected: str, failure_code: str) -> str | None:
    path = Path(name)
    try:
        if path.is_symlink() or not path.is_file():
            return failure_code.replace("HASH_MISMATCH", "UNAVAILABLE")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return failure_code.replace("HASH_MISMATCH", "UNAVAILABLE")
    return None if digest == expected else failure_code


def main() -> int:
    for name, expected, error in (
        (V4_TEST_FILE, V4_TEST_FILE_SHA256, "V4_TEST_SOURCE_HASH_MISMATCH"),
        (V5_TEST_FILE, V5_TEST_FILE_SHA256, "V5_TEST_SOURCE_HASH_MISMATCH"),
        (V6_TEST_FILE, V6_TEST_FILE_SHA256, "V6_TEST_SOURCE_HASH_MISMATCH"),
        (V6_TEST_RUNNER_FILE, V6_TEST_RUNNER_SHA256, "V6_TEST_RUNNER_SOURCE_HASH_MISMATCH"),
        (V6_CLASSIFIER_FILE, V6_CLASSIFIER_SHA256, "V6_CLASSIFIER_SOURCE_HASH_MISMATCH"),
        (CLASSIFIER_FILE, CLASSIFIER_FILE_SHA256, "V7_CLASSIFIER_SOURCE_HASH_MISMATCH"),
        (TEST_FILE, TEST_FILE_SHA256, "V7_TEST_SOURCE_HASH_MISMATCH"),
    ):
        failure = _verify_source(name, expected, error)
        if failure:
            return _emit(failure)

    try:
        if importlib.util.find_spec("pytest") is None:
            return _emit("V7_PYTEST_UNAVAILABLE")
        import pytest
    except Exception:
        return _emit("V7_PYTEST_IMPORT_FAILED")

    plugin = _ResultPlugin()
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            result = pytest.main(
                ["-q", "-p", "no:cacheprovider", TEST_FILE],
                plugins=[plugin],
            )
    except Exception:
        return _emit("V7_PYTEST_RUNNER_FAILED")

    codes = plugin.result_codes(int(result))
    for code in codes:
        _emit(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
