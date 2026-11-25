\set ON_ERROR_STOP on

-- Synthetic post-#272 state: five proposed refreshes are pending at
-- enrichment, the sixth course has an ambiguous staging alias, and two rows
-- are unchanged. No real institution URL or database is used.
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

-- The sixth identity has a second stored trailing-slash alias. Its distinct
-- staging ID and exact downstream foreign keys are intentionally retained so
-- the recovery preflight proves ambiguity and excludes it without deletion.
INSERT INTO public.staging_raw (
  id, institution_id, url, raw_name, raw_description, raw_html, status,
  content_hash, effective_url, canonical_url, metadata
)
VALUES (
  '52000000-0000-0000-0000-000000000066'::uuid,
  '20000000-0000-0000-0000-000000000001'::uuid,
  'https://ssr.fg2.example/programas/post272-refresh-06/',
  'Post-272 recovered course 06', 'Synthetic alias row',
  '<!doctype html><html><body><h1>Ambiguous alias</h1></body></html>',
  'processed',
  encode(digest('<!doctype html><html><body><h1>Ambiguous alias</h1></body></html>', 'sha256'), 'hex'),
  'https://ssr.fg2.example/programas/post272-refresh-06/',
  'https://ssr.fg2.example/programas/post272-refresh-06/',
  jsonb_build_object('fixture_case', 'post272_ambiguous_alias')
);

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

INSERT INTO public.cleansed_programs (
  id, staging_id, institution_id, url, effective_url, canonical_url,
  clean_name, clean_description, modality, status, metadata
)
VALUES (
  '54000000-0000-0000-0000-000000000066'::uuid,
  '52000000-0000-0000-0000-000000000066'::uuid,
  '20000000-0000-0000-0000-000000000001'::uuid,
  'https://ssr.fg2.example/programas/post272-refresh-06/',
  'https://ssr.fg2.example/programas/post272-refresh-06/',
  'https://ssr.fg2.example/programas/post272-refresh-06/',
  'Ambiguous alias row', 'Synthetic duplicate identity', 'Online', 'pending',
  jsonb_build_object('fixture_case', 'post272_ambiguous_alias')
);

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

INSERT INTO public.enriched_programs (
  id, cleansed_id, institution_id, url, official_name, status,
  provider_used, is_mock_data, metadata
)
VALUES (
  '55000000-0000-0000-0000-000000000066'::uuid,
  '54000000-0000-0000-0000-000000000066'::uuid,
  '20000000-0000-0000-0000-000000000001'::uuid,
  'https://ssr.fg2.example/programas/post272-refresh-06/',
  'Ambiguous alias row', 'synced', 'prior-fixture', false,
  jsonb_build_object('fixture_case', 'post272_ambiguous_alias')
);

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

-- Local fault switch for the recovery E2E. The first scoped enrichment write
-- can be failed deterministically; no trigger exists in product migrations.
CREATE TABLE public.fg2_recovery_fault_switch (
  singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  fail_next_enrichment boolean NOT NULL DEFAULT false
);
INSERT INTO public.fg2_recovery_fault_switch (singleton, fail_next_enrichment)
VALUES (true, false);
CREATE OR REPLACE FUNCTION public.fg2_fixture_fail_recovery_enrichment()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  _fail boolean;
BEGIN
  IF rtrim(NEW.url, '/') = 'https://ssr.fg2.example/programas/post272-refresh-01' THEN
    SELECT fail_next_enrichment INTO _fail
    FROM public.fg2_recovery_fault_switch WHERE singleton=true FOR UPDATE;
    IF _fail THEN
      UPDATE public.fg2_recovery_fault_switch
      SET fail_next_enrichment=false WHERE singleton=true;
      RAISE EXCEPTION 'synthetic_recovery_enrichment_write_failure';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER fg2_fixture_recovery_enrichment_fault
  BEFORE INSERT OR UPDATE ON public.enriched_programs
  FOR EACH ROW EXECUTE FUNCTION public.fg2_fixture_fail_recovery_enrichment();

DO $$
BEGIN
  IF (SELECT count(*) FROM public.staging_raw WHERE id::text LIKE '52000000-0000-0000-0000-%') <> 9
     OR (SELECT count(*) FROM public.cleansed_programs WHERE id::text LIKE '54000000-0000-0000-0000-%' AND status='pending') <> 7
     OR (SELECT count(*) FROM public.cleansed_programs WHERE id::text LIKE '54000000-0000-0000-0000-%' AND status='synced') <> 2
     OR (SELECT count(*) FROM public.enriched_programs WHERE id::text LIKE '55000000-0000-0000-0000-%' AND status='synced') <> 9 THEN
    RAISE EXCEPTION 'post272_fixture_state_mismatch';
  END IF;
END $$;
SELECT 'phase=post272_recovery_fixture|result=PASS|refresh_pending=5|ambiguous_excluded=1|unchanged_excluded=2|synthetic_only=true';
