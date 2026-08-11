from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone


INPUT_SCHEMA = "f10.10-m1-offline-input.v1"
STATE_SCHEMA = "f10.10-m1-offline-state.v1"
COMMAND_SCHEMA = "f10.10-m1-offline-command.v1"
MANIFEST_SCHEMA = "f10.10-m1-sanitized-manifest.v1"
POLICY_ID = "metadata-remediation-v1"
NORMALIZATION_VERSION = "f10.9-metadata-v2"
PLACEHOLDERS = frozenset(("n/a", "none", "por definir"))

MAX_DEPTH = 12
MAX_NODES = 250_000
MAX_TOTAL_CHARS = 8_000_000
MAX_STRING_CHARS = 100_000
MAX_DICT_KEYS = 32
MAX_COURSES = 10_000
MAX_SOURCE_RECORDS = 20_000
MAX_PROVIDER_OUTPUTS = 40_000
MAX_REVIEWS = 40_000
MAX_TRIGGER_PROJECTIONS = 10_000
MAX_PILOT_ROWS = 5
MAX_ID_CHARS = 256

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FIELDS = ("syllabus", "objectives")

ENVELOPE_KEYS = {
    "schema",
    "evaluated_at",
    "target",
    "context",
    "snapshots",
    "population_expectation",
    "source_ledger",
    "provider_ledger",
    "reviewer_ledger",
    "trigger_projections",
    "pilot_course_ids",
}
TARGET_KEYS = {"project_ref", "host_fingerprint", "approval_replays"}
CONTEXT_KEYS = {
    "base_sha",
    "base_tree",
    "schema_fingerprint",
    "trigger_fingerprint",
    "profile_fingerprint",
    "policy_id",
    "normalization_version",
    "writers_paused",
    "schedules_paused",
}
SNAPSHOT_KEYS = {"first", "second"}
POPULATION_KEYS = {
    "total_count",
    "total_ids_digest",
    "active_count",
    "active_ids_digest",
    "attestation_mode",
    "acquisition_manifest_digest",
}
COURSE_KEYS = {
    "id",
    "institution_id",
    "is_active",
    "syllabus",
    "objectives",
    "category",
    "category_id",
    "category_confirmed",
    "other_columns_fingerprint",
}
SOURCE_KEYS = {
    "source_id",
    "course_id",
    "institution_id",
    "field_name",
    "project_ref",
    "host_fingerprint",
    "source_kind",
    "lineage_hash",
    "source_hash",
    "evidence_location_hash",
    "evidence_text",
    "extraction_method",
    "extraction_version",
    "semantic_class",
    "extracted_value",
    "mock",
    "observed_at",
    "freshness_rule",
    "fresh_until",
}
PROVIDER_KEYS = {
    "output_id",
    "course_id",
    "field_name",
    "source_id",
    "provider_identity_hash",
    "status",
    "value",
    "value_hash",
}
REVIEW_KEYS = {
    "review_id",
    "output_id",
    "reviewer_identity_hash",
    "decision",
    "reviewed_value_hash",
    "decided_at",
}
TRIGGER_KEYS = {
    "course_id",
    "syllabus_value_hash",
    "category",
    "category_id",
    "category_confirmed",
    "trigger_fingerprint",
}
COMMAND_KEYS = {
    "schema",
    "command_id",
    "action",
    "context_digest",
    "expected_state_digest",
    "expected_sequence",
    "outcomes",
}
OUTCOME_KEYS = {
    "course_id",
    "metadata_outcome",
    "metadata_poststate",
    "category_outcome",
    "category_poststate",
}

SOURCE_KINDS = {"PERSISTED_FIELD", "DETERMINISTIC_EXTRACTION", "PROVIDER_EVIDENCE"}
PROVIDER_STATUSES = {"SUCCEEDED", "FAILED", "DISCARDED", "SUPERSEDED"}
REVIEW_DECISIONS = {"APPROVED", "REJECTED", "HOLD"}
OUTCOMES = {
    "ACK_EXACT_ONE",
    "AMBIGUOUS_APPLIED",
    "AMBIGUOUS_NOT_APPLIED",
    "AMBIGUOUS_CONFLICT",
    "AMBIGUOUS_UNKNOWN",
    "EXACT_ZERO",
    "EXACT_MANY",
    "NOT_REQUIRED",
}
POSTSTATES = {"EXACT_CANDIDATE", "EXACT_PREIMAGE", "CONFLICT", "UNKNOWN", "NOT_REQUIRED"}

PHASE_ACTIONS = {
    "READY_INITIAL_APPLY": "INITIAL_APPLY",
    "EXPECT_INITIAL_NOOP": "INITIAL_APPLY_NOOP",
    "EXPECT_RESTORE": "RESTORE",
    "EXPECT_RESTORE_NOOP": "RESTORE_NOOP",
    "EXPECT_FINAL_APPLY": "FINAL_APPLY",
    "EXPECT_FINAL_NOOP": "FINAL_APPLY_NOOP",
}
NEXT_PHASE = {
    "INITIAL_APPLY": "EXPECT_INITIAL_NOOP",
    "INITIAL_APPLY_NOOP": "EXPECT_RESTORE",
    "RESTORE": "EXPECT_RESTORE_NOOP",
    "RESTORE_NOOP": "EXPECT_FINAL_APPLY",
    "FINAL_APPLY": "EXPECT_FINAL_NOOP",
    "FINAL_APPLY_NOOP": "COMPLETE",
}
MUTATION_ACTIONS = {"INITIAL_APPLY", "RESTORE", "FINAL_APPLY"}
NOOP_ACTIONS = {"INITIAL_APPLY_NOOP", "RESTORE_NOOP", "FINAL_APPLY_NOOP"}


class M1Error(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class OfflineResult:
    exit_code: int
    private: dict[str, object] | None
    manifest: dict[str, object]


def _require(condition: bool, reason_code: str) -> None:
    if not condition:
        raise M1Error(reason_code)


def _exact_keys(value: object, expected: set[str], reason: str) -> dict[str, object]:
    _require(type(value) is dict, reason)
    typed = value
    _require(all(type(key) is str for key in typed), reason)
    _require(set(typed) == expected, reason)
    return typed


def _string(value: object, reason: str, *, nonempty: bool = True) -> str:
    _require(type(value) is str, reason)
    typed = value
    _require(len(typed) <= MAX_STRING_CHARS, "M1_INPUT_LIMIT_EXCEEDED")
    if nonempty:
        _require(bool(typed), reason)
    try:
        typed.encode("utf-8")
    except UnicodeError as error:
        raise M1Error("M1_INVALID_UNICODE") from error
    return typed


def _id(value: object, reason: str = "M1_INPUT_SCHEMA_INVALID") -> str:
    typed = _string(value, reason)
    _require(len(typed) <= MAX_ID_CHARS, "M1_INPUT_LIMIT_EXCEEDED")
    return typed


def _digest_value(value: object, reason: str = "M1_INPUT_SCHEMA_INVALID") -> str:
    typed = _string(value, reason)
    _require(bool(DIGEST_RE.fullmatch(typed)), reason)
    return typed


def _preflight_native(value: object) -> None:
    stack: list[tuple[object, int]] = [(value, 0)]
    nodes = 0
    chars = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        _require(nodes <= MAX_NODES and depth <= MAX_DEPTH, "M1_INPUT_LIMIT_EXCEEDED")
        if current is None or type(current) in (bool, int):
            if type(current) is int:
                _require(0 <= current <= MAX_NODES, "M1_INPUT_LIMIT_EXCEEDED")
            continue
        if type(current) is str:
            chars += len(current)
            _require(
                len(current) <= MAX_STRING_CHARS and chars <= MAX_TOTAL_CHARS,
                "M1_INPUT_LIMIT_EXCEEDED",
            )
            try:
                current.encode("utf-8")
            except UnicodeError as error:
                raise M1Error("M1_INVALID_UNICODE") from error
            continue
        if type(current) is list:
            _require(
                nodes + len(stack) + len(current) <= MAX_NODES,
                "M1_INPUT_LIMIT_EXCEEDED",
            )
            stack.extend((item, depth + 1) for item in current)
            continue
        if type(current) is dict:
            _require(len(current) <= MAX_DICT_KEYS, "M1_INPUT_LIMIT_EXCEEDED")
            _require(all(type(key) is str for key in current), "M1_INPUT_SCHEMA_INVALID")
            _require(
                nodes + len(stack) + len(current) <= MAX_NODES,
                "M1_INPUT_LIMIT_EXCEEDED",
            )
            for key in current:
                chars += len(key)
                _require(
                    len(key) <= MAX_STRING_CHARS and chars <= MAX_TOTAL_CHARS,
                    "M1_INPUT_LIMIT_EXCEEDED",
                )
                try:
                    key.encode("utf-8")
                except UnicodeError as error:
                    raise M1Error("M1_INVALID_UNICODE") from error
            stack.extend((item, depth + 1) for item in current.values())
            continue
        raise M1Error("M1_INPUT_SCHEMA_INVALID")


def _canonical(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError, UnicodeError) as error:
        raise M1Error("M1_INPUT_SCHEMA_INVALID") from error


def _digest(domain: str, value: object) -> str:
    payload = _canonical(value).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(f"f10.10-m1:{domain}\n".encode("utf-8"))
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return f"sha256:{digest.hexdigest()}"


def _normalize(value: object) -> str:
    if value is None:
        return ""
    typed = _string(value, "M1_INPUT_SCHEMA_INVALID", nonempty=False)
    normalized = unicodedata.normalize("NFKC", typed)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Cf")
    return " ".join(normalized.split()).casefold()


def _timestamp(value: object) -> datetime:
    typed = _string(value, "M1_INPUT_SCHEMA_INVALID")
    _require(bool(UTC_RE.fullmatch(typed)), "M1_INPUT_SCHEMA_INVALID")
    try:
        parsed = datetime.strptime(typed, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise M1Error("M1_INPUT_SCHEMA_INVALID") from error
    return parsed.replace(tzinfo=timezone.utc)


def _missing(value: object) -> bool:
    normalized = _normalize(value)
    return not normalized or normalized in PLACEHOLDERS


def _value_hash(value: object) -> str:
    return _digest("field-value", value)


def _validate_target(value: object) -> dict[str, object]:
    target = _exact_keys(value, TARGET_KEYS, "M1_TARGET_BINDING_INVALID")
    project_ref = _id(target["project_ref"], "M1_TARGET_BINDING_INVALID")
    host = _digest_value(target["host_fingerprint"], "M1_TARGET_BINDING_INVALID")
    aliases = target["approval_replays"]
    _require(type(aliases) is list and bool(aliases), "M1_TARGET_BINDING_INVALID")
    parsed_aliases = [
        _normalize(_id(alias, "M1_TARGET_BINDING_INVALID")) for alias in aliases
    ]
    _require(all(parsed_aliases), "M1_TARGET_BINDING_INVALID")
    parsed_aliases = sorted(set(parsed_aliases))
    return {
        "project_ref": project_ref,
        "host_fingerprint": host,
        "approval_replays": sorted(parsed_aliases),
    }


def _validate_context(value: object) -> dict[str, object]:
    context = _exact_keys(value, CONTEXT_KEYS, "M1_INPUT_SCHEMA_INVALID")
    for key in ("base_sha", "base_tree"):
        parsed = _string(context[key], "M1_INPUT_SCHEMA_INVALID")
        _require(bool(SHA40_RE.fullmatch(parsed)), "M1_INPUT_SCHEMA_INVALID")
    for key in ("schema_fingerprint", "trigger_fingerprint", "profile_fingerprint"):
        _digest_value(context[key])
    _require(context["policy_id"] == POLICY_ID, "M1_POLICY_MISMATCH")
    _require(context["normalization_version"] == NORMALIZATION_VERSION, "M1_NORMALIZATION_MISMATCH")
    _require(type(context["writers_paused"]) is bool, "M1_INPUT_SCHEMA_INVALID")
    _require(type(context["schedules_paused"]) is bool, "M1_INPUT_SCHEMA_INVALID")
    _require(context["writers_paused"] is True, "STOP_WRITERS_ACTIVE")
    _require(context["schedules_paused"] is True, "STOP_SCHEDULES_ACTIVE")
    return dict(context)


def _validate_course(row: object) -> dict[str, object]:
    parsed = _exact_keys(row, COURSE_KEYS, "M1_INPUT_SCHEMA_INVALID")
    _id(parsed["id"])
    _id(parsed["institution_id"])
    _require(type(parsed["is_active"]) is bool, "M1_INPUT_SCHEMA_INVALID")
    for field in FIELDS + ("category", "category_id"):
        _require(parsed[field] is None or type(parsed[field]) is str, "M1_INPUT_SCHEMA_INVALID")
        if type(parsed[field]) is str:
            _string(parsed[field], "M1_INPUT_SCHEMA_INVALID", nonempty=False)
    _require(
        parsed["category_confirmed"] is None or type(parsed["category_confirmed"]) is bool,
        "M1_INPUT_SCHEMA_INVALID",
    )
    _digest_value(parsed["other_columns_fingerprint"])
    return dict(parsed)


def _course_map(rows: object) -> dict[str, dict[str, object]]:
    _require(type(rows) is list, "M1_INPUT_SCHEMA_INVALID")
    _require(len(rows) <= MAX_COURSES, "M1_INPUT_LIMIT_EXCEEDED")
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        parsed = _validate_course(row)
        course_id = parsed["id"]
        _require(course_id not in result, "M1_DUPLICATE_COURSE_ID")
        result[course_id] = parsed
    return result


def _validate_source(record: object) -> dict[str, object]:
    parsed = _exact_keys(record, SOURCE_KEYS, "M1_INPUT_SCHEMA_INVALID")
    for key in ("source_id", "course_id", "institution_id", "field_name"):
        _id(parsed[key])
    _require(parsed["field_name"] in FIELDS, "M1_INPUT_SCHEMA_INVALID")
    _id(parsed["project_ref"])
    _digest_value(parsed["host_fingerprint"])
    _require(parsed["source_kind"] in SOURCE_KINDS, "M1_INPUT_SCHEMA_INVALID")
    for key in ("lineage_hash", "source_hash", "evidence_location_hash"):
        _digest_value(parsed[key])
    _require(parsed["evidence_text"] is None or type(parsed["evidence_text"]) is str, "M1_INPUT_SCHEMA_INVALID")
    _string(parsed["extraction_method"], "M1_INPUT_SCHEMA_INVALID")
    _string(parsed["extraction_version"], "M1_INPUT_SCHEMA_INVALID")
    _require(parsed["semantic_class"] in {"SYLLABUS", "OBJECTIVES", "GRADUATE_PROFILE", "OTHER"}, "M1_INPUT_SCHEMA_INVALID")
    _require(parsed["extracted_value"] is None or type(parsed["extracted_value"]) is str, "M1_INPUT_SCHEMA_INVALID")
    _require(type(parsed["mock"]) is bool, "M1_INPUT_SCHEMA_INVALID")
    _timestamp(parsed["observed_at"])
    _require(parsed["freshness_rule"] == "VALID_UNTIL_INCLUSIVE", "M1_INPUT_SCHEMA_INVALID")
    _timestamp(parsed["fresh_until"])
    _require(
        parsed["source_hash"] == _value_hash(parsed["extracted_value"]),
        "M1_SOURCE_HASH_MISMATCH",
    )
    return dict(parsed)


def _validate_provider(record: object) -> dict[str, object]:
    parsed = _exact_keys(record, PROVIDER_KEYS, "M1_INPUT_SCHEMA_INVALID")
    for key in ("output_id", "course_id", "field_name", "source_id"):
        _id(parsed[key])
    _require(parsed["field_name"] in FIELDS, "M1_INPUT_SCHEMA_INVALID")
    _digest_value(parsed["provider_identity_hash"])
    _require(parsed["status"] in PROVIDER_STATUSES, "M1_INPUT_SCHEMA_INVALID")
    _require(parsed["value"] is None or type(parsed["value"]) is str, "M1_INPUT_SCHEMA_INVALID")
    _require(parsed["value_hash"] is None or type(parsed["value_hash"]) is str, "M1_INPUT_SCHEMA_INVALID")
    if parsed["status"] == "SUCCEEDED":
        _require(type(parsed["value"]) is str and not _missing(parsed["value"]), "M1_PROVIDER_LEDGER_UNRECONCILED")
        _require(parsed["value_hash"] == _value_hash(parsed["value"]), "M1_PROVIDER_LEDGER_UNRECONCILED")
    return dict(parsed)


def _validate_review(record: object) -> dict[str, object]:
    parsed = _exact_keys(record, REVIEW_KEYS, "M1_INPUT_SCHEMA_INVALID")
    _id(parsed["review_id"])
    _id(parsed["output_id"])
    _digest_value(parsed["reviewer_identity_hash"])
    _require(parsed["decision"] in REVIEW_DECISIONS, "M1_INPUT_SCHEMA_INVALID")
    _require(parsed["reviewed_value_hash"] is None or type(parsed["reviewed_value_hash"]) is str, "M1_INPUT_SCHEMA_INVALID")
    if parsed["reviewed_value_hash"] is not None:
        _digest_value(parsed["reviewed_value_hash"])
    _timestamp(parsed["decided_at"])
    return dict(parsed)


def _validate_trigger(record: object) -> dict[str, object]:
    parsed = _exact_keys(record, TRIGGER_KEYS, "M1_INPUT_SCHEMA_INVALID")
    _id(parsed["course_id"])
    _digest_value(parsed["syllabus_value_hash"])
    _digest_value(parsed["trigger_fingerprint"])
    for key in ("category", "category_id"):
        _require(parsed[key] is None or type(parsed[key]) is str, "M1_INPUT_SCHEMA_INVALID")
    _require(parsed["category_confirmed"] is None or type(parsed["category_confirmed"]) is bool, "M1_INPUT_SCHEMA_INVALID")
    return dict(parsed)


def _validate_population_expectation(value: object) -> dict[str, object]:
    parsed = _exact_keys(value, POPULATION_KEYS, "M1_INPUT_SCHEMA_INVALID")
    for key in ("total_count", "active_count"):
        _require(type(parsed[key]) is int and parsed[key] >= 0, "M1_INPUT_SCHEMA_INVALID")
    for key in ("total_ids_digest", "active_ids_digest"):
        _digest_value(parsed[key])
    _require(
        parsed["attestation_mode"] == "SYNTHETIC_OFFLINE_ONLY",
        "M1_INPUT_SCHEMA_INVALID",
    )
    _digest_value(parsed["acquisition_manifest_digest"])
    _require(parsed["active_count"] <= parsed["total_count"], "M1_INPUT_SCHEMA_INVALID")
    return dict(parsed)


def _population_facts(rows: list[dict[str, object]]) -> dict[str, object]:
    total_ids = sorted(row["id"] for row in rows)
    active_ids = sorted(row["id"] for row in rows if row["is_active"] is True)
    return {
        "total_count": len(total_ids),
        "total_ids_digest": _digest("total-course-ids", total_ids),
        "active_count": len(active_ids),
        "active_ids_digest": _digest("active-course-ids", active_ids),
    }


def _base_manifest(status: str, reasons: list[str]) -> dict[str, object]:
    return {
        "schema": MANIFEST_SCHEMA,
        "status": status,
        "reason_codes": sorted(set(reasons)),
        "network_calls": 0,
        "database_calls": 0,
        "provider_calls": 0,
        "writer_calls": 0,
        "simulation_only": True,
        "population_authoritative": False,
        "remote_execution_authorized": False,
    }


def _error_result(reason: str) -> OfflineResult:
    return OfflineResult(2, None, _base_manifest("M1_SIMULATION_ERROR", [reason]))


def _source_reason(
    source: dict[str, object],
    row: dict[str, object],
    field: str,
    target: dict[str, object],
    evaluated_at: datetime,
) -> str | None:
    if source["institution_id"] != row["institution_id"]:
        return "HOLD_AMBIGUOUS_LINEAGE"
    if source["project_ref"] != target["project_ref"] or source["host_fingerprint"] != target["host_fingerprint"]:
        return "HOLD_AMBIGUOUS_LINEAGE"
    if source["mock"] is True:
        return "HOLD_INSUFFICIENT_EVIDENCE"
    observed_at = _timestamp(source["observed_at"])
    fresh_until = _timestamp(source["fresh_until"])
    if observed_at > evaluated_at:
        return "HOLD_SOURCE_STALE"
    if fresh_until < evaluated_at:
        return "HOLD_SOURCE_STALE"
    if source["semantic_class"] != field.upper():
        return "HOLD_INSUFFICIENT_EVIDENCE"
    if field == "objectives" and source["semantic_class"] == "GRADUATE_PROFILE":
        return "HOLD_INSUFFICIENT_EVIDENCE"
    if source["source_kind"] == "PERSISTED_FIELD" and _missing(row[field]):
        return "HOLD_INSUFFICIENT_EVIDENCE"
    if source["source_kind"] != "PERSISTED_FIELD" and not source["evidence_text"]:
        return "HOLD_INSUFFICIENT_EVIDENCE"
    return None


def _state_seal(state: dict[str, object]) -> str:
    return _digest("private-state", {key: value for key, value in state.items() if key != "seal"})


def _simulation_context(
    target: dict[str, object],
    context: dict[str, object],
    population_expectation: dict[str, object],
    evaluated_at: str,
) -> dict[str, object]:
    return {
        "target_binding": {
            "project_ref": target["project_ref"],
            "host_fingerprint": target["host_fingerprint"],
        },
        "evaluated_at": evaluated_at,
        "context": context,
        "population_expectation": population_expectation,
    }


def _require_slot_accounting(counts: dict[str, object]) -> None:
    keys = (
        "frozen_incomplete_slots",
        "current_incomplete_slots",
        "remediated_slots",
        "pending_slots",
        "hold_slots",
        "conflict_slots",
        "newly_incomplete_slots",
        "unclassified_incomplete_slots",
    )
    _require(
        all(type(counts.get(key)) is int and counts[key] >= 0 for key in keys),
        "M1_UNCLASSIFIED_SLOT",
    )
    _require(
        counts["frozen_incomplete_slots"]
        == counts["remediated_slots"]
        + counts["pending_slots"]
        + counts["hold_slots"]
        + counts["conflict_slots"],
        "M1_UNCLASSIFIED_SLOT",
    )
    _require(
        counts["current_incomplete_slots"]
        == counts["pending_slots"]
        + counts["hold_slots"]
        + counts["conflict_slots"]
        + counts["newly_incomplete_slots"],
        "M1_UNCLASSIFIED_SLOT",
    )
    _require(counts["unclassified_incomplete_slots"] == 0, "M1_UNCLASSIFIED_SLOT")


def _manifest_from_plan(
    status: str,
    reasons: list[str],
    target: dict[str, object],
    context: dict[str, object],
    rows: list[dict[str, object]],
    sources: list[dict[str, object]],
    providers: list[dict[str, object]],
    reviews: list[dict[str, object]],
    triggers: list[dict[str, object]],
    population_expectation: dict[str, object],
    evaluated_at: str,
    counts: dict[str, int],
    plan: list[dict[str, object]],
    state: dict[str, object] | None,
) -> dict[str, object]:
    manifest = _base_manifest(status, reasons)
    manifest.update(
        {
            "target_binding_digest": _digest("target-binding", {"project_ref": target["project_ref"], "host_fingerprint": target["host_fingerprint"]}),
            "approval_replay_count": len(target["approval_replays"]),
            "approval_replay_digest": _digest("approval-replays", target["approval_replays"]),
            "context_digest": _digest(
                "simulation-context",
                _simulation_context(
                    target, context, population_expectation, evaluated_at
                ),
            ),
            "evaluation_boundary_digest": _digest(
                "evaluation-boundary",
                _simulation_context(
                    target, context, population_expectation, evaluated_at
                ),
            ),
            "cohort_digest": _digest("cohort", rows),
            "source_ledger_digest": _digest("source-ledger", sources),
            "provider_ledger_digest": _digest("provider-ledger", providers),
            "reviewer_ledger_digest": _digest("reviewer-ledger", reviews),
            "trigger_projection_digest": _digest("trigger-projections", triggers),
            "population_expectation_digest": _digest(
                "population-expectation", population_expectation
            ),
            "plan_digest": _digest("plan", plan) if plan else None,
            "state_digest": state["seal"] if state else None,
            "counts": counts,
            "sequence": list(state["sequence"]) if state else [],
            "population_authoritative": False,
            "remote_execution_authorized": False,
        }
    )
    return manifest


def build_offline_plan(envelope: object) -> OfflineResult:
    try:
        _preflight_native(envelope)
        root = _exact_keys(envelope, ENVELOPE_KEYS, "M1_INPUT_SCHEMA_INVALID")
        _require(root["schema"] == INPUT_SCHEMA, "M1_INPUT_SCHEMA_INVALID")
        evaluated_at_text = _string(root["evaluated_at"], "M1_INPUT_SCHEMA_INVALID")
        evaluated_at = _timestamp(evaluated_at_text)
        target = _validate_target(root["target"])
        context = _validate_context(root["context"])
        population_expectation = _validate_population_expectation(
            root["population_expectation"]
        )
        snapshots = _exact_keys(root["snapshots"], SNAPSHOT_KEYS, "M1_INPUT_SCHEMA_INVALID")
        first_map = _course_map(snapshots["first"])
        second_map = _course_map(snapshots["second"])
        first_rows = [first_map[key] for key in sorted(first_map)]
        second_rows = [second_map[key] for key in sorted(second_map)]
        _require(first_rows == second_rows, "STOP_FULL_SNAPSHOT_DRIFT")
        first_population = _population_facts(first_rows)
        second_population = _population_facts(second_rows)
        _require(
            all(
                first_population[key] == population_expectation[key]
                for key in first_population
            ),
            "STOP_POPULATION_EXPECTATION_DRIFT",
        )
        _require(
            all(
                second_population[key] == population_expectation[key]
                for key in second_population
            ),
            "STOP_POPULATION_EXPECTATION_DRIFT",
        )
        active_rows = [row for row in first_rows if row["is_active"] is True]
        _require(bool(active_rows), "M1_EMPTY_ACTIVE_POPULATION")

        source_raw = root["source_ledger"]
        provider_raw = root["provider_ledger"]
        review_raw = root["reviewer_ledger"]
        trigger_raw = root["trigger_projections"]
        _require(type(source_raw) is list and len(source_raw) <= MAX_SOURCE_RECORDS, "M1_INPUT_LIMIT_EXCEEDED")
        _require(type(provider_raw) is list and len(provider_raw) <= MAX_PROVIDER_OUTPUTS, "M1_INPUT_LIMIT_EXCEEDED")
        _require(type(review_raw) is list and len(review_raw) <= MAX_REVIEWS, "M1_INPUT_LIMIT_EXCEEDED")
        _require(type(trigger_raw) is list and len(trigger_raw) <= MAX_TRIGGER_PROJECTIONS, "M1_INPUT_LIMIT_EXCEEDED")
        sources = [_validate_source(record) for record in source_raw]
        providers = [_validate_provider(record) for record in provider_raw]
        reviews = [_validate_review(record) for record in review_raw]
        triggers = [_validate_trigger(record) for record in trigger_raw]
        sources.sort(key=lambda record: record["source_id"])
        providers.sort(key=lambda record: record["output_id"])
        reviews.sort(key=lambda record: record["review_id"])
        triggers.sort(key=lambda record: (record["course_id"], record["syllabus_value_hash"]))

        for records, id_key in ((sources, "source_id"), (providers, "output_id"), (reviews, "review_id")):
            identifiers = [record[id_key] for record in records]
            _require(len(identifiers) == len(set(identifiers)), "M1_DUPLICATE_LEDGER_ID")

        provider_by_id = {record["output_id"]: record for record in providers}
        source_by_id = {record["source_id"]: record for record in sources}
        review_by_output: dict[str, list[dict[str, object]]] = {}
        for review in reviews:
            _require(review["output_id"] in provider_by_id, "M1_LEDGER_ORPHAN")
            review_by_output.setdefault(review["output_id"], []).append(review)
        _require(all(len(review_by_output.get(output_id, [])) == 1 for output_id in provider_by_id), "M1_REVIEW_LEDGER_UNRECONCILED")
        for output_id, provider in provider_by_id.items():
            _require(provider["source_id"] in source_by_id, "M1_LEDGER_ORPHAN")
            provider_source = source_by_id[provider["source_id"]]
            _require(
                provider_source["source_kind"] == "PROVIDER_EVIDENCE",
                "M1_PROVIDER_LEDGER_UNRECONCILED",
            )
            _require(
                provider["course_id"] == provider_source["course_id"]
                and provider["field_name"] == provider_source["field_name"],
                "M1_LEDGER_ORPHAN",
            )
            review = review_by_output[output_id][0]
            _require(
                _timestamp(review["decided_at"]) <= evaluated_at,
                "M1_REVIEW_LEDGER_UNRECONCILED",
            )
            if provider["status"] == "SUCCEEDED":
                _require(review["reviewed_value_hash"] == provider["value_hash"], "M1_REVIEW_LEDGER_UNRECONCILED")
            elif review["decision"] == "APPROVED":
                raise M1Error("M1_REVIEW_LEDGER_UNRECONCILED")

        provider_events_by_slot: dict[
            tuple[str, str],
            list[tuple[datetime, str, dict[str, object], dict[str, object]]],
        ] = {}
        for provider in providers:
            review = review_by_output[provider["output_id"]][0]
            provider_events_by_slot.setdefault(
                (provider["course_id"], provider["field_name"]), []
            ).append(
                (
                    _timestamp(review["decided_at"]),
                    provider["output_id"],
                    provider,
                    review,
                )
            )
        terminal_provider_by_slot: dict[
            tuple[str, str], tuple[dict[str, object], dict[str, object]]
        ] = {}
        for slot, events in provider_events_by_slot.items():
            events.sort(key=lambda event: (event[0], event[1]))
            max_time = events[-1][0]
            _require(
                sum(event[0] == max_time for event in events) == 1,
                "M1_PROVIDER_LEDGER_UNRECONCILED",
            )
            terminal_provider_by_slot[slot] = (events[-1][2], events[-1][3])
            _require(
                events[-1][3]["decision"] != "REJECTED",
                "M1_PROVIDER_LEDGER_UNRECONCILED",
            )

        source_by_slot: dict[tuple[str, str], list[dict[str, object]]] = {}
        active_ids = {row["id"] for row in active_rows}
        for source in sources:
            _require(source["course_id"] in first_map, "M1_LEDGER_ORPHAN")
            _require(source["course_id"] in active_ids, "M1_LEDGER_ORPHAN")
            source_by_slot.setdefault((source["course_id"], source["field_name"]), []).append(source)

        trigger_by_course: dict[str, list[dict[str, object]]] = {}
        for trigger in triggers:
            _require(trigger["course_id"] in first_map, "M1_LEDGER_ORPHAN")
            _require(
                trigger["trigger_fingerprint"] == context["trigger_fingerprint"],
                "M1_TRIGGER_PROJECTION_INVALID",
            )
            trigger_by_course.setdefault(trigger["course_id"], []).append(trigger)

        pilot_raw = root["pilot_course_ids"]
        _require(type(pilot_raw) is list and len(pilot_raw) <= MAX_PILOT_ROWS, "M1_PILOT_LIMIT_EXCEEDED")
        pilot_ids = [_id(value) for value in pilot_raw]
        _require(len(pilot_ids) == len(set(pilot_ids)), "M1_PILOT_LIMIT_EXCEEDED")

        plan_by_course: dict[str, dict[str, object]] = {}
        holds: list[str] = []
        conflict_slots = 0
        incomplete_slots = 0
        validated_source_slots = 0
        quality_failure_slots = 0

        for row in active_rows:
            for field in FIELDS:
                slot = (row["id"], field)
                missing = _missing(row[field])
                incomplete_slots += int(missing)
                slot_sources = source_by_slot.get(slot, [])
                if len(slot_sources) != 1:
                    quality_failure_slots += 1
                    if len(slot_sources) > 1:
                        conflict_slots += int(missing)
                        holds.append("HOLD_AMBIGUOUS_LINEAGE")
                    else:
                        holds.append("HOLD_SOURCE_MISSING")
                    continue
                source = slot_sources[0]
                reason = _source_reason(source, row, field, target, evaluated_at)
                if reason:
                    quality_failure_slots += 1
                    holds.append(reason)
                    continue
                candidate_value: object = source["extracted_value"]
                if source["source_kind"] == "PROVIDER_EVIDENCE":
                    terminal = terminal_provider_by_slot.get((row["id"], field))
                    if terminal is None:
                        quality_failure_slots += 1
                        holds.append("HOLD_PROVIDER_FAILED")
                        continue
                    terminal_provider, terminal_review = terminal
                    if terminal_provider["source_id"] != source["source_id"]:
                        quality_failure_slots += 1
                        holds.append("HOLD_EDITORIAL_REVIEW")
                        continue
                    if terminal_provider["status"] != "SUCCEEDED":
                        quality_failure_slots += 1
                        holds.append("HOLD_PROVIDER_FAILED")
                        continue
                    if terminal_review["decision"] != "APPROVED":
                        quality_failure_slots += 1
                        holds.append("HOLD_EDITORIAL_REVIEW")
                        continue
                    candidate_value = terminal_provider["value"]
                if candidate_value is None or _missing(candidate_value):
                    quality_failure_slots += 1
                    holds.append("HOLD_INSUFFICIENT_EVIDENCE")
                    continue
                if not missing:
                    if candidate_value != row[field]:
                        quality_failure_slots += 1
                        holds.append("HOLD_INSUFFICIENT_EVIDENCE")
                    else:
                        validated_source_slots += 1
                    continue
                validated_source_slots += 1
                course_plan = plan_by_course.setdefault(
                    row["id"],
                    {
                        "course_id": row["id"],
                        "preimage": {name: row[name] for name in FIELDS},
                        "candidate": {},
                        "category_preimage": {name: row[name] for name in ("category", "category_id", "category_confirmed")},
                        "category_projection": None,
                        "category_restore_required": False,
                    },
                )
                course_plan["candidate"][field] = candidate_value

        plan = [plan_by_course[key] for key in sorted(plan_by_course)]
        plan_ids = {item["course_id"] for item in plan}
        _require(set(pilot_ids).issubset(active_ids), "M1_INPUT_SCHEMA_INVALID")
        if not set(pilot_ids).issubset(plan_ids):
            holds.append("HOLD_PILOT_NOT_READY")
        if plan and not pilot_ids:
            raise M1Error("M1_PILOT_REQUIRED")

        for item in plan:
            projections = trigger_by_course.get(item["course_id"], [])
            if "syllabus" in item["candidate"]:
                _require(len(projections) == 1, "M1_TRIGGER_PROJECTION_INVALID")
                projection = projections[0]
                _require(
                    projection["syllabus_value_hash"] == _value_hash(item["candidate"]["syllabus"]),
                    "M1_TRIGGER_PROJECTION_INVALID",
                )
                projected = {name: projection[name] for name in ("category", "category_id", "category_confirmed")}
                item["category_projection"] = projected
                item["category_restore_required"] = projected != item["category_preimage"]
            else:
                _require(not projections, "M1_TRIGGER_PROJECTION_INVALID")
            item["pilot"] = item["course_id"] in pilot_ids

        used_trigger_ids = {
            item["course_id"] for item in plan if "syllabus" in item["candidate"]
        }
        if set(trigger_by_course) != used_trigger_ids:
            if holds or conflict_slots or quality_failure_slots:
                holds.append("HOLD_TRIGGER_NOT_READY")
            else:
                raise M1Error("M1_TRIGGER_PROJECTION_INVALID")

        review_counts = {decision: 0 for decision in REVIEW_DECISIONS}
        for review in reviews:
            review_counts[review["decision"]] += 1
        candidate_slots = sum(len(item["candidate"]) for item in plan)
        pilot_plan = [item for item in plan if item["pilot"]]
        pilot_slots = sum(len(item["candidate"]) for item in pilot_plan)
        hold_slots = max(0, incomplete_slots - candidate_slots - conflict_slots)
        pending_slots = candidate_slots
        counts = {
            "total_courses": len(first_rows),
            "active_courses": len(active_rows),
            "active_field_slots": len(active_rows) * 2,
            "complete_slots": len(active_rows) * 2 - incomplete_slots,
            "frozen_incomplete_slots": incomplete_slots,
            "current_incomplete_slots": incomplete_slots,
            "remediated_slots": 0,
            "pending_slots": pending_slots,
            "hold_slots": hold_slots,
            "conflict_slots": conflict_slots,
            "newly_incomplete_slots": 0,
            "unclassified_incomplete_slots": incomplete_slots - pending_slots - hold_slots - conflict_slots,
            "validated_source_slots": validated_source_slots,
            "quality_failure_slots": quality_failure_slots,
            "duplicate_source_slots": sum(1 for records in source_by_slot.values() if len(records) > 1),
            "unclassified_source_slots": len(active_rows) * 2
            - sum(1 for records in source_by_slot.values() if records),
            "provider_outputs_total": len(providers),
            "reviewed_approved": review_counts["APPROVED"],
            "reviewed_rejected": review_counts["REJECTED"],
            "review_holds": review_counts["HOLD"],
            "unreviewed_provider_outputs": len(providers) - len(reviews),
            "pilot_rows": len(pilot_plan),
            "pilot_slots": pilot_slots,
        }
        _require(counts["unclassified_incomplete_slots"] == 0, "M1_UNCLASSIFIED_SLOT")
        _require(counts["unreviewed_provider_outputs"] == 0, "M1_PROVIDER_LEDGER_UNRECONCILED")
        _require_slot_accounting(counts)

        blocking = bool(holds or conflict_slots or quality_failure_slots)
        status = (
            "M1_SIMULATION_BLOCKED"
            if blocking
            else ("M1_SIMULATION_NOOP" if not plan else "M1_SIMULATION_READY")
        )
        state: dict[str, object] | None = None
        if status == "M1_SIMULATION_READY":
            context_digest = _digest(
                "simulation-context",
                _simulation_context(
                    target, context, population_expectation, evaluated_at_text
                ),
            )
            slot_count_keys = (
                "frozen_incomplete_slots",
                "current_incomplete_slots",
                "remediated_slots",
                "pending_slots",
                "hold_slots",
                "conflict_slots",
                "newly_incomplete_slots",
                "unclassified_incomplete_slots",
            )
            state = {
                "schema": STATE_SCHEMA,
                "phase": "READY_INITIAL_APPLY",
                "context_digest": context_digest,
                "target_binding_digest": _digest(
                    "target-binding",
                    {
                        "project_ref": target["project_ref"],
                        "host_fingerprint": target["host_fingerprint"],
                    },
                ),
                "plan_digest": _digest("plan", plan),
                "pilot_plan": pilot_plan,
                "slot_counts": {key: counts[key] for key in slot_count_keys},
                "sequence": [],
                "sequence_number": 0,
                "simulation_only": True,
                "event_log": [],
                "write_counts": {},
                "seal": "",
            }
            state["seal"] = _state_seal(state)
        manifest = _manifest_from_plan(
            status,
            holds,
            target,
            context,
            first_rows,
            sources,
            providers,
            reviews,
            triggers,
            population_expectation,
            evaluated_at_text,
            counts,
            plan,
            state,
        )
        private = {
            "target": target,
            "context": context,
            "rows": first_rows,
            "sources": sources,
            "providers": providers,
            "reviews": reviews,
            "triggers": triggers,
            "population_expectation": population_expectation,
            "plan": plan,
            "state": state,
        }
        return OfflineResult(1 if blocking else 0, private, manifest)
    except Exception as error:
        reason = error.reason_code if isinstance(error, M1Error) else "M1_INTERNAL_ERROR"
        return _error_result(reason)


def _state_manifest(state: dict[str, object], status: str, reasons: list[str]) -> dict[str, object]:
    manifest = _base_manifest(status, reasons)
    manifest.update(
        {
            "context_digest": state["context_digest"],
            "target_binding_digest": state["target_binding_digest"],
            "plan_digest": state["plan_digest"],
            "state_digest": state["seal"],
            "counts": {**state["slot_counts"], **state["write_counts"]},
            "sequence": list(state["sequence"]),
        }
    )
    return manifest


def _classify_write(outcome: dict[str, object], desired: str) -> str | None:
    metadata = outcome["metadata_outcome"]
    poststate = outcome["metadata_poststate"]
    if metadata in {"EXACT_ZERO", "EXACT_MANY"}:
        return "STOP_EXACT_ONE_FAILURE"
    if metadata == "AMBIGUOUS_NOT_APPLIED":
        return "STOP_WRITE_NOT_APPLIED"
    if metadata == "AMBIGUOUS_CONFLICT" or poststate == "CONFLICT":
        return "STOP_CAS_CONFLICT"
    if metadata == "AMBIGUOUS_UNKNOWN" or poststate == "UNKNOWN":
        return "HOLD_AMBIGUOUS_WRITE"
    if metadata not in {"ACK_EXACT_ONE", "AMBIGUOUS_APPLIED"} or poststate != desired:
        return "STOP_UNEXPECTED_COLUMN_CHANGE"
    return None


def _slot_disposition(
    reason: str | None,
    outcome: dict[str, object],
    *,
    category_failed: bool = False,
) -> str:
    if reason is None and not category_failed:
        return "SUCCESS"
    if category_failed or reason in {
        "HOLD_AMBIGUOUS_WRITE",
        "STOP_UNEXPECTED_COLUMN_CHANGE",
        "STOP_MIXED_WRITE_STATE",
    }:
        return "HOLD"
    if reason == "STOP_CAS_CONFLICT":
        return "CONFLICT"
    if reason == "STOP_EXACT_ONE_FAILURE" and outcome["metadata_outcome"] != "EXACT_ZERO":
        return "HOLD"
    return "UNCHANGED"


def _apply_slot_transition(
    counts: dict[str, object],
    action: str,
    slots: int,
    disposition: str,
) -> None:
    source = "remediated_slots" if action == "RESTORE" else "pending_slots"
    if disposition == "UNCHANGED":
        return
    target = {
        "SUCCESS": "pending_slots" if action == "RESTORE" else "remediated_slots",
        "CONFLICT": "conflict_slots",
        "HOLD": "hold_slots",
    }[disposition]
    _require(counts[source] >= slots, "M1_UNCLASSIFIED_SLOT")
    counts[source] -= slots
    counts[target] += slots


def advance_offline_state(state: object, command: object) -> OfflineResult:
    try:
        _preflight_native(state)
        _preflight_native(command)
        _require(type(state) is dict and state.get("schema") == STATE_SCHEMA, "STOP_STATE_TAMPERED")
        current = json.loads(_canonical(state))
        _require(current.get("seal") == _state_seal(current), "STOP_STATE_TAMPERED")
        _require_slot_accounting(current.get("slot_counts", {}))
        parsed = _exact_keys(command, COMMAND_KEYS, "M1_INPUT_SCHEMA_INVALID")
        _require(parsed["schema"] == COMMAND_SCHEMA, "M1_INPUT_SCHEMA_INVALID")
        command_id = _id(parsed["command_id"])
        action = _string(parsed["action"], "M1_INPUT_SCHEMA_INVALID")
        context_digest = _digest_value(parsed["context_digest"])
        _require(context_digest == current["context_digest"], "STOP_CONTEXT_DRIFT")
        expected_state_digest = _digest_value(parsed["expected_state_digest"])
        _require(type(parsed["expected_sequence"]) is int, "M1_INPUT_SCHEMA_INVALID")
        command_digest = _digest("command", parsed)
        prior = [event for event in current["event_log"] if event["command_id"] == command_id]
        if prior:
            _require(len(prior) == 1 and prior[0]["command_digest"] == command_digest, "STOP_SEQUENCE_VIOLATION")
            return OfflineResult(
                0,
                current,
                _state_manifest(current, "M1_SIMULATION_STEP_NOOP", []),
            )
        _require(expected_state_digest == current["seal"], "STOP_PREDECESSOR_DRIFT")
        _require(parsed["expected_sequence"] == current["sequence_number"], "STOP_SEQUENCE_VIOLATION")

        expected = PHASE_ACTIONS.get(current["phase"])
        _require(expected == action, "STOP_SEQUENCE_VIOLATION")
        outcomes_raw = parsed["outcomes"]
        _require(type(outcomes_raw) is list, "M1_INPUT_SCHEMA_INVALID")
        reasons: list[str] = []
        stage_counts: dict[str, int] = {}
        slot_transitions: list[tuple[int, str]] = []

        pilot_plan = current["pilot_plan"]
        if action in NOOP_ACTIONS:
            _require(len(outcomes_raw) == len(pilot_plan), "STOP_EXACT_ONE_FAILURE")
            outcomes: dict[str, dict[str, object]] = {}
            for raw in outcomes_raw:
                outcome = _exact_keys(raw, OUTCOME_KEYS, "M1_INPUT_SCHEMA_INVALID")
                course_id = _id(outcome["course_id"])
                _require(course_id not in outcomes, "STOP_EXACT_ONE_FAILURE")
                outcomes[course_id] = outcome
            _require(set(outcomes) == {item["course_id"] for item in pilot_plan}, "STOP_EXACT_ONE_FAILURE")
            desired = "EXACT_PREIMAGE" if action == "RESTORE_NOOP" else "EXACT_CANDIDATE"
            for item in pilot_plan:
                outcome = outcomes[item["course_id"]]
                _require(
                    outcome["metadata_outcome"] == "EXACT_ZERO"
                    and outcome["metadata_poststate"] == desired,
                    "STOP_NOOP_EVIDENCE_INVALID",
                )
                if item["category_restore_required"] is True:
                    _require(
                        outcome["category_outcome"] == "EXACT_ZERO"
                        and outcome["category_poststate"] == "EXACT_PREIMAGE",
                        "STOP_NOOP_EVIDENCE_INVALID",
                    )
                else:
                    _require(
                        outcome["category_outcome"] == "NOT_REQUIRED"
                        and outcome["category_poststate"] == "NOT_REQUIRED",
                        "STOP_NOOP_EVIDENCE_INVALID",
                    )
            prefix = {
                "INITIAL_APPLY_NOOP": "initial",
                "RESTORE_NOOP": "restore",
                "FINAL_APPLY_NOOP": "final",
            }[action]
            stage_counts[f"{prefix}_noop_attempts"] = len(pilot_plan)
            stage_counts[f"{prefix}_noop_mutations"] = 0
        else:
            _require(len(outcomes_raw) == len(pilot_plan), "STOP_EXACT_ONE_FAILURE")
            outcomes: dict[str, dict[str, object]] = {}
            for raw in outcomes_raw:
                outcome = _exact_keys(raw, OUTCOME_KEYS, "M1_INPUT_SCHEMA_INVALID")
                course_id = _id(outcome["course_id"])
                _require(course_id not in outcomes, "STOP_EXACT_ONE_FAILURE")
                _require(outcome["metadata_outcome"] in OUTCOMES, "M1_INPUT_SCHEMA_INVALID")
                _require(outcome["category_outcome"] in OUTCOMES, "M1_INPUT_SCHEMA_INVALID")
                _require(outcome["metadata_poststate"] in POSTSTATES, "M1_INPUT_SCHEMA_INVALID")
                _require(outcome["category_poststate"] in POSTSTATES, "M1_INPUT_SCHEMA_INVALID")
                outcomes[course_id] = outcome
            _require(set(outcomes) == {item["course_id"] for item in pilot_plan}, "STOP_EXACT_ONE_FAILURE")
            desired = "EXACT_PREIMAGE" if action == "RESTORE" else "EXACT_CANDIDATE"
            prefix = {"INITIAL_APPLY": "initial", "RESTORE": "restore", "FINAL_APPLY": "final"}[action]
            stage_counts[f"{prefix}_metadata_patch_requests_planned"] = len(pilot_plan)
            stage_counts[f"{prefix}_metadata_patch_requests_requested"] = len(pilot_plan)
            stage_counts[f"{prefix}_metadata_patch_requests_acknowledged"] = 0
            stage_counts[f"{prefix}_rows_touched_verified"] = 0
            stage_counts[f"{prefix}_field_mutations_verified"] = 0
            stage_counts[f"{prefix}_category_restore_patches_planned"] = sum(
                item["category_restore_required"] is True for item in pilot_plan
            )
            stage_counts[f"{prefix}_category_restore_patches_requested"] = 0
            stage_counts[f"{prefix}_category_restore_patches_acknowledged"] = 0
            stage_counts[f"{prefix}_category_restore_patches_verified"] = 0
            for item in pilot_plan:
                outcome = outcomes[item["course_id"]]
                reason = _classify_write(outcome, desired)
                if reason:
                    reasons.append(reason)
                    slot_transitions.append(
                        (
                            len(item["candidate"]),
                            _slot_disposition(reason, outcome),
                        )
                    )
                    continue
                if outcome["metadata_outcome"] == "ACK_EXACT_ONE":
                    stage_counts[f"{prefix}_metadata_patch_requests_acknowledged"] += 1
                stage_counts[f"{prefix}_rows_touched_verified"] += 1
                stage_counts[f"{prefix}_field_mutations_verified"] += len(item["candidate"])
                category_required = item["category_restore_required"] is True
                category_failed = False
                if category_required:
                    stage_counts[f"{prefix}_category_restore_patches_requested"] += 1
                    category = outcome["category_outcome"]
                    category_state = outcome["category_poststate"]
                    if category in {"EXACT_ZERO", "EXACT_MANY"}:
                        reasons.append("STOP_EXACT_ONE_FAILURE")
                        category_failed = True
                    elif category in {"AMBIGUOUS_UNKNOWN", "AMBIGUOUS_CONFLICT", "AMBIGUOUS_NOT_APPLIED"} or category_state != "EXACT_PREIMAGE":
                        reasons.append("STOP_MIXED_WRITE_STATE")
                        category_failed = True
                    elif category not in {"ACK_EXACT_ONE", "AMBIGUOUS_APPLIED"}:
                        reasons.append("STOP_MIXED_WRITE_STATE")
                        category_failed = True
                    else:
                        if category == "ACK_EXACT_ONE":
                            stage_counts[f"{prefix}_category_restore_patches_acknowledged"] += 1
                        stage_counts[f"{prefix}_category_restore_patches_verified"] += 1
                elif outcome["category_outcome"] != "NOT_REQUIRED" or outcome["category_poststate"] != "NOT_REQUIRED":
                    reasons.append("STOP_UNEXPECTED_COLUMN_CHANGE")
                    category_failed = True
                slot_transitions.append(
                    (
                        len(item["candidate"]),
                        _slot_disposition(
                            "STOP_MIXED_WRITE_STATE" if category_failed else None,
                            outcome,
                            category_failed=category_failed,
                        ),
                    )
                )

        current["event_log"].append({"command_id": command_id, "command_digest": command_digest})
        current["sequence"].append(action)
        current["sequence_number"] += 1
        for key, value in stage_counts.items():
            current["write_counts"][key] = current["write_counts"].get(key, 0) + value
        if action in MUTATION_ACTIONS:
            for slots, disposition in slot_transitions:
                _apply_slot_transition(
                    current["slot_counts"], action, slots, disposition
                )
            current["slot_counts"]["current_incomplete_slots"] = (
                current["slot_counts"]["pending_slots"]
                + current["slot_counts"]["hold_slots"]
                + current["slot_counts"]["conflict_slots"]
                + current["slot_counts"]["newly_incomplete_slots"]
            )
        _require_slot_accounting(current["slot_counts"])
        if reasons:
            current["phase"] = "STOPPED"
        else:
            current["phase"] = NEXT_PHASE[action]
        current["seal"] = _state_seal(current)
        status = (
            "M1_SIMULATION_STOPPED"
            if reasons
            else (
                "M1_SIMULATION_COMPLETE"
                if current["phase"] == "COMPLETE"
                else (
                    "M1_SIMULATION_STEP_APPLIED"
                    if action in MUTATION_ACTIONS
                    else "M1_SIMULATION_STEP_NOOP"
                )
            )
        )
        return OfflineResult(2 if reasons else 0, current, _state_manifest(current, status, reasons))
    except Exception as error:
        reason = error.reason_code if isinstance(error, M1Error) else "M1_INTERNAL_ERROR"
        return _error_result(reason)
