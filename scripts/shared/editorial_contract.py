from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


REQUIRED_FIELDS: tuple[str, ...] = (
    "name",
    "institution",
    "url",
    "slug",
    "category",
    "mode",
    "duration",
)

OPTIONAL_DISPLAY_DEFAULTS: dict[str, str] = {
    "price_pen": "A consultar",
    "start_date": "Sin confirmar",
    "start_date_text": "Sin confirmar",
}

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "institution": ("institution", "institution_name", "institution_id"),
    "category": ("category", "category_name", "category_id"),
}

MANUAL_SOURCE = "manual_override"
PIPELINE_SOURCE = "pipeline"
DEFAULT_SOURCE = "display_default"


@dataclass(frozen=True)
class EditorialComputation:
    effective_values: dict[str, Any]
    missing_fields: list[str]
    quality_status: str
    field_sources: dict[str, str]
    field_timestamps: dict[str, str]


def compute_editorial_state(
    course: Mapping[str, Any],
    manual_overrides: Mapping[str, Any] | None = None,
    pipeline_timestamp: str | None = None,
    manual_timestamp: str | None = None,
) -> EditorialComputation:
    if not isinstance(course, Mapping) or not course:
        raise ValueError("course must be a non-empty mapping")
    if manual_overrides is None:
        manual_overrides = {}
    if not isinstance(manual_overrides, Mapping):
        raise ValueError("manual_overrides must be a mapping")

    now = datetime.now(timezone.utc).isoformat()
    pipeline_ts = pipeline_timestamp or _string_or_none(course.get("updated_at")) or now
    manual_ts = manual_timestamp or now

    field_keys = set(course.keys()) | set(manual_overrides.keys()) | set(REQUIRED_FIELDS) | set(OPTIONAL_DISPLAY_DEFAULTS)
    effective_values: dict[str, Any] = {}
    field_sources: dict[str, str] = {}
    field_timestamps: dict[str, str] = {}

    for field in sorted(field_keys):
        manual_value = manual_overrides.get(field)
        if _present(manual_value):
            effective_values[field] = manual_value
            field_sources[field] = MANUAL_SOURCE
            field_timestamps[field] = manual_ts
            continue

        pipeline_value = _first_present(course, _keys_for(field))
        if _present(pipeline_value):
            effective_values[field] = pipeline_value
            field_sources[field] = PIPELINE_SOURCE
            field_timestamps[field] = pipeline_ts
            continue

        if field in OPTIONAL_DISPLAY_DEFAULTS:
            effective_values[field] = OPTIONAL_DISPLAY_DEFAULTS[field]
            field_sources[field] = DEFAULT_SOURCE
            field_timestamps[field] = pipeline_ts

    missing_fields = [field for field in REQUIRED_FIELDS if not _present(effective_values.get(field))]
    quality_status = "complete" if not missing_fields else "pending"

    return EditorialComputation(
        effective_values=effective_values,
        missing_fields=missing_fields,
        quality_status=quality_status,
        field_sources=field_sources,
        field_timestamps=field_timestamps,
    )


def _keys_for(field: str) -> tuple[str, ...]:
    return FIELD_ALIASES.get(field, (field,))


def _first_present(values: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = values.get(key)
        if _present(value):
            return value
    return None


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "none", "null", "nan"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _string_or_none(value: Any) -> str | None:
    if not _present(value):
        return None
    return str(value)
