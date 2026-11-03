#!/usr/bin/env python3
"""Run pinned classifier tests and emit only closed result codes."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import sys
from collections.abc import Iterable
from pathlib import Path


TEST_FILE = "test_f1_read_failure_classification_once.py"
TEST_FILE_V5 = "test_f1_read_failure_classification_v5_once.py"
TEST_FILE_V5_SHA256 = "f8880ccb9d6bf2324e5f7982712ce08f6508d09df68b3c087b91b3753e51219f"
EXPECTED_CASES = {
    "test_v2_main_failure_returns_nonzero",
    "test_v2_main_failure_keeps_private_detail_out",
    "test_v2_main_failure_emits_exact_sanitized_sequence",
    "test_v2_failure_code_classification_is_closed_allowlist",
    "test_classifier_v4_reporter_requires_all_expected_cases_to_pass",
    "test_classifier_v4_reporter_fails_closed_on_skipped_case",
    "test_classifier_v4_reporter_fails_closed_on_missing_call_result",
    "test_f1_template_v5_guards_optional_maps",
    "test_f1_template_v5_is_applied_before_inspect",
    "test_f1_template_v5_missing_labels_still_fail_closed",
    "test_f1_template_v5_missing_tmpfs_still_fail_closed",
}
CASE_FAILURE_CODES = {
    "test_v2_main_failure_returns_nonzero": "V2_MAIN_EXIT_ASSERT_FAILED",
    "test_v2_main_failure_keeps_private_detail_out": "V2_MAIN_SECRET_ASSERT_FAILED",
    "test_v2_main_failure_emits_exact_sanitized_sequence": "V2_MAIN_OUTPUT_ASSERT_FAILED",
    "test_v2_failure_code_classification_is_closed_allowlist": "V2_FAILURE_CODE_CLASSIFIER_FAILED",
    "test_f1_template_v5_guards_optional_maps": "V5_TEMPLATE_GUARD_ASSERT_FAILED",
    "test_f1_template_v5_is_applied_before_inspect": "V5_APPLY_ASSERT_FAILED",
    "test_f1_template_v5_missing_labels_still_fail_closed": "V5_LABEL_POLICY_ASSERT_FAILED",
    "test_f1_template_v5_missing_tmpfs_still_fail_closed": "V5_TMPFS_POLICY_ASSERT_FAILED",
}


def error_code_for_failed_node(nodeid: str) -> str:
    """Map only the allowlisted test case name; never inspect traceback text."""
    case = nodeid.rsplit("::", 1)[-1]
    return CASE_FAILURE_CODES.get(case, "V2_TEST_FAILURE_UNCLASSIFIED")


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
            self.failures.add(error_code_for_failed_node(report.nodeid))

    def result_codes(self, exit_code: int) -> tuple[str, ...]:
        if self.phase_failure:
            return ("V2_TEST_PHASE_FAILED",)
        if self.collected != EXPECTED_CASES:
            return ("V2_TEST_COLLECTION_FAILED",)
        if self.failures:
            return tuple(sorted(self.failures))
        if self.skipped:
            return ("V2_TEST_SKIPPED",)
        if int(exit_code) != 0:
            return ("PYTEST_RUNNER_FAILED",)
        if self.passed != EXPECTED_CASES:
            return ("V2_TEST_RESULT_INCOMPLETE",)
        return ("PASS",)


def _emit(code: str) -> int:
    sys.stdout.write(f"CLASSIFIER_TESTS_{code}\n")
    sys.stdout.flush()
    return 0


def main() -> int:
    test_path = Path(TEST_FILE_V5)
    try:
        if test_path.is_symlink() or not test_path.is_file():
            return _emit("V5_TEST_SOURCE_UNAVAILABLE")
        test_digest = hashlib.sha256(test_path.read_bytes()).hexdigest()
    except OSError:
        return _emit("V5_TEST_SOURCE_UNAVAILABLE")
    if test_digest != TEST_FILE_V5_SHA256:
        return _emit("V5_TEST_SOURCE_HASH_MISMATCH")

    try:
        if importlib.util.find_spec("pytest") is None:
            return _emit("PYTEST_UNAVAILABLE")
        import pytest
    except Exception:
        return _emit("PYTEST_IMPORT_FAILED")

    plugin = _ResultPlugin()
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            result = pytest.main(
                [
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    TEST_FILE,
                    TEST_FILE_V5,
                    "-k",
                    "v2_main_failure or test_v2_failure_code_classification_is_closed_allowlist "
                    "or classifier_v4_reporter or f1_template_v5",
                ],
                plugins=[plugin],
            )
    except Exception:
        return _emit("PYTEST_RUNNER_FAILED")

    codes = plugin.result_codes(int(result))
    for code in codes:
        _emit(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
