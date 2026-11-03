-- H3 RBAC: User management (admin-only)
-- Scope: Free/Development DDL only under DDL-H3-RBAC-USERS-FREE
-- No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.
-- NOTE: Creating auth.users requires the Supabase Admin API (service role). This RPC only
--       manages the admin_members membership for an existing auth user (invite flow).
--       Production user creation must go through a protected Edge Function (verify_jwt = true).

CREATE OR REPLACE FUNCTION public.admin_list_members()
RETURNS TABLE (
  user_id UUID,
  email TEXT,
  role TEXT,
  is_active BOOLEAN,
  created_at TIMESTAMPTZ
)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_admin() THEN
    RAISE EXCEPTION 'User is not an active admin';
  END IF;

  RETURN QUERY
  SELECT m.user_id AS user_id, u.email AS email, m.role AS role, m.is_active AS is_active, m.created_at AS created_at
  FROM public.admin_members m
  JOIN auth.users u ON u.id = m.user_id
  ORDER BY m.created_at DESC;
END;
$$;

COMMENT ON FUNCTION public.admin_list_members() IS
  'H3: List editorial members (admin only). Returns user_id, email, role, is_active, created_at.';

CREATE OR REPLACE FUNCTION public.admin_create_member(
  p_email TEXT,
  p_role TEXT
)
RETURNS TABLE (
  success BOOLEAN,
  user_id UUID,
  error TEXT
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _actor_id UUID;
  _target_id UUID;
BEGIN
  _actor_id := (SELECT auth.uid());
  IF _actor_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, 'No authenticated user'::TEXT;
    RETURN;
  END IF;

  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_admin() THEN
    RETURN QUERY SELECT false, NULL::UUID, 'User is not an active admin'::TEXT;
    RETURN;
  END IF;

  IF p_role NOT IN ('admin', 'user') THEN
    RETURN QUERY SELECT false, NULL::UUID, 'Invalid role: must be admin or user'::TEXT;
    RETURN;
  END IF;

  IF p_email IS NULL OR lower(trim(p_email)) !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' THEN
    RETURN QUERY SELECT false, NULL::UUID, 'Invalid email'::TEXT;
    RETURN;
  END IF;

  SELECT id INTO _target_id FROM auth.users WHERE email = lower(trim(p_email));
  IF _target_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, 'Email not found in auth.users (invite must be created first)'::TEXT;
    RETURN;
  END IF;

  IF EXISTS (SELECT 1 FROM public.admin_members am WHERE am.user_id = _target_id) THEN
    RETURN QUERY SELECT false, _target_id, 'Duplicate email: membership already exists'::TEXT;
    RETURN;
  END IF;

  INSERT INTO public.admin_members (user_id, role, is_active)
  VALUES (_target_id, p_role, true);

  INSERT INTO public.admin_membership_audit (actor_user_id, target_user_id, action, old_values, new_values)
  VALUES (_actor_id, _target_id, 'invite', '{}'::jsonb, jsonb_build_object('role', p_role, 'is_active', true));

  RETURN QUERY SELECT true, _target_id, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_create_member(TEXT, TEXT) IS
  'H3: Create an editorial membership (admin only). Requires the auth user to exist (invite flow).';

REVOKE ALL ON FUNCTION public.admin_list_members() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_create_member(TEXT, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_list_members() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_create_member(TEXT, TEXT) TO authenticated, service_role;

-- Helper de identidad faltante en versiones anteriores
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

GRANT EXECUTE ON FUNCTION public.admin_is_active_editor() TO authenticated, service_role;
