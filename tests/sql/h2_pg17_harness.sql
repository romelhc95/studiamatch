\set ON_ERROR_STOP on

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN;

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

CREATE TABLE public.institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    website_url TEXT
);

CREATE TABLE public.institution_site_profiles (
    institution_id UUID PRIMARY KEY REFERENCES public.institutions(id) ON DELETE CASCADE,
    pipeline_ready BOOLEAN NOT NULL DEFAULT false,
    production_enabled BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL
);

CREATE TABLE public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES public.institutions(id) ON DELETE CASCADE,
    category_id UUID REFERENCES public.categories(id),
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    url TEXT UNIQUE,
    price_pen NUMERIC,
    price_status TEXT DEFAULT 'publicado',
    mode TEXT,
    duration TEXT,
    category TEXT,
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
    seniority_level TEXT,
    roi_months NUMERIC,
    provider_used TEXT,
    is_mock_data BOOLEAN DEFAULT false,
    view_count INTEGER DEFAULT 0,
    comparison_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    course_id UUID REFERENCES public.courses(id)
);

GRANT SELECT ON public.institutions, public.institution_site_profiles, public.categories, public.courses TO anon, authenticated, service_role;
GRANT INSERT ON public.leads TO anon, authenticated;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for courses" ON public.courses FOR SELECT USING (true);

CREATE OR REPLACE FUNCTION public.increment_view_count(p_course_id UUID)
RETURNS void
LANGUAGE plpgsql
SET search_path = public
SECURITY DEFINER
AS $$
BEGIN
    UPDATE public.courses SET view_count = view_count + 1 WHERE id = p_course_id;
END;
$$;
GRANT EXECUTE ON FUNCTION public.increment_view_count(UUID) TO anon, authenticated, service_role;

\ir ../../db/migrations/20260825_h2_editorial_layer.sql
\ir ../../db/migrations/20260825_h2_editorial_layer_grants_fix.sql
\ir ../../db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql
\ir ../../db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql
\ir ../../db/migrations/20260826_h2_editorial_layer_forward_fix.sql
\ir ../../db/migrations/20260826_h2_security_advisor_remediation.sql
\ir ../../db/migrations/20260826_h2_seed_editorial_field_definitions.sql
\ir ../../db/migrations/20260826_h2_seed_editorial_field_definitions.sql
\ir ../../db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql

DO $$
BEGIN
    IF (SELECT count(*) FROM public.editorial_field_definitions) <> 41 THEN
        RAISE EXCEPTION 'unexpected editorial_field_definitions seed count';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM public.editorial_field_definitions
        WHERE is_public = true
          AND field_key IN (
              'editorial_status',
              'quality_status',
              'missing_fields',
              'field_sources',
              'field_timestamps',
              'manual_overrides',
              'manual_start_date',
              'is_sponsored',
              'sponsored_priority',
              'sponsorship_label',
              'lead_cta_enabled',
              'availability_status',
              'published_at',
              'archived_at',
              'manual_updated_at',
              'manual_updated_by'
          )
    ) THEN
        RAISE EXCEPTION 'private editorial fields exposed in seed';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.editorial_field_definitions
        WHERE field_key = 'duration'
          AND ownership = 'hybrid_manual_preferred'
          AND is_required_for_publish = true
          AND is_public = true
    ) THEN
        RAISE EXCEPTION 'duration seed contract missing';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'courses_public_effective'
          AND column_name IN (
              'editorial_status',
              'quality_status',
              'missing_fields',
              'field_sources',
              'field_timestamps',
              'is_sponsored',
              'lead_cta_enabled',
              'sponsored_priority',
              'sponsorship_label',
              'availability_status',
              'editorial_updated_at'
          )
    ) THEN
        RAISE EXCEPTION 'private editorial fields exposed in public view';
    END IF;
END;
$$;

INSERT INTO public.institutions (id, name, website_url)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'Inst A', 'https://inst-a.example'),
    ('00000000-0000-0000-0000-000000000002', 'Inst B', 'https://inst-b.example');

INSERT INTO public.institution_site_profiles (institution_id, pipeline_ready, production_enabled)
VALUES
    ('00000000-0000-0000-0000-000000000001', true, true),
    ('00000000-0000-0000-0000-000000000002', true, false);

INSERT INTO public.categories (id, name)
VALUES ('10000000-0000-0000-0000-000000000001', 'Data');

INSERT INTO public.courses (
    id,
    institution_id,
    category_id,
    name,
    slug,
    url,
    mode,
    duration,
    category,
    is_active,
    is_verified,
    start_date
)
VALUES
    (
        '20000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000001',
        'Curso Completo',
        'curso-completo',
        'https://inst-a.example/curso-completo',
        'Remoto',
        '6 meses',
        'Data',
        true,
        true,
        '2026-09-01'
    ),
    (
        '20000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000001',
        'Curso Pendiente',
        'curso-pendiente',
        'https://inst-a.example/curso-pendiente',
        NULL,
        NULL,
        'Data',
        true,
        true,
        NULL
    ),
    (
        '20000000-0000-0000-0000-000000000003',
        '00000000-0000-0000-0000-000000000002',
        '10000000-0000-0000-0000-000000000001',
        'Curso No Produccion',
        'curso-no-produccion',
        'https://inst-b.example/curso-no-produccion',
        'Remoto',
        '6 meses',
        'Data',
        true,
        true,
        NULL
    );

INSERT INTO public.course_editorial_state (
    course_id,
    editorial_status,
    quality_status,
    manual_overrides,
    missing_fields,
    field_sources,
    field_timestamps,
    manual_start_date,
    manual_updated_by,
    published_at,
    availability_status
)
VALUES
    (
        '20000000-0000-0000-0000-000000000001',
        'published',
        'complete',
        '{"name":"Curso Completo Manual"}',
        ARRAY[]::TEXT[],
        '{"name":"manual_override","mode":"pipeline"}',
        '{"name":"2026-08-25T00:00:00Z"}',
        '2026-10-01',
        '30000000-0000-0000-0000-000000000001',
        now(),
        'available'
    ),
    (
        '20000000-0000-0000-0000-000000000003',
        'published',
        'complete',
        '{}',
        ARRAY[]::TEXT[],
        '{"name":"pipeline"}',
        '{"name":"2026-08-25T00:00:00Z"}',
        NULL,
        '30000000-0000-0000-0000-000000000001',
        now(),
        'available'
    );

\ir ../../db/migrations/20260826_h2_development_legacy_public_compat.sql

SET ROLE anon;

DO $$
DECLARE
    visible_count INTEGER;
    effective_name TEXT;
    effective_start_date DATE;
BEGIN
    SELECT count(*) INTO visible_count FROM public.courses_public_effective;
    IF visible_count <> 2 THEN
        RAISE EXCEPTION 'expected one strict H2 course plus one legacy public course, got %', visible_count;
    END IF;

    BEGIN
        SELECT count(*) INTO visible_count FROM public.courses;
        RAISE EXCEPTION 'anon direct courses read unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        NULL;
    END;

    SELECT name, start_date INTO effective_name, effective_start_date
      FROM public.courses_public_effective
     WHERE id = '20000000-0000-0000-0000-000000000001';

    IF effective_name <> 'Curso Completo Manual' THEN
        RAISE EXCEPTION 'manual name override not applied';
    END IF;
    IF effective_start_date <> DATE '2026-10-01' THEN
        RAISE EXCEPTION 'manual_start_date was not preferred';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM public.courses_public_effective
        WHERE id = '20000000-0000-0000-0000-000000000002'
          AND name = 'Curso Pendiente'
    ) THEN
        RAISE EXCEPTION 'legacy public pending course was not preserved by compatibility cohort';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM public.courses_public_effective
        WHERE id = '20000000-0000-0000-0000-000000000003'
    ) THEN
        RAISE EXCEPTION 'non-production course leaked through compatibility cohort';
    END IF;
END;
$$;

RESET ROLE;

SET ROLE service_role;

SELECT public.h2_update_course_quality(
    '20000000-0000-0000-0000-000000000002',
    ARRAY['mode', 'duration']::TEXT[],
    '{"name":"pipeline"}'::JSONB,
    '{"name":"2026-08-25T00:00:00Z"}'::JSONB,
    'h2-harness-quality-1',
    'hash-h2-harness-quality-1'
);

SELECT public.h2_update_course_quality(
    '20000000-0000-0000-0000-000000000002',
    ARRAY['mode', 'duration']::TEXT[],
    '{"name":"pipeline"}'::JSONB,
    '{"name":"2026-08-25T00:00:00Z"}'::JSONB,
    'h2-harness-quality-1',
    'hash-h2-harness-quality-1'
);

DO $$
DECLARE
    audit_count INTEGER;
    status_value TEXT;
BEGIN
    SELECT count(*) INTO audit_count
      FROM public.course_editorial_audit
     WHERE request_id = 'h2-harness-quality-1';
    IF audit_count <> 1 THEN
        RAISE EXCEPTION 'expected idempotent audit count 1, got %', audit_count;
    END IF;

    SELECT editorial_status INTO status_value
      FROM public.course_editorial_state
     WHERE course_id = '20000000-0000-0000-0000-000000000002';
    IF status_value <> 'pending_review' THEN
        RAISE EXCEPTION 'quality RPC changed editorial_status to %', status_value;
    END IF;
END;
$$;

DO $$
BEGIN
    BEGIN
        PERFORM public.h2_update_course_quality(
            '20000000-0000-0000-0000-000000000002',
            ARRAY[]::TEXT[],
            '{"name":"pipeline"}'::JSONB,
            '{"name":"2026-08-25T00:00:00Z"}'::JSONB,
            'h2-harness-quality-1',
            'different-payload-hash'
        );
        RAISE EXCEPTION 'quality RPC accepted reused request_id with different payload';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'request_id already exists for a different payload' THEN
            RAISE;
        END IF;
    END;
END;
$$;

DO $$
BEGIN
    BEGIN
        UPDATE public.course_editorial_audit
           SET reason = 'forbidden'
         WHERE request_id = 'h2-harness-quality-1';
        RAISE EXCEPTION 'audit update unexpectedly succeeded';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'course_editorial_audit is append-only' THEN
            RAISE;
        END IF;
    WHEN insufficient_privilege THEN
        NULL;
    END;
END;
$$;

RESET ROLE;

DO $$
BEGIN
    BEGIN
        DELETE FROM public.courses
         WHERE id = '20000000-0000-0000-0000-000000000002';
        RAISE EXCEPTION 'course delete unexpectedly succeeded despite audit FK';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
END;
$$;

RESET ROLE;

DO $$
BEGIN
    IF has_table_privilege('anon', 'public.leads', 'INSERT') THEN
        RAISE EXCEPTION 'anon still has INSERT on leads';
    END IF;
    IF has_table_privilege('authenticated', 'public.leads', 'INSERT') THEN
        RAISE EXCEPTION 'authenticated still has INSERT on leads';
    END IF;
    IF has_function_privilege('anon', 'public.increment_view_count(UUID)', 'EXECUTE') THEN
        RAISE EXCEPTION 'anon can still execute increment_view_count';
    END IF;
    IF has_function_privilege('authenticated', 'public.increment_view_count(UUID)', 'EXECUTE') THEN
        RAISE EXCEPTION 'authenticated can still execute increment_view_count';
    END IF;
END;
$$;

\ir ../../db/migrations/20260826_h2_security_advisor_remediation.sql
\ir ../../db/migrations/20260826_h2_seed_editorial_field_definitions.sql
\ir ../../db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql
\ir ../../db/migrations/20260826_h2_development_legacy_public_compat.sql

SELECT 'h2_pg17_harness_ok' AS result;
