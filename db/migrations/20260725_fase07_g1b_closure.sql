SET search_path = '';

DROP FUNCTION IF EXISTS public.increment_view_count(uuid);
DROP FUNCTION IF EXISTS public.increment_view_count_v2(uuid, text);

DROP POLICY IF EXISTS ratings_select_authenticated ON public.ratings;
DROP POLICY IF EXISTS ratings_insert_authenticated ON public.ratings;
DROP POLICY IF EXISTS reviews_select_authenticated ON public.reviews;
DROP POLICY IF EXISTS reviews_insert_authenticated ON public.reviews;

REVOKE SELECT ON TABLE public.ratings, public.reviews
FROM anon, authenticated;

GRANT SELECT (
    id,
    course_id,
    rating_value,
    user_nickname,
    created_at
) ON TABLE public.ratings TO anon, authenticated;

GRANT SELECT (
    id,
    course_id,
    content,
    user_nickname,
    created_at
) ON TABLE public.reviews TO anon, authenticated;

CREATE OR REPLACE FUNCTION public.verify_fase07_g1b_closure()
RETURNS boolean
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $function$
DECLARE
    role_name text;
    column_name text;
    privilege_name text;
BEGIN
    IF NOT public.verify_fase06_g1b_reconciliation()
       OR NOT public.verify_fase06_hito1_contract() THEN
        RETURN false;
    END IF;

    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN ('ratings', 'reviews')
          AND policy.roles && ARRAY['public', 'anon', 'authenticated']::name[]
    ) <> 2 OR EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure.proname IN (
              'increment_view_count', 'increment_view_count_v2'
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN ('ratings', 'reviews')
          AND policy.roles && ARRAY['public', 'anon', 'authenticated']::name[]
          AND (
              policy.policyname <> policy.tablename || '_select_public'
              OR policy.cmd <> 'SELECT'
              OR policy.permissive <> 'PERMISSIVE'
              OR NOT policy.roles @> ARRAY['anon', 'authenticated']::name[]
              OR NOT policy.roles <@ ARRAY['anon', 'authenticated']::name[]
              OR COALESCE(policy.qual, '') NOT LIKE '%moderation_status%approved%'
              OR COALESCE(policy.qual, '') NOT LIKE '%course.id%'
              OR COALESCE(policy.qual, '') NOT LIKE (
                  '%' || policy.tablename || '.course_id%'
              )
              OR COALESCE(policy.qual, '') NOT LIKE '%course.is_active%true%'
              OR COALESCE(policy.qual, '') NOT LIKE '%course.is_verified%true%'
              OR COALESCE(policy.qual, '') NOT LIKE '%profile.institution_id%'
              OR COALESCE(policy.qual, '') NOT LIKE '%course.institution_id%'
              OR COALESCE(policy.qual, '') NOT LIKE '%publication_status%publicado%'
              OR COALESCE(policy.qual, '') NOT LIKE '%production_enabled%true%'
              OR pg_catalog.upper(COALESCE(policy.qual, '')) LIKE '% OR %'
          )
    ) THEN
        RETURN false;
    END IF;

    FOREACH role_name IN ARRAY ARRAY['anon', 'authenticated']
    LOOP
        IF pg_catalog.has_table_privilege(
            role_name, 'public.ratings', 'SELECT'
        ) OR pg_catalog.has_table_privilege(
            role_name, 'public.reviews', 'SELECT'
        ) THEN
            RETURN false;
        END IF;

        FOREACH column_name IN ARRAY ARRAY[
            'id', 'course_id', 'rating_value', 'user_nickname', 'created_at'
        ]
        LOOP
            IF NOT pg_catalog.has_column_privilege(
                role_name, 'public.ratings', column_name, 'SELECT'
            ) THEN
                RETURN false;
            END IF;
        END LOOP;

        FOREACH column_name IN ARRAY ARRAY[
            'id', 'course_id', 'content', 'user_nickname', 'created_at'
        ]
        LOOP
            IF NOT pg_catalog.has_column_privilege(
                role_name, 'public.reviews', column_name, 'SELECT'
            ) THEN
                RETURN false;
            END IF;
        END LOOP;

        FOREACH column_name IN ARRAY ARRAY[
            'moderation_status', 'moderated_at'
        ]
        LOOP
            IF pg_catalog.has_column_privilege(
                role_name, 'public.ratings', column_name, 'SELECT'
            ) OR pg_catalog.has_column_privilege(
                role_name, 'public.reviews', column_name, 'SELECT'
            ) THEN
                RETURN false;
            END IF;
        END LOOP;
    END LOOP;

    FOREACH privilege_name IN ARRAY ARRAY[
        'SELECT', 'INSERT', 'UPDATE', 'DELETE'
    ]
    LOOP
        IF NOT pg_catalog.has_table_privilege(
            'service_role', 'public.ratings', privilege_name
        ) OR NOT pg_catalog.has_table_privilege(
            'service_role', 'public.reviews', privilege_name
        ) THEN
            RETURN false;
        END IF;
    END LOOP;

    IF pg_catalog.has_function_privilege(
        'anon', 'public.verify_fase07_g1b_closure()', 'EXECUTE'
    ) OR pg_catalog.has_function_privilege(
        'authenticated', 'public.verify_fase07_g1b_closure()', 'EXECUTE'
    ) OR NOT pg_catalog.has_function_privilege(
        'service_role', 'public.verify_fase07_g1b_closure()', 'EXECUTE'
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure
        CROSS JOIN LATERAL pg_catalog.aclexplode(
            COALESCE(
                procedure.proacl,
                pg_catalog.acldefault('f', procedure.proowner)
            )
        ) AS acl
        WHERE procedure.oid =
            'public.verify_fase07_g1b_closure()'::regprocedure
          AND acl.privilege_type = 'EXECUTE'
          AND (
              acl.grantee NOT IN (
                  procedure.proowner,
                  (
                      SELECT role.oid
                      FROM pg_catalog.pg_roles AS role
                      WHERE role.rolname = 'service_role'
                  )
              )
              OR (
                  acl.grantee = (
                      SELECT role.oid
                      FROM pg_catalog.pg_roles AS role
                      WHERE role.rolname = 'service_role'
                  )
                  AND acl.is_grantable
              )
          )
    ) THEN
        RETURN false;
    END IF;

    RETURN true;
END;
$function$;

ALTER FUNCTION public.verify_fase07_g1b_closure() OWNER TO postgres;
REVOKE ALL ON FUNCTION public.verify_fase07_g1b_closure()
FROM PUBLIC, anon, authenticated, service_role CASCADE;
GRANT EXECUTE ON FUNCTION public.verify_fase07_g1b_closure()
TO service_role;
