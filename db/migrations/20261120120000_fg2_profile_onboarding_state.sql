-- FG2 profile onboarding: persist bounded observations and suggestions
-- without replacing effective/manual profile configuration.
-- Additive only. This migration is prepared for review; it has not been
-- applied to Development, Certification, or Pro.

BEGIN;

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

COMMIT;
