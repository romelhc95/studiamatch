\set ON_ERROR_STOP on

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

DROP SCHEMA IF EXISTS private CASCADE;
DROP ROLE IF EXISTS anon;
DROP ROLE IF EXISTS authenticated;
DROP ROLE IF EXISTS service_role;
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN;

GRANT USAGE, CREATE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

CREATE TABLE public.institutions (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT,
    website_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.institution_site_profiles (
    institution_id UUID PRIMARY KEY REFERENCES public.institutions(id),
    pipeline_ready BOOLEAN DEFAULT false,
    allowed_url_patterns JSONB DEFAULT '[]'::jsonb,
    noise_patterns JSONB DEFAULT '[]'::jsonb,
    max_consecutive_errors INTEGER DEFAULT 5,
    circuit_open BOOLEAN DEFAULT false,
    circuit_opened_at TIMESTAMPTZ,
    discovery_enabled BOOLEAN DEFAULT true,
    pipeline_enabled BOOLEAN DEFAULT true,
    production_enabled BOOLEAN DEFAULT false,
    notes TEXT
);

CREATE TABLE public.categories (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.courses (
    id UUID PRIMARY KEY,
    institution_id UUID REFERENCES public.institutions(id),
    category_id UUID REFERENCES public.categories(id),
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
    view_count INTEGER DEFAULT 0,
    comparison_count INTEGER DEFAULT 0,
    category TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES public.courses(id),
    email TEXT
);

ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institution_site_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY courses_select_public ON public.courses FOR SELECT TO anon USING (
    is_active IS TRUE
    AND is_verified IS TRUE
    AND EXISTS (
        SELECT 1 FROM public.institution_site_profiles p
        WHERE p.institution_id = courses.institution_id
          AND p.production_enabled IS TRUE
    )
);
CREATE POLICY courses_select_authenticated ON public.courses FOR SELECT TO authenticated USING (
    is_active IS TRUE
    AND is_verified IS TRUE
    AND EXISTS (
        SELECT 1 FROM public.institution_site_profiles p
        WHERE p.institution_id = courses.institution_id
          AND p.production_enabled IS TRUE
    )
);
CREATE POLICY courses_exclude_release_canary ON public.courses AS RESTRICTIVE FOR SELECT TO anon, authenticated USING (
    NOT EXISTS (
        SELECT 1 FROM public.institution_site_profiles p
        WHERE p.institution_id = courses.institution_id
          AND COALESCE(p.notes, '') = 'DB_AS_CODE_RELEASE_CANARY'
    )
);
CREATE POLICY profiles_select_public ON public.institution_site_profiles FOR SELECT TO anon USING (production_enabled = true);
CREATE POLICY profiles_select_authenticated ON public.institution_site_profiles FOR SELECT TO authenticated USING (production_enabled = true);
CREATE POLICY profiles_exclude_release_canary ON public.institution_site_profiles AS RESTRICTIVE FOR SELECT TO anon, authenticated USING (COALESCE(notes, '') <> 'DB_AS_CODE_RELEASE_CANARY');
CREATE POLICY institutions_public_read ON public.institutions FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY categories_public_read ON public.categories FOR SELECT TO anon, authenticated USING (true);

GRANT SELECT ON public.institutions, public.institution_site_profiles, public.categories, public.courses TO anon, authenticated, service_role;
GRANT INSERT ON public.leads TO anon, authenticated;

CREATE OR REPLACE FUNCTION public.increment_view_count(p_course_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE public.courses SET view_count = view_count + 1 WHERE id = p_course_id;
END;
$$;
GRANT EXECUTE ON FUNCTION public.increment_view_count(UUID) TO anon, authenticated, service_role;

INSERT INTO public.institutions (id, name, slug, website_url)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'Inst A', 'inst-a', 'https://inst-a.example'),
    ('00000000-0000-0000-0000-000000000002', 'Inst B', 'inst-b', 'https://inst-b.example'),
    ('00000000-0000-0000-0000-000000000003', 'Inst Canary', 'inst-canary', 'https://canary.example');

INSERT INTO public.institution_site_profiles (institution_id, pipeline_ready, production_enabled, notes)
VALUES
    ('00000000-0000-0000-0000-000000000001', true, true, NULL),
    ('00000000-0000-0000-0000-000000000002', true, false, NULL),
    ('00000000-0000-0000-0000-000000000003', true, true, 'DB_AS_CODE_RELEASE_CANARY');

INSERT INTO public.categories (id, name, slug)
VALUES ('10000000-0000-0000-0000-000000000001', 'Data', 'data');

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
SELECT
    ('20000000-0000-0000-0000-' || lpad(gs::TEXT, 12, '0'))::UUID,
    '00000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    'Curso ' || gs,
    'curso-' || gs,
    'https://inst-a.example/curso-' || gs,
    CASE WHEN gs <= 120 THEN 'Remoto' ELSE NULL END,
    CASE WHEN gs <= 120 THEN '6 meses' ELSE NULL END,
    'Data',
    true,
    true,
    '2026-09-01'
FROM generate_series(1, 224) AS gs;

INSERT INTO public.courses (id, institution_id, category_id, name, slug, url, mode, duration, category, is_active, is_verified)
VALUES
    ('30000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'Inactive', 'inactive', 'https://inst-a.example/inactive', 'Remoto', '1 mes', 'Data', false, true),
    ('30000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', 'Non Production', 'non-production', 'https://inst-b.example/non-production', 'Remoto', '1 mes', 'Data', true, true),
    ('30000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', 'Release Canary', 'release-canary', 'https://canary.invalid/release-canary', 'Remoto', '1 mes', 'Data', true, true);

SELECT 1 / CASE WHEN count(*) = 224 THEN 1 ELSE 0 END AS assert_initial_contract_count
FROM public.courses c
WHERE c.is_active IS TRUE
  AND c.is_verified IS TRUE
  AND c.institution_id = '00000000-0000-0000-0000-000000000001'
  AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%');

SELECT set_config('app.h2_expected_eligible_count', '224', false);
SELECT set_config(
    'app.h2_expected_cohort_digest',
    (SELECT 'sha256:' || encode(sha256(convert_to(string_agg(id::TEXT, ',' ORDER BY id::TEXT), 'UTF8')), 'hex')
       FROM public.courses
      WHERE id::TEXT LIKE '20000000-0000-0000-0000-%'),
    false
);
SELECT set_config('app.h2_payload_sha', 'h2-pg17-harness', false);
SELECT set_config('app.h2_authorization_id', 'DDL-H2-PG17-HARNESS', false);

\ir ../../db/migrations/20260827_h2_pro_expand_schema_compat.sql
\ir ../../db/migrations/20260827_h2_pro_seed_editorial_field_definitions.sql
\ir ../../db/migrations/20260827_h2_pro_backfill_editorial_state.sql
\ir ../../db/migrations/20260827_h2_pro_capture_legacy_cohort.sql

DO $$
DECLARE
    expected_digest TEXT;
    verify_payload JSONB;
BEGIN
    SELECT 'sha256:' || encode(sha256(convert_to(string_agg(course_id::TEXT, ',' ORDER BY course_id::TEXT), 'UTF8')), 'hex')
      INTO expected_digest
      FROM private.h2_legacy_public_course_cohort;

    SELECT public.h2_verify_expand_compat(224, expected_digest) INTO verify_payload;

    IF (verify_payload ->> 'cohort_count')::INTEGER <> 224 THEN
        RAISE EXCEPTION 'unexpected cohort count after expand';
    END IF;
    IF (verify_payload ->> 'private_column_count')::INTEGER <> 0 THEN
        RAISE EXCEPTION 'private columns exposed after expand';
    END IF;
END;
$$;

SELECT count(*) AS effective_public_count FROM public.courses_public_effective;
SELECT 1 / CASE WHEN count(*) = 224 THEN 1 ELSE 0 END AS assert_effective_public_count FROM public.courses_public_effective;
SELECT 1 / CASE WHEN count(*) = 0 THEN 1 ELSE 0 END AS assert_effective_canary_hidden FROM public.courses_public_effective WHERE slug = 'release-canary';

DO $$
BEGIN
    IF NOT has_table_privilege('anon', 'public.courses_public_effective', 'SELECT') THEN
        RAISE EXCEPTION 'anon lacks SELECT grant on courses_public_effective';
    END IF;
END;
$$;

\ir ../../db/migrations/20260827_h2_pro_expand_schema_compat.sql
\ir ../../db/migrations/20260827_h2_pro_seed_editorial_field_definitions.sql
\ir ../../db/migrations/20260827_h2_pro_backfill_editorial_state.sql
\ir ../../db/migrations/20260827_h2_pro_capture_legacy_cohort.sql

\ir ../../db/migrations/20260827_h2_pro_contract_public_reader.sql

DO $$
BEGIN
    IF has_table_privilege('anon', 'public.courses', 'SELECT') THEN
        RAISE EXCEPTION 'contract-public-reader did not revoke anon direct courses SELECT';
    END IF;
END;
$$;

\ir ../../db/migrations/20260827_h2_pro_rollback_public_reader_contract.sql

DO $$
BEGIN
    IF NOT has_table_privilege('anon', 'public.courses', 'SELECT') THEN
        RAISE EXCEPTION 'rollback-public-reader-contract did not restore anon direct courses SELECT';
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT has_table_privilege('anon', 'public.courses', 'SELECT') THEN
        RAISE EXCEPTION 'rollback did not restore anon SELECT grant';
    END IF;
END;
$$;

\ir ../../db/migrations/20260827_h2_pro_contract_public_reader.sql

UPDATE public.course_editorial_state
   SET editorial_status = 'published',
       quality_status = 'complete',
       availability_status = 'available',
       missing_fields = ARRAY[]::TEXT[],
       manual_updated_by = '40000000-0000-0000-0000-000000000001',
       manual_updated_at = now(),
       published_at = now()
 WHERE course_id IN (SELECT course_id FROM private.h2_legacy_public_course_cohort);

\ir ../../db/migrations/20260827_h2_pro_contract_legacy_cohort.sql

DO $$
BEGIN
    IF to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL THEN
        RAISE EXCEPTION 'legacy cohort was not retired';
    END IF;
    IF (SELECT count(*) FROM public.courses_public_effective) <> 224 THEN
        RAISE EXCEPTION 'strict H2 public view did not preserve 224 courses';
    END IF;
    IF has_table_privilege('anon', 'public.courses', 'SELECT') THEN
        RAISE EXCEPTION 'direct courses SELECT restored unexpectedly after contract';
    END IF;
END;
$$;

DO $$
BEGIN
    IF to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL THEN
        RAISE EXCEPTION 'rollback guard cannot be proven while legacy cohort exists';
    END IF;
END;
$$;

\set ON_ERROR_STOP off
BEGIN;
\ir ../../db/migrations/20260827_h2_pro_rollback_public_reader_contract.sql
ROLLBACK;
\set ON_ERROR_STOP on

DO $$
BEGIN
    IF has_table_privilege('anon', 'public.courses', 'SELECT') THEN
        RAISE EXCEPTION 'rollback after legacy cohort retirement unexpectedly restored anon direct courses SELECT';
    END IF;
END;
$$;
