import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.maintenance.h2_backfill_editorial_state import build_quality_payload, run_backfill


class FakeDb:
    def __init__(self, courses, states):
        self.courses = courses
        self.states = states
        self.calls = []

    def select_service_raise(self, table, filters=None, columns="*", limit=None, order=None):
        if table == "courses":
            rows = self.courses
            if filters and filters.startswith("id=gt."):
                cursor = filters.split("id=gt.", 1)[1]
                rows = [row for row in rows if row["id"] > cursor]
            return rows[:limit]
        if table == "course_editorial_state":
            return list(self.states.values())
        raise AssertionError(table)

    def rpc_raise(self, function_name, params):
        self.calls.append((function_name, params))
        return {"status": "success"}


def course(course_id="00000000-0000-0000-0000-000000000001", **overrides):
    payload = {
        "id": course_id,
        "institution_id": "inst-1",
        "category_id": "cat-1",
        "name": "Curso Data",
        "slug": "curso-data",
        "url": "https://example.edu/curso-data",
        "category": None,
        "mode": "Remoto",
        "duration": "6 meses",
        "updated_at": "2026-08-25T00:00:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_build_quality_payload_maps_complete_course() -> None:
    payload = build_quality_payload(course())

    assert payload["quality_status"] == "complete"
    assert payload["missing_fields"] == []
    assert payload["field_sources"]["institution"] == "pipeline"
    assert payload["field_sources"]["category"] == "pipeline"


def test_build_quality_payload_preserves_existing_field_timestamps() -> None:
    payload = build_quality_payload(
        course(mode="Presencial"),
        {
            "manual_overrides": {"mode": "Hibrido"},
            "manual_updated_at": "2026-08-24T00:00:00+00:00",
            "field_timestamps": {"mode": "2026-08-20T00:00:00+00:00"},
        },
    )

    assert payload["quality_status"] == "complete"
    assert payload["field_sources"]["mode"] == "manual_override"
    assert payload["field_timestamps"]["mode"] == "2026-08-20T00:00:00+00:00"


def test_dry_run_does_not_write_and_reports_insert() -> None:
    db = FakeDb([course()], {})

    stats = run_backfill(db, apply=False, batch_size=500)

    assert stats == {"scanned": 1, "inserted": 1, "updated": 0, "deleted": 0, "noop": 0}
    assert db.calls == []


def test_apply_uses_quality_rpc_without_publication_fields() -> None:
    db = FakeDb([course()], {})

    stats = run_backfill(db, apply=True, batch_size=500)

    assert stats["inserted"] == 1
    assert len(db.calls) == 1
    function_name, params = db.calls[0]
    assert function_name == "h2_update_course_quality"
    assert params["p_request_id"].startswith("h2-backfill:")
    assert "editorial_status" not in params


def test_second_run_noops_when_quality_matches() -> None:
    payload = build_quality_payload(course())
    existing = {
        "course_id": "00000000-0000-0000-0000-000000000001",
        "quality_status": payload["quality_status"],
        "manual_overrides": {},
        "missing_fields": payload["missing_fields"],
        "field_sources": payload["field_sources"],
        "field_timestamps": payload["field_timestamps"],
        "manual_updated_at": None,
    }
    db = FakeDb([course()], {existing["course_id"]: existing})

    stats = run_backfill(db, apply=True, batch_size=500)

    assert stats == {"scanned": 1, "inserted": 0, "updated": 0, "deleted": 0, "noop": 1}
    assert db.calls == []
