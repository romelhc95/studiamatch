import re
import sys
import argparse

sys.path.insert(0, '/app')

from scripts.shared.db_client import get_db_client
from scripts.shared.roi_engine import compute_roi, infer_seniority, lookup_market_salary


def duration_text_to_hours(duration_text):
    text = str(duration_text or "").lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(horas?|mes(?:es)?|anos?|años?)", text)
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)
    if unit.startswith("hora"):
        return amount
    if unit.startswith("mes"):
        return amount * 160
    return amount * 1920


def fix_taxonomy_roi(apply_changes=False):
    db = get_db_client()
    courses = db.select_all(
        "courses",
        filters="is_active=eq.true",
        columns="id,name,category,category_id,course_type,duration,price_pen,seniority_level,expected_monthly_salary,roi_months",
        batch_size=1000,
    )

    fixed_count = 0
    skipped_count = 0

    for course in courses:
        category_id = course.get("category_id")
        if not category_id:
            skipped_count += 1
            continue

        duration_hours = duration_text_to_hours(course.get("duration"))
        seniority = infer_seniority(course.get("course_type"), duration_hours)
        salary_base = lookup_market_salary(db, category_id, seniority)
        expected_salary, roi_months = compute_roi(course.get("price_pen"), salary_base, course.get("course_type"))

        payload = {"seniority_level": seniority}
        if expected_salary is not None:
            payload["expected_monthly_salary"] = expected_salary
            payload["roi_months"] = roi_months

        if not apply_changes:
            fixed_count += 1
            continue

        res = db.patch("courses", filters=f"id=eq.{course['id']}", data=payload)
        if res and res.get("status") == "success":
            fixed_count += 1
        else:
            skipped_count += 1

    mode = "Updated" if apply_changes else "Would update"
    print(f"Taxonomy/ROI backfill complete. {mode}: {fixed_count}. Skipped: {skipped_count}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill taxonomy and ROI fields for active courses.")
    parser.add_argument("--apply", action="store_true", help="Persist changes. Without this flag, runs as dry-run.")
    args = parser.parse_args()
    fix_taxonomy_roi(apply_changes=args.apply)
