-- H3 Invitation Flow persistence layer (design: STUDIAMATCH-H3-INVITATION-DESIGN-01 / H3-DESIGN-DB-01)
-- Scope: local SQL migration only. No frontend, no Edge Functions, no MFA removal, no remote apply.
-- Compatibility contract:
--   * `is_active`, `role`, existing RPCs, seed and audit keep working unchanged (expand phase).
--   * Existing rows are backfilled to account_status = 'ready' by the column default.
--   * The invitation lifecycle (accept/password/ready transitions) will be driven by future RPCs
--     and Edge Functions; this migration only provides the persistence and guard rails.
-- Idempotent: safe to re-run (IF NOT EXISTS / guarded DO blocks / CREATE OR REPLACE).

-- ---------------------------------------------------------------------------
-- 1) admin_invitations: invitation lifecycle, separate from membership
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.admin_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_member_user_id UUID REFERENCES public.admin_members(user_id) ON DELETE SET NULL,
  email TEXT NOT NULL,
  role TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_by_user_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  accepted_at TIMESTAMPTZ,
  accepted_user_id UUID REFERENCES auth.users(id),
  revoked_at TIMESTAMPTZ,
  revoked_by_user_id UUID REFERENCES auth.users(id),
  last_sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  send_count INTEGER NOT NULL DEFAULT 1,
  resend_of_invitation_id UUID REFERENCES public.admin_invitations(id),
  accepted_ip_hash TEXT,
  accepted_user_agent_hash TEXT,
  failure_code TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT admin_invitations_role_allowed CHECK (role IN ('admin', 'user')),
  CONSTRAINT admin_invitations_status_allowed CHECK (status IN ('pending', 'accepted', 'expired', 'revoked', 'superseded')),
  CONSTRAINT admin_invitations_email_valid CHECK (email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'),
  CONSTRAINT admin_invitations_email_normalized CHECK (email = lower(trim(email))),
  CONSTRAINT admin_invitations_token_hash_min_length CHECK (length(token_hash) >= 32),
  CONSTRAINT admin_invitations_expiry_after_creation CHECK (expires_at > created_at),
  CONSTRAINT admin_invitations_send_count_positive CHECK (send_count >= 1),
  CONSTRAINT admin_invitations_pending_state CHECK (
    status <> 'pending'
    OR (accepted_at IS NULL AND accepted_user_id IS NULL AND revoked_at IS NULL AND revoked_by_user_id IS NULL)
  ),
  CONSTRAINT admin_invitations_accepted_state CHECK (
    status <> 'accepted' OR (accepted_at IS NOT NULL AND accepted_user_id IS NOT NULL AND revoked_at IS NULL)
  ),
  CONSTRAINT admin_invitations_revoked_state CHECK (
    status <> 'revoked' OR (revoked_at IS NOT NULL AND revoked_by_user_id IS NOT NULL)
  ),
  CONSTRAINT admin_invitations_superseded_state CHECK (
    status <> 'superseded' OR (accepted_at IS NULL AND revoked_at IS NOT NULL)
  )
);

COMMENT ON TABLE public.admin_invitations IS
  'H3 Invitation Flow: one row per invitation emission. Token stored only as hash. Single pending invitation per email enforced by partial unique index.';

CREATE UNIQUE INDEX IF NOT EXISTS uq_admin_invitations_token_hash
  ON public.admin_invitations (token_hash);
-- Only one live invitation per email: a resend must supersede/revoke the previous one first.
CREATE UNIQUE INDEX IF NOT EXISTS uq_admin_invitations_one_pending_per_email
  ON public.admin_invitations (email) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_admin_invitations_email_created
  ON public.admin_invitations (email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_invitations_status
  ON public.admin_invitations (status);
CREATE INDEX IF NOT EXISTS idx_admin_invitations_member
  ON public.admin_invitations (admin_member_user_id) WHERE admin_member_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_admin_invitations_pending_expiry
  ON public.admin_invitations (expires_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_admin_invitations_resend_chain
  ON public.admin_invitations (resend_of_invitation_id) WHERE resend_of_invitation_id IS NOT NULL;

ALTER TABLE public.admin_invitations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.admin_invitations FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON TABLE public.admin_invitations TO service_role;

-- Security guards: invitations are append-only lifecycle rows.
CREATE OR REPLACE FUNCTION public.prevent_admin_invitations_delete()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
  RAISE EXCEPTION 'admin_invitations is append-only: rows are superseded or revoked, never deleted';
END;
$$;

CREATE OR REPLACE FUNCTION public.guard_admin_invitations_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
  IF NEW.token_hash IS DISTINCT FROM OLD.token_hash THEN
    RAISE EXCEPTION 'admin_invitations.token_hash is immutable';
  END IF;
  IF NEW.email IS DISTINCT FROM OLD.email THEN
    RAISE EXCEPTION 'admin_invitations.email is immutable';
  END IF;
  IF NEW.created_by_user_id IS DISTINCT FROM OLD.created_by_user_id THEN
    RAISE EXCEPTION 'admin_invitations.created_by_user_id is immutable';
  END IF;
  IF NEW.created_at IS DISTINCT FROM OLD.created_at THEN
    RAISE EXCEPTION 'admin_invitations.created_at is immutable';
  END IF;
  RETURN NEW;
END;
$$;

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
  IF NEW.status NOT IN ('accepted', 'expired', 'revoked', 'superseded') THEN
    RAISE EXCEPTION 'admin_invitations invalid status transition % -> %', OLD.status, NEW.status;
  END IF;
  IF NEW.status = 'accepted' THEN
    NEW.accepted_at := COALESCE(NEW.accepted_at, now());
  END IF;
  IF NEW.status IN ('revoked', 'superseded') THEN
    NEW.revoked_at := COALESCE(NEW.revoked_at, now());
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS prevent_admin_invitations_delete ON public.admin_invitations;
CREATE TRIGGER prevent_admin_invitations_delete
  BEFORE DELETE ON public.admin_invitations
  FOR EACH ROW EXECUTE FUNCTION public.prevent_admin_invitations_delete();

DROP TRIGGER IF EXISTS guard_admin_invitations_identity ON public.admin_invitations;
CREATE TRIGGER guard_admin_invitations_identity
  BEFORE UPDATE ON public.admin_invitations
  FOR EACH ROW EXECUTE FUNCTION public.guard_admin_invitations_identity();

DROP TRIGGER IF EXISTS guard_admin_invitations_status ON public.admin_invitations;
CREATE TRIGGER guard_admin_invitations_status
  BEFORE UPDATE ON public.admin_invitations
  FOR EACH ROW EXECUTE FUNCTION public.guard_admin_invitations_status_transition();

-- ---------------------------------------------------------------------------
-- 2) admin_members: onboarding state expansion (expand phase, backward compatible)
-- ---------------------------------------------------------------------------
ALTER TABLE public.admin_members
  ADD COLUMN IF NOT EXISTS account_status TEXT NOT NULL DEFAULT 'ready',
  ADD COLUMN IF NOT EXISTS invited_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS password_set_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_invited_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS activated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS invited_by UUID,
  ADD COLUMN IF NOT EXISTS updated_by UUID,
  ADD COLUMN IF NOT EXISTS status_reason TEXT,
  ADD COLUMN IF NOT EXISTS last_invitation_id UUID;

COMMENT ON COLUMN public.admin_members.account_status IS
  'H3 Invitation Flow onboarding state: invited/accepted/password_pending/ready/inactive/revoked. Legacy rows default to ready; authorization requires ready + is_active.';

-- FK to invitations (table created above). Nullable: legacy rows have no invitation.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_members'::regclass
      AND conname = 'admin_members_last_invitation_fk'
  ) THEN
    ALTER TABLE public.admin_members
      ADD CONSTRAINT admin_members_last_invitation_fk
      FOREIGN KEY (last_invitation_id) REFERENCES public.admin_invitations(id);
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_members'::regclass
      AND conname = 'admin_members_account_status_allowed'
  ) THEN
    ALTER TABLE public.admin_members
      ADD CONSTRAINT admin_members_account_status_allowed
      CHECK (account_status IN ('invited', 'accepted', 'password_pending', 'ready', 'inactive', 'revoked'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_members'::regclass
      AND conname = 'admin_members_invited_open'
  ) THEN
    ALTER TABLE public.admin_members
      ADD CONSTRAINT admin_members_invited_open
      CHECK (account_status <> 'invited' OR (accepted_at IS NULL AND password_set_at IS NULL));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_members'::regclass
      AND conname = 'admin_members_inactive_not_active'
  ) THEN
    ALTER TABLE public.admin_members
      ADD CONSTRAINT admin_members_inactive_not_active
      CHECK (account_status <> 'inactive' OR is_active = false);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_members'::regclass
      AND conname = 'admin_members_revoked_not_active'
  ) THEN
    ALTER TABLE public.admin_members
      ADD CONSTRAINT admin_members_revoked_not_active
      CHECK (account_status <> 'revoked' OR is_active = false);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_members'::regclass
      AND conname = 'admin_members_revoked_timestamped'
  ) THEN
    ALTER TABLE public.admin_members
      ADD CONSTRAINT admin_members_revoked_timestamped
      CHECK (account_status <> 'revoked' OR revoked_at IS NOT NULL);
  END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_admin_members_status_active_role
  ON public.admin_members (account_status, is_active, role);
CREATE INDEX IF NOT EXISTS idx_admin_members_ready_admins
  ON public.admin_members (role, is_active, account_status)
  WHERE role = 'admin' AND is_active = true AND account_status = 'ready';
CREATE INDEX IF NOT EXISTS idx_admin_members_last_invitation
  ON public.admin_members (last_invitation_id) WHERE last_invitation_id IS NOT NULL;

-- Transition guard (design state machine):
--   invited -> accepted -> password_pending -> ready
--   invited -> expired | revoked
--   accepted -> revoked
--   password_pending -> revoked
--   ready -> inactive | revoked
--   inactive -> invited
-- Same-state updates (legacy role/is_active changes) always allowed.
-- Transition into 'ready' requires accepted_at and password_set_at (new flow only;
-- legacy rows backfilled to 'ready' are grandfathered by the column default).
CREATE OR REPLACE FUNCTION public.guard_admin_members_status_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
  IF NEW.account_status = OLD.account_status THEN
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
    IF NEW.last_invitation_id IS NULL THEN
      RAISE EXCEPTION 'admin_members transition to accepted requires last_invitation_id';
    END IF;
  END IF;
  IF NEW.account_status = 'password_pending' THEN
    NEW.accepted_at := COALESCE(NEW.accepted_at, now());
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

DROP TRIGGER IF EXISTS admin_members_status_transition_guard ON public.admin_members;
CREATE TRIGGER admin_members_status_transition_guard
  BEFORE UPDATE ON public.admin_members
  FOR EACH ROW EXECUTE FUNCTION public.guard_admin_members_status_transition();

-- Insert guard: auto-stamp invited_at/last_invited_at for new 'invited' members.
CREATE OR REPLACE FUNCTION public.guard_admin_members_status_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
  IF NEW.account_status = 'invited' THEN
    NEW.invited_at := COALESCE(NEW.invited_at, now());
    NEW.last_invited_at := COALESCE(NEW.last_invited_at, now());
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS admin_members_status_insert_guard ON public.admin_members;
CREATE TRIGGER admin_members_status_insert_guard
  BEFORE INSERT ON public.admin_members
  FOR EACH ROW EXECUTE FUNCTION public.guard_admin_members_status_insert();

-- ---------------------------------------------------------------------------
-- 3) admin_membership_audit: invitation lifecycle vocabulary + linkage
-- ---------------------------------------------------------------------------
ALTER TABLE public.admin_membership_audit
  ADD COLUMN IF NOT EXISTS entity_type TEXT NOT NULL DEFAULT 'membership',
  ADD COLUMN IF NOT EXISTS invitation_id UUID,
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_membership_audit'::regclass
      AND conname = 'admin_membership_audit_entity_allowed'
  ) THEN
    ALTER TABLE public.admin_membership_audit
      ADD CONSTRAINT admin_membership_audit_entity_allowed
      CHECK (entity_type IN ('membership', 'invitation'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.admin_membership_audit'::regclass
      AND conname = 'admin_membership_audit_invitation_fk'
  ) THEN
    ALTER TABLE public.admin_membership_audit
      ADD CONSTRAINT admin_membership_audit_invitation_fk
      FOREIGN KEY (invitation_id) REFERENCES public.admin_invitations(id);
  END IF;
END;
$$;

ALTER TABLE public.admin_membership_audit DROP CONSTRAINT IF EXISTS admin_membership_audit_action_allowed;
ALTER TABLE public.admin_membership_audit
  ADD CONSTRAINT admin_membership_audit_action_allowed
  CHECK (action IN (
    'invite', 'resend', 'accept', 'password_set',
    'role_change', 'activation', 'deactivation', 'revoke', 'expire'
  ));

CREATE INDEX IF NOT EXISTS idx_admin_membership_audit_invitation
  ON public.admin_membership_audit (invitation_id) WHERE invitation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_admin_membership_audit_entity_action
  ON public.admin_membership_audit (entity_type, action, created_at DESC);
