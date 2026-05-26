-- Fase 114: Security hardening for Fases 112-113 contracts.
-- Prevents public execution of SECURITY DEFINER RPCs and limits public profile exposure.

REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) FROM anon;
REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) TO service_role;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname = 'exec_sql'
      AND pg_get_function_identity_arguments(p.oid) = 'sql_text text'
  ) THEN
    ALTER FUNCTION public.exec_sql(sql_text text) SET search_path = pg_catalog, public;
    REVOKE ALL ON FUNCTION public.exec_sql(sql_text text) FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.exec_sql(sql_text text) FROM anon;
    REVOKE ALL ON FUNCTION public.exec_sql(sql_text text) FROM authenticated;
    GRANT EXECUTE ON FUNCTION public.exec_sql(sql_text text) TO service_role;
  END IF;
END $$;

-- The courses public RLS policy depends on checking production_enabled through
-- institution_site_profiles. Grant only the columns needed for that predicate.
REVOKE ALL ON public.institution_site_profiles FROM anon;
GRANT SELECT (institution_id, production_enabled) ON public.institution_site_profiles TO anon;

DROP POLICY IF EXISTS profiles_select_public ON public.institution_site_profiles;
CREATE POLICY profiles_select_public ON public.institution_site_profiles
  FOR SELECT TO anon
  USING (production_enabled = true);
