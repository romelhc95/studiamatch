from __future__ import annotations

import ast
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from scripts.shared.f10_9_metadata_planner import run_metadata_gate


def course(
    course_id: str,
    *,
    syllabus: object = "Valid syllabus",
    objectives: object = "Valid objectives",
    is_active: bool = True,
) -> dict[str, object]:
    return {
        "id": course_id,
        "is_active": is_active,
        "syllabus": syllabus,
        "objectives": objectives,
    }


def test_complete_cohort_passes_without_external_calls() -> None:
    result = run_metadata_gate([course("course-1")])

    assert result.exit_code == 0
    assert result.manifest["status"] == "PASS"
    assert result.manifest["incomplete_active_courses"] == 0
    assert result.manifest["provider_calls"] == 0
    assert result.manifest["writer_calls"] == 0
    assert result.manifest["data_plane_calls"] == 0


@pytest.mark.parametrize(
    ("value", "field"),
    [
        (None, "syllabus"),
        ("", "objectives"),
        ("\u2003\t\n", "syllabus"),
        ("\u200b\ufeff", "objectives"),
        (" N/A ", "objectives"),
        ("NoNe", "syllabus"),
        ("POR\u00a0DEFINIR", "objectives"),
        ("Ｎ／Ａ", "syllabus"),
    ],
)
def test_null_blank_unicode_and_placeholders_block(value: object, field: str) -> None:
    row = course("course-1")
    row[field] = value

    result = run_metadata_gate([row])

    assert result.exit_code == 1
    assert result.manifest["status"] == "BLOCKED"
    assert result.manifest["reason_codes"] == ["MISSING_ACTIVE_COURSE_METADATA"]


def test_placeholder_matching_is_exact_not_substring() -> None:
    rows = [
        course(
            "course-1",
            syllabus="This is not none and contains N/A examples",
            objectives="Objectives por definir in the next committee meeting",
        )
    ]

    assert run_metadata_gate(rows).exit_code == 0


def test_inactive_incomplete_courses_are_ignored_before_pagination() -> None:
    rows = [
        course("course-0", syllabus=None, objectives="", is_active=False),
        course("course-1"),
    ]

    result = run_metadata_gate(rows, page_size=1)

    assert result.exit_code == 0
    assert result.manifest["active_courses"] == 1


def test_category_arithmetic_counts_union_and_intersection() -> None:
    rows = [
        course("course-1", syllabus=None),
        course("course-2", objectives=""),
        course("course-3", syllabus="none", objectives="n/a"),
        course("course-4"),
    ]

    manifest = run_metadata_gate(rows, page_size=2).manifest

    assert manifest["active_courses"] == 4
    assert manifest["missing_syllabus"] == 2
    assert manifest["missing_objectives"] == 2
    assert manifest["missing_both"] == 1
    assert manifest["incomplete_active_courses"] == 3


@pytest.mark.parametrize("size", [1001, 2007])
def test_complete_internal_pagination_over_one_thousand(size: int) -> None:
    rows = [course(f"course-{index:04d}") for index in range(size)]

    result = run_metadata_gate(rows, page_size=137)

    assert result.exit_code == 0
    assert result.manifest["active_courses"] == size


def test_digest_is_stable_across_page_size_and_input_order() -> None:
    rows = [course(f"course-{index:04d}") for index in range(1103)]

    first = run_metadata_gate(rows, page_size=1000)
    second = run_metadata_gate(list(reversed(rows)), page_size=83)

    assert first.manifest["cohort_fingerprint"] == second.manifest["cohort_fingerprint"]
    assert first.manifest["placeholder_policy_fingerprint"] == second.manifest[
        "placeholder_policy_fingerprint"
    ]


def test_mixed_missing_states_are_stable_across_page_boundaries() -> None:
    rows = [
        course(
            f"course-{index:04d}",
            syllabus=None if index % 5 == 0 else "Valid syllabus",
            objectives="" if index % 7 == 0 else "Valid objectives",
        )
        for index in range(1203)
    ]

    first = run_metadata_gate(rows, page_size=1000)
    second = run_metadata_gate(rows, page_size=61)

    assert first.manifest == second.manifest


def test_concurrent_runs_are_deterministic() -> None:
    rows = [course(f"course-{index:04d}") for index in range(1201)]

    def execute(_: int) -> dict[str, object]:
        return run_metadata_gate(rows, page_size=97).manifest

    with ThreadPoolExecutor(max_workers=6) as executor:
        manifests = list(executor.map(execute, range(12)))

    assert all(manifest == manifests[0] for manifest in manifests)


def test_active_count_drift_between_local_snapshots_fails_closed() -> None:
    result = run_metadata_gate(
        [course("course-1")],
        verification_rows=[course("course-1"), course("course-2")],
    )

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["ACTIVE_COUNT_DRIFT"]


def test_classification_drift_with_constant_count_fails_closed() -> None:
    result = run_metadata_gate(
        [course("course-1")],
        verification_rows=[course("course-1", syllabus=None)],
    )

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["COHORT_FINGERPRINT_DRIFT"]


def test_valid_to_valid_metadata_drift_is_detected() -> None:
    result = run_metadata_gate(
        [course("course-1", syllabus="Version A")],
        verification_rows=[course("course-1", syllabus="Version B")],
    )

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["COHORT_FINGERPRINT_DRIFT"]


def test_duplicate_id_fails_closed() -> None:
    result = run_metadata_gate([course("course-1"), course("course-1")])

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["DUPLICATE_COURSE_ID"]


@pytest.mark.parametrize(
    "row",
    [
        {"id": "course-1", "is_active": True, "syllabus": "Valid"},
        course("course-1", syllabus=123),
        {**course("course-1"), "is_active": "true"},
        {**course("course-1"), "id": ""},
    ],
)
def test_invalid_rows_fail_closed(row: dict[str, object]) -> None:
    result = run_metadata_gate([row])

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["INVALID_COURSE_ROW"]


@pytest.mark.parametrize("rows", [None, 1, "rows", {"id": "course-1"}, object()])
def test_non_native_snapshot_fails_closed(rows: object) -> None:
    result = run_metadata_gate(rows)

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["INVALID_LOCAL_SNAPSHOT"]


def test_custom_sequence_cannot_hide_external_reader_effects() -> None:
    class HostileSequence:
        def __iter__(self):
            raise AssertionError("must never iterate")

    result = run_metadata_gate(HostileSequence())

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["INVALID_LOCAL_SNAPSHOT"]


def test_custom_dictionary_key_is_rejected_before_equality_lookup() -> None:
    class HostileKey:
        def __hash__(self) -> int:
            return 0

        def __eq__(self, other: object) -> bool:
            raise AssertionError("must never compare")

    row: dict[object, object] = {
        "id": "course-1",
        "is_active": True,
        "syllabus": "Valid syllabus",
        "objectives": "Valid objectives",
        HostileKey(): "hidden",
    }

    result = run_metadata_gate([row])

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["INVALID_COURSE_ROW"]


def test_snapshot_row_limit_fails_closed() -> None:
    rows = [course(f"course-{index:05d}") for index in range(10_001)]

    result = run_metadata_gate(rows)

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["SNAPSHOT_LIMIT_EXCEEDED"]


@pytest.mark.parametrize(
    "row",
    [
        course("x" * 257),
        course("course-1", syllabus="x" * 100_001),
        {**course("course-1"), **{f"extra-{index}": index for index in range(29)}},
    ],
)
def test_snapshot_width_and_value_limits_fail_closed(row: dict[str, object]) -> None:
    result = run_metadata_gate([row])

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["SNAPSHOT_LIMIT_EXCEEDED"]


def test_snapshot_total_metadata_budget_fails_closed() -> None:
    value = "x" * 100_000
    rows = [
        course(f"course-{index:02d}", syllabus=value, objectives=value)
        for index in range(26)
    ]

    result = run_metadata_gate(rows)

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["SNAPSHOT_LIMIT_EXCEEDED"]


def test_manifest_never_contains_raw_course_values() -> None:
    rows = [
        course(
            "private-course-id",
            syllabus="private syllabus payload",
            objectives="private objectives payload",
        )
    ]

    serialized = json.dumps(run_metadata_gate(rows).manifest, sort_keys=True)

    assert "private-course-id" not in serialized
    assert "private syllabus payload" not in serialized
    assert "private objectives payload" not in serialized
    assert "http" not in serialized


def test_collection_errors_are_sanitized() -> None:
    result = run_metadata_gate([course("private-course-id", syllabus=object())])
    serialized = json.dumps(result.manifest, sort_keys=True)

    assert result.exit_code == 2
    assert "private-course-id" not in serialized
    assert set(result.manifest) == {
        "plan_id",
        "normalization_version",
        "placeholder_policy_fingerprint",
        "provider_calls",
        "writer_calls",
        "data_plane_calls",
        "status",
        "reason_codes",
    }


def test_module_has_no_external_reader_or_mutating_capability() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts/shared/f10_9_metadata_planner.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_modules = {
        "http",
        "os",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    imported_roots: set[str] = set()
    called_attributes: set[str] = set()
    defined_methods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            called_attributes.add(node.func.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_methods.add(node.name)

    assert imported_roots.isdisjoint(forbidden_modules)
    assert called_attributes.isdisjoint(
        {"delete", "fetch", "insert", "patch", "post", "put", "rpc", "upsert"}
    )
    assert defined_methods.isdisjoint(
        {"count_active_courses", "fetch_active_courses", "request"}
    )
    source = path.read_text(encoding="utf-8").casefold()
    assert "db_client" not in source
    assert "cloudflare" not in source
    assert "openai" not in source


@pytest.mark.parametrize("page_size", [0, -1, True, 1.5, 1001])
def test_invalid_or_oversized_page_size_fails_closed(page_size: object) -> None:
    result = run_metadata_gate([], page_size=page_size)

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["INVALID_PAGE_SIZE"]


@pytest.mark.parametrize(
    "placeholders",
    [None, 1, object(), [], [""], ["n/a", " N/A "], [1], "n/a"],
)
def test_invalid_placeholder_policy_fails_closed(placeholders: object) -> None:
    result = run_metadata_gate([], placeholders=placeholders)

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["INVALID_PLACEHOLDER_POLICY"]
    assert "placeholder_policy_fingerprint" not in result.manifest
    assert result.manifest["placeholder_policy_status"] == "INVALID"


def test_invalid_unicode_policy_fails_closed_without_reprocessing() -> None:
    result = run_metadata_gate([], placeholders=["\ud800"])

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["INVALID_UNICODE"]
    assert "placeholder_policy_fingerprint" not in result.manifest


@pytest.mark.parametrize(
    "placeholders",
    [[f"value-{index}" for index in range(65)], ["x" * 257]],
)
def test_placeholder_policy_limits_fail_closed(placeholders: list[str]) -> None:
    result = run_metadata_gate([], placeholders=placeholders)

    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["PLACEHOLDER_POLICY_LIMIT_EXCEEDED"]
    assert "placeholder_policy_fingerprint" not in result.manifest
