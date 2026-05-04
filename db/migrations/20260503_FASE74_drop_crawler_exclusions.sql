-- Migration: Fase 74 — DROP crawler_exclusions (replaced by institution_site_profiles.exclusion_patterns)
-- Run in Supabase Dashboard > SQL Editor on BOTH Free and Pro
-- PREREQUISITE: institution_site_profiles must have exclusion_patterns populated for ALL institutions

BEGIN;

-- Drop policies first (must happen before DROP TABLE)
DROP POLICY IF EXISTS "crawler_exclusions_select_public" ON crawler_exclusions;
DROP POLICY IF EXISTS "crawler_exclusions_service_role" ON crawler_exclusions;
DROP POLICY IF EXISTS "profiles_select_public" ON institution_site_profiles;

-- Drop the table itself
DROP TABLE IF EXISTS crawler_exclusions CASCADE;

-- Verify profiles exist as replacement
DO $$
DECLARE
    profile_count INTEGER;
    ce_orphans INTEGER;
BEGIN
    SELECT COUNT(*) INTO profile_count FROM institution_site_profiles
    WHERE exclusion_patterns IS NOT NULL AND jsonb_array_length(exclusion_patterns) > 0;

    RAISE NOTICE 'institution_site_profiles with exclusion_patterns: %', profile_count;

    IF profile_count < 10 THEN
        RAISE EXCEPTION 'Cannot drop crawler_exclusions: only % profiles have exclusion_patterns (need >=10)', profile_count;
    END IF;
END $$;

COMMIT;
