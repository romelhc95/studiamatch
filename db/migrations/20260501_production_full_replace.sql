-- ============================================================
-- MIGRATION: Production Full Replace (Supabase Pro)
-- Project:   StudIAMatch
-- Date:      2026-05-01
-- Target:    zogdcvlqxanzqbvkkdar
-- 
-- FULL REPLACE: Drops & recreates intermediate ETL tables +
-- ratings/reviews. Preserves courses, institutions, categories,
-- category_rules, market_salaries, and leads.
--
-- Sections:
--   1. Extensions
--   2. DROP existing tables (6)
--   3. CREATE tables (6)
--   4. INDEXES (UNIQUE constraints)
--   5. RPC Functions (8)
--   6. Triggers
--   7. RLS Policies (12)
--   8. GRANT permissions
--
-- ⚠️  EJECUTAR MANUALMENTE en Supabase Dashboard > SQL Editor
--    (el anon key no tiene permisos DDL vía REST API)
-- ============================================================

-- ============================================================
-- SECTION 1: EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- SECTION 2: DROP EXISTING TABLES
-- ============================================================
DROP TABLE IF EXISTS staging_raw CASCADE;
DROP TABLE IF EXISTS cleansed_programs CASCADE;
DROP TABLE IF EXISTS enriched_programs CASCADE;
DROP TABLE IF EXISTS crawler_exclusions CASCADE;
DROP TABLE IF EXISTS ratings CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;

-- ============================================================
-- SECTION 3: CREATE TABLES
-- ============================================================

-- 3a. crawler_exclusions — URL exclusion rules per institution
CREATE TABLE crawler_exclusions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id  UUID REFERENCES institutions(id) ON DELETE CASCADE,
    pattern         TEXT NOT NULL,
    reason          TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_crawler_exclusions_institution
    ON crawler_exclusions(institution_id);

CREATE INDEX idx_crawler_exclusions_active
    ON crawler_exclusions(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE crawler_exclusions IS 
'Patrones de URL a excluir del harvesting. institution_id=NULL = regla global. 
Ej: /noticias/, .pdf, /login';

-- 3b. staging_raw — Raw HTML from harvesting (Station 1)
CREATE TABLE staging_raw (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id  UUID REFERENCES institutions(id) ON DELETE SET NULL,
    url             TEXT UNIQUE,
    raw_name        TEXT,
    raw_description TEXT,
    raw_html        TEXT,
    html_content    TEXT,
    description_long TEXT,
    raw_json_ld     JSONB,
    raw_og_tags     JSONB,
    status          TEXT DEFAULT 'pending',
    content_hash    TEXT,
    effective_url   TEXT,
    canonical_url   TEXT,
    discard_reason  TEXT,
    processing_error TEXT,
    metadata        JSONB DEFAULT '{}'::jsonb,
    last_harvested_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_staging_raw_status
    ON staging_raw(status);

CREATE INDEX idx_staging_raw_institution_status
    ON staging_raw(institution_id, status);

CREATE INDEX idx_staging_raw_url
    ON staging_raw(url);

COMMENT ON TABLE staging_raw IS
'Estación 1 del Golden Pipeline. HTML crudo extraído por universal_harvester.py.
Máquina de estados: discovered -> pending -> processing -> processed/error/discarded.
Content hashing: solo se re-procesa si raw_html cambió (SHA256).';

-- 3c. cleansed_programs — Cleaned & consolidated HTML (Station 2)
CREATE TABLE cleansed_programs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staging_id      UUID,
    institution_id  UUID REFERENCES institutions(id) ON DELETE SET NULL,
    url             TEXT UNIQUE,
    effective_url   TEXT,
    canonical_url   TEXT,
    clean_name      TEXT,
    clean_description TEXT,
    modality        TEXT,
    location        TEXT,
    base_price      NUMERIC,
    currency        TEXT DEFAULT 'PEN',
    status          TEXT DEFAULT 'pending',
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_cleansed_programs_status
    ON cleansed_programs(status);

CREATE INDEX idx_cleansed_programs_staging
    ON cleansed_programs(staging_id);

CREATE INDEX idx_cleansed_programs_url
    ON cleansed_programs(url);

COMMENT ON TABLE cleansed_programs IS
'Estación 2 del Golden Pipeline. cleansing_worker.py limpia HTML, elimina headers/footers/nav,
consolida subpáginas (sibling URLs), aplica exclusiones de crawler_exclusions,
filtra contenido obsoleto (años < actual), y detecta soft 404.
Máquina de estados: pending -> processing -> synced/discarded.';

-- 3d. enriched_programs — LLM-enriched data (Station 3)
CREATE TABLE enriched_programs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cleansed_id     UUID UNIQUE,
    institution_id  UUID REFERENCES institutions(id) ON DELETE SET NULL,
    url             TEXT,
    official_name   TEXT,
    duration_text   TEXT,
    duration_months INTEGER,
    total_cost_est  NUMERIC,
    requirements    TEXT,
    graduate_profile TEXT,
    curriculum_summary JSONB,
    modality        TEXT,
    primary_campus  TEXT,
    degree_type     TEXT,
    start_date      TEXT,
    partnerships    TEXT,
    certifications  TEXT,
    language        TEXT,
    categories      TEXT,
    difficulty_level TEXT,
    ai_summary      TEXT,
    embedding       TEXT,
    status          TEXT DEFAULT 'pending',
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_enriched_programs_status
    ON enriched_programs(status);

CREATE INDEX idx_enriched_programs_cleansed
    ON enriched_programs(cleansed_id);

CREATE INDEX idx_enriched_programs_url
    ON enriched_programs(url);

COMMENT ON TABLE enriched_programs IS
'Estación 3 del Golden Pipeline. enrichment_worker.py extrae 14 pilares via LLM
(Cascade: Cloudflare -> GitHub Models -> Gemini). Campos obligatorios validados por
sync_vector_worker.py: official_name (NOT NULL/None/""), modality, total_cost_est, start_date.
Máquina de estados: pending -> synced/discarded.';

-- 3e. ratings — User ratings for courses (Social Proof)
CREATE TABLE ratings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL,
    rating_value INTEGER NOT NULL CHECK (rating_value >= 1 AND rating_value <= 5),
    user_nickname VARCHAR(255) NOT NULL CHECK (char_length(TRIM(user_nickname)) > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3f. reviews — User reviews for courses (Social Proof)
CREATE TABLE reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL,
    content TEXT NOT NULL CHECK (char_length(TRIM(content)) > 0),
    user_nickname VARCHAR(255) NOT NULL CHECK (char_length(TRIM(user_nickname)) > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ============================================================
-- SECTION 4: INDEXES (UNIQUE constraints)
-- ============================================================

-- staging_raw.url UNIQUE is inline in CREATE TABLE (line ~48)
-- cleansed_programs.url UNIQUE is inline in CREATE TABLE (line ~88)
-- enriched_programs has cleansed_id UNIQUE inline, but url is NOT unique
-- Add explicit UNIQUE index on enriched_programs.url
CREATE UNIQUE INDEX IF NOT EXISTS idx_enriched_programs_url_unique
    ON enriched_programs(url);

-- courses.url UNIQUE — ensure it exists (courses table is NOT recreated)
CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_url_unique
    ON courses(url);

-- crawler_exclusions — composite unique to prevent duplicate patterns per institution
CREATE UNIQUE INDEX IF NOT EXISTS idx_crawler_exclusions_pattern_inst
    ON crawler_exclusions(institution_id, pattern);

-- ============================================================
-- SECTION 5: RPC FUNCTIONS
-- ============================================================

-- 5a. lock_staging_records — Optimistic lock (pending → processing)
-- FIXED version from 20260429_rpc_ambiguous_fix.sql
-- Column references fully qualified with staging_raw. prefix
DROP FUNCTION IF EXISTS lock_staging_records(UUID, INT) CASCADE;
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

-- 5b. lock_cleansed_records — Optimistic lock (pending → processing)
-- FIXED version from 20260429_rpc_ambiguous_fix.sql
-- Column references fully qualified with cleansed_programs. prefix
DROP FUNCTION IF EXISTS lock_cleansed_records(INT) CASCADE;
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

-- 5c. unlock_staging_record — Release lock on staging record
-- ORIGINAL from 20260428_rls_intermediate_tables.sql (no fixes needed)
DROP FUNCTION IF EXISTS unlock_staging_record(UUID, TEXT, TEXT) CASCADE;
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

-- 5d. unlock_cleansed_record — Release lock on cleansed record
-- ORIGINAL from 20260428_rls_intermediate_tables.sql (no fixes needed)
DROP FUNCTION IF EXISTS unlock_cleansed_record(UUID, TEXT, TEXT) CASCADE;
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

-- 5e. atomic_cleansing_promote — Batch upsert cleansed + update staging
-- FIXED version from 20260429_fix_p0003_duplicate_rows.sql
-- Fix: Replaced RETURNING * INTO inserted (P0003 error) with RETURN QUERY
DROP FUNCTION IF EXISTS atomic_cleansing_promote(UUID[], JSONB) CASCADE;
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

-- 5f. atomic_enrichment_promote — Upsert enriched + update cleansed
-- FIXED version from 20260429_fix_p0003_duplicate_rows.sql
-- Fix: Replaced RETURNING * INTO inserted (P0003 error) with RETURN QUERY
-- Includes partnerships, certifications, language columns from DDL
-- Uses ON CONFLICT (cleansed_id) — one enrichment per cleansed record
DROP FUNCTION IF EXISTS atomic_enrichment_promote(JSONB, UUID) CASCADE;
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

-- 5g. fn_auto_assign_category — Auto-assign category via keyword matching
-- FROM: 20260412_dynamic_categories.sql / PRODUCTION_MASTER.sql
DROP FUNCTION IF EXISTS fn_auto_assign_category() CASCADE;
CREATE OR REPLACE FUNCTION fn_auto_assign_category()
RETURNS TRIGGER AS $$
DECLARE
    found_category_id UUID;
    general_id UUID;
BEGIN
    -- 1. Attempt to find the highest-priority category matching course text
    SELECT category_id INTO found_category_id
    FROM category_rules
    WHERE 
        LOWER(NEW.name) ~* ('\y' || keyword || '\y') OR
        LOWER(COALESCE(NEW.description_long, '')) ~* ('\y' || keyword || '\y') OR
        LOWER(COALESCE(NEW.syllabus, '')) ~* ('\y' || keyword || '\y')
    ORDER BY priority DESC
    LIMIT 1;

    -- 2. If a rule matched, assign and mark as confirmed
    IF found_category_id IS NOT NULL THEN
        NEW.category_id := found_category_id;
        NEW.category_confirmed := true; 
    ELSE
        -- 3. Fallback: assign "General / Por Clasificar"
        SELECT id INTO general_id FROM categories WHERE name = 'General / Por Clasificar' LIMIT 1;
        NEW.category_id := general_id;
        NEW.category_confirmed := false;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5h. update_updated_at_column — Standard trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECTION 6: TRIGGERS
-- ============================================================

-- 6a. enriched_programs — auto-update updated_at on row change
DROP TRIGGER IF EXISTS tr_enriched_programs_updated_at ON enriched_programs;
CREATE TRIGGER tr_enriched_programs_updated_at
    BEFORE UPDATE ON enriched_programs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 6b. courses — auto-assign category on insert/update
DROP TRIGGER IF EXISTS tr_auto_assign_category ON courses;
CREATE TRIGGER tr_auto_assign_category
    BEFORE INSERT OR UPDATE OF name, description_long, syllabus ON courses
    FOR EACH ROW
    EXECUTE FUNCTION fn_auto_assign_category();

-- ============================================================
-- SECTION 7: RLS POLICIES
-- ============================================================

-- 7a. crawler_exclusions — Public SELECT on active, service_role ALL
ALTER TABLE crawler_exclusions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "crawler_exclusions_select_public" ON crawler_exclusions;
CREATE POLICY "crawler_exclusions_select_public"
    ON crawler_exclusions FOR SELECT
    TO anon, authenticated
    USING (is_active = true);

DROP POLICY IF EXISTS "crawler_exclusions_service_role" ON crawler_exclusions;
CREATE POLICY "crawler_exclusions_service_role"
    ON crawler_exclusions FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 7b. staging_raw — No public access, service_role ALL
ALTER TABLE staging_raw ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "staging_raw_no_public_access" ON staging_raw;
CREATE POLICY "staging_raw_no_public_access"
    ON staging_raw FOR ALL
    TO anon
    USING (false);

DROP POLICY IF EXISTS "staging_raw_service_role" ON staging_raw;
CREATE POLICY "staging_raw_service_role"
    ON staging_raw FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 7c. cleansed_programs — No public access, service_role ALL
ALTER TABLE cleansed_programs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "cleansed_programs_no_public_access" ON cleansed_programs;
CREATE POLICY "cleansed_programs_no_public_access"
    ON cleansed_programs FOR ALL
    TO anon
    USING (false);

DROP POLICY IF EXISTS "cleansed_programs_service_role" ON cleansed_programs;
CREATE POLICY "cleansed_programs_service_role"
    ON cleansed_programs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 7d. enriched_programs — No public access, service_role ALL
ALTER TABLE enriched_programs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "enriched_programs_no_public_access" ON enriched_programs;
CREATE POLICY "enriched_programs_no_public_access"
    ON enriched_programs FOR ALL
    TO anon
    USING (false);

DROP POLICY IF EXISTS "enriched_programs_service_role" ON enriched_programs;
CREATE POLICY "enriched_programs_service_role"
    ON enriched_programs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 7e. ratings — Public SELECT + validated INSERT
ALTER TABLE ratings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access on ratings" ON ratings;
CREATE POLICY "Allow public read access on ratings"
    ON ratings FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public insert on ratings" ON ratings;
CREATE POLICY "Allow public insert on ratings"
    ON ratings FOR INSERT
    WITH CHECK (
        rating_value >= 1 AND rating_value <= 5
        AND char_length(TRIM(user_nickname)) > 0
    );

-- 7f. reviews — Public SELECT + validated INSERT
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access on reviews" ON reviews;
CREATE POLICY "Allow public read access on reviews"
    ON reviews FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public insert on reviews" ON reviews;
CREATE POLICY "Allow public insert on reviews"
    ON reviews FOR INSERT
    WITH CHECK (
        char_length(TRIM(content)) > 0
        AND char_length(TRIM(user_nickname)) > 0
    );

-- ============================================================
-- SECTION 8: GRANT PERMISSIONS
-- ============================================================

-- Grant SELECT on all public-facing tables to anon role
-- (RLS policies further restrict access per table)
GRANT SELECT ON public.staging_raw TO anon;
GRANT SELECT ON public.cleansed_programs TO anon;
GRANT SELECT ON public.enriched_programs TO anon;
GRANT SELECT ON public.crawler_exclusions TO anon;
GRANT SELECT ON public.ratings TO anon;
GRANT SELECT ON public.reviews TO anon;
GRANT SELECT ON public.courses TO anon;
GRANT SELECT ON public.institutions TO anon;
GRANT SELECT ON public.categories TO anon;
GRANT SELECT ON public.category_rules TO anon;
GRANT SELECT ON public.market_salaries TO anon;

-- Allow anon to insert into ratings and reviews (subject to RLS WITH CHECK)
GRANT INSERT ON public.ratings TO anon;
GRANT INSERT ON public.reviews TO anon;
GRANT INSERT ON public.leads TO anon;
