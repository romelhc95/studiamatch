-- Hito 1: Contrato editorial, calidad de datos, patrocinio y leads base
-- CAs cubiertos: CA2 parcial, preparacion CA7/CA10
-- DB-as-Code: columnas, checks, indices y backfill operativo idempotente justificado. Sin UUIDs hardcodeados.
-- Consumido por: TAREA-002 (escribe/calcula), TAREA-003 (edita/publica), TAREA-005 (muestra patrocinio)

-- ============================================================
-- Tabla courses: estado editorial, calidad, fuentes y patrocinio
-- ============================================================

ALTER TABLE public.courses
ADD COLUMN IF NOT EXISTS publication_status text NOT NULL DEFAULT 'borrador',
ADD COLUMN IF NOT EXISTS data_quality_status text NOT NULL DEFAULT 'pendiente',
ADD COLUMN IF NOT EXISTS missing_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS field_sources jsonb NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS manual_updated_at timestamptz,
ADD COLUMN IF NOT EXISTS is_sponsored boolean NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS sponsorship_priority integer NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS sponsorship_label text;

-- Reutilizacion de start_date / start_date_text confirmada:
-- start_date (DATE) y start_date_text (varchar) YA existen en courses.
-- NO se crea next_start_date; Hito 2/3 consumen start_date como fecha estructurada
-- y start_date_text como texto original.

-- ============================================================
-- Tabla leads: clasificacion base de fuente
-- ============================================================

ALTER TABLE public.leads
ADD COLUMN IF NOT EXISTS lead_source_type text NOT NULL DEFAULT 'organic';

-- ============================================================
-- Constraints (idempotentes via pg_constraint)
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_courses_publication_status' AND conrelid = 'public.courses'::regclass) THEN
        ALTER TABLE public.courses
        ADD CONSTRAINT chk_courses_publication_status
        CHECK (publication_status IN ('borrador', 'pendiente_revision', 'publicado', 'despublicado'));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_courses_data_quality_status' AND conrelid = 'public.courses'::regclass) THEN
        ALTER TABLE public.courses
        ADD CONSTRAINT chk_courses_data_quality_status
        CHECK (data_quality_status IN ('pendiente', 'completo'));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_courses_missing_fields_array' AND conrelid = 'public.courses'::regclass) THEN
        ALTER TABLE public.courses
        ADD CONSTRAINT chk_courses_missing_fields_array
        CHECK (jsonb_typeof(missing_fields) = 'array');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_courses_field_sources_object' AND conrelid = 'public.courses'::regclass) THEN
        ALTER TABLE public.courses
        ADD CONSTRAINT chk_courses_field_sources_object
        CHECK (jsonb_typeof(field_sources) = 'object');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_courses_sponsorship_priority_nonnegative' AND conrelid = 'public.courses'::regclass) THEN
        ALTER TABLE public.courses
        ADD CONSTRAINT chk_courses_sponsorship_priority_nonnegative
        CHECK (sponsorship_priority >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_courses_sponsorship_label_length' AND conrelid = 'public.courses'::regclass) THEN
        ALTER TABLE public.courses
        ADD CONSTRAINT chk_courses_sponsorship_label_length
        CHECK (sponsorship_label IS NULL OR char_length(sponsorship_label) <= 80);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_leads_source_type' AND conrelid = 'public.leads'::regclass) THEN
        ALTER TABLE public.leads
        ADD CONSTRAINT chk_leads_source_type
        CHECK (lead_source_type IN ('organic', 'sponsored'));
    END IF;
END $$;

-- ============================================================
-- Indices
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_courses_publication_quality
    ON public.courses (publication_status, data_quality_status)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_courses_missing_fields_gin
    ON public.courses USING gin (missing_fields);

CREATE INDEX IF NOT EXISTS idx_courses_sponsored_priority
    ON public.courses (is_sponsored, sponsorship_priority DESC)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_leads_source_type_created_at
    ON public.leads (lead_source_type, created_at DESC);

-- ============================================================
-- Comentarios de columna para documentacion del contrato
-- ============================================================

COMMENT ON COLUMN public.courses.publication_status IS 'Hito 1: estado editorial publico. Valores: borrador, pendiente_revision, publicado, despublicado. NO reutiliza estados ETL.';
COMMENT ON COLUMN public.courses.data_quality_status IS 'Hito 1: calidad de datos. Valores: pendiente, completo. Consumido por TAREA-002 para marcado automatico.';
COMMENT ON COLUMN public.courses.missing_fields IS 'Hito 1: array JSON de nombres de campos criticos faltantes. Ej: ["price_pen","duration","mode"]. Llenado por TAREA-002.';
COMMENT ON COLUMN public.courses.field_sources IS 'Hito 1: objeto JSON con origen de cada campo. Ej: {"price_pen":"scraping","duration":"manual"}. TAREA-002 escribe scraping/llm; TAREA-003 escribe manual.';
COMMENT ON COLUMN public.courses.manual_updated_at IS 'Hito 1: timestamp de ultima curacion manual via /admin (TAREA-003). NULL si nunca fue editado manualmente.';
COMMENT ON COLUMN public.courses.is_sponsored IS 'Hito 1: flag base para patrocinio. TAREA-005 consume para ordenar y mostrar badges. Sin logica comercial avanzada.';
COMMENT ON COLUMN public.courses.sponsorship_priority IS 'Hito 1: prioridad de despliegue para patrocinados (mayor = mas arriba). TAREA-005 consume para ordenamiento.';
COMMENT ON COLUMN public.courses.sponsorship_label IS 'Hito 1: etiqueta visible de patrocinio (max 80 chars). Ej: "Patrocinado", "Destacado". TAREA-005 consume.';
COMMENT ON COLUMN public.leads.lead_source_type IS 'Hito 1: clasificacion base de lead. Valores: organic, sponsored. Solo clasificacion; sin email/webhook/CRM.';

-- ============================================================
-- Backfill: cursos existentes activos+verificados → publicado
-- ============================================================
-- Unica vez: cursos que ya estaban publicos antes de que existiera
-- publication_status deben marcarse como 'publicado' para que el
-- nuevo filtro RLS no los oculte.
UPDATE public.courses
SET publication_status = 'publicado'
WHERE is_active = true AND is_verified = true
  AND publication_status = 'borrador';

-- ============================================================
-- RLS Hardening: contrato publico y anti-spoofing
-- ============================================================

-- ST-09: Filtrar solo cursos publicados para anon/authenticated
DROP POLICY IF EXISTS courses_select_public ON public.courses;
CREATE POLICY courses_select_public ON public.courses
  FOR SELECT TO anon
  USING (
    is_active = true
    AND is_verified = true
    AND publication_status = 'publicado'
    AND EXISTS (
      SELECT 1 FROM institution_site_profiles p
      WHERE p.institution_id = courses.institution_id
        AND p.production_enabled = true
    )
  );

DROP POLICY IF EXISTS courses_select_authenticated ON public.courses;
CREATE POLICY courses_select_authenticated ON public.courses
  FOR SELECT TO authenticated
  USING (
    is_active = true
    AND is_verified = true
    AND publication_status = 'publicado'
    AND EXISTS (
      SELECT 1 FROM institution_site_profiles p
      WHERE p.institution_id = courses.institution_id
        AND p.production_enabled = true
    )
  );

-- ST-10: Forzar lead_source_type = 'organic' para INSERT anonimo
DROP POLICY IF EXISTS leads_insert_public ON public.leads;
CREATE POLICY leads_insert_public ON public.leads
  FOR INSERT TO anon
  WITH CHECK (
    length(first_name::text) > 0
    AND length(first_name::text) <= 100
    AND email::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    AND length(email::text) <= 255
    AND length(whatsapp::text) <= 30
    AND lead_source_type = 'organic'
  );

-- La autenticacion por si sola no autoriza atribucion patrocinada.
DROP POLICY IF EXISTS leads_insert_authenticated ON public.leads;
CREATE POLICY leads_insert_authenticated ON public.leads
  FOR INSERT TO authenticated
  WITH CHECK (
    length(first_name::text) > 0
    AND length(first_name::text) <= 100
    AND email::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    AND length(email::text) <= 255
    AND length(whatsapp::text) <= 30
    AND lead_source_type = 'organic'
  );
