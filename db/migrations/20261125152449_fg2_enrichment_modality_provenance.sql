-- FG2 modality fix: preserve worker field provenance through the existing
-- atomic enrichment promotion RPC. The metadata column already exists; this
-- migration only expands the RPC payload mapping and keeps old callers valid.
CREATE OR REPLACE FUNCTION public.atomic_enrichment_promote(
  p_enriched_data jsonb,
  p_cleansed_id uuid
)
RETURNS SETOF public.enriched_programs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS
$$
BEGIN
  INSERT INTO public.enriched_programs (
    cleansed_id,
    institution_id,
    url,
    official_name,
    duration_text,
    duration_months,
    total_cost_est,
    requirements,
    graduate_profile,
    curriculum_summary,
    modality,
    primary_campus,
    degree_type,
    start_date,
    partnerships,
    certifications,
    language,
    categories,
    difficulty_level,
    ai_summary,
    status,
    provider_used,
    is_mock_data,
    metadata
  )
  SELECT
    (item->>'cleansed_id')::uuid,
    (item->>'institution_id')::uuid,
    item->>'url',
    item->>'official_name',
    item->>'duration_text',
    COALESCE(NULLIF(item->>'duration_months', '')::numeric, 0)::int,
    NULLIF(item->>'total_cost_est', '')::numeric,
    item->>'requirements',
    item->>'graduate_profile',
    COALESCE(NULLIF(item->>'curriculum_summary', ''), '{}')::jsonb,
    item->>'modality',
    item->>'primary_campus',
    item->>'degree_type',
    item->>'start_date',
    item->>'partnerships',
    item->>'certifications',
    item->>'language',
    item->>'categories',
    item->>'difficulty_level',
    item->>'ai_summary',
    'pending',
    item->>'provider_used',
    (item->>'is_mock_data')::boolean,
    CASE
      WHEN jsonb_typeof(item->'metadata') = 'object' THEN item->'metadata'
      ELSE '{}'::jsonb
    END
  FROM jsonb_array_elements(p_enriched_data) AS item
  ON CONFLICT (cleansed_id) DO UPDATE SET
    official_name = EXCLUDED.official_name,
    duration_text = EXCLUDED.duration_text,
    duration_months = COALESCE(NULLIF(EXCLUDED.duration_months, NULL)::numeric, 0)::int,
    total_cost_est = EXCLUDED.total_cost_est,
    requirements = EXCLUDED.requirements,
    graduate_profile = EXCLUDED.graduate_profile,
    curriculum_summary = EXCLUDED.curriculum_summary,
    modality = EXCLUDED.modality,
    primary_campus = EXCLUDED.primary_campus,
    degree_type = EXCLUDED.degree_type,
    start_date = EXCLUDED.start_date,
    categories = EXCLUDED.categories,
    difficulty_level = EXCLUDED.difficulty_level,
    ai_summary = EXCLUDED.ai_summary,
    provider_used = EXCLUDED.provider_used,
    is_mock_data = EXCLUDED.is_mock_data,
    metadata =
      COALESCE(public.enriched_programs.metadata, '{}'::jsonb)
      || (COALESCE(EXCLUDED.metadata, '{}'::jsonb) - 'field_provenance')
      || CASE
        WHEN jsonb_typeof(public.enriched_programs.metadata->'field_provenance') = 'object'
          OR jsonb_typeof(EXCLUDED.metadata->'field_provenance') = 'object'
        THEN jsonb_build_object(
          'field_provenance',
          (CASE
            WHEN jsonb_typeof(public.enriched_programs.metadata->'field_provenance') = 'object'
            THEN public.enriched_programs.metadata->'field_provenance'
            ELSE '{}'::jsonb
          END)
          ||
          (CASE
            WHEN jsonb_typeof(EXCLUDED.metadata->'field_provenance') = 'object'
            THEN EXCLUDED.metadata->'field_provenance'
            ELSE '{}'::jsonb
          END)
        )
        ELSE '{}'::jsonb
      END,
    status = 'pending';

  UPDATE public.cleansed_programs
  SET status = 'enriched'
  WHERE id = p_cleansed_id
    AND status = 'pending';

  RETURN QUERY
  SELECT *
  FROM public.enriched_programs
  WHERE cleansed_id = p_cleansed_id;
END;
$$;

REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid)
  TO service_role;

COMMENT ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) IS
  'FG2 atomic enrichment promotion. Persists worker metadata, including field_provenance, while retaining the existing service_role-only execution contract.';

-- Read-only verifier used by the protected DB Sync verify operation. It
-- returns function metadata/source only, never application rows.
CREATE OR REPLACE FUNCTION public.fg2_modality_provenance_schema_contract()
RETURNS JSONB
LANGUAGE SQL
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public
AS $function$
WITH target AS (
  SELECT p.*, l.lanname
  FROM pg_catalog.pg_proc AS p
  JOIN pg_catalog.pg_language AS l ON l.oid = p.prolang
  WHERE p.oid = pg_catalog.to_regprocedure('public.atomic_enrichment_promote(jsonb,uuid)')
)
SELECT jsonb_build_object(
  'schema_version', 1,
  'function_count', (SELECT count(*) FROM target),
  'function', (
    SELECT jsonb_build_object(
      'identity_arguments', pg_catalog.pg_get_function_identity_arguments(oid),
      'return_type', pg_catalog.format_type(prorettype, NULL),
      'returns_set', proretset,
      'language', lanname,
      'volatility', provolatile,
      'security_definer', prosecdef,
      'search_path', proconfig,
      'source', prosrc,
      'anon_can_execute', pg_catalog.has_function_privilege('anon', oid, 'EXECUTE'),
      'authenticated_can_execute', pg_catalog.has_function_privilege('authenticated', oid, 'EXECUTE'),
      'service_role_can_execute', pg_catalog.has_function_privilege('service_role', oid, 'EXECUTE')
    )
    FROM target
  ),
  'contract_anon_can_execute', COALESCE(pg_catalog.has_function_privilege(
    'anon', pg_catalog.to_regprocedure('public.fg2_modality_provenance_schema_contract()'), 'EXECUTE'
  ), false),
  'contract_authenticated_can_execute', COALESCE(pg_catalog.has_function_privilege(
    'authenticated', pg_catalog.to_regprocedure('public.fg2_modality_provenance_schema_contract()'), 'EXECUTE'
  ), false),
  'contract_service_role_can_execute', COALESCE(pg_catalog.has_function_privilege(
    'service_role', pg_catalog.to_regprocedure('public.fg2_modality_provenance_schema_contract()'), 'EXECUTE'
  ), false)
)
$function$;

REVOKE ALL ON FUNCTION public.fg2_modality_provenance_schema_contract()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fg2_modality_provenance_schema_contract()
  TO service_role;

COMMENT ON FUNCTION public.fg2_modality_provenance_schema_contract() IS
  'Read-only FG2 modality RPC signature, definition, search_path, and ACL contract for protected DB Sync verification.';
