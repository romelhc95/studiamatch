\set ON_ERROR_STOP on
CREATE SEQUENCE IF NOT EXISTS public.fg2_fixture_cleansing_fault_seq;
CREATE OR REPLACE FUNCTION public.fg2_fixture_cleansing_fault()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF nextval('public.fg2_fixture_cleansing_fault_seq') = 1 THEN
    RAISE EXCEPTION 'synthetic one-shot fixture fault';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS fg2_fixture_cleansing_fault ON public.cleansed_programs;
CREATE TRIGGER fg2_fixture_cleansing_fault
  BEFORE INSERT OR UPDATE ON public.cleansed_programs
  FOR EACH ROW EXECUTE FUNCTION public.fg2_fixture_cleansing_fault();
SELECT setval('public.fg2_fixture_cleansing_fault_seq', 1, false);
