-- StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261102-h3-legacy-public-withdrawal
\set ON_ERROR_STOP on

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END;
$$;

CREATE SCHEMA private;
GRANT USAGE ON SCHEMA private TO anon, authenticated, service_role;

CREATE TABLE public.courses (
  id UUID PRIMARY KEY,
  institution_id UUID NOT NULL,
  category_id UUID,
  name TEXT NOT NULL,
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
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_active BOOLEAN NOT NULL DEFAULT true,
  is_verified BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE public.institution_site_profiles (
  institution_id UUID PRIMARY KEY,
  production_enabled BOOLEAN NOT NULL DEFAULT true,
  notes TEXT
);

CREATE TABLE public.course_editorial_state (
  course_id UUID PRIMARY KEY,
  editorial_status TEXT NOT NULL,
  published_editorial_values JSONB,
  published_manual_overrides JSONB,
  manual_overrides JSONB,
  published_manual_start_date DATE,
  manual_start_date DATE,
  availability_override_status TEXT,
  availability_valid_until TIMESTAMPTZ,
  availability_status TEXT
);

CREATE TABLE public.course_editorial_audit (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  course_id UUID NOT NULL,
  action TEXT NOT NULL
);

CREATE TABLE private.h2_legacy_public_course_cohort (
  course_id UUID PRIMARY KEY
);

CREATE VIEW private.h3_legacy_public_course_cohort AS
SELECT course_id FROM private.h2_legacy_public_course_cohort;
REVOKE ALL ON TABLE private.h3_legacy_public_course_cohort FROM PUBLIC, anon, authenticated, service_role;

INSERT INTO public.institution_site_profiles (institution_id)
VALUES ('10000000-0000-0000-0000-000000000001');

INSERT INTO public.courses (id, institution_id, name, is_active, is_verified)
VALUES
  ('10000000-0000-0000-0000-000000000011', '10000000-0000-0000-0000-000000000001', 'Harvester untouched legacy', true, true),
  ('10000000-0000-0000-0000-000000000012', '10000000-0000-0000-0000-000000000001', 'Harvester published snapshot', true, true),
  ('10000000-0000-0000-0000-000000000013', '10000000-0000-0000-0000-000000000001', 'Harvester after withdrawal', true, true),
  ('10000000-0000-0000-0000-000000000014', '10000000-0000-0000-0000-000000000001', 'Harvester archived', true, true);

INSERT INTO private.h2_legacy_public_course_cohort (course_id)
VALUES
  ('10000000-0000-0000-0000-000000000011'),
  ('10000000-0000-0000-0000-000000000012'),
  ('10000000-0000-0000-0000-000000000013'),
  ('10000000-0000-0000-0000-000000000014');

INSERT INTO public.course_editorial_state (
  course_id, editorial_status, published_editorial_values, availability_status
)
VALUES
  ('10000000-0000-0000-0000-000000000012', 'published', '{"name":"Approved snapshot","price_pen":""}', 'available'),
  ('10000000-0000-0000-0000-000000000013', 'published', '{"name":"Approved snapshot before withdrawal"}', 'available'),
  ('10000000-0000-0000-0000-000000000014', 'published', '{"name":"Approved snapshot before archive"}', 'available');
