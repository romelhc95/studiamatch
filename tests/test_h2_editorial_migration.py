import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/migrations/20260825_h2_editorial_layer.sql"
GRANTS_FIX = ROOT / "db/migrations/20260825_h2_editorial_layer_grants_fix.sql"
START_DATE_FIX = ROOT / "db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql"
ALLOWLIST_FIX = ROOT / "db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql"
FORWARD_FIX = ROOT / "db/migrations/20260826_h2_editorial_layer_forward_fix.sql"
SECURITY_REMEDIATION = ROOT / "db/migrations/20260826_h2_security_advisor_remediation.sql"
FIELD_DEFINITIONS_SEED = ROOT / "db/migrations/20260826_h2_seed_editorial_field_definitions.sql"
PUBLIC_VIEW_FIELDS_FIX = ROOT / "db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql"
LEGACY_COMPAT = ROOT / "db/migrations/20260826_h2_development_legacy_public_compat.sql"
PRO_EXPAND = ROOT / "db/migrations/20260827_h2_pro_expand_schema_compat.sql"
PRO_SEED = ROOT / "db/migrations/20260827_h2_pro_seed_editorial_field_definitions.sql"
PRO_BACKFILL = ROOT / "db/migrations/20260827_h2_pro_backfill_editorial_state.sql"
PRO_COHORT = ROOT / "db/migrations/20260827_h2_pro_capture_legacy_cohort.sql"
PRO_CONTRACT_PUBLIC = ROOT / "db/migrations/20260827_h2_pro_contract_public_reader.sql"
PRO_CONTRACT_COHORT = ROOT / "db/migrations/20260827_h2_pro_contract_legacy_cohort.sql"
PRO_ROLLBACK_PUBLIC = ROOT / "db/migrations/20260827_h2_pro_rollback_public_reader_contract.sql"

PRIVATE_PUBLIC_SURFACE_FIELDS = (
    "editorial_status",
    "quality_status",
    "missing_fields",
    "field_sources",
    "field_timestamps",
    "is_sponsored",
    "lead_cta_enabled",
    "sponsored_priority",
    "sponsorship_label",
    "availability_status",
    "editorial_updated_at",
)


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


def security_remediation_sql() -> str:
    return SECURITY_REMEDIATION.read_text(encoding="utf-8")


def field_definitions_seed_sql() -> str:
    return FIELD_DEFINITIONS_SEED.read_text(encoding="utf-8")


def public_view_fields_fix_sql() -> str:
    return PUBLIC_VIEW_FIELDS_FIX.read_text(encoding="utf-8")


def legacy_compat_sql() -> str:
    return LEGACY_COMPAT.read_text(encoding="utf-8")


def pro_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    assert "REVOKE SELECT ON TABLE public.courses FROM anon, authenticated" in text
    assert 'DROP POLICY IF EXISTS "Public read for courses" ON public.courses' in text
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


def test_h2_forward_fix_blocks_direct_public_courses_reads() -> None:
    text = forward_fix_sql()

    assert "DROP POLICY IF EXISTS courses_select_public ON public.courses" in text
    assert "DROP POLICY IF EXISTS courses_select_authenticated ON public.courses" in text
    assert "CREATE POLICY courses_select_public" not in text
    assert "CREATE POLICY courses_select_authenticated" not in text
    assert "CREATE VIEW public.courses_public_effective AS" in text


def test_h2_security_remediation_uses_private_bounded_reader() -> None:
    text = security_remediation_sql()
    private_reader_signature = text.split("CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()", 1)[1].split(")\nLANGUAGE sql", 1)[0]

    assert "CREATE SCHEMA IF NOT EXISTS private" in text
    assert "CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()" in text
    assert "slug VARCHAR" in private_reader_signature
    assert "seniority_level VARCHAR" in private_reader_signature
    assert "slug TEXT" not in private_reader_signature
    assert "seniority_level TEXT" not in private_reader_signature
    assert "SECURITY DEFINER" in text.split("CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()", 1)[1].split("$$;", 1)[0]
    assert "DROP VIEW IF EXISTS public.courses_public_effective" in text
    assert "CREATE OR REPLACE VIEW public.courses_public_effective" in text
    assert "WITH (security_invoker = true)" in text
    assert "SELECT * FROM private.h2_public_courses_effective()" in text
    assert "GRANT SELECT (" not in text
    assert "GRANT SELECT ON TABLE public.courses TO anon" not in text
    assert "REVOKE ALL ON TABLE public.courses FROM anon, authenticated" in text
    assert "REVOKE ALL ON TABLE public.course_editorial_state FROM anon, authenticated" in text
    assert_no_private_public_surface_fields(text)


def test_h2_security_remediation_keeps_public_rpc_invoker() -> None:
    text = security_remediation_sql()
    public_rpc = text.split("CREATE OR REPLACE FUNCTION public.h2_update_course_quality", 1)[1].split("$$;", 1)[0]

    assert "SECURITY DEFINER" not in public_rpc
    assert "CREATE OR REPLACE FUNCTION private.h2_update_course_quality_impl" in text
    assert "CREATE OR REPLACE FUNCTION private.h2_update_course_quality_batch_impl" in text
    assert "CREATE OR REPLACE FUNCTION public.h2_update_course_quality_batch" in text
    assert "pg_advisory_xact_lock" in text
    assert "p_payload_hash is required" in text
    assert "p_items exceeds max batch size 1000" in text
    assert "request_id already exists for a different payload" in text
    assert "p_missing_fields does not match server-side quality contract" in text
    assert "GRANT EXECUTE ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) TO service_role" in text
    assert "GRANT EXECUTE ON FUNCTION public.h2_update_course_quality_batch(JSONB) TO service_role" in text


def test_h2_security_remediation_preserves_safety_gates() -> None:
    text = security_remediation_sql()
    reader = text.split("CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()", 1)[1].split("DROP POLICY IF EXISTS", 1)[0]

    assert "c.is_active = true" in reader
    assert "c.is_verified = true" in reader
    assert "es.editorial_status = 'published'" in reader
    assert "es.quality_status = 'complete'" in reader
    assert "es.availability_status = 'available'" in reader
    assert "p.production_enabled = true" in reader
    assert "DROP POLICY IF EXISTS courses_exclude_release_canary" in text
    assert "REVOKE ALL ON TABLE public.leads FROM anon, authenticated" in text


def test_h2_field_definitions_seed_is_idempotent_and_scoped() -> None:
    text = field_definitions_seed_sql()

    assert "INSERT INTO public.editorial_field_definitions" in text
    assert "ON CONFLICT (field_key) DO UPDATE SET" in text
    assert "DELETE" not in text
    assert "TRUNCATE" not in text
    assert "manual_updated_by" in text
    assert "published_at" in text
    assert "availability_status" in text
    assert "('duration', 'courses.duration', 'hybrid_manual_preferred', true, true" in text
    assert "('editorial_status', 'course_editorial_state.editorial_status', 'manual_owned', true, false" in text
    assert "('manual_overrides', 'course_editorial_state.manual_overrides', 'manual_owned', false, false" in text


def test_h2_public_view_fields_fix_removes_private_fields() -> None:
    text = public_view_fields_fix_sql()

    assert "DROP VIEW IF EXISTS public.courses_public_effective" in text
    assert "DROP FUNCTION IF EXISTS private.h2_public_courses_effective()" in text
    assert text.index("DROP VIEW IF EXISTS public.courses_public_effective") < text.index("CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()")
    assert text.index("DROP FUNCTION IF EXISTS private.h2_public_courses_effective()") < text.index("CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()")
    assert "REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role" in text
    assert "GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role" in text
    assert text.index("REVOKE ALL ON FUNCTION private.h2_public_courses_effective()") < text.index("GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective()")
    assert "WITH (security_invoker = true)" in text
    assert "SELECT * FROM private.h2_public_courses_effective()" in text
    assert_no_private_public_surface_fields(text)


def test_h2_legacy_compat_creates_private_frozen_cohort() -> None:
    text = legacy_compat_sql()

    assert "CREATE TABLE IF NOT EXISTS private.h2_legacy_public_course_cohort" in text
    assert "course_id UUID PRIMARY KEY REFERENCES public.courses(id) ON DELETE RESTRICT" in text
    assert "REVOKE ALL ON TABLE private.h2_legacy_public_course_cohort FROM PUBLIC, anon, authenticated, service_role" in text
    assert "INSERT INTO private.h2_legacy_public_course_cohort" in text
    assert "ON CONFLICT (course_id) DO NOTHING" in text
    assert "c.is_active = true" in text
    assert "c.is_verified = true" in text
    assert "p.production_enabled = true" in text


def test_h2_legacy_compat_preserves_legacy_visible_courses_without_frontend_fallback() -> None:
    text = legacy_compat_sql()
    reader = text.split("CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()", 1)[1].split("$$;", 1)[0]

    assert "LEFT JOIN public.course_editorial_state es ON es.course_id = c.id" in reader
    assert "is_strict_h2_public" in reader
    assert "is_legacy_public" in reader
    assert "WHERE c.is_strict_h2_public = true" in reader
    assert "OR c.is_legacy_public = true" in reader
    assert "CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'name', c.name) ELSE c.name END AS name" in reader
    assert "FROM private.h2_legacy_public_course_cohort cohort" in reader
    assert "SELECT * FROM private.h2_public_courses_effective()" in text
    assert "GRANT SELECT ON TABLE public.courses TO anon" not in text
    assert_no_private_public_surface_fields(text)


def test_h2_pro_expand_is_additive_and_preserves_legacy_courses_reader() -> None:
    text = pro_sql(PRO_EXPAND)

    assert "CREATE TABLE IF NOT EXISTS public.course_editorial_state" in text
    assert "CREATE TABLE IF NOT EXISTS private.h2_legacy_public_course_cohort" in text
    assert "CREATE OR REPLACE VIEW public.courses_public_effective" in text
    assert "WITH (security_invoker = true)" in text
    assert "is_strict_h2_public" in text
    assert "is_legacy_public" in text
    assert "REVOKE SELECT ON TABLE public.courses FROM anon, authenticated" not in text
    assert "DROP POLICY IF EXISTS courses_select_public ON public.courses" not in text
    assert "DROP POLICY IF EXISTS \"Public read for courses\" ON public.courses" not in text
    assert "CREATE OR REPLACE FUNCTION public.h2_public_courses_effective()" not in text
    assert "GRANT USAGE ON SCHEMA private TO anon, authenticated, service_role" in text
    assert "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA private FROM PUBLIC, anon, authenticated" in text
    assert "ALTER DEFAULT PRIVILEGES IN SCHEMA private REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated" in text
    assert "GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role" in text
    assert "SELECT * FROM private.h2_public_courses_effective()" in text
    assert "CREATE OR REPLACE FUNCTION public.h2_verify_expand_compat" in text
    assert "GRANT EXECUTE ON FUNCTION public.h2_verify_expand_compat(INTEGER, TEXT) TO service_role" in text
    assert "H2 cohort digest mismatch" in text
    assert "https://canary.invalid/%" in text
    assert "duplicate course institution_id+slug pairs block idx_courses_institution_slug_h2" in text
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_institution_slug_h2" in text
    assert "ON public.courses (institution_id, slug)" in text
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_slug_global_h2" not in text
    assert_no_private_public_surface_fields(text)


def test_h2_pro_expand_includes_idempotent_seed_backfill_and_baselined_cohort() -> None:
    seed = pro_sql(PRO_SEED)
    backfill = pro_sql(PRO_BACKFILL)
    cohort = pro_sql(PRO_COHORT)

    assert "ON CONFLICT (field_key) DO UPDATE SET" in seed
    assert "INSERT INTO public.course_editorial_state" in backfill
    assert "ON CONFLICT (course_id) DO NOTHING" in backfill
    assert "private.h2_required_missing_fields(c, '{}'::jsonb)" in backfill
    assert "current_setting('app.h2_expected_eligible_count')::INTEGER" in cohort
    assert "current_setting('app.h2_expected_cohort_digest')" in cohort
    assert "snapshot_ids_sha256" in cohort
    assert "H2 Pro cohort baseline drift" in cohort
    assert "H2 Pro cohort digest drift" in cohort
    assert "SELECT count(*) INTO effective_count FROM public.courses_public_effective" in cohort


def test_h2_pro_contracts_are_separate_and_guarded() -> None:
    public_contract = pro_sql(PRO_CONTRACT_PUBLIC)
    cohort_contract = pro_sql(PRO_CONTRACT_COHORT)

    assert "REVOKE SELECT ON TABLE public.courses FROM PUBLIC, anon, authenticated" in public_contract
    assert "REVOKE INSERT ON TABLE public.leads" not in public_contract
    assert "REVOKE EXECUTE ON FUNCTION public.increment_view_count" not in public_contract
    assert "DROP TABLE private.h2_legacy_public_course_cohort" not in public_contract
    assert "missing_count" in public_contract
    assert "snapshot_ids_sha256" in public_contract
    assert "remaining_legacy_only" in cohort_contract
    assert "strict identity mismatch" in cohort_contract
    assert "https://canary.invalid/%" in cohort_contract
    assert "RAISE EXCEPTION 'H2 Pro cannot retire legacy cohort" in cohort_contract
    assert "DROP TABLE private.h2_legacy_public_course_cohort" in cohort_contract
    assert "DROP FUNCTION IF EXISTS public.h2_public_courses_effective()" in cohort_contract
    assert "CREATE OR REPLACE FUNCTION public.h2_public_courses_effective()" not in cohort_contract
    assert "SELECT * FROM private.h2_public_courses_effective()" in cohort_contract
    assert_no_private_public_surface_fields(cohort_contract)


def test_h2_pro_migrations_document_jit_scope() -> None:
    for path in (PRO_EXPAND, PRO_SEED, PRO_BACKFILL, PRO_COHORT, PRO_CONTRACT_PUBLIC, PRO_CONTRACT_COHORT, PRO_ROLLBACK_PUBLIC):
        text = pro_sql(path)
        assert "explicit JIT" in text
        assert "Production" in text


def test_h2_pro_rollback_public_reader_contract_is_forward_only_and_guarded() -> None:
    text = pro_sql(PRO_ROLLBACK_PUBLIC)

    assert "to_regclass('private.h2_legacy_public_course_cohort') IS NULL" in text
    assert "Cannot rollback public reader contract after legacy cohort retirement" in text
    assert "GRANT SELECT ON TABLE public.courses TO anon, authenticated" in text
    assert "CREATE POLICY courses_select_public" in text
    assert "CREATE POLICY courses_select_authenticated" in text
    assert "CREATE POLICY courses_exclude_release_canary" in text
    assert "AS RESTRICTIVE" in text
    assert "GRANT INSERT ON TABLE public.leads" not in text
    assert "GRANT EXECUTE ON FUNCTION public.increment_view_count" not in text


def test_h2_pro_security_definer_functions_use_safe_search_path() -> None:
    for text in (pro_sql(PRO_EXPAND), pro_sql(PRO_CONTRACT_COHORT)):
        for match in re.finditer(r"CREATE OR REPLACE FUNCTION .*?AS \$\$", text, flags=re.DOTALL):
            header = match.group(0)
            if "SECURITY DEFINER" not in header:
                continue
            assert "SET search_path = pg_catalog, pg_temp" in header
            assert "SET search_path = public" not in header


def assert_no_private_public_surface_fields(text: str) -> None:
    reader = text.split("CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()", 1)[1].split("$$;", 1)[0]
    signature = reader.split(")\nLANGUAGE sql", 1)[0]
    body = reader.split("AS $$", 1)[1]
    if "FROM eligible_courses c" in body:
        select_list = body.rsplit("    SELECT", 1)[1].split("FROM eligible_courses c", 1)[0]
    else:
        select_list = body.split("FROM public.courses c", 1)[0]
    for field in PRIVATE_PUBLIC_SURFACE_FIELDS:
        assert field not in signature
        assert field not in select_list
