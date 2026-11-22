\set ON_ERROR_STOP on

ALTER TABLE public.institutions
  ADD COLUMN IF NOT EXISTS last_harvest_at timestamptz,
  ADD COLUMN IF NOT EXISTS last_harvest_duration_sec integer;

ALTER TABLE public.institution_site_profiles
  ADD COLUMN IF NOT EXISTS id uuid DEFAULT gen_random_uuid(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
CREATE UNIQUE INDEX IF NOT EXISTS fg2_fixture_site_profile_id_unique
  ON public.institution_site_profiles (id);

-- Constraint names are not globally unique in PostgreSQL. This fixture
-- catches migrations that mistake a same-named check on another relation
-- for the FG2 profile constraint.
CREATE TABLE public.fg2_constraint_name_collision_fixture (
  enabled boolean NOT NULL,
  CONSTRAINT institution_site_profiles_active_requires_effective_mode
    CHECK (enabled)
);

CREATE OR REPLACE FUNCTION public.fg2_fixture_touch_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS fg2_fixture_site_profile_updated_at
  ON public.institution_site_profiles;
CREATE TRIGGER fg2_fixture_site_profile_updated_at
  BEFORE UPDATE ON public.institution_site_profiles
  FOR EACH ROW EXECUTE FUNCTION public.fg2_fixture_touch_updated_at();

-- PostgREST v13 supplies the verified JWT as request.jwt.claims. Mirror the
-- Supabase auth.uid compatibility behavior while retaining the older GUC
-- fallback used by the shared PG17 test bootstrap.
CREATE OR REPLACE FUNCTION auth.uid()
RETURNS uuid LANGUAGE sql STABLE SET search_path = pg_catalog AS $$
  SELECT COALESCE(
    NULLIF(current_setting('request.jwt.claim.sub', true), ''),
    NULLIF(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub'
  )::uuid
$$;
