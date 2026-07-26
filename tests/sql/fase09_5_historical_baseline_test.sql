\set ON_ERROR_STOP on

CREATE FUNCTION pg_temp.assert_f95_baseline(condition boolean, message text)
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
    IF condition IS NOT TRUE THEN
        RAISE EXCEPTION 'F9.5 historical baseline assertion failed: %', message;
    END IF;
END;
$function$;

SELECT pg_temp.assert_f95_baseline(
    NOT EXISTS (SELECT 1 FROM public.supabase_migrations),
    'the observed Free ledger is empty'
);

SELECT pg_temp.assert_f95_baseline(
    pg_catalog.to_regprocedure('public.verify_fase08_hito1_contract()') IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM pg_catalog.pg_attribute
        WHERE attrelid = 'public.courses'::regclass
          AND attname = 'publication_status'
          AND NOT attisdropped
    )
    AND EXISTS (
        SELECT 1
        FROM pg_catalog.pg_constraint
        WHERE conrelid = 'public.leads'::regclass
          AND conname = 'chk_leads_source_type'
          AND convalidated
    )
    AND EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class
        WHERE relnamespace = 'public'::regnamespace
          AND relname = 'idx_courses_publication_quality'
          AND relkind = 'i'
    ),
    'representative F8 function, column, constraint and index effects exist'
);

SET ROLE service_role;
SELECT public.verify_fase08_hito1_contract() AS historical_f8_verifier \gset
RESET ROLE;
SELECT pg_temp.assert_f95_baseline(
    NOT :'historical_f8_verifier'::boolean
    AND EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'institution_site_profiles'
          AND policyname = 'profiles_select_authenticated'
    )
    AND (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_policies
        WHERE schemaname = 'public'
          AND policyname IN (
              'institutions_exclude_release_canary',
              'profiles_exclude_release_canary',
              'courses_exclude_release_canary'
          )
    ) = 3,
    'historical unledgered RLS drift is present before the overlay'
);
