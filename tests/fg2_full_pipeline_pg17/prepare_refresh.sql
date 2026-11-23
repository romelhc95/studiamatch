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

-- Pending work outside the reviewed URL is a sentinel for the delegated
-- cleansing/enrichment/sync consumers; they must leave it untouched.
INSERT INTO public.staging_raw (
  id, institution_id, url, raw_name, raw_html, status, content_hash, metadata
)
VALUES (
  '40000000-0000-0000-0000-000000000009',
  '20000000-0000-0000-0000-000000000001',
  'https://ssr.fg2.example/programas/outside-approved-cohort',
  'Synthetic out-of-cohort sentinel',
  '<html><body>outside approved cohort</body></html>',
  'pending',
  repeat('c', 64),
  '{}'::jsonb
);

-- The approved-lot refresh fixture targets the already-synced course above.
-- It does not discover or add a course; its ordered hardcoded seed is the
-- exact existing processed URL under test.
UPDATE public.institution_site_profiles
SET discovery_mode = 'hardcoded_urls',
    seed_urls = jsonb_build_array('https://ssr.fg2.example/programas/analitica-aplicada')
WHERE institution_id = '20000000-0000-0000-0000-000000000001';
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.institution_site_profiles
    WHERE institution_id = '20000000-0000-0000-0000-000000000001'
      AND discovery_mode = 'hardcoded_urls'
      AND seed_urls = jsonb_build_array('https://ssr.fg2.example/programas/analitica-aplicada')
  ) THEN
    RAISE EXCEPTION 'refresh fixture profile missing';
  END IF;
END $$;
