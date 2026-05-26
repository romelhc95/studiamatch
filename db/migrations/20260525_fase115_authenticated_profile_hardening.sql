-- Fase 115: Restrict authenticated profile exposure.
-- Keeps institution_site_profiles usable for production gates without exposing scraper config.

REVOKE ALL ON public.institution_site_profiles FROM authenticated;
GRANT SELECT (institution_id, production_enabled) ON public.institution_site_profiles TO authenticated;

DROP POLICY IF EXISTS profiles_select_authenticated ON public.institution_site_profiles;
CREATE POLICY profiles_select_authenticated ON public.institution_site_profiles
  FOR SELECT TO authenticated
  USING (production_enabled = true);

CREATE TABLE IF NOT EXISTS public.schema_repair_audit (
  id bigserial PRIMARY KEY,
  migration_name text NOT NULL,
  table_name text NOT NULL,
  record_id uuid NOT NULL,
  old_values jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (migration_name, table_name, record_id)
);

REVOKE ALL ON public.schema_repair_audit FROM anon;
REVOKE ALL ON public.schema_repair_audit FROM authenticated;
