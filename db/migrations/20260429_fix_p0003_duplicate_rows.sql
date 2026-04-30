-- ============================================================
-- FASE 59 P1-6: Fix RPC P0003 "query returned more than one row"
-- en atomic_cleansing_promote
-- 
-- Bug: Si p_cleansed_data contiene 2+ items con la misma URL
-- (ej: trailing-slash normalization), ON CONFLICT DO UPDATE
-- retorna una fila por cada item procesado. RETURNING * INTO inserted
-- falla porque INTO espera exactamente 1 fila.
-- 
-- Incidence: 8/8 batches en pipeline run #25126753299 log.
-- 
-- Fix: Reemplazar INTO scalar por RETURN QUERY que soporta
-- múltiples filas. El caller (cleansing_worker.py) ya itera
-- sobre resultados múltiples.
-- 
-- ⚠️ EJECUTAR MANUALMENTE en Supabase Dashboard > SQL Editor
-- ============================================================

CREATE OR REPLACE FUNCTION atomic_cleansing_promote(
    p_staging_ids UUID[],
    p_cleansed_data JSONB
)
RETURNS SETOF cleansed_programs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
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
$$;


-- ============================================================
-- FASE 59 P1-6b: Fix RPC P0003 también en atomic_enrichment_promote
-- (mismo patrón: RETURNING * INTO inserted puede fallar si hay
--  conflicto por cleansed_id duplicado en la misma batch)
-- ============================================================

CREATE OR REPLACE FUNCTION atomic_enrichment_promote(
    p_enriched_data JSONB,
    p_cleansed_id UUID
)
RETURNS SETOF enriched_programs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
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
$$;
