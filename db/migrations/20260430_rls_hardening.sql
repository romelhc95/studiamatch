-- ============================================================
-- Migration: RLS Hardening — Fase 32A
-- Project: StudIAMatch (Dev Free: YOUR_FREE_PROJECT_REF)
-- Date: 2026-04-30
-- Description: Habilitar RLS en 8 tablas sin protección, 
--   crear policies de acceso público read-only y service_role ALL,
--   revocar EXECUTE de RPCs a anon/authenticated,
--   mover extensiones a schema extensions.
-- CRITICAL: Ejecutar ANTES de pg_dump para migración a Pro.
-- ============================================================

-- ============================================================
-- STEP 1: Habilitar RLS en 8 tablas sin protección
-- ============================================================
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.category_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.market_salaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- STEP 2: Policies — Tablas de contenido (anon: SELECT, service_role: ALL)
-- ============================================================

-- courses
CREATE POLICY "courses_select_public" ON public.courses FOR SELECT TO anon USING (true);
CREATE POLICY "courses_select_authenticated" ON public.courses FOR SELECT TO authenticated USING (true);
CREATE POLICY "courses_service_role" ON public.courses FOR ALL TO service_role USING (true) WITH CHECK (true);

-- institutions
CREATE POLICY "institutions_select_public" ON public.institutions FOR SELECT TO anon USING (true);
CREATE POLICY "institutions_select_authenticated" ON public.institutions FOR SELECT TO authenticated USING (true);
CREATE POLICY "institutions_service_role" ON public.institutions FOR ALL TO service_role USING (true) WITH CHECK (true);

-- categories
CREATE POLICY "categories_select_public" ON public.categories FOR SELECT TO anon USING (true);
CREATE POLICY "categories_select_authenticated" ON public.categories FOR SELECT TO authenticated USING (true);
CREATE POLICY "categories_service_role" ON public.categories FOR ALL TO service_role USING (true) WITH CHECK (true);

-- category_rules
CREATE POLICY "category_rules_select_public" ON public.category_rules FOR SELECT TO anon USING (true);
CREATE POLICY "category_rules_select_authenticated" ON public.category_rules FOR SELECT TO authenticated USING (true);
CREATE POLICY "category_rules_service_role" ON public.category_rules FOR ALL TO service_role USING (true) WITH CHECK (true);

-- market_salaries
CREATE POLICY "market_salaries_select_public" ON public.market_salaries FOR SELECT TO anon USING (true);
CREATE POLICY "market_salaries_select_authenticated" ON public.market_salaries FOR SELECT TO authenticated USING (true);
CREATE POLICY "market_salaries_service_role" ON public.market_salaries FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================
-- STEP 3: Policies — leads (anon: INSERT only, authenticated: INSERT, service_role: ALL)
-- NOTA: anon NO puede SELECT leads (PII protegido)
-- ============================================================
CREATE POLICY "leads_insert_public" ON public.leads FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "leads_insert_authenticated" ON public.leads FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "leads_service_role" ON public.leads FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================
-- STEP 4: Policies — ratings (authenticated: SELECT+INSERT, service_role: ALL)
-- ============================================================
CREATE POLICY "ratings_select_authenticated" ON public.ratings FOR SELECT TO authenticated USING (true);
CREATE POLICY "ratings_insert_authenticated" ON public.ratings FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "ratings_service_role" ON public.ratings FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================
-- STEP 5: Policies — reviews (authenticated: SELECT+INSERT, service_role: ALL)
-- ============================================================
CREATE POLICY "reviews_select_authenticated" ON public.reviews FOR SELECT TO authenticated USING (true);
CREATE POLICY "reviews_insert_authenticated" ON public.reviews FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "reviews_service_role" ON public.reviews FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================
-- STEP 6: Revocar EXECUTE de RPCs a anon, authenticated y PUBLIC
-- Solo service_role (pipeline CI/CD) debe ejecutar estas funciones
-- NOTA: Requiere revoke de PUBLIC además de anon/authenticated
-- ============================================================
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- ============================================================
-- STEP 7: Mover extensiones a schema extensions (recomendado por Supabase Advisor)
-- NOTA: Esto puede requerir que las funciones y operadores referencien
--   el schema extensions explícitamente (extensions.pg_trgm, extensions.vector)
--   Si hay errores, revertir con ALTER EXTENSION ... SET SCHEMA public;
-- ============================================================
-- ALTER EXTENSION pg_trgm SET SCHEMA extensions;
-- ALTER EXTENSION vector SET SCHEMA extensions;
-- NOTA: Comentado por seguridad. Verificar si las queries del frontend
--   y scripts usan operadores pg_trgm (%, %%) o vector (<=>) sin
--   schema prefix. Si usan search_path=public, puede fallar.

-- ============================================================
-- VERIFICATION QUERIES (ejecutar después de la migration)
-- ============================================================
-- Verificar RLS habilitado en todas las tablas:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- Esperado: TODAS las tablas con rowsecurity = true

-- Verificar policies:
-- SELECT tablename, policyname, roles, cmd FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;

-- Verificar que anon NO puede modificar courses:
-- Con anon key: PATCH /rest/v1/courses?id=eq.test → debe dar 403 o empty result

-- Verificar Supabase Advisor: 0 errores RLS, 0 warnings SECURITY DEFINER

-- ============================================================
-- ROLLBACK (en caso de emergencia)
-- ============================================================
-- ALTER TABLE public.courses DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.institutions DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.categories DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.category_rules DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.market_salaries DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.leads DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.ratings DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.reviews DISABLE ROW LEVEL SECURITY;
-- DROP POLICY "courses_select_public" ON public.courses;
-- DROP POLICY "courses_select_authenticated" ON public.courses;
-- DROP POLICY "courses_service_role" ON public.courses;
-- (etc... para cada policy creada)
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;