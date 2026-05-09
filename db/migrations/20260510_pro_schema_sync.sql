-- ===================================================================
-- Migration: 20260510_pro_schema_sync.sql
-- Fase 95: Pro Schema Sync — corrige 8 diferencias estructurales
-- entre Free y Pro para que FG2 pueda ejecutarse en producción.
--
-- Incluye también el RPC exec_sql() usado por db_migrate.py (Fase 97)
-- para aplicar migrations futuras automáticamente.
--
-- Idempotente: todas las operaciones usan IF NOT EXISTS / OR REPLACE.
-- Puede ejecutarse múltiples veces sin daño.
-- ===================================================================

BEGIN;

-- ===================================================================
-- 1. Fase 73: start_date DATE en courses (columna faltante en Pro)
-- ===================================================================
ALTER TABLE courses ADD COLUMN IF NOT EXISTS start_date DATE;
COMMENT ON COLUMN courses.start_date IS 'Fecha de inicio parseada (DATE). Usado para filtrado de expiración con 90d de gracia.';
CREATE INDEX IF NOT EXISTS idx_courses_start_date ON courses(start_date) WHERE start_date IS NOT NULL;

-- ===================================================================
-- 2. Fase 79C: noise_patterns (columna faltante en Pro)
-- ===================================================================
ALTER TABLE institution_site_profiles ADD COLUMN IF NOT EXISTS noise_patterns JSONB DEFAULT '[]'::jsonb;

UPDATE institution_site_profiles
SET noise_patterns = '[
  "agradecimiento",
  "thank.?\\s*you",
  "^https?://[^/]+/?$",
  "/facultad-de-[^/]+/?$",
  "matr[ií]cul",
  "inscr[ií]b",
  "gracias",
  "matr[ií]culas?\\s+abiert",
  "inscr[ií]bete",
  "^facultad\\s+de\\b",
  "^universidad.+?\\|"
]'::jsonb
WHERE noise_patterns = '[]'::jsonb OR noise_patterns IS NULL;

-- ===================================================================
-- 3. Fase 79B: Circuit Breaker (3 columnas faltantes en Pro)
-- ===================================================================
ALTER TABLE institution_site_profiles
  ADD COLUMN IF NOT EXISTS max_consecutive_errors INTEGER NOT NULL DEFAULT 5,
  ADD COLUMN IF NOT EXISTS circuit_open BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS circuit_opened_at TIMESTAMPTZ;

COMMENT ON COLUMN institution_site_profiles.max_consecutive_errors IS 'Fase 79B: Umbral de errores 403/429 antes de abrir el circuito.';
COMMENT ON COLUMN institution_site_profiles.circuit_open IS 'Fase 79B: Si true, el pipeline salta esta institucion.';
COMMENT ON COLUMN institution_site_profiles.circuit_opened_at IS 'Fase 79B: Timestamp de cuando se abrio el circuito.';

-- ===================================================================
-- 4. Fase 79D: JSONB Guardrails (RPCs + trigger faltantes en Pro)
-- ===================================================================
CREATE OR REPLACE FUNCTION repair_jsonb_array(val jsonb)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE AS
BEGIN
  IF val IS NULL THEN RETURN '[]'::jsonb; END IF;
  IF jsonb_typeof(val) = 'array' THEN RETURN val; END IF;
  IF jsonb_typeof(val) = 'object' THEN RETURN val; END IF;
  RETURN '[]'::jsonb;
END;
;

CREATE OR REPLACE FUNCTION repair_jsonb_object(val jsonb)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE AS
BEGIN
  IF val IS NULL THEN RETURN '{}'::jsonb; END IF;
  IF jsonb_typeof(val) = 'object' THEN RETURN val; END IF;
  RETURN '{}'::jsonb;
END;
;

UPDATE institution_site_profiles SET
  seed_urls = repair_jsonb_array(seed_urls),
  exclusion_patterns = repair_jsonb_array(exclusion_patterns),
  catalog_url_patterns = repair_jsonb_array(catalog_url_patterns),
  popup_close_selectors = repair_jsonb_array(popup_close_selectors),
  title_prefix_removals = repair_jsonb_array(title_prefix_removals),
  title_split_separators = repair_jsonb_array(title_split_separators),
  allowed_url_patterns = repair_jsonb_array(allowed_url_patterns),
  section_keywords = repair_jsonb_object(section_keywords),
  field_defaults = repair_jsonb_object(field_defaults),
  section_mode_map = repair_jsonb_object(section_mode_map),
  section_course_type_map = repair_jsonb_object(section_course_type_map);

CREATE OR REPLACE FUNCTION validate_institution_site_profiles_jsonb()
RETURNS trigger LANGUAGE plpgsql AS
BEGIN
  NEW.seed_urls := repair_jsonb_array(NEW.seed_urls);
  NEW.exclusion_patterns := repair_jsonb_array(NEW.exclusion_patterns);
  NEW.catalog_url_patterns := repair_jsonb_array(NEW.catalog_url_patterns);
  NEW.popup_close_selectors := repair_jsonb_array(NEW.popup_close_selectors);
  NEW.title_prefix_removals := repair_jsonb_array(NEW.title_prefix_removals);
  NEW.title_split_separators := repair_jsonb_array(NEW.title_split_separators);
  NEW.allowed_url_patterns := repair_jsonb_array(NEW.allowed_url_patterns);
  NEW.section_keywords := repair_jsonb_object(NEW.section_keywords);
  NEW.field_defaults := repair_jsonb_object(NEW.field_defaults);
  NEW.section_mode_map := repair_jsonb_object(NEW.section_mode_map);
  NEW.section_course_type_map := repair_jsonb_object(NEW.section_course_type_map);
  RETURN NEW;
END;
;

DROP TRIGGER IF EXISTS trg_validate_institution_site_profiles_jsonb ON institution_site_profiles;
CREATE TRIGGER trg_validate_institution_site_profiles_jsonb
  BEFORE INSERT OR UPDATE ON institution_site_profiles
  FOR EACH ROW EXECUTE FUNCTION validate_institution_site_profiles_jsonb();

-- ===================================================================
-- 5. Fase 90 + 93 + 94: Perfil DMC completo
-- ===================================================================
UPDATE institution_site_profiles
SET
  catalog_link_selector = 'a.woocommerce-LoopProduct-link',
  section_keywords = '{
    "Pre-requisitos": "requirements",
    "Lo que vas a obtener": "graduate_profile",
    "Objetivo General": "objectives",
    "Objetivos Específicos": "objectives",
    "Características": "curriculum_summary",
    "Certificación": "certification",
    "Inicio": "start_date",
    "Duración": "duration_text",
    "Modalidad": "modality"
  }'::jsonb,
  field_defaults = COALESCE(field_defaults, '{}'::jsonb) || '{"mode": "Híbrido", "campus": "DMC"}'::jsonb,
  seed_urls = '[
    "https://dmc.pe/categoria-producto/cursos/",
    "https://dmc.pe/categoria-producto/especializaciones/",
    "https://dmc.pe/categoria-producto/diplomas/",
    "https://dmc.pe/categoria-producto/certificaciones/"
  ]'::jsonb,
  price_regex = 'S/[\\s]*[\\d,]+',
  duration_regex = '(\\d+)\\s*hrs?\\.?\\s*acad',
  title_prefix_removals = '["- DMC Institute"]'::jsonb,
  exclusion_patterns = COALESCE(exclusion_patterns, '[]'::jsonb) || '["/checkout/", "/mi-cuenta/", "/cart/", "add-to-cart="]'::jsonb,
  pipeline_ready = true
WHERE institution_id = (SELECT id FROM institutions WHERE slug = 'dmc');

-- ===================================================================
-- 6. Actualizar RPC atomic_enrichment_promote (versión moderna)
-- ===================================================================
CREATE OR REPLACE FUNCTION atomic_enrichment_promote(
  p_enriched_data jsonb,
  p_cleansed_id uuid
)
RETURNS SETOF enriched_programs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS
$$
BEGIN
    INSERT INTO enriched_programs (
        cleansed_id, institution_id, url, official_name, duration_text,
        duration_months, total_cost_est, requirements, graduate_profile,
        curriculum_summary, modality, primary_campus, degree_type,
        start_date, partnerships, certifications, language, categories,
        difficulty_level, ai_summary, status, provider_used, is_mock_data
    )
    SELECT
        (item->>'cleansed_id')::UUID,
        (item->>'institution_id')::UUID,
        item->>'url',
        item->>'official_name',
        item->>'duration_text',
        COALESCE(NULLIF(item->>'duration_months', '')::NUMERIC, 0)::INT,
        NULLIF(item->>'total_cost_est', '')::NUMERIC,
        item->>'requirements',
        item->>'graduate_profile',
        COALESCE(NULLIF(item->>'curriculum_summary', ''), '{}')::JSONB,
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
        (item->>'is_mock_data')::BOOLEAN
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
        provider_used = EXCLUDED.provider_used,
        is_mock_data = EXCLUDED.is_mock_data,
        status = 'pending';

    UPDATE cleansed_programs
    SET status = 'enriched'
    WHERE id = p_cleansed_id AND status = 'pending';

    RETURN QUERY
    SELECT *
    FROM enriched_programs
    WHERE cleansed_id = p_cleansed_id;
END;
$$;

-- ===================================================================
-- 7. RPC exec_sql() para db_migrate.py (Fase 97)
-- Permite ejecutar SQL arbitrario vía REST API.
-- Solo accesible por service_role.
-- ===================================================================
CREATE OR REPLACE FUNCTION exec_sql(sql_text text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  EXECUTE sql_text;
END;
$$;

REVOKE EXECUTE ON FUNCTION exec_sql(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION exec_sql(text) TO service_role;

-- ===================================================================
-- 8. Mover extensiones a schema extensions (si aplica)
-- ===================================================================
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector' AND extrelocatable) THEN
    ALTER EXTENSION vector SET SCHEMA extensions;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm' AND extrelocatable) THEN
    ALTER EXTENSION pg_trgm SET SCHEMA extensions;
  END IF;
END;
$$;

COMMIT;
