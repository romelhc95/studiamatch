-- ===================================================================
-- Fase 79B: Circuit Breaker por Institucion
-- Agrega columnas para control de errores consecutivos por perfil.
-- ===================================================================
ALTER TABLE institution_site_profiles
  ADD COLUMN IF NOT EXISTS max_consecutive_errors INTEGER NOT NULL DEFAULT 5,
  ADD COLUMN IF NOT EXISTS circuit_open BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS circuit_opened_at TIMESTAMPTZ;

COMMENT ON COLUMN institution_site_profiles.max_consecutive_errors IS 'Fase 79B: Umbral de errores 403/429 antes de abrir el circuito.';
COMMENT ON COLUMN institution_site_profiles.circuit_open IS 'Fase 79B: Si true, el pipeline salta esta institucion.';
COMMENT ON COLUMN institution_site_profiles.circuit_opened_at IS 'Fase 79B: Timestamp de cuando se abrio el circuito.';

-- ===================================================================
-- Fase 79D: JSONB Guardrails — auto-repair + CHECK constraints
-- Previene el bug string-vs-array en columnas JSONB.
-- ===================================================================

-- Funcion helper: repara valores JSONB que son strings invalidos
CREATE OR REPLACE FUNCTION repair_jsonb_array(val jsonb)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE AS 
BEGIN
  IF val IS NULL THEN RETURN '[]'::jsonb; END IF;
  IF jsonb_typeof(val) = 'array' THEN RETURN val; END IF;
  IF jsonb_typeof(val) = 'object' THEN 
    -- Para campos objeto como section_keywords, field_defaults
    RETURN val;
  END IF;
  -- Si es string o cualquier otra cosa, devolver array vacio
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

-- Auto-repair: corrige valores existentes que sean strings en vez de arrays
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

-- Trigger: previene inserts/updates con valores JSONB invalidos
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
