-- H3 first-admin bootstrap for an Auth invitation created outside the app.
-- The only eligible identity is romelhc95@gmail.com, after Supabase Auth has
-- recorded and confirmed its invitation. The existing callback still calls
-- admin_accept_current_invitation(); the normal acceptance/password lifecycle
-- remains authoritative and this migration never marks a member ready/active.
-- Expand-only and idempotent. No Auth invitation is sent by this SQL.
-- StudIAMatch-Docs: .context/componentes/database_migrations.md#first-admin-auth-bootstrap

-- ---------------------------------------------------------------------------
-- 1) Represent the external Auth invitation without inventing an app sender
-- ---------------------------------------------------------------------------
ALTER TABLE public.admin_invitations
  ALTER COLUMN created_by_user_id DROP NOT NULL;

-- The existing Auth token delta already permits NULL token_hash for ordinary
-- reserve-before-delivery rows. Do not tighten that established contract here.

ALTER TABLE public.admin_invitations
  DROP CONSTRAINT IF EXISTS admin_invitations_first_admin_auth_origin;

ALTER TABLE public.admin_invitations
  ADD CONSTRAINT admin_invitations_first_admin_auth_origin CHECK (
    CASE
      WHEN metadata ->> 'source' = 'first_admin_auth_bootstrap' THEN
        COALESCE(
          email = 'romelhc95@gmail.com'
          AND role = 'admin'
          AND created_by_user_id IS NULL
          AND token_hash IS NULL
          AND send_count = 1
          AND metadata ->> 'auth_invitation_origin' = 'supabase_auth'
          AND metadata ->> 'app_email_sent' = 'false'
          AND (metadata ->> 'auth_invited_at') IS NOT NULL
          AND last_sent_at IS NOT DISTINCT FROM
              (metadata ->> 'auth_invited_at')::TIMESTAMPTZ
          AND (metadata ->> 'auth_email_confirmed_at') IS NOT NULL
          AND (metadata ->> 'auth_email_confirmed_at')::TIMESTAMPTZ >=
              (metadata ->> 'auth_invited_at')::TIMESTAMPTZ,
          false
        )
      ELSE
        created_by_user_id IS NOT NULL
        AND last_sent_at IS NOT NULL
        AND send_count >= 1
    END
  );

COMMENT ON COLUMN public.admin_invitations.created_by_user_id IS
  'App invitation creator. NULL is permitted only for an explicitly sourced Supabase Auth first-admin bootstrap; it never fabricates a prior Admin actor.';

COMMENT ON COLUMN public.admin_invitations.token_hash IS
  'Application invitation token hash. The existing Auth reservation contract permits NULL for ordinary reserved rows; first-admin bootstrap also stores NULL because Supabase Auth owns and validates its invitation link.';

-- ---------------------------------------------------------------------------
-- 2) Preserve the existing acceptance implementation as the lifecycle core
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF to_regprocedure('public.admin_accept_current_invitation_lifecycle(uuid)') IS NULL THEN
    IF to_regprocedure('public.admin_accept_current_invitation(uuid)') IS NULL THEN
      RAISE EXCEPTION 'H3 acceptance lifecycle function is missing';
    END IF;
    ALTER FUNCTION public.admin_accept_current_invitation(UUID)
      RENAME TO admin_accept_current_invitation_lifecycle;
  END IF;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_accept_current_invitation_lifecycle(UUID)
  FROM PUBLIC, anon, authenticated, service_role;

ALTER TABLE public.admin_membership_audit
  DROP CONSTRAINT IF EXISTS admin_membership_audit_action_allowed;
ALTER TABLE public.admin_membership_audit
  ADD CONSTRAINT admin_membership_audit_action_allowed CHECK (action IN (
    'invite', 'resend', 'send_failed', 'delivery_unknown', 'delivery_reconciliation',
    'accept', 'password_set', 'role_change', 'activation', 'deactivation',
    'revoke', 'expire', 'first_admin_bootstrap'
  ));

-- Internal one-time materializer. It accepts no caller-supplied email or actor;
-- auth.uid() and the Auth invitation timestamps are the identity evidence.
CREATE OR REPLACE FUNCTION private.h3_first_admin_auth_bootstrap_invitation()
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, auth, pg_temp
AS $$
DECLARE
  actor_id UUID := (SELECT auth.uid());
  normalized_email TEXT;
  auth_invited_at TIMESTAMPTZ;
  auth_confirmed_at TIMESTAMPTZ;
  invitation_id UUID;
BEGIN
  IF actor_id IS NULL THEN
    RETURN NULL;
  END IF;

  SELECT lower(btrim(auth_user.email::TEXT)), auth_user.invited_at, auth_user.email_confirmed_at
  INTO normalized_email, auth_invited_at, auth_confirmed_at
  FROM auth.users AS auth_user
  WHERE auth_user.id = actor_id;

  IF normalized_email IS DISTINCT FROM 'romelhc95@gmail.com'
     OR auth_invited_at IS NULL
     OR auth_confirmed_at IS NULL
     OR auth_confirmed_at < auth_invited_at THEN
    RETURN NULL;
  END IF;

  -- Match the invitation lifecycle lock order so acceptance and bootstrap are
  -- serialized with the existing per-email and per-user operations.
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_invite:' || normalized_email, 0));
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_onboarding_email:' || normalized_email, 0));
  PERFORM pg_advisory_xact_lock(hashtextextended('h3_admin_onboarding_user:' || actor_id::TEXT, 0));

  IF EXISTS (
       SELECT 1 FROM public.admin_members AS member
       WHERE member.role = 'admin'
     )
     OR EXISTS (
       SELECT 1 FROM public.admin_members AS member
       WHERE member.user_id = actor_id
     )
     OR EXISTS (
       SELECT 1 FROM public.admin_invitations AS invitation
       WHERE invitation.email = normalized_email
     )
     OR EXISTS (
       SELECT 1 FROM public.admin_invitations AS invitation
       WHERE invitation.role = 'admin'
         AND invitation.status = 'pending'
     )
     OR EXISTS (
       SELECT 1 FROM public.admin_membership_audit AS audit_row
       WHERE audit_row.action = 'first_admin_bootstrap'
     ) THEN
    RETURN NULL;
  END IF;

  INSERT INTO public.admin_members (
    user_id, role, is_active, account_status, invited_at, last_invited_at,
    invited_by, status_reason
  ) VALUES (
    actor_id, 'admin', false, 'invited', auth_invited_at, auth_invited_at,
    NULL, 'first_admin_supabase_auth_invitation'
  );

  INSERT INTO public.admin_invitations (
    admin_member_user_id, email, role, token_hash, status, created_by_user_id,
    expires_at, last_sent_at, send_count, metadata
  ) VALUES (
    actor_id,
    normalized_email,
    'admin',
    NULL,
    'pending',
    NULL,
    clock_timestamp() + INTERVAL '24 hours',
    auth_invited_at,
    1,
    jsonb_build_object(
      'source', 'first_admin_auth_bootstrap',
      'auth_invitation_origin', 'supabase_auth',
      'auth_invited_at', auth_invited_at,
      'auth_email_confirmed_at', auth_confirmed_at,
      'app_email_sent', false,
      'created_by_user_id', NULL
    )
  )
  RETURNING id INTO invitation_id;

  UPDATE public.admin_members AS member
  SET last_invitation_id = invitation_id
  WHERE member.user_id = actor_id;

  INSERT INTO public.admin_membership_audit (
    actor_user_id, target_user_id, entity_type, invitation_id, action,
    old_values, new_values, metadata
  ) VALUES (
    actor_id,
    actor_id,
    'invitation',
    invitation_id,
    'first_admin_bootstrap',
    jsonb_build_object(
      'membership', 'absent',
      'app_invitation', 'absent',
      'supabase_auth_invitation', 'created_and_email_confirmed'
    ),
    jsonb_build_object(
      'role', 'admin',
      'account_status', 'invited',
      'is_active', false,
      'invitation_status', 'pending',
      'app_email_sent', false,
      'created_by_user_id', NULL
    ),
    jsonb_build_object(
      'source', 'first_admin_auth_bootstrap',
      'auth_invited_at', auth_invited_at,
      'auth_email_confirmed_at', auth_confirmed_at
    )
  );

  RETURN invitation_id;
END;
$$;

REVOKE ALL ON FUNCTION private.h3_first_admin_auth_bootstrap_invitation()
  FROM PUBLIC, anon, authenticated, service_role;

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
  lifecycle_result RECORD;
  bootstrap_invitation_id UUID;
BEGIN
  -- The existing callback sends no invitation id. Only that path may attempt
  -- to materialize the exact confirmed Auth invitation; both callback forms
  -- then enter the quota-wrapped lifecycle through this single call site.
  BEGIN
    IF p_invitation_id IS NULL THEN
      bootstrap_invitation_id := private.h3_first_admin_auth_bootstrap_invitation();
    END IF;

    SELECT * INTO lifecycle_result
    FROM public.admin_accept_current_invitation_lifecycle(
      COALESCE(bootstrap_invitation_id, p_invitation_id)
    );

    IF bootstrap_invitation_id IS NOT NULL
       AND lifecycle_result.success IS DISTINCT FROM TRUE THEN
      RAISE EXCEPTION USING
        ERRCODE = 'PZ001',
        MESSAGE = 'First-admin bootstrap did not complete the existing invitation lifecycle';
    END IF;
  EXCEPTION WHEN SQLSTATE 'PZ001' THEN
    -- Roll back the bootstrap subtransaction and retain the ordinary safe
    -- response when the established lifecycle rejects the new row.
    RETURN QUERY SELECT false, NULL::UUID, NULL::UUID, NULL::TEXT, NULL::TEXT,
      'invitation_not_pending'::TEXT;
    RETURN;
  END;

  RETURN QUERY SELECT lifecycle_result.success, lifecycle_result.invitation_id,
    lifecycle_result.member_id, lifecycle_result.account_status,
    lifecycle_result.role, lifecycle_result.error_code;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_accept_current_invitation(UUID)
  FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_accept_current_invitation(UUID)
  TO authenticated, service_role;

COMMENT ON FUNCTION private.h3_first_admin_auth_bootstrap_invitation() IS
  'Materializes exactly one external, confirmed Supabase Auth invitation for romelhc95@gmail.com when no Admin membership or prior bootstrap audit exists; creates an inactive invited membership and factual audit only.';
COMMENT ON FUNCTION public.admin_accept_current_invitation(UUID) IS
  'Preserves the existing invitation acceptance/password lifecycle and permits a one-time, exact-identity bootstrap only after Supabase Auth records and confirms the invited first Admin.';

NOTIFY pgrst, 'reload schema';
