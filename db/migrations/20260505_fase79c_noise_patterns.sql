-- Fase 79C: Noise Patterns Centralizados
-- Mueve patrones de ruido hardcodeados a JSONB en institution_site_profiles
-- Consolidando 3 fuentes: sync_vector_worker.py + cleansing_worker.py (HTML + name)

ALTER TABLE institution_site_profiles ADD COLUMN IF NOT EXISTS noise_patterns JSONB DEFAULT '[]'::jsonb;

-- Seed: migrar todos los patrones únicos de las 3 ubicaciones hardcodeadas
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
