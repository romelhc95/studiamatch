\set ON_ERROR_STOP on

CREATE EXTENSION IF NOT EXISTS pgcrypto;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN CREATE ROLE service_role NOLOGIN; END IF;
END $$;

CREATE TABLE public.institutions (id uuid PRIMARY KEY, name text NOT NULL);
CREATE TABLE public.institution_site_profiles (institution_id uuid PRIMARY KEY REFERENCES public.institutions(id));
INSERT INTO public.institutions (id, name)
VALUES ('10000000-0000-0000-0000-000000000001', 'H3 Synthetic Institute');

\i /fixture/20260430_intermediate_tables_ddl.sql
ALTER TABLE public.enriched_programs ADD COLUMN provider_used text;
ALTER TABLE public.enriched_programs ADD COLUMN is_mock_data boolean DEFAULT true;
\i /fixture/20260808_fase10_8_atomic_cleansing_provenance.sql
\i /fixture/20260525_fase113_pro_rls_and_rpc_sync.sql

CREATE TABLE public.courses (
  id uuid PRIMARY KEY,
  institution_id uuid NOT NULL REFERENCES public.institutions(id),
  category_id uuid,
  name text NOT NULL,
  slug text NOT NULL,
  url text NOT NULL UNIQUE,
  mode text,
  duration text,
  price_pen numeric,
  price_status text,
  description_long text,
  provider_used text,
  is_mock_data boolean DEFAULT true,
  is_active boolean DEFAULT false,
  is_verified boolean DEFAULT false,
  updated_at timestamptz DEFAULT now()
);

\echo phase=discovery-checkpoint|result=START
BEGIN;
INSERT INTO public.staging_raw (
  id, institution_id, url, raw_name, raw_description, status, metadata
)
VALUES (
  '00000000-0000-0000-0000-000000000101',
  '10000000-0000-0000-0000-000000000001',
  'https://pipeline.synthetic.example/course-001',
  'Curso H3 sintético', 'Descripción sintética', 'discovered',
  '{"fixture":"h3req1-pg17-persistence-r1"}'::jsonb
);
COMMIT;

\connect h3_pipeline_recovery_r1
DO $$
DECLARE saved_status text; saved_count integer;
BEGIN
  SELECT status INTO STRICT saved_status FROM public.staging_raw
  WHERE id = '00000000-0000-0000-0000-000000000101';
  SELECT count(*) INTO saved_count FROM public.staging_raw
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  IF saved_status <> 'discovered' OR saved_count <> 1 THEN
    RAISE EXCEPTION 'discovery checkpoint did not survive reconnect';
  END IF;
END $$;
\echo phase=discovery-checkpoint|result=PASS

\echo phase=resume-and-cleansing|result=START
BEGIN;
UPDATE public.staging_raw SET status = 'processing'
WHERE id = '00000000-0000-0000-0000-000000000101' AND status = 'discovered';
SELECT public.atomic_cleansing_promote(
  ARRAY['00000000-0000-0000-0000-000000000101'::uuid],
  '[{
    "staging_id":"00000000-0000-0000-0000-000000000101",
    "institution_id":"10000000-0000-0000-0000-000000000001",
    "url":"https://pipeline.synthetic.example/course-001",
    "effective_url":"https://pipeline.synthetic.example/course-001",
    "canonical_url":"https://pipeline.synthetic.example/course-001",
    "clean_name":"Curso H3 sintético",
    "clean_description":"Descripción sintética",
    "modality":"online",
    "location":"Lima",
    "base_price":150,
    "currency":"PEN",
    "metadata":{"source":"synthetic-discovery","record":"course-001"}
  }]'::jsonb
);
COMMIT;

\connect h3_pipeline_recovery_r1
DO $$
DECLARE stage_status text; cleansed_status text; row_count integer;
BEGIN
  SELECT status INTO STRICT stage_status FROM public.staging_raw
  WHERE id = '00000000-0000-0000-0000-000000000101';
  SELECT status INTO STRICT cleansed_status FROM public.cleansed_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  SELECT count(*) INTO row_count FROM public.cleansed_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  IF stage_status <> 'processed' OR cleansed_status <> 'pending' OR row_count <> 1 THEN
    RAISE EXCEPTION 'cleansing handoff did not persist exactly once';
  END IF;
END $$;
\echo phase=resume-and-cleansing|result=PASS

\echo phase=enrichment-failure-recovery|result=START
DO $$
BEGIN
  BEGIN
    PERFORM public.atomic_enrichment_promote(
      jsonb_build_array(jsonb_build_object(
        'cleansed_id', (SELECT id::text FROM public.cleansed_programs WHERE url='https://pipeline.synthetic.example/course-001'),
        'institution_id', '10000000-0000-0000-0000-000000000001',
        'url', 'https://pipeline.synthetic.example/course-001',
        'official_name', 'Curso H3 sintético',
        'duration_text', '12 meses',
        'duration_months', 'not-a-number',
        'total_cost_est', '1500',
        'curriculum_summary', '{}',
        'modality', 'online',
        'provider_used', 'synthetic',
        'is_mock_data', true
      )),
      (SELECT id FROM public.cleansed_programs WHERE url='https://pipeline.synthetic.example/course-001')
    );
    RAISE EXCEPTION 'expected malformed enrichment to fail';
  EXCEPTION WHEN invalid_text_representation THEN
    RAISE NOTICE 'synthetic malformed enrichment rejected';
  END;
END $$;
DO $$
DECLARE cleansed_status text; enriched_count integer;
BEGIN
  SELECT status INTO STRICT cleansed_status FROM public.cleansed_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  SELECT count(*) INTO enriched_count FROM public.enriched_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  IF cleansed_status <> 'pending' OR enriched_count <> 0 THEN
    RAISE EXCEPTION 'failed enrichment changed persisted state';
  END IF;
END $$;

SELECT public.atomic_enrichment_promote(
  jsonb_build_array(jsonb_build_object(
    'cleansed_id', (SELECT id::text FROM public.cleansed_programs WHERE url='https://pipeline.synthetic.example/course-001'),
    'institution_id', '10000000-0000-0000-0000-000000000001',
    'url', 'https://pipeline.synthetic.example/course-001',
    'official_name', 'Curso H3 sintético',
    'duration_text', '12 meses',
    'duration_months', '12',
    'total_cost_est', '1500',
    'requirements', 'Requisitos sintéticos',
    'graduate_profile', 'Perfil sintético',
    'curriculum_summary', '{"modules":2}',
    'modality', 'online',
    'primary_campus', 'Lima',
    'degree_type', 'certificado',
    'start_date', '2026-11-01',
    'categories', 'tecnología',
    'difficulty_level', 'intermedio',
    'ai_summary', 'Resumen sintético',
    'provider_used', 'synthetic',
    'is_mock_data', true
  )),
  (SELECT id FROM public.cleansed_programs WHERE url='https://pipeline.synthetic.example/course-001')
);
SELECT public.atomic_enrichment_promote(
  jsonb_build_array(jsonb_build_object(
    'cleansed_id', (SELECT id::text FROM public.cleansed_programs WHERE url='https://pipeline.synthetic.example/course-001'),
    'institution_id', '10000000-0000-0000-0000-000000000001',
    'url', 'https://pipeline.synthetic.example/course-001',
    'official_name', 'Curso H3 sintético revisado',
    'duration_text', '12 meses',
    'duration_months', '12',
    'total_cost_est', '1500',
    'curriculum_summary', '{"modules":2}',
    'modality', 'online',
    'provider_used', 'synthetic',
    'is_mock_data', true
  )),
  (SELECT id FROM public.cleansed_programs WHERE url='https://pipeline.synthetic.example/course-001')
);

\connect h3_pipeline_recovery_r1
DO $$
DECLARE enriched_count integer; cleansed_status text; v_official_name text;
BEGIN
  SELECT count(*) INTO enriched_count FROM public.enriched_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  SELECT status INTO STRICT cleansed_status FROM public.cleansed_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  SELECT ep.official_name INTO STRICT v_official_name FROM public.enriched_programs AS ep
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  IF enriched_count <> 1 OR cleansed_status <> 'enriched' OR v_official_name <> 'Curso H3 sintético revisado' THEN
    RAISE EXCEPTION 'enrichment recovery/idempotence assertion failed';
  END IF;
END $$;
\echo phase=enrichment-failure-recovery|result=PASS

\echo phase=sync-failure-recovery|result=START
BEGIN;
INSERT INTO public.courses (
  id, institution_id, name, slug, url, mode, duration, price_pen,
  provider_used, is_mock_data, is_active, is_verified
)
VALUES (
  '30000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'Curso H3 sintético revisado', 'curso-h3-sintetico-001',
  'https://pipeline.synthetic.example/course-001', 'online', '12 meses',
  1500, 'synthetic', true, true, true
)
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, updated_at = now();
COMMIT;

DO $$
BEGIN
  BEGIN
    UPDATE public.enriched_programs
    SET status = ('not-a-uuid'::uuid)::text
    WHERE url = 'https://pipeline.synthetic.example/course-001';
    RAISE EXCEPTION 'expected sync status update to fail';
  EXCEPTION WHEN invalid_text_representation THEN
    RAISE NOTICE 'synthetic sync status update rejected';
  END;
END $$;
DO $$
DECLARE course_count integer; enrichment_status text;
BEGIN
  SELECT count(*) INTO course_count FROM public.courses
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  SELECT status INTO STRICT enrichment_status FROM public.enriched_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  IF course_count <> 1 OR enrichment_status <> 'pending' THEN
    RAISE EXCEPTION 'sync partial-failure state was not recoverable';
  END IF;
END $$;

BEGIN;
INSERT INTO public.courses (
  id, institution_id, name, slug, url, mode, duration, price_pen,
  provider_used, is_mock_data, is_active, is_verified
)
VALUES (
  '30000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'Curso H3 sintético revisado', 'curso-h3-sintetico-001',
  'https://pipeline.synthetic.example/course-001', 'online', '12 meses',
  1500, 'synthetic', true, true, true
)
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, updated_at = now();
UPDATE public.enriched_programs SET status = 'synced'
WHERE url = 'https://pipeline.synthetic.example/course-001' AND status = 'pending';
COMMIT;

BEGIN;
INSERT INTO public.courses (
  id, institution_id, name, slug, url, mode, duration, price_pen,
  provider_used, is_mock_data, is_active, is_verified
)
VALUES (
  '30000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'Curso H3 sintético revisado', 'curso-h3-sintetico-001',
  'https://pipeline.synthetic.example/course-001', 'online', '12 meses',
  1500, 'synthetic', true, true, true
)
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, updated_at = now();
COMMIT;

\connect h3_pipeline_recovery_r1
DO $$
DECLARE course_count integer; course_id uuid; enrichment_status text;
BEGIN
  SELECT count(*) INTO course_count FROM public.courses
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  SELECT id INTO STRICT course_id FROM public.courses
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  SELECT status INTO STRICT enrichment_status FROM public.enriched_programs
  WHERE url = 'https://pipeline.synthetic.example/course-001';
  IF course_count <> 1 OR course_id <> '30000000-0000-0000-0000-000000000001'::uuid OR enrichment_status <> 'synced' THEN
    RAISE EXCEPTION 'sync recovery/idempotence assertion failed';
  END IF;
END $$;
\echo phase=sync-failure-recovery|result=PASS
\echo phase=pipeline-persistence-recovery|result=PASS
