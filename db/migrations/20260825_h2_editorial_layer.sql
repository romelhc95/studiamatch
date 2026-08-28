-- H2: Editorial layer for course publication and quality state.
-- Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE.
-- No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

CREATE TABLE IF NOT EXISTS public.editorial_field_definitions (
    field_key TEXT PRIMARY KEY,
    target_column TEXT NOT NULL,
    ownership TEXT NOT NULL CHECK (
        ownership IN (
            'pipeline_owned',
            'manual_owned',
            'computed',
            'hybrid_manual_preferred'
        )
    ),
    is_required_for_publish BOOLEAN NOT NULL DEFAULT false,
    is_public BOOLEAN NOT NULL DEFAULT true,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.course_editorial_state (
    course_id UUID PRIMARY KEY REFERENCES public.courses(id) ON DELETE CASCADE,
    editorial_status TEXT NOT NULL DEFAULT 'pending_review' CHECK (
        editorial_status IN ('draft', 'pending_review', 'published', 'archived')
    ),
    quality_status TEXT NOT NULL DEFAULT 'pending' CHECK (
        quality_status IN ('pending', 'complete', 'blocked')
    ),
    manual_overrides JSONB NOT NULL DEFAULT '{}'::jsonb,
    missing_fields TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    field_sources JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_sponsored BOOLEAN NOT NULL DEFAULT false,
    lead_cta_enabled BOOLEAN NOT NULL DEFAULT false,
    manual_updated_at TIMESTAMPTZ,
    manual_updated_by UUID,
    published_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT course_editorial_state_manual_overrides_object
        CHECK (jsonb_typeof(manual_overrides) = 'object'),
    CONSTRAINT course_editorial_state_field_sources_object
        CHECK (jsonb_typeof(field_sources) = 'object'),
    CONSTRAINT course_editorial_state_manual_overrides_public_allowlist
        CHECK (
            manual_overrides
            - 'name'
            - 'price_pen'
            - 'price_status'
            - 'mode'
            - 'duration'
            - 'description_long'
            - 'syllabus'
            - 'target_audience'
            - 'requirements'
            - 'certification'
            - 'benefits'
            - 'objectives'
            - 'start_date_text'
            = '{}'::jsonb
        ),
    CONSTRAINT course_editorial_state_published_has_manual_actor
        CHECK (editorial_status <> 'published' OR manual_updated_by IS NOT NULL),
    CONSTRAINT course_editorial_state_published_at_required
        CHECK (editorial_status <> 'published' OR published_at IS NOT NULL),
    CONSTRAINT course_editorial_state_archived_at_required
        CHECK (editorial_status <> 'archived' OR archived_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS public.course_editorial_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    actor_user_id UUID,
    action TEXT NOT NULL CHECK (char_length(trim(action)) > 0),
    old_values JSONB,
    new_values JSONB,
    reason TEXT,
    request_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT course_editorial_audit_old_values_object
        CHECK (old_values IS NULL OR jsonb_typeof(old_values) = 'object'),
    CONSTRAINT course_editorial_audit_new_values_object
        CHECK (new_values IS NULL OR jsonb_typeof(new_values) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_editorial_field_definitions_public
    ON public.editorial_field_definitions (is_public, ownership);

CREATE INDEX IF NOT EXISTS idx_course_editorial_state_status
    ON public.course_editorial_state (editorial_status, quality_status);

CREATE INDEX IF NOT EXISTS idx_course_editorial_state_sponsored
    ON public.course_editorial_state (is_sponsored, editorial_status, quality_status);

CREATE INDEX IF NOT EXISTS idx_course_editorial_audit_course_created
    ON public.course_editorial_audit (course_id, created_at DESC);

ALTER TABLE public.editorial_field_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_editorial_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_editorial_audit ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.editorial_field_definitions FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.course_editorial_state FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.course_editorial_audit FROM PUBLIC, anon, authenticated;

GRANT SELECT ON TABLE public.editorial_field_definitions TO anon, authenticated;
GRANT SELECT (
    course_id,
    editorial_status,
    quality_status,
    manual_overrides,
    missing_fields,
    field_sources,
    is_sponsored,
    lead_cta_enabled,
    updated_at
) ON TABLE public.course_editorial_state TO anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.editorial_field_definitions TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.course_editorial_state TO service_role;
GRANT SELECT, INSERT ON TABLE public.course_editorial_audit TO service_role;

DROP POLICY IF EXISTS editorial_field_definitions_public_select
    ON public.editorial_field_definitions;
CREATE POLICY editorial_field_definitions_public_select
    ON public.editorial_field_definitions
    FOR SELECT
    TO anon, authenticated
    USING (is_public = true);

DROP POLICY IF EXISTS editorial_field_definitions_service_all
    ON public.editorial_field_definitions;
CREATE POLICY editorial_field_definitions_service_all
    ON public.editorial_field_definitions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS course_editorial_state_public_effective_select
    ON public.course_editorial_state;
CREATE POLICY course_editorial_state_public_effective_select
    ON public.course_editorial_state
    FOR SELECT
    TO anon, authenticated
    USING (
        editorial_status = 'published'
        AND quality_status = 'complete'
        AND EXISTS (
            SELECT 1
            FROM public.courses c
            WHERE c.id = course_editorial_state.course_id
              AND c.is_active = true
              AND c.is_verified = true
              AND EXISTS (
                  SELECT 1
                  FROM public.institution_site_profiles p
                  WHERE p.institution_id = c.institution_id
                    AND p.production_enabled = true
              )
        )
    );

DROP POLICY IF EXISTS course_editorial_state_service_all
    ON public.course_editorial_state;
CREATE POLICY course_editorial_state_service_all
    ON public.course_editorial_state
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS course_editorial_audit_service_select
    ON public.course_editorial_audit;
CREATE POLICY course_editorial_audit_service_select
    ON public.course_editorial_audit
    FOR SELECT
    TO service_role
    USING (true);

DROP POLICY IF EXISTS course_editorial_audit_service_insert
    ON public.course_editorial_audit;
CREATE POLICY course_editorial_audit_service_insert
    ON public.course_editorial_audit
    FOR INSERT
    TO service_role
    WITH CHECK (true);

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

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

COMMENT ON TABLE public.editorial_field_definitions IS
    'H2 dictionary for field ownership and editorial allowlist. Writes require controlled backend or migration context.';
COMMENT ON TABLE public.course_editorial_state IS
    'H2 editorial state for course publication, quality, public-safe overrides, sponsorship and CTA flags.';
COMMENT ON TABLE public.course_editorial_audit IS
    'H2 append-only editorial audit. No public access and no update/delete/truncate grants.';
COMMENT ON VIEW public.courses_public_effective IS
    'H2 public effective course view. Applies published+complete editorial gate and manual override precedence.';
