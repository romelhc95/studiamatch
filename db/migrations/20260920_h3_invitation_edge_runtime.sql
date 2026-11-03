-- H3-BUILD-03A-EDGE runtime support.
-- The Edge Function uses these service-role-only RPCs to keep reservation,
-- completion and failure transitions atomic within the database.
-- Auth remains the authority for invitation tokens and delivery.

ALTER TABLE public.admin_membership_audit
  ALTER COLUMN target_user_id DROP NOT NULL;

CREATE OR REPLACE FUNCTION public.admin_invitation_reserve(
  p_email TEXT,
  p_role TEXT,
  p_actor_user_id UUID,
  p_auth_user_id UUID DEFAULT NULL,
  p_resend BOOLEAN DEFAULT false,
  p_request_id TEXT DEFAULT NULL,
  p_metadata JSONB DEFAULT '{}'::JSONB,
  p_resend_cooldown_until TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
  success BOOLEAN,
  invitation_id UUID,
  member_id UUID,
  old_status TEXT,
  resent BOOLEAN,
  error_code TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  normalized_email TEXT := lower(btrim(p_email));
  member_row public.admin_members%ROWTYPE;
  pending_row public.admin_invitations%ROWTYPE;
  previous_id UUID;
  invitation_row public.admin_invitations%ROWTYPE;
BEGIN
  IF normalized_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
     OR p_role NOT IN ('admin', 'user')
     OR p_actor_user_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'none'::TEXT, false, 'invalid_request'::TEXT;
    RETURN;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.admin_members actor
    WHERE actor.user_id = p_actor_user_id
      AND actor.role = 'admin'
      AND actor.is_active = true
      AND actor.account_status = 'ready'
  ) THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'none'::TEXT, false, 'forbidden'::TEXT;
    RETURN;
  END IF;

  IF p_auth_user_id IS NOT NULL AND NOT EXISTS (
    SELECT 1
    FROM auth.users auth_user
    WHERE auth_user.id = p_auth_user_id
      AND lower(auth_user.email) = normalized_email
  ) THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'none'::TEXT, false, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  -- Serialize all decisions for one normalized email. The partial unique index
  -- remains the final defense if a caller bypasses this function.
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || normalized_email, 0));

  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  JOIN auth.users auth_user ON auth_user.id = member.user_id
  WHERE lower(auth_user.email) = normalized_email
  FOR UPDATE OF member;

  IF member_row.user_id IS NOT NULL THEN
    IF member_row.user_id <> p_auth_user_id THEN
      RETURN QUERY SELECT false, NULL::UUID, member_row.user_id, member_row.account_status, false, 'auth_identity_mismatch'::TEXT;
      RETURN;
    END IF;
    IF member_row.role <> p_role THEN
      RETURN QUERY SELECT false, NULL::UUID, member_row.user_id, member_row.account_status, false, 'role_mismatch'::TEXT;
      RETURN;
    END IF;
    IF member_row.account_status = 'ready' THEN
      RETURN QUERY SELECT false, NULL::UUID, member_row.user_id, 'ready'::TEXT, false, 'duplicate_ready'::TEXT;
      RETURN;
    END IF;
    IF member_row.account_status IN ('inactive', 'revoked') THEN
      RETURN QUERY SELECT false, NULL::UUID, member_row.user_id, member_row.account_status, false, 'membership_blocked'::TEXT;
      RETURN;
    END IF;
    IF member_row.account_status <> 'invited' THEN
      RETURN QUERY SELECT false, NULL::UUID, member_row.user_id, member_row.account_status, false, 'onboarding_in_progress'::TEXT;
      RETURN;
    END IF;
    UPDATE public.admin_members
    SET is_active = false
    WHERE user_id = member_row.user_id AND is_active = true;
    member_row.is_active := false;
  END IF;

  SELECT invitation.*
  INTO pending_row
  FROM public.admin_invitations invitation
  WHERE invitation.email = normalized_email
    AND invitation.status = 'pending'
  ORDER BY invitation.created_at DESC
  LIMIT 1
  FOR UPDATE;

  IF pending_row.id IS NOT NULL AND pending_row.expires_at <= now() THEN
    UPDATE public.admin_invitations
    SET status = 'expired'
    WHERE id = pending_row.id;
    pending_row := NULL;
  END IF;

  IF pending_row.id IS NOT NULL THEN
    IF NOT p_resend THEN
      RETURN QUERY SELECT false, NULL::UUID, COALESCE(member_row.user_id, pending_row.admin_member_user_id), 'pending'::TEXT, false, 'duplicate_pending'::TEXT;
      RETURN;
    END IF;
    IF p_resend_cooldown_until IS NOT NULL AND pending_row.last_sent_at >= p_resend_cooldown_until THEN
      RETURN QUERY SELECT false, NULL::UUID, COALESCE(member_row.user_id, pending_row.admin_member_user_id), 'pending'::TEXT, false, 'resend_cooldown'::TEXT;
      RETURN;
    END IF;
    previous_id := pending_row.id;
    UPDATE public.admin_invitations
    SET status = 'superseded'
    WHERE id = pending_row.id;
  END IF;

  IF member_row.user_id IS NULL AND p_auth_user_id IS NOT NULL THEN
    INSERT INTO public.admin_members (
      user_id, role, is_active, account_status, invited_at, last_invited_at,
      invited_by, status_reason
    )
    VALUES (
      p_auth_user_id, p_role, false, 'invited', now(), now(),
      p_actor_user_id, 'invitation_reserved'
    )
    RETURNING * INTO member_row;
  END IF;

  INSERT INTO public.admin_invitations (
    admin_member_user_id,
    email,
    role,
    token_hash,
    status,
    created_by_user_id,
    expires_at,
    last_sent_at,
    send_count,
    resend_of_invitation_id,
    metadata
  )
  VALUES (
    member_row.user_id,
    normalized_email,
    COALESCE(member_row.role, p_role),
    NULL,
    'pending',
    p_actor_user_id,
    now() + interval '48 hours',
    now(),
    COALESCE(pending_row.send_count, 0) + 1,
    previous_id,
    jsonb_build_object(
      'source', 'admin-invite',
      'request_id', COALESCE(p_request_id, ''),
      'reserved', true
    ) || COALESCE(p_metadata, '{}'::JSONB)
  )
  RETURNING * INTO invitation_row;

  RETURN QUERY SELECT true, invitation_row.id, COALESCE(member_row.user_id, p_auth_user_id), COALESCE(member_row.account_status, 'none'), previous_id IS NOT NULL, NULL::TEXT;
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_invitation_record_failure(
  p_email TEXT,
  p_role TEXT,
  p_actor_user_id UUID,
  p_auth_user_id UUID,
  p_failure_code TEXT,
  p_request_id TEXT DEFAULT NULL,
  p_metadata JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE (success BOOLEAN, invitation_id UUID, error_code TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  normalized_email TEXT := lower(btrim(p_email));
  target_id UUID := p_auth_user_id;
  failure_invitation_id UUID;
BEGIN
  IF normalized_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
     OR p_role NOT IN ('admin', 'user')
     OR p_actor_user_id IS NULL
     OR p_failure_code IS NULL
     OR btrim(p_failure_code) !~ '^[a-z][a-z0-9_]{2,63}$' THEN
    RETURN QUERY SELECT false, NULL::UUID, 'invalid_request'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || normalized_email, 0));

  IF target_id IS NULL THEN
    SELECT auth_user.id
    INTO target_id
    FROM auth.users auth_user
    WHERE lower(auth_user.email) = normalized_email;
  END IF;

  IF target_id IS NULL THEN
    target_id := p_actor_user_id;
  END IF;

  INSERT INTO public.admin_invitations (
    admin_member_user_id, email, role, token_hash, status, created_by_user_id,
    expires_at, last_sent_at, send_count, failure_code, metadata
  )
  VALUES (
    CASE WHEN p_auth_user_id IS NULL THEN NULL ELSE target_id END,
    normalized_email, p_role, NULL, 'send_failed', p_actor_user_id,
    now() + interval '48 hours', now(), 1, p_failure_code,
    jsonb_build_object('source', 'admin-invite', 'request_id', COALESCE(p_request_id, '')) || COALESCE(p_metadata, '{}'::JSONB)
  )
  RETURNING id INTO failure_invitation_id;

  INSERT INTO public.admin_membership_audit (
    actor_user_id, target_user_id, entity_type, invitation_id, action,
    old_values, new_values, metadata
  )
  VALUES (
    p_actor_user_id, target_id, 'invitation', failure_invitation_id, 'send_failed',
    '{}'::JSONB, jsonb_build_object('status', 'send_failed', 'failure_code', p_failure_code),
      jsonb_build_object(
        'email', normalized_email,
        'request_id', COALESCE(p_request_id, ''),
        'target_user_id_unresolved', p_auth_user_id IS NULL
      ) || COALESCE(p_metadata, '{}'::JSONB)
  );

  RETURN QUERY SELECT true, failure_invitation_id, NULL::TEXT;
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_invitation_complete(
  p_invitation_id UUID,
  p_auth_user_id UUID
)
RETURNS TABLE (success BOOLEAN, member_id UUID, error_code TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  invitation_row public.admin_invitations%ROWTYPE;
  member_row public.admin_members%ROWTYPE;
  action_name TEXT;
BEGIN
  SELECT invitation.*
  INTO invitation_row
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id
  FOR UPDATE;

  IF invitation_row.id IS NULL OR invitation_row.status <> 'pending' THEN
    RETURN QUERY SELECT false, NULL::UUID, 'invitation_not_pending'::TEXT;
    RETURN;
  END IF;
  IF p_auth_user_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, 'missing_auth_user'::TEXT;
    RETURN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = p_auth_user_id AND lower(email) = invitation_row.email) THEN
    RETURN QUERY SELECT false, NULL::UUID, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  WHERE member.user_id = p_auth_user_id
  FOR UPDATE;

  IF member_row.user_id IS NULL THEN
    INSERT INTO public.admin_members (
      user_id, role, is_active, account_status, invited_at, last_invited_at,
      invited_by, last_invitation_id, status_reason
    )
    VALUES (
      p_auth_user_id, invitation_row.role, false, 'invited', now(), now(),
      invitation_row.created_by_user_id, invitation_row.id, 'invitation_sent'
    )
    RETURNING * INTO member_row;
  ELSIF member_row.account_status <> 'invited' THEN
    RETURN QUERY SELECT false, member_row.user_id, 'membership_state_changed'::TEXT;
    RETURN;
  ELSE
    UPDATE public.admin_members
    SET last_invitation_id = invitation_row.id,
        last_invited_at = now(),
        invited_by = invitation_row.created_by_user_id,
        status_reason = 'invitation_sent'
    WHERE user_id = p_auth_user_id;
  END IF;

  UPDATE public.admin_invitations
  SET admin_member_user_id = p_auth_user_id
  WHERE id = invitation_row.id;

  action_name := CASE WHEN invitation_row.resend_of_invitation_id IS NULL THEN 'invite' ELSE 'resend' END;
  INSERT INTO public.admin_membership_audit (
    actor_user_id, target_user_id, entity_type, invitation_id, action,
    old_values, new_values, metadata
  )
  VALUES (
    invitation_row.created_by_user_id, p_auth_user_id, 'invitation', invitation_row.id, action_name,
    jsonb_build_object(
      'account_status',
      CASE WHEN invitation_row.resend_of_invitation_id IS NULL THEN 'none' ELSE 'invited' END
    ),
    jsonb_build_object('account_status', 'invited', 'role', invitation_row.role),
    invitation_row.metadata || jsonb_build_object(
      'email', invitation_row.email,
      'result', 'auth_accepted'
    )
  );

  RETURN QUERY SELECT true, p_auth_user_id, NULL::TEXT;
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_invitation_fail(
  p_invitation_id UUID,
  p_auth_user_id UUID,
  p_failure_code TEXT
)
RETURNS TABLE (success BOOLEAN, error_code TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  invitation_row public.admin_invitations%ROWTYPE;
  target_id UUID := p_auth_user_id;
BEGIN
  IF p_failure_code IS NULL OR btrim(p_failure_code) !~ '^[a-z][a-z0-9_]{2,63}$' THEN
    RETURN QUERY SELECT false, 'invalid_failure_code'::TEXT;
    RETURN;
  END IF;

  SELECT invitation.*
  INTO invitation_row
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id
  FOR UPDATE;
  IF invitation_row.id IS NULL THEN
    RETURN QUERY SELECT false, 'invitation_not_found'::TEXT;
    RETURN;
  END IF;
  IF invitation_row.status <> 'pending' THEN
    RETURN QUERY SELECT false, 'invitation_not_pending'::TEXT;
    RETURN;
  END IF;

  IF target_id IS NULL THEN
    SELECT member.user_id
    INTO target_id
    FROM public.admin_members member
    JOIN auth.users auth_user ON auth_user.id = member.user_id
    WHERE lower(auth_user.email) = invitation_row.email;
  END IF;

  UPDATE public.admin_invitations
  SET status = 'send_failed',
      failure_code = p_failure_code,
      metadata = invitation_row.metadata || jsonb_build_object('failure_code', p_failure_code)
  WHERE id = invitation_row.id;

  INSERT INTO public.admin_membership_audit (
    actor_user_id, target_user_id, entity_type, invitation_id, action,
    old_values, new_values, metadata
  )
  VALUES (
    invitation_row.created_by_user_id, target_id, 'invitation', invitation_row.id, 'send_failed',
    jsonb_build_object('status', 'pending'),
    jsonb_build_object('status', 'send_failed', 'failure_code', p_failure_code),
    invitation_row.metadata
  );

  RETURN QUERY SELECT true, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_invitation_reserve(TEXT, TEXT, UUID, UUID, BOOLEAN, TEXT, JSONB, TIMESTAMPTZ) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.admin_invitation_record_failure(TEXT, TEXT, UUID, UUID, TEXT, TEXT, JSONB) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.admin_invitation_complete(UUID, UUID) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.admin_invitation_fail(UUID, UUID, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_invitation_reserve(TEXT, TEXT, UUID, UUID, BOOLEAN, TEXT, JSONB, TIMESTAMPTZ) TO service_role;
GRANT EXECUTE ON FUNCTION public.admin_invitation_record_failure(TEXT, TEXT, UUID, UUID, TEXT, TEXT, JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION public.admin_invitation_complete(UUID, UUID) TO service_role;
GRANT EXECUTE ON FUNCTION public.admin_invitation_fail(UUID, UUID, TEXT) TO service_role;
