-- Migration: 20260509_ulima_pipeline_ready.sql
-- Activa Universidad de Lima en el pipeline con extracción mejorada.
-- Basado en análisis de URLs proporcionadas por el usuario (102 programas).
-- ===================================================================

BEGIN;

-- 1. Configurar extractores específicos para ULIMA
UPDATE institution_site_profiles
SET
  price_regex = 'S/[\s]*[\d,.]+',
  duration_regex = '(\d+\.?\d*)\s*(meses|años|ciclos|horas)',
  pipeline_ready = true
WHERE institution_id = (SELECT id FROM institutions WHERE slug = 'universidad-de-lima');

-- 2. Resetear staging_raw para re-procesar las URLs descubiertas
UPDATE staging_raw
SET status = 'pending'
WHERE institution_id = (SELECT id FROM institutions WHERE slug = 'universidad-de-lima')
  AND status = 'discovered';

COMMIT;
