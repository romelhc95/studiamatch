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
    production_enabled BOOLEAN NOT NULL DEFAULT false,
    notes TEXT
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
\ir ../../db/migrations/20260918_h3_invitation_flow_persistence.sql

-- Legacy compatibility fixture: the Auth-owned delta must preserve an
-- existing application-managed hash while making future hashes optional.
INSERT INTO auth.users (id, email)
VALUES ('39000000-0000-0000-0000-000000000001', 'legacy-invitation@local.test');
INSERT INTO public.admin_invitations (
    email, role, token_hash, created_by_user_id, expires_at
) VALUES (
    'legacy-invitation@local.test', 'user',
    encode(digest('legacy-token-h3-local-validation', 'sha256'), 'hex'),
    '39000000-0000-0000-0000-000000000001', now() + interval '48 hours'
);

\ir ../../db/migrations/20260919_h3_invitation_auth_token_delta.sql
-- Re-run the delta to prove DDL idempotency on the same PG17 schema.
\ir ../../db/migrations/20260919_h3_invitation_auth_token_delta.sql
\ir ../../db/migrations/20260920_h3_invitation_edge_runtime.sql
\ir ../../db/migrations/20260921_h3_invitation_onboarding_rpc.sql
\ir ../../db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql
\ir ../../db/migrations/20261001_h3_invitation_reservation_compensation.sql
-- The reservation/failure delta is intentionally idempotent.
\ir ../../db/migrations/20261001_h3_invitation_reservation_compensation.sql
\ir ../../db/migrations/20260924_h3_onboarding_rbac_hardening.sql
\ir ../../db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql
\ir ../../db/migrations/20260925_h3_legacy_member_creation_guard.sql
\ir ../../db/migrations/20260925_h3_admin_members_onboarding_reader.sql
\ir ../../db/migrations/20260927_h3_admin_queue_facets_filter.sql
\ir ../../db/migrations/20261004_h3_admin_queue_first_null_guard.sql
\ir ../../db/migrations/20260927_h3_publication_visibility_contract.sql

-- The default harness preserves Free's compatibility cohort. Set
-- h3_pro_baseline=1 to model the H2 Pro baseline after cohort retirement.
\if :{?h3_pro_baseline}
\else
CREATE TABLE private.h2_legacy_public_course_cohort (
    course_id UUID PRIMARY KEY REFERENCES public.courses(id) ON DELETE RESTRICT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    contract_version TEXT NOT NULL DEFAULT 'h2-pro-legacy-public-compat-v1',
    reason TEXT NOT NULL DEFAULT 'PG17 harness fixture'
);
\endif

\ir ../../db/migrations/20261001_h3_course_editorial_audit_availability.sql
\ir ../../db/migrations/20261028_h3_editorial_publication_snapshot.sql
-- Re-run to prove the forward-only delta is idempotent.
\ir ../../db/migrations/20261001_h3_course_editorial_audit_availability.sql
\ir ../../db/migrations/20261028_h3_editorial_publication_snapshot.sql

DO $$
BEGIN
    IF (SELECT token_hash FROM public.admin_invitations
        WHERE email = 'legacy-invitation@local.test') IS DISTINCT FROM
        encode(digest('legacy-token-h3-local-validation', 'sha256'), 'hex') THEN
        RAISE EXCEPTION 'legacy invitation token hash was not preserved';
    END IF;
END;
$$;

\ir ../../db/seeds/h3_admin_seed_local.sql

-- The isolated fixture models institutions whose source gates were approved.
INSERT INTO public.institution_site_profiles (institution_id, pipeline_ready, production_enabled)
SELECT id, true, true FROM public.institutions
ON CONFLICT (institution_id) DO UPDATE
SET pipeline_ready = true, production_enabled = true;

DO $$
DECLARE
    actual INTEGER;
BEGIN
    SELECT count(*) INTO actual FROM auth.users;
    IF actual <> 6 THEN RAISE EXCEPTION 'expected six local auth users including legacy invitation fixture, got %', actual; END IF;

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

-- ACL/RLS smoke: the harness must prove that the PostgREST roles cannot write
-- administrative tables directly. Function behavior is tested separately
-- through SECURITY DEFINER RPCs.
DO $$
BEGIN
    IF has_table_privilege('authenticated', 'public.admin_members', 'INSERT')
       OR has_table_privilege('authenticated', 'public.admin_members', 'UPDATE')
       OR has_table_privilege('authenticated', 'public.admin_members', 'DELETE') THEN
        RAISE EXCEPTION 'authenticated role has direct admin_members mutation privilege';
    END IF;
    IF has_table_privilege('authenticated', 'public.admin_membership_audit', 'INSERT')
       OR has_table_privilege('authenticated', 'public.admin_membership_audit', 'UPDATE')
       OR has_table_privilege('authenticated', 'public.admin_membership_audit', 'DELETE') THEN
        RAISE EXCEPTION 'authenticated role has direct audit mutation privilege';
    END IF;
    IF has_table_privilege('anon', 'public.admin_members', 'SELECT')
       OR has_table_privilege('anon', 'public.admin_invitations', 'SELECT') THEN
        RAISE EXCEPTION 'anon role has direct administrative read privilege';
    END IF;
END;
$$;

-- Re-run the seed: idempotency must keep every fixture count unchanged.
\ir ../../db/seeds/h3_admin_seed_local.sql
INSERT INTO public.institution_site_profiles (institution_id, pipeline_ready, production_enabled)
SELECT id, true, true FROM public.institutions
ON CONFLICT (institution_id) DO UPDATE
SET pipeline_ready = true, production_enabled = true;

DO $$
DECLARE
    actual INTEGER;
BEGIN
    SELECT count(*) INTO actual FROM auth.users;
    IF actual <> 6 THEN RAISE EXCEPTION 'idempotent seed re-run changed auth user count to %', actual; END IF;

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
    null_version_result RECORD;
    audit_row RECORD;
    detail_result RECORD;
    eff_detail RECORD;
    filtered_result RECORD;
    facets_result RECORD;
    publish_ok RECORD;
    publish_update RECORD;
    publish_draft RECORD;
    current_version INTEGER;
    effective_name TEXT;
    effective_description TEXT;
    published_description TEXT;
    reset_result RECORD;
    restore_result RECORD;
    draft_course UUID := '20000000-0000-0000-0000-000000000001';
    role_value TEXT;
    pipeline_name_source TEXT;
    audit_started_at TIMESTAMPTZ;
    audit_count_before INTEGER;
    null_version_audit_before INTEGER;
    atomicity_caught BOOLEAN := false;
    atomicity_constraint TEXT;
    atomicity_state_before JSONB;
    null_version_state_before JSONB;
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

    SELECT q.total INTO total_count
    FROM public.admin_count_course_queue_filtered('pending_review', 'complete', 'ulima') q;
    IF total_count <> 2 THEN RAISE EXCEPTION 'expected institutional filtered count 2, got %', total_count; END IF;

    SELECT * INTO filtered_result
    FROM public.admin_get_course_queue_filtered(1, NULL, 'pending_review', 'complete', 'ulima');
    IF filtered_result.error IS NOT NULL
       OR jsonb_array_length(filtered_result.courses) <> 1
       OR (filtered_result.page_info ->> 'hasNextPage')::boolean IS NOT TRUE THEN
        RAISE EXCEPTION 'filtered queue pagination failed: %', filtered_result.error;
    END IF;

    SELECT * INTO filtered_result
    FROM public.admin_get_course_queue_filtered(NULL, NULL, NULL, NULL, NULL);
    IF filtered_result.error IS DISTINCT FROM 'First must be between 1 and 100'
       OR filtered_result.courses IS NOT NULL
       OR filtered_result.page_info IS NOT NULL THEN
        RAISE EXCEPTION 'filtered queue accepted a NULL page size';
    END IF;

    SELECT * INTO facets_result FROM public.admin_get_course_queue_facets();
    IF facets_result.error IS NOT NULL OR jsonb_array_length(facets_result.institutions) <> 5 THEN
        RAISE EXCEPTION 'queue facets failed: %', facets_result.error;
    END IF;

    SELECT * INTO detail_result
    FROM public.admin_get_course_editorial(first_course);
    IF detail_result.error IS NOT NULL OR detail_result.course ->> 'course_id' <> first_course::text THEN
        RAISE EXCEPTION 'editorial detail reader failed: %', detail_result.error;
    END IF;
    IF jsonb_array_length(detail_result.field_definitions) <> 13 THEN
        RAISE EXCEPTION 'expected 13 editable field definitions';
    END IF;
    pipeline_name_source := detail_result.course -> 'field_sources' ->> 'name';

    -- A failed audit append must roll back the preceding editorial mutation.
    -- NOT VALID avoids requiring historical fixture rows to satisfy this test-only constraint.
    SELECT to_jsonb(es) INTO atomicity_state_before
      FROM public.course_editorial_state es
     WHERE es.course_id = first_course;
    SELECT count(*) INTO audit_count_before
      FROM public.course_editorial_audit
     WHERE course_id = first_course AND action = 'update';
    EXECUTE 'ALTER TABLE public.course_editorial_audit DROP CONSTRAINT IF EXISTS h3_test_reject_update_audit';
    EXECUTE 'ALTER TABLE public.course_editorial_audit ADD CONSTRAINT h3_test_reject_update_audit CHECK (action <> ''update'') NOT VALID';
    BEGIN
        PERFORM * FROM public.admin_update_course(
            first_course, '{"name":"Must roll back"}'::jsonb,
            (atomicity_state_before ->> 'version')::integer, 'Expected audit append failure'
        );
    EXCEPTION
        WHEN check_violation THEN
            GET STACKED DIAGNOSTICS atomicity_constraint = CONSTRAINT_NAME;
            atomicity_caught := atomicity_constraint = 'h3_test_reject_update_audit';
    END;
    EXECUTE 'ALTER TABLE public.course_editorial_audit DROP CONSTRAINT h3_test_reject_update_audit';
    IF atomicity_caught IS DISTINCT FROM true
       OR (SELECT to_jsonb(es) FROM public.course_editorial_state es WHERE es.course_id = first_course)
            IS DISTINCT FROM atomicity_state_before
       OR (SELECT count(*) FROM public.course_editorial_audit
            WHERE course_id = first_course AND action = 'update') <> audit_count_before THEN
        RAISE EXCEPTION 'failed audit append did not atomically roll back the editorial mutation';
    END IF;

    audit_started_at := transaction_timestamp();
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

    SELECT to_jsonb(es) INTO null_version_state_before
      FROM public.course_editorial_state es
     WHERE es.course_id = first_course;
    SELECT count(*) INTO null_version_audit_before
      FROM public.course_editorial_audit
     WHERE course_id = first_course AND action = 'update';
    SELECT * INTO null_version_result
    FROM public.admin_update_course(
        first_course, '{"name":"Null version must not write"}'::jsonb,
        NULL::INTEGER, 'reject missing version'
    );
    IF null_version_result.success
       OR null_version_result.error NOT LIKE 'Version conflict:%'
       OR (SELECT to_jsonb(es) FROM public.course_editorial_state es WHERE es.course_id = first_course)
            IS DISTINCT FROM null_version_state_before
       OR (SELECT count(*) FROM public.course_editorial_audit
            WHERE course_id = first_course AND action = 'update') <> null_version_audit_before THEN
        RAISE EXCEPTION 'NULL version was not rejected without an editorial or audit write';
    END IF;

    IF (SELECT count(*) FROM public.course_editorial_audit WHERE course_id = first_course AND action = 'update') <> 1 THEN
        RAISE EXCEPTION 'update audit was not appended';
    END IF;
    SELECT * INTO audit_row
      FROM public.course_editorial_audit
     WHERE course_id = first_course AND action = 'update'
     ORDER BY created_at DESC, id DESC LIMIT 1;
    IF audit_row.actor_user_id IS DISTINCT FROM auth.uid()
       OR audit_row.created_at IS NULL
       OR audit_row.created_at < audit_started_at
       OR audit_row.old_values -> 'manual_overrides' IS DISTINCT FROM '{}'::jsonb
       OR audit_row.new_values -> 'manual_overrides' ->> 'name' IS DISTINCT FROM 'Programa H3 editado'
       OR audit_row.new_values ->> 'version' IS DISTINCT FROM '2' THEN
        RAISE EXCEPTION 'editorial update audit lost actor, timestamp, before, or after values';
    END IF;

    -- Effective-value reader: manual overrides must win everywhere (course_name, current_values, field current_value).
    SELECT * INTO eff_detail
    FROM public.admin_get_course_editorial(first_course);
    IF eff_detail.error IS NOT NULL THEN
        RAISE EXCEPTION 'effective reader failed: %', eff_detail.error;
    END IF;
    IF eff_detail.course ->> 'course_name' <> 'Programa H3 editado'
       OR eff_detail.course -> 'current_values' ->> 'name' <> 'Programa H3 editado'
       OR eff_detail.course -> 'pipeline_values' ->> 'name' <> 'Programa local H3 11'
       OR eff_detail.course -> 'manual_overrides' ->> 'name' <> 'Programa H3 editado'
       OR eff_detail.course -> 'field_sources' ->> 'name' IS DISTINCT FROM pipeline_name_source THEN
        RAISE EXCEPTION 'effective name is inconsistent across the editorial reader';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM jsonb_array_elements(eff_detail.field_definitions) d
        WHERE d->>'field_key' = 'name' AND d->>'current_value' <> 'Programa H3 editado'
    ) THEN
        RAISE EXCEPTION 'field definition current_value ignores manual overrides';
    END IF;

    SELECT count(*) INTO audit_count_before
      FROM public.course_editorial_audit
     WHERE course_id = first_course AND action = 'update';
    audit_started_at := transaction_timestamp();
    SELECT * INTO reset_result
    FROM public.admin_update_course(first_course, '{"name":null}'::jsonb, 2, 'Restore pipeline value');
    IF NOT reset_result.success
       OR reset_result.new_version IS DISTINCT FROM 3
       OR EXISTS (
         SELECT 1 FROM public.course_editorial_state es
          WHERE es.course_id = first_course AND es.manual_overrides ? 'name'
       ) THEN
        RAISE EXCEPTION 'null override did not restore the pipeline-owned name: %', reset_result.error;
    END IF;
    IF (SELECT count(*) FROM public.course_editorial_audit
         WHERE course_id = first_course AND action = 'update') <> audit_count_before + 1 THEN
        RAISE EXCEPTION 'clearing a manual override did not append exactly one update audit event';
    END IF;
    SELECT * INTO audit_row
      FROM public.course_editorial_audit
     WHERE course_id = first_course AND action = 'update'
       AND new_values ->> 'version' = '3'
     ORDER BY created_at DESC, id DESC LIMIT 1;
    IF audit_row.actor_user_id IS DISTINCT FROM auth.uid()
       OR audit_row.created_at IS NULL
       OR audit_row.created_at < audit_started_at
       OR audit_row.old_values -> 'manual_overrides' ->> 'name' IS DISTINCT FROM 'Programa H3 editado'
       OR audit_row.new_values -> 'manual_overrides' IS DISTINCT FROM '{}'::jsonb
       OR audit_row.new_values ->> 'version' IS DISTINCT FROM '3' THEN
        RAISE EXCEPTION 'override removal audit lost actor, timestamp, before, or after values';
    END IF;
    SELECT * INTO eff_detail FROM public.admin_get_course_editorial(first_course);
    IF eff_detail.course -> 'current_values' ->> 'name' <> 'Programa local H3 11'
       OR eff_detail.course -> 'pipeline_values' ->> 'name' <> 'Programa local H3 11'
       OR eff_detail.course -> 'manual_overrides' ? 'name'
       OR eff_detail.course -> 'field_sources' ->> 'name' IS DISTINCT FROM pipeline_name_source THEN
        RAISE EXCEPTION 'reset override did not restore pipeline value and provenance';
    END IF;

    SELECT * INTO restore_result
    FROM public.admin_update_course(first_course, '{"name":"Programa H3 editado"}'::jsonb, 3, 'Correct from official source');
    IF NOT restore_result.success THEN
        RAISE EXCEPTION 'manual correction after reset failed: %', restore_result.error;
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

    SELECT c.name INTO effective_name
      FROM public.courses_public_effective c WHERE c.id = first_course;
    IF effective_name <> 'Programa H3 editado' THEN
        RAISE EXCEPTION 'public reader did not receive the Admin-published editorial value';
    END IF;
    IF (SELECT count(*)
          FROM public.course_editorial_state s,
               jsonb_object_keys(s.published_editorial_values) AS published_key
         WHERE s.course_id = first_course) <> 14 THEN
        RAISE EXCEPTION 'publication did not capture the complete 13-field editorial snapshot and public start date';
    END IF;

    -- Snapshotless legacy rows remain public with their existing overrides and
    -- are upgraded lazily on the first editor correction (no mass backfill).
    SELECT c.description_long INTO published_description
      FROM public.courses c WHERE c.id = first_course;
    UPDATE public.course_editorial_state
       SET published_editorial_values = NULL
     WHERE course_id = first_course;
    SELECT c.name, c.description_long INTO effective_name, effective_description
      FROM public.courses_public_effective c WHERE c.id = first_course;
    IF effective_name <> 'Programa H3 editado'
       OR effective_description IS DISTINCT FROM published_description THEN
        RAISE EXCEPTION 'snapshotless legacy publication lost existing public content';
    END IF;

    SELECT version INTO current_version
      FROM public.course_editorial_state WHERE course_id = first_course;
    SELECT * INTO publish_update
      FROM public.admin_update_course(
        first_course, '{"name":"Borrador editorial H3"}'::jsonb,
        current_version, 'Draft a corrected public title'
      );
    IF NOT publish_update.success THEN
        RAISE EXCEPTION 'post-publication draft correction failed: %', publish_update.error;
    END IF;
    SELECT c.name INTO effective_name
      FROM public.courses_public_effective c WHERE c.id = first_course;
    IF effective_name <> 'Programa H3 editado' THEN
        RAISE EXCEPTION 'saving a draft changed the published public value before Admin publication';
    END IF;
    SELECT * INTO eff_detail FROM public.admin_get_course_editorial(first_course);
    IF eff_detail.course ->> 'has_unpublished_changes' <> 'true'
       OR eff_detail.course -> 'published_values' ->> 'name' <> 'Programa H3 editado'
       OR eff_detail.course -> 'current_values' ->> 'name' <> 'Borrador editorial H3' THEN
        RAISE EXCEPTION 'editorial reader did not distinguish draft and approved values';
    END IF;
    IF (SELECT published_editorial_values IS NULL FROM public.course_editorial_state WHERE course_id = first_course) THEN
        RAISE EXCEPTION 'first post-migration edit did not lazily snapshot the legacy published content';
    END IF;
    SELECT * INTO publish_update FROM public.admin_publish_course(first_course);
    IF NOT publish_update.success THEN
        RAISE EXCEPTION 'Admin could not publish the corrected snapshot: %', publish_update.error;
    END IF;
    SELECT c.name INTO effective_name
      FROM public.courses_public_effective c WHERE c.id = first_course;
    IF effective_name <> 'Borrador editorial H3' THEN
        RAISE EXCEPTION 'public reader did not receive the republished editorial value';
    END IF;
    SELECT c.description_long INTO published_description
      FROM public.courses_public_effective c WHERE c.id = first_course;
    UPDATE public.courses
       SET name = 'Harvester title after publication',
           description_long = 'Harvester description after publication'
     WHERE id = first_course;
    SELECT c.name, c.description_long INTO effective_name, effective_description
      FROM public.courses_public_effective c WHERE c.id = first_course;
    IF effective_name <> 'Borrador editorial H3'
       OR effective_description IS DISTINCT FROM published_description THEN
        RAISE EXCEPTION 'harvester base changes replaced the last Admin-published snapshot';
    END IF;
END;
$$;

-- Enrollment evidence stays independent from strict published snapshots while
-- legacy rows retain their existing availability behavior during compatibility.
DO $$
DECLARE
    target_course UUID := '20000000-0000-0000-0000-000000000011';
    legacy_course UUID := '20000000-0000-0000-0000-000000000013';
    legacy_cohort_present BOOLEAN := to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL;
    current_version INTEGER;
    write_result RECORD;
    publish_without_evidence RECORD;
    audit_row RECORD;
    audit_page RECORD;
    effective_name TEXT;
    legacy_effective_name TEXT;
    audit_started_at TIMESTAMPTZ;
    audit_count_before INTEGER;
    strict_unproven_course UUID := '20000000-0000-0000-0000-000000000012';
    observed_at_value TIMESTAMPTZ := now() - interval '1 hour';
    valid_until_value TIMESTAMPTZ;
    constraint_rejected BOOLEAN;
BEGIN
    valid_until_value := ((observed_at_value AT TIME ZONE 'UTC') + interval '90 days') AT TIME ZONE 'UTC';
    IF has_table_privilege('authenticated', 'public.course_editorial_audit', 'SELECT') THEN
        RAISE EXCEPTION 'authenticated role must not read course audit table directly';
    END IF;
    IF has_function_privilege('anon', 'public.admin_get_course_audit(uuid,integer,timestamp with time zone,uuid)', 'EXECUTE') THEN
        RAISE EXCEPTION 'anon role must not execute the course audit reader';
    END IF;

    -- Enrollment evidence does not determine whether Admin may approve content.
    UPDATE public.course_editorial_state
       SET availability_status = 'unknown'
     WHERE course_id = strict_unproven_course;
    SELECT * INTO publish_without_evidence
      FROM public.admin_publish_course(strict_unproven_course);
    IF NOT publish_without_evidence.success OR publish_without_evidence.new_status <> 'published'
       OR NOT EXISTS (
           SELECT 1 FROM public.course_editorial_audit
            WHERE course_id = strict_unproven_course AND action = 'publish'
       ) THEN
        RAISE EXCEPTION 'Admin publication was incorrectly coupled to enrollment evidence';
    END IF;
    UPDATE public.course_editorial_state
       SET availability_status = 'available'
     WHERE course_id = strict_unproven_course;

    IF legacy_cohort_present THEN
        EXECUTE 'INSERT INTO private.h2_legacy_public_course_cohort(course_id, reason)
                 VALUES ($1, $2) ON CONFLICT (course_id) DO NOTHING'
          USING target_course, 'PG17 compatibility behavior fixture';
    END IF;
    UPDATE public.course_editorial_state
       SET availability_status = 'unknown'
     WHERE course_id = target_course;

    SELECT c.name INTO effective_name
      FROM public.courses_public_effective c WHERE c.id = target_course;
    IF effective_name <> 'Borrador editorial H3' THEN
        RAISE EXCEPTION 'unknown enrollment status replaced the last published editorial value';
    END IF;

    IF legacy_cohort_present THEN
        EXECUTE 'INSERT INTO private.h2_legacy_public_course_cohort(course_id, reason)
                 VALUES ($1, $2) ON CONFLICT (course_id) DO NOTHING'
          USING legacy_course, 'PG17 legacy compatibility fixture';
        UPDATE public.course_editorial_state
           SET availability_status = 'unknown'
         WHERE course_id = legacy_course;
        SELECT c.name INTO legacy_effective_name
          FROM public.courses_public_effective c WHERE c.id = legacy_course;
        IF legacy_effective_name <> 'Programa local H3 13' THEN
            RAISE EXCEPTION 'legacy cohort compatibility stopped exposing an unknown-availability row';
        END IF;
        UPDATE public.course_editorial_state
           SET availability_status = 'unavailable'
         WHERE course_id = legacy_course;
        IF EXISTS (SELECT 1 FROM public.courses_public_effective c WHERE c.id = legacy_course) THEN
            RAISE EXCEPTION 'legacy cohort availability behavior changed during compatibility';
        END IF;
    END IF;

    SELECT version INTO current_version
      FROM public.course_editorial_state WHERE course_id = target_course;
    SELECT count(*) INTO audit_count_before
      FROM public.course_editorial_audit
     WHERE course_id = target_course AND action = 'availability_override';
    SELECT * INTO write_result FROM public.admin_set_course_availability(
        target_course,
        'available',
        NULL,
        observed_at_value,
        now() + interval '1 day',
        current_version,
        'Reject missing availability evidence'
    );
    IF write_result.success OR write_result.error <> 'Evidence must be an HTTPS URL'
       OR (SELECT version FROM public.course_editorial_state WHERE course_id = target_course) <> current_version
       OR (SELECT count(*) FROM public.course_editorial_audit
            WHERE course_id = target_course AND action = 'availability_override') <> audit_count_before THEN
        RAISE EXCEPTION 'missing availability evidence changed state or was accepted';
    END IF;

    audit_started_at := transaction_timestamp();
    SELECT * INTO write_result FROM public.admin_set_course_availability(
        target_course,
        'unavailable',
        'https://local.example.test/programas/11',
        now() - interval '1 hour',
        now() + interval '1 day',
        current_version,
        'Official course page confirms enrollment closed'
    );
    IF NOT write_result.success THEN
        RAISE EXCEPTION 'evidence-backed availability write failed: %', write_result.error;
    END IF;
    SELECT * INTO audit_row
      FROM public.course_editorial_audit
     WHERE course_id = target_course AND action = 'availability_override'
     ORDER BY created_at DESC, id DESC LIMIT 1;
    IF audit_row.actor_user_id IS DISTINCT FROM auth.uid()
       OR audit_row.created_at IS NULL
       OR audit_row.created_at < audit_started_at
       OR audit_row.old_values -> 'availability_override_status' IS DISTINCT FROM 'null'::jsonb
       OR audit_row.new_values ->> 'availability_override_status' IS DISTINCT FROM 'unavailable'
       OR audit_row.new_values ->> 'availability_evidence_url' IS DISTINCT FROM 'https://local.example.test/programas/11' THEN
        RAISE EXCEPTION 'availability audit lost actor, timestamp, before, or after values';
    END IF;
    SELECT c.name INTO effective_name
      FROM public.courses_public_effective c WHERE c.id = target_course;
    IF effective_name <> 'Borrador editorial H3' THEN
        RAISE EXCEPTION 'closed enrollment hid or replaced a still-active published course';
    END IF;

    SELECT * INTO audit_page
      FROM public.admin_get_course_audit(target_course, 2, NULL, NULL);
    IF audit_page.error IS NOT NULL
       OR jsonb_array_length(audit_page.events) <> 2
       OR audit_page.page_info ->> 'hasNextPage' <> 'true'
       OR audit_page.events -> 0 ->> 'actor_label' <> 'admin@local.test' THEN
        RAISE EXCEPTION 'Admin audit reader did not return attributed paginated history: %', audit_page.error;
    END IF;

    UPDATE public.course_editorial_state
       SET availability_valid_until = now() - interval '1 second'
     WHERE course_id = target_course;
    SELECT c.name INTO effective_name
      FROM public.courses_public_effective c WHERE c.id = target_course;
    IF effective_name <> 'Borrador editorial H3' THEN
        RAISE EXCEPTION 'expired evidence reverted the published editorial snapshot';
    END IF;
    SELECT * INTO audit_page FROM public.admin_get_course_editorial(target_course);
    IF audit_page.course ->> 'availability_status' <> 'unknown'
       OR audit_page.course ->> 'availability_override_active' <> 'false' THEN
        RAISE EXCEPTION 'expired evidence was not fail-closed to the computed status';
    END IF;

    SELECT version INTO current_version FROM public.course_editorial_state WHERE course_id = target_course;
    SELECT * INTO write_result FROM public.admin_set_course_availability(
        target_course, NULL, NULL, NULL, NULL, current_version,
        'Remove expired manual determination'
    );
    IF NOT write_result.success THEN
        RAISE EXCEPTION 'clearing availability evidence failed: %', write_result.error;
    END IF;
    SELECT c.name INTO effective_name
      FROM public.courses_public_effective c WHERE c.id = target_course;
    IF effective_name <> 'Borrador editorial H3' THEN
        RAISE EXCEPTION 'clearing enrollment evidence changed the published editorial snapshot';
    END IF;

    SELECT * INTO write_result FROM public.admin_set_course_availability(
        target_course,
        'available',
        'https://unrelated.invalid/evidence',
        now() - interval '1 hour',
        now() + interval '1 day',
        (SELECT version FROM public.course_editorial_state WHERE course_id = target_course),
        'Reject evidence from unrelated domain'
    );
    IF write_result.success OR write_result.error NOT LIKE 'Evidence host must match%' THEN
        RAISE EXCEPTION 'availability evidence from unrelated host was not rejected';
    END IF;

    SELECT version INTO current_version FROM public.course_editorial_state WHERE course_id = target_course;
    SELECT * INTO write_result FROM public.admin_set_course_availability(
        target_course,
        'available',
        'https://local.example.test/programas/11',
        observed_at_value,
        valid_until_value,
        current_version,
        'Official course page confirms current enrollment'
    );
    IF NOT write_result.success THEN
        RAISE EXCEPTION 'the inclusive 90-calendar-day evidence boundary was rejected: %', write_result.error;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.courses_public_effective c WHERE c.id = target_course) THEN
        RAISE EXCEPTION 'confirmed-available strict course did not become public';
    END IF;

    constraint_rejected := false;
    BEGIN
        UPDATE public.course_editorial_state
           SET availability_valid_until = valid_until_value + interval '1 second'
         WHERE course_id = target_course;
    EXCEPTION WHEN check_violation THEN
        constraint_rejected := true;
    END;
    IF NOT constraint_rejected THEN
        RAISE EXCEPTION 'the table constraint accepted evidence beyond 90 calendar days';
    END IF;

    SELECT version INTO current_version FROM public.course_editorial_state WHERE course_id = target_course;
    SELECT * INTO write_result FROM public.admin_set_course_availability(
        target_course,
        'available',
        'https://local.example.test/programas/11',
        observed_at_value,
        valid_until_value + interval '1 second',
        current_version,
        'Reject evidence beyond the approved 90-day maximum'
    );
    IF write_result.success OR write_result.error NOT LIKE 'Evidence validity cannot exceed 90 calendar days%' THEN
        RAISE EXCEPTION 'the availability RPC accepted evidence beyond 90 calendar days: %', write_result.error;
    END IF;

    SELECT version INTO current_version FROM public.course_editorial_state WHERE course_id = target_course;
    SELECT * INTO write_result FROM public.admin_set_course_availability(
        target_course, NULL, NULL, NULL, NULL, current_version,
        'Clear the maximum-age boundary fixture'
    );
    IF NOT write_result.success THEN
        RAISE EXCEPTION 'could not clear the availability boundary fixture: %', write_result.error;
    END IF;

    UPDATE public.institution_site_profiles
       SET notes = 'DB_AS_CODE_RELEASE_CANARY'
     WHERE institution_id = (SELECT institution_id FROM public.courses WHERE id = '20000000-0000-0000-0000-000000000014');
    SELECT * INTO write_result FROM public.admin_publish_course('20000000-0000-0000-0000-000000000014');
    IF write_result.success OR write_result.error NOT LIKE 'Course is not publishable: source pipeline gates%' THEN
        RAISE EXCEPTION 'publication allowed a canary institution: %', write_result.error;
    END IF;
    UPDATE public.institution_site_profiles SET notes = NULL
     WHERE notes = 'DB_AS_CODE_RELEASE_CANARY';
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
    IF member_row.email <> 'admin@local.test' THEN
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
    audit_result RECORD;
    availability_result RECORD;
    current_version INTEGER;
    role_value TEXT;
    user_id UUID := '30000000-0000-0000-0000-000000000003';
    target_course UUID := '20000000-0000-0000-0000-000000000001';
    upd_result RECORD;
    pub_result RECORD;
    arch_result RECORD;
    quality_result RECORD;
    audit_row RECORD;
    editable_count INTEGER;
    missing_field_editable BOOLEAN;
    complete_field_editable BOOLEAN;
    audit_count_before INTEGER;
    audit_started_at TIMESTAMPTZ;
    original_populated_name TEXT;
BEGIN
    PERFORM set_config('request.jwt.claim.sub', user_id::text, false);

    SELECT * INTO audit_result
      FROM public.admin_get_course_audit('20000000-0000-0000-0000-000000000011', 10, NULL, NULL);
    IF audit_result.error <> 'User is not an active admin' THEN
        RAISE EXCEPTION 'non-admin user was able to read editorial audit history';
    END IF;
    SELECT version INTO current_version FROM public.course_editorial_state WHERE course_id = target_course;
    SELECT * INTO availability_result FROM public.admin_set_course_availability(
        target_course,
        'available',
        'https://local.example.test/programas/1',
        now() - interval '1 hour',
        now() + interval '1 day',
        current_version,
        'Non-admin write must be denied'
    );
    IF availability_result.success OR availability_result.error <> 'User is not an active admin' THEN
        RAISE EXCEPTION 'non-admin user was able to write an availability override';
    END IF;

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

    -- The 13-field allowlist is editable regardless of missing_fields.
    SELECT count(*) INTO editable_count
    FROM jsonb_array_elements(detail_result.field_definitions) d
    WHERE (d->>'is_editable')::boolean IS TRUE;
    IF editable_count <> 13 THEN RAISE EXCEPTION 'expected all 13 editorial fields editable for user, got %', editable_count; END IF;

    SELECT (d->>'is_editable')::boolean INTO missing_field_editable
    FROM jsonb_array_elements(detail_result.field_definitions) d
    WHERE d->>'field_key' = 'description_long';
    IF NOT missing_field_editable THEN RAISE EXCEPTION 'missing field should remain editable'; END IF;

    SELECT (d->>'is_editable')::boolean INTO complete_field_editable
    FROM jsonb_array_elements(detail_result.field_definitions) d
    WHERE d->>'field_key' = 'name';
    IF NOT complete_field_editable THEN RAISE EXCEPTION 'populated field should be editable for user'; END IF;
    original_populated_name := detail_result.course -> 'current_values' ->> 'name';

    -- user can edit a missing field
    SELECT * INTO upd_result
    FROM public.admin_update_course(target_course, '{"description_long":"Actualizado por user"}'::jsonb, 1, 'user edit');
    IF NOT upd_result.success OR upd_result.new_version <> 2 THEN
        RAISE EXCEPTION 'user update failed: %', upd_result.error;
    END IF;

    -- User corrects an already-populated field, reloads it, and corrects it again.
    SELECT count(*) INTO audit_count_before
      FROM public.course_editorial_audit
     WHERE course_id = target_course AND action = 'update';
    audit_started_at := transaction_timestamp();
    SELECT * INTO upd_result
    FROM public.admin_update_course(target_course, '{"name":"Curso corregido por user"}'::jsonb, 2, 'Correct populated editorial name');
    IF NOT upd_result.success OR upd_result.new_version <> 3 THEN
        RAISE EXCEPTION 'user could not correct a populated field: %', upd_result.error;
    END IF;
    SELECT * INTO detail_result FROM public.admin_get_course_editorial(target_course);
    IF detail_result.error IS NOT NULL
       OR detail_result.course -> 'current_values' ->> 'name' <> 'Curso corregido por user' THEN
        RAISE EXCEPTION 'saved populated-field correction did not persist on reload';
    END IF;
    SELECT * INTO audit_row
      FROM public.course_editorial_audit
     WHERE course_id = target_course AND action = 'update'
       AND new_values ->> 'version' = '3'
     ORDER BY created_at DESC, id DESC LIMIT 1;
    IF audit_row.actor_user_id IS DISTINCT FROM auth.uid()
       OR audit_row.created_at IS NULL OR audit_row.created_at < audit_started_at
       OR audit_row.old_values -> 'editorial_fields' ->> 'name' IS DISTINCT FROM original_populated_name
       OR audit_row.new_values -> 'editorial_fields' ->> 'name' IS DISTINCT FROM 'Curso corregido por user'
       OR audit_row.reason <> 'Correct populated editorial name' THEN
        RAISE EXCEPTION 'populated-field correction audit lost actor, date, before or after';
    END IF;

    audit_started_at := transaction_timestamp();
    SELECT * INTO upd_result
    FROM public.admin_update_course(target_course, '{"name":"Curso corregido nuevamente"}'::jsonb, 3, 'Repeat editorial correction');
    IF NOT upd_result.success OR upd_result.new_version <> 4 THEN
        RAISE EXCEPTION 'user could not repeat a correction to the same field: %', upd_result.error;
    END IF;
    SELECT * INTO detail_result FROM public.admin_get_course_editorial(target_course);
    SELECT * INTO audit_row
      FROM public.course_editorial_audit
     WHERE course_id = target_course AND action = 'update'
       AND new_values ->> 'version' = '4'
     ORDER BY created_at DESC, id DESC LIMIT 1;
    IF detail_result.course -> 'current_values' ->> 'name' <> 'Curso corregido nuevamente'
       OR audit_row.actor_user_id IS DISTINCT FROM auth.uid()
       OR audit_row.created_at IS NULL OR audit_row.created_at < audit_started_at
       OR audit_row.old_values -> 'editorial_fields' ->> 'name' IS DISTINCT FROM 'Curso corregido por user'
       OR audit_row.new_values -> 'editorial_fields' ->> 'name' IS DISTINCT FROM 'Curso corregido nuevamente'
       OR (SELECT count(*) FROM public.course_editorial_audit WHERE course_id = target_course AND action = 'update') <> audit_count_before + 2 THEN
        RAISE EXCEPTION 'repeated correction did not persist with a complete audit';
    END IF;

    SELECT * INTO upd_result
    FROM public.admin_update_course(target_course, '{"category":"No permitido"}'::jsonb, 4, 'Reject non-editorial field');
    IF upd_result.success OR upd_result.error NOT LIKE 'Unknown field not allowed:%' THEN
        RAISE EXCEPTION 'user was allowed to edit outside the editorial allowlist';
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

-- Invitation Flow persistence regression (design H3-DESIGN-DB-01):
-- legacy backfill, lifecycle transitions, constraints, single pending per email,
-- token immutability, append-only invitations, audit vocabulary.
DO $$
DECLARE
    admin_id UUID := '30000000-0000-0000-0000-000000000001';
    invited_id UUID := '30000000-0000-0000-0000-000000000003';
    invitee_user UUID := '30000000-0000-0000-0000-000000000002';
    invitation_id UUID;
    stale_token TEXT;
    inv_invited_at TIMESTAMPTZ;
    inv_accepted_at TIMESTAMPTZ;
    inv_password_at TIMESTAMPTZ;
    revoked_active BOOLEAN;
    revoked_at_ts TIMESTAMPTZ;
    legacy_ready INTEGER;
    audit_count INTEGER;
    editor_version INTEGER;
    editor_result RECORD;
BEGIN
    -- Backfill: every legacy seed member must be account_status = 'ready'.
    SELECT count(*) INTO legacy_ready
    FROM public.admin_members WHERE account_status <> 'ready';
    IF legacy_ready <> 0 THEN
        RAISE EXCEPTION 'legacy members were not backfilled to ready: % rows', legacy_ready;
    END IF;

    -- An invited member is persisted with an open onboarding state. Even if a
    -- drifted row is active, editorial writes must require account_status=ready.
    -- Design machine: ready cannot re-invite directly; the path is ready -> inactive -> invited.
    UPDATE public.admin_members SET account_status = 'inactive', is_active = false
    WHERE user_id = invited_id;
    UPDATE public.admin_members SET account_status = 'invited', is_active = true
    WHERE user_id = invited_id;
    SELECT account_status, invited_at, accepted_at, password_set_at
    INTO stale_token, inv_invited_at, inv_accepted_at, inv_password_at
    FROM public.admin_members WHERE user_id = invited_id;
    IF stale_token <> 'invited' OR inv_invited_at IS NULL OR inv_accepted_at IS NOT NULL OR inv_password_at IS NOT NULL THEN
        RAISE EXCEPTION 'invited member persistence is inconsistent (status=%, invited_at=%, accepted_at=%, password_set_at=%)',
            stale_token, inv_invited_at, inv_accepted_at, inv_password_at;
    END IF;
    PERFORM set_config('request.jwt.claim.sub', invited_id::text, false);
    PERFORM set_config('request.jwt.claim.aal', 'aal2', false);
    SELECT version INTO editor_version FROM public.course_editorial_state
    WHERE course_id = '20000000-0000-0000-0000-000000000011';
    SELECT * INTO editor_result FROM public.admin_update_course(
        '20000000-0000-0000-0000-000000000011',
        '{"name":"Invited member must not edit"}'::jsonb,
        editor_version,
        'reject invited active drift'
    );
    IF editor_result.success OR editor_result.error <> 'User is not an active editor' THEN
        RAISE EXCEPTION 'active invited member was able to edit a course: %', editor_result.error;
    END IF;
    PERFORM set_config('request.jwt.claim.sub', admin_id::text, false);

    -- Invitation lifecycle: invite -> accept -> password_set -> ready.
    INSERT INTO public.admin_invitations (
        admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
    ) VALUES (
        invited_id,
        'invited-flow@local.test',
        'user',
        encode(digest('invitation-token-h3-local-validation-0001', 'sha256'), 'hex'),
        admin_id,
        now() + interval '48 hours'
    )
    RETURNING id INTO invitation_id;

    UPDATE public.admin_members
    SET account_status = 'accepted', last_invitation_id = invitation_id
    WHERE user_id = invited_id;
    UPDATE public.admin_members
    SET account_status = 'password_pending'
    WHERE user_id = invited_id;
    UPDATE public.admin_members
    SET account_status = 'ready',
        password_set_at = now(),
        last_invitation_id = invitation_id
    WHERE user_id = invited_id;

    SELECT account_status INTO stale_token FROM public.admin_members WHERE user_id = invited_id;
    IF stale_token <> 'ready' THEN
        RAISE EXCEPTION 'invitation lifecycle did not reach ready, got %', stale_token;
    END IF;
    SELECT accepted_at, password_set_at INTO inv_accepted_at, inv_password_at
    FROM public.admin_members WHERE user_id = invited_id;
    IF inv_accepted_at IS NULL OR inv_password_at IS NULL THEN
        RAISE EXCEPTION 'ready member is missing accepted_at/password_set_at';
    END IF;

    -- The used invitation must be closed so the email can be invited again later.
    UPDATE public.admin_invitations
    SET status = 'accepted', accepted_user_id = invitee_user
    WHERE id = invitation_id;

    -- ready -> invited directly is forbidden by design (requires deactivation first).
    BEGIN
        UPDATE public.admin_members SET account_status = 'invited' WHERE user_id = invited_id;
        RAISE EXCEPTION 'ready -> invited direct transition was not rejected';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM NOT LIKE 'admin_members invalid status transition ready -> invited%' THEN
            RAISE EXCEPTION 'unexpected transition error: %', SQLERRM;
        END IF;
    END;

    -- New onboarding cycle for the negative test: ready -> inactive -> invited -> accepted -> password_pending.
    UPDATE public.admin_members SET account_status = 'inactive', is_active = false
    WHERE user_id = invited_id;
    UPDATE public.admin_members SET account_status = 'invited', is_active = true
    WHERE user_id = invited_id;
    INSERT INTO public.admin_invitations (
        admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
    ) VALUES (
        invited_id, 'invited-flow@local.test', 'user',
        encode(digest('invitation-token-h3-local-validation-0002', 'sha256'), 'hex'),
        admin_id, now() + interval '48 hours'
    );
    UPDATE public.admin_members
    SET account_status = 'accepted',
        last_invitation_id = (SELECT id FROM public.admin_invitations
                              WHERE email = 'invited-flow@local.test' AND status = 'pending')
    WHERE user_id = invited_id;
    UPDATE public.admin_members SET account_status = 'password_pending' WHERE user_id = invited_id;

    PERFORM set_config('request.jwt.claim.sub', invited_id::text, false);
    SELECT version INTO editor_version FROM public.course_editorial_state
    WHERE course_id = '20000000-0000-0000-0000-000000000011';
    SELECT * INTO editor_result FROM public.admin_update_course(
        '20000000-0000-0000-0000-000000000011',
        '{"name":"Password pending member must not edit"}'::jsonb,
        editor_version,
        'reject password pending active drift'
    );
    IF editor_result.success OR editor_result.error <> 'User is not an active editor' THEN
        RAISE EXCEPTION 'active password_pending member was able to edit a course: %', editor_result.error;
    END IF;
    PERFORM set_config('request.jwt.claim.sub', admin_id::text, false);

    -- Transition to ready without password_set_at must fail (accepted_at is already set).
    BEGIN
        UPDATE public.admin_members SET account_status = 'ready' WHERE user_id = invited_id;
        RAISE EXCEPTION 'ready transition without accepted/password timestamps was not rejected';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM NOT LIKE 'admin_members transition to ready requires%' THEN
            RAISE EXCEPTION 'unexpected transition error: %', SQLERRM;
        END IF;
    END;

    -- Positive completion: with password_set_at the member becomes ready again.
    UPDATE public.admin_members
    SET account_status = 'ready', password_set_at = now()
    WHERE user_id = invited_id;

    -- A revoked member is blocked and timestamped (guard enforces is_active = false).
    UPDATE public.admin_members SET account_status = 'revoked'
    WHERE user_id = invited_id;
    SELECT is_active, revoked_at, accepted_at, password_set_at
    INTO revoked_active, revoked_at_ts, inv_accepted_at, inv_password_at
    FROM public.admin_members WHERE user_id = invited_id;
    IF revoked_active THEN
        RAISE EXCEPTION 'revoked member must not remain active';
    END IF;
    IF revoked_at_ts IS NULL OR inv_accepted_at IS NULL OR inv_password_at IS NULL THEN
        RAISE EXCEPTION 'revoked member is missing revoked_at or onboarding timestamps';
    END IF;
    PERFORM set_config('request.jwt.claim.sub', invited_id::text, false);
    IF public.admin_is_active_editor() THEN
        RAISE EXCEPTION 'revoked member with active flag false must not be an editor';
    END IF;
    PERFORM set_config('request.jwt.claim.sub', admin_id::text, false);

    -- Close the invitation used by the second onboarding cycle.
    UPDATE public.admin_invitations
    SET status = 'accepted', accepted_user_id = invitee_user
    WHERE email = 'invited-flow@local.test' AND status = 'pending'
      AND token_hash = encode(digest('invitation-token-h3-local-validation-0002', 'sha256'), 'hex');

    -- New pending invitation for the same email is allowed once none is pending.
    INSERT INTO public.admin_invitations (
        admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
    ) VALUES (
        invited_id, 'invited-flow@local.test', 'user',
        encode(digest('invitation-token-h3-local-validation-0003', 'sha256'), 'hex'),
        admin_id, now() + interval '48 hours'
    );
    BEGIN
        INSERT INTO public.admin_invitations (
            admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
        ) VALUES (
            invited_id, 'invited-flow@local.test', 'user',
            encode(digest('invitation-token-h3-local-validation-0004', 'sha256'), 'hex'),
            admin_id, now() + interval '48 hours'
        );
        RAISE EXCEPTION 'second pending invitation for the same email was not rejected';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;

    -- Supersede (resend): pending -> superseded, then a new pending row is allowed.
    UPDATE public.admin_invitations SET status = 'superseded'
    WHERE email = 'invited-flow@local.test' AND status = 'pending';
    INSERT INTO public.admin_invitations (
        admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
    ) VALUES (
        invited_id, 'invited-flow@local.test', 'user',
        encode(digest('invitation-token-h3-local-validation-0004', 'sha256'), 'hex'),
        admin_id, now() + interval '48 hours'
    );

    -- Non-pending invitations are frozen (accept after supersede must fail).
    BEGIN
        UPDATE public.admin_invitations
        SET status = 'accepted', accepted_user_id = invitee_user
        WHERE email = 'invited-flow@local.test' AND status = 'superseded';
        RAISE EXCEPTION 'superseded invitation was accepted';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM NOT LIKE 'admin_invitations invalid status transition%' THEN
            RAISE EXCEPTION 'unexpected invitation transition error: %', SQLERRM;
        END IF;
    END;

    -- token_hash/email/created_by/created_at are immutable.
    BEGIN
        UPDATE public.admin_invitations
        SET token_hash = encode(digest('forged-token', 'sha256'), 'hex')
        WHERE email = 'invited-flow@local.test' AND status = 'pending';
        RAISE EXCEPTION 'token_hash mutation was not rejected';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM NOT LIKE 'admin_invitations.token_hash is immutable%' THEN
            RAISE EXCEPTION 'unexpected token immutability error: %', SQLERRM;
        END IF;
    END;

    -- Invitations are append-only.
    BEGIN
        DELETE FROM public.admin_invitations WHERE email = 'invited-flow@local.test';
        RAISE EXCEPTION 'invitation deletion was not rejected';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM NOT LIKE 'admin_invitations is append-only%' THEN
            RAISE EXCEPTION 'unexpected delete guard error: %', SQLERRM;
        END IF;
    END;

    -- Opcion A: Auth owns the token, so a new invitation may omit token_hash.
    INSERT INTO public.admin_invitations (
        admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
    ) VALUES (
        invited_id, 'auth-owned-token@local.test', 'user', NULL,
        admin_id, now() + interval '48 hours'
    ) RETURNING id INTO invitation_id;

    IF (SELECT token_hash FROM public.admin_invitations WHERE id = invitation_id) IS NOT NULL THEN
        RAISE EXCEPTION 'Auth-owned invitation unexpectedly persisted a token hash';
    END IF;

    -- A failed send/persistence attempt is explicit, auditable and retryable.
    UPDATE public.admin_invitations
    SET status = 'send_failed', failure_code = 'persistence_failed'
    WHERE id = invitation_id;

    IF NOT EXISTS (
        SELECT 1
        FROM public.admin_invitations
        WHERE id = invitation_id AND status = 'send_failed'
          AND token_hash IS NULL AND failure_code = 'persistence_failed'
    ) THEN
        RAISE EXCEPTION 'send_failed invitation state was not persisted';
    END IF;

    BEGIN
        UPDATE public.admin_invitations
        SET status = 'pending'
        WHERE id = invitation_id;
        RAISE EXCEPTION 'send_failed -> pending transition was not rejected';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM NOT LIKE 'admin_invitations invalid status transition%' THEN
            RAISE EXCEPTION 'unexpected send_failed transition error: %', SQLERRM;
        END IF;
    END;

    INSERT INTO public.admin_invitations (
        admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
    ) VALUES (
        invited_id, 'auth-owned-token@local.test', 'user', NULL,
        admin_id, now() + interval '48 hours'
    );

    BEGIN
        INSERT INTO public.admin_invitations (
            admin_member_user_id, email, role, token_hash, created_by_user_id, expires_at
        ) VALUES (
            invited_id, 'auth-owned-token@local.test', 'user', NULL,
            admin_id, now() + interval '48 hours'
        );
        RAISE EXCEPTION 'second pending Auth-owned invitation was not rejected';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;

    BEGIN
        INSERT INTO public.admin_invitations (
            admin_member_user_id, email, role, token_hash, created_by_user_id,
            expires_at, status
        ) VALUES (
            invited_id, 'auth-owned-failure@local.test', 'user', NULL,
            admin_id, now() + interval '48 hours', 'send_failed'
        );
        RAISE EXCEPTION 'send_failed insert without failure_code was not rejected';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;

    INSERT INTO public.admin_membership_audit (
        actor_user_id, target_user_id, entity_type, invitation_id, action,
        old_values, new_values, metadata
    ) VALUES (
        admin_id, invited_id, 'invitation', invitation_id, 'send_failed',
        '{"status":"pending"}'::jsonb,
        '{"status":"send_failed","failure_code":"persistence_failed"}'::jsonb,
        '{"source":"harness"}'::jsonb
    );

    -- Audit vocabulary: lifecycle events must be insertable and append-only.
    INSERT INTO public.admin_membership_audit (
        actor_user_id, target_user_id, entity_type, invitation_id, action,
        old_values, new_values, metadata
    )
    SELECT admin_id, invited_id, 'invitation', i.id, 'invite',
           '{}'::jsonb, jsonb_build_object('status', 'pending', 'role', 'user'),
           jsonb_build_object('source', 'harness')
    FROM public.admin_invitations i
    WHERE i.email = 'invited-flow@local.test' AND i.status = 'pending';
    INSERT INTO public.admin_membership_audit (
        actor_user_id, target_user_id, entity_type, action, old_values, new_values
    )
    VALUES (admin_id, invited_id, 'invitation', 'accept', '{"status":"pending"}'::jsonb, '{"status":"accepted"}'::jsonb),
           (admin_id, invited_id, 'invitation', 'password_set', '{"status":"password_pending"}'::jsonb, '{"status":"ready"}'::jsonb),
           (admin_id, invited_id, 'invitation', 'resend', '{"status":"pending"}'::jsonb, '{"status":"superseded"}'::jsonb),
           (admin_id, invited_id, 'invitation', 'expire', '{"status":"pending"}'::jsonb, '{"status":"expired"}'::jsonb),
           (admin_id, invited_id, 'membership', 'revoke', '{"account_status":"ready"}'::jsonb, '{"account_status":"revoked"}'::jsonb);

    SELECT count(*) INTO audit_count
    FROM public.admin_membership_audit
    WHERE target_user_id = invited_id AND action IN ('invite', 'accept', 'password_set', 'resend', 'expire', 'revoke');
    IF audit_count < 6 THEN
        RAISE EXCEPTION 'invitation lifecycle audit events missing: %', audit_count;
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.admin_membership_audit WHERE action NOT IN (
        'invite', 'resend', 'send_failed', 'delivery_unknown', 'delivery_reconciliation', 'accept', 'password_set',
            'role_change', 'activation', 'deactivation', 'revoke', 'expire'
        )
    ) THEN
        RAISE EXCEPTION 'audit constraint vocabulary mismatch';
    END IF;
END;
$$;

-- Reservation compensation is exercised without calling Auth or sending mail.
DO $$
DECLARE
    admin_id UUID := '30000000-0000-0000-0000-000000000001';
    expired_invitation_id UUID;
    expire_result RECORD;
    expire_audit_count INTEGER;
BEGIN
    INSERT INTO public.admin_invitations (
        email, role, token_hash, status, created_by_user_id, expires_at, last_sent_at,
        metadata, created_at
    ) VALUES (
        'h3-audited-expiry@local.test', 'user', NULL, 'pending', admin_id,
        now() - interval '1 minute', now() - interval '25 hours',
        '{"request_id":"h3-audited-expiry-request"}'::jsonb,
        now() - interval '26 hours'
    ) RETURNING id INTO expired_invitation_id;

    SELECT * INTO expire_result
    FROM public.admin_invitation_expire(expired_invitation_id, admin_id);
    IF NOT expire_result.success OR NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = expired_invitation_id AND status = 'expired'
    ) THEN
        RAISE EXCEPTION 'expired invitation did not transition through the audited RPC: %', expire_result.error_code;
    END IF;
    SELECT * INTO expire_result
    FROM public.admin_invitation_expire(expired_invitation_id, admin_id);
    SELECT count(*) INTO expire_audit_count
    FROM public.admin_membership_audit
    WHERE invitation_id = expired_invitation_id AND action = 'expire';
    IF NOT expire_result.success OR expire_audit_count <> 1 THEN
        RAISE EXCEPTION 'invitation expiry RPC must be idempotent and audit exactly once';
    END IF;
END;
$$;

DO $$
DECLARE
    admin_id UUID := '30000000-0000-0000-0000-000000000001';
    old_invitation_id UUID;
    new_invitation_id UUID;
    reserve_result RECORD;
    failure_result RECORD;
BEGIN
    INSERT INTO public.admin_invitations (
        email, role, token_hash, created_by_user_id, expires_at, last_sent_at, send_count
    ) VALUES (
        'h3-resend-restore@local.test', 'user', NULL, admin_id,
        now() + interval '24 hours', now() - interval '1 hour', 1
    ) RETURNING id INTO old_invitation_id;

    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        'h3-resend-restore@local.test', 'user', admin_id, NULL, true,
        'h3-resend-restore-request', '{"source":"pg17-harness"}'::jsonb,
        now() - interval '5 minutes'
    );
    IF NOT reserve_result.success THEN
        RAISE EXCEPTION 'resend reservation failed: %', reserve_result.error_code;
    END IF;
    new_invitation_id := reserve_result.invitation_id;

    SELECT * INTO failure_result
    FROM public.admin_invitation_fail(new_invitation_id, NULL, 'auth_invite_failed');
    IF NOT failure_result.success THEN
        RAISE EXCEPTION 'failed Auth resend was not compensated: %', failure_result.error_code;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = old_invitation_id AND status = 'pending' AND revoked_at IS NULL
    ) THEN
        RAISE EXCEPTION 'definitive Auth rejection did not restore the previous unexpired invitation';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = new_invitation_id AND status = 'send_failed' AND failure_code = 'auth_invite_failed'
    ) THEN
        RAISE EXCEPTION 'failed resend reservation was not persisted as send_failed';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_membership_audit
        WHERE invitation_id = new_invitation_id AND action = 'send_failed'
          AND metadata ->> 'restored_previous_invitation_id' = old_invitation_id::TEXT
    ) THEN
        RAISE EXCEPTION 'resend compensation was not linked in the audit metadata';
    END IF;

    INSERT INTO public.admin_invitations (
        email, role, token_hash, created_by_user_id, expires_at, last_sent_at, send_count
    ) VALUES (
        'h3-resend-uncertain@local.test', 'user', NULL, admin_id,
        now() + interval '24 hours', now() - interval '1 hour', 1
    ) RETURNING id INTO old_invitation_id;

    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        'h3-resend-uncertain@local.test', 'user', admin_id, NULL, true,
        'h3-resend-uncertain-request', '{"source":"pg17-harness"}'::jsonb,
        now() - interval '5 minutes'
    );
    IF NOT reserve_result.success THEN
        RAISE EXCEPTION 'uncertain resend reservation failed: %', reserve_result.error_code;
    END IF;
    new_invitation_id := reserve_result.invitation_id;

    SELECT * INTO failure_result
    FROM public.admin_invitation_mark_delivery_reconciliation(
        new_invitation_id, NULL, 'auth_accepted', 'invitation_completion_failed'
    );
    IF NOT failure_result.success THEN
        RAISE EXCEPTION 'post-delivery persistence failure was not recorded for reconciliation';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = old_invitation_id AND status = 'superseded'
    ) THEN
        RAISE EXCEPTION 'uncertain post-Auth failure incorrectly restored the old invitation';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = new_invitation_id AND status = 'pending'
          AND metadata ->> 'delivery_outcome' = 'auth_accepted'
          AND metadata ->> 'delivery_state' = 'reconciliation_required'
          AND metadata ->> 'reconciliation_required' = 'true'
    ) THEN
        RAISE EXCEPTION 'successful Auth delivery was incorrectly invalidated by a persistence failure';
    END IF;
END;
$$;

-- Ambiguous Auth delivery is audited without marking a possibly delivered link
-- failed or restoring the previous invitation.
DO $$
DECLARE
    admin_id UUID := '30000000-0000-0000-0000-000000000001';
    old_invitation_id UUID;
    new_invitation_id UUID;
    auth_user_id UUID := '3d000000-0000-0000-0000-000000000001';
    reserve_result RECORD;
    unknown_result RECORD;
    unknown_audit_count INTEGER;
BEGIN
    INSERT INTO auth.users (id, email, encrypted_password, role, aud, created_at, updated_at)
    VALUES (auth_user_id, 'h3-delivery-unknown@local.test', 'x', 'authenticated', 'authenticated', now(), now());
    INSERT INTO public.admin_invitations (
        email, role, token_hash, created_by_user_id, expires_at, last_sent_at, send_count,
        metadata
    ) VALUES (
        'h3-delivery-unknown@local.test', 'user', NULL, admin_id,
        now() + interval '24 hours', now() - interval '1 hour', 1,
        '{"request_id":"h3-delivery-unknown-old"}'::jsonb
    ) RETURNING id INTO old_invitation_id;

    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        'h3-delivery-unknown@local.test', 'user', admin_id, NULL, true,
        'h3-delivery-unknown-request', '{"request_id":"h3-delivery-unknown-request","source":"pg17-harness"}'::jsonb,
        now() - interval '5 minutes'
    );
    IF NOT reserve_result.success THEN
        RAISE EXCEPTION 'ambiguous-delivery reservation failed: %', reserve_result.error_code;
    END IF;
    new_invitation_id := reserve_result.invitation_id;

    SELECT * INTO unknown_result
    FROM public.admin_invitation_mark_delivery_reconciliation(
        new_invitation_id, NULL, 'unknown', 'auth_delivery_unknown'
    );
    IF NOT unknown_result.success THEN
        RAISE EXCEPTION 'ambiguous Auth outcome was not durably recorded: %', unknown_result.error_code;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = new_invitation_id AND status = 'pending'
          AND metadata ->> 'delivery_outcome' = 'unknown'
          AND metadata ->> 'reconciliation_required' = 'true'
    ) THEN
        RAISE EXCEPTION 'ambiguous delivery invalidated or failed the possibly usable invitation';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = old_invitation_id AND status = 'superseded'
    ) THEN
        RAISE EXCEPTION 'ambiguous delivery incorrectly restored the older invitation';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_invitations
        WHERE id = new_invitation_id AND admin_member_user_id = auth_user_id
    ) OR NOT EXISTS (
        SELECT 1 FROM public.admin_members
        WHERE user_id = auth_user_id AND account_status = 'invited'
          AND last_invitation_id = new_invitation_id AND is_active = false
    ) THEN
        RAISE EXCEPTION 'Auth identity discovered after ambiguous delivery was not attached to the pending invitation';
    END IF;

    SELECT count(*) INTO unknown_audit_count
    FROM public.admin_membership_audit
    WHERE invitation_id = new_invitation_id AND action = 'delivery_unknown'
      AND metadata ->> 'request_id' = 'h3-delivery-unknown-request';
    IF unknown_audit_count <> 1 THEN
        RAISE EXCEPTION 'ambiguous Auth outcome must have exactly one audit event, got %', unknown_audit_count;
    END IF;

    SELECT * INTO unknown_result
    FROM public.admin_invitation_mark_delivery_reconciliation(
        new_invitation_id, NULL, 'unknown', 'auth_delivery_unknown'
    );
    SELECT count(*) INTO unknown_audit_count
    FROM public.admin_membership_audit
    WHERE invitation_id = new_invitation_id AND action = 'delivery_unknown'
      AND metadata ->> 'request_id' = 'h3-delivery-unknown-request';
    IF NOT unknown_result.success OR unknown_audit_count <> 1 THEN
        RAISE EXCEPTION 'delivery outcome reconciliation must be idempotent';
    END IF;

    PERFORM set_config('request.jwt.claim.sub', auth_user_id::TEXT, false);
    SELECT * INTO unknown_result FROM public.admin_accept_current_invitation(new_invitation_id);
    IF NOT unknown_result.success OR unknown_result.account_status <> 'password_pending' THEN
        RAISE EXCEPTION 'pending invitation with ambiguous delivery was not safely accept-able: %', unknown_result.error_code;
    END IF;
END;
$$;

\ir ../../tests/sql/h3_invitation_onboarding_harness.sql
\ir ../../tests/sql/h3_onboarding_rbac_hardening_harness.sql
\ir ../../tests/sql/h3_invitation_edge_runtime_harness.sql
SELECT 'h3_pg17_harness_ok' AS result;
