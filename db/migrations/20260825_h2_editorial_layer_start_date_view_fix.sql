-- H2: remove unsafe DATE cast from the public effective view.
-- Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE.
-- This migration performs no DML/backfill.

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS
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
    COALESCE(es.manual_overrides ->> 'price_status', c.price_status) AS price_status,
    COALESCE(es.manual_overrides ->> 'mode', c.mode) AS mode,
    COALESCE(es.manual_overrides ->> 'duration', c.duration) AS duration,
    COALESCE(es.manual_overrides ->> 'description_long', c.description_long) AS description_long,
    COALESCE(es.manual_overrides ->> 'syllabus', c.syllabus) AS syllabus,
    COALESCE(es.manual_overrides ->> 'target_audience', c.target_audience) AS target_audience,
    COALESCE(es.manual_overrides ->> 'requirements', c.requirements) AS requirements,
    COALESCE(es.manual_overrides ->> 'certification', c.certification) AS certification,
    COALESCE(es.manual_overrides ->> 'benefits', c.benefits) AS benefits,
    COALESCE(es.manual_overrides ->> 'objectives', c.objectives) AS objectives,
    c.start_date,
    COALESCE(es.manual_overrides ->> 'start_date_text', c.start_date_text) AS start_date_text,
    c.course_type,
    c.brochure_url,
    c.expected_monthly_salary,
    c.seniority_level,
    c.roi_months,
    c.provider_used,
    c.is_mock_data,
    c.view_count,
    c.comparison_count,
    es.editorial_status,
    es.quality_status,
    es.missing_fields,
    es.field_sources,
    es.is_sponsored,
    es.lead_cta_enabled,
    c.created_at,
    c.updated_at,
    es.updated_at AS editorial_updated_at
FROM public.courses c
JOIN public.course_editorial_state es ON es.course_id = c.id
WHERE c.is_active = true
  AND c.is_verified = true
  AND es.editorial_status = 'published'
  AND es.quality_status = 'complete'
  AND EXISTS (
      SELECT 1
      FROM public.institution_site_profiles p
      WHERE p.institution_id = c.institution_id
        AND p.production_enabled = true
  );

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

COMMENT ON VIEW public.courses_public_effective IS
    'H2 public effective course view. Applies published+complete editorial gate and manual override precedence; start_date stays pipeline-owned until validated override support exists.';
