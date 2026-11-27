"""Call the exact Admin queue and count RPCs used by AdminCourseQueue.tsx."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import requests

from sitecustomize import SERVICE_JWT, _jwt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.maintenance.check_db_parity import (
    FG2_PROFILE_ONBOARDING_COLUMNS,
    FG2_PROFILE_ONBOARDING_CONSTRAINTS,
)

BASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
ADMIN_ID = "30000000-0000-0000-0000-000000000001"
UTEC_EXPECTED_URL = "https://posgrado.utec.edu.pe/maestrias/ciencia-de-datos-inteligencia-artificial"


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


def verify_utec_review_queue() -> None:
    user_token = _jwt(role="authenticated", sub=ADMIN_ID)
    role_response = call("admin_current_user_role", {}, user_token)
    aal2_response = call("admin_has_aal2", {}, user_token)
    if role_response.status_code != 200 or role_response.json() != "admin":
        raise SystemExit("phase=utec_admin_queue|result=FAIL|code=fixture_admin_gate")
    if aal2_response.status_code != 200 or aal2_response.json() is not True:
        raise SystemExit("phase=utec_admin_queue|result=FAIL|code=fixture_admin_gate")
    response = call(
        "admin_get_course_queue_filtered",
        {
            "p_first": 20,
            "p_after_cursor": None,
            "p_editorial_status": "pending_review",
            "p_quality_status": None,
            "p_institution_slug": "utec",
        },
        user_token,
    )
    if response.status_code != 200:
        raise SystemExit(f"phase=utec_admin_queue|result=FAIL|code=rpc_http_{response.status_code}")
    try:
        row = response.json()[0]
        courses = row["courses"]
    except (ValueError, IndexError, KeyError, TypeError):
        raise SystemExit("phase=utec_admin_queue|result=FAIL|code=rpc_shape") from None
    if row.get("error") is not None or not isinstance(courses, list) or len(courses) != 1:
        raise SystemExit("phase=utec_admin_queue|result=FAIL|code=utec_queue_count")
    course = courses[0]
    if (
        course.get("institution_slug") != "utec"
        or str(course.get("course_url") or "").rstrip("/") != UTEC_EXPECTED_URL.rstrip("/")
        or course.get("editorial_status") != "pending_review"
    ):
        raise SystemExit("phase=utec_admin_queue|result=FAIL|code=editorial_queue_contract")
    print("phase=utec_admin_queue|result=PASS|rows=1|editorial=pending_review|public_effective=0")


def verify_fg2_profile_schema_contract() -> None:
    endpoint = f"{BASE_URL}/rest/v1/rpc/fg2_profile_onboarding_schema_contract"
    headers = {
        "apikey": os.environ["FG2_FIXTURE_PUBLISHABLE_API_KEY"],
        "Authorization": f"Bearer {SERVICE_JWT}",
    }
    response = requests.get(endpoint, headers=headers, timeout=10)
    if response.status_code != 200:
        fail(f"profile_schema_contract_service_http_{response.status_code}")
    try:
        contract = response.json()
        columns = contract["columns"]
        constraints = contract["constraints"]
        function = contract["function"]
    except (ValueError, KeyError, TypeError):
        fail("profile_schema_contract_shape")
    expected_constraints = set(FG2_PROFILE_ONBOARDING_CONSTRAINTS)
    if not isinstance(columns, dict) or not isinstance(constraints, dict) or not isinstance(function, dict):
        fail("profile_schema_contract_shape")
    mismatches = []
    if contract.get("schema_version") != 1:
        mismatches.append("schema_version")
    if contract.get("table_exists") is not True:
        mismatches.append("table_exists")
    if contract.get("effective_modes_nullable") is not True:
        mismatches.append("effective_modes_nullable")
    if set(columns) != set(FG2_PROFILE_ONBOARDING_COLUMNS):
        mismatches.append("column_set")
    for name, expected in FG2_PROFILE_ONBOARDING_COLUMNS.items():
        actual = columns.get(name)
        if not isinstance(actual, dict) or any(
            actual.get(key) != value
            for key, value in zip(("data_type", "is_nullable", "column_default"), expected)
        ):
            mismatches.append(f"column_{name}")
    if not expected_constraints.issubset(constraints):
        mismatches.append("constraint_set")
    for name, expected in FG2_PROFILE_ONBOARDING_CONSTRAINTS.items():
        actual = constraints.get(name)
        if (
            not isinstance(actual, dict)
            or actual.get("validated") is not True
            or re.sub(r"\s+", " ", str(actual.get("definition", "")).lower()).strip()
            != re.sub(r"\s+", " ", expected.lower()).strip()
        ):
            mismatches.append(f"constraint_{name}")
    for name, expected in {
        "identity_arguments": "",
        "return_type": "jsonb",
        "volatility": "s",
        "security_definer": False,
        "search_path": ["search_path=pg_catalog"],
        "anon_can_execute": False,
        "authenticated_can_execute": False,
        "service_role_can_execute": True,
    }.items():
        if function.get(name) != expected:
            mismatches.append(f"function_{name}")
    if mismatches:
        fail("profile_schema_contract_mismatch_" + "_".join(mismatches))

    public_response = requests.get(
        endpoint,
        headers={"apikey": os.environ["FG2_FIXTURE_PUBLISHABLE_API_KEY"]},
        timeout=10,
    )
    if public_response.status_code not in (401, 403, 404):
        fail(f"profile_schema_contract_public_acl_http_{public_response.status_code}")
    print("phase=fg2_profile_schema_contract|result=PASS|columns=6|constraints=4|public=denied")


def main() -> None:
    if sys.argv[1:] == ["--utec-reviewed-exact"]:
        verify_utec_review_queue()
        return
    verify_fg2_profile_schema_contract()
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
