\set ON_ERROR_STOP on

DO $$
DECLARE
  contract JSONB;
BEGIN
  contract := public.fg2_modality_provenance_schema_contract();
  IF contract->>'schema_version' <> '1'
     OR contract->>'function_count' <> '1'
     OR contract->>'contract_anon_can_execute' <> 'false'
     OR contract->>'contract_authenticated_can_execute' <> 'false'
     OR contract->>'contract_service_role_can_execute' <> 'true'
     OR contract->'function'->>'identity_arguments' <> 'p_enriched_data jsonb, p_cleansed_id uuid'
     OR contract->'function'->>'language' <> 'plpgsql'
     OR contract->'function'->>'volatility' <> 'v'
     OR contract->'function'->>'security_definer' <> 'true'
     OR contract->'function'->'search_path' <> '["search_path=pg_catalog, public"]'::jsonb
     OR contract->'function'->>'anon_can_execute' <> 'false'
     OR contract->'function'->>'authenticated_can_execute' <> 'false'
     OR contract->'function'->>'service_role_can_execute' <> 'true'
     OR contract->'function'->>'source' NOT LIKE '%field_provenance%' THEN
    RAISE EXCEPTION 'FG2 modality migration contract mismatch';
  END IF;
END;
$$;
DO $$
DECLARE
  _expected_staging integer := current_setting('fg2.fixture_expected_staging')::integer;
  _expected_cleansed integer := current_setting('fg2.fixture_expected_cleansed')::integer;
  _expected_enriched integer := current_setting('fg2.fixture_expected_enriched')::integer;
  _expected_courses integer := current_setting('fg2.fixture_expected_courses')::integer;
  _mode text;
  _enriched_modality text;
  _modality_source text;
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

  IF _expected_courses >= 6 THEN
    IF NOT EXISTS (
      SELECT 1
      FROM public.courses c
      JOIN public.enriched_programs e ON e.url = c.url
      WHERE rtrim(c.url, '/') = 'https://ssr.fg2.example/programas/gestion-datos'
        AND c.mode = 'Remoto'
        AND e.modality = 'Remoto'
        AND e.metadata #>> '{field_provenance,modality,source}' = 'provider'
    ) THEN
      SELECT c.mode, e.modality,
             e.metadata #>> '{field_provenance,modality,source}'
        INTO _mode, _enriched_modality, _modality_source
      FROM public.courses c
      JOIN public.enriched_programs e ON e.url = c.url
      WHERE rtrim(c.url, '/') = 'https://ssr.fg2.example/programas/gestion-datos'
      LIMIT 1;
      RAISE EXCEPTION 'valid_provider_modality_did_not_win mode=% enriched=% source=%',
        COALESCE(_mode, '<NULL>'), COALESCE(_enriched_modality, '<NULL>'),
        COALESCE(_modality_source, '<NULL>');
    END IF;

    IF NOT EXISTS (
      SELECT 1
      FROM public.courses c
      JOIN public.enriched_programs e ON e.url = c.url
      WHERE rtrim(c.url, '/') = 'https://spa.fg2.example/programas/diseno-digital'
        AND c.mode = 'Hibrido'
        AND e.modality = 'Híbrido'
        AND e.metadata #>> '{field_provenance,modality,source}' = 'cleansed_programs'
    ) THEN
      RAISE EXCEPTION 'hybrid_cleansing_modality_did_not_reach_courses';
    END IF;

    IF NOT EXISTS (
      SELECT 1
      FROM public.courses c
      JOIN public.enriched_programs e ON e.url = c.url
      WHERE rtrim(c.url, '/') = 'https://ecommerce.fg2.example/programas/marketing-digital'
        AND c.mode = 'Presencial'
        AND e.modality = 'Presencial'
        AND e.metadata #>> '{field_provenance,modality,source}' = 'cleansed_programs'
    ) THEN
      RAISE EXCEPTION 'in_person_cleansing_modality_did_not_reach_courses';
    END IF;

    IF NOT EXISTS (
      SELECT 1
      FROM public.courses c
      JOIN public.enriched_programs e ON e.url = c.url
      JOIN public.course_editorial_state es ON es.course_id = c.id
      WHERE rtrim(c.url, '/') = 'https://ecommerce.fg2.example/programas/gestion-productos'
        AND c.mode IS NULL
        AND e.modality IS NULL
        AND e.metadata #>> '{field_provenance,modality,source}' = 'unavailable'
        AND es.quality_status = 'pending'
        AND array_position(es.missing_fields, 'mode') IS NOT NULL
    ) THEN
      RAISE EXCEPTION 'missing_modality_must_remain_pending';
    END IF;
  END IF;
END $$;
