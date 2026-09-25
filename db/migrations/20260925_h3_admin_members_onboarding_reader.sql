-- H3REQ1 compatibility reader for admin membership management.
-- The legacy admin_list_members() signature remains unchanged. This additive
-- RPC exposes onboarding state to the existing admin UI without changing the
-- old contract or granting direct table access.

CREATE OR REPLACE FUNCTION public.admin_list_members_onboarding()
RETURNS TABLE (
  user_id UUID,
  email TEXT,
  role TEXT,
  is_active BOOLEAN,
  created_at TIMESTAMPTZ,
  account_status TEXT,
  invitation_status TEXT,
  expires_at TIMESTAMPTZ
)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_admin() THEN
    RAISE EXCEPTION 'User is not an active admin';
  END IF;

  RETURN QUERY
  SELECT
    member.user_id,
    auth_user.email::text,
    member.role,
    member.is_active,
    member.created_at,
    member.account_status,
    invitation.status,
    invitation.expires_at
  FROM public.admin_members AS member
  JOIN auth.users AS auth_user ON auth_user.id = member.user_id
  LEFT JOIN LATERAL (
    SELECT current_invitation.status, current_invitation.expires_at
    FROM public.admin_invitations AS current_invitation
    WHERE current_invitation.id = member.last_invitation_id
       OR current_invitation.admin_member_user_id = member.user_id
    ORDER BY current_invitation.created_at DESC
    LIMIT 1
  ) AS invitation ON true
  ORDER BY member.created_at DESC;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_list_members_onboarding() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_list_members_onboarding() TO authenticated, service_role;

COMMENT ON FUNCTION public.admin_list_members_onboarding() IS
  'H3REQ1: admin-only membership reader exposing onboarding and invitation state; legacy reader remains unchanged.';
