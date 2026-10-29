\set ON_ERROR_STOP on

-- Local-only H3REQ1 hardening regression. The enclosing canonical harness
-- supplies the schema and wraps this fixture in a transaction.
DO $$
DECLARE
  admin_id UUID := '30000000-0000-0000-0000-000000000001';
  second_admin_id UUID := '30000000-0000-0000-0000-000000000002';
  h3_user_id UUID := '30000000-0000-0000-0000-000000000004';
  invited_id UUID := '3a000000-0000-0000-0000-000000000005';
  result_row RECORD;
  audit_before INTEGER;
  member_before INTEGER;
BEGIN
  PERFORM set_config('request.jwt.claim.sub', admin_id::text, false);
  PERFORM set_config('request.jwt.claim.aal', 'aal2', false);

  IF public.admin_current_user_role() <> 'admin' THEN
    RAISE EXCEPTION 'ready legacy admin role was not preserved';
  END IF;
  IF NOT public.admin_is_active_admin() OR NOT public.admin_is_active_editor() THEN
    RAISE EXCEPTION 'ready legacy admin authorization was not preserved';
  END IF;

  -- The legacy RPC must preserve its callable contract without creating a
  -- ready/active membership outside the invitation/onboarding flow. Use the
  -- canonical ready user fixture so the guard is tested on a real Auth user.
  SELECT count(*) INTO member_before
  FROM public.admin_members AS member
  WHERE member.user_id = h3_user_id;
  SELECT * INTO result_row
  FROM public.admin_create_member('seed-4@studiamatch.local', 'user');
  IF result_row.success OR result_row.error <> 'Legacy membership creation disabled; use admin-invite' THEN
    RAISE EXCEPTION 'legacy membership creation bypass was not blocked: %', result_row.error;
  END IF;
  IF (SELECT count(*) FROM public.admin_members AS member WHERE member.user_id = h3_user_id) <> member_before THEN
    RAISE EXCEPTION 'legacy membership creation changed membership state';
  END IF;

  -- An invited or password-incomplete member can never be activated by the
  -- administrative membership RPC; onboarding must complete first.
  SELECT * INTO result_row
  FROM public.admin_update_member(invited_id, NULL, true, 'activation');
  IF result_row.success OR result_row.error <> 'Membership onboarding is not ready' THEN
    RAISE EXCEPTION 'incomplete onboarding was activated: %', result_row.error;
  END IF;
  IF (SELECT member.is_active FROM public.admin_members AS member WHERE member.user_id = invited_id) THEN
    RAISE EXCEPTION 'incomplete onboarding member became active';
  END IF;
  IF public.admin_current_user_role() <> 'admin' THEN
    RAISE EXCEPTION 'actor role changed after rejected activation';
  END IF;

  -- A user member remains an editor only when it is ready and active.
  PERFORM set_config('request.jwt.claim.sub', h3_user_id::text, false);
  IF public.admin_current_user_role() <> 'user' OR NOT public.admin_is_active_editor() THEN
    RAISE EXCEPTION 'ready user editor compatibility was not preserved';
  END IF;
  SELECT * INTO result_row
  FROM public.admin_update_member(second_admin_id, NULL, false, 'deactivation');
  IF result_row.success OR result_row.error <> 'User is not an active admin' THEN
    RAISE EXCEPTION 'non-admin member mutation was not denied: %', result_row.error;
  END IF;

  -- The last active admin cannot self-lock. Keep a second admin available for
  -- the reversible deactivation/activation check.
  PERFORM set_config('request.jwt.claim.sub', admin_id::text, false);
  SELECT count(*) INTO audit_before
  FROM public.admin_membership_audit AS audit_row
  WHERE audit_row.target_user_id = second_admin_id;
  SELECT * INTO result_row
  FROM public.admin_update_member(second_admin_id, NULL, false, 'deactivation');
  IF NOT result_row.success OR result_row.is_active THEN
    RAISE EXCEPTION 'second admin deactivation failed: %', result_row.error;
  END IF;
  SELECT * INTO result_row
  FROM public.admin_update_member(admin_id, NULL, false, 'deactivation');
  IF result_row.success OR result_row.error NOT LIKE 'Cannot%' THEN
    RAISE EXCEPTION 'last active admin protection failed: %', result_row.error;
  END IF;
  SELECT * INTO result_row
  FROM public.admin_update_member(second_admin_id, NULL, true, 'activation');
  IF NOT result_row.success OR NOT result_row.is_active THEN
    RAISE EXCEPTION 'second admin reactivation failed: %', result_row.error;
  END IF;
  IF (SELECT count(*) FROM public.admin_membership_audit AS audit_row WHERE audit_row.target_user_id = second_admin_id) < audit_before + 2 THEN
    RAISE EXCEPTION 'membership mutations did not append audit rows';
  END IF;
END;
$$;

SELECT 'h3_onboarding_rbac_hardening_harness_ok' AS result;
