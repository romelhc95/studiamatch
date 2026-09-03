\set ON_ERROR_STOP on

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN CREATE ROLE service_role NOLOGIN; END IF;
END;
$$;
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

CREATE SCHEMA auth;
CREATE TABLE auth.users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    encrypted_password TEXT,
    role TEXT,
    aud TEXT,
    email_confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION auth.uid()
RETURNS UUID
LANGUAGE sql
STABLE
SET search_path = pg_catalog
AS $$
    SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID
$$;

CREATE OR REPLACE FUNCTION auth.jwt()
RETURNS JSONB
LANGUAGE sql
STABLE
SET search_path = pg_catalog
AS $$
    SELECT jsonb_build_object('aal', current_setting('request.jwt.claim.aal', true))
$$;

CREATE TABLE public.institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    website_url TEXT
);

CREATE TABLE public.institution_site_profiles (
    institution_id UUID PRIMARY KEY REFERENCES public.institutions(id) ON DELETE CASCADE,
    pipeline_ready BOOLEAN NOT NULL DEFAULT false,
    production_enabled BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL
);

CREATE TABLE public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES public.institutions(id) ON DELETE CASCADE,
    category_id UUID REFERENCES public.categories(id),
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    url TEXT UNIQUE,
    price_pen NUMERIC,
    price_status TEXT DEFAULT 'publicado',
    mode TEXT,
    duration TEXT,
    category TEXT,
    description_long TEXT,
    syllabus TEXT,
    target_audience TEXT,
    requirements TEXT,
    certification TEXT,
    benefits TEXT,
    objectives TEXT,
    start_date DATE,
    start_date_text TEXT,
    course_type TEXT,
    brochure_url TEXT,
    expected_monthly_salary NUMERIC,
    seniority_level TEXT,
    roi_months NUMERIC,
    provider_used TEXT,
    is_mock_data BOOLEAN DEFAULT false,
    view_count INTEGER DEFAULT 0,
    comparison_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    course_id UUID REFERENCES public.courses(id)
);

CREATE OR REPLACE FUNCTION public.increment_view_count(p_course_id UUID)
RETURNS void
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    UPDATE public.courses SET view_count = view_count + 1 WHERE id = p_course_id;
END;
$$;

\ir ../../db/migrations/20260825_h2_editorial_layer.sql
\ir ../../db/migrations/20260825_h2_editorial_layer_grants_fix.sql
\ir ../../db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql
\ir ../../db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql
\ir ../../db/migrations/20260826_h2_editorial_layer_forward_fix.sql
\ir ../../db/migrations/20260826_h2_security_advisor_remediation.sql
\ir ../../db/migrations/20260826_h2_seed_editorial_field_definitions.sql
\ir ../../db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql

\ir ../../db/migrations/20260828_h3_admin_auth.sql
\ir ../../db/migrations/20260830_h3_expanded_contract.sql
\ir ../../db/migrations/20260828_h3_admin_editorial_rpc.sql
\ir ../../db/migrations/20260828_h3_admin_editorial_reader_rpc.sql
\ir ../../db/migrations/20260828_h3_admin_course_queue_view.sql
\ir ../../db/migrations/20260828_h3_admin_queue_rpc.sql
\ir ../../db/migrations/20260829_h3_rbac_users.sql
\ir ../../db/migrations/20260902_h3_pr_contract.sql
\ir ../../db/migrations/20260903_h3_rbac_contract_fix.sql
\ir ../../db/seeds/h3_admin_seed_local.sql

DO $$
DECLARE
    actual INTEGER;
BEGIN
    SELECT count(*) INTO actual FROM auth.users;
    IF actual <> 5 THEN RAISE EXCEPTION 'expected five local auth users, got %', actual; END IF;

    SELECT count(*) INTO actual FROM public.admin_members WHERE is_active AND role = 'admin';
    IF actual <> 2 THEN RAISE EXCEPTION 'expected two active admins, got %', actual; END IF;

    SELECT count(*) INTO actual FROM public.admin_members WHERE is_active AND role = 'user';
    IF actual <> 2 THEN RAISE EXCEPTION 'expected two active users, got %', actual; END IF;

    SELECT count(*) INTO actual FROM public.admin_members WHERE NOT is_active;
    IF actual <> 1 THEN RAISE EXCEPTION 'expected one inactive member, got %', actual; END IF;

    SELECT count(*) INTO actual FROM public.institutions;
    IF actual <> 5 THEN RAISE EXCEPTION 'expected five institutions, got %', actual; END IF;

    SELECT count(*) INTO actual FROM public.courses;
    IF actual <> 30 THEN RAISE EXCEPTION 'expected thirty courses, got %', actual; END IF;

    SELECT count(*) INTO actual FROM public.course_editorial_state;
    IF actual <> 30 THEN RAISE EXCEPTION 'expected thirty editorial states, got %', actual; END IF;

    IF EXISTS (
        SELECT editorial_status, count(*)
        FROM public.course_editorial_state
        GROUP BY editorial_status
        EXCEPT VALUES ('draft'::text, 10::bigint), ('pending_review', 10), ('published', 5), ('archived', 5)
    ) THEN
        RAISE EXCEPTION 'unexpected editorial status distribution';
    END IF;
END;
$$;

-- Re-run the seed: idempotency must keep every fixture count unchanged.
\ir ../../db/seeds/h3_admin_seed_local.sql

DO $$
DECLARE
    actual INTEGER;
BEGIN
    SELECT count(*) INTO actual FROM auth.users;
    IF actual <> 5 THEN RAISE EXCEPTION 'idempotent seed re-run changed auth user count to %', actual; END IF;

    SELECT count(*) INTO actual FROM public.admin_members WHERE is_active AND role = 'admin';
    IF actual <> 2 THEN RAISE EXCEPTION 'idempotent seed re-run changed active admin count to %', actual; END IF;

    SELECT count(*) INTO actual FROM public.admin_members WHERE is_active AND role = 'user';
    IF actual <> 2 THEN RAISE EXCEPTION 'idempotent seed re-run changed active user count to %', actual; END IF;

    SELECT count(*) INTO actual FROM public.courses;
    IF actual <> 30 THEN RAISE EXCEPTION 'idempotent seed re-run changed course count to %', actual; END IF;
END;
$$;

SELECT set_config('request.jwt.claim.sub', '30000000-0000-0000-0000-000000000001', false);
SELECT set_config('request.jwt.claim.aal', 'aal2', false);

DO $$
DECLARE
    queue_count INTEGER;
    total_count INTEGER;
    first_course UUID := '20000000-0000-0000-0000-000000000011';
    first_result RECORD;
    conflict_result RECORD;
    detail_result RECORD;
    eff_detail RECORD;
    publish_ok RECORD;
    publish_draft RECORD;
    draft_course UUID := '20000000-0000-0000-0000-000000000001';
    role_value TEXT;
BEGIN
    IF NOT public.admin_is_active_admin() THEN
        RAISE EXCEPTION 'local admin identity was not authorized';
    END IF;

    SELECT public.admin_current_user_role() INTO role_value;
    IF role_value <> 'admin' THEN RAISE EXCEPTION 'expected admin role, got %', role_value; END IF;

    SELECT count(*) INTO queue_count FROM public.admin_course_queue;
    IF queue_count <> 25 THEN RAISE EXCEPTION 'expected 25 non-archived queue rows, got %', queue_count; END IF;

    SELECT q.total INTO total_count
    FROM public.admin_count_course_queue('pending_review', 'complete') q;
    IF total_count <> 10 THEN RAISE EXCEPTION 'expected filtered count 10, got %', total_count; END IF;

    SELECT * INTO detail_result
    FROM public.admin_get_course_editorial(first_course);
    IF detail_result.error IS NOT NULL OR detail_result.course ->> 'course_id' <> first_course::text THEN
        RAISE EXCEPTION 'editorial detail reader failed: %', detail_result.error;
    END IF;
    IF jsonb_array_length(detail_result.field_definitions) <> 13 THEN
        RAISE EXCEPTION 'expected 13 editable field definitions';
    END IF;

    SELECT * INTO first_result
    FROM public.admin_update_course(first_course, '{"name":"Programa H3 editado"}'::jsonb, 1, 'local validation');
    IF NOT first_result.success OR first_result.new_version <> 2 THEN
        RAISE EXCEPTION 'admin update failed: %', first_result.error;
    END IF;

    SELECT * INTO conflict_result
    FROM public.admin_update_course(first_course, '{"name":"Conflicto"}'::jsonb, 1, 'stale version');
    IF conflict_result.success OR conflict_result.error NOT LIKE 'Version conflict:%' THEN
        RAISE EXCEPTION 'optimistic lock conflict was not enforced';
    END IF;

    IF (SELECT count(*) FROM public.course_editorial_audit WHERE course_id = first_course AND action = 'update') <> 1 THEN
        RAISE EXCEPTION 'update audit was not appended';
    END IF;

    -- Effective-value reader: manual overrides must win everywhere (course_name, current_values, field current_value).
    SELECT * INTO eff_detail
    FROM public.admin_get_course_editorial(first_course);
    IF eff_detail.error IS NOT NULL THEN
        RAISE EXCEPTION 'effective reader failed: %', eff_detail.error;
    END IF;
    IF eff_detail.course ->> 'course_name' <> 'Programa H3 editado'
       OR eff_detail.course -> 'current_values' ->> 'name' <> 'Programa H3 editado' THEN
        RAISE EXCEPTION 'effective name is inconsistent across the editorial reader';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM jsonb_array_elements(eff_detail.field_definitions) d
        WHERE d->>'field_key' = 'name' AND d->>'current_value' <> 'Programa H3 editado'
    ) THEN
        RAISE EXCEPTION 'field definition current_value ignores manual overrides';
    END IF;

    -- Publish gate: a draft with missing fields must be rejected with a completeness error.
    SELECT * INTO publish_draft
    FROM public.admin_publish_course(draft_course);
    IF publish_draft.success OR publish_draft.error NOT LIKE 'Course is not publishable:%' THEN
        RAISE EXCEPTION 'publish gate did not reject an incomplete course: %', publish_draft.error;
    END IF;

    -- Publish gate: a complete pending_review course can be published by an admin with audit.
    SELECT * INTO publish_ok
    FROM public.admin_publish_course(first_course);
    IF NOT publish_ok.success OR publish_ok.new_status <> 'published' THEN
        RAISE EXCEPTION 'admin publish of a complete course failed: %', publish_ok.error;
    END IF;
    IF (SELECT count(*) FROM public.course_editorial_audit WHERE course_id = first_course AND action = 'publish') <> 1 THEN
        RAISE EXCEPTION 'publish audit was not appended';
    END IF;
END;
$$;

-- Regression: JIT-A remote findings A6 (42804 email type) and A13 (42702 role ambiguity).
DO $$
DECLARE
    member_row RECORD;
    member_count INTEGER;
    adm1 UUID := '30000000-0000-0000-0000-000000000001';
    adm2 UUID := '30000000-0000-0000-0000-000000000002';
    upd_result RECORD;
BEGIN
    SELECT count(*) INTO member_count FROM public.admin_list_members();
    IF member_count <> 5 THEN
        RAISE EXCEPTION 'expected 5 listed members, got %', member_count;
    END IF;

    SELECT * INTO member_row
    FROM public.admin_list_members()
    WHERE user_id = '30000000-0000-0000-0000-000000000001';
    IF member_row.email <> 'admin@studiamatch.com' THEN
        RAISE EXCEPTION 'unexpected listed admin email %', member_row.email;
    END IF;

    SELECT * INTO upd_result FROM public.admin_update_member(adm2, NULL, false);
    IF NOT upd_result.success OR upd_result.is_active THEN
        RAISE EXCEPTION 'admin deactivation failed: %', upd_result.error;
    END IF;

    SELECT * INTO upd_result FROM public.admin_update_member(adm2, NULL, true);
    IF NOT upd_result.success OR NOT upd_result.is_active THEN
        RAISE EXCEPTION 'admin reactivation failed: %', upd_result.error;
    END IF;
END;
$$;

-- USER role tests
DO $$
DECLARE
    denied BOOLEAN;
    detail_result RECORD;
    role_value TEXT;
    user_id UUID := '30000000-0000-0000-0000-000000000003';
    target_course UUID := '20000000-0000-0000-0000-000000000001';
    upd_result RECORD;
    pub_result RECORD;
    arch_result RECORD;
    quality_result RECORD;
    editable_count INTEGER;
    missing_field_editable BOOLEAN;
    complete_field_editable BOOLEAN;
BEGIN
    PERFORM set_config('request.jwt.claim.sub', user_id::text, false);

    SELECT public.admin_current_user_role() INTO role_value;
    IF role_value <> 'user' THEN RAISE EXCEPTION 'expected user role, got %', role_value; END IF;

    SELECT public.admin_is_active_editor() INTO denied;
    IF NOT denied THEN RAISE EXCEPTION 'user should be active editor'; END IF;

    SELECT public.admin_is_active_admin() INTO denied;
    IF denied THEN RAISE EXCEPTION 'user must not be admin'; END IF;

    -- user can read the queue and detail
    SELECT * INTO detail_result
    FROM public.admin_get_course_editorial(target_course);
    IF detail_result.error IS NOT NULL THEN
        RAISE EXCEPTION 'user editorial detail reader failed: %', detail_result.error;
    END IF;

    -- course 1 has missing_fields = ['description_long','requirements']
    SELECT count(*) INTO editable_count
    FROM jsonb_array_elements(detail_result.field_definitions) d
    WHERE (d->>'is_editable')::boolean IS TRUE;
    IF editable_count <> 2 THEN RAISE EXCEPTION 'expected 2 editable fields for user, got %', editable_count; END IF;

    SELECT (d->>'is_editable')::boolean INTO missing_field_editable
    FROM jsonb_array_elements(detail_result.field_definitions) d
    WHERE d->>'field_key' = 'description_long';
    IF NOT missing_field_editable THEN RAISE EXCEPTION 'missing field should be editable'; END IF;

    SELECT (d->>'is_editable')::boolean INTO complete_field_editable
    FROM jsonb_array_elements(detail_result.field_definitions) d
    WHERE d->>'field_key' = 'name';
    IF complete_field_editable THEN RAISE EXCEPTION 'complete field must not be editable for user'; END IF;

    -- user can edit a missing field
    SELECT * INTO upd_result
    FROM public.admin_update_course(target_course, '{"description_long":"Actualizado por user"}'::jsonb, 1, 'user edit');
    IF NOT upd_result.success OR upd_result.new_version <> 2 THEN
        RAISE EXCEPTION 'user update failed: %', upd_result.error;
    END IF;

    -- user cannot edit a complete field
    SELECT * INTO upd_result
    FROM public.admin_update_course(target_course, '{"name":"No deberia"}'::jsonb, 2, 'user forbidden field');
    IF upd_result.success OR upd_result.error NOT LIKE 'User is not allowed to edit field%' THEN
        RAISE EXCEPTION 'user should not be able to edit complete field';
    END IF;

    -- user cannot publish
    SELECT * INTO pub_result
    FROM public.admin_publish_course(target_course);
    IF pub_result.success OR pub_result.error <> 'User is not an active admin' THEN
        RAISE EXCEPTION 'user must not publish';
    END IF;

    -- user cannot archive
    SELECT * INTO arch_result
    FROM public.admin_archive_course(target_course);
    IF arch_result.success OR arch_result.error <> 'User is not an active admin' THEN
        RAISE EXCEPTION 'user must not archive';
    END IF;

    -- user cannot change quality
    SELECT * INTO quality_result
    FROM public.admin_update_quality_status(target_course, 'complete');
    IF quality_result.success OR quality_result.error <> 'User is not an active admin' THEN
        RAISE EXCEPTION 'user must not change quality';
    END IF;
END;
$$;

-- ANON and inactive user tests
DO $$
DECLARE
    denied BOOLEAN;
    detail_result RECORD;
    role_value TEXT;
    list_result RECORD;
BEGIN
    PERFORM set_config('request.jwt.claim.sub', '', false);
    SELECT public.admin_current_user_role() INTO role_value;
    IF role_value <> 'anon' THEN RAISE EXCEPTION 'expected anon role, got %', role_value; END IF;

    SELECT public.admin_is_active_editor() INTO denied;
    IF denied THEN RAISE EXCEPTION 'anon must not be editor'; END IF;

    SELECT * INTO detail_result
    FROM public.admin_get_course_editorial('20000000-0000-0000-0000-000000000011');
    IF detail_result.error <> 'User is not an active editor' OR detail_result.course IS NOT NULL THEN
        RAISE EXCEPTION 'anonymous editorial detail reader was not denied';
    END IF;

    -- inactive user must be rejected
    PERFORM set_config('request.jwt.claim.sub', '30000000-0000-0000-0000-000000000005', false);
    SELECT public.admin_current_user_role() INTO role_value;
    IF role_value <> 'authenticated' THEN RAISE EXCEPTION 'inactive user must be authenticated (no active role), got %', role_value; END IF;

    SELECT public.admin_is_active_editor() INTO denied;
    IF denied THEN RAISE EXCEPTION 'inactive user must not be editor'; END IF;
END;
$$;

SELECT 'h3_pg17_harness_ok' AS result;
