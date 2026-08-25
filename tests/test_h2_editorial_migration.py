from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/migrations/20260825_h2_editorial_layer.sql"
GRANTS_FIX = ROOT / "db/migrations/20260825_h2_editorial_layer_grants_fix.sql"
START_DATE_FIX = ROOT / "db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql"
ALLOWLIST_FIX = ROOT / "db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql"
FORWARD_FIX = ROOT / "db/migrations/20260826_h2_editorial_layer_forward_fix.sql"


def sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def grants_fix_sql() -> str:
    return GRANTS_FIX.read_text(encoding="utf-8")


def start_date_fix_sql() -> str:
    return START_DATE_FIX.read_text(encoding="utf-8")


def allowlist_fix_sql() -> str:
    return ALLOWLIST_FIX.read_text(encoding="utf-8")


def forward_fix_sql() -> str:
    return FORWARD_FIX.read_text(encoding="utf-8")


def test_h2_migration_creates_editorial_layer_objects() -> None:
    text = sql()

    assert "CREATE TABLE IF NOT EXISTS public.editorial_field_definitions" in text
    assert "CREATE TABLE IF NOT EXISTS public.course_editorial_state" in text
    assert "CREATE TABLE IF NOT EXISTS public.course_editorial_audit" in text
    assert "CREATE OR REPLACE VIEW public.courses_public_effective" in text
    assert "WITH (security_invoker = true)" in text


def test_h2_migration_enforces_publication_and_quality_gate() -> None:
    text = sql()

    assert "es.editorial_status = 'published'" in text
    assert "es.quality_status = 'complete'" in text
    assert "c.is_active = true" in text
    assert "c.is_verified = true" in text
    assert "p.production_enabled = true" in text
    assert "COALESCE(es.manual_overrides ->> 'name', c.name)" in text
    assert "THEN (es.manual_overrides ->> 'start_date')::DATE" not in text


def test_h2_migration_has_explicit_rls_and_grants() -> None:
    text = sql()

    for table in (
        "public.editorial_field_definitions",
        "public.course_editorial_state",
        "public.course_editorial_audit",
    ):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in text
        assert f"REVOKE ALL ON TABLE {table} FROM PUBLIC, anon, authenticated" in text

    assert "GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role" in text
    assert "GRANT SELECT (" in text
    assert "manual_updated_by" not in text.split("GRANT SELECT (", 1)[1].split(") ON TABLE public.course_editorial_state", 1)[0]
    assert "course_editorial_state_manual_overrides_public_allowlist" in text
    assert "GRANT SELECT, INSERT ON TABLE public.course_editorial_audit TO service_role" in text
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.course_editorial_audit" not in text
    assert "GRANT ALL ON TABLE public.course_editorial_audit" not in text


def test_h2_migration_does_not_create_privileged_rpc_or_backfill() -> None:
    text = sql().upper()

    assert "SECURITY DEFINER" not in text
    assert "CREATE OR REPLACE FUNCTION" not in text
    assert "INSERT INTO PUBLIC.COURSE_EDITORIAL_STATE" not in text
    assert "UPDATE PUBLIC.COURSES" not in text
    assert "DELETE FROM PUBLIC.COURSES" not in text


def test_h2_state_public_policy_matches_effective_view_gate() -> None:
    text = sql()
    policy = text.split("CREATE POLICY course_editorial_state_public_effective_select", 1)[1].split(
        "DROP POLICY IF EXISTS course_editorial_state_service_all", 1
    )[0]

    assert "editorial_status = 'published'" in policy
    assert "quality_status = 'complete'" in policy
    assert "c.is_active = true" in policy
    assert "c.is_verified = true" in policy
    assert "p.production_enabled = true" in policy


def test_h2_grants_fix_limits_effective_service_role_privileges() -> None:
    text = grants_fix_sql()

    assert "REVOKE ALL ON TABLE public.course_editorial_audit FROM service_role" in text
    assert "GRANT SELECT, INSERT ON TABLE public.course_editorial_audit TO service_role" in text
    assert "REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.course_editorial_audit FROM service_role" in text
    assert "GRANT SELECT ON TABLE public.courses_public_effective TO service_role" in text
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.courses_public_effective FROM service_role" in text


def test_h2_grants_fix_does_not_include_dml_or_rpc() -> None:
    text = grants_fix_sql().upper()

    assert "CREATE OR REPLACE FUNCTION" not in text
    assert "SECURITY DEFINER" not in text
    assert "INSERT INTO" not in text
    assert "UPDATE PUBLIC.COURSES" not in text
    assert "DELETE FROM PUBLIC.COURSES" not in text


def test_h2_start_date_fix_removes_unsafe_date_cast() -> None:
    text = start_date_fix_sql()

    assert "CREATE OR REPLACE VIEW public.courses_public_effective" in text
    assert "WITH (security_invoker = true)" in text
    assert "c.start_date," in text
    assert "(es.manual_overrides ->> 'start_date')::DATE" not in text
    assert "start_date stays pipeline-owned" in text


def test_h2_allowlist_fix_keeps_start_date_pipeline_owned() -> None:
    text = allowlist_fix_sql()

    assert "DROP CONSTRAINT IF EXISTS course_editorial_state_manual_overrides_public_allowlist" in text
    assert "ADD CONSTRAINT course_editorial_state_manual_overrides_public_allowlist" in text
    assert "- 'start_date_text'" in text
    assert "- 'start_date'" not in text
    assert "INSERT INTO" not in text.upper()


def test_h2_forward_fix_adds_typed_contract_fields() -> None:
    text = forward_fix_sql()

    assert "ADD COLUMN IF NOT EXISTS manual_start_date DATE" in text
    assert "ADD COLUMN IF NOT EXISTS sponsored_priority INTEGER" in text
    assert "ADD COLUMN IF NOT EXISTS sponsorship_label TEXT" in text
    assert "ADD COLUMN IF NOT EXISTS availability_status TEXT" in text
    assert "ADD COLUMN IF NOT EXISTS field_timestamps JSONB" in text
    assert "course_editorial_state_availability_status_valid" in text
    assert "availability_status IN ('available', 'unavailable', 'unknown')" in text
    assert "COALESCE(es.manual_start_date, c.start_date) AS start_date" in text
    assert "DROP VIEW IF EXISTS public.courses_public_effective" in text
    assert "manual_overrides," in text.split("GRANT SELECT (", 1)[1].split(") ON TABLE public.course_editorial_state", 1)[0]
    assert "manual_updated_by" not in text.split("GRANT SELECT (", 1)[1].split(") ON TABLE public.course_editorial_state", 1)[0]


def test_h2_forward_fix_makes_audit_append_only_and_idempotent() -> None:
    text = forward_fix_sql()

    assert "ON DELETE RESTRICT" in text
    assert "prevent_course_editorial_audit_update" in text
    assert "prevent_course_editorial_audit_delete" in text
    assert "idx_course_editorial_audit_request_id" in text
    assert "ON CONFLICT (request_id) WHERE request_id IS NOT NULL DO NOTHING" in text
    assert "REVOKE ALL ON FUNCTION public.prevent_course_editorial_audit_mutation() FROM PUBLIC, anon, authenticated" in text


def test_h2_forward_fix_quality_rpc_never_publishes() -> None:
    text = forward_fix_sql()
    function_body = text.split("CREATE OR REPLACE FUNCTION public.h2_update_course_quality", 1)[1].split(
        "REVOKE ALL ON FUNCTION public.prevent_course_editorial_audit_mutation", 1
    )[0]

    assert "GRANT EXECUTE ON FUNCTION public.h2_update_course_quality" in text
    assert "REVOKE ALL ON FUNCTION public.h2_update_course_quality" in text
    assert "WHERE audit.request_id = p_request_id" in function_body
    assert "request_id already exists for a different course" in function_body
    assert "RETURN updated_state" in function_body
    assert "quality_status = EXCLUDED.quality_status" in function_body
    assert "editorial_status = 'published'" not in function_body
    assert "SET editorial_status" not in function_body.upper()


def test_h2_forward_fix_closes_lead_capture_and_marks_legacy_publication_columns() -> None:
    text = forward_fix_sql()

    assert "REVOKE INSERT ON TABLE public.leads FROM anon, authenticated" in text
    assert "DROP POLICY IF EXISTS leads_insert_public ON public.leads" in text
    assert "DROP POLICY IF EXISTS leads_insert_authenticated ON public.leads" in text
    assert "REVOKE EXECUTE ON FUNCTION public.increment_view_count(UUID) FROM PUBLIC, anon, authenticated" in text
    assert "ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY" in text
    assert "Deprecated as publication authority in H2" in text
    assert "duplicate course slugs block idx_courses_slug_global_h2" in text
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_slug_global_h2" in text


def test_h2_forward_fix_public_gate_uses_editorial_state_and_environment_safety() -> None:
    text = forward_fix_sql()
    view = text.split("CREATE VIEW public.courses_public_effective", 1)[1].split(
        "REVOKE ALL ON TABLE public.courses_public_effective", 1
    )[0]
    policy = text.split("CREATE POLICY course_editorial_state_public_effective_select", 1)[1].split(
        "REVOKE ALL ON TABLE public.course_editorial_state", 1
    )[0]

    assert "es.editorial_status = 'published'" in view
    assert "es.quality_status = 'complete'" in view
    assert "es.availability_status = 'available'" in view
    assert "c.is_active = true" not in view
    assert "c.is_verified = true" not in view
    assert "production_enabled = true" in view
    assert "provider_used" not in view
    assert "is_mock_data" not in view
    assert "availability_status = 'available'" in policy


def test_h2_forward_fix_direct_courses_policy_uses_editorial_gate() -> None:
    text = forward_fix_sql()
    public_policy = text.split("CREATE POLICY courses_select_public", 1)[1].split(
        "DROP POLICY IF EXISTS courses_select_authenticated", 1
    )[0]
    auth_policy = text.split("CREATE POLICY courses_select_authenticated", 1)[1].split(
        "DROP POLICY IF EXISTS course_editorial_state_public_effective_select", 1
    )[0]

    for policy in (public_policy, auth_policy):
        assert "public.course_editorial_state es" in policy
        assert "es.editorial_status = 'published'" in policy
        assert "es.quality_status = 'complete'" in policy
        assert "es.availability_status = 'available'" in policy
        assert "production_enabled = true" in policy
