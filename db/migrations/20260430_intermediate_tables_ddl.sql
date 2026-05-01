-- ============================================================
-- FASE 51: Versionado de DDL — 4 Tablas Intermedias del Pipeline
-- 
-- Estas tablas fueron creadas originalmente en Supabase Dashboard 
-- sin DDL versionado en el repositorio. Este archivo es la
-- "fuente de verdad" para reconstruir el schema desde cero.
--
-- Nota: Las RLS policies, índices y RPC functions se encuentran en:
--   - 20260428_rls_intermediate_tables.sql (policies + atomic RPCs)
--   - 20260429_rpc_ambiguous_fix.sql (fix columnas ambiguas)
--   - 20260429_fix_p0003_duplicate_rows.sql (fix INTO -> RETURN QUERY)
--
-- Ejecutar: Supabase Dashboard > SQL Editor
-- ============================================================

-- ============================================================
-- 1. crawler_exclusions — Reglas de exclusión de URLs por institución
-- ============================================================
CREATE TABLE IF NOT EXISTS crawler_exclusions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id  UUID REFERENCES institutions(id) ON DELETE CASCADE,
    pattern         TEXT NOT NULL,
    reason          TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Índice para búsqueda rápida por institución
CREATE INDEX IF NOT EXISTS idx_crawler_exclusions_institution
    ON crawler_exclusions(institution_id);

-- Índice para filtrar exclusiones activas
CREATE INDEX IF NOT EXISTS idx_crawler_exclusions_active
    ON crawler_exclusions(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE crawler_exclusions IS 
'Patrones de URL a excluir del harvesting. institution_id=NULL = regla global. 
Ej: /noticias/, .pdf, /login';


-- ============================================================
-- 2. staging_raw — HTML crudo del harvesting (Estación 1)
-- ============================================================
CREATE TABLE IF NOT EXISTS staging_raw (
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

-- Índice para consultas del pipeline
CREATE INDEX IF NOT EXISTS idx_staging_raw_status
    ON staging_raw(status);

CREATE INDEX IF NOT EXISTS idx_staging_raw_institution_status
    ON staging_raw(institution_id, status);

CREATE INDEX IF NOT EXISTS idx_staging_raw_url
    ON staging_raw(url);

COMMENT ON TABLE staging_raw IS
'Estación 1 del Golden Pipeline. HTML crudo extraído por universal_harvester.py.
Máquina de estados: discovered -> pending -> processing -> processed/error/discarded.
Content hashing: solo se re-procesa si raw_html cambió (SHA256).';


-- ============================================================
-- 3. cleansed_programs — HTML limpio y consolidado (Estación 2)
-- ============================================================
CREATE TABLE IF NOT EXISTS cleansed_programs (
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

-- Índices
CREATE INDEX IF NOT EXISTS idx_cleansed_programs_status
    ON cleansed_programs(status);

CREATE INDEX IF NOT EXISTS idx_cleansed_programs_staging
    ON cleansed_programs(staging_id);

CREATE INDEX IF NOT EXISTS idx_cleansed_programs_url
    ON cleansed_programs(url);

COMMENT ON TABLE cleansed_programs IS
'Estación 2 del Golden Pipeline. cleansing_worker.py limpia HTML, elimina headers/footers/nav,
consolida subpáginas (sibling URLs), aplica exclusiones de crawler_exclusions,
filtra contenido obsoleto (años < actual), y detecta soft 404.
Máquina de estados: pending -> processing -> synced/discarded.';


-- ============================================================
-- 4. enriched_programs — Datos enriquecidos por LLM (Estación 3)
-- ============================================================
CREATE TABLE IF NOT EXISTS enriched_programs (
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

-- Índices
CREATE INDEX IF NOT EXISTS idx_enriched_programs_status
    ON enriched_programs(status);

CREATE INDEX IF NOT EXISTS idx_enriched_programs_cleansed
    ON enriched_programs(cleansed_id);

CREATE INDEX IF NOT EXISTS idx_enriched_programs_url
    ON enriched_programs(url);

COMMENT ON TABLE enriched_programs IS
'Estación 3 del Golden Pipeline. enrichment_worker.py extrae 14 pilares via LLM
(Cascade: Cloudflare -> GitHub Models -> Gemini). Campos obligatorios validados por
sync_vector_worker.py: official_name (NOT NULL/None/""), modality, total_cost_est, start_date.
Máquina de estados: pending -> synced/discarded.';
