-- Fase 100: explicit institution gates for discovery, pipeline and production.
-- `pipeline_ready` remains as a temporary compatibility fallback in code.

ALTER TABLE public.institution_site_profiles
    ADD COLUMN IF NOT EXISTS discovery_enabled BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS pipeline_enabled BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS production_enabled BOOLEAN NOT NULL DEFAULT false;

UPDATE public.institution_site_profiles
SET
    discovery_enabled = discovery_enabled OR COALESCE(pipeline_ready, false),
    pipeline_enabled = pipeline_enabled OR COALESCE(pipeline_ready, false),
    production_enabled = production_enabled OR COALESCE(pipeline_ready, false);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'institution_site_profiles_pipeline_requires_discovery'
    ) THEN
        ALTER TABLE public.institution_site_profiles
            ADD CONSTRAINT institution_site_profiles_pipeline_requires_discovery
            CHECK (NOT pipeline_enabled OR discovery_enabled);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'institution_site_profiles_production_requires_pipeline'
    ) THEN
        ALTER TABLE public.institution_site_profiles
            ADD CONSTRAINT institution_site_profiles_production_requires_pipeline
            CHECK (NOT production_enabled OR pipeline_enabled);
    END IF;
END $$;

COMMENT ON COLUMN public.institution_site_profiles.discovery_enabled IS
    'Allows institution URL discovery/harvesting into staging_raw.';
COMMENT ON COLUMN public.institution_site_profiles.pipeline_enabled IS
    'Allows cleansing and enrichment pipeline processing for this institution.';
COMMENT ON COLUMN public.institution_site_profiles.production_enabled IS
    'Allows synced courses for this institution to be publicly active.';
