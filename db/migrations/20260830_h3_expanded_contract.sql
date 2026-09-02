CREATE OR REPLACE FUNCTION public.admin_has_aal2()
RETURNS BOOLEAN
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  claim_aal TEXT;
BEGIN
  claim_aal := COALESCE((SELECT auth.jwt() ->> 'aal'), current_setting('request.jwt.claim.aal', true));
  RETURN claim_aal = 'aal2';
EXCEPTION WHEN OTHERS THEN
  RETURN false;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_has_aal2() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_has_aal2() TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.admin_require_aal2()
RETURNS VOID
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
  IF NOT public.admin_has_aal2() THEN
    RAISE EXCEPTION 'MFA aal2 required';
  END IF;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_require_aal2() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_require_aal2() TO authenticated, service_role;

CREATE TABLE IF NOT EXISTS public.admin_membership_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id UUID NOT NULL,
  target_user_id UUID NOT NULL,
  action TEXT NOT NULL,
  old_values JSONB NOT NULL DEFAULT '{}'::jsonb,
  new_values JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT admin_membership_audit_action_allowed CHECK (action IN ('invite', 'role_change', 'activation', 'deactivation', 'revoke'))
);

ALTER TABLE public.admin_membership_audit ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_membership_audit'::regclass
      AND conname = 'admin_membership_audit_action_allowed'
  ) THEN
    ALTER TABLE public.admin_membership_audit
      ADD CONSTRAINT admin_membership_audit_action_allowed
      CHECK (action IN ('invite', 'role_change', 'activation', 'deactivation', 'revoke'));
  END IF;
END;
$$;
REVOKE ALL ON TABLE public.admin_membership_audit FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON TABLE public.admin_membership_audit TO service_role;

CREATE OR REPLACE FUNCTION public.prevent_admin_membership_audit_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
  RAISE EXCEPTION 'admin_membership_audit is append-only';
END;
$$;

DROP TRIGGER IF EXISTS prevent_admin_membership_audit_update ON public.admin_membership_audit;
CREATE TRIGGER prevent_admin_membership_audit_update
BEFORE UPDATE ON public.admin_membership_audit
FOR EACH ROW EXECUTE FUNCTION public.prevent_admin_membership_audit_mutation();

DROP TRIGGER IF EXISTS prevent_admin_membership_audit_delete ON public.admin_membership_audit;
CREATE TRIGGER prevent_admin_membership_audit_delete
BEFORE DELETE ON public.admin_membership_audit
FOR EACH ROW EXECUTE FUNCTION public.prevent_admin_membership_audit_mutation();

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
  current_role TEXT;
  current_active BOOLEAN;
  active_admins INTEGER;
  next_role TEXT;
  next_active BOOLEAN;
  event_action TEXT;
  member_exists BOOLEAN;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_membership_mutation', 0));
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_admin() THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'User is not an active admin';
    RETURN;
  END IF;
  IF p_user_id = actor_id AND (p_is_active = false OR p_role = 'user') THEN
    SELECT count(*) INTO active_admins FROM public.admin_members WHERE role = 'admin' AND is_active;
    IF active_admins <= 1 THEN
      RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Cannot deactivate the last active admin';
      RETURN;
    END IF;
  END IF;
  SELECT am.role, am.is_active INTO current_role, current_active
  FROM public.admin_members am WHERE am.user_id = p_user_id FOR UPDATE;
  member_exists := current_role IS NOT NULL;
  IF current_role IS NULL THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Membership not found';
    RETURN;
  END IF;
  next_role := COALESCE(p_role, current_role);
  next_active := COALESCE(p_is_active, current_active);
  IF next_role NOT IN ('admin', 'user') THEN
    RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Invalid role';
    RETURN;
  END IF;
  IF current_role = 'admin' AND (next_role <> 'admin' OR NOT next_active) THEN
    SELECT count(*) INTO active_admins FROM public.admin_members WHERE role = 'admin' AND is_active;
    IF active_admins <= 1 THEN
      RETURN QUERY SELECT false, p_user_id, NULL::TEXT, NULL::BOOLEAN, 'Cannot leave zero active admins';
      RETURN;
    END IF;
  END IF;
  UPDATE public.admin_members SET role = next_role, is_active = next_active WHERE user_id = p_user_id;
  event_action := CASE
    WHEN current_role <> next_role THEN 'role_change'
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
    jsonb_build_object('role', current_role, 'is_active', current_active),
    jsonb_build_object('role', next_role, 'is_active', next_active)
  );
  RETURN QUERY SELECT true, p_user_id, next_role, next_active, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_update_member(UUID, TEXT, BOOLEAN, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_update_member(UUID, TEXT, BOOLEAN, TEXT) TO authenticated, service_role;
