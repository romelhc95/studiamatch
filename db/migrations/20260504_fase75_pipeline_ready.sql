-- Fase 75: Exclusion Gate + Noise Sentinel v2
-- Agrega pipeline_ready gate y allowed_url_patterns (whitelist positiva)

ALTER TABLE institution_site_profiles
ADD COLUMN IF NOT EXISTS pipeline_ready boolean DEFAULT false;

ALTER TABLE institution_site_profiles
ADD COLUMN IF NOT EXISTS allowed_url_patterns jsonb DEFAULT '[]'::jsonb;

-- Indice para filtrar instituciones listas
CREATE INDEX IF NOT EXISTS idx_profiles_pipeline_ready
ON institution_site_profiles (institution_id)
WHERE pipeline_ready = true;

COMMENT ON COLUMN institution_site_profiles.pipeline_ready IS 'Fase 75: Si false, el pipeline omite esta institucion. Solo activar tras afinar exclusiones.';
COMMENT ON COLUMN institution_site_profiles.allowed_url_patterns IS 'Fase 75: Lista de regex de URLs que SI son programas (whitelist positiva).';
