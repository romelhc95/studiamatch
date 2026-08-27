-- H2 Pro rollback: restore legacy public course reader after contract-public-reader.
-- Scope: Production DDL only after explicit JIT rollback authorization.
-- This forward-only rollback is valid only before retiring the legacy cohort.

DO $$
BEGIN
    IF to_regclass('private.h2_legacy_public_course_cohort') IS NULL THEN
        RAISE EXCEPTION 'Cannot rollback public reader contract after legacy cohort retirement';
    END IF;
END;
$$;

GRANT SELECT ON TABLE public.courses TO anon, authenticated;

DROP POLICY IF EXISTS courses_h2_public_effective_select ON public.courses;
DROP POLICY IF EXISTS courses_select_public ON public.courses;
DROP POLICY IF EXISTS courses_select_authenticated ON public.courses;
DROP POLICY IF EXISTS courses_exclude_release_canary ON public.courses;

CREATE POLICY courses_select_public ON public.courses
    FOR SELECT
    TO anon
    USING (
        is_active IS TRUE
        AND is_verified IS TRUE
        AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = courses.institution_id
              AND p.production_enabled IS TRUE
        )
    );

CREATE POLICY courses_select_authenticated ON public.courses
    FOR SELECT
    TO authenticated
    USING (
        is_active IS TRUE
        AND is_verified IS TRUE
        AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = courses.institution_id
              AND p.production_enabled IS TRUE
        )
    );

CREATE POLICY courses_exclude_release_canary ON public.courses
    AS RESTRICTIVE
    FOR SELECT
    TO anon, authenticated
    USING (
        (url IS NULL OR url NOT LIKE 'https://canary.invalid/%')
        AND NOT EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = courses.institution_id
              AND COALESCE(p.notes, '') = 'DB_AS_CODE_RELEASE_CANARY'
        )
    );

COMMENT ON TABLE public.courses IS
    'Legacy public course reader temporarily restored by H2 rollback-public-reader-contract before legacy cohort retirement.';

DO $$
DECLARE
    restored_policy_count INTEGER;
BEGIN
    SELECT count(*) INTO restored_policy_count
      FROM pg_policies
     WHERE schemaname = 'public'
       AND tablename = 'courses'
       AND policyname IN ('courses_select_public', 'courses_select_authenticated', 'courses_exclude_release_canary');

    IF restored_policy_count <> 3 THEN
        RAISE EXCEPTION 'Rollback did not restore expected courses public policies: %/3', restored_policy_count;
    END IF;
    IF NOT has_table_privilege('anon', 'public.courses', 'SELECT')
       OR NOT has_table_privilege('authenticated', 'public.courses', 'SELECT') THEN
        RAISE EXCEPTION 'Rollback did not restore direct public courses SELECT grants';
    END IF;
END;
$$;
