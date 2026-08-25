import argparse
import os
import sys
from typing import Any
from urllib.parse import quote

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.shared.db_client import get_db_client
from scripts.shared.editorial_contract import compute_editorial_state


COURSE_COLUMNS = ",".join(
    [
        "id",
        "institution_id",
        "category_id",
        "name",
        "slug",
        "url",
        "category",
        "mode",
        "duration",
        "price_pen",
        "price_status",
        "start_date",
        "start_date_text",
        "updated_at",
    ]
)

STATE_COLUMNS = ",".join(
    [
        "course_id",
        "quality_status",
        "manual_overrides",
        "missing_fields",
        "field_sources",
        "field_timestamps",
        "manual_updated_at",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill H2 course_editorial_state quality fields")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Persist changes through h2_update_course_quality")
    mode.add_argument("--dry-run", action="store_true", help="Preview changes without writes (default)")
    parser.add_argument("--batch-size", type=int, default=500, help="Rows per keyset page, capped at 1000")
    parser.add_argument("--after-id", help="Resume after this course UUID")
    parser.add_argument("--limit", type=int, help="Maximum courses to inspect")
    return parser.parse_args()


def run_backfill(db: Any, apply: bool = False, batch_size: int = 500, after_id: str | None = None, limit: int | None = None) -> dict[str, int]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    batch_size = min(batch_size, 1000)
    stats = {"scanned": 0, "inserted": 0, "updated": 0, "deleted": 0, "noop": 0}
    cursor = after_id

    while True:
        remaining = None if limit is None else max(limit - stats["scanned"], 0)
        if remaining == 0:
            break
        current_batch_size = min(batch_size, remaining) if remaining is not None else batch_size
        filters = f"id=gt.{quote(cursor, safe='')}" if cursor else None
        courses = db.select_service_raise(
            "courses",
            filters=filters,
            columns=COURSE_COLUMNS,
            limit=current_batch_size,
            order="id.asc",
        )
        if not courses:
            break

        states = _load_states(db, [str(course["id"]) for course in courses])
        for course in courses:
            cursor = str(course["id"])
            stats["scanned"] += 1
            existing_state = states.get(cursor, {})
            payload = build_quality_payload(course, existing_state)
            if not existing_state:
                stats["inserted"] += 1
            elif _quality_equal(existing_state, payload):
                stats["noop"] += 1
                continue
            else:
                stats["updated"] += 1

            if apply:
                db.rpc_raise(
                    "h2_update_course_quality",
                    {
                        "p_course_id": cursor,
                        "p_missing_fields": payload["missing_fields"],
                        "p_field_sources": payload["field_sources"],
                        "p_field_timestamps": payload["field_timestamps"],
                        "p_request_id": f"h2-backfill:{cursor}",
                    },
                )

        if len(courses) < current_batch_size:
            break

    return stats


def build_quality_payload(course: dict[str, Any], existing_state: dict[str, Any] | None = None) -> dict[str, Any]:
    existing_state = existing_state or {}
    manual_overrides = _dict(existing_state.get("manual_overrides"))
    computed = compute_editorial_state(
        course,
        manual_overrides=manual_overrides,
        pipeline_timestamp=_string_or_none(course.get("updated_at")),
        manual_timestamp=_string_or_none(existing_state.get("manual_updated_at")),
    )
    field_timestamps = dict(computed.field_timestamps)
    field_timestamps.update(_dict(existing_state.get("field_timestamps")))
    return {
        "quality_status": computed.quality_status,
        "missing_fields": computed.missing_fields,
        "field_sources": computed.field_sources,
        "field_timestamps": field_timestamps,
    }


def _load_states(db: Any, course_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not course_ids:
        return {}
    encoded_ids = ",".join(quote(course_id, safe="") for course_id in course_ids)
    rows = db.select_service_raise(
        "course_editorial_state",
        filters=f"course_id=in.({encoded_ids})",
        columns=STATE_COLUMNS,
        limit=len(course_ids),
        order="course_id.asc",
    )
    return {str(row["course_id"]): row for row in rows or []}


def _quality_equal(existing_state: dict[str, Any], payload: dict[str, Any]) -> bool:
    return (
        existing_state.get("quality_status") == payload["quality_status"]
        and sorted(existing_state.get("missing_fields") or []) == payload["missing_fields"]
        and _dict(existing_state.get("field_sources")) == payload["field_sources"]
        and _dict(existing_state.get("field_timestamps")) == payload["field_timestamps"]
    )


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def main() -> int:
    args = parse_args()
    stats = run_backfill(
        get_db_client(),
        apply=args.apply,
        batch_size=args.batch_size,
        after_id=args.after_id,
        limit=args.limit,
    )
    mode = "APPLY" if args.apply else "DRY_RUN"
    print(
        f"{mode} scanned={stats['scanned']} inserted={stats['inserted']} "
        f"updated={stats['updated']} deleted={stats['deleted']} noop={stats['noop']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
