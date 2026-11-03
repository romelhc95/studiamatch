-- Local H3 delta: reserve the invitation row before calling Auth, serialize
-- failures with the same per-email advisory lock, restore a superseded
-- invitation only on definitive rejection, and audit ambiguous delivery without
-- invalidating a link that Auth may already have sent.
-- Applying this migration to any Supabase project requires separate JIT DDL.

CREATE OR REPLACE FUNCTION public.guard_admin_invitations_status_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
  IF NEW.status = OLD.status THEN
    RETURN NEW;
  END IF;

  -- Only admin_invitation_fail sets this transaction-local marker, after it
  -- has failed the new reservation and while holding the per-email lock.
  IF OLD.status = 'superseded'
     AND NEW.status = 'pending'
     AND current_setting('app.admin_invitation_restore_id', true) = NEW.id::TEXT THEN
    NEW.revoked_at := NULL;
    RETURN NEW;
  END IF;

  IF OLD.status <> 'pending' THEN
    RAISE EXCEPTION 'admin_invitations invalid status transition % -> %: only pending invitations change status', OLD.status, NEW.status;
  END IF;
  IF NEW.status NOT IN ('accepted', 'expired', 'revoked', 'superseded', 'send_failed') THEN
    RAISE EXCEPTION 'admin_invitations invalid status transition % -> %', OLD.status, NEW.status;
  END IF;
  IF NEW.status = 'accepted' THEN
    NEW.accepted_at := COALESCE(NEW.accepted_at, now());
  END IF;
  IF NEW.status IN ('revoked', 'superseded') THEN
    NEW.revoked_at := COALESCE(NEW.revoked_at, now());
  END IF;
  IF NEW.status = 'send_failed'
     AND (NEW.failure_code IS NULL OR length(btrim(NEW.failure_code)) = 0) THEN
    RAISE EXCEPTION 'admin_invitations send_failed transition requires failure_code';
  END IF;
  RETURN NEW;
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
  invitation_email TEXT;
  initial_member_id UUID;
  lock_member_id UUID;
  invitation_row public.admin_invitations%ROWTYPE;
  target_id UUID := p_auth_user_id;
  restored_previous_id UUID;
BEGIN
  IF p_invitation_id IS NULL
     OR p_failure_code IS NULL
     OR btrim(p_failure_code) !~ '^[a-z][a-z0-9_]{2,63}$' THEN
    RETURN QUERY SELECT false, 'invalid_failure_code'::TEXT;
    RETURN;
  END IF;

  -- Read lookup keys first, then use membership-before-invitation row locks.
  -- Audit FK checks also touch the membership row, so the reverse order can
  -- deadlock with admin_get_onboarding_status.
  SELECT lower(invitation.email::TEXT), invitation.admin_member_user_id
  INTO invitation_email, initial_member_id
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id;
  IF invitation_email IS NULL THEN
    RETURN QUERY SELECT false, 'invitation_not_found'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || invitation_email, 0));

  IF target_id IS NULL THEN
    SELECT member.user_id
    INTO target_id
    FROM public.admin_members member
    JOIN auth.users auth_user ON auth_user.id = member.user_id
    WHERE lower(auth_user.email::TEXT) = invitation_email;
  END IF;
  lock_member_id := COALESCE(target_id, initial_member_id);
  PERFORM 1
  FROM public.admin_members member
  WHERE member.user_id = lock_member_id
  FOR UPDATE;

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

  IF lower(invitation_row.email::TEXT) <> invitation_email
     OR invitation_row.admin_member_user_id IS DISTINCT FROM initial_member_id THEN
    RETURN QUERY SELECT false, 'invitation_changed_retry'::TEXT;
    RETURN;
  END IF;

  UPDATE public.admin_invitations
  SET status = 'send_failed',
      failure_code = p_failure_code,
      metadata = invitation_row.metadata || jsonb_build_object('failure_code', p_failure_code)
  WHERE id = invitation_row.id;

  -- A definitive Auth rejection/rate limit means no resend was emitted. Restore
  -- the previous unexpired invitation atomically. Persistence errors after an
  -- Auth call remain in reconciliation and never resurrect an old link.
  IF p_failure_code IN ('auth_invite_failed', 'auth_recovery_failed', 'auth_rate_limited')
     AND invitation_row.resend_of_invitation_id IS NOT NULL THEN
    PERFORM set_config(
      'app.admin_invitation_restore_id',
      invitation_row.resend_of_invitation_id::TEXT,
      true
    );
    UPDATE public.admin_invitations previous
    SET status = 'pending',
        revoked_at = NULL
    WHERE previous.id = invitation_row.resend_of_invitation_id
      AND previous.email = invitation_row.email
      AND previous.status = 'superseded'
      AND previous.expires_at > clock_timestamp()
      AND NOT EXISTS (
        SELECT 1
        FROM public.admin_invitations active
        WHERE active.email = invitation_row.email
          AND active.status = 'pending'
      )
    RETURNING previous.id INTO restored_previous_id;
    PERFORM set_config('app.admin_invitation_restore_id', '', true);
  END IF;

  INSERT INTO public.admin_membership_audit (
    actor_user_id, target_user_id, entity_type, invitation_id, action,
    old_values, new_values, metadata
  )
  VALUES (
    invitation_row.created_by_user_id, target_id, 'invitation', invitation_row.id, 'send_failed',
    jsonb_build_object('status', 'pending'),
    jsonb_build_object(
      'status', 'send_failed',
      'failure_code', p_failure_code,
      'restored_previous_invitation_id', restored_previous_id
    ),
    invitation_row.metadata || jsonb_build_object(
      'failure_code', p_failure_code,
      'restored_previous_invitation_id', restored_previous_id
    )
  );

  RETURN QUERY SELECT true, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_invitation_fail(UUID, UUID, TEXT)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_invitation_fail(UUID, UUID, TEXT)
  TO service_role;

COMMENT ON FUNCTION public.admin_invitation_fail(UUID, UUID, TEXT) IS
  'Serializes invitation send failure with reservation and restores an unexpired superseded row only after a definitive Auth rejection.';

CREATE OR REPLACE FUNCTION public.admin_invitation_expire(
  p_invitation_id UUID,
  p_actor_user_id UUID
)
RETURNS TABLE (success BOOLEAN, error_code TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  invitation_email TEXT;
  initial_member_id UUID;
  invitation_row public.admin_invitations%ROWTYPE;
BEGIN
  IF p_invitation_id IS NULL OR p_actor_user_id IS NULL THEN
    RETURN QUERY SELECT false, 'invalid_request'::TEXT;
    RETURN;
  END IF;

  SELECT lower(invitation.email::TEXT), invitation.admin_member_user_id
  INTO invitation_email, initial_member_id
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id;
  IF invitation_email IS NULL THEN
    RETURN QUERY SELECT false, 'invitation_not_found'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || invitation_email, 0));
  PERFORM 1
  FROM public.admin_members member
  WHERE member.user_id = initial_member_id
  FOR UPDATE;

  SELECT invitation.*
  INTO invitation_row
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id
  FOR UPDATE;
  IF invitation_row.id IS NULL THEN
    RETURN QUERY SELECT false, 'invitation_not_found'::TEXT;
    RETURN;
  END IF;
  IF lower(invitation_row.email::TEXT) <> invitation_email
     OR invitation_row.admin_member_user_id IS DISTINCT FROM initial_member_id THEN
    RETURN QUERY SELECT false, 'invitation_changed_retry'::TEXT;
    RETURN;
  END IF;
  IF invitation_row.status = 'pending' AND invitation_row.expires_at <= clock_timestamp() THEN
    UPDATE public.admin_invitations AS invitation
    SET status = 'expired'
    WHERE invitation.id = invitation_row.id;
  ELSIF invitation_row.status NOT IN ('expired') THEN
    RETURN QUERY SELECT false, CASE
      WHEN invitation_row.status <> 'pending' THEN 'invitation_not_pending'
      ELSE 'invitation_not_expired'
    END::TEXT;
    RETURN;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.admin_membership_audit audit_row
    WHERE audit_row.invitation_id = invitation_row.id AND audit_row.action = 'expire'
  ) THEN
    INSERT INTO public.admin_membership_audit (
      actor_user_id, target_user_id, entity_type, invitation_id, action,
      old_values, new_values, metadata
    ) VALUES (
      p_actor_user_id, invitation_row.admin_member_user_id, 'invitation', invitation_row.id, 'expire',
      jsonb_build_object('status', 'pending'),
      jsonb_build_object('status', 'expired'),
      jsonb_build_object('source', 'admin-invite-expiry', 'request_id', COALESCE(invitation_row.metadata ->> 'request_id', ''))
    );
  END IF;

  RETURN QUERY SELECT true, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_invitation_expire(UUID, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_invitation_expire(UUID, UUID)
  TO service_role;

COMMENT ON FUNCTION public.admin_invitation_expire(UUID, UUID) IS
  'Expires a pending invitation under the shared email lock and creates its audit record idempotently.';

-- Re-assert reservation with request-id idempotency inside the same per-email
-- critical section. The Edge preflight is only an optimization; this check is
-- what prevents two concurrent retries from creating two Auth sends.
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
  sent_at TIMESTAMPTZ := clock_timestamp();
  member_row public.admin_members%ROWTYPE;
  pending_row public.admin_invitations%ROWTYPE;
  previous_id UUID;
  invitation_row public.admin_invitations%ROWTYPE;
BEGIN
  IF normalized_email IS NULL
     OR normalized_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
     OR p_role IS NULL
     OR p_role NOT IN ('admin', 'user')
     OR (p_request_id IS NOT NULL AND btrim(p_request_id) !~ '^[A-Za-z0-9._:-]{1,100}$')
     OR p_actor_user_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'none'::TEXT, false, 'invalid_request'::TEXT;
    RETURN;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.admin_members actor
    WHERE actor.user_id = p_actor_user_id
      AND actor.role = 'admin'
      AND actor.is_active = true
      AND actor.account_status = 'ready'
  ) THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'none'::TEXT, false, 'forbidden'::TEXT;
    RETURN;
  END IF;

  IF p_auth_user_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM auth.users auth_user
    WHERE auth_user.id = p_auth_user_id
      AND lower(auth_user.email::TEXT) = normalized_email
  ) THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'none'::TEXT, false, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || normalized_email, 0));

  IF p_request_id IS NOT NULL THEN
    PERFORM pg_advisory_xact_lock(hashtextextended(
      'h3_admin_invite_request:' || p_actor_user_id::TEXT || ':' || p_request_id,
      0
    ));
    IF EXISTS (
       SELECT 1 FROM public.admin_invitations existing
       WHERE existing.created_by_user_id = p_actor_user_id
         AND existing.metadata ->> 'request_id' = p_request_id
    ) THEN
      RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'pending'::TEXT, false, 'reconciliation_required'::TEXT;
      RETURN;
    END IF;
  END IF;

  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  JOIN auth.users auth_user ON auth_user.id = member.user_id
  WHERE lower(auth_user.email::TEXT) = normalized_email
  FOR UPDATE OF member;

  IF member_row.user_id IS NOT NULL THEN
    IF member_row.user_id IS DISTINCT FROM p_auth_user_id THEN
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
    UPDATE public.admin_members AS member
    SET is_active = false
    WHERE member.user_id = member_row.user_id AND member.is_active = true;
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
    UPDATE public.admin_invitations AS invitation
    SET status = 'expired'
    WHERE invitation.id = pending_row.id;
    INSERT INTO public.admin_membership_audit (
      actor_user_id, target_user_id, entity_type, invitation_id, action,
      old_values, new_values, metadata
    )
    SELECT p_actor_user_id, pending_row.admin_member_user_id, 'invitation', pending_row.id, 'expire',
      jsonb_build_object('status', 'pending'),
      jsonb_build_object('status', 'expired'),
      jsonb_build_object('source', 'admin_invitation_reserve')
    WHERE NOT EXISTS (
      SELECT 1 FROM public.admin_membership_audit audit_row
      WHERE audit_row.invitation_id = pending_row.id AND audit_row.action = 'expire'
    );
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
    UPDATE public.admin_invitations AS invitation
    SET status = 'superseded'
    WHERE invitation.id = pending_row.id;
  END IF;

  IF member_row.user_id IS NULL AND p_auth_user_id IS NOT NULL THEN
    INSERT INTO public.admin_members (
      user_id, role, is_active, account_status, invited_at, last_invited_at,
      invited_by, status_reason
    ) VALUES (
      p_auth_user_id, p_role, false, 'invited', sent_at, sent_at,
      p_actor_user_id, 'invitation_reserved'
    )
    RETURNING * INTO member_row;
  END IF;

  INSERT INTO public.admin_invitations (
    admin_member_user_id, email, role, token_hash, status, created_by_user_id,
    expires_at, last_sent_at, send_count, resend_of_invitation_id, metadata
  ) VALUES (
    member_row.user_id, normalized_email, COALESCE(member_row.role, p_role), NULL,
    'pending', p_actor_user_id, sent_at + interval '24 hours', sent_at,
    COALESCE(pending_row.send_count, 0) + 1, previous_id,
    (jsonb_build_object(
      'source', 'admin-invite',
      'request_id', COALESCE(p_request_id, ''),
      'reserved', true,
      'delivery_state', 'reserved'
    ) || COALESCE(p_metadata, '{}'::JSONB))
      || jsonb_build_object('request_id', COALESCE(p_request_id, ''), 'delivery_state', 'reserved')
  ) RETURNING * INTO invitation_row;

  RETURN QUERY SELECT true, invitation_row.id, COALESCE(member_row.user_id, p_auth_user_id),
    COALESCE(member_row.account_status, 'none'), previous_id IS NOT NULL, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_invitation_reserve(TEXT, TEXT, UUID, UUID, BOOLEAN, TEXT, JSONB, TIMESTAMPTZ)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_invitation_reserve(TEXT, TEXT, UUID, UUID, BOOLEAN, TEXT, JSONB, TIMESTAMPTZ)
  TO service_role;

COMMENT ON FUNCTION public.admin_invitation_reserve(TEXT, TEXT, UUID, UUID, BOOLEAN, TEXT, JSONB, TIMESTAMPTZ) IS
  'Reserves one invitation per request id under the per-email lock before any Auth delivery side effect.';

ALTER TABLE public.admin_membership_audit
  DROP CONSTRAINT IF EXISTS admin_membership_audit_action_allowed;
ALTER TABLE public.admin_membership_audit
  ADD CONSTRAINT admin_membership_audit_action_allowed CHECK (action IN (
    'invite', 'resend', 'send_failed', 'delivery_unknown', 'delivery_reconciliation', 'accept', 'password_set',
    'role_change', 'activation', 'deactivation', 'revoke', 'expire'
  ));

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
  invitation_email TEXT;
  invitation_row public.admin_invitations%ROWTYPE;
  member_row public.admin_members%ROWTYPE;
  target_auth_user_id UUID;
  action_name TEXT;
BEGIN
  IF p_invitation_id IS NULL OR p_auth_user_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, 'missing_auth_user'::TEXT;
    RETURN;
  END IF;

  SELECT lower(invitation.email::TEXT)
  INTO invitation_email
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id;
  IF invitation_email IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, 'invitation_not_pending'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || invitation_email, 0));

  SELECT auth_user.id
  INTO target_auth_user_id
  FROM auth.users auth_user
  WHERE auth_user.id = p_auth_user_id
    AND lower(auth_user.email::TEXT) = invitation_email;
  IF target_auth_user_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  -- Match onboarding-status lock order: membership row before invitation row.
  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  WHERE member.user_id = target_auth_user_id
  FOR UPDATE;

  SELECT invitation.*
  INTO invitation_row
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id
  FOR UPDATE;
  IF invitation_row.id IS NULL
     OR lower(invitation_row.email::TEXT) <> invitation_email THEN
    RETURN QUERY SELECT false, NULL::UUID, 'invitation_not_pending'::TEXT;
    RETURN;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM auth.users auth_user
    WHERE auth_user.id = target_auth_user_id
      AND lower(auth_user.email::TEXT) = invitation_row.email
  ) THEN
    RETURN QUERY SELECT false, NULL::UUID, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  -- The recipient may accept the Auth email before this post-delivery RPC
  -- acquires the invitation lock. In that race, acceptance has already
  -- materialized the exact membership; finish the delivery marker idempotently
  -- instead of leaving the request permanently in reconciliation_required.
  IF invitation_row.status = 'accepted' THEN
    IF invitation_row.accepted_user_id IS DISTINCT FROM target_auth_user_id
       OR invitation_row.admin_member_user_id IS DISTINCT FROM target_auth_user_id
       OR member_row.user_id IS DISTINCT FROM target_auth_user_id
       OR member_row.last_invitation_id IS DISTINCT FROM invitation_row.id
       OR member_row.role IS DISTINCT FROM invitation_row.role
       OR member_row.account_status IS NULL
       OR member_row.account_status NOT IN ('password_pending', 'ready') THEN
      RETURN QUERY SELECT false, member_row.user_id, 'membership_state_changed'::TEXT;
      RETURN;
    END IF;

    action_name := CASE WHEN invitation_row.resend_of_invitation_id IS NULL THEN 'invite' ELSE 'resend' END;
    IF COALESCE(invitation_row.metadata ->> 'delivery_state', '') <> 'completed' THEN
      UPDATE public.admin_invitations invitation
      SET metadata = (COALESCE(invitation.metadata, '{}'::JSONB)
        - 'delivery_outcome' - 'delivery_failure_code' - 'reconciliation_required')
        || jsonb_build_object('delivery_state', 'completed', 'delivery_completed_at', clock_timestamp())
      WHERE invitation.id = invitation_row.id;
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM public.admin_membership_audit audit_row
      WHERE audit_row.invitation_id = invitation_row.id
        AND audit_row.action = action_name
    ) THEN
      INSERT INTO public.admin_membership_audit (
        actor_user_id, target_user_id, entity_type, invitation_id, action,
        old_values, new_values, metadata
      ) VALUES (
        invitation_row.created_by_user_id, target_auth_user_id, 'invitation', invitation_row.id, action_name,
        jsonb_build_object('delivery_state', 'reserved'),
        jsonb_build_object(
          'delivery_state', 'completed',
          'invitation_status', 'accepted',
          'account_status', member_row.account_status
        ),
        invitation_row.metadata || jsonb_build_object(
          'email', invitation_row.email,
          'result', 'auth_accepted_before_completion'
        )
      );
    END IF;

    RETURN QUERY SELECT true, target_auth_user_id, NULL::TEXT;
    RETURN;
  END IF;

  IF invitation_row.status <> 'pending' THEN
    RETURN QUERY SELECT false, NULL::UUID, 'invitation_not_pending'::TEXT;
    RETURN;
  END IF;

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
  ELSIF member_row.account_status <> 'invited' OR member_row.role <> invitation_row.role THEN
    RETURN QUERY SELECT false, member_row.user_id, 'membership_state_changed'::TEXT;
    RETURN;
  ELSE
    IF member_row.last_invitation_id = invitation_row.id
       AND COALESCE(invitation_row.metadata ->> 'delivery_state', '') = 'completed' THEN
      RETURN QUERY SELECT true, p_auth_user_id, NULL::TEXT;
      RETURN;
    END IF;
    UPDATE public.admin_members
    SET last_invitation_id = invitation_row.id,
        last_invited_at = now(),
        invited_by = invitation_row.created_by_user_id,
        status_reason = 'invitation_sent'
    WHERE user_id = p_auth_user_id;
  END IF;

  UPDATE public.admin_invitations
  SET admin_member_user_id = p_auth_user_id,
      metadata = (COALESCE(metadata, '{}'::JSONB)
        - 'delivery_outcome' - 'delivery_failure_code' - 'reconciliation_required')
        || jsonb_build_object('delivery_state', 'completed', 'delivery_completed_at', clock_timestamp())
  WHERE id = invitation_row.id;

  action_name := CASE WHEN invitation_row.resend_of_invitation_id IS NULL THEN 'invite' ELSE 'resend' END;
  INSERT INTO public.admin_membership_audit (
    actor_user_id, target_user_id, entity_type, invitation_id, action,
    old_values, new_values, metadata
  )
  VALUES (
    invitation_row.created_by_user_id, p_auth_user_id, 'invitation', invitation_row.id, action_name,
    jsonb_build_object('account_status', CASE WHEN invitation_row.resend_of_invitation_id IS NULL THEN 'none' ELSE 'invited' END),
    jsonb_build_object('account_status', 'invited', 'role', invitation_row.role),
    invitation_row.metadata || jsonb_build_object('email', invitation_row.email, 'result', 'auth_accepted')
  );

  RETURN QUERY SELECT true, p_auth_user_id, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_invitation_complete(UUID, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_invitation_complete(UUID, UUID)
  TO service_role;

COMMENT ON FUNCTION public.admin_invitation_complete(UUID, UUID) IS
  'Completes Auth invitation persistence under the per-email advisory lock and clears only reconciled delivery markers.';

CREATE OR REPLACE FUNCTION public.admin_invitation_mark_delivery_reconciliation(
  p_invitation_id UUID,
  p_auth_user_id UUID,
  p_delivery_outcome TEXT,
  p_failure_code TEXT
)
RETURNS TABLE (success BOOLEAN, error_code TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  invitation_email TEXT;
  initial_member_id UUID;
  invitation_row public.admin_invitations%ROWTYPE;
  auth_user_id UUID;
  member_row public.admin_members%ROWTYPE;
  target_id UUID;
  request_id TEXT;
  audit_action TEXT;
BEGIN
  IF p_invitation_id IS NULL
     OR p_delivery_outcome IS NULL
     OR p_failure_code IS NULL
     OR p_delivery_outcome NOT IN ('unknown', 'auth_accepted')
     OR (p_delivery_outcome = 'unknown' AND p_failure_code IS DISTINCT FROM 'auth_delivery_unknown')
     OR (p_delivery_outcome = 'auth_accepted' AND p_failure_code IS DISTINCT FROM 'invitation_completion_failed') THEN
    RETURN QUERY SELECT false, 'invalid_failure_code'::TEXT;
    RETURN;
  END IF;

  -- Match the reservation/failure lock order so an uncertain Auth response
  -- cannot race a resend or a definitive failure compensation.
  SELECT lower(invitation.email::TEXT), invitation.admin_member_user_id
  INTO invitation_email, initial_member_id
  FROM public.admin_invitations invitation
  WHERE invitation.id = p_invitation_id;
  IF invitation_email IS NULL THEN
    RETURN QUERY SELECT false, 'invitation_not_found'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || invitation_email, 0));

  SELECT auth_user.id
  INTO auth_user_id
  FROM auth.users auth_user
  WHERE (p_auth_user_id IS NULL OR auth_user.id = p_auth_user_id)
    AND lower(auth_user.email::TEXT) = invitation_email
  ORDER BY auth_user.created_at DESC
  LIMIT 1;
  IF p_auth_user_id IS NOT NULL AND auth_user_id IS NULL THEN
    RETURN QUERY SELECT false, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  target_id := auth_user_id;
  IF target_id IS NOT NULL THEN
    SELECT member.*
    INTO member_row
    FROM public.admin_members member
    WHERE member.user_id = target_id
    FOR UPDATE;
  END IF;

  -- Keep member-before-invitation row-lock ordering consistent with
  -- admin_get_onboarding_status, preventing a status/reconciliation deadlock.
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
  IF lower(invitation_row.email::TEXT) <> invitation_email
     OR (initial_member_id IS NOT NULL AND auth_user_id IS NULL) THEN
    RETURN QUERY SELECT false, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;
  IF invitation_row.metadata ->> 'delivery_state' = 'completed' THEN
    RETURN QUERY SELECT true, NULL::TEXT;
    RETURN;
  END IF;
  IF target_id IS NOT NULL THEN
    IF member_row.user_id IS NULL THEN
      INSERT INTO public.admin_members (
        user_id, role, is_active, account_status, invited_at, last_invited_at,
        invited_by, last_invitation_id, status_reason
      )
      VALUES (
        target_id, invitation_row.role, false, 'invited', now(), now(),
        invitation_row.created_by_user_id, invitation_row.id, 'invitation_delivery_reconciliation'
      )
      RETURNING * INTO member_row;
    ELSIF member_row.account_status <> 'invited' OR member_row.role <> invitation_row.role THEN
      RETURN QUERY SELECT false, 'membership_state_changed'::TEXT;
      RETURN;
    ELSE
      UPDATE public.admin_members
      SET last_invitation_id = invitation_row.id,
          last_invited_at = now(),
          invited_by = invitation_row.created_by_user_id,
          status_reason = 'invitation_delivery_reconciliation'
      WHERE user_id = target_id;
    END IF;
  END IF;

  request_id := invitation_row.metadata ->> 'request_id';

  audit_action := CASE WHEN p_delivery_outcome = 'unknown' THEN 'delivery_unknown' ELSE 'delivery_reconciliation' END;
  UPDATE public.admin_invitations invitation
  SET admin_member_user_id = COALESCE(target_id, invitation.admin_member_user_id),
      metadata = COALESCE(invitation.metadata, '{}'::JSONB) || jsonb_build_object(
    'delivery_outcome', p_delivery_outcome,
    'delivery_failure_code', p_failure_code,
    'delivery_state', 'reconciliation_required',
    'reconciliation_required', true
  )
  WHERE invitation.id = invitation_row.id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.admin_membership_audit audit_row
    WHERE audit_row.invitation_id = invitation_row.id
      AND audit_row.action = audit_action
      AND audit_row.metadata ->> 'request_id' IS NOT DISTINCT FROM request_id
  ) THEN
    INSERT INTO public.admin_membership_audit (
      actor_user_id, target_user_id, entity_type, invitation_id, action,
      old_values, new_values, metadata
    )
    VALUES (
      invitation_row.created_by_user_id, target_id, 'invitation', invitation_row.id, audit_action,
      jsonb_build_object('status', 'pending'),
      jsonb_build_object('status', 'pending', 'delivery_outcome', p_delivery_outcome, 'failure_code', p_failure_code),
      COALESCE(invitation_row.metadata, '{}'::JSONB) || jsonb_build_object(
        'delivery_outcome', p_delivery_outcome,
        'delivery_failure_code', p_failure_code,
        'reconciliation_required', true
      )
    );
  END IF;

  RETURN QUERY SELECT true, NULL::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_invitation_mark_delivery_reconciliation(UUID, UUID, TEXT, TEXT)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_invitation_mark_delivery_reconciliation(UUID, UUID, TEXT, TEXT)
  TO service_role;

COMMENT ON FUNCTION public.admin_invitation_mark_delivery_reconciliation(UUID, UUID, TEXT, TEXT) IS
  'Records ambiguous delivery or incomplete post-delivery persistence under the per-email lock and repairs matching Auth membership when possible.';

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

  -- Serialize acceptance with reservation, resend, completion, and delivery
  -- reconciliation before any membership or invitation row is locked.
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || normalized_email, 0));
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
    -- Auth may have created the identity and sent the link immediately before
    -- an edge timeout. A verified session with the exact invite email may
    -- materialize the invited membership from that still-pending reservation.
    INSERT INTO public.admin_members (
      user_id, role, is_active, account_status, invited_at, last_invited_at,
      invited_by, last_invitation_id, status_reason
    )
    VALUES (
      actor_id, invitation_row.role, false, 'invited', accepted_at_ts, accepted_at_ts,
      invitation_row.created_by_user_id, invitation_row.id, 'invitation_delivery_reconciliation'
    )
    RETURNING * INTO member_row;
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
      accepted_at = accepted_at_ts,
      metadata = COALESCE(invitation.metadata, '{}'::JSONB)
        - 'delivery_outcome' - 'delivery_failure_code' - 'reconciliation_required'
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
  'Accepts a pending Auth invitation under the shared email lock and materializes a missing invited membership only for the matching authenticated email.';
