-- H3REQ1 legacy compatibility guard.
-- The canonical invitation path is admin-invite -> Auth email -> callback/PKCE
-- -> accept -> password setup. The old direct membership RPC remains callable
-- for compatibility, but may no longer create a ready/active membership and
-- therefore cannot bypass onboarding.

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
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  actor_id UUID := (SELECT auth.uid());
  target_id UUID;
BEGIN
  IF actor_id IS NULL THEN
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

  SELECT auth_user.id
  INTO target_id
  FROM auth.users AS auth_user
  WHERE auth_user.email = lower(trim(p_email));

  IF target_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, 'Email not found in auth.users (invite must be created first)'::TEXT;
    RETURN;
  END IF;

  -- Do not INSERT here. A successful INSERT would default to ready/active and
  -- bypass Auth invitation, acceptance, password setup and onboarding audit.
  RETURN QUERY SELECT
    false,
    target_id,
    'Legacy membership creation disabled; use admin-invite'::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_create_member(TEXT, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_create_member(TEXT, TEXT) TO authenticated, service_role;

COMMENT ON FUNCTION public.admin_create_member(TEXT, TEXT) IS
  'H3REQ1 compatibility shim: validates legacy input but never creates a membership; use admin-invite for onboarding.';
