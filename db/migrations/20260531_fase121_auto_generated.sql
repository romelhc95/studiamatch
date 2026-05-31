-- Fase 121: Auto-Deteccion de Sitio en Harvester
-- Agrega columna auto_generated para distinguir perfiles creados automaticamente
-- de perfiles revisados por humanos.

ALTER TABLE public.institution_site_profiles
ADD COLUMN IF NOT EXISTS auto_generated BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN public.institution_site_profiles.auto_generated IS
'Fase 121: true = perfil creado automaticamente por auto-deteccion, false = perfil revisado por humano';
