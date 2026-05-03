-- Fase 62+75: Agregar columnas faltantes a Pro DB
-- EJECUTAR en Supabase Dashboard > SQL Editor > Pro project
-- SDLC: Aprobacion @SDLC-Chief requerida antes de ejecutar en Pro

ALTER TABLE institution_site_profiles
ADD COLUMN IF NOT EXISTS pipeline_ready boolean DEFAULT false;

ALTER TABLE institution_site_profiles
ADD COLUMN IF NOT EXISTS allowed_url_patterns jsonb DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_profiles_pipeline_ready
ON institution_site_profiles (institution_id)
WHERE pipeline_ready = true;

COMMENT ON COLUMN institution_site_profiles.pipeline_ready IS 'Fase 75: Si false, el pipeline omite esta institucion. Solo activar tras afinar exclusiones.';
COMMENT ON COLUMN institution_site_profiles.allowed_url_patterns IS 'Fase 75: Lista de regex de URLs que SI son programas (whitelist positiva).';

-- Nota: Los cambios de perfil (discovery_mode, title_prefix_removals, etc.)
-- se sincronizan via API desde el script fase62b_create_pucp_and_sync_pro.py
-- que se ejecuta desde desarrollo con credenciales Pro.
