-- Migration: RLS Policies for Intermediate ETL Tables + RPC Functions
-- Fase 53: Correcciones P0 (Seguridad e Integridad)
-- Fecha: 2026-04-28
-- 
-- 1. Habilita RLS en las 4 tablas intermedias que no tenían políticas
-- 2. Crea políticas de seguridad: solo service_role puede escribir
-- 3. Crea funciones RPC para transacciones multi-tabla atómicas
-- 4. Crea función RPC para lock optimista (pending→processing)

-- ============================================================
-- PARTE 1: RLS en tablas intermedias
-- ============================================================

-- 1a. crawler_exclusions
ALTER TABLE crawler_exclusions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "crawler_exclusions_select_public"
ON crawler_exclusions FOR SELECT
TO anon, authenticated
USING (is_active = true);

CREATE POLICY "crawler_exclusions_service_role"
ON crawler_exclusions FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 1b. staging_raw
ALTER TABLE staging_raw ENABLE ROW LEVEL SECURITY;

CREATE POLICY "staging_raw_no_public_access"
ON staging_raw FOR ALL
TO anon
USING (false);

CREATE POLICY "staging_raw_service_role"
ON staging_raw FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 1c. cleansed_programs
ALTER TABLE cleansed_programs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "cleansed_programs_no_public_access"
ON cleansed_programs FOR ALL
TO anon
USING (false);

CREATE POLICY "cleansed_programs_service_role"
ON cleansed_programs FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 1d. enriched_programs
ALTER TABLE enriched_programs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "enriched_programs_no_public_access"
ON enriched_programs FOR ALL
TO anon
USING (false);

CREATE POLICY "enriched_programs_service_role"
ON enriched_programs FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================
-- PARTE 2: RPC - Lock Optimista (pending → processing)
-- ============================================================

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
                COALESCE(metadata, '{}'::jsonb),
                '{locked_at}',
                to_jsonb(now()::text)
            )
        WHERE id IN (
            SELECT id FROM staging_raw
            WHERE status = 'pending'
            AND (institution_id = inst_id OR inst_id IS NULL)
            ORDER BY last_harvested_at ASC NULLS FIRST
            LIMIT batch_size
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, url, institution_id, raw_html, raw_name, raw_description
    )
    SELECT * FROM updated;
END;
$$;

CREATE OR REPLACE FUNCTION unlock_staging_record(rec_id UUID, new_status TEXT, reason TEXT DEFAULT NULL)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
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
$$;

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
        WHERE id IN (
            SELECT id FROM cleansed_programs
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT batch_size
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, staging_id as cleansed_id, clean_name, clean_description, institution_id, url
    )
    SELECT * FROM updated;
END;
$$;

CREATE OR REPLACE FUNCTION unlock_cleansed_record(rec_id UUID, new_status TEXT, error_msg TEXT DEFAULT NULL)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE cleansed_programs
    SET status = new_status
    WHERE id = rec_id AND status = 'processing';
END;
$$;

-- ============================================================
-- PARTE 3: RPC - Writes Multi-Tabla Atómicos
-- ============================================================

CREATE OR REPLACE FUNCTION atomic_cleansing_promote(
    p_staging_ids UUID[],
    p_cleansed_data JSONB
)
RETURNS SETOF cleansed_programs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    inserted cleansed_programs%ROWTYPE;
BEGIN
    -- Upsert cleansed record
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
        status = 'pending'
    RETURNING * INTO inserted;

    -- Update staging_raw status to processed
    UPDATE staging_raw
    SET status = 'processed'
    WHERE id = ANY(p_staging_ids) AND status = 'processing';

    RETURN QUERY SELECT * FROM cleansed_programs WHERE id = inserted.id;
END;
$$;

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
    -- Upsert enriched record
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
        (item->>'duration_months')::INT,
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
        ai_summary = EXCLUDED.ai_summary,
        status = 'pending'
    RETURNING * INTO inserted;

    -- Update cleansed_programs status to enriched
    UPDATE cleansed_programs
    SET status = 'enriched'
    WHERE id = p_cleansed_id AND status = 'processing';

    RETURN QUERY SELECT * FROM enriched_programs WHERE id = inserted.id;
END;
$$;

-- ============================================================
-- PARTE 4: Actualizar máquina de estados en PRODUCTION_MASTER.sql
-- ============================================================
-- NOTA: La máquina de estados ahora soporta el estado 'processing':
-- staging_raw: discovered → pending → processing → processed
--                                               → discarded (con discard_reason)
--                                               → error (con processing_error)
-- cleansed_programs: pending → processing → enriched
--                                          → error
-- enriched_programs: pending → processing → synced
--                                          → error
-- courses: is_active: true ↔ false (vía integrity_ping con gracia 3 días)
