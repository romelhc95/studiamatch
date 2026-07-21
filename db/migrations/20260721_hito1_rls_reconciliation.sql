-- Hito 1 remediacion: reconciliacion RLS leads INSERT policies
-- Origen: TAREA-006 finding #3 (Auditoria de cobertura 2026-07-21)
-- Causa: Supabase Free tiene las policies leads_insert_public/authenticated
--   sin la validacion de course_id contra cursos publicables. La migracion
--   versionada 20260712_hito1_editorial_quality_contract.sql SI contiene
--   esa validacion, pero Free se aplico desde una version anterior.
-- Accion: recrear ambas policies con el texto completo versionado.
-- Objetivo: inserts anon/authenticated validan que course_id sea NULL
--   o apunte a un curso activo, verificado, publicado y de institucion
--   con production_enabled=true.
-- Forward-only, idempotente. No toca Pro.

-- ============================================================
-- Recreacion idempotente de leads_insert_public
-- ============================================================

DROP POLICY IF EXISTS leads_insert_public ON public.leads;
CREATE POLICY leads_insert_public ON public.leads
  FOR INSERT TO anon
  WITH CHECK (
    length(first_name::text) > 0
    AND length(first_name::text) <= 100
    AND email::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    AND length(email::text) <= 255
    AND length(whatsapp::text) <= 30
    AND (
      course_id IS NULL
      OR EXISTS (
        SELECT 1
        FROM public.courses c
        WHERE c.id = leads.course_id
          AND c.is_active = true
          AND c.is_verified = true
          AND c.publication_status = 'publicado'
          AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = c.institution_id
              AND p.production_enabled = true
          )
      )
    )
    AND lead_source_type = 'organic'
  );

-- ============================================================
-- Recreacion idempotente de leads_insert_authenticated
-- ============================================================

DROP POLICY IF EXISTS leads_insert_authenticated ON public.leads;
CREATE POLICY leads_insert_authenticated ON public.leads
  FOR INSERT TO authenticated
  WITH CHECK (
    length(first_name::text) > 0
    AND length(first_name::text) <= 100
    AND email::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    AND length(email::text) <= 255
    AND length(whatsapp::text) <= 30
    AND (
      course_id IS NULL
      OR EXISTS (
        SELECT 1
        FROM public.courses c
        WHERE c.id = leads.course_id
          AND c.is_active = true
          AND c.is_verified = true
          AND c.publication_status = 'publicado'
          AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = c.institution_id
              AND p.production_enabled = true
          )
      )
    )
    AND lead_source_type = 'organic'
  );

-- ============================================================
-- Verificacion post-migracion: las policies deben contener
-- el texto 'publication_status' como evidencia del hardening.
-- ============================================================
