-- H3 invitation onboarding remediation.
--
-- The Free/Development function definition drifted from the versioned
-- contract: its email validation contained two backslashes before the dot,
-- rejecting every normal email address before the invitation transition.
-- Re-assert the canonical function body with the single escaped dot below.
-- This migration is intentionally separate so the remote DDL approval and
-- evidence remain traceable.

CREATE OR REPLACE FUNCTION public.admin_accept_current_invitation(
  p_invitation_id UUID DEFAULT NULL
)
RETURNS TABLE (
  success BOOLEAN,
  invitation_id UUID,
  member_id UUID,
  account_status TEXT,
  role TEXT,
  error_code TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  actor_id UUID := (SELECT auth.uid());
  auth_email TEXT;
  normalized_email TEXT;
  invitation_row public.admin_invitations%ROWTYPE;
  member_row public.admin_members%ROWTYPE;
  accepted_at_ts TIMESTAMPTZ;
BEGIN
  IF actor_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, NULL::TEXT, NULL::TEXT, 'missing_auth_user'::TEXT;
    RETURN;
  END IF;

  accepted_at_ts := clock_timestamp();

  SELECT auth_user.email::TEXT
  INTO auth_email
  FROM auth.users auth_user
  WHERE auth_user.id = actor_id;
  normalized_email := lower(btrim(auth_email));
  IF normalized_email IS NULL OR normalized_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, NULL::TEXT, NULL::TEXT, 'missing_auth_user'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_onboarding_email:' || normalized_email, 0));
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_onboarding_user:' || actor_id::TEXT, 0));

  IF p_invitation_id IS NULL THEN
    SELECT invitation.*
    INTO invitation_row
    FROM public.admin_invitations invitation
    WHERE invitation.email = normalized_email
      AND invitation.status = 'pending'
    ORDER BY invitation.created_at DESC
    LIMIT 1
    FOR UPDATE;

    IF invitation_row.id IS NULL THEN
      SELECT invitation.*
      INTO invitation_row
      FROM public.admin_invitations invitation
      WHERE invitation.email = normalized_email
      ORDER BY invitation.created_at DESC
      LIMIT 1
      FOR UPDATE;
    END IF;
  ELSE
    SELECT invitation.*
    INTO invitation_row
    FROM public.admin_invitations invitation
    WHERE invitation.id = p_invitation_id
    FOR UPDATE;
    IF invitation_row.id IS NULL THEN
      RETURN QUERY SELECT false, p_invitation_id, actor_id, NULL::TEXT, NULL::TEXT, 'invitation_not_pending'::TEXT;
      RETURN;
    END IF;
    IF invitation_row.email <> normalized_email THEN
      RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'auth_identity_mismatch'::TEXT;
      RETURN;
    END IF;
  END IF;

  IF invitation_row.id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, actor_id, NULL::TEXT, NULL::TEXT, 'invitation_not_pending'::TEXT;
    RETURN;
  END IF;

  IF invitation_row.status = 'pending' AND invitation_row.expires_at <= now() THEN
    UPDATE public.admin_invitations AS invitation
    SET status = 'expired'
    WHERE invitation.id = invitation_row.id;
    IF NOT EXISTS (
      SELECT 1 FROM public.admin_membership_audit audit_row
      WHERE audit_row.invitation_id = invitation_row.id AND audit_row.action = 'expire'
    ) THEN
      INSERT INTO public.admin_membership_audit (
        actor_user_id, target_user_id, entity_type, invitation_id, action,
        old_values, new_values, metadata
      ) VALUES (
        actor_id, invitation_row.admin_member_user_id, 'invitation', invitation_row.id, 'expire',
        jsonb_build_object('status', 'pending'),
        jsonb_build_object('status', 'expired'),
        jsonb_build_object('source', 'admin_accept_current_invitation')
      );
    END IF;
    RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'invitation_expired'::TEXT;
    RETURN;
  END IF;

  IF invitation_row.status = 'revoked' THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'invitation_revoked'::TEXT;
    RETURN;
  ELSIF invitation_row.status = 'superseded' THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'invitation_superseded'::TEXT;
    RETURN;
  ELSIF invitation_row.status = 'expired' THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'invitation_expired'::TEXT;
    RETURN;
  ELSIF invitation_row.status = 'send_failed' THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'invitation_not_pending'::TEXT;
    RETURN;
  ELSIF invitation_row.status = 'accepted' THEN
    IF invitation_row.accepted_user_id IS DISTINCT FROM actor_id THEN
      RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'auth_identity_mismatch'::TEXT;
      RETURN;
    END IF;
    SELECT member.*
    INTO member_row
    FROM public.admin_members member
    WHERE member.user_id = actor_id
    FOR UPDATE;
    IF member_row.user_id IS NULL OR member_row.last_invitation_id <> invitation_row.id
       OR member_row.account_status NOT IN ('password_pending', 'ready')
       OR member_row.role <> invitation_row.role THEN
      RETURN QUERY SELECT false, invitation_row.id, actor_id, COALESCE(member_row.account_status, NULL::TEXT), invitation_row.role, 'reconciliation_required'::TEXT;
      RETURN;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM public.admin_membership_audit audit_row
      WHERE audit_row.invitation_id = invitation_row.id AND audit_row.action = 'accept'
    ) THEN
      INSERT INTO public.admin_membership_audit (
        actor_user_id, target_user_id, entity_type, invitation_id, action,
        old_values, new_values, metadata
      ) VALUES (
        actor_id, actor_id, 'invitation', invitation_row.id, 'accept',
        jsonb_build_object('account_status', 'invited'),
        jsonb_build_object('account_status', member_row.account_status, 'role', member_row.role),
        jsonb_build_object('source', 'admin_accept_current_invitation', 'idempotent', true)
      );
    END IF;
    RETURN QUERY SELECT true, invitation_row.id, actor_id, member_row.account_status, member_row.role, NULL::TEXT;
    RETURN;
  END IF;

  IF invitation_row.admin_member_user_id IS NOT NULL AND invitation_row.admin_member_user_id <> actor_id THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  WHERE member.user_id = actor_id
  FOR UPDATE;
  IF member_row.user_id IS NULL THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, NULL::TEXT, invitation_row.role, 'reconciliation_required'::TEXT;
    RETURN;
  END IF;
  IF member_row.role <> invitation_row.role THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, member_row.account_status, member_row.role, 'role_mismatch'::TEXT;
    RETURN;
  END IF;
  IF member_row.account_status IN ('inactive', 'revoked') THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, member_row.account_status, member_row.role, 'membership_state_changed'::TEXT;
    RETURN;
  END IF;
  IF member_row.account_status <> 'invited' THEN
    RETURN QUERY SELECT false, invitation_row.id, actor_id, member_row.account_status, member_row.role, 'membership_state_changed'::TEXT;
    RETURN;
  END IF;

  UPDATE public.admin_invitations AS invitation
  SET admin_member_user_id = actor_id,
      status = 'accepted',
      accepted_user_id = actor_id,
      accepted_at = accepted_at_ts
  WHERE invitation.id = invitation_row.id;

  UPDATE public.admin_members AS member
  SET account_status = 'accepted',
      is_active = false,
      accepted_at = accepted_at_ts,
      last_invitation_id = invitation_row.id,
      status_reason = 'invitation_accepted'
  WHERE member.user_id = actor_id;

  UPDATE public.admin_members AS member
  SET account_status = 'password_pending',
      is_active = false,
      status_reason = 'password_setup_pending'
  WHERE member.user_id = actor_id;

  INSERT INTO public.admin_membership_audit (
    actor_user_id, target_user_id, entity_type, invitation_id, action,
    old_values, new_values, metadata
  ) VALUES (
    actor_id, actor_id, 'invitation', invitation_row.id, 'accept',
    jsonb_build_object('account_status', 'invited', 'invitation_status', 'pending'),
    jsonb_build_object('account_status', 'password_pending', 'invitation_status', 'accepted', 'role', invitation_row.role),
    jsonb_build_object('source', 'admin_accept_current_invitation')
  );

  RETURN QUERY SELECT true, invitation_row.id, actor_id, 'password_pending'::TEXT, invitation_row.role, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_accept_current_invitation(UUID) IS
  'Accepts the pending Auth invitation for the current authenticated identity and advances it to password setup.';
