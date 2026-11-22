\set ON_ERROR_STOP on
DO $$
DECLARE
  _course_id uuid;
BEGIN
  SELECT id INTO STRICT _course_id
  FROM public.courses
  WHERE institution_id = '20000000-0000-0000-0000-000000000001'
    AND rtrim(url, '/') = 'https://ssr.fg2.example/programas/analitica-aplicada';
  UPDATE public.course_editorial_state
  SET editorial_status = 'published',
      quality_status = 'complete',
      manual_overrides = jsonb_build_object('name', 'Título manual sintético preservado'),
      field_sources = COALESCE(field_sources, '{}'::jsonb) || jsonb_build_object('name', 'manual_override'),
      field_timestamps = COALESCE(field_timestamps, '{}'::jsonb) || jsonb_build_object('name', now()),
      manual_updated_at = now(),
      manual_updated_by = '30000000-0000-0000-0000-000000000001',
      published_at = now()
  WHERE course_id = _course_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'fixture editorial row missing';
  END IF;
END $$;
