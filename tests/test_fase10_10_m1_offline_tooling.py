from __future__ import annotations

import ast
import hashlib
import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.shared import f10_10_metadata_remediation as m1
from scripts.shared.f10_10_metadata_remediation import (
    COMMAND_SCHEMA,
    INPUT_SCHEMA,
    advance_offline_state,
    build_offline_plan,
)


BASE_SHA = "b143e92a3a40d5acf8b3968f415122e321f01f31"
BASE_TREE = "2a8fb42b80d75fc6d6c8cfdf1dac3ee81f15a105"
HOST = "sha256:" + "a" * 64
PROJECT = "private-project-ref"
EVALUATED_AT = "2026-08-10T19:00:00Z"


def digest(domain: str, value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    result = hashlib.sha256()
    result.update(f"f10.10-m1:{domain}\n".encode())
    result.update(len(payload).to_bytes(8, "big"))
    result.update(payload)
    return "sha256:" + result.hexdigest()


def course(
    course_id: str,
    *,
    syllabus: object = "Official syllabus",
    objectives: object = "Official objectives",
    active: bool = True,
    institution: str = "institution-1",
) -> dict[str, object]:
    return {
        "id": course_id,
        "institution_id": institution,
        "is_active": active,
        "syllabus": syllabus,
        "objectives": objectives,
        "category": "Category A",
        "category_id": "category-1",
        "category_confirmed": True,
        "other_columns_fingerprint": "sha256:" + "b" * 64,
    }


def population_expectation(rows: list[dict[str, object]]) -> dict[str, object]:
    total_ids = sorted(row["id"] for row in rows)
    active_ids = sorted(row["id"] for row in rows if row["is_active"])
    return {
        "total_count": len(total_ids),
        "total_ids_digest": digest("total-course-ids", total_ids),
        "active_count": len(active_ids),
        "active_ids_digest": digest("active-course-ids", active_ids),
        "attestation_mode": "SYNTHETIC_OFFLINE_ONLY",
        "acquisition_manifest_digest": digest(
            "synthetic-acquisition",
            {"total_ids": total_ids, "active_ids": active_ids},
        ),
    }


def source(
    row: dict[str, object],
    field: str,
    *,
    candidate: str | None = None,
    kind: str | None = None,
    semantic: str | None = None,
) -> dict[str, object]:
    extracted = row[field] if candidate is None else candidate
    source_kind = kind or (
        "DETERMINISTIC_EXTRACTION" if candidate is not None else "PERSISTED_FIELD"
    )
    return {
        "source_id": f"source-{row['id']}-{field}",
        "course_id": row["id"],
        "institution_id": row["institution_id"],
        "field_name": field,
        "project_ref": PROJECT,
        "host_fingerprint": HOST,
        "source_kind": source_kind,
        "lineage_hash": "sha256:" + "c" * 64,
        "source_hash": digest("field-value", extracted),
        "evidence_location_hash": "sha256:" + "d" * 64,
        "evidence_text": None if source_kind == "PERSISTED_FIELD" else f"Evidence for {field}",
        "extraction_method": "persisted" if source_kind == "PERSISTED_FIELD" else "deterministic-v1",
        "extraction_version": "v1",
        "semantic_class": semantic or field.upper(),
        "extracted_value": extracted,
        "mock": False,
        "observed_at": "2026-08-10T18:00:00Z",
        "freshness_rule": "VALID_UNTIL_INCLUSIVE",
        "fresh_until": "2026-09-10T00:00:00Z",
    }


def envelope() -> dict[str, object]:
    first = [
        course("course-1", syllabus=None),
        course("course-2", objectives=""),
        course("course-3"),
        course("course-inactive", syllabus=None, objectives=None, active=False),
    ]
    sources = []
    for row in first:
        if not row["is_active"]:
            continue
        for field in ("syllabus", "objectives"):
            candidate = None
            if row["id"] == "course-1" and field == "syllabus":
                candidate = "Generated syllabus from persisted evidence"
            if row["id"] == "course-2" and field == "objectives":
                candidate = "Generated objectives from persisted evidence"
            sources.append(source(row, field, candidate=candidate))
    syllabus_candidate = "Generated syllabus from persisted evidence"
    return {
        "schema": INPUT_SCHEMA,
        "evaluated_at": EVALUATED_AT,
        "target": {
            "project_ref": PROJECT,
            "host_fingerprint": HOST,
            "approval_replays": ["Free", "Certification"],
        },
        "context": {
            "base_sha": BASE_SHA,
            "base_tree": BASE_TREE,
            "schema_fingerprint": "sha256:" + "1" * 64,
            "trigger_fingerprint": "sha256:" + "2" * 64,
            "profile_fingerprint": "sha256:" + "3" * 64,
            "policy_id": "metadata-remediation-v1",
            "normalization_version": "f10.9-metadata-v2",
            "writers_paused": True,
            "schedules_paused": True,
        },
        "snapshots": {"first": first, "second": deepcopy(first)},
        "population_expectation": population_expectation(first),
        "source_ledger": sources,
        "provider_ledger": [],
        "reviewer_ledger": [],
        "trigger_projections": [
            {
                "course_id": "course-1",
                "syllabus_value_hash": digest("field-value", syllabus_candidate),
                "category": "Trigger Category",
                "category_id": "trigger-category",
                "category_confirmed": False,
                "trigger_fingerprint": "sha256:" + "2" * 64,
            }
        ],
        "pilot_course_ids": ["course-1", "course-2"],
    }


def mutation_command(
    state: dict[str, object],
    action: str,
    command_id: str,
    *,
    metadata_outcome: str = "ACK_EXACT_ONE",
    category_outcome: str = "ACK_EXACT_ONE",
) -> dict[str, object]:
    desired = "EXACT_PREIMAGE" if action == "RESTORE" else "EXACT_CANDIDATE"
    outcomes = []
    for item in state["pilot_plan"]:
        required = item["category_restore_required"]
        outcomes.append(
            {
                "course_id": item["course_id"],
                "metadata_outcome": metadata_outcome,
                "metadata_poststate": desired,
                "category_outcome": category_outcome if required else "NOT_REQUIRED",
                "category_poststate": "EXACT_PREIMAGE" if required else "NOT_REQUIRED",
            }
        )
    return {
        "schema": COMMAND_SCHEMA,
        "command_id": command_id,
        "action": action,
        "context_digest": state["context_digest"],
        "expected_state_digest": state["seal"],
        "expected_sequence": state["sequence_number"],
        "outcomes": outcomes,
    }


def noop_command(state: dict[str, object], action: str, command_id: str) -> dict[str, object]:
    desired = "EXACT_PREIMAGE" if action == "RESTORE_NOOP" else "EXACT_CANDIDATE"
    outcomes = [
        {
            "course_id": item["course_id"],
            "metadata_outcome": "EXACT_ZERO",
            "metadata_poststate": desired,
            "category_outcome": "EXACT_ZERO" if item["category_restore_required"] else "NOT_REQUIRED",
            "category_poststate": "EXACT_PREIMAGE" if item["category_restore_required"] else "NOT_REQUIRED",
        }
        for item in state["pilot_plan"]
    ]
    return {
        "schema": COMMAND_SCHEMA,
        "command_id": command_id,
        "action": action,
        "context_digest": state["context_digest"],
        "expected_state_digest": state["seal"],
        "expected_sequence": state["sequence_number"],
        "outcomes": outcomes,
    }


def test_ready_plan_is_fill_only_accounted_and_sanitized() -> None:
    raw = envelope()
    result = build_offline_plan(raw)

    assert result.exit_code == 0
    assert result.manifest["status"] == "M1_SIMULATION_READY"
    assert result.manifest["population_authoritative"] is False
    assert result.manifest["remote_execution_authorized"] is False
    assert result.manifest["approval_replay_count"] == 2
    assert result.manifest["counts"]["active_courses"] == 3
    assert result.manifest["counts"]["active_field_slots"] == 6
    assert result.manifest["counts"]["frozen_incomplete_slots"] == 2
    assert result.manifest["counts"]["pending_slots"] == 2
    assert result.manifest["counts"]["unclassified_incomplete_slots"] == 0
    plan = result.private["plan"]
    assert plan[0]["candidate"] == {"syllabus": "Generated syllabus from persisted evidence"}
    assert plan[1]["candidate"] == {"objectives": "Generated objectives from persisted evidence"}
    serialized = json.dumps(result.manifest, sort_keys=True)
    for private_value in (
        PROJECT,
        "course-1",
        "Generated syllabus from persisted evidence",
        "Trigger Category",
    ):
        assert private_value not in serialized
    assert result.manifest["network_calls"] == 0
    assert result.manifest["database_calls"] == 0
    assert result.manifest["provider_calls"] == 0
    assert result.manifest["writer_calls"] == 0


def test_order_and_alias_order_do_not_change_plan_digests() -> None:
    first = envelope()
    second = deepcopy(first)
    second["snapshots"]["first"].reverse()
    second["snapshots"]["second"].reverse()
    second["source_ledger"].reverse()
    second["target"]["approval_replays"].reverse()

    left = build_offline_plan(first).manifest
    right = build_offline_plan(second).manifest

    for key in (
        "target_binding_digest",
        "approval_replay_digest",
        "cohort_digest",
        "source_ledger_digest",
        "plan_digest",
    ):
        assert left[key] == right[key]


def test_snapshot_drift_and_denominator_gaming_stop() -> None:
    value_change = envelope()
    value_change["snapshots"]["second"][0]["syllabus"] = "Concurrent value"
    assert build_offline_plan(value_change).manifest["reason_codes"] == ["STOP_FULL_SNAPSHOT_DRIFT"]

    active_swap = envelope()
    active_swap["snapshots"]["second"][0]["is_active"] = False
    active_swap["snapshots"]["second"][3]["is_active"] = True
    assert build_offline_plan(active_swap).manifest["reason_codes"] == ["STOP_FULL_SNAPSHOT_DRIFT"]


def test_population_expectation_is_independent_and_blocking() -> None:
    data = envelope()
    data["population_expectation"]["total_count"] -= 1
    result = build_offline_plan(data)
    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["STOP_POPULATION_EXPECTATION_DRIFT"]


def test_recomputed_synthetic_expectation_never_becomes_authoritative() -> None:
    data = envelope()
    rows = [course("only-course")]
    data["snapshots"] = {"first": rows, "second": deepcopy(rows)}
    data["population_expectation"] = population_expectation(rows)
    data["source_ledger"] = [
        source(rows[0], field) for field in ("syllabus", "objectives")
    ]
    data["trigger_projections"] = []
    data["pilot_course_ids"] = []

    result = build_offline_plan(data)

    assert result.manifest["status"] == "M1_SIMULATION_NOOP"
    assert result.manifest["population_authoritative"] is False
    assert result.manifest["remote_execution_authorized"] is False


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda data: data["source_ledger"].pop(), "HOLD_SOURCE_MISSING"),
        (
            lambda data: data["source_ledger"].append(
                {**deepcopy(data["source_ledger"][0]), "source_id": "duplicate-slot-source"}
            ),
            "HOLD_AMBIGUOUS_LINEAGE",
        ),
        (lambda data: data["source_ledger"][0].__setitem__("project_ref", "other-target"), "HOLD_AMBIGUOUS_LINEAGE"),
        (lambda data: data["source_ledger"][0].__setitem__("mock", True), "HOLD_INSUFFICIENT_EVIDENCE"),
        (lambda data: data["source_ledger"][0].__setitem__("fresh_until", "2026-01-01T00:00:00Z"), "HOLD_SOURCE_STALE"),
    ],
)
def test_source_quality_failures_block(mutation, reason: str) -> None:
    data = envelope()
    mutation(data)
    result = build_offline_plan(data)

    assert result.exit_code == 1
    assert reason in result.manifest["reason_codes"]
    assert result.manifest["counts"]["quality_failure_slots"] > 0


def test_graduate_profile_never_supplies_objectives() -> None:
    data = envelope()
    objective = next(
        record
        for record in data["source_ledger"]
        if record["course_id"] == "course-2" and record["field_name"] == "objectives"
    )
    objective["semantic_class"] = "GRADUATE_PROFILE"

    result = build_offline_plan(data)

    assert result.exit_code == 1
    assert "HOLD_INSUFFICIENT_EVIDENCE" in result.manifest["reason_codes"]


def test_source_hash_is_bound_to_extracted_value() -> None:
    data = envelope()
    data["source_ledger"][0]["source_hash"] = "sha256:" + "9" * 64
    result = build_offline_plan(data)
    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["M1_SOURCE_HASH_MISMATCH"]


def test_timestamp_must_be_real_and_not_from_the_future() -> None:
    impossible = envelope()
    impossible["source_ledger"][0]["observed_at"] = "2026-02-31T00:00:00Z"
    assert build_offline_plan(impossible).manifest["reason_codes"] == ["M1_INPUT_SCHEMA_INVALID"]

    future = envelope()
    future["source_ledger"][0]["observed_at"] = "2026-08-11T00:00:00Z"
    assert "HOLD_SOURCE_STALE" in build_offline_plan(future).manifest["reason_codes"]


def test_provider_history_and_review_denominator_are_exhaustive() -> None:
    data = envelope()
    objective = next(
        record
        for record in data["source_ledger"]
        if record["course_id"] == "course-2" and record["field_name"] == "objectives"
    )
    objective["source_kind"] = "PROVIDER_EVIDENCE"
    value = objective["extracted_value"]
    approved = {
        "output_id": "output-approved",
        "course_id": "course-2",
        "field_name": "objectives",
        "source_id": objective["source_id"],
        "provider_identity_hash": "sha256:" + "4" * 64,
        "status": "SUCCEEDED",
        "value": value,
        "value_hash": digest("field-value", value),
    }
    rejected = deepcopy(approved)
    rejected.update(
        {
            "output_id": "output-rejected",
            "value": "Rejected version",
            "value_hash": digest("field-value", "Rejected version"),
        }
    )
    data["provider_ledger"] = [approved, rejected]
    data["reviewer_ledger"] = [
        {
            "review_id": "review-approved",
            "output_id": "output-approved",
            "reviewer_identity_hash": "sha256:" + "5" * 64,
            "decision": "APPROVED",
            "reviewed_value_hash": approved["value_hash"],
            "decided_at": "2026-08-10T18:30:00Z",
        },
        {
            "review_id": "review-rejected",
            "output_id": "output-rejected",
            "reviewer_identity_hash": "sha256:" + "6" * 64,
            "decision": "REJECTED",
            "reviewed_value_hash": rejected["value_hash"],
            "decided_at": "2026-08-10T18:00:00Z",
        },
    ]

    result = build_offline_plan(data)

    assert result.exit_code == 0
    assert result.manifest["counts"]["provider_outputs_total"] == 2
    assert result.manifest["counts"]["reviewed_approved"] == 1
    assert result.manifest["counts"]["reviewed_rejected"] == 1
    assert result.manifest["counts"]["unreviewed_provider_outputs"] == 0


def test_unreviewed_or_failed_provider_output_never_disappears() -> None:
    data = envelope()
    objective = next(
        record
        for record in data["source_ledger"]
        if record["course_id"] == "course-2" and record["field_name"] == "objectives"
    )
    objective["source_kind"] = "PROVIDER_EVIDENCE"
    data["provider_ledger"] = [
        {
            "output_id": "failed-output",
            "course_id": "course-2",
            "field_name": "objectives",
            "source_id": objective["source_id"],
            "provider_identity_hash": "sha256:" + "7" * 64,
            "status": "FAILED",
            "value": None,
            "value_hash": None,
        }
    ]
    assert build_offline_plan(data).manifest["reason_codes"] == ["M1_REVIEW_LEDGER_UNRECONCILED"]

    data["reviewer_ledger"] = [
        {
            "review_id": "failed-review",
            "output_id": "failed-output",
            "reviewer_identity_hash": "sha256:" + "8" * 64,
            "decision": "HOLD",
            "reviewed_value_hash": None,
            "decided_at": EVALUATED_AT,
        }
    ]
    result = build_offline_plan(data)
    assert result.exit_code == 1
    assert "HOLD_PROVIDER_FAILED" in result.manifest["reason_codes"]
    assert result.manifest["counts"]["provider_outputs_total"] == 1
    assert result.manifest["counts"]["review_holds"] == 1


def test_provider_output_must_bind_to_source_slot_and_rejection_terminal() -> None:
    data = envelope()
    data["provider_ledger"] = [
        {
            "output_id": "orphan-output",
            "course_id": "course-2",
            "field_name": "objectives",
            "source_id": "missing-source",
            "provider_identity_hash": "sha256:" + "7" * 64,
            "status": "FAILED",
            "value": None,
            "value_hash": None,
        }
    ]
    data["reviewer_ledger"] = [
        {
            "review_id": "orphan-review",
            "output_id": "orphan-output",
            "reviewer_identity_hash": "sha256:" + "8" * 64,
            "decision": "HOLD",
            "reviewed_value_hash": None,
            "decided_at": EVALUATED_AT,
        }
    ]
    assert build_offline_plan(data).manifest["reason_codes"] == ["M1_LEDGER_ORPHAN"]

    rejected = envelope()
    objective = next(
        record
        for record in rejected["source_ledger"]
        if record["course_id"] == "course-2" and record["field_name"] == "objectives"
    )
    objective["source_kind"] = "PROVIDER_EVIDENCE"
    value = objective["extracted_value"]
    rejected["provider_ledger"] = [
        {
            "output_id": "rejected-only",
            "course_id": "course-2",
            "field_name": "objectives",
            "source_id": objective["source_id"],
            "provider_identity_hash": "sha256:" + "7" * 64,
            "status": "SUCCEEDED",
            "value": value,
            "value_hash": digest("field-value", value),
        }
    ]
    rejected["reviewer_ledger"] = [
        {
            "review_id": "rejected-review",
            "output_id": "rejected-only",
            "reviewer_identity_hash": "sha256:" + "8" * 64,
            "decision": "REJECTED",
            "reviewed_value_hash": digest("field-value", value),
            "decided_at": EVALUATED_AT,
        }
    ]
    assert build_offline_plan(rejected).manifest["reason_codes"] == [
        "M1_PROVIDER_LEDGER_UNRECONCILED"
    ]


def test_review_cutoff_and_terminal_order_are_fail_closed() -> None:
    data = envelope()
    objective = next(
        record
        for record in data["source_ledger"]
        if record["course_id"] == "course-2" and record["field_name"] == "objectives"
    )
    objective["source_kind"] = "PROVIDER_EVIDENCE"
    value = objective["extracted_value"]
    output = {
        "output_id": "future-approved",
        "course_id": "course-2",
        "field_name": "objectives",
        "source_id": objective["source_id"],
        "provider_identity_hash": "sha256:" + "7" * 64,
        "status": "SUCCEEDED",
        "value": value,
        "value_hash": digest("field-value", value),
    }
    data["provider_ledger"] = [output]
    data["reviewer_ledger"] = [
        {
            "review_id": "future-review",
            "output_id": "future-approved",
            "reviewer_identity_hash": "sha256:" + "8" * 64,
            "decision": "APPROVED",
            "reviewed_value_hash": output["value_hash"],
            "decided_at": "2026-08-11T00:00:00Z",
        }
    ]
    assert build_offline_plan(data).manifest["reason_codes"] == [
        "M1_REVIEW_LEDGER_UNRECONCILED"
    ]

    chronological = envelope()
    objective = next(
        record
        for record in chronological["source_ledger"]
        if record["course_id"] == "course-2" and record["field_name"] == "objectives"
    )
    objective["source_kind"] = "PROVIDER_EVIDENCE"
    approved = deepcopy(output)
    approved.update({"output_id": "early-approved", "source_id": objective["source_id"]})
    rejected = deepcopy(approved)
    rejected["output_id"] = "late-rejected"
    chronological["provider_ledger"] = [approved, rejected]
    chronological["reviewer_ledger"] = [
        {
            "review_id": "early-review",
            "output_id": "early-approved",
            "reviewer_identity_hash": "sha256:" + "8" * 64,
            "decision": "APPROVED",
            "reviewed_value_hash": approved["value_hash"],
            "decided_at": "2026-08-10T17:00:00Z",
        },
        {
            "review_id": "late-review",
            "output_id": "late-rejected",
            "reviewer_identity_hash": "sha256:" + "9" * 64,
            "decision": "REJECTED",
            "reviewed_value_hash": rejected["value_hash"],
            "decided_at": "2026-08-10T18:30:00Z",
        },
    ]
    assert build_offline_plan(chronological).manifest["reason_codes"] == [
        "M1_PROVIDER_LEDGER_UNRECONCILED"
    ]

    terminal_hold = deepcopy(chronological)
    hold_output = deepcopy(approved)
    hold_output.update(
        {
            "output_id": "terminal-hold",
            "status": "FAILED",
            "value": None,
            "value_hash": None,
        }
    )
    terminal_hold["provider_ledger"].append(hold_output)
    terminal_hold["reviewer_ledger"].append(
        {
            "review_id": "terminal-hold-review",
            "output_id": "terminal-hold",
            "reviewer_identity_hash": "sha256:" + "a" * 64,
            "decision": "HOLD",
            "reviewed_value_hash": None,
            "decided_at": "2026-08-10T18:45:00Z",
        }
    )
    hold_result = build_offline_plan(terminal_hold)
    assert hold_result.exit_code == 1
    assert "HOLD_PROVIDER_FAILED" in hold_result.manifest["reason_codes"]


def test_evaluation_cutoff_is_bound_into_manifest_and_state() -> None:
    first = envelope()
    second = envelope()
    second["evaluated_at"] = "2026-08-10T19:30:00Z"

    left = build_offline_plan(first)
    right = build_offline_plan(second)

    assert left.manifest["evaluation_boundary_digest"] != right.manifest[
        "evaluation_boundary_digest"
    ]
    assert left.private["state"]["context_digest"] != right.private["state"][
        "context_digest"
    ]


def test_physical_target_is_bound_into_context_and_state_seal() -> None:
    first = envelope()
    second = envelope()
    second["target"]["project_ref"] = "other-private-project"
    second["target"]["host_fingerprint"] = "sha256:" + "e" * 64
    for record in second["source_ledger"]:
        record["project_ref"] = second["target"]["project_ref"]
        record["host_fingerprint"] = second["target"]["host_fingerprint"]

    left = build_offline_plan(first)
    right = build_offline_plan(second)

    assert left.exit_code == right.exit_code == 0
    assert left.private["state"]["context_digest"] != right.private["state"]["context_digest"]
    assert left.private["state"]["target_binding_digest"] != right.private["state"]["target_binding_digest"]
    assert left.private["state"]["seal"] != right.private["state"]["seal"]


def test_native_preflight_counts_keys_and_checks_lists_before_expansion(monkeypatch) -> None:
    monkeypatch.setattr(m1, "MAX_TOTAL_CHARS", 10)
    assert build_offline_plan({"123456": None, "abcdef": None}).manifest["reason_codes"] == [
        "M1_INPUT_LIMIT_EXCEEDED"
    ]

    monkeypatch.setattr(m1, "MAX_TOTAL_CHARS", 8_000_000)
    monkeypatch.setattr(m1, "MAX_NODES", 10)
    assert build_offline_plan([None] * 11).manifest["reason_codes"] == [
        "M1_INPUT_LIMIT_EXCEEDED"
    ]
    implementation = inspect.getsource(m1._preflight_native)
    list_branch = implementation.split("if type(current) is list:", 1)[1].split(
        "if type(current) is dict:", 1
    )[0]
    assert list_branch.index("nodes + len(stack) + len(current)") < list_branch.index(
        "stack.extend"
    )


def test_more_than_one_thousand_rows_are_fully_accounted() -> None:
    data = envelope()
    rows = [course(f"course-{index:04d}") for index in range(1005)]
    data["snapshots"] = {"first": rows, "second": deepcopy(rows)}
    data["population_expectation"] = population_expectation(rows)
    data["source_ledger"] = [source(row, field) for row in rows for field in ("syllabus", "objectives")]
    data["trigger_projections"] = []
    data["pilot_course_ids"] = []

    result = build_offline_plan(data)

    assert result.exit_code == 0
    assert result.manifest["status"] == "M1_SIMULATION_NOOP"
    assert result.manifest["counts"]["total_courses"] == 1005
    assert result.manifest["counts"]["active_field_slots"] == 2010
    assert result.manifest["counts"]["validated_source_slots"] == 2010


def test_complete_slot_with_bad_source_blocks_global_quality() -> None:
    data = envelope()
    complete_source = next(
        record
        for record in data["source_ledger"]
        if record["course_id"] == "course-3" and record["field_name"] == "syllabus"
    )
    complete_source["mock"] = True

    result = build_offline_plan(data)

    assert result.exit_code == 1
    assert result.manifest["counts"]["quality_failure_slots"] == 1
    assert (
        result.manifest["counts"]["validated_source_slots"]
        + result.manifest["counts"]["quality_failure_slots"]
        == result.manifest["counts"]["active_field_slots"]
    )


def test_persisted_field_cannot_fill_a_missing_slot() -> None:
    data = envelope()
    row = data["snapshots"]["first"][0]
    replacement = source(
        row,
        "syllabus",
        candidate="Unsupported persisted fill",
        kind="PERSISTED_FIELD",
    )
    data["source_ledger"][0] = replacement

    result = build_offline_plan(data)

    assert result.exit_code == 1
    assert "HOLD_INSUFFICIENT_EVIDENCE" in result.manifest["reason_codes"]
    assert result.manifest["counts"]["quality_failure_slots"] == 1


def test_provider_source_requires_reconciled_output_even_for_complete_slot() -> None:
    data = envelope()
    provider_source = next(
        record
        for record in data["source_ledger"]
        if record["course_id"] == "course-3" and record["field_name"] == "objectives"
    )
    provider_source["source_kind"] = "PROVIDER_EVIDENCE"
    provider_source["evidence_text"] = "Official objective evidence"
    provider_source["extraction_method"] = "provider-v1"

    result = build_offline_plan(data)

    assert result.exit_code == 1
    assert "HOLD_PROVIDER_FAILED" in result.manifest["reason_codes"]
    assert result.manifest["counts"]["quality_failure_slots"] == 1


def test_any_source_conflicting_with_complete_value_blocks_quality() -> None:
    data = envelope()
    row = data["snapshots"]["first"][2]
    replacement = source(
        row,
        "syllabus",
        candidate="Contradictory deterministic value",
        kind="DETERMINISTIC_EXTRACTION",
    )
    index = next(
        index
        for index, record in enumerate(data["source_ledger"])
        if record["course_id"] == "course-3" and record["field_name"] == "syllabus"
    )
    data["source_ledger"][index] = replacement

    result = build_offline_plan(data)

    assert result.exit_code == 1
    assert "HOLD_INSUFFICIENT_EVIDENCE" in result.manifest["reason_codes"]
    assert result.manifest["counts"]["quality_failure_slots"] == 1


def test_inactive_source_is_rejected_and_source_counts_never_negative() -> None:
    data = envelope()
    inactive = data["snapshots"]["first"][3]
    data["source_ledger"].append(source(inactive, "syllabus", candidate="Unused"))
    assert build_offline_plan(data).manifest["reason_codes"] == ["M1_LEDGER_ORPHAN"]


def test_alias_variants_coalesce_to_one_approval_replay() -> None:
    data = envelope()
    data["target"]["approval_replays"] = ["Free", " free ", "Ｆｒｅｅ"]
    result = build_offline_plan(data)
    assert result.exit_code == 0
    assert result.manifest["approval_replay_count"] == 1


def test_trigger_projection_is_bound_and_exhaustive() -> None:
    mismatch = envelope()
    mismatch["trigger_projections"][0]["trigger_fingerprint"] = "sha256:" + "f" * 64
    assert build_offline_plan(mismatch).manifest["reason_codes"] == [
        "M1_TRIGGER_PROJECTION_INVALID"
    ]

    extra = envelope()
    projection = deepcopy(extra["trigger_projections"][0])
    projection["course_id"] = "course-3"
    extra["trigger_projections"].append(projection)
    assert build_offline_plan(extra).manifest["reason_codes"] == [
        "M1_TRIGGER_PROJECTION_INVALID"
    ]


def test_pilot_is_capped_and_must_reference_candidates() -> None:
    data = envelope()
    data["pilot_course_ids"] = [f"course-{index}" for index in range(6)]
    assert build_offline_plan(data).manifest["reason_codes"] == ["M1_PILOT_LIMIT_EXCEEDED"]

    data = envelope()
    data["pilot_course_ids"] = ["course-3"]
    assert build_offline_plan(data).manifest["reason_codes"] == ["HOLD_PILOT_NOT_READY"]


def test_required_state_machine_sequence_and_counters() -> None:
    result = build_offline_plan(envelope())
    state = result.private["state"]
    steps = [
        ("INITIAL_APPLY", False),
        ("INITIAL_APPLY_NOOP", True),
        ("RESTORE", False),
        ("RESTORE_NOOP", True),
        ("FINAL_APPLY", False),
        ("FINAL_APPLY_NOOP", True),
    ]
    for index, (action, noop) in enumerate(steps):
        command = noop_command(state, action, f"command-{index}") if noop else mutation_command(state, action, f"command-{index}")
        advanced = advance_offline_state(state, command)
        assert advanced.exit_code == 0
        state = advanced.private
        counts = state["slot_counts"]
        assert counts["frozen_incomplete_slots"] == (
            counts["remediated_slots"]
            + counts["pending_slots"]
            + counts["hold_slots"]
            + counts["conflict_slots"]
        )
        assert counts["current_incomplete_slots"] == (
            counts["pending_slots"]
            + counts["hold_slots"]
            + counts["conflict_slots"]
            + counts["newly_incomplete_slots"]
        )
        assert counts["unclassified_incomplete_slots"] == 0

    assert state["phase"] == "COMPLETE"
    assert state["sequence"] == [action for action, _ in steps]
    assert state["write_counts"]["initial_metadata_patch_requests_requested"] == 2
    assert state["write_counts"]["initial_metadata_patch_requests_acknowledged"] == 2
    assert state["write_counts"]["initial_field_mutations_verified"] == 2
    assert state["write_counts"]["initial_category_restore_patches_acknowledged"] == 1
    assert state["write_counts"]["restore_category_restore_patches_acknowledged"] == 1
    assert state["write_counts"]["final_category_restore_patches_acknowledged"] == 1
    assert state["write_counts"]["initial_noop_mutations"] == 0
    assert state["slot_counts"]["remediated_slots"] == 2
    assert state["slot_counts"]["pending_slots"] == 0
    assert state["slot_counts"]["current_incomplete_slots"] == 0
    terminal_manifest = advanced.manifest
    assert terminal_manifest["status"] == "M1_SIMULATION_COMPLETE"
    assert terminal_manifest["simulation_only"] is True
    assert terminal_manifest["population_authoritative"] is False
    assert terminal_manifest["remote_execution_authorized"] is False


def test_partial_apply_reconciles_successful_and_not_applied_slots() -> None:
    state = build_offline_plan(envelope()).private["state"]
    command = mutation_command(state, "INITIAL_APPLY", "partial-apply")
    command["outcomes"][1]["metadata_outcome"] = "AMBIGUOUS_NOT_APPLIED"
    command["outcomes"][1]["metadata_poststate"] = "EXACT_PREIMAGE"

    result = advance_offline_state(state, command)

    assert result.exit_code == 2
    assert result.manifest["status"] == "M1_SIMULATION_STOPPED"
    assert result.private["write_counts"]["initial_rows_touched_verified"] == 1
    assert result.private["write_counts"]["initial_field_mutations_verified"] == 1
    counts = result.private["slot_counts"]
    assert counts["remediated_slots"] == 1
    assert counts["pending_slots"] == 1
    assert counts["current_incomplete_slots"] == 1
    assert counts["frozen_incomplete_slots"] == (
        counts["remediated_slots"]
        + counts["pending_slots"]
        + counts["hold_slots"]
        + counts["conflict_slots"]
    )


def test_partial_apply_classifies_conflict_and_mixed_state_slots() -> None:
    state = build_offline_plan(envelope()).private["state"]
    conflict = mutation_command(state, "INITIAL_APPLY", "partial-conflict")
    conflict["outcomes"][1]["metadata_outcome"] = "AMBIGUOUS_CONFLICT"
    conflict["outcomes"][1]["metadata_poststate"] = "CONFLICT"

    conflict_result = advance_offline_state(state, conflict)
    assert conflict_result.private["slot_counts"]["remediated_slots"] == 1
    assert conflict_result.private["slot_counts"]["conflict_slots"] == 1
    assert conflict_result.private["slot_counts"]["pending_slots"] == 0

    mixed = mutation_command(state, "INITIAL_APPLY", "partial-mixed")
    mixed["outcomes"][0]["category_outcome"] = "AMBIGUOUS_UNKNOWN"
    mixed["outcomes"][0]["category_poststate"] = "UNKNOWN"
    mixed_result = advance_offline_state(state, mixed)
    assert mixed_result.private["slot_counts"]["hold_slots"] == 1
    assert mixed_result.private["slot_counts"]["remediated_slots"] == 1
    assert mixed_result.private["slot_counts"]["pending_slots"] == 0


def test_duplicate_command_is_noop_but_changed_payload_is_violation() -> None:
    state = build_offline_plan(envelope()).private["state"]
    command = mutation_command(state, "INITIAL_APPLY", "same-command")
    first = advance_offline_state(state, command)
    replay = advance_offline_state(first.private, command)
    assert replay.exit_code == 0
    assert replay.manifest["status"] == "M1_SIMULATION_STEP_NOOP"
    assert replay.private["sequence"] == ["INITIAL_APPLY"]

    changed = deepcopy(command)
    changed["outcomes"][0]["metadata_outcome"] = "EXACT_ZERO"
    assert advance_offline_state(first.private, changed).manifest["reason_codes"] == ["STOP_SEQUENCE_VIOLATION"]


def test_command_is_bound_to_exact_predecessor_and_sequence() -> None:
    state = build_offline_plan(envelope()).private["state"]
    wrong_digest = mutation_command(state, "INITIAL_APPLY", "wrong-digest")
    wrong_digest["expected_state_digest"] = "sha256:" + "e" * 64
    assert advance_offline_state(state, wrong_digest).manifest["reason_codes"] == [
        "STOP_PREDECESSOR_DRIFT"
    ]

    wrong_sequence = mutation_command(state, "INITIAL_APPLY", "wrong-sequence")
    wrong_sequence["expected_sequence"] = 1
    assert advance_offline_state(state, wrong_sequence).manifest["reason_codes"] == [
        "STOP_SEQUENCE_VIOLATION"
    ]


def test_noop_requires_exact_zero_row_evidence() -> None:
    state = build_offline_plan(envelope()).private["state"]
    state = advance_offline_state(
        state, mutation_command(state, "INITIAL_APPLY", "initial")
    ).private
    command = noop_command(state, "INITIAL_APPLY_NOOP", "bad-noop")
    command["outcomes"][0]["metadata_outcome"] = "ACK_EXACT_ONE"
    result = advance_offline_state(state, command)
    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["STOP_NOOP_EVIDENCE_INVALID"]


def test_failed_writes_do_not_inflate_acknowledged_counters() -> None:
    state = build_offline_plan(envelope()).private["state"]
    command = mutation_command(
        state, "INITIAL_APPLY", "zero-write", metadata_outcome="EXACT_ZERO"
    )
    result = advance_offline_state(state, command)
    counts = result.private["write_counts"]
    assert counts["initial_metadata_patch_requests_requested"] == 2
    assert counts["initial_metadata_patch_requests_acknowledged"] == 0
    assert counts["initial_rows_touched_verified"] == 0
    assert counts["initial_field_mutations_verified"] == 0
    assert counts["initial_category_restore_patches_planned"] == 1
    assert counts["initial_category_restore_patches_requested"] == 0


def test_ambiguous_applied_is_verified_but_not_transport_acknowledged() -> None:
    state = build_offline_plan(envelope()).private["state"]
    command = mutation_command(
        state,
        "INITIAL_APPLY",
        "ambiguous-applied",
        metadata_outcome="AMBIGUOUS_APPLIED",
        category_outcome="AMBIGUOUS_APPLIED",
    )
    result = advance_offline_state(state, command)
    counts = result.private["write_counts"]
    assert result.exit_code == 0
    assert counts["initial_metadata_patch_requests_acknowledged"] == 0
    assert counts["initial_rows_touched_verified"] == 2
    assert counts["initial_category_restore_patches_acknowledged"] == 0
    assert counts["initial_category_restore_patches_verified"] == 1


@pytest.mark.parametrize(
    ("metadata_outcome", "expected"),
    [
        ("EXACT_ZERO", "STOP_EXACT_ONE_FAILURE"),
        ("EXACT_MANY", "STOP_EXACT_ONE_FAILURE"),
        ("AMBIGUOUS_NOT_APPLIED", "STOP_WRITE_NOT_APPLIED"),
        ("AMBIGUOUS_CONFLICT", "STOP_CAS_CONFLICT"),
        ("AMBIGUOUS_UNKNOWN", "HOLD_AMBIGUOUS_WRITE"),
    ],
)
def test_write_outcomes_fail_closed(metadata_outcome: str, expected: str) -> None:
    state = build_offline_plan(envelope()).private["state"]
    command = mutation_command(state, "INITIAL_APPLY", "failure", metadata_outcome=metadata_outcome)
    result = advance_offline_state(state, command)
    assert result.exit_code == 2
    assert expected in result.manifest["reason_codes"]
    assert result.private["phase"] == "STOPPED"


def test_category_mixed_state_is_never_applied() -> None:
    state = build_offline_plan(envelope()).private["state"]
    command = mutation_command(
        state,
        "INITIAL_APPLY",
        "mixed-category",
        category_outcome="AMBIGUOUS_UNKNOWN",
    )
    result = advance_offline_state(state, command)
    assert result.exit_code == 2
    assert result.manifest["reason_codes"] == ["STOP_MIXED_WRITE_STATE"]


def test_out_of_sequence_context_drift_and_state_tampering_stop() -> None:
    state = build_offline_plan(envelope()).private["state"]
    assert advance_offline_state(state, noop_command(state, "RESTORE_NOOP", "skip")).manifest["reason_codes"] == ["STOP_SEQUENCE_VIOLATION"]

    command = mutation_command(state, "INITIAL_APPLY", "context-drift")
    command["context_digest"] = "sha256:" + "f" * 64
    assert advance_offline_state(state, command).manifest["reason_codes"] == ["STOP_CONTEXT_DRIFT"]

    tampered = deepcopy(state)
    tampered["phase"] = "COMPLETE"
    assert advance_offline_state(tampered, command).manifest["reason_codes"] == ["STOP_STATE_TAMPERED"]


@pytest.mark.parametrize("invalid", [None, 1, "input", (), object()])
def test_non_native_input_fails_closed(invalid: object) -> None:
    assert build_offline_plan(invalid).manifest["reason_codes"] == ["M1_INPUT_SCHEMA_INVALID"]


def test_hostile_mapping_is_rejected_without_iteration() -> None:
    class HostileDict(dict):
        def values(self):
            raise AssertionError("must not inspect subclass")

    assert build_offline_plan(HostileDict()).manifest["reason_codes"] == ["M1_INPUT_SCHEMA_INVALID"]


def test_native_input_limits_and_invalid_unicode_fail_closed() -> None:
    too_many = envelope()
    rows = [course(f"course-{index:05d}") for index in range(10_001)]
    too_many["snapshots"] = {"first": rows, "second": deepcopy(rows)}
    too_many["population_expectation"] = population_expectation(rows)
    assert build_offline_plan(too_many).manifest["reason_codes"] == [
        "M1_INPUT_LIMIT_EXCEEDED"
    ]

    invalid_unicode = envelope()
    invalid_unicode["target"]["approval_replays"] = ["\ud800"]
    assert build_offline_plan(invalid_unicode).manifest["reason_codes"] == [
        "M1_INVALID_UNICODE"
    ]

    nested: object = "leaf"
    for _ in range(14):
        nested = [nested]
    assert build_offline_plan(nested).manifest["reason_codes"] == [
        "M1_INPUT_LIMIT_EXCEEDED"
    ]


def test_error_manifests_never_include_private_exception_values() -> None:
    data = envelope()
    data["source_ledger"][0]["source_hash"] = "private-invalid-hash"
    serialized = json.dumps(build_offline_plan(data).manifest, sort_keys=True)
    assert "private-invalid-hash" not in serialized
    assert PROJECT not in serialized
    assert "course-1" not in serialized


def test_empty_active_population_is_not_vacuous_success() -> None:
    data = envelope()
    for snapshot in data["snapshots"].values():
        for row in snapshot:
            row["is_active"] = False
    data["population_expectation"] = population_expectation(
        data["snapshots"]["first"]
    )
    data["source_ledger"] = []
    data["trigger_projections"] = []
    data["pilot_course_ids"] = []
    assert build_offline_plan(data).manifest["reason_codes"] == ["M1_EMPTY_ACTIVE_POPULATION"]


def test_module_has_no_external_capabilities_or_cli() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts/shared/f10_10_metadata_remediation.py"
    source_text = path.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    assert imports.isdisjoint({"os", "pathlib", "requests", "socket", "subprocess", "supabase", "urllib"})
    assert calls.isdisjoint({"open", "getenv", "insert", "patch", "post", "put", "request", "rpc", "upsert"})
    lowered = source_text.casefold()
    assert "db_client" not in lowered
    assert "__main__" not in lowered
    assert "http://" not in lowered
    assert "https://" not in lowered
