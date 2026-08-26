-- H2: forward-only remediation for Supabase Security Advisor findings.
-- Scope: Free DDL remediation only. Remote apply requires explicit JIT approval.
-- No DML, seed, backfill, Pro, writers, schedules, canaries, deploys, push, PR, or merge.

CREATE SCHEMA IF NOT EXISTS private;

REVOKE ALL ON SCHEMA private FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA private TO anon, authenticated, service_role;

ALTER TABLE public.course_editorial_audit
    ADD COLUMN IF NOT EXISTS request_payload_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_course_editorial_state_public_gate_h2
    ON public.course_editorial_state (
        editorial_status,
        quality_status,
        availability_status,
        course_id
    );

CREATE INDEX IF NOT EXISTS idx_course_editorial_state_sponsored_priority_h2
    ON public.course_editorial_state (
        is_sponsored DESC,
        sponsored_priority DESC,
        updated_at DESC
    )
    WHERE editorial_status = 'published'
      AND quality_status = 'complete'
      AND availability_status = 'available';

CREATE OR REPLACE FUNCTION public.prevent_course_editorial_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION 'course_editorial_audit is append-only';
END;
$$;

CREATE OR REPLACE FUNCTION private.h2_required_missing_fields(
    p_course public.courses,
    p_manual_overrides JSONB
)
RETURNS TEXT[]
LANGUAGE sql
STABLE
SET search_path = public, pg_temp
AS $$
    SELECT ARRAY(
        SELECT field_name
        FROM (
            VALUES
                ('name', COALESCE(p_manual_overrides ->> 'name', (p_course).name)),
                ('institution', (p_course).institution_id::TEXT),
                ('url', (p_course).url),
                ('slug', (p_course).slug),
                ('category', COALESCE(p_manual_overrides ->> 'category', (p_course).category, (p_course).category_id::TEXT)),
                ('mode', COALESCE(p_manual_overrides ->> 'mode', (p_course).mode)),
                ('duration', COALESCE(p_manual_overrides ->> 'duration', (p_course).duration))
        ) AS required(field_name, field_value)
        WHERE field_value IS NULL
           OR btrim(field_value) = ''
           OR lower(btrim(field_value)) IN ('none', 'null', 'nan', 'consultar', 'a consultar', 'sin confirmar')
        ORDER BY array_position(ARRAY['name','institution','url','slug','category','mode','duration'], field_name)
    );
$$;

CREATE OR REPLACE FUNCTION private.h2_update_course_quality_impl(
    p_course_id UUID,
    p_missing_fields TEXT[],
    p_field_sources JSONB,
    p_field_timestamps JSONB,
    p_request_id TEXT DEFAULT NULL,
    p_payload_hash TEXT DEFAULT NULL
)
RETURNS public.course_editorial_state
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, private, pg_temp
AS $$
DECLARE
    previous_state JSONB;
    updated_state public.course_editorial_state;
    current_state public.course_editorial_state;
    course_row public.courses;
    expected_missing TEXT[];
    existing_hash TEXT;
BEGIN
    IF p_course_id IS NULL THEN
        RAISE EXCEPTION 'p_course_id is required';
    END IF;
    IF p_request_id IS NULL OR btrim(p_request_id) = '' THEN
        RAISE EXCEPTION 'p_request_id is required';
    END IF;
    IF p_payload_hash IS NULL OR btrim(p_payload_hash) = '' THEN
        RAISE EXCEPTION 'p_payload_hash is required';
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

    PERFORM pg_advisory_xact_lock(hashtextextended(p_request_id, 0));

    SELECT audit.request_payload_hash
      INTO existing_hash
      FROM public.course_editorial_audit audit
     WHERE audit.request_id = p_request_id
     LIMIT 1;

    IF existing_hash IS NOT NULL THEN
        IF existing_hash <> p_payload_hash THEN
            RAISE EXCEPTION 'request_id already exists for a different payload';
        END IF;

        SELECT * INTO updated_state
          FROM public.course_editorial_state es
         WHERE es.course_id = p_course_id;

        IF updated_state.course_id IS NULL THEN
            RAISE EXCEPTION 'request_id already exists but course state is missing';
        END IF;

        RETURN updated_state;
    END IF;

    SELECT * INTO course_row
      FROM public.courses c
     WHERE c.id = p_course_id;

    IF course_row.id IS NULL THEN
        RAISE EXCEPTION 'course not found';
    END IF;

    SELECT * INTO current_state
      FROM public.course_editorial_state es
     WHERE es.course_id = p_course_id
     FOR UPDATE;

    expected_missing := private.h2_required_missing_fields(
        course_row,
        COALESCE(current_state.manual_overrides, '{}'::jsonb)
    );

    IF expected_missing <> p_missing_fields THEN
        RAISE EXCEPTION 'p_missing_fields does not match server-side quality contract';
    END IF;

    previous_state := to_jsonb(current_state);

    INSERT INTO public.course_editorial_state (
        course_id,
        quality_status,
        missing_fields,
        field_sources,
        field_timestamps,
        updated_at
    ) VALUES (
        p_course_id,
        CASE WHEN cardinality(expected_missing) = 0 THEN 'complete' ELSE 'pending' END,
        expected_missing,
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
        request_id,
        request_payload_hash
    ) VALUES (
        p_course_id,
        'quality_recomputed',
        previous_state,
        to_jsonb(updated_state),
        'h2_update_course_quality',
        p_request_id,
        p_payload_hash
    );

    RETURN updated_state;
END;
$$;

CREATE OR REPLACE FUNCTION public.h2_update_course_quality(
    p_course_id UUID,
    p_missing_fields TEXT[],
    p_field_sources JSONB,
    p_field_timestamps JSONB,
    p_request_id TEXT DEFAULT NULL,
    p_payload_hash TEXT DEFAULT NULL
)
RETURNS public.course_editorial_state
LANGUAGE sql
SET search_path = public, private, pg_temp
AS $$
    SELECT private.h2_update_course_quality_impl(
        p_course_id,
        p_missing_fields,
        p_field_sources,
        p_field_timestamps,
        p_request_id,
        p_payload_hash
    );
$$;

CREATE OR REPLACE FUNCTION private.h2_update_course_quality_batch_impl(p_items JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, private, pg_temp
AS $$
DECLARE
    item JSONB;
    processed INTEGER := 0;
BEGIN
    IF p_items IS NULL OR jsonb_typeof(p_items) <> 'array' THEN
        RAISE EXCEPTION 'p_items must be a JSON array';
    END IF;
    IF jsonb_array_length(p_items) > 1000 THEN
        RAISE EXCEPTION 'p_items exceeds max batch size 1000';
    END IF;

    FOR item IN SELECT value FROM jsonb_array_elements(p_items)
    LOOP
        PERFORM private.h2_update_course_quality_impl(
            (item ->> 'course_id')::UUID,
            ARRAY(SELECT jsonb_array_elements_text(item -> 'missing_fields')),
            item -> 'field_sources',
            item -> 'field_timestamps',
            item ->> 'request_id',
            item ->> 'payload_hash'
        );
        processed := processed + 1;
    END LOOP;

    RETURN jsonb_build_object('processed', processed);
END;
$$;

CREATE OR REPLACE FUNCTION public.h2_update_course_quality_batch(p_items JSONB)
RETURNS JSONB
LANGUAGE sql
SET search_path = public, private, pg_temp
AS $$
    SELECT private.h2_update_course_quality_batch_impl(p_items);
$$;

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

DROP POLICY IF EXISTS courses_h2_public_effective_select ON public.courses;
DROP POLICY IF EXISTS courses_exclude_release_canary ON public.courses;
DROP POLICY IF EXISTS "Public read for courses" ON public.courses;
DROP POLICY IF EXISTS courses_select_public ON public.courses;
DROP POLICY IF EXISTS courses_select_authenticated ON public.courses;

DROP POLICY IF EXISTS course_editorial_state_public_effective_select
    ON public.course_editorial_state;

REVOKE ALL ON TABLE public.courses FROM anon, authenticated;
REVOKE ALL ON TABLE public.course_editorial_state FROM anon, authenticated;
REVOKE ALL ON TABLE public.leads FROM anon, authenticated;
REVOKE ALL ON FUNCTION public.increment_view_count(UUID) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.h2_update_course_quality_batch(JSONB) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.prevent_course_editorial_audit_mutation() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.h2_required_missing_fields(public.courses, JSONB) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.h2_update_course_quality_impl(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION private.h2_update_course_quality_batch_impl(JSONB) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;

REVOKE ALL ON TABLE public.course_editorial_state FROM service_role;
REVOKE ALL ON TABLE public.course_editorial_audit FROM service_role;

GRANT SELECT ON TABLE public.course_editorial_state TO service_role;
GRANT SELECT ON TABLE public.course_editorial_audit TO service_role;
GRANT EXECUTE ON FUNCTION private.h2_update_course_quality_impl(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION private.h2_update_course_quality_batch_impl(JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.h2_update_course_quality_batch(JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;

DROP VIEW IF EXISTS public.courses_public_effective;

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS
SELECT * FROM private.h2_public_courses_effective();

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

COMMENT ON FUNCTION public.prevent_course_editorial_audit_mutation() IS
    'H2 append-only audit guard. Uses fixed search_path for Security Advisor compliance.';
COMMENT ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) IS
    'H2 bounded quality recomputation RPC wrapper. Invoker function delegates to private implementation and never publishes courses.';
COMMENT ON FUNCTION public.h2_update_course_quality_batch(JSONB) IS
    'H2 bounded batch quality recomputation RPC wrapper. Max 1000 operations per batch and never publishes courses.';
COMMENT ON FUNCTION private.h2_update_course_quality_impl(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) IS
    'H2 private quality recomputation implementation. Uses advisory-lock idempotency and validates missing fields server-side.';
COMMENT ON FUNCTION private.h2_update_course_quality_batch_impl(JSONB) IS
    'H2 private batch quality recomputation implementation for scalable backfills.';
COMMENT ON FUNCTION private.h2_public_courses_effective() IS
    'H2 bounded public effective reader. Security definer is kept in a non-exposed private schema and returns only gated effective rows.';
COMMENT ON VIEW public.courses_public_effective IS
    'H2 public effective course view with security_invoker=true over a bounded private reader; base tables remain inaccessible to public roles.';
