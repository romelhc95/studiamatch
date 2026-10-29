-- H3 Invitation Flow Opcion A delta.
-- Scope: expand-only local SQL migration. Supabase Auth owns the invitation
-- token; StudIAMatch retains the business record, lifecycle and audit trail.
-- This migration intentionally does not modify 20260918_h3_invitation_flow_persistence.sql.
-- Idempotent: safe to re-run after the persistence migration.

-- ---------------------------------------------------------------------------
-- 1) admin_invitations: make the legacy token column optional
-- ---------------------------------------------------------------------------
ALTER TABLE public.admin_invitations
  ALTER COLUMN token_hash DROP NOT NULL;

-- The application no longer owns or derives an invitation token. Existing
-- hashes remain readable and immutable for legacy rows, but no new hash is
-- required by the Auth-owned flow.
ALTER TABLE public.admin_invitations
  DROP CONSTRAINT IF EXISTS admin_invitations_token_hash_min_length;

DROP INDEX IF EXISTS public.uq_admin_invitations_token_hash;

COMMENT ON COLUMN public.admin_invitations.token_hash IS
  'Legacy compatibility column. Nullable because Supabase Auth owns invitation tokens under H3 Opcion A; new runtime code must not populate or derive this value.';

-- ---------------------------------------------------------------------------
-- 2) invitation lifecycle: record an unconfirmed send/persistence outcome
-- ---------------------------------------------------------------------------
ALTER TABLE public.admin_invitations
  DROP CONSTRAINT IF EXISTS admin_invitations_status_allowed;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.admin_invitations'::regclass
      AND conname = 'admin_invitations_status_allowed'
  ) THEN
    ALTER TABLE public.admin_invitations
      ADD CONSTRAINT admin_invitations_status_allowed CHECK (
        status IN ('pending', 'accepted', 'expired', 'revoked', 'superseded', 'send_failed')
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.admin_invitations'::regclass
      AND conname = 'admin_invitations_send_failed_state'
  ) THEN
    ALTER TABLE public.admin_invitations
      ADD CONSTRAINT admin_invitations_send_failed_state CHECK (
        status <> 'send_failed'
        OR (
          failure_code IS NOT NULL
          AND length(btrim(failure_code)) > 0
          AND accepted_at IS NULL
          AND accepted_user_id IS NULL
          AND revoked_at IS NULL
          AND revoked_by_user_id IS NULL
        )
      );
  END IF;
END;
$$;

-- Keep the original pending-only unique index: send_failed rows do not block a
-- later retry, while concurrent pending invitations remain forbidden.

CREATE OR REPLACE FUNCTION public.guard_admin_invitations_status_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
  IF NEW.status = OLD.status THEN
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

-- ---------------------------------------------------------------------------
-- 3) audit vocabulary: record Auth/DB send failures without secrets
-- ---------------------------------------------------------------------------
ALTER TABLE public.admin_membership_audit
  DROP CONSTRAINT IF EXISTS admin_membership_audit_action_allowed;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.admin_membership_audit'::regclass
      AND conname = 'admin_membership_audit_action_allowed'
  ) THEN
    ALTER TABLE public.admin_membership_audit
      ADD CONSTRAINT admin_membership_audit_action_allowed CHECK (action IN (
        'invite', 'resend', 'send_failed', 'accept', 'password_set',
        'role_change', 'activation', 'deactivation', 'revoke', 'expire'
      ));
  END IF;
END;
$$;
