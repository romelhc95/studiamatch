-- H2 Pro expand: additive editorial schema and compatibility reader.
-- Scope: Production DDL only after explicit JIT, backup/PITR and manifest approval.
-- This migration must not revoke legacy public reads from public.courses.

CREATE SCHEMA IF NOT EXISTS private;

REVOKE ALL ON SCHEMA private FROM PUBLIC;
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA private FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA private TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA private REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;

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
    field_timestamps JSONB NOT NULL DEFAULT '{}'::jsonb,
    editorial_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_sponsored BOOLEAN NOT NULL DEFAULT false,
    sponsored_priority INTEGER NOT NULL DEFAULT 0,
    sponsorship_label TEXT,
    lead_cta_enabled BOOLEAN NOT NULL DEFAULT false,
    availability_status TEXT NOT NULL DEFAULT 'unknown',
    manual_start_date DATE,
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
    CONSTRAINT course_editorial_state_field_timestamps_object
        CHECK (jsonb_typeof(field_timestamps) = 'object'),
    CONSTRAINT course_editorial_state_editorial_metadata_object
        CHECK (jsonb_typeof(editorial_metadata) = 'object'),
    CONSTRAINT course_editorial_state_sponsored_priority_nonnegative
        CHECK (sponsored_priority >= 0),
    CONSTRAINT course_editorial_state_availability_status_valid
        CHECK (availability_status IN ('available', 'unavailable', 'unknown')),
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
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE RESTRICT,
    actor_user_id UUID,
    action TEXT NOT NULL CHECK (char_length(trim(action)) > 0),
    old_values JSONB,
    new_values JSONB,
    reason TEXT,
    request_id TEXT,
    request_payload_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT course_editorial_audit_old_values_object
        CHECK (old_values IS NULL OR jsonb_typeof(old_values) = 'object'),
    CONSTRAINT course_editorial_audit_new_values_object
        CHECK (new_values IS NULL OR jsonb_typeof(new_values) = 'object')
);

CREATE TABLE IF NOT EXISTS private.h2_legacy_public_course_cohort (
    course_id UUID PRIMARY KEY REFERENCES public.courses(id) ON DELETE RESTRICT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    contract_version TEXT NOT NULL DEFAULT 'h2-pro-legacy-public-compat-v1',
    reason TEXT NOT NULL CHECK (char_length(trim(reason)) > 0),
    snapshot_expected_count INTEGER,
    snapshot_ids_sha256 TEXT,
    payload_sha TEXT,
    authorization_id TEXT
);

REVOKE ALL ON TABLE private.h2_legacy_public_course_cohort FROM PUBLIC, anon, authenticated, service_role;

CREATE INDEX IF NOT EXISTS idx_editorial_field_definitions_public
    ON public.editorial_field_definitions (is_public, ownership);
CREATE INDEX IF NOT EXISTS idx_course_editorial_state_status
    ON public.course_editorial_state (editorial_status, quality_status);
CREATE INDEX IF NOT EXISTS idx_course_editorial_state_public_gate_h2
    ON public.course_editorial_state (editorial_status, quality_status, availability_status, course_id);
CREATE INDEX IF NOT EXISTS idx_course_editorial_state_sponsored_priority_h2
    ON public.course_editorial_state (is_sponsored DESC, sponsored_priority DESC, updated_at DESC)
    WHERE editorial_status = 'published'
      AND quality_status = 'complete'
      AND availability_status = 'available';
CREATE INDEX IF NOT EXISTS idx_course_editorial_audit_course_created
    ON public.course_editorial_audit (course_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_course_editorial_audit_request_id
    ON public.course_editorial_audit (request_id)
    WHERE request_id IS NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.courses
        WHERE institution_id IS NOT NULL
          AND slug IS NOT NULL
        GROUP BY institution_id, slug
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'duplicate course institution_id+slug pairs block idx_courses_institution_slug_h2';
    END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_institution_slug_h2
    ON public.courses (institution_id, slug)
    WHERE institution_id IS NOT NULL
      AND slug IS NOT NULL;

ALTER TABLE public.editorial_field_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_editorial_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_editorial_audit ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.editorial_field_definitions FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.course_editorial_state FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.course_editorial_audit FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.editorial_field_definitions TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.editorial_field_definitions TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.course_editorial_state TO service_role;
GRANT SELECT, INSERT ON TABLE public.course_editorial_audit TO service_role;

DROP POLICY IF EXISTS editorial_field_definitions_public_select ON public.editorial_field_definitions;
CREATE POLICY editorial_field_definitions_public_select
    ON public.editorial_field_definitions
    FOR SELECT
    TO anon, authenticated
    USING (is_public = true);

DROP POLICY IF EXISTS editorial_field_definitions_service_all ON public.editorial_field_definitions;
CREATE POLICY editorial_field_definitions_service_all
    ON public.editorial_field_definitions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS course_editorial_state_service_all ON public.course_editorial_state;
CREATE POLICY course_editorial_state_service_all
    ON public.course_editorial_state
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS course_editorial_audit_service_select ON public.course_editorial_audit;
CREATE POLICY course_editorial_audit_service_select
    ON public.course_editorial_audit
    FOR SELECT
    TO service_role
    USING (true);

DROP POLICY IF EXISTS course_editorial_audit_service_insert ON public.course_editorial_audit;
CREATE POLICY course_editorial_audit_service_insert
    ON public.course_editorial_audit
    FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE OR REPLACE FUNCTION public.prevent_course_editorial_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION 'course_editorial_audit is append-only';
END;
$$;

DROP TRIGGER IF EXISTS prevent_course_editorial_audit_update ON public.course_editorial_audit;
CREATE TRIGGER prevent_course_editorial_audit_update
    BEFORE UPDATE ON public.course_editorial_audit
    FOR EACH ROW EXECUTE FUNCTION public.prevent_course_editorial_audit_mutation();

DROP TRIGGER IF EXISTS prevent_course_editorial_audit_delete ON public.course_editorial_audit;
CREATE TRIGGER prevent_course_editorial_audit_delete
    BEFORE DELETE ON public.course_editorial_audit
    FOR EACH ROW EXECUTE FUNCTION public.prevent_course_editorial_audit_mutation();

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
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    previous_state JSONB;
    updated_state public.course_editorial_state;
    current_state public.course_editorial_state;
    course_row public.courses;
    expected_missing TEXT[];
    existing_hash TEXT;
    existing_course_id UUID;
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

    SELECT audit.request_payload_hash, audit.course_id
      INTO existing_hash, existing_course_id
      FROM public.course_editorial_audit audit
     WHERE audit.request_id = p_request_id
     LIMIT 1;

    IF existing_hash IS NOT NULL THEN
        IF existing_hash <> p_payload_hash THEN
            RAISE EXCEPTION 'request_id already exists for a different payload';
        END IF;
        IF existing_course_id <> p_course_id THEN
            RAISE EXCEPTION 'request_id already exists for a different course';
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

    expected_missing := private.h2_required_missing_fields(course_row, COALESCE(current_state.manual_overrides, '{}'::jsonb));

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
SET search_path = pg_catalog, pg_temp
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
SET search_path = pg_catalog, pg_temp
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
SET search_path = pg_catalog, pg_temp
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
SET search_path = pg_catalog, pg_temp
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
                AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
          )
          AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%')
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

REVOKE ALL ON FUNCTION public.prevent_course_editorial_audit_mutation() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.h2_required_missing_fields(public.courses, JSONB) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.h2_update_course_quality_impl(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION private.h2_update_course_quality_batch_impl(JSONB) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.h2_update_course_quality_batch(JSONB) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_update_course_quality_impl(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION private.h2_update_course_quality_batch_impl(JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION public.h2_update_course_quality(UUID, TEXT[], JSONB, JSONB, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.h2_update_course_quality_batch(JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS
SELECT * FROM private.h2_public_courses_effective();

REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION private.h2_verify_expand_compat_impl(
    p_expected_count INTEGER,
    p_expected_cohort_digest TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    eligible_count INTEGER;
    cohort_count INTEGER;
    effective_count INTEGER;
    missing_count INTEGER;
    unexpected_count INTEGER;
    cohort_digest TEXT;
    public_column_count INTEGER;
    private_column_count INTEGER;
    view_is_security_invoker BOOLEAN;
    rls_tables_count INTEGER;
    direct_courses_public BOOLEAN;
BEGIN
    IF p_expected_count IS NULL OR p_expected_count <= 0 THEN
        RAISE EXCEPTION 'p_expected_count must be positive';
    END IF;
    IF p_expected_cohort_digest IS NULL OR p_expected_cohort_digest !~ '^sha256:[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'p_expected_cohort_digest must use sha256:<64 hex chars>';
    END IF;

    WITH eligible AS (
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
    )
    SELECT count(*) INTO eligible_count FROM eligible;

    SELECT count(*) INTO cohort_count FROM private.h2_legacy_public_course_cohort;
    SELECT count(*) INTO effective_count FROM public.courses_public_effective;

    WITH eligible AS (
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
    )
    SELECT count(*) INTO missing_count
    FROM eligible e
    WHERE NOT EXISTS (
        SELECT 1 FROM private.h2_legacy_public_course_cohort cohort WHERE cohort.course_id = e.id
    );

    WITH eligible AS (
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
    )
    SELECT count(*) INTO unexpected_count
    FROM private.h2_legacy_public_course_cohort cohort
    WHERE NOT EXISTS (SELECT 1 FROM eligible e WHERE e.id = cohort.course_id);

    SELECT 'sha256:' || encode(sha256(convert_to(string_agg(course_id::TEXT, ',' ORDER BY course_id::TEXT), 'UTF8')), 'hex')
      INTO cohort_digest
      FROM private.h2_legacy_public_course_cohort;

    SELECT count(*) INTO public_column_count
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'courses_public_effective';

    SELECT count(*) INTO private_column_count
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'courses_public_effective'
       AND column_name IN (
           'editorial_status', 'quality_status', 'missing_fields', 'field_sources',
           'field_timestamps', 'manual_overrides', 'manual_start_date', 'is_sponsored',
           'sponsored_priority', 'sponsorship_label', 'lead_cta_enabled',
           'availability_status', 'published_at', 'archived_at', 'manual_updated_at',
           'manual_updated_by', 'editorial_updated_at'
       );

    SELECT COALESCE('security_invoker=true' = ANY(c.reloptions), false)
      INTO view_is_security_invoker
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relname = 'courses_public_effective';

    SELECT count(*) INTO rls_tables_count
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relname IN ('editorial_field_definitions', 'course_editorial_state', 'course_editorial_audit')
       AND c.relrowsecurity IS TRUE;

    SELECT has_table_privilege('anon', 'public.courses', 'SELECT')
       AND has_table_privilege('authenticated', 'public.courses', 'SELECT')
      INTO direct_courses_public;

    IF eligible_count <> p_expected_count THEN
        RAISE EXCEPTION 'eligible_count mismatch: expected %, got %', p_expected_count, eligible_count;
    END IF;
    IF cohort_count <> p_expected_count OR effective_count <> p_expected_count THEN
        RAISE EXCEPTION 'H2 count mismatch: expected %, cohort %, effective %', p_expected_count, cohort_count, effective_count;
    END IF;
    IF missing_count <> 0 OR unexpected_count <> 0 THEN
        RAISE EXCEPTION 'H2 cohort identity mismatch: missing %, unexpected %', missing_count, unexpected_count;
    END IF;
    IF cohort_digest <> p_expected_cohort_digest THEN
        RAISE EXCEPTION 'H2 cohort digest mismatch: expected %, got %', p_expected_cohort_digest, cohort_digest;
    END IF;
    IF public_column_count <> 28 OR private_column_count <> 0 OR view_is_security_invoker IS NOT TRUE THEN
        RAISE EXCEPTION 'H2 public view contract mismatch: columns %, private %, security_invoker %', public_column_count, private_column_count, view_is_security_invoker;
    END IF;
    IF rls_tables_count <> 3 THEN
        RAISE EXCEPTION 'H2 RLS contract mismatch: %/3 tables have RLS', rls_tables_count;
    END IF;
    IF direct_courses_public IS NOT TRUE THEN
        RAISE EXCEPTION 'H2 expand must preserve direct public courses reads until contract';
    END IF;

    RETURN jsonb_build_object(
        'eligible_count', eligible_count,
        'cohort_count', cohort_count,
        'effective_count', effective_count,
        'missing_count', missing_count,
        'unexpected_count', unexpected_count,
        'cohort_digest', cohort_digest,
        'public_column_count', public_column_count,
        'private_column_count', private_column_count,
        'security_invoker', view_is_security_invoker,
        'rls_tables_count', rls_tables_count,
        'direct_courses_public', direct_courses_public
    );
END;
$$;

CREATE OR REPLACE FUNCTION public.h2_verify_expand_compat(
    p_expected_count INTEGER,
    p_expected_cohort_digest TEXT
)
RETURNS JSONB
LANGUAGE sql
STABLE
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT private.h2_verify_expand_compat_impl(p_expected_count, p_expected_cohort_digest);
$$;

REVOKE ALL ON FUNCTION private.h2_verify_expand_compat_impl(INTEGER, TEXT) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.h2_verify_expand_compat(INTEGER, TEXT) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_verify_expand_compat_impl(INTEGER, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.h2_verify_expand_compat(INTEGER, TEXT) TO service_role;

COMMENT ON TABLE private.h2_legacy_public_course_cohort IS
    'H2 Pro private compatibility cohort. Populated by a separate DML migration before the frontend cutover.';
COMMENT ON FUNCTION private.h2_public_courses_effective() IS
    'H2 Pro compatibility reader. Returns strict H2 public courses plus frozen legacy cohort rows, exposing only public fields.';
COMMENT ON VIEW public.courses_public_effective IS
    'H2 Pro public effective course view with security_invoker=true over a bounded private reader. Created during expand while legacy public courses reads remain available until contract.';
