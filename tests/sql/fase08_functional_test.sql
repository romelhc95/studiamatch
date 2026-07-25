\set ON_ERROR_STOP on

CREATE FUNCTION pg_temp.assert_true(condition boolean, message text)
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
    IF condition IS NOT TRUE THEN
        RAISE EXCEPTION 'FASE-08 assertion failed: %', message;
    END IF;
END;
$function$;

SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS initial_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(:'initial_verifier'::boolean, 'initial verifier');

INSERT INTO public.institution_site_profiles (
    institution_id, production_enabled, exclusion_patterns
) VALUES
    ('10000000-0000-0000-0000-000000000001', true, '["private-pattern"]'),
    ('10000000-0000-0000-0000-000000000002', false, '[]');

INSERT INTO public.courses (
    id, name, slug, url, institution_id, is_active, is_verified,
    publication_status, view_count, comparison_count
) VALUES
    (
        '20000000-0000-0000-0000-000000000001', 'Visible', 'visible',
        'https://fixture.invalid/visible',
        '10000000-0000-0000-0000-000000000001', true, true,
        'publicado', 7, 3
    ),
    (
        '20000000-0000-0000-0000-000000000002', 'Disabled', 'disabled',
        'https://fixture.invalid/disabled',
        '10000000-0000-0000-0000-000000000002', true, true,
        'publicado', 11, 5
    );

INSERT INTO public.ratings (
    id, course_id, rating_value, user_nickname, moderation_status
) VALUES
    (
        '30000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001', 5, 'approved-user',
        'approved'
    ),
    (
        '30000000-0000-0000-0000-000000000002',
        '20000000-0000-0000-0000-000000000001', 1, 'pending-user',
        'pending'
    );

INSERT INTO public.reviews (
    id, course_id, content, user_nickname, moderation_status
) VALUES
    (
        '40000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001', 'approved review',
        'approved-user', 'approved'
    ),
    (
        '40000000-0000-0000-0000-000000000002',
        '20000000-0000-0000-0000-000000000001', 'pending review',
        'pending-user', 'pending'
    );

SET ROLE anon;
SELECT pg_catalog.count(id) AS anon_course_count FROM public.courses \gset
SELECT pg_catalog.count(id) AS anon_rating_count FROM public.ratings \gset
SELECT pg_catalog.count(id) AS anon_review_count FROM public.reviews \gset
INSERT INTO public.leads (
    id, first_name, email, whatsapp, course_id
) VALUES (
    '50000000-0000-0000-0000-000000000001', 'Anon',
    'anon@example.test', '+51000000001',
    '20000000-0000-0000-0000-000000000001'
);
RESET ROLE;

SELECT pg_temp.assert_true(:'anon_course_count'::integer = 1, 'anon course RLS');
SELECT pg_temp.assert_true(:'anon_rating_count'::integer = 1, 'anon rating RLS');
SELECT pg_temp.assert_true(:'anon_review_count'::integer = 1, 'anon review RLS');

\set ON_ERROR_STOP off
SET ROLE anon;
SELECT view_count FROM public.courses LIMIT 1;
\set anon_legacy_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'anon_legacy_state' = '42501', 'anon legacy course ACL'
);

\set ON_ERROR_STOP off
SET ROLE anon;
INSERT INTO public.leads (
    id, first_name, email, whatsapp, lead_source_type
) VALUES (
    '50000000-0000-0000-0000-000000000002', 'Sponsored',
    'sponsored@example.test', '+51000000002', 'sponsored'
);
\set anon_sponsored_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'anon_sponsored_state' = '42501', 'anon sponsored lead RLS'
);

SET ROLE authenticated;
SELECT pg_catalog.count(id) AS authenticated_course_count
FROM public.courses \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'authenticated_course_count'::integer = 1,
    'authenticated course RLS'
);

\set ON_ERROR_STOP off
SET ROLE authenticated;
SELECT exclusion_patterns FROM public.institution_site_profiles LIMIT 1;
\set authenticated_private_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'authenticated_private_state' = '42501',
    'authenticated profile private ACL'
);

\set ON_ERROR_STOP off
SET ROLE anon;
SELECT public.verify_fase08_hito1_contract();
\set anon_verifier_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'anon_verifier_state' = '42501', 'verifier is not public'
);

SET ROLE service_role;
SELECT view_count AS service_view_count
FROM public.courses
WHERE id = '20000000-0000-0000-0000-000000000001' \gset
INSERT INTO public.leads (
    id, first_name, email, whatsapp, lead_source_type
) VALUES (
    '50000000-0000-0000-0000-000000000003', 'Service',
    'service@example.test', '+51000000003', 'sponsored'
);
RESET ROLE;
SELECT pg_temp.assert_true(
    :'service_view_count'::integer = 7, 'service role positive ACL'
);

INSERT INTO public.cleansed_programs (
    id, institution_id, url, clean_name, status
) VALUES (
    '60000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    'https://fixture.invalid/enriched', 'Enriched fixture', 'pending'
);

SET ROLE service_role;
SELECT pg_catalog.count(*) AS rpc_insert_count
FROM public.atomic_enrichment_promote(
    '[{
        "cleansed_id": "60000000-0000-0000-0000-000000000001",
        "institution_id": "10000000-0000-0000-0000-000000000001",
        "url": "https://fixture.invalid/enriched",
        "official_name": "First name",
        "duration_months": "3.5",
        "curriculum_summary": {"units": 2},
        "is_mock_data": false,
        "metadata": {"source": "insert"},
        "brochure_url": "https://fixture.invalid/insert.pdf"
    }]'::jsonb,
    '60000000-0000-0000-0000-000000000001'
) \gset
RESET ROLE;

SELECT pg_temp.assert_true(:'rpc_insert_count'::integer = 1, 'RPC insert result');
SELECT pg_temp.assert_true(
    (
        SELECT metadata = '{"source":"insert"}'::jsonb
           AND brochure_url = 'https://fixture.invalid/insert.pdf'
        FROM public.enriched_programs
        WHERE cleansed_id = '60000000-0000-0000-0000-000000000001'
    ),
    'RPC insert metadata and brochure'
);

SET ROLE service_role;
SELECT pg_catalog.count(*) AS rpc_update_count
FROM public.atomic_enrichment_promote(
    '[{
        "cleansed_id": "60000000-0000-0000-0000-000000000001",
        "institution_id": "10000000-0000-0000-0000-000000000001",
        "url": "https://fixture.invalid/enriched",
        "official_name": "Updated name",
        "duration_months": "4",
        "curriculum_summary": {"units": 3},
        "is_mock_data": false,
        "metadata": {"source": "update"},
        "brochure_url": "https://fixture.invalid/update.pdf"
    }]'::jsonb,
    '60000000-0000-0000-0000-000000000001'
) \gset
RESET ROLE;

SELECT pg_temp.assert_true(:'rpc_update_count'::integer = 1, 'RPC update result');
SELECT pg_temp.assert_true(
    (
        SELECT metadata = '{"source":"update"}'::jsonb
           AND brochure_url = 'https://fixture.invalid/update.pdf'
        FROM public.enriched_programs
        WHERE cleansed_id = '60000000-0000-0000-0000-000000000001'
    ),
    'RPC update metadata and brochure'
);

INSERT INTO public.cleansed_programs (
    id, institution_id, url, clean_name, status
) VALUES (
    '60000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    'https://fixture.invalid/empty-metadata', 'Empty metadata', 'pending'
);
SET ROLE service_role;
SELECT pg_catalog.count(*) AS empty_metadata_rpc_count
FROM public.atomic_enrichment_promote(
    '[{
        "cleansed_id": "60000000-0000-0000-0000-000000000002",
        "institution_id": "10000000-0000-0000-0000-000000000001",
        "url": "https://fixture.invalid/empty-metadata",
        "official_name": "Empty metadata",
        "duration_months": "1",
        "curriculum_summary": {},
        "is_mock_data": false,
        "metadata": null
    }]'::jsonb,
    '60000000-0000-0000-0000-000000000002'
) \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'empty_metadata_rpc_count'::integer = 1
    AND (
        SELECT metadata = '{}'::jsonb
        FROM public.enriched_programs
        WHERE cleansed_id = '60000000-0000-0000-0000-000000000002'
    ),
    'empty RPC metadata remains an object'
);

\set ON_ERROR_STOP off
SET ROLE service_role;
SELECT public.atomic_enrichment_promote(
    '[{
        "cleansed_id": "60000000-0000-0000-0000-000000000002",
        "institution_id": "10000000-0000-0000-0000-000000000001",
        "url": "https://fixture.invalid/empty-metadata",
        "official_name": "Mismatched",
        "duration_months": "1",
        "curriculum_summary": {},
        "is_mock_data": false
    }]'::jsonb,
    '60000000-0000-0000-0000-000000000001'
);
\set rpc_identity_state :SQLSTATE
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'rpc_identity_state' = 'P0001', 'RPC identity mismatch is rejected'
);

ALTER TABLE public.courses DISABLE ROW LEVEL SECURITY;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS disabled_rls_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'disabled_rls_verifier'::boolean, 'disabled RLS drift detection'
);
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;

CREATE POLICY leads_unexpected_public_read
ON public.leads
FOR SELECT
TO anon
USING (true);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS permissive_policy_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'permissive_policy_verifier'::boolean,
    'extra permissive lead policy drift detection'
);
DROP POLICY leads_unexpected_public_read ON public.leads;

CREATE POLICY courses_unexpected_restrictive
ON public.courses AS RESTRICTIVE
FOR SELECT
TO anon
USING (false);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS restrictive_policy_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'restrictive_policy_verifier'::boolean,
    'extra restrictive policy drift detection'
);
DROP POLICY courses_unexpected_restrictive ON public.courses;

CREATE ROLE fase08_inherited_public NOLOGIN;
GRANT fase08_inherited_public TO anon;
CREATE POLICY courses_inherited_public
ON public.courses
FOR SELECT
TO fase08_inherited_public
USING (true);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS inherited_policy_verifier \gset
RESET ROLE;
SET ROLE anon;
SELECT pg_catalog.count(id) AS inherited_policy_course_count
FROM public.courses \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'inherited_policy_verifier'::boolean
    AND :'inherited_policy_course_count'::integer = 2,
    'inherited public policy drift detection'
);
DROP POLICY courses_inherited_public ON public.courses;
REVOKE fase08_inherited_public FROM anon;
DROP ROLE fase08_inherited_public;

DROP POLICY courses_select_public ON public.courses;
CREATE POLICY courses_select_public
ON public.courses
FOR SELECT
TO anon
USING (
    true OR (
        is_active = true
        AND is_verified = true
        AND publication_status = 'publicado'
        AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles AS profile
            WHERE profile.institution_id = courses.institution_id
              AND profile.production_enabled = true
        )
    )
);
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS same_name_policy_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'same_name_policy_verifier'::boolean,
    'same-name policy expression drift detection'
);
DROP POLICY courses_select_public ON public.courses;
CREATE POLICY courses_select_public
ON public.courses
FOR SELECT
TO anon
USING (
    is_active = true
    AND is_verified = true
    AND publication_status = 'publicado'
    AND EXISTS (
        SELECT 1
        FROM public.institution_site_profiles AS profile
        WHERE profile.institution_id = courses.institution_id
          AND profile.production_enabled = true
    )
);

GRANT INSERT ON TABLE public.institution_site_profiles TO anon;
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS profile_acl_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    NOT :'profile_acl_verifier'::boolean,
    'unexpected profile write ACL detection'
);
REVOKE INSERT ON TABLE public.institution_site_profiles FROM anon;

SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS final_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(:'final_verifier'::boolean, 'final verifier');
