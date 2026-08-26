-- H2 Pro contract: retire the legacy compatibility cohort after strict H2 parity.
-- Scope: Production DDL/DML only after explicit JIT and strict-H2 catalog parity approval.

DO $$
DECLARE
    remaining_legacy_only INTEGER;
    expected_digest TEXT;
    actual_digest TEXT;
    strict_digest TEXT;
    strict_count INTEGER;
    baseline_missing INTEGER;
BEGIN
    IF has_table_privilege('anon', 'public.courses', 'SELECT')
       OR has_table_privilege('authenticated', 'public.courses', 'SELECT') THEN
        RAISE EXCEPTION 'Cannot retire H2 legacy cohort before direct public courses SELECT is revoked';
    END IF;

    SELECT count(*) INTO remaining_legacy_only
    FROM private.h2_legacy_public_course_cohort cohort
    JOIN public.courses c ON c.id = cohort.course_id
    LEFT JOIN public.course_editorial_state es ON es.course_id = c.id
    WHERE NOT (
        c.is_active IS TRUE
        AND c.is_verified IS TRUE
        AND es.editorial_status = 'published'
        AND es.quality_status = 'complete'
        AND es.availability_status = 'available'
        AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = c.institution_id
              AND p.production_enabled IS TRUE
              AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
        )
        AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%')
    );

    SELECT max(snapshot_ids_sha256) INTO expected_digest
      FROM private.h2_legacy_public_course_cohort;
    SELECT 'sha256:' || encode(sha256(convert_to(string_agg(course_id::TEXT, ',' ORDER BY course_id::TEXT), 'UTF8')), 'hex')
      INTO actual_digest
      FROM private.h2_legacy_public_course_cohort;
    SELECT count(*) INTO baseline_missing
      FROM private.h2_legacy_public_course_cohort cohort
      LEFT JOIN public.courses c ON c.id = cohort.course_id
     WHERE c.id IS NULL;
    SELECT count(*), 'sha256:' || encode(sha256(convert_to(string_agg(c.id::TEXT, ',' ORDER BY c.id::TEXT), 'UTF8')), 'hex')
      INTO strict_count, strict_digest
      FROM public.courses c
      JOIN public.course_editorial_state es ON es.course_id = c.id
     WHERE c.is_active IS TRUE
       AND c.is_verified IS TRUE
       AND es.editorial_status = 'published'
       AND es.quality_status = 'complete'
       AND es.availability_status = 'available'
       AND EXISTS (
           SELECT 1
           FROM public.institution_site_profiles p
           WHERE p.institution_id = c.institution_id
             AND p.production_enabled IS TRUE
             AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
       )
       AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%');

    IF remaining_legacy_only <> 0 THEN
        RAISE EXCEPTION 'H2 Pro cannot retire legacy cohort: % legacy-only rows remain', remaining_legacy_only;
    END IF;
    IF baseline_missing <> 0 OR expected_digest IS NULL OR actual_digest <> expected_digest THEN
        RAISE EXCEPTION 'H2 Pro cannot retire legacy cohort: missing %, digest expected %, got %', baseline_missing, expected_digest, actual_digest;
    END IF;
    IF strict_count <> (SELECT max(snapshot_expected_count) FROM private.h2_legacy_public_course_cohort)
       OR strict_digest <> expected_digest THEN
        RAISE EXCEPTION 'H2 Pro cannot retire legacy cohort: strict identity mismatch count %, digest %', strict_count, strict_digest;
    END IF;
END;
$$;

DROP VIEW IF EXISTS public.courses_public_effective;
DROP FUNCTION IF EXISTS public.h2_public_courses_effective();
DROP FUNCTION IF EXISTS private.h2_public_courses_effective();

CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()
RETURNS TABLE (
    id UUID,
    institution_id UUID,
    category_id UUID,
    name TEXT,
    slug VARCHAR,
    url TEXT,
    price_pen NUMERIC,
    price_status TEXT,
    mode TEXT,
    duration TEXT,
    description_long TEXT,
    syllabus TEXT,
    target_audience TEXT,
    requirements TEXT,
    certification TEXT,
    benefits TEXT,
    objectives TEXT,
    start_date DATE,
    start_date_text TEXT,
    course_type TEXT,
    brochure_url TEXT,
    expected_monthly_salary NUMERIC,
    seniority_level VARCHAR,
    roi_months NUMERIC,
    view_count INTEGER,
    comparison_count INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT
        c.id,
        c.institution_id,
        c.category_id,
        COALESCE(es.manual_overrides ->> 'name', c.name) AS name,
        c.slug,
        c.url,
        CASE
            WHEN es.manual_overrides ->> 'price_pen' ~ '^[0-9]+(\.[0-9]+)?$'
                THEN (es.manual_overrides ->> 'price_pen')::NUMERIC
            ELSE c.price_pen
        END AS price_pen,
        COALESCE(es.manual_overrides ->> 'price_status', c.price_status, 'A consultar') AS price_status,
        COALESCE(es.manual_overrides ->> 'mode', c.mode) AS mode,
        COALESCE(es.manual_overrides ->> 'duration', c.duration) AS duration,
        COALESCE(es.manual_overrides ->> 'description_long', c.description_long) AS description_long,
        COALESCE(es.manual_overrides ->> 'syllabus', c.syllabus) AS syllabus,
        COALESCE(es.manual_overrides ->> 'target_audience', c.target_audience) AS target_audience,
        COALESCE(es.manual_overrides ->> 'requirements', c.requirements) AS requirements,
        COALESCE(es.manual_overrides ->> 'certification', c.certification) AS certification,
        COALESCE(es.manual_overrides ->> 'benefits', c.benefits) AS benefits,
        COALESCE(es.manual_overrides ->> 'objectives', c.objectives) AS objectives,
        COALESCE(es.manual_start_date, c.start_date) AS start_date,
        COALESCE(es.manual_overrides ->> 'start_date_text', c.start_date_text, 'Sin confirmar') AS start_date_text,
        c.course_type,
        c.brochure_url,
        c.expected_monthly_salary,
        c.seniority_level,
        c.roi_months,
        c.view_count,
        c.comparison_count,
        c.created_at,
        c.updated_at
    FROM public.courses c
    JOIN public.course_editorial_state es ON es.course_id = c.id
    WHERE c.is_active IS TRUE
      AND c.is_verified IS TRUE
      AND es.editorial_status = 'published'
      AND es.quality_status = 'complete'
      AND es.availability_status = 'available'
      AND EXISTS (
          SELECT 1
          FROM public.institution_site_profiles p
          WHERE p.institution_id = c.institution_id
            AND p.production_enabled IS TRUE
            AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
      )
      AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%');
$$;

REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS
SELECT * FROM private.h2_public_courses_effective();

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

DROP TABLE private.h2_legacy_public_course_cohort;

COMMENT ON FUNCTION private.h2_public_courses_effective() IS
    'H2 strict public course reader after legacy cohort retirement.';
COMMENT ON VIEW public.courses_public_effective IS
    'H2 strict public effective course view after legacy compatibility cohort retirement.';
