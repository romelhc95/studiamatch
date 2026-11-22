-- FG2 profile onboarding: persist bounded observations and suggestions
-- without replacing effective/manual profile configuration.
-- Additive only. This migration is prepared for review; it has not been
-- applied to Development, Certification, or Pro. db_migrate.py wraps each
-- application and its ledger write in one exec_sql transaction; do not add
-- top-level BEGIN/COMMIT here.

ALTER TABLE public.institution_site_profiles
  ALTER COLUMN site_type DROP NOT NULL,
  ALTER COLUMN discovery_mode DROP NOT NULL;

ALTER TABLE public.institution_site_profiles
  ADD COLUMN IF NOT EXISTS profile_status TEXT NOT NULL DEFAULT 'active'
    CHECK (profile_status IN ('active', 'pending_review')),
  ADD COLUMN IF NOT EXISTS diagnostic_status TEXT NOT NULL DEFAULT 'not_requested'
    CHECK (diagnostic_status IN ('not_requested', 'verified', 'review_required', 'blocked')),
  ADD COLUMN IF NOT EXISTS diagnostic_observed JSONB NOT NULL DEFAULT '{}'::JSONB,
  ADD COLUMN IF NOT EXISTS diagnostic_suggested JSONB NOT NULL DEFAULT '{}'::JSONB,
  ADD COLUMN IF NOT EXISTS diagnostic_provenance JSONB NOT NULL DEFAULT '{}'::JSONB,
  ADD COLUMN IF NOT EXISTS allowed_resource_origins JSONB NOT NULL DEFAULT '[]'::JSONB;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'institution_site_profiles_resource_origins_array'
      AND conrelid = 'public.institution_site_profiles'::regclass
  ) THEN
    ALTER TABLE public.institution_site_profiles
      ADD CONSTRAINT institution_site_profiles_resource_origins_array
      CHECK (jsonb_typeof(allowed_resource_origins) = 'array');
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'institution_site_profiles_active_requires_effective_mode'
      AND conrelid = 'public.institution_site_profiles'::regclass
  ) THEN
    ALTER TABLE public.institution_site_profiles
      ADD CONSTRAINT institution_site_profiles_active_requires_effective_mode
      CHECK (profile_status <> 'active' OR (site_type IS NOT NULL AND discovery_mode IS NOT NULL));
  END IF;
END $$;

COMMENT ON COLUMN public.institution_site_profiles.profile_status IS
  'active profiles may enter the FG2 selector; pending_review rows preserve diagnostics without runnable effective modes.';
COMMENT ON COLUMN public.institution_site_profiles.diagnostic_observed IS
  'Sanitized bounded FG2 observations; never authoritative effective configuration.';
COMMENT ON COLUMN public.institution_site_profiles.diagnostic_suggested IS
  'Sanitized FG2 profile suggestion; applied only under an explicit activation policy and verification.';
COMMENT ON COLUMN public.institution_site_profiles.diagnostic_provenance IS
  'FG2 diagnostic policy version, source SHA, timestamp, and evidence digest; does not copy profiles between environments.';
COMMENT ON COLUMN public.institution_site_profiles.allowed_resource_origins IS
  'Exact origin allowlist for browser subresources. Every request is still publicly resolved, DNS-pinned, paced, and charged to the institution budget.';

-- Read-only schema contract consumed by DB Sync verify. This reports schema
-- metadata only; it does not return profile data or invoke any writer.
CREATE OR REPLACE FUNCTION public.fg2_profile_onboarding_schema_contract()
RETURNS JSONB
LANGUAGE SQL
STABLE
SECURITY INVOKER
SET search_path = pg_catalog
AS $function$
  SELECT jsonb_build_object(
    'schema_version', 1,
    'table_exists', to_regclass('public.institution_site_profiles') IS NOT NULL,
    'effective_modes_nullable', COALESCE((
      SELECT bool_and(is_nullable = 'YES')
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = 'institution_site_profiles'
        AND column_name IN ('site_type', 'discovery_mode')
    ), false),
    'columns', COALESCE((
      SELECT jsonb_object_agg(
        column_name,
        jsonb_build_object(
          'data_type', data_type,
          'is_nullable', is_nullable,
          'column_default', column_default
        )
      )
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = 'institution_site_profiles'
        AND column_name IN (
          'profile_status',
          'diagnostic_status',
          'diagnostic_observed',
          'diagnostic_suggested',
          'diagnostic_provenance',
          'allowed_resource_origins'
        )
    ), '{}'::jsonb),
    'constraints', COALESCE((
      SELECT jsonb_object_agg(
        conname,
        jsonb_build_object(
          'definition', pg_get_constraintdef(oid, true),
          'validated', convalidated
        )
      )
      FROM pg_constraint
      WHERE conrelid = to_regclass('public.institution_site_profiles')
        AND conname IN (
          'institution_site_profiles_profile_status_check',
          'institution_site_profiles_diagnostic_status_check',
          'institution_site_profiles_resource_origins_array',
          'institution_site_profiles_active_requires_effective_mode'
        )
    ), '{}'::jsonb),
    'function', (
      SELECT jsonb_build_object(
        'identity_arguments', pg_get_function_identity_arguments(oid),
        'return_type', format_type(prorettype, NULL),
        'volatility', provolatile,
        'security_definer', prosecdef,
        'search_path', proconfig,
        'anon_can_execute', has_function_privilege('anon', oid, 'EXECUTE'),
        'authenticated_can_execute', has_function_privilege('authenticated', oid, 'EXECUTE'),
        'service_role_can_execute', has_function_privilege('service_role', oid, 'EXECUTE')
      )
      FROM pg_proc
      WHERE oid = to_regprocedure('public.fg2_profile_onboarding_schema_contract()')
    )
  );
$function$;

REVOKE ALL ON FUNCTION public.fg2_profile_onboarding_schema_contract() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fg2_profile_onboarding_schema_contract() FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fg2_profile_onboarding_schema_contract() TO service_role;

COMMENT ON FUNCTION public.fg2_profile_onboarding_schema_contract() IS
  'Read-only FG2 profile onboarding schema contract for the closed Pro verify route; returns no profile rows.';
