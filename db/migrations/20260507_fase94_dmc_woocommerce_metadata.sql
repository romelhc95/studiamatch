-- Fase 94: DMC WooCommerce Structured Data Extraction for Pillar Enrichment
-- Agrega campus por defecto al perfil DMC
UPDATE institution_site_profiles
SET field_defaults = field_defaults || '{"campus": "DMC"}'::jsonb,
    updated_at = now()
WHERE institution_id = (SELECT id FROM institutions WHERE slug = 'dmc');
