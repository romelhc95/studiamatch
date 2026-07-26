\set ON_ERROR_STOP on

CREATE FUNCTION pg_temp.assert_true(condition boolean, message text)
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
    IF condition IS NOT TRUE THEN
        RAISE EXCEPTION 'F9.5 assertion failed: %', message;
    END IF;
END;
$function$;

SELECT pg_temp.assert_true(
    pg_catalog.current_setting('server_version_num')::integer >= 170000
    AND pg_catalog.current_setting('server_version_num')::integer < 180000,
    'PostgreSQL major version is 17'
);

SELECT pg_temp.assert_true(
    (
        SELECT pg_catalog.count(*) = 5
           AND pg_catalog.count(DISTINCT version) = 1
           AND pg_catalog.count(*) FILTER (
               WHERE name = '20260724_fase06_g1b_reconciliation'
                 AND statements = 'sha256:d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df'
           ) = 1
           AND pg_catalog.count(*) FILTER (
               WHERE name = '20260724_fase06_hito1_editorial_contract'
                 AND statements = 'sha256:b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a'
           ) = 1
           AND pg_catalog.count(*) FILTER (
               WHERE name = '20260725_fase07_g1b_closure'
                 AND statements = 'sha256:9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120'
           ) = 1
           AND pg_catalog.count(*) FILTER (
               WHERE name = '20260725_fase08_hito1_functional_closure'
                 AND statements = 'sha256:7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527'
           ) = 1
           AND pg_catalog.count(*) FILTER (
               WHERE name = '20260726_fase09_5_rls_canary_reconciliation'
                   AND statements = 'sha256:4959b3f1ad60e2fe3a6e9a23161dd0467cfc549e10c1262ba8a0bb2aaf4c9a01'
           ) = 1
        FROM public.supabase_migrations
    ),
    'exact five-entry ledger'
);

SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS fase08_verifier \gset
SELECT public.verify_fase09_5_rls_canary_reconciliation() AS fase095_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'fase08_verifier'::boolean AND :'fase095_verifier'::boolean,
    'F8 and F9.5 verifiers converge'
);

SELECT pg_temp.assert_true(
    NOT pg_catalog.has_column_privilege(
        'anon', 'public.leads', 'status', 'UPDATE'
    ),
    'table ACL reset removes pre-existing column grants'
);

SELECT pg_temp.assert_true(
    (
        SELECT owner.rolname = 'postgres'
           AND language_record.lanname = 'plpgsql'
           AND NOT procedure_record.prosecdef
           AND procedure_record.provolatile = 's'
           AND procedure_record.proconfig = ARRAY['search_path=""']::text[]
           AND NOT pg_catalog.has_function_privilege(
               'anon', procedure_record.oid, 'EXECUTE'
           )
           AND NOT pg_catalog.has_function_privilege(
               'authenticated', procedure_record.oid, 'EXECUTE'
           )
           AND pg_catalog.has_function_privilege(
               'service_role', procedure_record.oid, 'EXECUTE'
           )
           AND NOT EXISTS (
               SELECT 1
               FROM pg_catalog.aclexplode(
                   COALESCE(
                       procedure_record.proacl,
                       pg_catalog.acldefault('f', procedure_record.proowner)
                   )
               ) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND (
                     acl.grantee NOT IN (
                         procedure_record.proowner,
                         'service_role'::regrole
                     )
                     OR (
                         acl.grantee = 'service_role'::regrole
                         AND acl.is_grantable
                     )
                 )
           )
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        WHERE procedure_record.oid =
            'public.verify_fase09_5_rls_canary_reconciliation()'::regprocedure
    ),
    'successor verifier owner mode path and ACL'
);

SELECT pg_temp.assert_true(
    (
        SELECT pg_catalog.count(*) = 3
           AND pg_catalog.bool_and(
               policy.permissive = 'RESTRICTIVE'
               AND policy.roles = ARRAY['anon', 'authenticated']::name[]
               AND policy.cmd = 'SELECT'
               AND policy.with_check IS NULL
               AND pg_catalog.regexp_replace(
                   policy.qual, E'\\s+', ' ', 'g'
               ) = expected.using_expression
           )
        FROM (VALUES
            (
                'institutions', 'institutions_exclude_release_canary',
                $policy$(slug !~~ 'zz-studiamatch-canary-%'::text)$policy$
            ),
            (
                'institution_site_profiles', 'profiles_exclude_release_canary',
                $policy$((COALESCE(notes, ''::text) <> 'DB_AS_CODE_RELEASE_CANARY'::text) AND (EXISTS ( SELECT 1 FROM institutions institution_record WHERE (institution_record.id = institution_site_profiles.institution_id))))$policy$
            ),
            (
                'courses', 'courses_exclude_release_canary',
                $policy$(((url IS NULL) OR (url !~~ 'https://canary.invalid/%'::text)) AND (EXISTS ( SELECT 1 FROM institutions institution_record WHERE (institution_record.id = courses.institution_id))))$policy$
            )
        ) AS expected(table_name, policy_name, using_expression)
        JOIN pg_catalog.pg_policies AS policy
          ON policy.schemaname = 'public'
         AND policy.tablename = expected.table_name
         AND policy.policyname = expected.policy_name
    ),
    'exact restrictive canary policy semantics'
);

SELECT pg_temp.assert_true(
    (
        SELECT policy.permissive = 'PERMISSIVE'
           AND policy.roles = ARRAY['anon', 'authenticated']::name[]
           AND policy.cmd = 'SELECT'
           AND policy.qual = '(production_enabled = true)'
           AND policy.with_check IS NULL
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename = 'institution_site_profiles'
          AND policy.policyname = 'profiles_select_public'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename = 'institution_site_profiles'
          AND policy.policyname = 'profiles_select_authenticated'
    ),
    'unified profile policy and redundant policy removal'
);

INSERT INTO public.institutions (id, name, slug) VALUES
    ('11000000-0000-0000-0000-000000000001', 'Ordinary fixture', 'ordinary-fixture'),
    ('11000000-0000-0000-0000-000000000002', 'Combined canary fixture', 'zz-studiamatch-canary-combined'),
    ('11000000-0000-0000-0000-000000000003', 'Profile canary fixture', 'profile-canary-fixture'),
    ('11000000-0000-0000-0000-000000000004', 'Institution canary fixture', 'zz-studiamatch-canary-institution');

INSERT INTO public.institution_site_profiles (
    institution_id, production_enabled, exclusion_patterns, notes
) VALUES
    ('11000000-0000-0000-0000-000000000001', true, '["private"]', 'ordinary'),
    ('11000000-0000-0000-0000-000000000002', true, '["private"]', 'DB_AS_CODE_RELEASE_CANARY'),
    ('11000000-0000-0000-0000-000000000003', true, '["private"]', 'DB_AS_CODE_RELEASE_CANARY'),
    ('11000000-0000-0000-0000-000000000004', true, '["private"]', 'ordinary');

INSERT INTO public.courses (
    id, name, slug, url, institution_id, is_active, is_verified,
    publication_status
) VALUES
    (
        '12000000-0000-0000-0000-000000000001', 'Ordinary course',
        'ordinary-course', 'https://fixture.invalid/ordinary',
        '11000000-0000-0000-0000-000000000001', true, true, 'publicado'
    ),
    (
        '12000000-0000-0000-0000-000000000002', 'Canary course',
        'canary-course', 'https://canary.invalid/release',
        '11000000-0000-0000-0000-000000000002', true, true, 'publicado'
    ),
    (
        '12000000-0000-0000-0000-000000000003', 'Independent canary course',
        'independent-canary-course', 'https://canary.invalid/independent',
        '11000000-0000-0000-0000-000000000001', true, true, 'publicado'
    ),
    (
        '12000000-0000-0000-0000-000000000004', 'Profile-only canary course',
        'profile-only-canary-course', 'https://fixture.invalid/profile-canary',
        '11000000-0000-0000-0000-000000000003', true, true, 'publicado'
    ),
    (
        '12000000-0000-0000-0000-000000000005', 'Institution-only canary course',
        'institution-only-canary-course', 'https://fixture.invalid/institution-canary',
        '11000000-0000-0000-0000-000000000004', true, true, 'publicado'
    );

INSERT INTO public.ratings (
    id, course_id, rating_value, user_nickname, moderation_status
) VALUES
    (
        '13000000-0000-0000-0000-000000000001',
        '12000000-0000-0000-0000-000000000001', 5, 'ordinary', 'approved'
    ),
    (
        '13000000-0000-0000-0000-000000000002',
        '12000000-0000-0000-0000-000000000002', 5, 'profile-canary', 'approved'
    ),
    (
        '13000000-0000-0000-0000-000000000003',
        '12000000-0000-0000-0000-000000000003', 5, 'url-canary', 'approved'
    ),
    (
        '13000000-0000-0000-0000-000000000004',
        '12000000-0000-0000-0000-000000000004', 5, 'profile-canary-only', 'approved'
    ),
    (
        '13000000-0000-0000-0000-000000000005',
        '12000000-0000-0000-0000-000000000005', 5, 'institution-canary-only', 'approved'
    );

INSERT INTO public.reviews (
    id, course_id, content, user_nickname, moderation_status
) VALUES
    (
        '14000000-0000-0000-0000-000000000001',
        '12000000-0000-0000-0000-000000000001', 'ordinary', 'ordinary',
        'approved'
    ),
    (
        '14000000-0000-0000-0000-000000000002',
        '12000000-0000-0000-0000-000000000002', 'profile canary',
        'profile-canary', 'approved'
    ),
    (
        '14000000-0000-0000-0000-000000000003',
        '12000000-0000-0000-0000-000000000003', 'url canary',
        'url-canary', 'approved'
    ),
    (
        '14000000-0000-0000-0000-000000000004',
        '12000000-0000-0000-0000-000000000004', 'profile canary only',
        'profile-canary-only', 'approved'
    ),
    (
        '14000000-0000-0000-0000-000000000005',
        '12000000-0000-0000-0000-000000000005', 'institution canary only',
        'institution-canary-only', 'approved'
    );

SET ROLE anon;
SELECT pg_catalog.count(id) AS anon_institutions FROM public.institutions \gset
SELECT pg_catalog.count(institution_id) AS anon_profiles
FROM public.institution_site_profiles \gset
SELECT pg_catalog.count(id) AS anon_courses FROM public.courses \gset
SELECT pg_catalog.count(id) AS anon_ratings FROM public.ratings \gset
SELECT pg_catalog.count(id) AS anon_reviews FROM public.reviews \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'anon_institutions'::integer = 2
    AND :'anon_profiles'::integer = 1
    AND :'anon_courses'::integer = 1
    AND :'anon_ratings'::integer = 1
    AND :'anon_reviews'::integer = 1,
    'anon excludes direct and relational canary rows'
);

SET ROLE authenticated;
SELECT pg_catalog.count(id) AS auth_institutions FROM public.institutions \gset
SELECT pg_catalog.count(institution_id) AS auth_profiles
FROM public.institution_site_profiles \gset
SELECT pg_catalog.count(id) AS auth_courses FROM public.courses \gset
SELECT pg_catalog.count(id) AS auth_ratings FROM public.ratings \gset
SELECT pg_catalog.count(id) AS auth_reviews FROM public.reviews \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'auth_institutions'::integer = 2
    AND :'auth_profiles'::integer = 1
    AND :'auth_courses'::integer = 1
    AND :'auth_ratings'::integer = 1
    AND :'auth_reviews'::integer = 1,
    'authenticated excludes direct and relational canary rows'
);

\set ON_ERROR_STOP off
SET ROLE anon;
SELECT notes FROM public.institution_site_profiles;
\set anon_notes_state :SQLSTATE
RESET ROLE;
SET ROLE authenticated;
SELECT exclusion_patterns FROM public.institution_site_profiles;
\set auth_patterns_state :SQLSTATE
RESET ROLE;
SET ROLE anon;
SELECT contact_email FROM public.institutions;
\set anon_contact_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'anon_notes_state' = '42501'
    AND :'auth_patterns_state' = '42501'
    AND :'anon_contact_state' = '42501',
    'profile and institution sensitive columns remain denied'
);

SET ROLE anon;
INSERT INTO public.leads (
    first_name, last_name, email, whatsapp, source_page, type, course_id,
    area_interest, budget, modality, description, is_late_enrollment_request
) VALUES (
    'Ordinary', 'Fixture', 'ordinary@example.invalid', '+51000000000',
    'detail', 'info', '12000000-0000-0000-0000-000000000001',
    'Testing', 100, 'online', 'Public form payload', true
);
\set ON_ERROR_STOP off
INSERT INTO public.leads (first_name, email, whatsapp, course_id)
VALUES (
    'Canary URL', 'canary-url@example.invalid', '+51000000001',
    '12000000-0000-0000-0000-000000000003'
);
\set anon_url_canary_lead_state :SQLSTATE
INSERT INTO public.leads (first_name, email, whatsapp, course_id)
VALUES (
    'Canary profile', 'canary-profile@example.invalid', '+51000000002',
    '12000000-0000-0000-0000-000000000004'
);
\set anon_profile_canary_lead_state :SQLSTATE
INSERT INTO public.leads (first_name, email, whatsapp, course_id)
VALUES (
    'Canary institution', 'canary-institution@example.invalid',
    '+51000000009', '12000000-0000-0000-0000-000000000005'
);
\set anon_institution_canary_lead_state :SQLSTATE
INSERT INTO public.leads (id, first_name, email, whatsapp)
VALUES (
    '15000000-0000-0000-0000-000000000003', 'Managed ID',
    'managed-id@example.invalid', '+51000000003'
);
\set anon_managed_id_state :SQLSTATE
INSERT INTO public.leads (first_name, email, whatsapp, status)
VALUES (
    'Managed status', 'managed-status@example.invalid', '+51000000004',
    'accepted'
);
\set anon_managed_status_state :SQLSTATE
INSERT INTO public.leads (first_name, email, whatsapp, created_at)
VALUES (
    'Managed timestamp', 'managed-time@example.invalid', '+51000000005',
    pg_catalog.now()
);
\set anon_managed_timestamp_state :SQLSTATE
INSERT INTO public.leads (first_name, email, whatsapp, lead_source_type)
VALUES (
    'Managed source', 'managed-source@example.invalid', '+51000000006',
    'sponsored'
);
\set anon_managed_source_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'anon_url_canary_lead_state' = '42501'
    AND :'anon_profile_canary_lead_state' = '42501'
    AND :'anon_institution_canary_lead_state' = '42501'
    AND :'anon_managed_id_state' = '42501'
    AND :'anon_managed_status_state' = '42501'
    AND :'anon_managed_timestamp_state' = '42501'
    AND :'anon_managed_source_state' = '42501'
    AND (SELECT pg_catalog.count(*) FROM public.leads) = 1,
    'lead insert is form-only and cannot reference canary dimensions'
);

SET ROLE authenticated;
INSERT INTO public.leads (first_name, email, whatsapp, course_id)
VALUES (
    'Authenticated', 'authenticated@example.invalid', '+51000000007',
    '12000000-0000-0000-0000-000000000001'
);
\set ON_ERROR_STOP off
INSERT INTO public.leads (first_name, email, whatsapp, status)
VALUES (
    'Authenticated managed', 'authenticated-managed@example.invalid',
    '+51000000008', 'accepted'
);
\set auth_managed_status_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'auth_managed_status_state' = '42501'
    AND (SELECT pg_catalog.count(*) FROM public.leads) = 2,
    'authenticated receives the same form-only lead contract'
);

SET ROLE service_role;
SELECT pg_catalog.count(id) AS service_institutions FROM public.institutions \gset
SELECT pg_catalog.count(institution_id) AS service_profiles
FROM public.institution_site_profiles \gset
SELECT pg_catalog.count(id) AS service_courses FROM public.courses \gset
SELECT pg_catalog.count(notes) AS service_notes
FROM public.institution_site_profiles \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'service_institutions'::integer = 4
    AND :'service_profiles'::integer = 4
    AND :'service_courses'::integer = 5
    AND :'service_notes'::integer = 4,
    'service role sees ordinary and canary rows including protected columns'
);

ALTER ROLE service_role NOBYPASSRLS;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS service_without_bypass \gset
SELECT pg_catalog.count(*) AS service_profiles_without_bypass
FROM public.institution_site_profiles \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'service_without_bypass'::boolean
    AND :'service_profiles_without_bypass'::integer = 0,
    'service role must retain BYPASSRLS for complete operational visibility'
);
ALTER ROLE service_role BYPASSRLS;

ALTER ROLE service_role SUPERUSER;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS service_superuser \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'service_superuser'::boolean,
    'service role cannot be a superuser'
);
ALTER ROLE service_role NOSUPERUSER;

CREATE ROLE fase095_service_parent NOLOGIN BYPASSRLS;
GRANT fase095_service_parent TO service_role;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS service_privileged_parent \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'service_privileged_parent'::boolean,
    'service role cannot inherit an additional privileged role'
);
REVOKE fase095_service_parent FROM service_role;
DROP ROLE fase095_service_parent;

ALTER ROLE anon BYPASSRLS;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS anon_with_bypass \gset
RESET ROLE;
SET ROLE anon;
SELECT pg_catalog.count(*) AS bypassed_institutions
FROM public.institutions \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'anon_with_bypass'::boolean
    AND :'bypassed_institutions'::integer = 4,
    'public roles cannot bypass RLS'
);
ALTER ROLE anon NOBYPASSRLS;

ALTER ROLE authenticated SUPERUSER;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS auth_superuser \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'auth_superuser'::boolean,
    'public roles cannot be superusers'
);
ALTER ROLE authenticated NOSUPERUSER;

CREATE ROLE fase095_bypass_parent NOLOGIN BYPASSRLS;
GRANT fase095_bypass_parent TO anon;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS anon_bypass_membership \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'anon_bypass_membership'::boolean,
    'anon cannot inherit membership in a BYPASSRLS role'
);
REVOKE fase095_bypass_parent FROM anon;
DROP ROLE fase095_bypass_parent;

CREATE ROLE fase095_superuser_parent NOLOGIN SUPERUSER;
GRANT fase095_superuser_parent TO authenticated;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS auth_super_membership \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'auth_super_membership'::boolean,
    'authenticated cannot inherit membership in a superuser role'
);
REVOKE fase095_superuser_parent FROM authenticated;
DROP ROLE fase095_superuser_parent;

BEGIN;
ALTER TABLE public.institutions OWNER TO anon;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS untrusted_table_owner \gset
RESET ROLE;
ROLLBACK;
SELECT pg_temp.assert_true(
    NOT :'untrusted_table_owner'::boolean,
    'all six RLS tables require trusted ownership'
);

GRANT INSERT ON TABLE public.leads TO PUBLIC;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS public_table_acl \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'public_table_acl'::boolean,
    'table ACL granted to PUBLIC fails closed'
);
REVOKE INSERT ON TABLE public.leads FROM PUBLIC;

GRANT SELECT (id) ON TABLE public.institutions TO PUBLIC;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS public_column_acl \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'public_column_acl'::boolean,
    'column ACL granted to PUBLIC fails closed'
);
REVOKE SELECT (id) ON TABLE public.institutions FROM PUBLIC;

GRANT REFERENCES ON TABLE public.institutions TO anon;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS unexpected_table_acl \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'unexpected_table_acl'::boolean,
    'unexpected table ACL fails closed'
);
REVOKE REFERENCES ON TABLE public.institutions FROM anon;

GRANT SELECT (id) ON TABLE public.institutions TO anon WITH GRANT OPTION;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS grantable_column_acl \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'grantable_column_acl'::boolean,
    'grantable public column ACL fails closed'
);
REVOKE GRANT OPTION FOR SELECT (id)
ON TABLE public.institutions FROM anon CASCADE;

GRANT EXECUTE
ON FUNCTION public.verify_fase09_5_rls_canary_reconciliation()
TO service_role WITH GRANT OPTION;
SET ROLE service_role;
SELECT public.verify_fase09_5_rls_canary_reconciliation()
AS grantable_successor_acl \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'grantable_successor_acl'::boolean,
    'grantable successor verifier ACL fails closed'
);
REVOKE GRANT OPTION FOR EXECUTE
ON FUNCTION public.verify_fase09_5_rls_canary_reconciliation()
FROM service_role CASCADE;

ALTER FUNCTION public.verify_fase09_5_rls_canary_reconciliation() VOLATILE;
SET ROLE service_role;
SELECT public.verify_fase09_5_rls_canary_reconciliation()
AS volatile_successor \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'volatile_successor'::boolean,
    'volatile successor verifier fails closed'
);
ALTER FUNCTION public.verify_fase09_5_rls_canary_reconciliation() STABLE;

ALTER FUNCTION public.atomic_enrichment_promote(jsonb, uuid) STABLE;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS stable_mutating_rpc \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'stable_mutating_rpc'::boolean,
    'the mutating enrichment RPC must remain volatile'
);
ALTER FUNCTION public.atomic_enrichment_promote(jsonb, uuid) VOLATILE;

ALTER TABLE public.institutions DISABLE ROW LEVEL SECURITY;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS institutions_rls_disabled \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'institutions_rls_disabled'::boolean,
    'disabled institutions RLS fails closed'
);
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;

CREATE POLICY fase09_5_unknown_institution
ON public.institutions AS RESTRICTIVE
FOR SELECT TO anon USING (true);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS f8_unknown_institution \gset
SELECT public.verify_fase09_5_rls_canary_reconciliation()
AS f95_unknown_institution \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'f8_unknown_institution'::boolean
    AND NOT :'f95_unknown_institution'::boolean,
    'unknown institution policy fails both verifiers'
);
DROP POLICY fase09_5_unknown_institution ON public.institutions;

CREATE POLICY fase09_5_unknown_service
ON public.institutions FOR SELECT TO service_role USING (true);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS f8_unknown_service \gset
SELECT public.verify_fase09_5_rls_canary_reconciliation()
AS f95_unknown_service \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'f8_unknown_service'::boolean
    AND NOT :'f95_unknown_service'::boolean,
    'unknown service policy fails both verifiers'
);
DROP POLICY fase09_5_unknown_service ON public.institutions;

CREATE POLICY fase09_5_unknown_other_role
ON public.institutions FOR SELECT TO postgres USING (true);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS f8_unknown_other_role \gset
SELECT public.verify_fase09_5_rls_canary_reconciliation()
AS f95_unknown_other_role \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'f8_unknown_other_role'::boolean
    AND NOT :'f95_unknown_other_role'::boolean,
    'unknown policy for any role fails both verifiers'
);
DROP POLICY fase09_5_unknown_other_role ON public.institutions;

CREATE POLICY fase09_5_unknown_public
ON public.leads FOR SELECT TO PUBLIC USING (true);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS f8_unknown \gset
SELECT public.verify_fase09_5_rls_canary_reconciliation() AS f95_unknown \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'f8_unknown'::boolean AND NOT :'f95_unknown'::boolean,
    'unknown public policy fails both verifiers'
);
DROP POLICY fase09_5_unknown_public ON public.leads;

SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS f8_final \gset
SELECT public.verify_fase09_5_rls_canary_reconciliation() AS f95_final \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'f8_final'::boolean AND :'f95_final'::boolean,
    'verifiers recover after synthetic drift removal'
);
