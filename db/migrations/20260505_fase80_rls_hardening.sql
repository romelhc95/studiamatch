-- Fase 80A: RLS Hardening + Column-Level Security + Validación
-- Aplicado vía supabase_apply_migration en Free (aqrldlmlszjtgpqiegaa) y Pro (nglyqraaalxbincabbzw)

-- 1. Restringir RLS en courses: solo activos y verificados para anon
DROP POLICY IF EXISTS courses_select_public ON courses;
CREATE POLICY courses_select_public ON courses
  FOR SELECT TO anon
  USING (is_active = true AND is_verified = true);

-- 2. Validación server-side en leads INSERT (email regex, longitud)
DROP POLICY IF EXISTS leads_insert_public ON leads;
CREATE POLICY leads_insert_public ON leads
  FOR INSERT TO anon
  WITH CHECK (
    length(first_name) > 0 AND length(first_name) <= 100
    AND email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    AND length(email) <= 255
    AND length(whatsapp) <= 30
  );

-- 3. Revocar test_ping() de anon (SECURITY DEFINER sin search_path)
REVOKE EXECUTE ON FUNCTION test_ping FROM anon;
