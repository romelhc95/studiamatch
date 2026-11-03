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

CREATE SCHEMA IF NOT EXISTS private;
GRANT USAGE ON SCHEMA private TO anon, authenticated, service_role;

CREATE TABLE public.h3_public_price_projection_fixture (
  fixture_id TEXT PRIMARY KEY,
  published_editorial_values JSONB,
  manual_overrides JSONB NOT NULL DEFAULT '{}'::JSONB,
  source_price NUMERIC,
  is_strict_public BOOLEAN NOT NULL DEFAULT false
);

CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()
RETURNS TABLE (fixture_id TEXT, price_pen NUMERIC)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $function$
  SELECT c.fixture_id,
         CASE
           WHEN c.is_strict_public AND c.published_editorial_values ? 'price_pen' THEN
             CASE WHEN c.published_editorial_values -> 'price_pen' = 'null'::JSONB THEN NULL
                  ELSE (c.published_editorial_values ->> 'price_pen')::NUMERIC END
           WHEN c.is_strict_public AND c.manual_overrides ->> 'price_pen' ~ '^[0-9]+(\.[0-9]+)?$'
             THEN (c.manual_overrides ->> 'price_pen')::NUMERIC
           ELSE c.source_price
         END
  FROM public.h3_public_price_projection_fixture AS c;
$function$;

REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS SELECT * FROM private.h2_public_courses_effective();
REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;

INSERT INTO public.h3_public_price_projection_fixture
  (fixture_id, published_editorial_values, manual_overrides, source_price, is_strict_public)
VALUES
  ('blank-snapshot-price', '{"price_pen":""}', '{}', 91, true),
  ('numeric-snapshot-price', '{"price_pen":"1234.50"}', '{}', 91, true),
  ('null-snapshot-price', '{"price_pen":null}', '{}', 91, true),
  ('invalid-snapshot-price', '{"price_pen":"not-a-number"}', '{}', 91, true),
  ('max-bounded-snapshot-price', jsonb_build_object('price_pen', repeat('9', 63)), '{}', 91, true),
  ('numeric-overflow-snapshot-price', jsonb_build_object('price_pen', repeat('9', 131073)), '{}', 91, true),
  ('strict-manual-price-without-snapshot', NULL, '{"price_pen":"777"}', 91, true),
  ('legacy-source-price', NULL, '{}', 91, false);
