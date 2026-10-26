-- H3REQ1: keep the onboarding reader's active-admin rejection distinct from
-- service failure after the quota wrapper catches the private base function.
-- Preserve the public signature, wrapper, grants, and quota admission.
BEGIN;

DO $$
DECLARE
  base_function REGPROCEDURE;
  public_wrapper REGPROCEDURE;
  base_source TEXT;
  wrapper_source TEXT;
  function_definition TEXT;
  old_guard CONSTANT TEXT := 'RAISE EXCEPTION ''User is not an active admin'';';
  new_guard CONSTANT TEXT := 'RAISE SQLSTATE ''42501'' USING MESSAGE = ''User is not an active admin'';';
  old_occurrences INTEGER;
  new_occurrences INTEGER;
BEGIN
  base_function := pg_catalog.to_regprocedure(
    'private.h3_quota_base_admin_list_members_onboarding()'
  );
  public_wrapper := pg_catalog.to_regprocedure(
    'public.admin_list_members_onboarding()'
  );
  IF base_function IS NULL OR public_wrapper IS NULL THEN
    RAISE EXCEPTION 'Onboarding quota base/wrapper is missing; refusing role-denial migration';
  END IF;

  SELECT p.prosrc INTO base_source
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = base_function;
  SELECT p.prosrc INTO wrapper_source
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = public_wrapper;

  IF base_source IS NULL OR wrapper_source IS NULL
     OR pg_catalog.strpos(wrapper_source, 'H3_QUOTA_WRAPPER_V1') = 0
     OR pg_catalog.strpos(wrapper_source, 'WHEN SQLSTATE=''42501'' THEN ''403''') = 0
     OR pg_catalog.strpos(base_source, 'H3_QUOTA_WRAPPER_V1') > 0 THEN
    RAISE EXCEPTION 'Onboarding quota wrapper drift; refusing role-denial migration';
  END IF;

  old_occurrences := (
    pg_catalog.length(base_source)
    - pg_catalog.length(pg_catalog.replace(base_source, old_guard, ''))
  ) / pg_catalog.length(old_guard);
  new_occurrences := (
    pg_catalog.length(base_source)
    - pg_catalog.length(pg_catalog.replace(base_source, new_guard, ''))
  ) / pg_catalog.length(new_guard);

  IF old_occurrences = 0 AND new_occurrences = 1 THEN
    RETURN;
  END IF;
  IF old_occurrences <> 1 OR new_occurrences <> 0 THEN
    RAISE EXCEPTION 'Onboarding active-admin guard drift; expected one exact legacy guard';
  END IF;

  SELECT pg_catalog.pg_get_functiondef(base_function) INTO function_definition;
  function_definition := pg_catalog.replace(function_definition, old_guard, new_guard);
  IF pg_catalog.strpos(function_definition, new_guard) = 0
     OR pg_catalog.strpos(function_definition, old_guard) > 0 THEN
    RAISE EXCEPTION 'Unable to construct the bounded onboarding role-denial function';
  END IF;

  -- The definition comes from the fixed private RPC signature; no caller input
  -- or operational data participates in this one-function DDL replacement.
  EXECUTE function_definition;

  SELECT p.prosrc INTO base_source
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = base_function;
  IF pg_catalog.strpos(base_source, new_guard) = 0
     OR pg_catalog.strpos(base_source, old_guard) > 0 THEN
    RAISE EXCEPTION 'Onboarding active-admin guard postflight failed';
  END IF;
END;
$$;

COMMIT;
