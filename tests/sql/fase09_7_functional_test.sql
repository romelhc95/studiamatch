\set ON_ERROR_STOP on

BEGIN;

CREATE FUNCTION pg_temp.assert_true(condition boolean, message text)
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
    IF condition IS NOT TRUE THEN
        RAISE EXCEPTION 'F9.7 assertion failed: %', message;
    END IF;
END;
$function$;

SET ROLE service_role;
SELECT public.verify_fase09_7_notify_new_lead_retirement() AS initial_verifier \gset
SELECT public.verify_fase09_7_public_access_closure() AS access_verifier \gset
SELECT public.verify_fase08_hito1_contract() AS transitive_f8_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(:'initial_verifier'::boolean, 'initial verifier');
SELECT pg_temp.assert_true(:'access_verifier'::boolean, 'access verifier');
SELECT pg_temp.assert_true(
    :'transitive_f8_verifier'::boolean, 'transitive F8 wrapper'
);
SELECT pg_temp.assert_true(
    pg_catalog.to_regprocedure('public.notify_new_lead()') IS NULL,
    'notify_new_lead function retired'
);
SELECT pg_temp.assert_true(
    NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_record
        WHERE NOT trigger_record.tgisinternal
          AND (
              trigger_record.tgrelid = 'public.leads'::regclass
              OR trigger_record.tgname = 'trg_notify_new_lead'
          )
    ),
    'notify_new_lead trigger retired'
);

INSERT INTO public.institution_site_profiles (
    institution_id, production_enabled, exclusion_patterns
) VALUES
    ('91000000-0000-0000-0000-000000000001', true, '[]'),
    ('91000000-0000-0000-0000-000000000002', false, '[]');

INSERT INTO public.courses (
    id, name, slug, url, institution_id, is_active, is_verified,
    publication_status
) VALUES
    (
        '92000000-0000-0000-0000-000000000001', 'Public fixture',
        'public-fixture', 'https://fixture.invalid/public',
        '91000000-0000-0000-0000-000000000001', true, true, 'publicado'
    ),
    (
        '92000000-0000-0000-0000-000000000002', 'Private fixture',
        'private-fixture', 'https://fixture.invalid/private',
        '91000000-0000-0000-0000-000000000002', true, true, 'publicado'
    );

SET ROLE anon;
INSERT INTO public.leads (
    first_name, last_name, email, whatsapp, source_page, type, course_id,
    area_interest, budget, modality, description,
    is_late_enrollment_request
) VALUES (
    'Anon', 'Fixture', 'anon@example.test', '+51000000001', 'detail',
    'information', '92000000-0000-0000-0000-000000000001', 'technology',
    1000, 'remote', 'transaction-scoped fixture', true
);
RESET ROLE;

SET ROLE authenticated;
INSERT INTO public.leads (
    first_name, last_name, email, whatsapp, source_page, type, course_id,
    area_interest, budget, modality, description,
    is_late_enrollment_request
) VALUES (
    'Auth', 'Fixture', 'auth@example.test', '+51000000002', 'home',
    'contact', NULL, 'business', NULL, 'hybrid', NULL, false
);
RESET ROLE;

SAVEPOINT denied_lead_select;
\set ON_ERROR_STOP off
SET ROLE anon;
SELECT email FROM public.leads LIMIT 1;
\set denied_lead_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_lead_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_lead_select_state' = '42501', 'anon lead SELECT denied'
);

SAVEPOINT denied_auth_lead_select;
\set ON_ERROR_STOP off
SET ROLE authenticated;
SELECT email FROM public.leads LIMIT 1;
\set denied_auth_lead_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_auth_lead_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_auth_lead_select_state' = '42501',
    'authenticated lead SELECT denied'
);

SAVEPOINT denied_email_select;
\set ON_ERROR_STOP off
SET ROLE authenticated;
SELECT recipient_email FROM public.email_log LIMIT 1;
\set denied_email_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_email_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_email_select_state' = '42501',
    'authenticated email_log SELECT denied'
);

SAVEPOINT denied_anon_email_select;
\set ON_ERROR_STOP off
SET ROLE anon;
SELECT recipient_email FROM public.email_log LIMIT 1;
\set denied_anon_email_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_anon_email_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_anon_email_select_state' = '42501',
    'anon email_log SELECT denied'
);

SAVEPOINT denied_managed_id;
\set ON_ERROR_STOP off
SET ROLE anon;
INSERT INTO public.leads (id, first_name, email, whatsapp) VALUES (
    '93000000-0000-0000-0000-000000000001', 'Managed',
    'managed-id@example.test', '+51000000003'
);
\set denied_managed_id_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_managed_id;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_managed_id_state' = '42501', 'managed id denied'
);

SAVEPOINT denied_managed_status;
\set ON_ERROR_STOP off
SET ROLE anon;
INSERT INTO public.leads (
    first_name, email, whatsapp, status
) VALUES (
    'Managed', 'managed-status@example.test', '+51000000007', 'pending'
);
\set denied_managed_status_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_managed_status;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_managed_status_state' = '42501', 'managed status denied'
);

SAVEPOINT denied_managed_created_at;
\set ON_ERROR_STOP off
SET ROLE authenticated;
INSERT INTO public.leads (
    first_name, email, whatsapp, created_at
) VALUES (
    'Managed', 'managed-created@example.test', '+51000000008',
    '2026-07-27T00:00:00Z'
);
\set denied_managed_created_at_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_managed_created_at;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_managed_created_at_state' = '42501',
    'managed created_at denied'
);

SAVEPOINT denied_managed_source;
\set ON_ERROR_STOP off
SET ROLE authenticated;
INSERT INTO public.leads (
    first_name, email, whatsapp, lead_source_type
) VALUES (
    'Managed', 'managed-source@example.test', '+51000000004', 'organic'
);
\set denied_managed_source_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_managed_source;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_managed_source_state' = '42501',
    'managed lead_source_type denied even when organic'
);

SAVEPOINT denied_malformed;
\set ON_ERROR_STOP off
SET ROLE anon;
INSERT INTO public.leads (first_name, email, whatsapp) VALUES (
    'Malformed', 'not-an-email', '+51000000005'
);
\set denied_malformed_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_malformed;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_malformed_state' = '42501', 'malformed email denied by policy'
);

SAVEPOINT denied_private_course;
\set ON_ERROR_STOP off
SET ROLE authenticated;
INSERT INTO public.leads (first_name, email, whatsapp, course_id) VALUES (
    'Private', 'private@example.test', '+51000000006',
    '92000000-0000-0000-0000-000000000002'
);
\set denied_private_course_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_private_course;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_private_course_state' = '42501',
    'non-public course denied by policy'
);

SET ROLE service_role;
SELECT pg_catalog.count(*) AS service_lead_count FROM public.leads \gset
SELECT pg_catalog.count(*) AS service_email_count FROM public.email_log \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'service_lead_count'::integer = 2, 'service reads leads'
);
SELECT pg_temp.assert_true(
    :'service_email_count'::integer = 0, 'service reads email_log'
);
SELECT pg_temp.assert_true(
    (
        SELECT pg_catalog.bool_and(pg_catalog.has_table_privilege(
            'service_role', required_table.table_name, 'SELECT'
        ))
        FROM pg_catalog.unnest(ARRAY[
            'public.institutions', 'public.categories',
            'public.category_rules', 'public.market_salaries',
            'public.courses', 'public.institution_site_profiles',
            'public.staging_raw', 'public.cleansed_programs',
            'public.enriched_programs', 'public.leads', 'public.email_log'
        ]::text[]) AS required_table(table_name)
    ),
    'service reads every automatic FG table'
);
REVOKE SELECT ON TABLE public.categories FROM service_role;
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS service_reader_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'service_reader_drift'::boolean, 'service reader ACL drift'
);
GRANT SELECT ON TABLE public.categories TO service_role;

GRANT INSERT (status) ON TABLE public.leads TO anon;
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS grant_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(NOT :'grant_drift'::boolean, 'column grant drift');
REVOKE INSERT (status) ON TABLE public.leads FROM anon;

GRANT MAINTAIN ON TABLE public.leads TO authenticated;
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS maintain_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'maintain_drift'::boolean, 'MAINTAIN grant drift'
);
REVOKE MAINTAIN ON TABLE public.leads FROM authenticated;

GRANT SELECT (recipient_email) ON TABLE public.email_log TO authenticated;
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS select_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'select_drift'::boolean, 'column SELECT drift'
);
REVOKE SELECT (recipient_email) ON TABLE public.email_log FROM authenticated;

CREATE ROLE fase097_private_reader NOLOGIN NOBYPASSRLS NOSUPERUSER;
CREATE POLICY fase097_private_reader_select
ON public.email_log
FOR SELECT
TO fase097_private_reader
USING (false);
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS private_policy \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'private_policy'::boolean, 'unrelated private policy is allowed'
);
DROP POLICY fase097_private_reader_select ON public.email_log;
DROP ROLE fase097_private_reader;

CREATE ROLE fase097_policy_parent NOLOGIN NOBYPASSRLS NOSUPERUSER;
GRANT fase097_policy_parent TO anon;
CREATE POLICY fase097_transitive_select
ON public.email_log
FOR SELECT
TO fase097_policy_parent
USING (true);
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS policy_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'policy_drift'::boolean, 'transitive SELECT policy drift'
);
DROP POLICY fase097_transitive_select ON public.email_log;
REVOKE fase097_policy_parent FROM anon;
DROP ROLE fase097_policy_parent;

ALTER TABLE public.email_log DISABLE ROW LEVEL SECURITY;
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS rls_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(NOT :'rls_drift'::boolean, 'RLS drift');
ALTER TABLE public.email_log ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.leads
ALTER COLUMN lead_source_type SET DEFAULT 'sponsored';
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS default_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'default_drift'::boolean, 'organic default drift'
);
ALTER TABLE public.leads
ALTER COLUMN lead_source_type SET DEFAULT 'organic';

ALTER TABLE public.courses DISABLE ROW LEVEL SECURITY;
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS courses_rls_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'courses_rls_drift'::boolean, 'F8 courses RLS drift'
);
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.courses
ALTER COLUMN publication_status SET DEFAULT 'publicado';
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS publication_default_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'publication_default_drift'::boolean, 'F8 publication default drift'
);
ALTER TABLE public.courses
ALTER COLUMN publication_status SET DEFAULT 'borrador';

CREATE ROLE fase097_courses_parent NOLOGIN NOBYPASSRLS NOSUPERUSER;
GRANT fase097_courses_parent TO authenticated;
CREATE POLICY fase097_inherited_courses_select
ON public.courses FOR SELECT TO fase097_courses_parent USING (true);
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS inherited_courses_policy_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'inherited_courses_policy_drift'::boolean,
    'F8 inherited courses SELECT policy drift'
);
DROP POLICY fase097_inherited_courses_select ON public.courses;
REVOKE fase097_courses_parent FROM authenticated;
DROP ROLE fase097_courses_parent;

SAVEPOINT f8_constraint_drift;
ALTER TABLE public.courses DROP CONSTRAINT chk_courses_data_quality_status;
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS constraint_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'constraint_drift'::boolean, 'F8 representative constraint drift'
);
ROLLBACK TO SAVEPOINT f8_constraint_drift;

SAVEPOINT f8_index_drift;
DROP INDEX public.idx_courses_publication_quality;
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS index_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'index_drift'::boolean, 'F8 representative index drift'
);
ROLLBACK TO SAVEPOINT f8_index_drift;

GRANT EXECUTE ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid)
TO anon;
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS function_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'function_drift'::boolean, 'F8 representative function ACL drift'
);
REVOKE EXECUTE ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid)
FROM anon;

CREATE ROLE fase097_insert_parent NOLOGIN NOBYPASSRLS NOSUPERUSER;
GRANT fase097_insert_parent TO anon;
CREATE POLICY fase097_inherited_leads_insert
ON public.leads
AS PERMISSIVE
FOR INSERT
TO fase097_insert_parent
WITH CHECK (true);
SET ROLE service_role;
SELECT (
    NOT public.verify_fase09_7_public_access_closure()
    AND NOT public.verify_fase08_hito1_contract()
) AS inherited_insert_drift \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'inherited_insert_drift'::boolean,
    'inherited permissive leads INSERT policy drift'
);
SET ROLE anon;
INSERT INTO public.leads (first_name, email, whatsapp) VALUES (
    'Bypass', 'malformed', '+51000000999'
);
RESET ROLE;
SELECT pg_temp.assert_true(
    (
        SELECT pg_catalog.count(*) = 1
        FROM public.leads
        WHERE email = 'malformed'
    ),
    'malformed insert is accepted only while verifier is false'
);
DELETE FROM public.leads WHERE email = 'malformed';
DROP POLICY fase097_inherited_leads_insert ON public.leads;
REVOKE fase097_insert_parent FROM anon;
DROP ROLE fase097_insert_parent;

SAVEPOINT denied_verifier;
\set ON_ERROR_STOP off
SET ROLE anon;
SELECT public.verify_fase09_7_public_access_closure();
\set denied_verifier_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_verifier;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_verifier_state' = '42501', 'verifier is service-only'
);

SAVEPOINT denied_retirement_verifier;
\set ON_ERROR_STOP off
SET ROLE authenticated;
SELECT public.verify_fase09_7_notify_new_lead_retirement();
\set denied_retirement_verifier_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_retirement_verifier;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_retirement_verifier_state' = '42501',
    'trigger retirement verifier is service-only'
);

SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure() AS final_verifier \gset
SELECT public.verify_fase09_7_notify_new_lead_retirement() AS final_retirement \gset
RESET ROLE;
SELECT pg_temp.assert_true(:'final_verifier'::boolean, 'final verifier');
SELECT pg_temp.assert_true(
    :'final_retirement'::boolean, 'final trigger retirement verifier'
);

ROLLBACK;
