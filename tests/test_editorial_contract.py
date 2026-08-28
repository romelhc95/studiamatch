import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.shared.editorial_contract import (
    CONTRACT_VERSION,
    DEFAULT_SOURCE,
    MANUAL_SOURCE,
    PIPELINE_SOURCE,
    canonical_quality_hash,
    compute_editorial_state,
)


BASE_COURSE = {
    "id": "course-1",
    "name": "Diplomado en Data",
    "institution_id": "inst-1",
    "url": "https://example.edu/data",
    "slug": "diplomado-data",
    "category_id": "cat-1",
    "mode": "Remoto",
    "duration": "6 meses",
    "updated_at": "2026-08-25T10:00:00+00:00",
}


def test_complete_course_computes_complete_quality() -> None:
    result = compute_editorial_state(BASE_COURSE)

    assert result.quality_status == "complete"
    assert result.missing_fields == []
    assert result.effective_values["name"] == "Diplomado en Data"
    assert result.effective_values["institution"] == "inst-1"
    assert result.effective_values["category"] == "cat-1"
    assert result.field_sources["name"] == PIPELINE_SOURCE
    assert result.field_timestamps["name"] == BASE_COURSE["updated_at"]


def test_manual_overrides_take_precedence_and_keep_timestamp() -> None:
    result = compute_editorial_state(
        BASE_COURSE,
        manual_overrides={"mode": "Hibrido", "duration": "8 meses"},
        manual_timestamp="2026-08-25T11:00:00+00:00",
    )

    assert result.quality_status == "complete"
    assert result.effective_values["mode"] == "Hibrido"
    assert result.effective_values["duration"] == "8 meses"
    assert result.field_sources["mode"] == MANUAL_SOURCE
    assert result.field_timestamps["mode"] == "2026-08-25T11:00:00+00:00"
    assert result.field_sources["name"] == PIPELINE_SOURCE


def test_missing_required_fields_keep_course_pending() -> None:
    course = dict(BASE_COURSE)
    course["mode"] = None
    course["duration"] = ""

    result = compute_editorial_state(course)

    assert result.quality_status == "pending"
    assert result.missing_fields == ["mode", "duration"]
    assert "mode" not in result.effective_values
    assert "duration" not in result.effective_values


def test_required_placeholders_are_missing() -> None:
    course = dict(BASE_COURSE)
    course["duration"] = "Consultar"

    result = compute_editorial_state(course)

    assert result.quality_status == "pending"
    assert result.missing_fields == ["duration"]


def test_optional_price_and_start_date_get_display_defaults() -> None:
    result = compute_editorial_state(BASE_COURSE)

    assert result.effective_values["price_pen"] == "A consultar"
    assert result.effective_values["start_date"] == "Sin confirmar"
    assert result.field_sources["price_pen"] == DEFAULT_SOURCE
    assert result.field_sources["start_date"] == DEFAULT_SOURCE
    assert result.quality_status == "complete"


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="course must be a non-empty mapping"):
        compute_editorial_state({})

    with pytest.raises(ValueError, match="manual_overrides must be a mapping"):
        compute_editorial_state(BASE_COURSE, manual_overrides=[])


def test_canonical_quality_hash_is_stable() -> None:
    payload = {
        "quality_status": "pending",
        "missing_fields": ["duration"],
        "field_sources": {"name": PIPELINE_SOURCE},
        "field_timestamps": {"name": "2026-08-25T10:00:00+00:00"},
    }

    assert len(canonical_quality_hash(payload)) == 64
    assert canonical_quality_hash(payload) == canonical_quality_hash(dict(reversed(payload.items())))
    assert CONTRACT_VERSION == "h2-quality-v2"
