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
DO $$
DECLARE
  _staging public.staging_raw%ROWTYPE;
  _cleansed public.cleansed_programs%ROWTYPE;
  _enriched public.enriched_programs%ROWTYPE;
  _course public.courses%ROWTYPE;
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.staging_raw
    WHERE id='792b1600-9939-4cf3-95fd-5056d8f5d99c'::uuid
  ) THEN
    SELECT * INTO STRICT _staging
    FROM public.staging_raw
    WHERE id='792b1600-9939-4cf3-95fd-5056d8f5d99c'::uuid
      AND institution_id='50d8779c-54fd-437e-b941-e817e202e60c'::uuid
      AND url='https://posgrado.utec.edu.pe/maestrias/ciencia-de-datos-inteligencia-artificial'
      AND status='processed';
    IF _staging.content_hash IS NULL
       OR _staging.content_hash='f05f5beb61a19d62b65c25530d4eda59ddfce2b8e8ba26c593203fd5a8d963ce' THEN
      RAISE EXCEPTION 'utec_harvest_did_not_replace_synthetic_prior_snapshot';
    END IF;

    SELECT * INTO STRICT _cleansed
    FROM public.cleansed_programs
    WHERE staging_id=_staging.id
      AND institution_id=_staging.institution_id
      AND rtrim(url, '/')=rtrim(_staging.url, '/')
      AND status='enriched';
    IF _cleansed.modality IS DISTINCT FROM 'Híbrido'
       OR _cleansed.metadata #>> '{modality_evidence,source}' IS DISTINCT FROM 'cleansing_text'
       OR _cleansed.metadata #>> '{modality_evidence,value}' IS DISTINCT FROM 'Híbrido'
       OR _cleansed.metadata #>> '{modality_evidence,staging_id}' IS DISTINCT FROM _staging.id::text
       OR _cleansed.metadata #>> '{modality_evidence,institution_id}' IS DISTINCT FROM _staging.institution_id::text
       OR _cleansed.metadata #>> '{modality_evidence,source_content_sha256}' IS DISTINCT FROM _staging.content_hash THEN
      RAISE EXCEPTION 'utec_cleansing_modality_provenance_mismatch';
    END IF;

    SELECT * INTO STRICT _enriched
    FROM public.enriched_programs
    WHERE cleansed_id=_cleansed.id
      AND institution_id=_cleansed.institution_id
      AND rtrim(url, '/')=rtrim(_cleansed.url, '/')
      AND status='synced';
    IF _enriched.modality IS DISTINCT FROM 'Remoto'
       OR _enriched.provider_used IS DISTINCT FROM 'OpenAI'
       OR _enriched.is_mock_data IS TRUE
       OR _enriched.metadata #>> '{field_provenance,modality,source}' IS DISTINCT FROM 'provider'
       OR _enriched.metadata #>> '{field_provenance,modality,value}' IS DISTINCT FROM 'Remoto'
       OR _enriched.metadata #>> '{field_provenance,modality,cleansed_id}' IS DISTINCT FROM _cleansed.id::text
       OR _enriched.metadata #>> '{field_provenance,modality,staging_id}' IS DISTINCT FROM _staging.id::text
       OR _enriched.metadata #>> '{field_provenance,modality,institution_id}' IS DISTINCT FROM _staging.institution_id::text THEN
      RAISE EXCEPTION 'utec_enrichment_modality_provenance_mismatch';
    END IF;

    SELECT * INTO STRICT _course
    FROM public.courses
    WHERE institution_id=_staging.institution_id
      AND rtrim(url, '/')=rtrim(_staging.url, '/');
    IF _course.mode IS DISTINCT FROM 'Remoto'
       OR _course.provider_used IS DISTINCT FROM 'OpenAI'
       OR _course.is_mock_data IS TRUE
       OR NOT EXISTS (
         SELECT 1 FROM public.course_editorial_state es
         WHERE es.course_id=_course.id AND es.editorial_status='pending_review'
       )
       OR EXISTS (
         SELECT 1 FROM public.courses_public_effective effective WHERE effective.id=_course.id
       ) THEN
      RAISE EXCEPTION 'utec_sync_editorial_or_publication_gate_mismatch';
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM public.course_editorial_state es
      JOIN public.courses existing ON existing.id=es.course_id
      WHERE rtrim(existing.url, '/')='https://ssr.fg2.example/programas/analitica-aplicada'
        AND es.editorial_status='published'
        AND es.manual_overrides->>'name'='Título manual sintético preservado'
        AND es.manual_overrides->>'mode'='Híbrido'
    ) THEN
      RAISE EXCEPTION 'preexisting_editorial_override_was_not_preserved';
    END IF;
    RAISE NOTICE 'phase=utec_reviewed_exact_pg17_postflight|result=PASS|harvest=processed|cleansing=Hibrido_with_identity_evidence|enrichment=Remoto_provider_provenance|sync=course_pending_review|public_effective=0|existing_editorial_override=preserved';
  END IF;
END $$;
