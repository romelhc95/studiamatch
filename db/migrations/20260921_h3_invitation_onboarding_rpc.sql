-- H3-BUILD-03B-DB-IMPLEMENTATION.
-- Auth owns the invitation token. Postgres owns the business lifecycle.
-- Expand-only delta: do not edit the historical 20260918/20260919/20260920 files.
-- No password, token, secret, or frontend-supplied expiry is accepted here.

-- ---------------------------------------------------------------------------
-- 1) Runtime TTL: every new emission starts a server-side 24-hour window.
--    `sent_at` is captured by the database when the service-role persistence
--    RPC is called. The persisted compatibility column is last_sent_at.
-- ---------------------------------------------------------------------------
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
      AND lower(auth_user.email::TEXT) = normalized_email
  ) THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, 'none'::TEXT, false, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || normalized_email, 0));

  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  JOIN auth.users auth_user ON auth_user.id = member.user_id
  WHERE lower(auth_user.email::TEXT) = normalized_email
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
      SELECT 1
      FROM public.admin_membership_audit audit_row
      WHERE audit_row.invitation_id = pending_row.id
        AND audit_row.action = 'expire'
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
    )
    VALUES (
      p_auth_user_id, p_role, false, 'invited', sent_at, sent_at,
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
    sent_at + interval '24 hours',
    sent_at,
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
  sent_at TIMESTAMPTZ := clock_timestamp();
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
    WHERE lower(auth_user.email::TEXT) = normalized_email;
  END IF;

  INSERT INTO public.admin_invitations (
    admin_member_user_id, email, role, token_hash, status, created_by_user_id,
    expires_at, last_sent_at, send_count, failure_code, metadata
  )
  VALUES (
    CASE WHEN p_auth_user_id IS NULL THEN NULL ELSE target_id END,
    normalized_email, p_role, NULL, 'send_failed', p_actor_user_id,
    sent_at + interval '24 hours', sent_at, 1, p_failure_code,
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

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.admin_invitations'::regclass
      AND conname = 'admin_invitations_expiry_after_send'
  ) THEN
    ALTER TABLE public.admin_invitations
      ADD CONSTRAINT admin_invitations_expiry_after_send
      CHECK (expires_at > last_sent_at);
  END IF;
END;
$$;

COMMENT ON COLUMN public.admin_invitations.last_sent_at IS
  'Server-side send timestamp used as the origin of the 24-hour invitation TTL.';

-- ---------------------------------------------------------------------------
-- 2) Membership transition guard: password_pending is never active.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.guard_admin_members_status_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
  IF NEW.account_status = OLD.account_status THEN
    IF NEW.account_status = 'password_pending' THEN
      NEW.is_active := false;
    END IF;
    RETURN NEW;
  END IF;
  IF (OLD.account_status, NEW.account_status) NOT IN (
    ('invited', 'accepted'),
    ('accepted', 'password_pending'),
    ('password_pending', 'ready'),
    ('invited', 'expired'),
    ('invited', 'revoked'),
    ('accepted', 'revoked'),
    ('password_pending', 'revoked'),
    ('ready', 'inactive'),
    ('ready', 'revoked'),
    ('inactive', 'invited')
  ) THEN
    RAISE EXCEPTION 'admin_members invalid status transition % -> %', OLD.account_status, NEW.account_status;
  END IF;
  IF NEW.account_status = 'accepted' THEN
    NEW.accepted_at := COALESCE(NEW.accepted_at, now());
    NEW.is_active := false;
    IF NEW.last_invitation_id IS NULL THEN
      RAISE EXCEPTION 'admin_members transition to accepted requires last_invitation_id';
    END IF;
  END IF;
  IF NEW.account_status = 'password_pending' THEN
    NEW.accepted_at := COALESCE(NEW.accepted_at, now());
    NEW.is_active := false;
  END IF;
  IF NEW.account_status = 'ready' THEN
    IF NEW.accepted_at IS NULL OR NEW.password_set_at IS NULL THEN
      RAISE EXCEPTION 'admin_members transition to ready requires accepted_at and password_set_at';
    END IF;
    NEW.activated_at := COALESCE(NEW.activated_at, now());
    NEW.revoked_at := NULL;
    NEW.deactivated_at := NULL;
  END IF;
  IF NEW.account_status = 'invited' THEN
    NEW.invited_at := COALESCE(NEW.invited_at, now());
    NEW.last_invited_at := COALESCE(NEW.last_invited_at, now());
    NEW.accepted_at := NULL;
    NEW.password_set_at := NULL;
    NEW.revoked_at := NULL;
    NEW.deactivated_at := NULL;
    NEW.is_active := false;
  END IF;
  IF NEW.account_status = 'inactive' THEN
    NEW.deactivated_at := COALESCE(NEW.deactivated_at, now());
    NEW.is_active := false;
  END IF;
  IF NEW.account_status = 'revoked' THEN
    NEW.revoked_at := COALESCE(NEW.revoked_at, now());
    NEW.is_active := false;
  END IF;
  RETURN NEW;
END;
$$;

-- ---------------------------------------------------------------------------
-- 3) Authenticated onboarding acceptance.
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- 4) Authenticated password setup completion. Auth updates the password first;
--    this RPC only records the successful post-Auth step and never receives it.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.admin_complete_password_setup()
RETURNS TABLE (
  success BOOLEAN,
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
  member_row public.admin_members%ROWTYPE;
  invitation_row public.admin_invitations%ROWTYPE;
  password_set_at_ts TIMESTAMPTZ;
BEGIN
  IF actor_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::TEXT, NULL::TEXT, 'missing_auth_user'::TEXT;
    RETURN;
  END IF;

  password_set_at_ts := clock_timestamp();

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_onboarding_user:' || actor_id::TEXT, 0));

  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  WHERE member.user_id = actor_id
  FOR UPDATE;
  IF member_row.user_id IS NULL THEN
    RETURN QUERY SELECT false, actor_id, NULL::TEXT, NULL::TEXT, 'membership_not_found'::TEXT;
    RETURN;
  END IF;

  IF member_row.account_status = 'ready' AND member_row.password_set_at IS NOT NULL THEN
    RETURN QUERY SELECT true, actor_id, member_row.account_status, member_row.role, NULL::TEXT;
    RETURN;
  END IF;
  IF member_row.account_status <> 'password_pending' THEN
    RETURN QUERY SELECT false, actor_id, member_row.account_status, member_row.role,
      CASE WHEN member_row.account_status = 'ready' THEN 'legacy_ready' ELSE 'password_setup_not_pending' END;
    RETURN;
  END IF;
  IF member_row.last_invitation_id IS NULL THEN
    RETURN QUERY SELECT false, actor_id, member_row.account_status, member_row.role, 'reconciliation_required'::TEXT;
    RETURN;
  END IF;

  SELECT invitation.*
  INTO invitation_row
  FROM public.admin_invitations invitation
  WHERE invitation.id = member_row.last_invitation_id
  FOR UPDATE;
  IF invitation_row.id IS NULL THEN
    RETURN QUERY SELECT false, actor_id, member_row.account_status, member_row.role, 'reconciliation_required'::TEXT;
    RETURN;
  END IF;
  IF invitation_row.status <> 'accepted' THEN
    RETURN QUERY SELECT false, actor_id, member_row.account_status, member_row.role, 'invitation_not_accepted'::TEXT;
    RETURN;
  END IF;
  IF invitation_row.accepted_user_id IS DISTINCT FROM actor_id THEN
    RETURN QUERY SELECT false, actor_id, member_row.account_status, member_row.role, 'auth_identity_mismatch'::TEXT;
    RETURN;
  END IF;
  IF invitation_row.admin_member_user_id IS DISTINCT FROM actor_id OR invitation_row.role <> member_row.role THEN
    RETURN QUERY SELECT false, actor_id, member_row.account_status, member_row.role, 'reconciliation_required'::TEXT;
    RETURN;
  END IF;

  UPDATE public.admin_members AS member
  SET account_status = 'ready',
      is_active = true,
      password_set_at = COALESCE(member.password_set_at, password_set_at_ts),
      status_reason = 'password_setup_complete'
  WHERE member.user_id = actor_id;

  IF NOT EXISTS (
    SELECT 1 FROM public.admin_membership_audit audit_row
    WHERE audit_row.invitation_id = invitation_row.id AND audit_row.action = 'password_set'
  ) THEN
    INSERT INTO public.admin_membership_audit (
      actor_user_id, target_user_id, entity_type, invitation_id, action,
      old_values, new_values, metadata
    ) VALUES (
      actor_id, actor_id, 'invitation', invitation_row.id, 'password_set',
      jsonb_build_object('account_status', 'password_pending'),
      jsonb_build_object('account_status', 'ready', 'is_active', true),
      jsonb_build_object('source', 'admin_complete_password_setup')
    );
  END IF;

  RETURN QUERY SELECT true, actor_id, 'ready'::TEXT, member_row.role, NULL::TEXT;
END;
$$;

-- ---------------------------------------------------------------------------
-- 5) Authenticated onboarding status. Pending invitations expire lazily here.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.admin_get_onboarding_status()
RETURNS TABLE (
  success BOOLEAN,
  user_id UUID,
  email TEXT,
  role TEXT,
  account_status TEXT,
  invitation_status TEXT,
  invitation_id UUID,
  expires_at TIMESTAMPTZ,
  error_code TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  actor_id UUID := (SELECT auth.uid());
  normalized_email TEXT;
  member_row public.admin_members%ROWTYPE;
  invitation_row public.admin_invitations%ROWTYPE;
BEGIN
  IF actor_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::UUID, NULL::TIMESTAMPTZ, 'missing_auth_user'::TEXT;
    RETURN;
  END IF;

  SELECT lower(btrim(auth_user.email::TEXT))
  INTO normalized_email
  FROM auth.users auth_user
  WHERE auth_user.id = actor_id;
  IF normalized_email IS NULL THEN
    RETURN QUERY SELECT false, actor_id, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::UUID, NULL::TIMESTAMPTZ, 'missing_auth_user'::TEXT;
    RETURN;
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_onboarding_email:' || normalized_email, 0));
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_onboarding_user:' || actor_id::TEXT, 0));

  SELECT member.*
  INTO member_row
  FROM public.admin_members member
  WHERE member.user_id = actor_id
  FOR UPDATE;
  IF member_row.user_id IS NULL THEN
    RETURN QUERY SELECT false, actor_id, normalized_email, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::UUID, NULL::TIMESTAMPTZ, 'membership_not_found'::TEXT;
    RETURN;
  END IF;

  -- Legacy ready members have no invitation history. Do not infer one by
  -- email because that could expose another lifecycle row to the caller.
  IF member_row.account_status = 'ready' AND member_row.last_invitation_id IS NULL THEN
    RETURN QUERY SELECT true, actor_id, normalized_email, member_row.role, member_row.account_status,
      NULL::TEXT, NULL::UUID, NULL::TIMESTAMPTZ, NULL::TEXT;
    RETURN;
  END IF;

  IF member_row.last_invitation_id IS NOT NULL THEN
    SELECT invitation.*
    INTO invitation_row
    FROM public.admin_invitations invitation
    WHERE invitation.id = member_row.last_invitation_id
    FOR UPDATE;
  END IF;
  IF invitation_row.id IS NULL THEN
    SELECT invitation.*
    INTO invitation_row
    FROM public.admin_invitations invitation
    WHERE invitation.email = normalized_email
    ORDER BY invitation.created_at DESC
    LIMIT 1
    FOR UPDATE;
  END IF;

  IF invitation_row.id IS NOT NULL AND invitation_row.status = 'pending'
     AND invitation_row.expires_at <= now() THEN
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
        actor_id, actor_id, 'invitation', invitation_row.id, 'expire',
        jsonb_build_object('status', 'pending'),
        jsonb_build_object('status', 'expired'),
        jsonb_build_object('source', 'admin_get_onboarding_status')
      );
    END IF;
    invitation_row.status := 'expired';
  END IF;

  RETURN QUERY SELECT true,
    actor_id,
    normalized_email,
    member_row.role,
    member_row.account_status,
    invitation_row.status,
    invitation_row.id,
    invitation_row.expires_at,
    NULL::TEXT;
END;
$$;

-- ---------------------------------------------------------------------------
-- 6) Explicit ACL: no anonymous/public execution; only authenticated callers
--    and the protected service-role path may invoke the onboarding contract.
-- ---------------------------------------------------------------------------
REVOKE ALL ON FUNCTION public.admin_accept_current_invitation(UUID) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.admin_complete_password_setup() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.admin_get_onboarding_status() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_accept_current_invitation(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_complete_password_setup() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_get_onboarding_status() TO authenticated, service_role;

REVOKE ALL ON FUNCTION public.admin_invitation_reserve(TEXT, TEXT, UUID, UUID, BOOLEAN, TEXT, JSONB, TIMESTAMPTZ) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.admin_invitation_record_failure(TEXT, TEXT, UUID, UUID, TEXT, TEXT, JSONB) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_invitation_reserve(TEXT, TEXT, UUID, UUID, BOOLEAN, TEXT, JSONB, TIMESTAMPTZ) TO service_role;
GRANT EXECUTE ON FUNCTION public.admin_invitation_record_failure(TEXT, TEXT, UUID, UUID, TEXT, TEXT, JSONB) TO service_role;

COMMENT ON FUNCTION public.admin_accept_current_invitation(UUID) IS
  'H3 onboarding: accepts the authenticated user invitation and moves the membership to inactive password_pending without exposing token material.';
COMMENT ON FUNCTION public.admin_complete_password_setup() IS
  'H3 onboarding: records a successful Auth password update and activates only the accepted membership; receives no password.';
COMMENT ON FUNCTION public.admin_get_onboarding_status() IS
  'H3 onboarding: returns only the authenticated user onboarding state and performs lazy invitation expiration.';
