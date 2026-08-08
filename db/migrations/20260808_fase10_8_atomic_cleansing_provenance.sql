-- F10.8: preserve cleansing canary provenance on URL conflicts.
--
-- Production Canary run 31236936740 showed that atomic_cleansing_promote
-- requeued existing cleansed_programs rows but kept their old metadata, so the
-- post-RPC provenance check could not find f10_production_canary_run_id.

CREATE OR REPLACE FUNCTION public.atomic_cleansing_promote(
  p_staging_ids uuid[],
  p_cleansed_data jsonb
)
RETURNS SETOF public.cleansed_programs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
BEGIN
  INSERT INTO public.cleansed_programs AS target (
    staging_id,
    institution_id,
    url,
    effective_url,
    canonical_url,
    clean_name,
    clean_description,
    modality,
    location,
    base_price,
    currency,
    status,
    metadata
  )
  SELECT
    (item->>'staging_id')::uuid,
    (item->>'institution_id')::uuid,
    item->>'url',
    item->>'effective_url',
    item->>'canonical_url',
    item->>'clean_name',
    item->>'clean_description',
    item->>'modality',
    item->>'location',
    NULLIF(item->>'base_price', '')::numeric,
    item->>'currency',
    'pending',
    COALESCE(item->'metadata', '{}'::jsonb)
  FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
  ON CONFLICT (url) DO UPDATE SET
    staging_id = EXCLUDED.staging_id,
    effective_url = EXCLUDED.effective_url,
    canonical_url = EXCLUDED.canonical_url,
    clean_name = EXCLUDED.clean_name,
    clean_description = EXCLUDED.clean_description,
    modality = EXCLUDED.modality,
    location = EXCLUDED.location,
    base_price = EXCLUDED.base_price,
    currency = EXCLUDED.currency,
    status = 'pending',
    metadata =
      COALESCE(target.metadata, '{}'::jsonb)
      || COALESCE(EXCLUDED.metadata, '{}'::jsonb);

  UPDATE public.staging_raw
  SET status = 'processed'
  WHERE id = ANY(p_staging_ids)
    AND status IN ('pending', 'processing');

  RETURN QUERY
  SELECT refreshed.*
  FROM public.cleansed_programs AS refreshed
  WHERE refreshed.url IN (
    SELECT item->>'url'
    FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
  );
END;
$$;

REVOKE ALL ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) FROM anon;
REVOKE ALL ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) TO service_role;
