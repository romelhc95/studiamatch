from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from typing import Sequence


NORMALIZATION_VERSION = "f10.9-metadata-v2"
DEFAULT_PLACEHOLDERS = ("n/a", "none", "por definir")
DEFAULT_PAGE_SIZE = 1000
MAX_SNAPSHOT_ROWS = 10_000
MAX_ROW_KEYS = 32
MAX_COURSE_ID_CHARS = 256
MAX_METADATA_FIELD_CHARS = 100_000
MAX_TOTAL_METADATA_CHARS = 5_000_000
MAX_PLACEHOLDERS = 64
MAX_PLACEHOLDER_CHARS = 256


class MetadataPlannerError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class MetadataGateResult:
    exit_code: int
    manifest: dict[str, object]


@dataclass(frozen=True)
class _CourseState:
    course_id: str
    missing_syllabus: bool
    missing_objectives: bool
    syllabus_fingerprint: str
    objectives_fingerprint: str


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    without_format_controls = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Cf"
    )
    return " ".join(without_format_controls.split()).casefold()


def _fingerprint(values: Sequence[str], *, domain: str) -> str:
    digest = hashlib.sha256()
    digest.update(f"{NORMALIZATION_VERSION}:{domain}\n".encode("utf-8"))
    for value in values:
        try:
            encoded = value.encode("utf-8")
        except UnicodeError as error:
            raise MetadataPlannerError("INVALID_UNICODE") from error
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _normalized_placeholders(placeholders: object) -> tuple[str, ...]:
    if type(placeholders) not in (list, tuple):
        raise MetadataPlannerError("INVALID_PLACEHOLDER_POLICY")
    if len(placeholders) > MAX_PLACEHOLDERS:
        raise MetadataPlannerError("PLACEHOLDER_POLICY_LIMIT_EXCEEDED")
    normalized: list[str] = []
    for placeholder in placeholders:
        if type(placeholder) is not str:
            raise MetadataPlannerError("INVALID_PLACEHOLDER_POLICY")
        if len(placeholder) > MAX_PLACEHOLDER_CHARS:
            raise MetadataPlannerError("PLACEHOLDER_POLICY_LIMIT_EXCEEDED")
        value = _normalize_text(placeholder)
        if not value or value in normalized:
            raise MetadataPlannerError("INVALID_PLACEHOLDER_POLICY")
        normalized.append(value)
    if not normalized:
        raise MetadataPlannerError("INVALID_PLACEHOLDER_POLICY")
    policy = tuple(sorted(normalized))
    _fingerprint(policy, domain="metadata-placeholders")
    return policy


def _validate_page_size(page_size: object) -> int:
    if type(page_size) is not int or page_size <= 0 or page_size > DEFAULT_PAGE_SIZE:
        raise MetadataPlannerError("INVALID_PAGE_SIZE")
    return page_size


def _copy_native_rows(rows: object) -> list[dict[str, object]]:
    if type(rows) not in (list, tuple):
        raise MetadataPlannerError("INVALID_LOCAL_SNAPSHOT")
    if len(rows) > MAX_SNAPSHOT_ROWS:
        raise MetadataPlannerError("SNAPSHOT_LIMIT_EXCEEDED")
    copied: list[dict[str, object]] = []
    total_metadata_chars = 0
    for row in rows:
        if type(row) is not dict:
            raise MetadataPlannerError("INVALID_COURSE_ROW")
        if len(row) > MAX_ROW_KEYS:
            raise MetadataPlannerError("SNAPSHOT_LIMIT_EXCEEDED")
        if any(type(key) is not str for key in row):
            raise MetadataPlannerError("INVALID_COURSE_ROW")
        course_id = row.get("id")
        if type(course_id) is str and len(course_id) > MAX_COURSE_ID_CHARS:
            raise MetadataPlannerError("SNAPSHOT_LIMIT_EXCEEDED")
        for field in ("syllabus", "objectives"):
            value = row.get(field)
            if type(value) is str:
                if len(value) > MAX_METADATA_FIELD_CHARS:
                    raise MetadataPlannerError("SNAPSHOT_LIMIT_EXCEEDED")
                total_metadata_chars += len(value)
                if total_metadata_chars > MAX_TOTAL_METADATA_CHARS:
                    raise MetadataPlannerError("SNAPSHOT_LIMIT_EXCEEDED")
        copied.append(
            {
                key: row[key]
                for key in ("id", "is_active", "syllabus", "objectives")
                if key in row
            }
        )
    return copied


def _parse_active_row(
    row: dict[str, object],
    placeholders: frozenset[str],
) -> _CourseState | None:
    course_id = row.get("id")
    is_active = row.get("is_active")
    if type(course_id) is not str or not course_id or type(is_active) is not bool:
        raise MetadataPlannerError("INVALID_COURSE_ROW")
    if not is_active:
        return None
    if "syllabus" not in row or "objectives" not in row:
        raise MetadataPlannerError("INVALID_COURSE_ROW")

    normalized_fields: list[str] = []
    missing_fields: list[bool] = []
    for field in ("syllabus", "objectives"):
        value = row[field]
        if value is None:
            normalized = ""
        elif type(value) is str:
            normalized = _normalize_text(value)
        else:
            raise MetadataPlannerError("INVALID_COURSE_ROW")
        normalized_fields.append(normalized)
        missing_fields.append(not normalized or normalized in placeholders)

    return _CourseState(
        course_id=course_id,
        missing_syllabus=missing_fields[0],
        missing_objectives=missing_fields[1],
        syllabus_fingerprint=_fingerprint(
            [normalized_fields[0]],
            domain="syllabus-value",
        ),
        objectives_fingerprint=_fingerprint(
            [normalized_fields[1]],
            domain="objectives-value",
        ),
    )


def _collect_local_snapshot(
    rows: object,
    *,
    page_size: int,
    placeholders: frozenset[str],
) -> tuple[_CourseState, ...]:
    native_rows = _copy_native_rows(rows)
    parsed = [
        state
        for state in (_parse_active_row(row, placeholders) for row in native_rows)
        if state is not None
    ]
    parsed.sort(key=lambda state: state.course_id)

    seen_ids: set[str] = set()
    collected: list[_CourseState] = []
    for offset in range(0, len(parsed), page_size):
        page = parsed[offset : offset + page_size]
        if not page or len(page) > page_size:
            raise MetadataPlannerError("INVALID_PAGE")
        for state in page:
            if state.course_id in seen_ids:
                raise MetadataPlannerError("DUPLICATE_COURSE_ID")
            if collected and state.course_id <= collected[-1].course_id:
                raise MetadataPlannerError("UNSTABLE_ID_ORDER")
            seen_ids.add(state.course_id)
            collected.append(state)

    if len(collected) != len(parsed):
        raise MetadataPlannerError("INCOMPLETE_PAGINATION")
    return tuple(collected)


def _cohort_fingerprint(states: Sequence[_CourseState]) -> str:
    return _fingerprint(
        [
            ":".join(
                (
                    state.course_id,
                    str(int(state.missing_syllabus)),
                    str(int(state.missing_objectives)),
                    state.syllabus_fingerprint,
                    state.objectives_fingerprint,
                )
            )
            for state in states
        ],
        domain="metadata-cohort",
    )


def _base_manifest(placeholders: tuple[str, ...] | None) -> dict[str, object]:
    manifest: dict[str, object] = {
        "plan_id": "F10.9-P5",
        "normalization_version": NORMALIZATION_VERSION,
        "provider_calls": 0,
        "writer_calls": 0,
        "data_plane_calls": 0,
    }
    if placeholders is not None:
        manifest["placeholder_policy_fingerprint"] = _fingerprint(
            placeholders,
            domain="metadata-placeholders",
        )
    else:
        manifest["placeholder_policy_status"] = "INVALID"
    return manifest


def run_metadata_gate(
    rows: object,
    *,
    verification_rows: object | None = None,
    page_size: object = DEFAULT_PAGE_SIZE,
    placeholders: object = DEFAULT_PLACEHOLDERS,
) -> MetadataGateResult:
    normalized_placeholders: tuple[str, ...] | None = None
    try:
        normalized_placeholders = _normalized_placeholders(placeholders)
        validated_page_size = _validate_page_size(page_size)
        placeholder_set = frozenset(normalized_placeholders)
        first = _collect_local_snapshot(
            rows,
            page_size=validated_page_size,
            placeholders=placeholder_set,
        )
        second = _collect_local_snapshot(
            rows if verification_rows is None else verification_rows,
            page_size=validated_page_size,
            placeholders=placeholder_set,
        )
        if len(first) != len(second):
            raise MetadataPlannerError("ACTIVE_COUNT_DRIFT")
        first_fingerprint = _cohort_fingerprint(first)
        if first_fingerprint != _cohort_fingerprint(second):
            raise MetadataPlannerError("COHORT_FINGERPRINT_DRIFT")

        missing_syllabus = sum(state.missing_syllabus for state in first)
        missing_objectives = sum(state.missing_objectives for state in first)
        missing_both = sum(
            state.missing_syllabus and state.missing_objectives for state in first
        )
        incomplete = sum(
            state.missing_syllabus or state.missing_objectives for state in first
        )
        status = "PASS" if incomplete == 0 else "BLOCKED"
        manifest = {
            **_base_manifest(normalized_placeholders),
            "status": status,
            "reason_codes": (
                [] if incomplete == 0 else ["MISSING_ACTIVE_COURSE_METADATA"]
            ),
            "active_courses": len(first),
            "incomplete_active_courses": incomplete,
            "missing_syllabus": missing_syllabus,
            "missing_objectives": missing_objectives,
            "missing_both": missing_both,
            "cohort_fingerprint": first_fingerprint,
        }
        return MetadataGateResult(exit_code=0 if status == "PASS" else 1, manifest=manifest)
    except Exception as error:
        reason_code = (
            error.reason_code
            if isinstance(error, MetadataPlannerError)
            else "LOCAL_SNAPSHOT_ERROR"
        )
        return MetadataGateResult(
            exit_code=2,
            manifest={
                **_base_manifest(normalized_placeholders),
                "status": "ERROR",
                "reason_codes": [reason_code],
            },
        )
