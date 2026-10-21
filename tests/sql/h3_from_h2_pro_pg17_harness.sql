\set ON_ERROR_STOP on
-- Disposable Docker PG17 only. The baseline harness initializes this database
-- once; H3 then runs on those exact H2 tables, constraints, grants and data.
-- Default: Pro CURRENT with cohort. h3_contracted_baseline is a separate future
-- contraction scenario, never evidence that the remote cohort has been retired.
\if :{?h3_contracted_baseline}
\else
\set h2_keep_cohort 1
\endif
\ir h2_pro_pg17_harness.sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TEMP TABLE h3_chain_baseline AS
SELECT count(*) AS visible_count,
       to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL AS cohort_present
FROM public.courses_public_effective;

-- Minimal local emulation of Supabase-owned Auth, NOT a replacement public schema.
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
-- PostgREST may set the combined claims GUC without the legacy per-claim GUC.
CREATE FUNCTION auth.uid() RETURNS UUID LANGUAGE sql STABLE
SET search_path = pg_catalog AS $$
  SELECT COALESCE(
    NULLIF(current_setting('request.jwt.claim.sub', true), ''),
    NULLIF(current_setting('request.jwt.claims', true), '')::JSONB ->> 'sub'
  )::UUID
$$;
CREATE FUNCTION auth.jwt() RETURNS JSONB LANGUAGE sql STABLE
SET search_path = pg_catalog AS $$
  SELECT jsonb_build_object('aal', current_setting('request.jwt.claim.aal', true))
$$;

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
\ir ../../db/migrations/20260919_h3_invitation_auth_token_delta.sql
\ir ../../db/migrations/20260920_h3_invitation_edge_runtime.sql
\ir ../../db/migrations/20260921_h3_invitation_onboarding_rpc.sql
\ir ../../db/migrations/20260924_h3_onboarding_rbac_hardening.sql
\ir ../../db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql
\ir ../../db/migrations/20260925_h3_legacy_member_creation_guard.sql
\ir ../../db/migrations/20260925_h3_admin_members_onboarding_reader.sql
\ir ../../db/migrations/20260927_h3_admin_queue_facets_filter.sql

-- Simulate the already-recorded legacy RPC body, then prove the forward patch.
DO $$
DECLARE
  function_definition TEXT;
  old_guard CONSTANT TEXT := 'IF p_first < 1 OR p_first > 100 THEN';
  new_guard CONSTANT TEXT := 'IF p_first IS NULL OR p_first < 1 OR p_first > 100 THEN';
BEGIN
  SELECT pg_catalog.pg_get_functiondef(
    'public.admin_get_course_queue_filtered(integer,text,text,text,text)'::REGPROCEDURE
  ) INTO function_definition;
  IF pg_catalog.strpos(function_definition, new_guard) = 0 THEN
    RAISE EXCEPTION 'baseline queue RPC is missing the null guard fixture';
  END IF;
  function_definition := pg_catalog.replace(function_definition, new_guard, old_guard);
  IF pg_catalog.strpos(function_definition, old_guard) = 0
     OR pg_catalog.strpos(function_definition, new_guard) > 0 THEN
    RAISE EXCEPTION 'could not stage the already-applied legacy queue RPC fixture';
  END IF;
  EXECUTE function_definition;
END;
$$;
\ir ../../db/migrations/20261004_h3_admin_queue_first_null_guard.sql
DO $$ DECLARE function_source TEXT; BEGIN
  SELECT p.prosrc INTO function_source
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = 'public.admin_get_course_queue_filtered(integer,text,text,text,text)'::REGPROCEDURE;
  IF function_source IS NULL
     OR pg_catalog.strpos(function_source, 'IF p_first IS NULL OR p_first < 1 OR p_first > 100 THEN') = 0
     OR pg_catalog.strpos(function_source, 'IF p_first < 1 OR p_first > 100 THEN') > 0 THEN
    RAISE EXCEPTION 'forward migration did not repair the already-applied direct queue RPC';
  END IF;
END; $$;
\ir ../../db/migrations/20260927_h3_publication_visibility_contract.sql
\ir ../../db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql
\ir ../../db/migrations/20261001_h3_invitation_reservation_compensation.sql
\ir ../../db/migrations/20261001_h3_course_editorial_audit_availability.sql

-- Reapply only the new idempotent deltas, not a schema reset or older expansion.
\ir ../../db/migrations/20260927_h3_publication_visibility_contract.sql
\ir ../../db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql
\ir ../../db/migrations/20261001_h3_invitation_reservation_compensation.sql
\ir ../../db/migrations/20261001_h3_course_editorial_audit_availability.sql
\ir ../../db/migrations/20261010_h3_admin_members_service_select.sql

DO $$
BEGIN
  IF (to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL)
       IS DISTINCT FROM (SELECT cohort_present FROM h3_chain_baseline) THEN
    RAISE EXCEPTION 'H3 changed the H2 Pro compatibility cohort lifecycle';
  END IF;
  IF NOT (SELECT cohort_present FROM h3_chain_baseline)
     AND EXISTS (SELECT 1 FROM private.h3_legacy_public_course_cohort) THEN
    RAISE EXCEPTION 'H3 compatibility view populated a retired cohort';
  END IF;
  IF (SELECT count(*) FROM public.courses_public_effective)
       <> (SELECT visible_count FROM h3_chain_baseline) THEN
    RAISE EXCEPTION 'H3 changed the H2 Pro public reader cohort';
  END IF;
  IF has_table_privilege('anon', 'public.courses', 'SELECT')
     OR has_table_privilege('authenticated', 'public.courses', 'SELECT')
     OR has_table_privilege('authenticated', 'public.course_editorial_audit', 'SELECT')
     OR has_table_privilege('authenticated', 'private.h3_legacy_public_course_cohort', 'SELECT') THEN
    RAISE EXCEPTION 'H3 reopened direct table access';
  END IF;
  IF NOT has_table_privilege('service_role', 'public.admin_members', 'SELECT') THEN
    RAISE EXCEPTION 'service-role membership lookup is missing its explicit SELECT grant';
  END IF;
  IF has_function_privilege('anon', 'public.admin_update_course(uuid,jsonb,integer,text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'anonymous editor write became executable';
  END IF;
END;
$$;
SELECT 'h3_from_h2_pro_pg17_harness_ok' AS result;
