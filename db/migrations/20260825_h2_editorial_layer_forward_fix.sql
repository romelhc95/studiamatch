-- H2: forward-only hardening for the editorial layer.
-- Scope: local PR payload only. Remote apply requires a new JIT DDL approval.
-- No backfill, Pro apply, schedules, canaries, deploys, or mass publication here.

ALTER TABLE public.course_editorial_state
    ADD COLUMN IF NOT EXISTS manual_start_date DATE,
    ADD COLUMN IF NOT EXISTS sponsored_priority INTEGER NOT NULL DEFAULT 0 CHECK (sponsored_priority >= 0),
    ADD COLUMN IF NOT EXISTS sponsorship_label TEXT,
    ADD COLUMN IF NOT EXISTS availability_status TEXT NOT NULL DEFAULT 'unknown' CHECK (
        availability_status IN ('available', 'unavailable', 'unknown')
    ),
    ADD COLUMN IF NOT EXISTS field_timestamps JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS editorial_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD CONSTRAINT course_editorial_state_field_timestamps_object
        CHECK (jsonb_typeof(field_timestamps) = 'object'),
    ADD CONSTRAINT course_editorial_state_editorial_metadata_object
        CHECK (jsonb_typeof(editorial_metadata) = 'object');

ALTER TABLE public.course_editorial_audit
    DROP CONSTRAINT IF EXISTS course_editorial_audit_course_id_fkey;

ALTER TABLE public.course_editorial_audit
    ADD CONSTRAINT course_editorial_audit_course_id_fkey
        FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_course_editorial_audit_request_id
    ON public.course_editorial_audit (request_id)
    WHERE request_id IS NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.courses
        WHERE slug IS NOT NULL
        GROUP BY slug
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'duplicate course slugs block idx_courses_slug_global_h2';
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_slug_global_h2
    ON public.courses (slug)
    WHERE slug IS NOT NULL;

CREATE OR REPLACE FUNCTION public.prevent_course_editorial_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'course_editorial_audit is append-only';
END;
$$;

DROP TRIGGER IF EXISTS prevent_course_editorial_audit_update
    ON public.course_editorial_audit;
CREATE TRIGGER prevent_course_editorial_audit_update
    BEFORE UPDATE ON public.course_editorial_audit
    FOR EACH ROW EXECUTE FUNCTION public.prevent_course_editorial_audit_mutation();

DROP TRIGGER IF EXISTS prevent_course_editorial_audit_delete
    ON public.course_editorial_audit;
CREATE TRIGGER prevent_course_editorial_audit_delete
    BEFORE DELETE ON public.course_editorial_audit
    FOR EACH ROW EXECUTE FUNCTION public.prevent_course_editorial_audit_mutation();

CREATE OR REPLACE FUNCTION public.h2_update_course_quality(
    p_course_id UUID,
    p_missing_fields TEXT[],
    p_field_sources JSONB,
    p_field_timestamps JSONB,
    p_request_id TEXT DEFAULT NULL
)
RETURNS public.course_editorial_state
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
    previous_state JSONB;
    updated_state public.course_editorial_state;
BEGIN
    IF p_course_id IS NULL THEN
        RAISE EXCEPTION 'p_course_id is required';
    END IF;
    IF p_missing_fields IS NULL THEN
        RAISE EXCEPTION 'p_missing_fields is required';
    END IF;
    IF p_field_sources IS NULL OR jsonb_typeof(p_field_sources) <> 'object' THEN
        RAISE EXCEPTION 'p_field_sources must be a JSON object';
    END IF;
    IF p_field_timestamps IS NULL OR jsonb_typeof(p_field_timestamps) <> 'object' THEN
        RAISE EXCEPTION 'p_field_timestamps must be a JSON object';
    END IF;

    SELECT to_jsonb(es)
      INTO previous_state
      FROM public.course_editorial_state es
     WHERE es.course_id = p_course_id
     FOR UPDATE;

    INSERT INTO public.course_editorial_state (
        course_id,
        quality_status,
        missing_fields,
        field_sources,
        field_timestamps,
        updated_at
    ) VALUES (
        p_course_id,
        CASE WHEN cardinality(p_missing_fields) = 0 THEN 'complete' ELSE 'pending' END,
        p_missing_fields,
        p_field_sources,
        p_field_timestamps,
        now()
    )
    ON CONFLICT (course_id) DO UPDATE SET
        quality_status = EXCLUDED.quality_status,
        missing_fields = EXCLUDED.missing_fields,
        field_sources = EXCLUDED.field_sources,
        field_timestamps = EXCLUDED.field_timestamps,
        updated_at = now(),
        version = public.course_editorial_state.version + 1
    RETURNING * INTO updated_state;

    INSERT INTO public.course_editorial_audit (
        course_id,
        action,
        old_values,
        new_values,
        reason,
        request_id
    ) VALUES (
        p_course_id,
        'quality_recomputed',
        previous_state,
        to_jsonb(updated_state),
        'h2_update_course_quality',
        p_request_id
    )
    ON CONFLICT (request_id) WHERE request_id IS NOT NULL DO NOTHING;

    RETURN updated_state;
END;
$$;

REVOKE ALL ON FUNCTION public.prevent_course_editorial_audit_mutation() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT) TO service_role;

REVOKE INSERT ON TABLE public.leads FROM anon, authenticated;

REVOKE ALL ON TABLE public.course_editorial_state FROM anon, authenticated;
GRANT SELECT (
    course_id,
    editorial_status,
    quality_status,
    missing_fields,
    field_sources,
    field_timestamps,
    is_sponsored,
    lead_cta_enabled,
    manual_start_date,
    sponsored_priority,
    sponsorship_label,
    availability_status,
    updated_at
) ON TABLE public.course_editorial_state TO anon, authenticated;

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
    c.provider_used,
    c.is_mock_data,
    c.view_count,
    c.comparison_count,
    es.editorial_status,
    es.quality_status,
    es.missing_fields,
    es.field_sources,
    es.field_timestamps,
    es.is_sponsored,
    es.lead_cta_enabled,
    es.sponsored_priority,
    es.sponsorship_label,
    es.availability_status,
    c.created_at,
    c.updated_at,
    es.updated_at AS editorial_updated_at
FROM public.courses c
JOIN public.course_editorial_state es ON es.course_id = c.id
WHERE es.editorial_status = 'published'
  AND es.quality_status = 'complete'
  AND c.is_active = true
  AND c.is_verified = true
  AND EXISTS (
      SELECT 1
      FROM public.institution_site_profiles p
      WHERE p.institution_id = c.institution_id
        AND p.production_enabled = true
  );

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

COMMENT ON COLUMN public.courses.is_active IS
    'Deprecated as publication authority in H2. Technical pipeline availability only; public publication is gated by course_editorial_state.';
COMMENT ON COLUMN public.courses.is_verified IS
    'Deprecated as publication authority in H2. Technical verification only; public publication is gated by course_editorial_state.';
COMMENT ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT) IS
    'H2 bounded quality recomputation RPC. Updates quality fields only and never sets editorial_status to published.';
