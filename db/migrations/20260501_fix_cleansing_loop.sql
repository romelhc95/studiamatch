-- Migration: 20260501_fix_cleansing_loop.sql
-- Fase 66: Fix pipeline cleansing infinite loop
--
-- Fix A: lock_staging_records ahora SETEA status='processing' atomically
--        (antes era SELECT-only, requiriendo mark_records_processing() que nunca se llamaba)
-- Fix B: atomic_cleansing_promote acepta status IN ('pending','processing')
--        (antes solo aceptaba 'processing', pero los registros llegaban como 'pending')

BEGIN;

-- Fix A: lock_staging_records con UPDATE...RETURNING atomico
-- Reemplaza la version SELECT-only que dejaba los registros en 'pending'
DROP FUNCTION IF EXISTS public.mark_records_processing(uuid[]);

CREATE OR REPLACE FUNCTION public.lock_staging_records(inst_id uuid, batch_size integer DEFAULT 100)
 RETURNS TABLE(id uuid, url text, institution_id uuid, raw_html text, raw_name text, raw_description text)
 LANGUAGE sql
 SECURITY DEFINER
 SET search_path = public
AS $function$
    UPDATE staging_raw
    SET status = 'processing'
    WHERE id IN (
        SELECT id
        FROM staging_raw
        WHERE status = 'pending'
        AND (institution_id = inst_id OR inst_id IS NULL)
        ORDER BY last_harvested_at ASC NULLS FIRST
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    RETURNING id, url, institution_id, raw_html, raw_name, raw_description;
$function$;

-- Fix B: atomic_cleansing_promote acepta ambos estados
CREATE OR REPLACE FUNCTION public.atomic_cleansing_promote(p_staging_ids uuid[], p_cleansed_data jsonb)
 RETURNS SETOF cleansed_programs
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    INSERT INTO cleansed_programs (
        staging_id, institution_id, url, effective_url, canonical_url,
        clean_name, clean_description, modality, location, base_price,
        currency, status, metadata
    )
    SELECT
        (item->>'staging_id')::UUID,
        (item->>'institution_id')::UUID,
        item->>'url',
        item->>'effective_url',
        item->>'canonical_url',
        item->>'clean_name',
        item->>'clean_description',
        item->>'modality',
        item->>'location',
        (item->>'base_price')::NUMERIC,
        item->>'currency',
        'pending',
        (item->>'metadata')::JSONB
    FROM jsonb_array_elements(p_cleansed_data) AS item
    ON CONFLICT (url) DO UPDATE SET
        clean_name = EXCLUDED.clean_name,
        clean_description = EXCLUDED.clean_description,
        status = 'pending';

    UPDATE staging_raw
    SET status = 'processed'
    WHERE id = ANY(p_staging_ids) AND status IN ('pending', 'processing');

    RETURN QUERY
    SELECT *
    FROM cleansed_programs
    WHERE url IN (
        SELECT item->>'url'
        FROM jsonb_array_elements(p_cleansed_data) AS item
    );
END;
$function$;

COMMIT;
