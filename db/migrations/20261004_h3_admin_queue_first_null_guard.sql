-- H3REQ1: forward-only guard for deployments where the original queue migration
-- is already recorded as applied. Preserve a quota wrapper when one is installed
-- by patching only its private original-function snapshot.
BEGIN;

DO $$
DECLARE
  target_function REGPROCEDURE;
  function_source TEXT;
  function_definition TEXT;
  old_guard CONSTANT TEXT := 'IF p_first < 1 OR p_first > 100 THEN';
  new_guard CONSTANT TEXT := 'IF p_first IS NULL OR p_first < 1 OR p_first > 100 THEN';
  old_occurrences INTEGER;
  new_occurrences INTEGER;
BEGIN
  target_function := pg_catalog.to_regprocedure(
    'public.admin_get_course_queue_filtered(integer,text,text,text,text)'
  );
  IF target_function IS NULL THEN
    RAISE EXCEPTION 'Queue page-size RPC is missing; refusing null-limit guard migration';
  END IF;

  SELECT p.prosrc INTO function_source
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = target_function;

  IF pg_catalog.strpos(function_source, 'H3_QUOTA_WRAPPER_V1') > 0 THEN
    target_function := pg_catalog.to_regprocedure(
      'private.h3_quota_base_admin_get_course_queue_filtered(integer,text,text,text,text)'
    );
    IF target_function IS NULL THEN
      RAISE EXCEPTION 'Quota queue snapshot is missing; refusing to replace the public wrapper';
    END IF;
    SELECT p.prosrc INTO function_source
    FROM pg_catalog.pg_proc AS p
    WHERE p.oid = target_function;
  END IF;

  IF function_source IS NULL THEN
    RAISE EXCEPTION 'Queue page-size function source is unavailable';
  END IF;

  old_occurrences := (
    pg_catalog.length(function_source)
    - pg_catalog.length(pg_catalog.replace(function_source, old_guard, ''))
  ) / pg_catalog.length(old_guard);
  new_occurrences := (
    pg_catalog.length(function_source)
    - pg_catalog.length(pg_catalog.replace(function_source, new_guard, ''))
  ) / pg_catalog.length(new_guard);

  IF new_occurrences = 1 AND old_occurrences = 0 THEN
    RETURN;
  END IF;
  IF old_occurrences <> 1 OR new_occurrences <> 0 THEN
    RAISE EXCEPTION 'Queue page-size function source drift; expected exactly one legacy guard';
  END IF;

  SELECT pg_catalog.pg_get_functiondef(target_function) INTO function_definition;
  function_definition := pg_catalog.replace(function_definition, old_guard, new_guard);
  IF pg_catalog.strpos(function_definition, new_guard) = 0
     OR pg_catalog.strpos(function_definition, old_guard) > 0 THEN
    RAISE EXCEPTION 'Unable to construct the bounded queue page-size function';
  END IF;

  -- The definition is read from the exact, fixed RPC signature above; no caller
  -- supplied values enter this one-time migration DDL.
  EXECUTE function_definition;
END;
$$;

COMMIT;
