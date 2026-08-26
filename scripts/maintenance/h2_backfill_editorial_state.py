import argparse
import os
import sys
from typing import Any
from urllib.parse import quote, urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.shared.db_client import get_db_client
from scripts.shared.editorial_contract import CONTRACT_VERSION, canonical_quality_hash, compute_editorial_state


FREE_PROJECT_REF = "aqrldlmlszjtgpqiegaa"
MAX_STATE_LOOKUP_IDS = 100


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
    parser.add_argument("--project-ref", default=FREE_PROJECT_REF, help="Required Supabase project ref for --apply")
    return parser.parse_args()


def run_backfill(
    db: Any,
    apply: bool = False,
    batch_size: int = 500,
    after_id: str | None = None,
    limit: int | None = None,
    project_ref: str = FREE_PROJECT_REF,
) -> dict[str, int]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if apply:
        _assert_expected_project(db, project_ref)
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
        batch_operations: list[dict[str, Any]] = []
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
                payload_hash = canonical_quality_hash(payload)
                batch_operations.append(
                    {
                        "course_id": cursor,
                        "missing_fields": payload["missing_fields"],
                        "field_sources": payload["field_sources"],
                        "field_timestamps": payload["field_timestamps"],
                        "request_id": f"h2-backfill:{CONTRACT_VERSION}:{cursor}:{payload_hash}",
                        "payload_hash": payload_hash,
                    }
                )

        if apply and batch_operations:
            result = db.rpc_raise(
                "h2_update_course_quality_batch",
                {"p_items": batch_operations},
            )
            processed = _processed_count(result)
            if processed != len(batch_operations):
                raise RuntimeError(
                    f"H2 backfill batch processed {processed}, expected {len(batch_operations)}"
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
    existing_sources = _dict(existing_state.get("field_sources"))
    existing_timestamps = _dict(existing_state.get("field_timestamps"))
    for field, source in computed.field_sources.items():
        if source == "manual_override" and existing_sources.get(field, "manual_override") == "manual_override":
            existing_timestamp = existing_timestamps.get(field)
            if existing_timestamp:
                field_timestamps[field] = existing_timestamp
    return {
        "quality_status": computed.quality_status,
        "missing_fields": computed.missing_fields,
        "field_sources": computed.field_sources,
        "field_timestamps": field_timestamps,
    }


def _load_states(db: Any, course_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not course_ids:
        return {}
    state_map: dict[str, dict[str, Any]] = {}
    for offset in range(0, len(course_ids), MAX_STATE_LOOKUP_IDS):
        chunk = course_ids[offset : offset + MAX_STATE_LOOKUP_IDS]
        encoded_ids = ",".join(quote(course_id, safe="") for course_id in chunk)
        rows = db.select_service_raise(
            "course_editorial_state",
            filters=f"course_id=in.({encoded_ids})",
            columns=STATE_COLUMNS,
            limit=len(chunk),
            order="course_id.asc",
        )
        state_map.update({str(row["course_id"]): row for row in rows or []})
    return state_map


def _quality_equal(existing_state: dict[str, Any], payload: dict[str, Any]) -> bool:
    return (
        existing_state.get("quality_status") == payload["quality_status"]
        and sorted(existing_state.get("missing_fields") or []) == sorted(payload["missing_fields"])
        and _dict(existing_state.get("field_sources")) == payload["field_sources"]
        and _dict(existing_state.get("field_timestamps")) == payload["field_timestamps"]
    )


def _assert_expected_project(db: Any, project_ref: str) -> None:
    parsed = urlparse(str(getattr(db, "supabase_url", "")))
    host = parsed.netloc or parsed.path
    actual_ref = host.split(".", 1)[0]
    if actual_ref != project_ref:
        raise RuntimeError(
            f"Refusing H2 backfill apply: expected project {project_ref}, got {actual_ref or 'unknown'}"
        )


def _processed_count(result: Any) -> int:
    if isinstance(result, dict):
        return int(result.get("processed", -1))
    if isinstance(result, list) and result and isinstance(result[0], dict):
        return int(result[0].get("processed", -1))
    return -1


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
        project_ref=args.project_ref,
    )
    mode = "APPLY" if args.apply else "DRY_RUN"
    print(
        f"{mode} scanned={stats['scanned']} inserted={stats['inserted']} "
        f"updated={stats['updated']} deleted={stats['deleted']} noop={stats['noop']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
