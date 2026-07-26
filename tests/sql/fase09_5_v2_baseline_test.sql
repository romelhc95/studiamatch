\set ON_ERROR_STOP on

SELECT pg_temp.assert_f95_baseline(
    NOT EXISTS (
        WITH expected(table_name, policy_name) AS (
            VALUES
                ('courses', 'courses_select_public'),
                ('courses', 'courses_select_authenticated'),
                ('courses', 'courses_exclude_release_canary'),
                ('courses', 'courses_canary_runner_select'),
                ('courses', 'courses_service_role'),
                ('leads', 'leads_insert_public'),
                ('leads', 'leads_insert_authenticated'),
                ('leads', 'leads_service_role'),
                ('ratings', 'ratings_select_public'),
                ('ratings', 'ratings_service_role'),
                ('reviews', 'reviews_select_public'),
                ('reviews', 'reviews_service_role'),
                ('institution_site_profiles', 'profiles_select_public'),
                ('institution_site_profiles', 'profiles_select_authenticated'),
                ('institution_site_profiles', 'profiles_exclude_release_canary'),
                ('institution_site_profiles', 'profiles_canary_runner_select'),
                ('institution_site_profiles', 'profiles_service_role'),
                ('institutions', 'institutions_select_public'),
                ('institutions', 'institutions_select_authenticated'),
                ('institutions', 'institutions_exclude_release_canary'),
                ('institutions', 'institutions_canary_runner_select'),
                ('institutions', 'institutions_service_role')
        ), actual AS (
            SELECT policy.tablename, policy.policyname
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename IN (
                  'courses', 'leads', 'ratings', 'reviews',
                  'institution_site_profiles', 'institutions'
              )
        ), difference AS (
            (SELECT * FROM expected EXCEPT ALL SELECT * FROM actual)
            UNION ALL
            (SELECT * FROM actual EXCEPT ALL SELECT * FROM expected)
        )
        SELECT 1 FROM difference
    ) AND (
        SELECT pg_catalog.count(*) = 22
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN (
              'courses', 'leads', 'ratings', 'reviews',
              'institution_site_profiles', 'institutions'
          )
    ),
    'observed Free baseline has exactly the closed 22-policy inventory'
);

SELECT pg_temp.assert_f95_baseline(
    (
        SELECT pg_catalog.count(*) = 4
           AND pg_catalog.bool_and(
               policy.permissive = expected.permissiveness
               AND policy.roles = expected.policy_roles
               AND policy.cmd = expected.command_name
               AND policy.qual = expected.using_expression
               AND policy.with_check IS NOT DISTINCT FROM expected.check_expression
           )
        FROM (VALUES
            (
                'courses', 'courses_canary_runner_select', 'PERMISSIVE',
                ARRAY['canary_runner']::name[], 'SELECT',
                $policy$(url ~~ 'https://canary.invalid/%'::text)$policy$,
                NULL::text
            ),
            (
                'institution_site_profiles', 'profiles_canary_runner_select',
                'PERMISSIVE', ARRAY['canary_runner']::name[], 'SELECT',
                $policy$(COALESCE(notes, ''::text) = 'DB_AS_CODE_RELEASE_CANARY'::text)$policy$,
                NULL::text
            ),
            (
                'institutions', 'institutions_canary_runner_select',
                'PERMISSIVE', ARRAY['canary_runner']::name[], 'SELECT',
                $policy$(slug ~~ 'zz-studiamatch-canary-%'::text)$policy$,
                NULL::text
            ),
            (
                'institution_site_profiles', 'profiles_service_role',
                'PERMISSIVE', ARRAY['service_role']::name[], 'ALL',
                'true', 'true'
            )
        ) AS expected(
            table_name, policy_name, permissiveness, policy_roles,
            command_name, using_expression, check_expression
        )
        JOIN pg_catalog.pg_policies AS policy
          ON policy.schemaname = 'public'
         AND policy.tablename = expected.table_name
         AND policy.policyname = expected.policy_name
    ),
    'observed Free baseline preserves the exact four historical policies'
);

SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS observed_v1_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_f95_baseline(
    NOT :'observed_v1_verifier'::boolean,
    'the frozen v1 verifier rejects the observed policy inventory'
);
