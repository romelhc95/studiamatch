-- H2: remove private editorial fields from the public effective course surface.
-- Scope: Free DDL remediation only. Remote apply requires explicit JIT DDL approval.
-- No DML, seed, backfill, Pro, writers, schedules, canaries, deploys, push, PR, or merge.

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
SET search_path = public, pg_temp
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
    WHERE c.is_active = true
      AND c.is_verified = true
      AND es.editorial_status = 'published'
      AND es.quality_status = 'complete'
      AND es.availability_status = 'available'
      AND EXISTS (
          SELECT 1
          FROM public.institution_site_profiles p
          WHERE p.institution_id = c.institution_id
            AND p.production_enabled = true
      );
$$;

REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS
SELECT * FROM private.h2_public_courses_effective();

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

COMMENT ON FUNCTION private.h2_public_courses_effective() IS
    'H2 bounded public effective reader. Returns only public course fields; private editorial gates remain internal.';
COMMENT ON VIEW public.courses_public_effective IS
    'H2 public effective course view with security_invoker=true over a bounded private reader; private editorial fields are not exposed.';
