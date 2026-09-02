-- H3: Admin authentication and authorization layer
-- Scope: Free/Development DDL only under DDL-H3-ADMIN-AUTH-FREE
-- No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

-- Tabla de miembros administrativos
CREATE TABLE IF NOT EXISTS public.admin_members (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.admin_members IS 'H3: Admin members with active roles. RLS protected.';

-- Índices para rendimiento
CREATE INDEX IF NOT EXISTS idx_admin_members_role_active ON public.admin_members (role, is_active);
CREATE INDEX IF NOT EXISTS idx_admin_members_user ON public.admin_members (user_id);

-- Activar RLS
ALTER TABLE public.admin_members ENABLE ROW LEVEL SECURITY;

-- Políticas RLS
DROP POLICY IF EXISTS admin_members_service_select ON public.admin_members;
CREATE POLICY admin_members_service_select
  ON public.admin_members
  FOR SELECT
  TO service_role
  USING (true);

DROP POLICY IF EXISTS admin_members_service_insert ON public.admin_members;
CREATE POLICY admin_members_service_insert
  ON public.admin_members
  FOR INSERT
  TO service_role
  WITH CHECK (true);

DROP POLICY IF EXISTS admin_members_service_update ON public.admin_members;
CREATE POLICY admin_members_service_update
  ON public.admin_members
  FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

-- RPC: Obtener rol del usuario actual
CREATE OR REPLACE FUNCTION public.admin_current_user_role()
RETURNS TEXT LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _user_id UUID;
  _role TEXT;
BEGIN
  BEGIN
    _user_id := (SELECT auth.uid());
  EXCEPTION WHEN OTHERS THEN
    RETURN 'anon';
  END;
  IF _user_id IS NULL THEN
    RETURN 'anon';
  END IF;

  SELECT am.role INTO _role
  FROM public.admin_members am
  WHERE am.user_id = _user_id
    AND am.is_active = true;
  
  RETURN COALESCE(_role, 'authenticated');
EXCEPTION
  WHEN OTHERS THEN
    RETURN 'error';
END;
$$;

COMMENT ON FUNCTION public.admin_current_user_role() IS 'H3: Returns role of current authenticated user (anon/authenticated/admin/user/error).';

-- RPC: Verificar si el usuario actual es admin activo
CREATE OR REPLACE FUNCTION public.admin_is_active_admin()
RETURNS BOOLEAN LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _user_id UUID;
BEGIN
  _user_id := (SELECT auth.uid());
  IF _user_id IS NULL THEN
    RETURN false;
  END IF;

  RETURN EXISTS (
    SELECT 1
    FROM public.admin_members am
    WHERE am.user_id = _user_id
      AND am.role = 'admin'
      AND am.is_active = true
  );
END;
$$;

COMMENT ON FUNCTION public.admin_is_active_admin() IS 'H3: Returns true if current user is active admin.';

-- RPC: Verificar si el usuario actual tiene rol admin o user activo
CREATE OR REPLACE FUNCTION public.admin_is_active_editor()
RETURNS BOOLEAN LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _user_id UUID;
BEGIN
  _user_id := (SELECT auth.uid());
  IF _user_id IS NULL THEN
    RETURN false;
  END IF;

  RETURN EXISTS (
    SELECT 1
    FROM public.admin_members am
    WHERE am.user_id = _user_id
      AND am.role IN ('admin', 'user')
      AND am.is_active = true
  );
END;
$$;

COMMENT ON FUNCTION public.admin_is_active_editor() IS 'H3: Returns true if current user is active admin or user.';

-- RPC: Verificar si el usuario actual puede editar un campo concreto como user
CREATE OR REPLACE FUNCTION public.admin_user_can_edit_field(
  p_course_id UUID,
  p_field_key TEXT
)
RETURNS BOOLEAN LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _user_id UUID;
  _role TEXT;
BEGIN
  _user_id := (SELECT auth.uid());
  IF _user_id IS NULL THEN
    RETURN false;
  END IF;

  SELECT am.role INTO _role
  FROM public.admin_members am
  WHERE am.user_id = _user_id
    AND am.is_active = true;

  IF _role IS NULL THEN
    RETURN false;
  END IF;

  IF _role = 'admin' THEN
    RETURN true;
  END IF;

  RETURN EXISTS (
    SELECT 1
    FROM public.course_editorial_state
    WHERE course_id = p_course_id
      AND p_field_key = ANY (missing_fields)
  );
END;
$$;

COMMENT ON FUNCTION public.admin_user_can_edit_field(UUID, TEXT) IS 'H3: User may edit a field only if it is in missing_fields; admin always may edit.';

-- RPCs de identidad disponibles para usuario autenticado y service role.
REVOKE ALL ON FUNCTION public.admin_current_user_role() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_is_active_admin() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_is_active_editor() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_user_can_edit_field(UUID, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_current_user_role() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_is_active_admin() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_is_active_editor() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_user_can_edit_field(UUID, TEXT) TO authenticated, service_role;

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS admin_members_updated_at ON public.admin_members;
CREATE TRIGGER admin_members_updated_at
  BEFORE UPDATE ON public.admin_members
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();
