-- H3 PG17 non-destructive harness for studiamatch_h3
-- Scope: local Docker only; uses transaction + SET LOCAL for identity.
-- This harness does NOT create tables, schemas, or users; it assumes H3 migrations exist.

\set ON_ERROR_STOP on

BEGIN;

CREATE OR REPLACE FUNCTION auth.jwt()
RETURNS JSONB
LANGUAGE sql
STABLE
SET search_path = pg_catalog
AS $$
  SELECT jsonb_build_object('aal', current_setting('request.jwt.claim.aal', true))
$$;

DO $$
DECLARE
  missing TEXT;
BEGIN
  SELECT string_agg(routine_name, ', ')
  INTO missing
  FROM (VALUES
    ('admin_current_user_role'),
    ('admin_is_active_admin'),
    ('admin_is_active_editor'),
    ('admin_user_can_edit_field'),
    ('admin_get_course_queue'),
    ('admin_count_course_queue'),
    ('admin_get_course_editorial'),
    ('admin_update_course'),
    ('admin_publish_course'),
    ('admin_unpublish_course'),
    ('admin_archive_course'),
    ('admin_update_quality_status'),
    ('admin_list_members'),
    ('admin_create_member')
  ) AS required(routine_name)
  WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.routines
    WHERE routine_schema = 'public' AND routine_name = required.routine_name
  );
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'Missing required routines: %', missing;
  END IF;
END;
$$;

DO $$
BEGIN
  PERFORM set_config('h3.test_password', 'local-only-fixture-password', true);

  DELETE FROM public.admin_members WHERE user_id IN (
    '31000000-0000-0000-0000-000000000001',
    '31000000-0000-0000-0000-000000000002',
    '31000000-0000-0000-0000-000000000003',
    '31000000-0000-0000-0000-000000000004'
  );
  DELETE FROM auth.users WHERE id IN (
    '31000000-0000-0000-0000-000000000001',
    '31000000-0000-0000-0000-000000000002',
    '31000000-0000-0000-0000-000000000003',
    '31000000-0000-0000-0000-000000000004'
  );

  INSERT INTO auth.users (id, email, encrypted_password, role, aud, email_confirmed_at, created_at, updated_at)
  VALUES
    ('31000000-0000-0000-0000-000000000001', 'h3-admin@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
    ('31000000-0000-0000-0000-000000000002', 'h3-user@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
    ('31000000-0000-0000-0000-000000000003', 'h3-auth@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
    ('31000000-0000-0000-0000-000000000004', 'h3-inactive@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now());

  INSERT INTO public.admin_members (user_id, role, is_active)
  VALUES
    ('31000000-0000-0000-0000-000000000001', 'admin', true),
    ('31000000-0000-0000-0000-000000000002', 'user', true),
    ('31000000-0000-0000-0000-000000000004', 'user', false);
END;
$$;

-- Idempotency guard: re-running the local seed must not grow any fixture table.
CREATE TEMP TABLE pg_temp.h3_seed_audit(kind TEXT PRIMARY KEY, n BIGINT);
INSERT INTO pg_temp.h3_seed_audit VALUES
  ('auth_users', (SELECT count(*) FROM auth.users)),
  ('active_admins', (SELECT count(*) FROM public.admin_members WHERE is_active AND role = 'admin')),
  ('active_users', (SELECT count(*) FROM public.admin_members WHERE is_active AND role = 'user')),
  ('inactive_members', (SELECT count(*) FROM public.admin_members WHERE NOT is_active)),
  ('institutions', (SELECT count(*) FROM public.institutions)),
  ('courses', (SELECT count(*) FROM public.courses)),
  ('editorial_states', (SELECT count(*) FROM public.course_editorial_state));

\ir ../../db/seeds/h3_admin_seed_local.sql

DO $$
DECLARE
    current_n BIGINT;
BEGIN
    SELECT count(*) INTO current_n FROM auth.users;
    IF current_n <> (SELECT n FROM pg_temp.h3_seed_audit WHERE kind = 'auth_users') THEN
        RAISE EXCEPTION 'idempotent seed re-run changed auth_users to %', current_n;
    END IF;

    SELECT count(*) INTO current_n FROM public.admin_members WHERE is_active AND role = 'admin';
    IF current_n <> (SELECT n FROM pg_temp.h3_seed_audit WHERE kind = 'active_admins') THEN
        RAISE EXCEPTION 'idempotent seed re-run changed active_admins to %', current_n;
    END IF;

    SELECT count(*) INTO current_n FROM public.admin_members WHERE is_active AND role = 'user';
    IF current_n <> (SELECT n FROM pg_temp.h3_seed_audit WHERE kind = 'active_users') THEN
        RAISE EXCEPTION 'idempotent seed re-run changed active_users to %', current_n;
    END IF;

    SELECT count(*) INTO current_n FROM public.admin_members WHERE NOT is_active;
    IF current_n <> (SELECT n FROM pg_temp.h3_seed_audit WHERE kind = 'inactive_members') THEN
        RAISE EXCEPTION 'idempotent seed re-run changed inactive_members to %', current_n;
    END IF;

    SELECT count(*) INTO current_n FROM public.courses;
    IF current_n <> (SELECT n FROM pg_temp.h3_seed_audit WHERE kind = 'courses') THEN
        RAISE EXCEPTION 'idempotent seed re-run changed courses to %', current_n;
    END IF;

    SELECT count(*) INTO current_n FROM public.course_editorial_state;
    IF current_n <> (SELECT n FROM pg_temp.h3_seed_audit WHERE kind = 'editorial_states') THEN
        RAISE EXCEPTION 'idempotent seed re-run changed editorial_states to %', current_n;
    END IF;
END;
$$;

DO $$
DECLARE
  target_course UUID;
  admin_id UUID := '31000000-0000-0000-0000-000000000001';
  user_id UUID := '31000000-0000-0000-0000-000000000002';
  auth_id UUID := '31000000-0000-0000-0000-000000000003';
  inactive_id UUID := '31000000-0000-0000-0000-000000000004';
  role_value TEXT;
  queue_count INTEGER;
  total_count INTEGER;
  detail_result RECORD;
  upd_result RECORD;
  conflict_result RECORD;
  pub_result RECORD;
  arch_result RECORD;
  quality_result RECORD;
  editable_count INTEGER;
  list_count INTEGER;
  create_result RECORD;
  missing_field_key TEXT;
BEGIN
  PERFORM set_config('request.jwt.claim.sub', admin_id::text, false);
  PERFORM set_config('request.jwt.claim.aal', 'aal2', false);

  IF NOT public.admin_is_active_admin() THEN
    RAISE EXCEPTION 'local admin identity was not authorized';
  END IF;

  SELECT public.admin_current_user_role() INTO role_value;
  IF role_value <> 'admin' THEN RAISE EXCEPTION 'expected admin role, got %', role_value; END IF;

  SELECT count(*) INTO queue_count FROM public.admin_course_queue;
  IF queue_count <> 25 THEN RAISE EXCEPTION 'expected 25 non-archived queue rows, got %', queue_count; END IF;

  SELECT q.total INTO total_count
  FROM public.admin_count_course_queue('pending_review', 'complete') q;
  IF total_count <> 10 THEN RAISE EXCEPTION 'expected filtered count 10, got %', total_count; END IF;

  IF EXISTS (SELECT 1 FROM public.admin_get_course_queue(20, NULL, 'invalid', NULL) q WHERE q.error <> 'Invalid editorial status') THEN
    RAISE EXCEPTION 'invalid editorial filter was not rejected';
  END IF;
  IF EXISTS (SELECT 1 FROM public.admin_get_course_queue(20, '{"id":"bad"}', NULL, NULL) q WHERE q.error <> 'Invalid cursor format') THEN
    RAISE EXCEPTION 'invalid cursor was not rejected';
  END IF;

  SELECT course_id INTO target_course FROM public.course_editorial_state
  ORDER BY course_id LIMIT 1;
   UPDATE public.courses
   SET duration = NULL
   WHERE public.courses.id = target_course;

   UPDATE public.course_editorial_state
   SET missing_fields = ARRAY['duration']::TEXT[], quality_status = 'pending'
   WHERE public.course_editorial_state.course_id = target_course;

  SELECT * INTO detail_result FROM public.admin_get_course_editorial(target_course);
  IF detail_result.error IS NOT NULL OR detail_result.course ->> 'course_id' <> target_course::text THEN
    RAISE EXCEPTION 'editorial detail reader failed: %', detail_result.error;
  END IF;
  IF jsonb_array_length(detail_result.field_definitions) <> 13 THEN
    RAISE EXCEPTION 'expected 13 editable field definitions';
  END IF;

  SELECT * INTO upd_result FROM public.admin_update_course(target_course, '{"name":"Programa H3 editado"}'::jsonb, (detail_result.course->>'version')::int, 'local validation');
  IF NOT upd_result.success THEN RAISE EXCEPTION 'admin update failed: %', upd_result.error; END IF;

  SELECT * INTO conflict_result FROM public.admin_update_course(target_course, '{"name":"Conflicto"}'::jsonb, (detail_result.course->>'version')::int, 'stale version');
  IF conflict_result.success OR conflict_result.error NOT LIKE 'Version conflict:%' THEN
    RAISE EXCEPTION 'optimistic lock conflict was not enforced';
  END IF;

   IF (SELECT count(*) FROM public.course_editorial_audit WHERE course_id = target_course AND action = 'update') <> 1 THEN
     RAISE EXCEPTION 'update audit was not appended';
   END IF;

   IF has_table_privilege('service_role', 'public.course_editorial_audit', 'UPDATE') OR has_table_privilege('service_role', 'public.course_editorial_audit', 'DELETE') OR has_table_privilege('service_role', 'public.course_editorial_audit', 'TRUNCATE') THEN
     RAISE EXCEPTION 'service role has forbidden audit mutation privilege';
   END IF;
   IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.course_editorial_audit'::regclass AND tgname = 'prevent_course_editorial_audit_update') OR NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.course_editorial_audit'::regclass AND tgname = 'prevent_course_editorial_audit_delete') THEN
     RAISE EXCEPTION 'append-only audit triggers are missing';
   END IF;

   SELECT count(*) INTO list_count FROM public.admin_list_members();
  IF list_count < 4 THEN RAISE EXCEPTION 'expected at least 4 members, got %', list_count; END IF;

  SELECT * INTO create_result FROM public.admin_create_member('h3-auth@local.test', 'user');
  IF NOT create_result.success THEN RAISE EXCEPTION 'admin_create_member failed: %', create_result.error; END IF;

  SELECT * INTO create_result FROM public.admin_create_member('h3-auth@local.test', 'user');
  IF create_result.success OR create_result.error NOT LIKE 'Duplicate email%' THEN
    RAISE EXCEPTION 'duplicate membership not rejected';
  END IF;

  SELECT * INTO create_result FROM public.admin_create_member('h3-auth@local.test', 'superuser');
  IF create_result.success OR create_result.error NOT LIKE 'Invalid role%' THEN
    RAISE EXCEPTION 'invalid role not rejected';
  END IF;

  SELECT * INTO create_result FROM public.admin_create_member('no-existe@local.test', 'user');
  IF create_result.success OR create_result.error NOT LIKE 'Email not found%' THEN
    RAISE EXCEPTION 'unknown email not rejected';
  END IF;

  PERFORM set_config('request.jwt.claim.sub', user_id::text, false);
  PERFORM set_config('request.jwt.claim.aal', 'aal2', false);

  SELECT public.admin_current_user_role() INTO role_value;
  IF role_value <> 'user' THEN RAISE EXCEPTION 'expected user role, got %', role_value; END IF;

  IF NOT public.admin_is_active_editor() THEN RAISE EXCEPTION 'user should be active editor'; END IF;
  IF public.admin_is_active_admin() THEN RAISE EXCEPTION 'user must not be admin'; END IF;

  SELECT * INTO detail_result FROM public.admin_get_course_editorial(target_course);
  IF detail_result.error IS NOT NULL THEN RAISE EXCEPTION 'user editorial detail reader failed: %', detail_result.error; END IF;

  SELECT count(*) INTO editable_count
  FROM jsonb_array_elements(detail_result.field_definitions) d
  WHERE (d->>'is_editable')::boolean IS TRUE;
  IF editable_count < 1 THEN RAISE EXCEPTION 'expected at least 1 editable field for user, got %', editable_count; END IF;

  SELECT field_key INTO missing_field_key
  FROM jsonb_array_elements_text(detail_result.course->'missing_fields') AS field_key
  LIMIT 1;

  IF NOT public.admin_user_can_edit_field(target_course, missing_field_key) THEN
    RAISE EXCEPTION 'missing field should be editable by user';
  END IF;

  SELECT * INTO upd_result
  FROM public.admin_update_course(target_course, '{"name":"No deberia"}'::jsonb, (detail_result.course->>'version')::int, 'user forbidden field');
  IF upd_result.success OR upd_result.error NOT LIKE 'User is not allowed to edit field%' THEN
    RAISE EXCEPTION 'user should not be able to edit complete field';
  END IF;

  SELECT * INTO upd_result
  FROM public.admin_update_course(target_course, '{"unknown_field":"No deberia"}'::jsonb, (detail_result.course->>'version')::int, 'unknown field');
  IF upd_result.success OR upd_result.error NOT LIKE 'Unknown field not allowed:%' THEN
    RAISE EXCEPTION 'unknown field should be rejected';
  END IF;

  SELECT * INTO pub_result FROM public.admin_publish_course(target_course);
  IF pub_result.success OR pub_result.error <> 'User is not an active admin' THEN
    RAISE EXCEPTION 'user must not publish';
  END IF;

  SELECT * INTO pub_result FROM public.admin_unpublish_course(target_course);
  IF pub_result.success OR pub_result.error <> 'User is not an active admin' THEN
    RAISE EXCEPTION 'user must not unpublish';
  END IF;

  SELECT * INTO arch_result FROM public.admin_archive_course(target_course);
  IF arch_result.success OR arch_result.error <> 'User is not an active admin' THEN
    RAISE EXCEPTION 'user must not archive';
  END IF;

  SELECT * INTO quality_result FROM public.admin_update_quality_status(target_course, 'complete');
  IF quality_result.success OR quality_result.error <> 'User is not an active admin' THEN
    RAISE EXCEPTION 'user must not change quality';
  END IF;

  PERFORM set_config('request.jwt.claim.sub', '', false);
  SELECT public.admin_current_user_role() INTO role_value;
  IF role_value <> 'anon' THEN RAISE EXCEPTION 'expected anon role, got %', role_value; END IF;
  IF public.admin_is_active_editor() THEN RAISE EXCEPTION 'anon must not be editor'; END IF;

  SELECT * INTO detail_result FROM public.admin_get_course_editorial(target_course);
  IF detail_result.error <> 'User is not an active editor' OR detail_result.course IS NOT NULL THEN
    RAISE EXCEPTION 'anonymous editorial detail reader was not denied';
  END IF;

  -- Use an auth user that is guaranteed to have no admin_members row
  PERFORM set_config('request.jwt.claim.sub', '31000000-0000-0000-0000-00000000f999', false);
  SELECT public.admin_current_user_role() INTO role_value;
  IF role_value <> 'authenticated' THEN RAISE EXCEPTION 'expected authenticated role without membership, got %', role_value; END IF;
  IF public.admin_is_active_editor() THEN RAISE EXCEPTION 'authenticated without membership must not be editor'; END IF;

  PERFORM set_config('request.jwt.claim.sub', auth_id::text, false);
  SELECT * INTO create_result FROM public.admin_create_member('h3-admin@local.test', 'user');
  IF create_result.success OR create_result.error <> 'User is not an active admin' THEN
    RAISE EXCEPTION 'non-admin user must not manage members';
  END IF;

  PERFORM set_config('request.jwt.claim.sub', inactive_id::text, false);
  SELECT public.admin_current_user_role() INTO role_value;
  IF role_value <> 'authenticated' THEN RAISE EXCEPTION 'inactive user must be authenticated (no active role), got %', role_value; END IF;
  IF public.admin_is_active_editor() THEN RAISE EXCEPTION 'inactive user must not be editor'; END IF;

  PERFORM set_config('request.jwt.claim.sub', 'invalid-uuid', false);
  SELECT public.admin_current_user_role() INTO role_value;
  IF role_value <> 'anon' THEN RAISE EXCEPTION 'invalid uuid should be anon, got %', role_value; END IF;
END;
$$;

DO $$
DECLARE
    admin_id UUID := '31000000-0000-0000-0000-000000000001';
    draft_course UUID;
    complete_course UUID;
    detail_result RECORD;
    upd_result RECORD;
    pub_result RECORD;
    override_name TEXT;
BEGIN
    PERFORM set_config('request.jwt.claim.sub', admin_id::text, false);
    PERFORM set_config('request.jwt.claim.aal', 'aal2', false);

    SELECT es.course_id INTO draft_course
    FROM public.course_editorial_state es
    WHERE es.editorial_status = 'draft' AND cardinality(es.missing_fields) > 0
    ORDER BY es.course_id
    LIMIT 1;
    IF draft_course IS NULL THEN
        RAISE EXCEPTION 'no incomplete draft course available for publish gate test';
    END IF;

    -- Completeness gate: an incomplete draft must not be publishable.
    SELECT * INTO pub_result
    FROM public.admin_publish_course(draft_course);
    IF pub_result.success OR pub_result.error NOT LIKE 'Course is not publishable:%' THEN
        RAISE EXCEPTION 'publish gate did not reject an incomplete draft: %', pub_result.error;
    END IF;

    -- Effective-value reader: a manual override must win in course_name, current_values and field current_value.
    SELECT * INTO detail_result
    FROM public.admin_get_course_editorial(draft_course);
    IF detail_result.error IS NOT NULL THEN
        RAISE EXCEPTION 'editorial reader failed: %', detail_result.error;
    END IF;

    override_name := 'Override efectivo ' || draft_course::text;
    SELECT * INTO upd_result
    FROM public.admin_update_course(
        draft_course,
        jsonb_build_object('name', override_name),
        (detail_result.course ->> 'version')::int,
        'effective reader local validation'
    );
    IF NOT upd_result.success THEN
        RAISE EXCEPTION 'admin update failed for effective reader test: %', upd_result.error;
    END IF;

    SELECT * INTO detail_result
    FROM public.admin_get_course_editorial(draft_course);
    IF detail_result.error IS NOT NULL THEN
        RAISE EXCEPTION 'editorial re-read failed: %', detail_result.error;
    END IF;
    IF detail_result.course ->> 'course_name' IS DISTINCT FROM override_name
       OR detail_result.course -> 'current_values' ->> 'name' IS DISTINCT FROM override_name THEN
        RAISE EXCEPTION 'effective name is inconsistent after override';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM jsonb_array_elements(detail_result.field_definitions) d
        WHERE d ->> 'field_key' = 'name' AND d ->> 'current_value' = override_name
    ) THEN
        RAISE EXCEPTION 'field definition current_value does not reflect the manual override';
    END IF;

    -- A complete pending_review course can be published by an admin with audit.
    SELECT es.course_id INTO complete_course
    FROM public.course_editorial_state es
    WHERE es.editorial_status = 'pending_review'
      AND es.quality_status = 'complete'
      AND cardinality(es.missing_fields) = 0
    ORDER BY es.course_id
    LIMIT 1;
    IF complete_course IS NULL THEN
        RAISE EXCEPTION 'no complete pending_review course available for publish gate test';
    END IF;

    SELECT * INTO pub_result
    FROM public.admin_publish_course(complete_course);
    IF NOT pub_result.success OR pub_result.new_status <> 'published' THEN
        RAISE EXCEPTION 'admin publish of a complete course failed: %', pub_result.error;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.course_editorial_audit
        WHERE course_id = complete_course AND action = 'publish'
    ) THEN
        RAISE EXCEPTION 'publish audit was not appended';
    END IF;
END;
$$;

ROLLBACK;

SELECT 'h3_pg17_harness_local_ok' AS result;
