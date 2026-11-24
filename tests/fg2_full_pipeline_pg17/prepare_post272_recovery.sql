\set ON_ERROR_STOP on

-- Synthetic state equivalent to the point after a successful harvest and
-- cleansing followed by an enrichment interruption: six reviewed refreshes
-- are pending at enrichment, while two processed identities are unchanged.
WITH items AS (
  SELECT
    n,
    'https://ssr.fg2.example/programas/post272-refresh-' || lpad(n::text, 2, '0') AS url,
    format(
      '<!doctype html><html><body><h1>Post-272 recovered course %s</h1><p>Updated synthetic source content for recovery.</p></body></html>',
      lpad(n::text, 2, '0')
    ) AS raw_html
  FROM generate_series(1, 8) AS n
)
INSERT INTO public.staging_raw (
  id, institution_id, url, raw_name, raw_description, raw_html, status,
  content_hash, effective_url, canonical_url, metadata
)
SELECT
  ('52000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
  '20000000-0000-0000-0000-000000000001'::uuid,
  url,
  'Post-272 recovered course ' || lpad(n::text, 2, '0'),
  'Synthetic recovered source description',
  raw_html,
  'processed',
  encode(digest(raw_html, 'sha256'), 'hex'),
  url,
  url,
  jsonb_build_object('fixture_case', 'post272_recovery', 'ordinal', n)
FROM items;

WITH items AS (
  SELECT
    n,
    ('52000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid AS staging_id,
    'https://ssr.fg2.example/programas/post272-refresh-' || lpad(n::text, 2, '0') AS url
  FROM generate_series(1, 8) AS n
)
INSERT INTO public.courses (
  id, institution_id, name, slug, url, mode, duration, description_long,
  provider_used, is_mock_data, is_active, is_verified, updated_at
)
SELECT
  ('53000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
  '20000000-0000-0000-0000-000000000001'::uuid,
  'Original recovery title ' || lpad(n::text, 2, '0'),
  'post272-recovery-' || lpad(n::text, 2, '0'),
  url,
  'Online',
  '6 meses',
  'Original synthetic course description',
  'prior-fixture',
  false,
  false,
  false,
  '2026-11-22T00:00:00Z'::timestamptz
FROM items;

WITH items AS (
  SELECT
    n,
    ('52000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid AS staging_id,
    'https://ssr.fg2.example/programas/post272-refresh-' || lpad(n::text, 2, '0') AS url
  FROM generate_series(1, 8) AS n
)
INSERT INTO public.cleansed_programs (
  id, staging_id, institution_id, url, effective_url, canonical_url,
  clean_name, clean_description, modality, status, metadata
)
SELECT
  ('54000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
  staging_id,
  '20000000-0000-0000-0000-000000000001'::uuid,
  url,
  url,
  url,
  'Post-272 recovered course ' || lpad(n::text, 2, '0'),
  'Updated synthetic course text prepared by the completed cleansing stage.',
  'Online',
  CASE WHEN n <= 6 THEN 'pending' ELSE 'synced' END,
  jsonb_build_object('fixture_case', 'post272_recovery', 'ordinal', n)
FROM items;

WITH items AS (
  SELECT
    n,
    ('54000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid AS cleansed_id,
    'https://ssr.fg2.example/programas/post272-refresh-' || lpad(n::text, 2, '0') AS url
  FROM generate_series(1, 8) AS n
)
INSERT INTO public.enriched_programs (
  id, cleansed_id, institution_id, url, official_name, duration_text,
  duration_months, total_cost_est, requirements, graduate_profile,
  curriculum_summary, modality, degree_type, start_date, categories,
  ai_summary, status, provider_used, is_mock_data, metadata
)
SELECT
  ('55000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
  cleansed_id,
  '20000000-0000-0000-0000-000000000001'::uuid,
  url,
  'Original recovery title ' || lpad(n::text, 2, '0'),
  '6 meses',
  6,
  900,
  'Original synthetic requirement',
  'Original synthetic profile',
  '[]'::jsonb,
  'Online',
  'Certificado',
  '2027-01-01',
  '[]',
  'Original synthetic summary',
  'synced',
  'prior-fixture',
  false,
  jsonb_build_object('fixture_case', 'post272_recovery', 'ordinal', n)
FROM items;

INSERT INTO public.course_editorial_state (
  course_id, editorial_status, quality_status, manual_overrides,
  field_sources, manual_updated_at, manual_updated_by
)
SELECT
  ('53000000-0000-0000-0000-' || lpad(n::text, 12, '0'))::uuid,
  'pending_review',
  'pending',
  CASE WHEN n = 1 THEN jsonb_build_object('name', 'Manual recovery title preserved') ELSE '{}'::jsonb END,
  CASE WHEN n = 1 THEN jsonb_build_object('name', 'manual_override') ELSE '{}'::jsonb END,
  CASE WHEN n = 1 THEN '2026-11-22T00:00:00Z'::timestamptz ELSE NULL END,
  CASE WHEN n = 1 THEN '30000000-0000-0000-0000-000000000001'::uuid ELSE NULL END
FROM generate_series(1, 8) AS n;

DO $$
BEGIN
  IF (SELECT count(*) FROM public.staging_raw WHERE id::text LIKE '52000000-0000-0000-0000-%') <> 8
     OR (SELECT count(*) FROM public.cleansed_programs WHERE id::text LIKE '54000000-0000-0000-0000-%' AND status='pending') <> 6
     OR (SELECT count(*) FROM public.cleansed_programs WHERE id::text LIKE '54000000-0000-0000-0000-%' AND status='synced') <> 2
     OR (SELECT count(*) FROM public.enriched_programs WHERE id::text LIKE '55000000-0000-0000-0000-%' AND status='synced') <> 8 THEN
    RAISE EXCEPTION 'post272_fixture_state_mismatch';
  END IF;
END $$;
SELECT 'phase=post272_recovery_fixture|result=PASS|refresh_pending=6|unchanged_excluded=2|synthetic_only=true';
