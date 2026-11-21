\set ON_ERROR_STOP on
DO $$
DECLARE
  _expected_staging integer := current_setting('fg2.fixture_expected_staging')::integer;
  _expected_cleansed integer := current_setting('fg2.fixture_expected_cleansed')::integer;
  _expected_enriched integer := current_setting('fg2.fixture_expected_enriched')::integer;
  _expected_courses integer := current_setting('fg2.fixture_expected_courses')::integer;
BEGIN
  IF (SELECT count(*) FROM public.staging_raw) <> _expected_staging THEN
    RAISE EXCEPTION 'fixture staging count mismatch';
  END IF;
  IF (SELECT count(*) FROM public.cleansed_programs) <> _expected_cleansed THEN
    RAISE EXCEPTION 'fixture cleansed count mismatch';
  END IF;
  IF (SELECT count(*) FROM public.enriched_programs) <> _expected_enriched THEN
    RAISE EXCEPTION 'fixture enriched count mismatch';
  END IF;
  IF (SELECT count(*) FROM public.courses) <> _expected_courses THEN
    RAISE EXCEPTION 'fixture courses count mismatch';
  END IF;
END $$;
