-- Fase 121: Extraccion configurable de 14 pilares por institucion y segmento URL.
-- DB-as-Code: agrega contrato JSONB para selectores, labels, overrides y confianza.

ALTER TABLE public.institution_site_profiles
ADD COLUMN IF NOT EXISTS field_selectors JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS label_selectors JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS url_type_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS extraction_transforms JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS extraction_confidence JSONB NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_profiles_field_selectors_object'
  ) THEN
    ALTER TABLE public.institution_site_profiles
    ADD CONSTRAINT chk_profiles_field_selectors_object
    CHECK (jsonb_typeof(field_selectors) = 'object');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_profiles_label_selectors_object'
  ) THEN
    ALTER TABLE public.institution_site_profiles
    ADD CONSTRAINT chk_profiles_label_selectors_object
    CHECK (jsonb_typeof(label_selectors) = 'object');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_profiles_url_type_rules_array'
  ) THEN
    ALTER TABLE public.institution_site_profiles
    ADD CONSTRAINT chk_profiles_url_type_rules_array
    CHECK (jsonb_typeof(url_type_rules) = 'array');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_profiles_extraction_transforms_object'
  ) THEN
    ALTER TABLE public.institution_site_profiles
    ADD CONSTRAINT chk_profiles_extraction_transforms_object
    CHECK (jsonb_typeof(extraction_transforms) = 'object');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_profiles_extraction_confidence_object'
  ) THEN
    ALTER TABLE public.institution_site_profiles
    ADD CONSTRAINT chk_profiles_extraction_confidence_object
    CHECK (jsonb_typeof(extraction_confidence) = 'object');
  END IF;
END $$;

COMMENT ON COLUMN public.institution_site_profiles.field_selectors IS
'Fase 121: selectores CSS base por pilar. Se aplican sobre staging_raw.raw_html antes del LLM.';

COMMENT ON COLUMN public.institution_site_profiles.label_selectors IS
'Fase 121: reglas label->valor para contenedores repetidos. Ej: .field-name-descripcion con label Duracion.';

COMMENT ON COLUMN public.institution_site_profiles.url_type_rules IS
'Fase 121: reglas por segmento URL con defaults, field_overrides y label_overrides.';

COMMENT ON COLUMN public.institution_site_profiles.extraction_transforms IS
'Fase 121: transformaciones declarativas permitidas: text, href, absolute_url, accordion_to_bullets, normalize_mode, price_to_float.';

COMMENT ON COLUMN public.institution_site_profiles.extraction_confidence IS
'Fase 121: politica de confianza por pilar: authoritative, authoritative_or_default, llm_required, url_rule_or_llm, llm_synthesis.';

UPDATE public.institution_site_profiles isp
SET
  field_selectors = COALESCE(isp.field_selectors, '{}'::jsonb) || jsonb_build_object(
    'official_name', jsonb_build_object('selector', 'h1', 'transform', 'text', 'confidence', 'authoritative'),
    'curriculum_summary', jsonb_build_object('selector', '.accordion-timeline', 'transform', 'accordion_to_bullets', 'confidence', 'authoritative'),
    'brochure_url', jsonb_build_object('selector', 'a[download][href$=''.pdf''], a[href*=''.pdf'']', 'attribute', 'href', 'transform', 'absolute_url', 'confidence', 'authoritative'),
    'ai_summary_source', jsonb_build_object('selector', '.margin-right-content .view-header', 'transform', 'text', 'confidence', 'context')
  ),
  label_selectors = COALESCE(isp.label_selectors, '{}'::jsonb) || jsonb_build_object(
    'Duración', jsonb_build_object('container', '.field-name-descripcion', 'value_selector', 'strong', 'field', 'duration_text', 'transform', 'text', 'confidence', 'authoritative'),
    'Modalidad', jsonb_build_object('container', '.field-name-descripcion', 'value_selector', 'strong', 'field', 'modality', 'transform', 'normalize_mode', 'fallback', 'Presencial', 'confidence', 'authoritative_or_default'),
    'Horarios', jsonb_build_object('container', '.field-name-descripcion', 'value_selector', 'strong', 'field', 'schedule_info', 'transform', 'text', 'confidence', 'authoritative')
  ),
  url_type_rules = CASE
    WHEN COALESCE(jsonb_array_length(isp.url_type_rules), 0) = 0 THEN jsonb_build_array(
    jsonb_build_object(
      'match', '/carreras-para-gente-que-trabaja/',
      'program_family', 'carreras_para_gente_que_trabaja',
      'defaults', jsonb_build_object('degree_type', 'Carrera para gente que trabaja', 'total_cost_est', NULL, 'requirements', NULL, 'price_status', 'consultar'),
      'label_overrides', jsonb_build_object('Modalidad', jsonb_build_object('fallback', 'Semipresencial'))
    ),
    jsonb_build_object(
      'match', '/carreras-profesionales-tecnicas/',
      'program_family', 'carreras_profesionales_tecnicas',
      'defaults', jsonb_build_object('degree_type', 'Carrera Técnica', 'total_cost_est', NULL, 'requirements', NULL, 'price_status', 'consultar')
    ),
    jsonb_build_object(
      'match', '/certificaciones/',
      'program_family', 'certificaciones',
      'defaults', jsonb_build_object('degree_type', 'Certificación', 'total_cost_est', NULL, 'requirements', NULL, 'price_status', 'consultar')
    ),
    jsonb_build_object(
      'match', '/cursos-de-formacion-continua/',
      'program_family', 'formacion_continua',
      'defaults', jsonb_build_object('degree_type', 'Curso', 'total_cost_est', NULL, 'requirements', NULL, 'price_status', 'consultar', 'modality', 'Presencial')
    ),
    jsonb_build_object(
      'match', '/diplomados/',
      'program_family', 'diplomados',
      'defaults', jsonb_build_object('degree_type', 'Diplomado', 'total_cost_est', NULL, 'requirements', NULL, 'price_status', 'consultar')
    ),
    jsonb_build_object(
      'match', '/escuela-de-coding/',
      'program_family', 'escuela_de_coding',
      'defaults', jsonb_build_object('degree_type', 'Curso', 'category_hint', 'Tecnología', 'total_cost_est', NULL, 'requirements', NULL, 'price_status', 'consultar')
    ),
    jsonb_build_object(
      'match', '/programas-especializacion/',
      'program_family', 'programas_especializacion',
      'defaults', jsonb_build_object('degree_type', 'Especialización', 'total_cost_est', NULL, 'requirements', NULL, 'price_status', 'consultar')
    )
    )
    ELSE isp.url_type_rules
  END,
  extraction_transforms = COALESCE(isp.extraction_transforms, '{}'::jsonb) || jsonb_build_object(
    'duration_months', 'derive_from_duration_text',
    'curriculum_summary', 'accordion_to_bullets',
    'brochure_url', 'absolute_url',
    'modality', 'normalize_mode'
  ),
  extraction_confidence = COALESCE(isp.extraction_confidence, '{}'::jsonb) || jsonb_build_object(
    'official_name', 'authoritative',
    'duration_text', 'authoritative',
    'modality', 'authoritative_or_default',
    'curriculum_summary', 'authoritative',
    'brochure_url', 'authoritative',
    'categories', 'llm_required',
    'degree_type', 'url_rule_or_llm',
    'ai_summary', 'llm_synthesis'
  ),
  field_defaults = COALESCE(isp.field_defaults, '{}'::jsonb) || jsonb_build_object(
    'total_cost_est', NULL,
    'requirements', NULL,
    'price_status', 'consultar'
  )
FROM public.institutions i
WHERE i.id = isp.institution_id
  AND i.slug = 'idat';
