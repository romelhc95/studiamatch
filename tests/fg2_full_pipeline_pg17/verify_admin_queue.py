"""Call the exact Admin queue and count RPCs used by AdminCourseQueue.tsx."""

from __future__ import annotations

import os
import sys

import requests

from sitecustomize import SERVICE_JWT, _jwt

BASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
ADMIN_ID = "30000000-0000-0000-0000-000000000001"


def call(name: str, payload: dict, token: str):
    response = requests.post(
        f"{BASE_URL}/rest/v1/rpc/{name}",
        json=payload,
        headers={
            "apikey": os.environ["FG2_FIXTURE_PUBLISHABLE_API_KEY"],
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    return response


def fail(code: str) -> None:
    print(f"phase=admin_queue_rpc|result=FAIL|code={code}")
    raise SystemExit(1)


def main() -> None:
    user_token = _jwt(role="authenticated", sub=ADMIN_ID)
    role_response = call("admin_current_user_role", {}, user_token)
    if role_response.status_code != 200:
        fail("synthetic_admin_identity_http")
    role_value = role_response.json()
    role_code = role_value if role_value in {"admin", "user", "authenticated", "anon", "error"} else "other"
    if role_value != "admin":
        fail(f"synthetic_admin_role_{role_code}")
    aal2_response = call("admin_has_aal2", {}, user_token)
    if aal2_response.status_code != 200 or aal2_response.json() is not True:
        fail("synthetic_admin_aal2")

    queue_payload = {
        "p_first": 20,
        "p_after_cursor": None,
        "p_editorial_status": "pending_review",
        "p_quality_status": None,
        "p_institution_slug": None,
    }
    queue_response = call("admin_get_course_queue_filtered", queue_payload, user_token)
    if queue_response.status_code != 200:
        fail(f"queue_http_{queue_response.status_code}")
    try:
        queue_result = queue_response.json()
        queue_row = queue_result[0]
        courses = queue_row["courses"]
    except (ValueError, IndexError, KeyError, TypeError):
        fail("queue_shape")
    if queue_row.get("error") is not None:
        error_categories = {
            "User is not an active editor": "queue_editor_denied",
            "First must be between 1 and 100": "queue_first_rejected",
            "Invalid editorial status": "queue_editorial_filter_rejected",
            "Invalid quality status": "queue_quality_filter_rejected",
            "Invalid cursor format": "queue_cursor_rejected",
        }
        fail(error_categories.get(queue_row["error"], "queue_error_unclassified"))
    if not isinstance(courses, list):
        fail("queue_courses_missing")
    if len(courses) != 5 or any(row.get("editorial_status") != "pending_review" for row in courses):
        fail("pending_queue_scope")
    slugs = {row.get("institution_slug") for row in courses}
    if slugs != {"fg2-ssr-onboard", "fg2-spa", "fg2-ecommerce"}:
        fail("pending_queue_institutions")

    count_response = call(
        "admin_count_course_queue_filtered",
        {
            "p_editorial_status": "pending_review",
            "p_quality_status": None,
            "p_institution_slug": None,
        },
        user_token,
    )
    if count_response.status_code != 200:
        fail(f"count_http_{count_response.status_code}")
    try:
        count_row = count_response.json()[0]
    except (ValueError, IndexError, KeyError, TypeError):
        fail("count_shape")
    if count_row.get("error") is not None or count_row.get("total") != len(courses):
        fail("queue_count_mismatch")

    public_response = requests.get(
        f"{BASE_URL}/rest/v1/courses_public_effective?select=id",
        headers={
            "apikey": os.environ["FG2_FIXTURE_SECRET_API_KEY"],
            "Authorization": f"Bearer {SERVICE_JWT}",
        },
        timeout=10,
    )
    if public_response.status_code != 200 or public_response.json() != []:
        fail("public_effective_not_empty")
    print("phase=admin_queue_rpc|result=PASS|pending=5|institutions=3|public_effective=0")


if __name__ == "__main__":
    main()
