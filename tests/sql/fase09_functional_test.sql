\set ON_ERROR_STOP on

CREATE FUNCTION pg_temp.assert_true(condition boolean, message text)
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
    IF condition IS NOT TRUE THEN
        RAISE EXCEPTION 'FASE-09 assertion failed: %', message;
    END IF;
END;
$function$;

SELECT pg_temp.assert_true(
    (
        SELECT owner.rolname = 'postgres'
           AND procedure.prosecdef
           AND procedure.prorettype = 'jsonb'::regtype
           AND procedure.proconfig = ARRAY['search_path=""']::text[]
        FROM pg_catalog.pg_proc AS procedure
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = procedure.proowner
        WHERE procedure.oid = 'public.exec_sql(text)'::regprocedure
    ),
    'exec_sql owner/security/return/search_path contract'
);
SELECT pg_temp.assert_true(
    NOT pg_catalog.has_function_privilege(
        'anon', 'public.exec_sql(text)', 'EXECUTE'
    )
    AND NOT pg_catalog.has_function_privilege(
        'authenticated', 'public.exec_sql(text)', 'EXECUTE'
    )
    AND pg_catalog.has_function_privilege(
        'service_role', 'public.exec_sql(text)', 'EXECUTE'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure
        CROSS JOIN LATERAL pg_catalog.aclexplode(
            COALESCE(
                procedure.proacl,
                pg_catalog.acldefault('f', procedure.proowner)
            )
        ) AS acl
        WHERE procedure.oid = 'public.exec_sql(text)'::regprocedure
          AND acl.privilege_type = 'EXECUTE'
          AND acl.grantee NOT IN (
              procedure.proowner,
              (
                  SELECT role.oid
                  FROM pg_catalog.pg_roles AS role
                  WHERE role.rolname = 'service_role'
              )
          )
    ),
    'exec_sql minimum privilege contract'
);

SELECT pg_temp.assert_true(
    CASE WHEN :'expect_applied'::boolean THEN
        (
            SELECT pg_catalog.count(*) = 4
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
            FROM public.supabase_migrations
        )
        AND pg_catalog.to_regprocedure(
            'public.verify_fase08_hito1_contract()'
        ) IS NOT NULL
        AND pg_catalog.to_regprocedure(
            'public.atomic_enrichment_promote(jsonb,uuid)'
        ) IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.courses'::regclass
              AND attribute.attname = 'publication_status'
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
        )
    ELSE
        NOT EXISTS (SELECT 1 FROM public.supabase_migrations)
        AND pg_catalog.to_regprocedure(
            'public.atomic_cleansing_promote(uuid[],jsonb)'
        ) IS NULL
        AND pg_catalog.to_regprocedure(
            'public.verify_fase08_hito1_contract()'
        ) IS NULL
        AND pg_catalog.to_regprocedure(
            'public.increment_view_count(uuid)'
        ) IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.courses'::regclass
              AND attribute.attname = 'publication_status'
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
        )
        AND EXISTS (
            SELECT 1
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename = 'leads'
              AND policy.policyname = 'fase09_final_verifier_fault'
        )
    END,
    'atomic package commit or rollback contract'
);

\if :expect_applied
SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS package_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_true(
    :'package_verifier'::boolean,
    'final package verifier after commit'
);
\endif
