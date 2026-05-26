-- Fase 113: Version RLS policy and sync atomic_enrichment_promote RPC.
-- Closes production drift found after Fase 111.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'institution_site_profiles'
      AND policyname = 'profiles_select_public'
  ) THEN
    CREATE POLICY profiles_select_public ON public.institution_site_profiles
      FOR SELECT TO anon
      USING (true);
  END IF;
END $$;

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
    is_mock_data
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
    (item->>'is_mock_data')::boolean
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

REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) FROM anon;
REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid) TO service_role;
