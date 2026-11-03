\set ON_ERROR_STOP on

DO $$
DECLARE
  _actual NUMERIC;
  _is_security_definer BOOLEAN;
  _function_config TEXT[];
BEGIN
  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'blank-snapshot-price';
  IF _actual IS NOT NULL THEN
    RAISE EXCEPTION 'blank published price must project as NULL, got %', _actual;
  END IF;

  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'numeric-snapshot-price';
  IF _actual IS DISTINCT FROM 1234.50::NUMERIC THEN
    RAISE EXCEPTION 'valid published price changed: %', _actual;
  END IF;

  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'null-snapshot-price';
  IF _actual IS NOT NULL THEN
    RAISE EXCEPTION 'JSON null published price must project as SQL NULL, got %', _actual;
  END IF;

  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'invalid-snapshot-price';
  IF _actual IS NOT NULL THEN
    RAISE EXCEPTION 'invalid published price must not break the public projection, got %', _actual;
  END IF;

  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'max-bounded-snapshot-price';
  IF _actual IS DISTINCT FROM repeat('9', 63)::NUMERIC THEN
    RAISE EXCEPTION 'bounded numeric price changed: %', _actual;
  END IF;

  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'numeric-overflow-snapshot-price';
  IF _actual IS NOT NULL THEN
    RAISE EXCEPTION 'oversized published price must not break the public projection';
  END IF;

  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'strict-manual-price-without-snapshot';
  IF _actual IS DISTINCT FROM 777::NUMERIC THEN
    RAISE EXCEPTION 'legacy manual price changed: %', _actual;
  END IF;

  SELECT price_pen INTO _actual FROM public.courses_public_effective WHERE fixture_id = 'legacy-source-price';
  IF _actual IS DISTINCT FROM 91::NUMERIC THEN
    RAISE EXCEPTION 'legacy source price changed: %', _actual;
  END IF;

  IF NOT has_function_privilege('anon', 'private.h2_public_courses_effective()', 'EXECUTE')
     OR NOT has_table_privilege('anon', 'public.courses_public_effective', 'SELECT') THEN
    RAISE EXCEPTION 'public read grants were not preserved';
  END IF;

  SELECT p.prosecdef, p.proconfig
    INTO _is_security_definer, _function_config
    FROM pg_catalog.pg_proc AS p
   WHERE p.oid = 'private.h2_public_courses_effective()'::pg_catalog.regprocedure;
  IF _is_security_definer IS DISTINCT FROM true
     OR NOT ('search_path=pg_catalog, pg_temp' = ANY(_function_config)) THEN
    RAISE EXCEPTION 'reader security-definer/search-path contract changed';
  END IF;

  IF EXISTS (
    SELECT 1
      FROM pg_catalog.pg_proc AS p
      CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) AS acl
     WHERE p.oid = 'private.h2_public_courses_effective()'::pg_catalog.regprocedure
       AND acl.grantee = 0
       AND acl.privilege_type = 'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'PUBLIC retains direct execute on private reader';
  END IF;
END;
$$;

SET ROLE anon;
SELECT count(*) AS public_fixture_rows FROM public.courses_public_effective;
RESET ROLE;

SELECT 'h3_public_price_projection_pg17_ok' AS result;
