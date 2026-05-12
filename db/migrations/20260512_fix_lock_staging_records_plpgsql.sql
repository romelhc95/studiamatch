-- Migration: 20260512_fix_lock_staging_records_plpgsql
-- Fix RPC lock_staging_records: migrate to plpgsql and fully qualify columns.

CREATE OR REPLACE FUNCTION public.lock_staging_records(inst_id uuid, batch_size integer DEFAULT 100)
RETURNS TABLE(id uuid, url text, institution_id uuid, raw_html text, raw_name text, raw_description text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $function$
BEGIN
    RETURN QUERY
    UPDATE staging_raw
    SET status = 'processing'
    WHERE staging_raw.id IN (
        SELECT sub.id
        FROM staging_raw AS sub
        WHERE sub.status = 'pending'
          AND (sub.institution_id = inst_id OR inst_id IS NULL)
        ORDER BY sub.last_harvested_at ASC NULLS FIRST
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    RETURNING
        staging_raw.id,
        staging_raw.url,
        staging_raw.institution_id,
        staging_raw.raw_html,
        staging_raw.raw_name,
        staging_raw.raw_description;
END;
$function$;
