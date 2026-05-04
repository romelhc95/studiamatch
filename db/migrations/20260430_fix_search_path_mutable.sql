-- ============================================================
-- Migration: Fix function_search_path_mutable — Fase 32A (Prioridad 2)
-- Project: StudIAMatch (Dev Free: YOUR_FREE_PROJECT_REF)
-- Date: 2026-04-30
-- Description: Agrega SET search_path = public a 8 funciones RPC
--   para eliminar los 8 warnings del Supabase Advisor.
-- ============================================================

-- 1. lock_staging_records(inst_id uuid, batch_size integer DEFAULT 100)
CREATE OR REPLACE FUNCTION public.lock_staging_records(inst_id uuid, batch_size integer DEFAULT 100)
 RETURNS TABLE(id uuid, url text, institution_id uuid, raw_html text, raw_name text, raw_description text)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    RETURN QUERY
    WITH updated AS (
        UPDATE staging_raw
        SET status = 'processing',
            metadata = jsonb_set(
                COALESCE(staging_raw.metadata, '{}'::jsonb),
                '{locked_at}',
                to_jsonb(now()::text)
            )
        WHERE staging_raw.id IN (
            SELECT staging_raw.id FROM staging_raw
            WHERE staging_raw.status = 'pending'
            AND (staging_raw.institution_id = inst_id OR inst_id IS NULL)
            ORDER BY staging_raw.last_harvested_at ASC NULLS FIRST
            LIMIT batch_size
            FOR UPDATE SKIP LOCKED
        )
        RETURNING staging_raw.id, staging_raw.url, staging_raw.institution_id,
                  staging_raw.raw_html, staging_raw.raw_name, staging_raw.raw_description
    )
    SELECT * FROM updated;
END;
$function$;

-- 2. lock_cleansed_records(batch_size integer DEFAULT 10)
CREATE OR REPLACE FUNCTION public.lock_cleansed_records(batch_size integer DEFAULT 10)
 RETURNS TABLE(id uuid, cleansed_id uuid, clean_name text, clean_description text, institution_id uuid, url text)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    RETURN QUERY
    WITH updated AS (
        UPDATE cleansed_programs
        SET status = 'processing'
        WHERE cleansed_programs.id IN (
            SELECT cleansed_programs.id FROM cleansed_programs
            WHERE cleansed_programs.status = 'pending'
            ORDER BY cleansed_programs.id ASC
            LIMIT batch_size
            FOR UPDATE SKIP LOCKED
        )
        RETURNING cleansed_programs.id, cleansed_programs.staging_id as cleansed_id,
                  cleansed_programs.clean_name, cleansed_programs.clean_description,
                  cleansed_programs.institution_id, cleansed_programs.url
    )
    SELECT * FROM updated;
END;
$function$;

-- 3. unlock_staging_record(rec_id uuid, new_status text, reason text DEFAULT NULL::text)
CREATE OR REPLACE FUNCTION public.unlock_staging_record(rec_id uuid, new_status text, reason text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    UPDATE staging_raw
    SET status = new_status,
        discard_reason = CASE WHEN new_status = 'discarded' THEN reason ELSE discard_reason END,
        processing_error = CASE WHEN new_status = 'error' THEN reason ELSE processing_error END,
        metadata = jsonb_set(
            COALESCE(metadata, '{}'::jsonb),
            '{unlocked_at}',
            to_jsonb(now()::text)
        )
    WHERE id = rec_id AND status = 'processing';
END;
$function$;

-- 4. unlock_cleansed_record(rec_id uuid, new_status text, error_msg text DEFAULT NULL::text)
CREATE OR REPLACE FUNCTION public.unlock_cleansed_record(rec_id uuid, new_status text, error_msg text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    UPDATE cleansed_programs
    SET status = new_status
    WHERE id = rec_id AND status = 'processing';
END;
$function$;

-- 5. atomic_cleansing_promote(p_staging_ids uuid[], p_cleansed_data jsonb)
CREATE OR REPLACE FUNCTION public.atomic_cleansing_promote(p_staging_ids uuid[], p_cleansed_data jsonb)
 RETURNS SETOF cleansed_programs
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    -- Upsert cleansed records (batch)
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

    -- Update staging_raw status to processed
    UPDATE staging_raw
    SET status = 'processed'
    WHERE id = ANY(p_staging_ids) AND status = 'processing';

    -- Return ALL affected cleansed rows (supports 1+ rows)
    RETURN QUERY
    SELECT *
    FROM cleansed_programs
    WHERE url IN (
        SELECT item->>'url'
        FROM jsonb_array_elements(p_cleansed_data) AS item
    );
END;
$function$;

-- 6. atomic_enrichment_promote(p_enriched_data jsonb, p_cleansed_id uuid)
CREATE OR REPLACE FUNCTION public.atomic_enrichment_promote(p_enriched_data jsonb, p_cleansed_id uuid)
 RETURNS SETOF enriched_programs
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path = public
AS $function$
BEGIN
    -- Upsert enriched record
    INSERT INTO enriched_programs (
        cleansed_id, institution_id, url, official_name, duration_text,
        duration_months, total_cost_est, requirements, graduate_profile,
        curriculum_summary, modality, primary_campus, degree_type,
        start_date, partnerships, certifications, language, categories,
        ai_summary, status
    )
    SELECT
        (item->>'cleansed_id')::UUID,
        (item->>'institution_id')::UUID,
        item->>'url',
        item->>'official_name',
        item->>'duration_text',
        COALESCE(NULLIF(item->>'duration_months', '')::NUMERIC, 0)::INT,
        (item->>'total_cost_est')::NUMERIC,
        item->>'requirements',
        item->>'graduate_profile',
        (item->>'curriculum_summary')::JSONB,
        item->>'modality',
        item->>'primary_campus',
        item->>'degree_type',
        item->>'start_date',
        item->>'partnerships',
        item->>'certifications',
        item->>'language',
        item->>'categories',
        item->>'ai_summary',
        'pending'
    FROM jsonb_array_elements(p_enriched_data) AS item
    ON CONFLICT (cleansed_id) DO UPDATE SET
        official_name = EXCLUDED.official_name,
        duration_text = EXCLUDED.duration_text,
        duration_months = COALESCE(NULLIF(EXCLUDED.duration_months, NULL)::NUMERIC, 0)::INT,
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
        status = 'pending';

    -- Update cleansed_programs status
    UPDATE cleansed_programs
    SET status = 'synced'
    WHERE id = p_cleansed_id AND status = 'processing';

    -- Return affected enriched rows
    RETURN QUERY
    SELECT *
    FROM enriched_programs
    WHERE cleansed_id = p_cleansed_id;
END;
$function$;

-- 7. fn_auto_assign_category() - trigger function
CREATE OR REPLACE FUNCTION public.fn_auto_assign_category()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path = public
AS $function$
DECLARE
    target_category_id UUID;
    target_category_name TEXT;
BEGIN
    -- Buscamos la regla usando limites de palabra (\y) para evitar falsos positivos
    SELECT r.category_id, cat.name 
    INTO target_category_id, target_category_name
    FROM public.category_rules r
    JOIN public.categories cat ON cat.id = r.category_id
    WHERE NEW.name ~* ('\\y' || r.keyword || '\\y')
    ORDER BY r.priority DESC
    LIMIT 1;

    -- Asignacion de resultados
    IF target_category_id IS NOT NULL THEN
        NEW.category_id := target_category_id;
        NEW.category := target_category_name;
        NEW.category_confirmed := true;
    ELSE
        NEW.category := 'General / Por Clasificar';
        NEW.category_confirmed := false;
    END IF;

    RETURN NEW;
END;
$function$;

-- 8. update_updated_at_column() - trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path = public
AS $function$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$function$;

-- ============================================================
-- VERIFICATION (ejecutar despues de la migration)
-- ============================================================
-- SELECT proname, pg_get_functiondef(p.oid) ~ 'SET search_path' as has_set_path
-- FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
-- WHERE n.nspname = 'public'
-- AND proname IN ('lock_staging_records', 'lock_cleansed_records', 'unlock_staging_record',
--                 'unlock_cleansed_record', 'atomic_cleansing_promote', 'atomic_enrichment_promote',
--                 'fn_auto_assign_category', 'update_updated_at_column')
-- ORDER BY proname;