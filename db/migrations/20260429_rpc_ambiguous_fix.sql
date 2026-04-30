-- ============================================================
-- FASE 57: Pipeline RPC Fixes
-- Corrige 3 bugs en funciones SQL del pipeline:
--   1. Columnas ambiguas en lock_staging_records y lock_cleansed_records
--   2. Cast float → INT en duration_months de atomic_enrichment_promote
--   3. (mismos nombres de columna cualificados en atomic_cleansing_promote)
-- 
-- ⚠️ REQUIERE EJECUCIÓN MANUAL en Supabase Dashboard > SQL Editor
--    (no se puede aplicar desde el contenedor Docker porque el anon key
--     no tiene permisos para CREATE/REPLACE FUNCTION via REST API)
-- ============================================================

-- ============================================================
-- FIX 1: lock_staging_records — cualificar todas las columnas con staging_raw.
-- ============================================================
DROP FUNCTION IF EXISTS lock_staging_records(UUID, INT);
CREATE OR REPLACE FUNCTION lock_staging_records(inst_id UUID, batch_size INT DEFAULT 100)
RETURNS TABLE(id UUID, url TEXT, institution_id UUID, raw_html TEXT, raw_name TEXT, raw_description TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
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
$$;

-- ============================================================
-- FIX 2: lock_cleansed_records — cualificar todas las columnas con cleansed_programs.
-- ============================================================
DROP FUNCTION IF EXISTS lock_cleansed_records(INT);
CREATE OR REPLACE FUNCTION lock_cleansed_records(batch_size INT DEFAULT 10)
RETURNS TABLE(id UUID, cleansed_id UUID, clean_name TEXT, clean_description TEXT, institution_id UUID, url TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
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
$$;

-- ============================================================
-- FIX 3: atomic_enrichment_promote — aceptar float en duration_months
--        usando COALESCE(NULLIF(…)::NUMERIC, 0)::INT en vez de ::INT directo
-- ============================================================
DROP FUNCTION IF EXISTS atomic_enrichment_promote(JSONB, UUID);
CREATE OR REPLACE FUNCTION atomic_enrichment_promote(
    p_enriched_data JSONB,
    p_cleansed_id UUID
)
RETURNS SETOF enriched_programs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    inserted enriched_programs%ROWTYPE;
BEGIN
    INSERT INTO enriched_programs (
        cleansed_id, institution_id, url, official_name, duration_text,
        duration_months, total_cost_est, requirements, graduate_profile,
        curriculum_summary, modality, primary_campus, degree_type,
        start_date, categories, difficulty_level, ai_summary, status
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
        item->>'categories',
        item->>'difficulty_level',
        item->>'ai_summary',
        'pending'
    FROM jsonb_array_elements(p_enriched_data) AS item
    ON CONFLICT (url) DO UPDATE SET
        official_name = EXCLUDED.official_name,
        duration_text = EXCLUDED.duration_text,
        duration_months = EXCLUDED.duration_months,
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
        status = 'pending'
    RETURNING * INTO inserted;

    UPDATE cleansed_programs
    SET status = 'enriched'
    WHERE id = p_cleansed_id AND status = 'processing';

    RETURN QUERY SELECT * FROM enriched_programs WHERE id = inserted.id;
END;
$$;
