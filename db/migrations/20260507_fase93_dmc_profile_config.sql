-- Fase 93: DMC Harvester — Section Keywords + H4 Extractor
-- Configura section_keywords, field_defaults, seed_urls, price/duration regex,
-- title_prefix_removals, y activa pipeline_ready para DMC.
-- Basado en análisis real de https://dmc.pe/producto/diploma-estrategia-liderazgo-data-ia/

UPDATE institution_site_profiles
SET
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
  field_defaults = '{"mode": "Híbrido"}'::jsonb,
  seed_urls = '[
    "https://dmc.pe/categoria-producto/cursos/",
    "https://dmc.pe/categoria-producto/especializaciones/",
    "https://dmc.pe/categoria-producto/diplomas/",
    "https://dmc.pe/categoria-producto/certificaciones/"
  ]'::jsonb,
  price_regex = 'S/[\s]*[\d,]+',
  duration_regex = '(\d+)\s*hrs?\.?\s*acad',
  title_prefix_removals = '["- DMC Institute"]'::jsonb,
  pipeline_ready = true
WHERE institution_id = (SELECT id FROM institutions WHERE slug = 'dmc');
