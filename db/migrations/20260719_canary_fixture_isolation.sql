-- Hide ephemeral release-canary fixtures from all public Data API reads.
-- Canary rows use a reserved slug, profile marker, and URL prefix.

ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institution_site_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.staging_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cleansed_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enriched_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.market_salaries ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    CREATE ROLE canary_runner NOLOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
EXCEPTION WHEN duplicate_object THEN
    NULL;
END;
$$;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM canary_runner;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM canary_runner;
REVOKE ALL PRIVILEGES ON SCHEMA public FROM canary_runner;
DO $$
DECLARE
    parent_role text;
    child_role text;
BEGIN
    FOR parent_role IN
        SELECT parent.rolname
        FROM pg_catalog.pg_auth_members membership
        JOIN pg_catalog.pg_roles parent ON parent.oid = membership.roleid
        JOIN pg_catalog.pg_roles child ON child.oid = membership.member
        WHERE child.rolname = 'canary_runner'
    LOOP
        EXECUTE pg_catalog.format('REVOKE %I FROM canary_runner', parent_role);
    END LOOP;
    FOR child_role IN
        SELECT child.rolname
        FROM pg_catalog.pg_auth_members membership
        JOIN pg_catalog.pg_roles parent ON parent.oid = membership.roleid
        JOIN pg_catalog.pg_roles child ON child.oid = membership.member
        WHERE parent.rolname = 'canary_runner'
          AND child.rolname <> 'postgres'
    LOOP
        EXECUTE pg_catalog.format('REVOKE canary_runner FROM %I', child_role);
    END LOOP;
END;
$$;
GRANT canary_runner TO authenticator;
GRANT USAGE ON SCHEMA public TO canary_runner;
GRANT SELECT ON public.institutions, public.institution_site_profiles,
    public.staging_raw, public.cleansed_programs, public.enriched_programs,
    public.courses, public.categories, public.market_salaries
TO canary_runner;

DROP POLICY IF EXISTS institutions_exclude_release_canary ON public.institutions;
CREATE POLICY institutions_exclude_release_canary
ON public.institutions
AS RESTRICTIVE
FOR SELECT
TO anon, authenticated
USING (slug NOT LIKE 'zz-studiamatch-canary-%');

DROP POLICY IF EXISTS profiles_exclude_release_canary ON public.institution_site_profiles;
CREATE POLICY profiles_exclude_release_canary
ON public.institution_site_profiles
AS RESTRICTIVE
FOR SELECT
TO anon, authenticated
USING (COALESCE(notes, '') <> 'DB_AS_CODE_RELEASE_CANARY');

DROP POLICY IF EXISTS courses_exclude_release_canary ON public.courses;
CREATE POLICY courses_exclude_release_canary
ON public.courses
AS RESTRICTIVE
FOR SELECT
TO anon, authenticated
USING (url IS NULL OR url NOT LIKE 'https://canary.invalid/%');

DROP POLICY IF EXISTS institutions_canary_runner_select ON public.institutions;
CREATE POLICY institutions_canary_runner_select
ON public.institutions FOR SELECT TO canary_runner
USING (slug LIKE 'zz-studiamatch-canary-%' AND status = 'Inactiva');

DROP POLICY IF EXISTS profiles_canary_runner_select ON public.institution_site_profiles;
CREATE POLICY profiles_canary_runner_select
ON public.institution_site_profiles FOR SELECT TO canary_runner
USING (notes = 'DB_AS_CODE_RELEASE_CANARY' AND production_enabled = false);

DROP POLICY IF EXISTS staging_canary_runner_select ON public.staging_raw;
CREATE POLICY staging_canary_runner_select
ON public.staging_raw FOR SELECT TO canary_runner
USING (
    url LIKE 'https://canary.invalid/%'
    AND EXISTS (
        SELECT 1 FROM public.institution_site_profiles p
        WHERE p.institution_id = staging_raw.institution_id
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    )
);

DROP POLICY IF EXISTS cleansed_canary_runner_select ON public.cleansed_programs;
CREATE POLICY cleansed_canary_runner_select
ON public.cleansed_programs FOR SELECT TO canary_runner
USING (
    url LIKE 'https://canary.invalid/%'
    AND EXISTS (
        SELECT 1 FROM public.institution_site_profiles p
        WHERE p.institution_id = cleansed_programs.institution_id
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    )
);

DROP POLICY IF EXISTS enriched_canary_runner_select ON public.enriched_programs;
CREATE POLICY enriched_canary_runner_select
ON public.enriched_programs FOR SELECT TO canary_runner
USING (
    url LIKE 'https://canary.invalid/%'
    AND EXISTS (
        SELECT 1 FROM public.institution_site_profiles p
        WHERE p.institution_id = enriched_programs.institution_id
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    )
);

DROP POLICY IF EXISTS courses_canary_runner_select ON public.courses;
CREATE POLICY courses_canary_runner_select
ON public.courses FOR SELECT TO canary_runner
USING (
    url LIKE 'https://canary.invalid/%'
    AND is_active = false
    AND EXISTS (
        SELECT 1 FROM public.institution_site_profiles p
        WHERE p.institution_id = courses.institution_id
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    )
);

DROP POLICY IF EXISTS market_salaries_canary_runner_select ON public.market_salaries;
CREATE POLICY market_salaries_canary_runner_select
ON public.market_salaries FOR SELECT TO canary_runner
USING (true);

DROP FUNCTION IF EXISTS public.verify_release_canary_guards();
CREATE FUNCTION public.verify_release_canary_guards()
RETURNS TABLE (guards_valid boolean)
LANGUAGE sql
SECURITY INVOKER
SET search_path TO ''
AS $$
    WITH expected_policy(name, relation, permissive, role_kind, marker) AS (
        VALUES
            ('institutions_exclude_release_canary', 'public.institutions'::regclass, false, 'public', 'zz-studiamatch-canary-'),
            ('profiles_exclude_release_canary', 'public.institution_site_profiles'::regclass, false, 'public', 'DB_AS_CODE_RELEASE_CANARY'),
            ('courses_exclude_release_canary', 'public.courses'::regclass, false, 'public', 'https://canary.invalid/'),
            ('institutions_canary_runner_select', 'public.institutions'::regclass, true, 'canary', 'zz-studiamatch-canary-'),
            ('profiles_canary_runner_select', 'public.institution_site_profiles'::regclass, true, 'canary', 'DB_AS_CODE_RELEASE_CANARY'),
            ('staging_canary_runner_select', 'public.staging_raw'::regclass, true, 'canary', 'https://canary.invalid/'),
            ('cleansed_canary_runner_select', 'public.cleansed_programs'::regclass, true, 'canary', 'https://canary.invalid/'),
            ('enriched_canary_runner_select', 'public.enriched_programs'::regclass, true, 'canary', 'https://canary.invalid/'),
            ('courses_canary_runner_select', 'public.courses'::regclass, true, 'canary', 'https://canary.invalid/'),
            ('market_salaries_canary_runner_select', 'public.market_salaries'::regclass, true, 'canary', 'true')
    ), policy_check AS (
        SELECT COUNT(*) = 10 AND BOOL_AND(
            p.polrelid = expected.relation
            AND p.polpermissive = expected.permissive
            AND p.polcmd = 'r'
            AND pg_catalog.pg_get_expr(p.polqual, p.polrelid) LIKE '%' || expected.marker || '%'
            AND CASE expected.role_kind
                WHEN 'public' THEN pg_catalog.cardinality(p.polroles) = 2
                    AND p.polroles @> ARRAY[
                        (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'anon'),
                        (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'authenticated')
                    ]::oid[]
                ELSE pg_catalog.cardinality(p.polroles) = 1
                    AND p.polroles @> ARRAY[
                        (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'canary_runner')
                    ]::oid[]
            END
        ) AS valid
        FROM expected_policy expected
        LEFT JOIN pg_catalog.pg_policy p ON p.polname = expected.name
    ), table_check AS (
        SELECT COUNT(*) = 8 AND BOOL_AND(
            relation.relrowsecurity
            AND pg_catalog.has_table_privilege('canary_runner', relation.oid, 'SELECT')
            AND NOT pg_catalog.has_table_privilege('canary_runner', relation.oid, 'INSERT')
            AND NOT pg_catalog.has_table_privilege('canary_runner', relation.oid, 'UPDATE')
            AND NOT pg_catalog.has_table_privilege('canary_runner', relation.oid, 'DELETE')
            AND NOT pg_catalog.has_table_privilege('canary_runner', relation.oid, 'TRUNCATE')
            AND NOT pg_catalog.has_table_privilege('canary_runner', relation.oid, 'REFERENCES')
            AND NOT pg_catalog.has_table_privilege('canary_runner', relation.oid, 'TRIGGER')
        ) AS valid
        FROM pg_catalog.pg_class relation
        WHERE relation.oid = ANY(ARRAY[
            'public.institutions'::regclass, 'public.institution_site_profiles'::regclass,
            'public.staging_raw'::regclass, 'public.cleansed_programs'::regclass,
            'public.enriched_programs'::regclass, 'public.courses'::regclass,
            'public.categories'::regclass, 'public.market_salaries'::regclass
        ])
    ), role_check AS (
        SELECT NOT runner.rolsuper AND NOT runner.rolinherit AND NOT runner.rolcreaterole
            AND NOT runner.rolcreatedb AND NOT runner.rolcanlogin AND NOT runner.rolreplication
            AND NOT runner.rolbypassrls
            AND pg_catalog.has_schema_privilege('canary_runner', 'public', 'USAGE')
            AND NOT pg_catalog.has_schema_privilege('canary_runner', 'public', 'CREATE')
            AND EXISTS (
                SELECT 1 FROM pg_catalog.pg_auth_members membership
                WHERE membership.roleid = runner.oid
                  AND membership.member = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'authenticator')
            )
            AND NOT EXISTS (
                SELECT 1 FROM pg_catalog.pg_auth_members membership
                WHERE membership.member = runner.oid
            )
            AND EXISTS (
                SELECT 1
                FROM pg_catalog.pg_auth_members membership
                JOIN pg_catalog.pg_roles member_role ON member_role.oid = membership.member
                WHERE membership.roleid = runner.oid
                  AND member_role.rolname = 'authenticator'
                  AND membership.inherit_option = false
            )
            AND NOT EXISTS (
                SELECT 1
                FROM pg_catalog.pg_auth_members membership
                JOIN pg_catalog.pg_roles member_role ON member_role.oid = membership.member
                WHERE membership.roleid = runner.oid
                  AND NOT (
                      member_role.rolname = 'authenticator'
                      OR (
                          member_role.rolname = 'postgres'
                          AND membership.inherit_option = false
                          AND membership.set_option = false
                      )
                  )
            ) AS valid
        FROM pg_catalog.pg_roles runner
        WHERE runner.rolname = 'canary_runner'
    ), expected_function(signature, definer, grant_canary, grant_service) AS (
        VALUES
            ('public.lock_staging_records_scoped(uuid,integer)', true, true, true),
            ('public.atomic_cleansing_promote_scoped(uuid,uuid[],jsonb)', true, true, true),
            ('public.atomic_enrichment_promote_scoped(uuid,jsonb,uuid)', true, true, true),
            ('public.atomic_canary_sync(uuid,uuid,jsonb)', true, true, true),
            ('public.verify_canary_runner_identity()', false, true, false),
            ('public.verify_release_canary_guards()', false, false, true)
    ), function_check AS (
        SELECT COUNT(function_oid) = 6 AND BOOL_AND(
            proc.prosecdef = resolved.definer
            AND owner.rolname = 'postgres'
            AND proc.proconfig = ARRAY['search_path=""']::text[]
            AND pg_catalog.has_function_privilege('canary_runner', function_oid, 'EXECUTE') = resolved.grant_canary
            AND pg_catalog.has_function_privilege('service_role', function_oid, 'EXECUTE') = resolved.grant_service
            AND NOT pg_catalog.has_function_privilege('anon', function_oid, 'EXECUTE')
            AND NOT pg_catalog.has_function_privilege('authenticated', function_oid, 'EXECUTE')
            AND NOT EXISTS (
                SELECT 1
                FROM pg_catalog.aclexplode(proc.proacl) acl
                WHERE acl.privilege_type = 'EXECUTE'
                  AND acl.grantee NOT IN (
                      proc.proowner,
                      CASE WHEN resolved.grant_canary
                          THEN (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'canary_runner')
                          ELSE proc.proowner END,
                      CASE WHEN resolved.grant_service
                          THEN (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'service_role')
                          ELSE proc.proowner END
                  )
            )
        ) AS valid
        FROM (
            SELECT pg_catalog.to_regprocedure(expected.signature) AS function_oid,
                   expected.definer, expected.grant_canary, expected.grant_service
            FROM expected_function expected
        ) resolved
        LEFT JOIN pg_catalog.pg_proc proc ON proc.oid = resolved.function_oid
        LEFT JOIN pg_catalog.pg_roles owner ON owner.oid = proc.proowner
    ), boundary_check AS (
        SELECT NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_class relation
            JOIN pg_catalog.pg_namespace namespace ON namespace.oid = relation.relnamespace
            WHERE namespace.nspname = 'public'
              AND relation.relkind IN ('r', 'p', 'v', 'm', 'f')
              AND (
                  pg_catalog.has_table_privilege('canary_runner', relation.oid, 'INSERT')
                  OR pg_catalog.has_table_privilege('canary_runner', relation.oid, 'UPDATE')
                  OR pg_catalog.has_table_privilege('canary_runner', relation.oid, 'DELETE')
                  OR pg_catalog.has_table_privilege('canary_runner', relation.oid, 'TRUNCATE')
                  OR pg_catalog.has_table_privilege('canary_runner', relation.oid, 'REFERENCES')
                  OR pg_catalog.has_table_privilege('canary_runner', relation.oid, 'TRIGGER')
              )
        ) AND NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_proc proc
            JOIN pg_catalog.pg_namespace namespace ON namespace.oid = proc.pronamespace
            WHERE namespace.nspname = 'public'
              AND pg_catalog.has_function_privilege('canary_runner', proc.oid, 'EXECUTE')
              AND proc.oid <> ALL(ARRAY[
                  pg_catalog.to_regprocedure('public.lock_staging_records_scoped(uuid,integer)'),
                  pg_catalog.to_regprocedure('public.atomic_cleansing_promote_scoped(uuid,uuid[],jsonb)'),
                  pg_catalog.to_regprocedure('public.atomic_enrichment_promote_scoped(uuid,jsonb,uuid)'),
                  pg_catalog.to_regprocedure('public.atomic_canary_sync(uuid,uuid,jsonb)'),
                  pg_catalog.to_regprocedure('public.verify_canary_runner_identity()')
              ])
        ) AS valid
    )
    SELECT policy_check.valid AND table_check.valid AND role_check.valid
        AND function_check.valid AND boundary_check.valid
    FROM policy_check, table_check, role_check, function_check, boundary_check;
$$;

REVOKE ALL ON FUNCTION public.verify_release_canary_guards()
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.verify_release_canary_guards()
TO service_role;
ALTER FUNCTION public.verify_release_canary_guards() OWNER TO postgres;

DROP FUNCTION IF EXISTS public.verify_canary_runner_identity();
CREATE FUNCTION public.verify_canary_runner_identity()
RETURNS TABLE (effective_role text, jwt_role text, expires_at timestamptz)
LANGUAGE sql
SECURITY INVOKER
SET search_path TO ''
AS $$
    SELECT current_user::text,
           claims.value->>'role',
           pg_catalog.to_timestamp((claims.value->>'exp')::double precision)
    FROM (SELECT current_setting('request.jwt.claims', true)::jsonb AS value) claims;
$$;

REVOKE ALL ON FUNCTION public.verify_canary_runner_identity()
FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.verify_canary_runner_identity()
TO canary_runner;
ALTER FUNCTION public.verify_canary_runner_identity() OWNER TO postgres;
