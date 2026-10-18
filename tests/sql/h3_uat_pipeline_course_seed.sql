-- Synthetic-only bridge fixture for the local end-to-end pipeline/Admin/public UAT.
-- The pipeline transform test produces these exact course fields and stable ID.
-- This seed is applied only to the disposable h3_final_uat_* PG17 database.
\set ON_ERROR_STOP on

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM auth.users
     WHERE id = '30000000-0000-0000-0000-000000000001'
       AND email = 'admin@local.test'
  ) THEN
    RAISE EXCEPTION 'local Admin runtime identity is not synthetic';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.institutions
     WHERE id = '00000000-0000-0000-0000-000000000001'
       AND slug = 'ulima'
  ) THEN
    RAISE EXCEPTION 'synthetic pipeline institution is missing';
  END IF;
END;
$$;

INSERT INTO public.categories (id, name)
VALUES ('10000000-0000-0000-0000-000000000001', 'Data');

INSERT INTO public.courses (
  id, institution_id, category_id, name, slug, url, price_pen, price_status,
  mode, duration, category, description_long, syllabus, target_audience,
  requirements, certification, benefits, objectives, start_date, start_date_text,
  course_type, seniority_level, is_active, is_verified, provider_used,
  is_mock_data, created_at, updated_at
) VALUES (
  '70000000-0000-0000-0000-000000000091',
  '00000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'Analítica Aplicada',
  'analitica-aplicada-60000000',
  'https://synthetic.h3.example/programs/analitica-aplicada/',
  1250,
  'publicado',
  'Remoto',
  '6 meses',
  'Data',
  'Formación aplicada en analítica con un proyecto basado en datos sintéticos.',
  'Modelado y comunicación',
  'Profesionales en transición',
  'Conocimientos básicos de hojas de cálculo',
  'Constancia sintética',
  'Proyecto práctico',
  'Modelar datos y comunicar hallazgos',
  DATE '2027-04-01',
  '2027-04-01',
  'Curso',
  'Junior',
  true,
  true,
  'synthetic-provider',
  false,
  now() - INTERVAL '35 days',
  now() - INTERVAL '35 days'
);

INSERT INTO public.course_editorial_state (
  course_id, editorial_status, quality_status, missing_fields, field_sources,
  field_timestamps, availability_status, created_at, updated_at
) VALUES (
  '70000000-0000-0000-0000-000000000091',
  'draft',
  'complete',
  ARRAY[]::TEXT[],
  jsonb_build_object(
    'name', 'pipeline', 'price_pen', 'pipeline', 'price_status', 'pipeline',
    'mode', 'pipeline', 'duration', 'pipeline', 'description_long', 'pipeline',
    'syllabus', 'pipeline', 'target_audience', 'pipeline', 'requirements', 'pipeline',
    'certification', 'pipeline', 'benefits', 'pipeline', 'objectives', 'pipeline',
    'start_date_text', 'pipeline'
  ),
  '{}'::JSONB,
  'unknown',
  now() - INTERVAL '35 days',
  now() - INTERVAL '35 days'
);

DO $$
BEGIN
  IF (SELECT count(*) FROM public.courses
       WHERE id = '70000000-0000-0000-0000-000000000091'
         AND provider_used = 'synthetic-provider'
         AND is_mock_data IS FALSE) <> 1 THEN
    RAISE EXCEPTION 'pipeline output was not bridged into the local course fixture';
  END IF;
  IF (SELECT count(*) FROM public.course_editorial_state
       WHERE course_id = '70000000-0000-0000-0000-000000000091'
         AND editorial_status = 'draft'
         AND availability_status = 'unknown'
         AND cardinality(missing_fields) = 0) <> 1 THEN
    RAISE EXCEPTION 'pipeline editorial fixture did not start unpublished and without availability evidence';
  END IF;
END;
$$;

SELECT 'h3_uat_pipeline_course_seed_ok' AS marker;
