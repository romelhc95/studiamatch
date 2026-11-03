-- Local-only functional fixture. Applies only to the disposable h3_final_uat_* PG17 database.
-- The pipeline payload comes from tests/test_h3req1_local_pipeline_walk.py.
\set ON_ERROR_STOP on
\if :{?h3_course_payload}
\else
\echo 'missing synthetic pipeline payload'
\quit 3
\endif

BEGIN;
CREATE TEMP TABLE h3_uat_pipeline_payload (payload JSONB) ON COMMIT DROP;
INSERT INTO h3_uat_pipeline_payload VALUES (:'h3_course_payload'::JSONB);

DO $$
DECLARE
  payload JSONB;
BEGIN
  SELECT source.payload INTO payload FROM h3_uat_pipeline_payload AS source;
  IF jsonb_typeof(payload) IS DISTINCT FROM 'object'
     OR payload->>'id' <> '70000000-0000-0000-0000-000000000091'
     OR payload->>'institution_id' <> '00000000-0000-0000-0000-000000000001'
     OR payload->>'category_id' <> '10000000-0000-0000-0000-000000000001'
     OR payload->>'provider_used' <> 'synthetic-provider'
     OR payload->>'is_mock_data' <> 'false'
     OR payload->>'url' NOT LIKE 'https://synthetic.h3.example/%'
     OR payload->>'slug' <> 'analitica-aplicada-60000000' THEN
    RAISE EXCEPTION 'pipeline payload did not match the synthetic fixture contract';
  END IF;
END;
$$;

INSERT INTO public.categories (id, name)
VALUES ('10000000-0000-0000-0000-000000000001', 'Data')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.courses (
  id, institution_id, category_id, name, slug, url, price_pen, price_status,
  mode, duration, category, description_long, syllabus, target_audience,
  requirements, certification, benefits, objectives, start_date, start_date_text,
  course_type, seniority_level, is_active, is_verified, provider_used,
  is_mock_data, created_at, updated_at
)
SELECT
  (source.payload->>'id')::UUID,
  (source.payload->>'institution_id')::UUID,
  (source.payload->>'category_id')::UUID,
  source.payload->>'name',
  source.payload->>'slug',
  source.payload->>'url',
  NULLIF(source.payload->>'price_pen', '')::NUMERIC,
  source.payload->>'price_status',
  source.payload->>'mode',
  source.payload->>'duration',
  source.payload->>'category',
  source.payload->>'description_long',
  source.payload->>'syllabus',
  source.payload->>'target_audience',
  source.payload->>'requirements',
  source.payload->>'certification',
  source.payload->>'benefits',
  source.payload->>'objectives',
  NULLIF(source.payload->>'start_date', '')::DATE,
  source.payload->>'start_date_text',
  source.payload->>'course_type',
  source.payload->>'seniority_level',
  COALESCE((source.payload->>'is_active')::BOOLEAN, false),
  COALESCE((source.payload->>'is_verified')::BOOLEAN, false),
  source.payload->>'provider_used',
  COALESCE((source.payload->>'is_mock_data')::BOOLEAN, true),
  now() - INTERVAL '35 days',
  COALESCE(NULLIF(source.payload->>'last_scraped_at', '')::TIMESTAMPTZ, now())
FROM h3_uat_pipeline_payload AS source
ON CONFLICT (id) DO UPDATE SET
  institution_id = EXCLUDED.institution_id,
  category_id = EXCLUDED.category_id,
  name = EXCLUDED.name,
  slug = EXCLUDED.slug,
  url = EXCLUDED.url,
  price_pen = EXCLUDED.price_pen,
  price_status = EXCLUDED.price_status,
  mode = EXCLUDED.mode,
  duration = EXCLUDED.duration,
  category = EXCLUDED.category,
  description_long = EXCLUDED.description_long,
  syllabus = EXCLUDED.syllabus,
  target_audience = EXCLUDED.target_audience,
  requirements = EXCLUDED.requirements,
  certification = EXCLUDED.certification,
  benefits = EXCLUDED.benefits,
  objectives = EXCLUDED.objectives,
  start_date = EXCLUDED.start_date,
  start_date_text = EXCLUDED.start_date_text,
  course_type = EXCLUDED.course_type,
  seniority_level = EXCLUDED.seniority_level,
  is_active = EXCLUDED.is_active,
  is_verified = EXCLUDED.is_verified,
  provider_used = EXCLUDED.provider_used,
  is_mock_data = EXCLUDED.is_mock_data,
  updated_at = EXCLUDED.updated_at;

-- Keep two unpublished rows as intentional incomplete, zero-price and null-price controls.
UPDATE public.courses
SET price_pen = 0, price_status = 'consultar', start_date = DATE '2025-09-01'
WHERE id = '20000000-0000-0000-0000-000000000001';
UPDATE public.courses
SET price_pen = NULL, price_status = 'consultar', start_date = NULL, duration = NULL
WHERE id = '20000000-0000-0000-0000-000000000002';

-- Add nine strict-public synthetic rows for filter, sorting, comparison and pagination.
UPDATE public.courses AS course
SET
  course_type = CASE substring(course.id::TEXT FROM '[0-9]+$')::INTEGER
    WHEN 12 THEN 'Curso'
    WHEN 13 THEN 'Diplomado'
    WHEN 14 THEN 'Maestría'
    WHEN 15 THEN 'Especialización'
    WHEN 16 THEN 'Certificado'
    WHEN 17 THEN 'Curso'
    WHEN 18 THEN 'Diplomado'
    WHEN 19 THEN 'Maestría'
    ELSE 'Curso'
  END,
  price_pen = CASE substring(course.id::TEXT FROM '[0-9]+$')::INTEGER
    WHEN 12 THEN 5000
    WHEN 13 THEN 5001
    WHEN 14 THEN 15000
    WHEN 15 THEN 15001
    WHEN 16 THEN 0
    WHEN 17 THEN NULL
    WHEN 18 THEN 1250
    WHEN 19 THEN 2000
    ELSE 3000
  END,
  price_status = CASE WHEN substring(course.id::TEXT FROM '[0-9]+$')::INTEGER IN (16, 17) THEN 'consultar' ELSE 'publicado' END,
  duration = CASE substring(course.id::TEXT FROM '[0-9]+$')::INTEGER
    WHEN 12 THEN '18 meses'
    WHEN 13 THEN '6 meses (24 semanas)'
    WHEN 14 THEN '3 meses'
    WHEN 15 THEN '6 meses'
    WHEN 16 THEN '7 meses'
    WHEN 17 THEN '12 meses'
    WHEN 18 THEN '6 meses'
    WHEN 19 THEN '4 meses'
    ELSE '3 meses'
  END,
  mode = CASE WHEN substring(course.id::TEXT FROM '[0-9]+$')::INTEGER = 13 THEN 'Híbrido' ELSE course.mode END,
  start_date = CASE WHEN substring(course.id::TEXT FROM '[0-9]+$')::INTEGER = 14 THEN DATE '2025-01-15' ELSE DATE '2027-04-01' END,
  certification = CASE WHEN substring(course.id::TEXT FROM '[0-9]+$')::INTEGER = 19 THEN 'Constancia sintética local' ELSE 'Certificación sintética' END,
  seniority_level = CASE WHEN substring(course.id::TEXT FROM '[0-9]+$')::INTEGER IN (12, 16, 18) THEN 'Junior' WHEN substring(course.id::TEXT FROM '[0-9]+$')::INTEGER IN (14, 19) THEN 'Senior' ELSE 'Mid' END,
  roi_months = CASE WHEN substring(course.id::TEXT FROM '[0-9]+$')::INTEGER = 19 THEN 5 ELSE 12 END,
  is_active = true,
  is_verified = true,
  created_at = now() - INTERVAL '60 days' + make_interval(mins => substring(course.id::TEXT FROM '[0-9]+$')::INTEGER),
  updated_at = now()
WHERE course.id::TEXT LIKE '20000000-0000-0000-0000-%'
  AND substring(course.id::TEXT FROM '[0-9]+$')::INTEGER BETWEEN 12 AND 20;

UPDATE public.course_editorial_state AS state
SET
  editorial_status = 'published',
  quality_status = 'complete',
  missing_fields = ARRAY[]::TEXT[],
  availability_status = 'unknown',
  availability_override_status = 'available',
  availability_evidence_url = 'https://synthetic.h3.example/availability/' || state.course_id::TEXT,
  availability_observed_at = now() - INTERVAL '1 day',
  availability_valid_until = now() - INTERVAL '1 day' + INTERVAL '90 days',
  availability_override_by = '30000000-0000-0000-0000-000000000001',
  published_at = COALESCE(state.published_at, now()),
  manual_updated_at = now(),
  manual_updated_by = '30000000-0000-0000-0000-000000000001',
  archived_at = NULL,
  manual_overrides = '{}'::JSONB,
  field_sources = jsonb_build_object('name', 'pipeline', 'price_pen', 'pipeline', 'mode', 'pipeline', 'duration', 'pipeline'),
  updated_at = now()
WHERE state.course_id::TEXT LIKE '20000000-0000-0000-0000-%'
  AND substring(state.course_id::TEXT FROM '[0-9]+$')::INTEGER BETWEEN 12 AND 25;

-- Publish the synthetic pipeline output for public listing/detail UAT only.
-- The base pipeline seed intentionally starts unpublished with unknown availability.
UPDATE public.course_editorial_state AS state
SET
  editorial_status = 'published',
  quality_status = 'complete',
  missing_fields = ARRAY[]::TEXT[],
  availability_status = 'unknown',
  availability_override_status = 'available',
  availability_evidence_url = 'https://synthetic.h3.example/availability/' || state.course_id::TEXT,
  availability_observed_at = now() - INTERVAL '1 day',
  availability_valid_until = now() - INTERVAL '1 day' + INTERVAL '90 days',
  availability_override_by = '30000000-0000-0000-0000-000000000001',
  published_at = COALESCE(state.published_at, now()),
  manual_updated_at = now(),
  manual_updated_by = '30000000-0000-0000-0000-000000000001',
  archived_at = NULL,
  manual_overrides = '{}'::JSONB,
  field_sources = jsonb_build_object('name', 'pipeline', 'price_pen', 'pipeline', 'mode', 'pipeline', 'duration', 'pipeline'),
  updated_at = now()
WHERE state.course_id = '70000000-0000-0000-0000-000000000091';

DO $$
BEGIN
  IF (SELECT count(*) FROM public.courses_public_effective) < 13 THEN
    RAISE EXCEPTION 'functional public fixture does not cross the 12-item pagination boundary';
  END IF;
  IF (SELECT count(*) FROM public.courses
       WHERE id = '70000000-0000-0000-0000-000000000091'
         AND provider_used = 'synthetic-provider'
         AND is_mock_data IS FALSE
         AND name = 'Analítica Aplicada'
         AND price_pen = 1250) <> 1 THEN
    RAISE EXCEPTION 'PG17 course does not match the emitted pipeline payload';
  END IF;
  IF (SELECT count(*) FROM public.course_editorial_state
       WHERE course_id = '70000000-0000-0000-0000-000000000091'
         AND editorial_status = 'published'
         AND availability_override_status = 'available'
       AND availability_valid_until > now()
       AND availability_valid_until <= availability_observed_at + INTERVAL '90 days') <> 1 THEN
    RAISE EXCEPTION 'pipeline Admin fixture is not currently eligible for its local static route';
  END IF;
END;
$$;

COMMIT;
SELECT 'h3_uat_functional_catalog_seed_ok' AS marker;
