-- H3 RBAC contract fix: runtime bugs found by remote JIT-A matrix (2026-09-02)
-- A6  -> 42804: admin_list_members returned auth.users.email (varchar(255)) into a TEXT OUT column.
-- A13 -> 42702: admin_update_member referenced role/is_active/user_id without qualification,
--        colliding with the RETURNS TABLE OUT parameters.
--        Root cause on PG17: the local variable was named `current_role`, a SQL pseudo-identifier
--        that resolves to the session role (CURRENT_USER), silently returning 'postgres' instead of
--        the membership column. The local variable is renamed to cur_role and every column reference
--        (role/is_active/user_id) is fully qualified with the table alias.
-- Idempotent CREATE OR REPLACE (no signature/ACL change); Free/Development DDL, applied via approved delta.

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
  SELECT m.user_id AS user_id, u.email::text AS email, m.role AS role, m.is_active AS is_active, m.created_at AS created_at
  FROM public.admin_members m
  JOIN auth.users u ON u.id = m.user_id
  ORDER BY m.created_at DESC;
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_update_member(
  p_user_id UUID,
  p_role TEXT DEFAULT NULL,
  p_is_active BOOLEAN DEFAULT NULL,
  p_action TEXT DEFAULT 'update'
)
RETURNS TABLE (success BOOLEAN, user_id UUID, role TEXT, is_active BOOLEAN, error TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  actor_id UUID := (SELECT auth.uid());
  cur_role TEXT;
  current_active BOOLEAN;
  active_admins INTEGER;
  next_role TEXT;
  next_active BOOLEAN;
  event_action TEXT;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_membership_mutation', 0));
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_admin() THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'User is not an active admin';
    RETURN;
  END IF;
  IF p_user_id = actor_id AND (p_is_active = false OR p_role = 'user') THEN
    SELECT count(*) INTO active_admins FROM public.admin_members
    WHERE public.admin_members.role = 'admin' AND public.admin_members.is_active;
    IF active_admins <= 1 THEN
      RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Cannot deactivate the last active admin';
      RETURN;
    END IF;
  END IF;
  SELECT am.role, am.is_active INTO cur_role, current_active
  FROM public.admin_members am WHERE am.user_id = p_user_id FOR UPDATE;
  IF cur_role IS NULL THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Membership not found';
    RETURN;
  END IF;
  next_role := COALESCE(p_role, cur_role);
  next_active := COALESCE(p_is_active, current_active);
  IF next_role NOT IN ('admin', 'user') THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Invalid role';
    RETURN;
  END IF;
  IF cur_role = 'admin' AND (next_role <> 'admin' OR NOT next_active) THEN
    SELECT count(*) INTO active_admins FROM public.admin_members
    WHERE public.admin_members.role = 'admin' AND public.admin_members.is_active;
    IF active_admins <= 1 THEN
      RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Cannot leave zero active admins';
      RETURN;
    END IF;
  END IF;
  UPDATE public.admin_members AS m
  SET role = next_role, is_active = next_active
  WHERE m.user_id = p_user_id;
  event_action := CASE
    WHEN cur_role <> next_role THEN 'role_change'
    WHEN current_active AND NOT next_active THEN 'deactivation'
    WHEN NOT current_active AND next_active THEN 'activation'
    ELSE p_action
  END;
  IF event_action NOT IN ('role_change', 'activation', 'deactivation', 'revoke') THEN
    event_action := 'role_change';
  END IF;
  INSERT INTO public.admin_membership_audit (actor_user_id, target_user_id, action, old_values, new_values)
  VALUES (
    actor_id, p_user_id, event_action,
    jsonb_build_object('role', cur_role, 'is_active', current_active),
    jsonb_build_object('role', next_role, 'is_active', next_active)
  );
  RETURN QUERY SELECT true, p_user_id, next_role, next_active, NULL::TEXT;
END;
$$;