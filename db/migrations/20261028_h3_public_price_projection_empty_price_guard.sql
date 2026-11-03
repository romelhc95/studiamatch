-- H3REQ1 forward fix: a blank or malformed published price must not make the
-- entire public course projection fail with 22P02.
DO $migration$
DECLARE
  _definition TEXT;
  _unsafe_cast CONSTANT TEXT := $unsafe$(c.published_editorial_values ->> 'price_pen')::NUMERIC$unsafe$;
  _safe_cast CONSTANT TEXT := $safe$CASE
                 WHEN NULLIF(BTRIM(c.published_editorial_values ->> 'price_pen'), '') ~ '^[0-9]{1,63}(\.[0-9]{1,63})?$'
                   THEN NULLIF(BTRIM(c.published_editorial_values ->> 'price_pen'), '')::NUMERIC
                 ELSE NULL
               END$safe$;
  _occurrences INTEGER;
BEGIN
  SELECT pg_catalog.pg_get_functiondef(
           'private.h2_public_courses_effective()'::pg_catalog.regprocedure
         )
    INTO _definition;

  IF _definition IS NULL THEN
    RAISE EXCEPTION 'H3 public price guard requires private.h2_public_courses_effective()';
  END IF;

  IF pg_catalog.strpos(_definition, _safe_cast) > 0 THEN
    RETURN;
  END IF;

  _occurrences := (
    pg_catalog.length(_definition)
    - pg_catalog.length(pg_catalog.replace(_definition, _unsafe_cast, ''))
  ) / pg_catalog.length(_unsafe_cast);

  IF _occurrences <> 1 THEN
    RAISE EXCEPTION 'H3 public price guard expected one known cast, found %', _occurrences;
  END IF;

  EXECUTE pg_catalog.replace(_definition, _unsafe_cast, _safe_cast);
END;
$migration$;

REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;
