-- Follow-up to 20260924_h3_onboarding_rbac_hardening.
-- The local variable uses `cur_role` to avoid PostgreSQL's current-role
-- identifier collision while preserving the same function signature and ACL.

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

REVOKE ALL ON FUNCTION public.admin_current_user_role() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_current_user_role() TO authenticated, service_role;
