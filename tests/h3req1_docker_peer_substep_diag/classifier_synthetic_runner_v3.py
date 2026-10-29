#!/usr/bin/env python3
"""Run pinned classifier tests and emit only closed failure codes."""

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
    "test_v2_main_assertion_markers_map_to_closed_codes[H3REQ1_V2_MAIN_EXIT_CODE-V2_MAIN_EXIT_ASSERT_FAILED]",
    "test_v2_main_assertion_markers_map_to_closed_codes[H3REQ1_V2_MAIN_SANITIZED_OUTPUT-V2_MAIN_OUTPUT_ASSERT_FAILED]",
    "test_v2_main_assertion_markers_map_to_closed_codes[H3REQ1_V2_MAIN_SECRET_ABSENCE-V2_MAIN_SECRET_ASSERT_FAILED]",
    "test_v2_main_assertion_markers_map_to_closed_codes[unrecognized-private-detail-V2_MAIN_SANITIZATION_FAILED]",
}
CASE_FAILURE_CODES = {
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[parse]": "V2_PARSE_CASE_FAILED",
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[evaluation]": "V2_EVALUATION_CASE_FAILED",
    "test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text[ambiguous]": "V2_AMBIGUOUS_CASE_FAILED",
    "test_v2_main_emits_only_sanitized_template_error": "V2_MAIN_SANITIZATION_FAILED",
    "test_v2_failure_code_classification_is_closed_allowlist": "V2_FAILURE_CODE_CLASSIFIER_FAILED",
    "test_v2_main_assertion_markers_map_to_closed_codes[H3REQ1_V2_MAIN_EXIT_CODE-V2_MAIN_EXIT_ASSERT_FAILED]": "V2_MAIN_CODE_MAPPING_FAILED",
    "test_v2_main_assertion_markers_map_to_closed_codes[H3REQ1_V2_MAIN_SANITIZED_OUTPUT-V2_MAIN_OUTPUT_ASSERT_FAILED]": "V2_MAIN_CODE_MAPPING_FAILED",
    "test_v2_main_assertion_markers_map_to_closed_codes[H3REQ1_V2_MAIN_SECRET_ABSENCE-V2_MAIN_SECRET_ASSERT_FAILED]": "V2_MAIN_CODE_MAPPING_FAILED",
    "test_v2_main_assertion_markers_map_to_closed_codes[unrecognized-private-detail-V2_MAIN_SANITIZATION_FAILED]": "V2_MAIN_CODE_MAPPING_FAILED",
}
MAIN_ASSERTION_CODES = {
    "H3REQ1_V2_MAIN_EXIT_CODE": "V2_MAIN_EXIT_ASSERT_FAILED",
    "H3REQ1_V2_MAIN_SANITIZED_OUTPUT": "V2_MAIN_OUTPUT_ASSERT_FAILED",
    "H3REQ1_V2_MAIN_SECRET_ABSENCE": "V2_MAIN_SECRET_ASSERT_FAILED",
}


def error_code_for_failed_node(nodeid: str, failure_detail: str = "") -> str:
    """Map a pytest failure to a closed code; never return its detail."""
    case = nodeid.rsplit("::", 1)[-1]
    if case == "test_v2_main_emits_only_sanitized_template_error":
        for marker, code in MAIN_ASSERTION_CODES.items():
            if marker in failure_detail:
                return code
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
        detail = getattr(report, "longreprtext", "")
        self.failures.add(error_code_for_failed_node(report.nodeid, detail))


def _emit(code: str) -> int:
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
                ["-q", "-p", "no:cacheprovider", TEST_FILE, "-k", "v2"],
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
