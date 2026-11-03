#!/usr/bin/env python3
"""Run the V2 classifier tests and emit closed result codes only."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from collections.abc import Iterable


TEST_FILE = "test_f1_read_failure_classification_once.py"
EXPECTED_CASES = {
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[parse]",
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[evaluation]",
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[ambiguous]",
    "test_v2_main_emits_only_sanitized_template_error",
    "test_v2_failure_code_classification_is_closed_allowlist",
}
CASE_FAILURE_CODES = {
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[parse]": "V2_PARSE_CASE_FAILED",
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[evaluation]": "V2_EVALUATION_CASE_FAILED",
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[ambiguous]": "V2_AMBIGUOUS_CASE_FAILED",
    "test_v2_main_emits_only_sanitized_template_error": "V2_MAIN_SANITIZATION_FAILED",
    "test_v2_failure_code_classification_is_closed_allowlist": "V2_FAILURE_CODE_CLASSIFIER_FAILED",
}


def error_code_for_failed_node(nodeid: str) -> str:
    """Map a pytest node id to a closed code without retaining its path."""
    case = nodeid.rsplit("::", 1)[-1]
    return CASE_FAILURE_CODES.get(case, "V2_TEST_FAILURE_UNCLASSIFIED")


def _case_names(nodeids: Iterable[str]) -> set[str]:
    return {nodeid.rsplit("::", 1)[-1] for nodeid in nodeids}


class _ResultPlugin:
    def __init__(self) -> None:
        self.collected: set[str] = set()
        self.failures: set[str] = set()
        self.phase_failure = False

    def pytest_collection_finish(self, session) -> None:
        self.collected = _case_names(item.nodeid for item in session.items)

    def pytest_runtest_logreport(self, report) -> None:
        if not report.failed:
            return
        if report.when != "call":
            self.phase_failure = True
            return
        self.failures.add(error_code_for_failed_node(report.nodeid))


def _emit(code: str) -> int:
    # Markers are deliberately independent of test output and filesystem paths.
    sys.stdout.write(f"CLASSIFIER_TESTS_{code}\n")
    sys.stdout.flush()
    return 0


def main() -> int:
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
                    "--tb=no",
                    TEST_FILE,
                    "-k",
                    "v2",
                ],
                plugins=[plugin],
            )
    except Exception:
        return _emit("PYTEST_RUNNER_FAILED")

    if plugin.phase_failure:
        return _emit("V2_TEST_PHASE_FAILED")
    if plugin.collected != EXPECTED_CASES:
        return _emit("V2_TEST_COLLECTION_FAILED")
    if plugin.failures:
        for code in sorted(plugin.failures):
            _emit(code)
        return 0
    if int(result) != 0:
        return _emit("PYTEST_RUNNER_FAILED")
    return _emit("PASS")


if __name__ == "__main__":
    raise SystemExit(main())
