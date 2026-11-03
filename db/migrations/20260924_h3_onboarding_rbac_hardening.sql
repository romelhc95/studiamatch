-- H3REQ1 compatibility hardening for onboarding-aware RBAC.
-- Expand-only: legacy rows default to account_status = ready and retain the
-- existing admin/user workflow. New or incomplete onboarding states cannot be
-- activated through the administrative membership RPC.

CREATE OR REPLACE FUNCTION public.admin_current_user_role()
RETURNS TEXT LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  current_user_id UUID := (SELECT auth.uid());
  cur_role TEXT;
BEGIN
  IF current_user_id IS NULL THEN
    RETURN 'anon';
  END IF;

  SELECT member.role
  INTO cur_role
  FROM public.admin_members AS member
  WHERE member.user_id = current_user_id
    AND member.is_active = true
    AND member.account_status = 'ready';

  RETURN COALESCE(cur_role, 'authenticated');
EXCEPTION WHEN OTHERS THEN
  RETURN 'error';
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_is_active_admin()
RETURNS BOOLEAN LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  current_user_id UUID := (SELECT auth.uid());
BEGIN
  RETURN current_user_id IS NOT NULL AND EXISTS (
    SELECT 1
    FROM public.admin_members AS member
    WHERE member.user_id = current_user_id
      AND member.role = 'admin'
      AND member.is_active = true
      AND member.account_status = 'ready'
  );
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_is_active_editor()
RETURNS BOOLEAN LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  current_user_id UUID := (SELECT auth.uid());
BEGIN
  RETURN current_user_id IS NOT NULL AND EXISTS (
    SELECT 1
    FROM public.admin_members AS member
    WHERE member.user_id = current_user_id
      AND member.role IN ('admin', 'user')
      AND member.is_active = true
      AND member.account_status = 'ready'
  );
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_user_can_edit_field(
  p_course_id UUID,
  p_field_key TEXT
)
RETURNS BOOLEAN LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  current_user_id UUID := (SELECT auth.uid());
  current_role TEXT;
BEGIN
  SELECT member.role
  INTO current_role
  FROM public.admin_members AS member
  WHERE member.user_id = current_user_id
    AND member.is_active = true
    AND member.account_status = 'ready';

  IF current_role IS NULL THEN
    RETURN false;
  END IF;
  IF current_role = 'admin' THEN
    RETURN true;
  END IF;

  RETURN EXISTS (
    SELECT 1
    FROM public.course_editorial_state AS editorial_state
    WHERE editorial_state.course_id = p_course_id
      AND p_field_key = ANY (editorial_state.missing_fields)
  );
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
  target_role TEXT;
  target_active BOOLEAN;
  target_status TEXT;
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

  SELECT member.role, member.is_active, member.account_status
  INTO target_role, target_active, target_status
  FROM public.admin_members AS member
  WHERE member.user_id = p_user_id
  FOR UPDATE;
  IF target_role IS NULL THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Membership not found';
    RETURN;
  END IF;

  -- Activation is intentionally separate from onboarding completion. Only the
  -- password-complete ready state may receive an active flag.
  IF p_is_active = true AND target_status <> 'ready' THEN
    RETURN QUERY SELECT false, p_user_id, target_role, target_active, 'Membership onboarding is not ready';
    RETURN;
  END IF;

  next_role := COALESCE(p_role, target_role);
  next_active := COALESCE(p_is_active, target_active);
  IF next_role NOT IN ('admin', 'user') THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Invalid role';
    RETURN;
  END IF;
  IF p_user_id = actor_id AND (p_is_active = false OR p_role = 'user') THEN
    SELECT count(*) INTO active_admins
    FROM public.admin_members AS member
    WHERE member.role = 'admin' AND member.is_active = true AND member.account_status = 'ready';
    IF active_admins <= 1 THEN
      RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Cannot deactivate the last active admin';
      RETURN;
    END IF;
  END IF;
  IF target_role = 'admin' AND (next_role <> 'admin' OR NOT next_active) THEN
    SELECT count(*) INTO active_admins
    FROM public.admin_members AS member
    WHERE member.role = 'admin' AND member.is_active = true AND member.account_status = 'ready';
    IF active_admins <= 1 THEN
      RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Cannot leave zero active admins';
      RETURN;
    END IF;
  END IF;

  UPDATE public.admin_members AS member
  SET role = next_role,
      is_active = next_active
  WHERE member.user_id = p_user_id;

  event_action := CASE
    WHEN target_role <> next_role THEN 'role_change'
    WHEN target_active AND NOT next_active THEN 'deactivation'
    WHEN NOT target_active AND next_active THEN 'activation'
    ELSE p_action
  END;
  IF event_action NOT IN ('role_change', 'activation', 'deactivation', 'revoke') THEN
    event_action := 'role_change';
  END IF;
  INSERT INTO public.admin_membership_audit (actor_user_id, target_user_id, action, old_values, new_values)
  VALUES (
    actor_id, p_user_id, event_action,
    jsonb_build_object('role', target_role, 'is_active', target_active, 'account_status', target_status),
    jsonb_build_object('role', next_role, 'is_active', next_active, 'account_status', target_status)
  );
  RETURN QUERY SELECT true, p_user_id, next_role, next_active, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_current_user_role() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_is_active_admin() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_is_active_editor() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_user_can_edit_field(UUID, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_update_member(UUID, TEXT, BOOLEAN, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_current_user_role() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_is_active_admin() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_is_active_editor() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_user_can_edit_field(UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_update_member(UUID, TEXT, BOOLEAN, TEXT) TO authenticated, service_role;

COMMENT ON FUNCTION public.admin_update_member(UUID, TEXT, BOOLEAN, TEXT) IS
  'H3REQ1: membership role/active mutations preserve last-admin protection and cannot activate incomplete onboarding.';
