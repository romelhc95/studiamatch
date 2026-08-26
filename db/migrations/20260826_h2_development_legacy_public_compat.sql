-- H2: development compatibility cohort for transparent public catalog transition.
-- Scope: Free/Development compatibility DDL+DML only under explicit JIT.
-- No Pro, production, schedules, canaries, deploys, or broad publication are authorized here.

CREATE SCHEMA IF NOT EXISTS private;

CREATE TABLE IF NOT EXISTS private.h2_legacy_public_course_cohort (
    course_id UUID PRIMARY KEY REFERENCES public.courses(id) ON DELETE RESTRICT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    contract_version TEXT NOT NULL DEFAULT 'h2-legacy-public-compat-v1',
    reason TEXT NOT NULL CHECK (char_length(trim(reason)) > 0)
);

REVOKE ALL ON TABLE private.h2_legacy_public_course_cohort FROM PUBLIC, anon, authenticated, service_role;

INSERT INTO private.h2_legacy_public_course_cohort (course_id, reason)
SELECT c.id, 'preserve pre-H2 public catalog visibility during editorial transition'
FROM public.courses c
WHERE c.is_active = true
  AND c.is_verified = true
  AND EXISTS (
      SELECT 1
      FROM public.institution_site_profiles p
      WHERE p.institution_id = c.institution_id
        AND p.production_enabled = true
  )
ON CONFLICT (course_id) DO NOTHING;

DROP VIEW IF EXISTS public.courses_public_effective;
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
SET search_path = public, private, pg_temp
AS $$
    WITH eligible_courses AS (
        SELECT
            c.*,
            es.manual_overrides,
            es.manual_start_date,
            (
                es.editorial_status = 'published'
                AND es.quality_status = 'complete'
                AND es.availability_status = 'available'
            ) AS is_strict_h2_public,
            EXISTS (
                SELECT 1
                FROM private.h2_legacy_public_course_cohort cohort
                WHERE cohort.course_id = c.id
            ) AS is_legacy_public
        FROM public.courses c
        LEFT JOIN public.course_editorial_state es ON es.course_id = c.id
        WHERE c.is_active = true
          AND c.is_verified = true
          AND EXISTS (
              SELECT 1
              FROM public.institution_site_profiles p
              WHERE p.institution_id = c.institution_id
                AND p.production_enabled = true
          )
    )
    SELECT
        c.id,
        c.institution_id,
        c.category_id,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'name', c.name) ELSE c.name END AS name,
        c.slug,
        c.url,
        CASE
            WHEN c.is_strict_h2_public AND c.manual_overrides ->> 'price_pen' ~ '^[0-9]+(\.[0-9]+)?$'
                THEN (c.manual_overrides ->> 'price_pen')::NUMERIC
            ELSE c.price_pen
        END AS price_pen,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'price_status', c.price_status, 'A consultar') ELSE COALESCE(c.price_status, 'A consultar') END AS price_status,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'mode', c.mode) ELSE c.mode END AS mode,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'duration', c.duration) ELSE c.duration END AS duration,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'description_long', c.description_long) ELSE c.description_long END AS description_long,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'syllabus', c.syllabus) ELSE c.syllabus END AS syllabus,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'target_audience', c.target_audience) ELSE c.target_audience END AS target_audience,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'requirements', c.requirements) ELSE c.requirements END AS requirements,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'certification', c.certification) ELSE c.certification END AS certification,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'benefits', c.benefits) ELSE c.benefits END AS benefits,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'objectives', c.objectives) ELSE c.objectives END AS objectives,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_start_date, c.start_date) ELSE c.start_date END AS start_date,
        CASE WHEN c.is_strict_h2_public THEN COALESCE(c.manual_overrides ->> 'start_date_text', c.start_date_text, 'Sin confirmar') ELSE COALESCE(c.start_date_text, 'Sin confirmar') END AS start_date_text,
        c.course_type,
        c.brochure_url,
        c.expected_monthly_salary,
        c.seniority_level,
        c.roi_months,
        c.view_count,
        c.comparison_count,
        c.created_at,
        c.updated_at
    FROM eligible_courses c
    WHERE c.is_strict_h2_public = true
       OR c.is_legacy_public = true;
$$;

REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS
SELECT * FROM private.h2_public_courses_effective();

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

COMMENT ON TABLE private.h2_legacy_public_course_cohort IS
    'H2 private compatibility cohort. Freezes courses that satisfied the pre-H2 public visibility contract so development web remains functional during editorial transition.';
COMMENT ON FUNCTION private.h2_public_courses_effective() IS
    'H2 bounded public reader. Returns strict H2 public courses plus the private legacy compatibility cohort, with only public fields.';
COMMENT ON VIEW public.courses_public_effective IS
    'H2 public effective course view with compatibility cohort. Direct public reads still use this view, not courses.';
