-- H2 Pro compatibility: freeze the production legacy-visible cohort.
-- Scope: Production DML only after explicit JIT, h2-expand-compat and baseline approval.

DO $$
DECLARE
    expected_count CONSTANT INTEGER := current_setting('app.h2_expected_eligible_count')::INTEGER;
    expected_digest CONSTANT TEXT := current_setting('app.h2_expected_cohort_digest');
    eligible_count INTEGER;
    eligible_digest TEXT;
BEGIN
    SELECT count(*) INTO eligible_count
    FROM public.courses c
    WHERE c.is_active IS TRUE
      AND c.is_verified IS TRUE
      AND EXISTS (
          SELECT 1
          FROM public.institution_site_profiles p
          WHERE p.institution_id = c.institution_id
            AND p.production_enabled IS TRUE
            AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
      )
      AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%');

    SELECT 'sha256:' || encode(sha256(convert_to(string_agg(id::TEXT, ',' ORDER BY id::TEXT), 'UTF8')), 'hex')
      INTO eligible_digest
      FROM (
          SELECT c.id
          FROM public.courses c
          WHERE c.is_active IS TRUE
            AND c.is_verified IS TRUE
            AND EXISTS (
                SELECT 1
                FROM public.institution_site_profiles p
                WHERE p.institution_id = c.institution_id
                  AND p.production_enabled IS TRUE
                  AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
            )
            AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%')
      ) eligible;

    IF eligible_count <> expected_count THEN
        RAISE EXCEPTION 'H2 Pro cohort baseline drift: expected %, got %', expected_count, eligible_count;
    END IF;
    IF eligible_digest <> expected_digest THEN
        RAISE EXCEPTION 'H2 Pro cohort digest drift: expected %, got %', expected_digest, eligible_digest;
    END IF;
END;
$$;

INSERT INTO private.h2_legacy_public_course_cohort (
    course_id,
    reason,
    snapshot_expected_count,
    snapshot_ids_sha256,
    payload_sha,
    authorization_id
)
SELECT
    c.id,
    'preserve pre-H2 production catalog visibility during editorial transition',
    current_setting('app.h2_expected_eligible_count')::INTEGER,
    current_setting('app.h2_expected_cohort_digest'),
    current_setting('app.h2_payload_sha', true),
    current_setting('app.h2_authorization_id', true)
FROM public.courses c
WHERE c.is_active IS TRUE
  AND c.is_verified IS TRUE
  AND EXISTS (
      SELECT 1
      FROM public.institution_site_profiles p
        WHERE p.institution_id = c.institution_id
          AND p.production_enabled IS TRUE
          AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
  )
  AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%')
ON CONFLICT (course_id) DO NOTHING;

DO $$
DECLARE
    expected_count CONSTANT INTEGER := current_setting('app.h2_expected_eligible_count')::INTEGER;
    expected_digest CONSTANT TEXT := current_setting('app.h2_expected_cohort_digest');
    cohort_count INTEGER;
    effective_count INTEGER;
    cohort_digest TEXT;
BEGIN
    SELECT count(*) INTO cohort_count FROM private.h2_legacy_public_course_cohort;
    SELECT count(*) INTO effective_count FROM public.courses_public_effective;
    SELECT 'sha256:' || encode(sha256(convert_to(string_agg(course_id::TEXT, ',' ORDER BY course_id::TEXT), 'UTF8')), 'hex')
      INTO cohort_digest
      FROM private.h2_legacy_public_course_cohort;

    IF cohort_count <> expected_count THEN
        RAISE EXCEPTION 'H2 Pro cohort count mismatch: expected %, got %', expected_count, cohort_count;
    END IF;
    IF effective_count <> expected_count THEN
        RAISE EXCEPTION 'H2 Pro effective view count mismatch after cohort capture: expected %, got %', expected_count, effective_count;
    END IF;
    IF cohort_digest <> expected_digest THEN
        RAISE EXCEPTION 'H2 Pro cohort digest mismatch after capture: expected %, got %', expected_digest, cohort_digest;
    END IF;
END;
$$;
