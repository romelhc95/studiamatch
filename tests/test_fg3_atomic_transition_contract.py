from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/migrations/20261115234509_h1_fg3_atomic_public_transition.sql"


def test_fg3_worker_selects_effective_public_projection_and_uses_one_atomic_rpc():
    source = (ROOT / "scripts/core/integrity_ping.py").read_text(encoding="utf-8")
    db_client = (ROOT / "scripts/shared/db_client.py").read_text(encoding="utf-8")

    assert "'courses_public_effective'" in source
    assert "'courses'" in source
    assert "fg3_apply_public_course_transition" in source
    assert "rpc_once_raise" in source
    assert "patch_if_match_raise" not in source
    assert "_patch_api(" not in source
    assert "DatabaseWriteOutcomeUnknown" in source
    assert "no retry was made" in db_client
    assert "requests.post(" in db_client


def test_atomic_fg3_function_locks_and_rechecks_eligibility_before_field_allowlist_write():
    sql = MIGRATION.read_text(encoding="utf-8")
    function_body = sql.split("AS $function$", 1)[1].split("$function$;", 1)[0]
    written_columns = set(
        re.findall(
            r"UPDATE\s+public\.courses\s+AS\s+course\s+SET\s+([a-z0-9_]+)\s*=",
            function_body,
            flags=re.IGNORECASE,
        )
    )

    assert written_columns == {"last_404_at", "is_active"}
    assert function_body.index("institution_site_profiles") < function_body.index("course_editorial_state")
    assert function_body.index("course_editorial_state") < function_body.index("h2_legacy_public_course_cohort")
    assert function_body.index("h2_legacy_public_course_cohort") < function_body.index("public.courses AS course")
    assert function_body.index("public.courses AS course") < function_body.index("courses_public_effective")
    assert "FOR SHARE" in function_body
    assert "FOR KEY SHARE" in function_body
    assert "FOR UPDATE" in function_body
    assert "IS DISTINCT FROM p_observed_last_404_at" in function_body
    assert "visible.url IS NOT DISTINCT FROM p_url" in function_body
    assert "pg_catalog.to_regclass('private.h2_legacy_public_course_cohort')" in function_body
    assert "INTO _locked_cohort_course_id" in function_body
    assert "INTERVAL '3 days'" in function_body
    assert "p_http_status NOT IN (404, 410)" in function_body
    assert "p_http_status < 200 OR p_http_status >= 300" in function_body


def test_atomic_fg3_uses_existing_course_marker_column_from_project_baselines():
    restore_schema = (ROOT / "db/restore_full_schema.sql").read_text(encoding="utf-8")
    production_init = (ROOT / "db/production_init.sql").read_text(encoding="utf-8")

    assert re.search(r"last_404_at\s+TIMESTAMPTZ", restore_schema)
    assert re.search(r"last_404_at\s+TIMESTAMPTZ", production_init)


def test_atomic_fg3_function_is_fixed_path_and_service_role_only():
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "SECURITY DEFINER\nSET search_path = ''" in sql
    assert "FROM PUBLIC, anon, authenticated, service_role" in sql
    assert "TO service_role" in sql
    assert "COMMENT ON FUNCTION public.fg3_apply_public_course_transition" in sql


def test_pg17_harness_covers_contracted_h2_schema_without_legacy_base_table():
    harness = (ROOT / "tests/h1_fg3_atomic_public_transition_pg17.sh").read_text(encoding="utf-8")

    assert "DROP TABLE private.h2_legacy_public_course_cohort" in harness
    assert "contracted_schema_assertions" in harness
    assert "Atomic strict-public without legacy table" in harness
