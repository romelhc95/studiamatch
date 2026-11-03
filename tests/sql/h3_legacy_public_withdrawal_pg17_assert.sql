\set ON_ERROR_STOP on
-- StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261102-h3-legacy-public-withdrawal

DO $$
DECLARE
  _value TEXT;
  _price NUMERIC;
  _before_courses BIGINT;
  _before_cohort BIGINT;
  _before_snapshots BIGINT;
BEGIN
  SELECT count(*) INTO _before_courses FROM public.courses;
  SELECT count(*) INTO _before_cohort FROM private.h2_legacy_public_course_cohort;
  SELECT count(*) INTO _before_snapshots
    FROM public.course_editorial_state
   WHERE published_editorial_values IS NOT NULL;

  SELECT name INTO _value FROM public.courses_public_effective
   WHERE id = '10000000-0000-0000-0000-000000000011';
  IF _value IS DISTINCT FROM 'Harvester untouched legacy' THEN
    RAISE EXCEPTION 'untouched legacy course must remain visible with its compatible value';
  END IF;

  SELECT name, price_pen INTO _value, _price FROM public.courses_public_effective
   WHERE id = '10000000-0000-0000-0000-000000000012';
  IF _value IS DISTINCT FROM 'Approved snapshot' THEN
    RAISE EXCEPTION 'published snapshot must remain visible with editorial content';
  END IF;
  IF _price IS NOT NULL THEN
    RAISE EXCEPTION 'malformed published price must be projected as null by the effective reader';
  END IF;

  UPDATE public.course_editorial_state
     SET editorial_status = 'pending_review'
   WHERE course_id = '10000000-0000-0000-0000-000000000013';
  INSERT INTO public.course_editorial_audit (course_id, action)
  VALUES ('10000000-0000-0000-0000-000000000013', 'unpublish');
  IF EXISTS (SELECT 1 FROM public.courses_public_effective
              WHERE id = '10000000-0000-0000-0000-000000000013') THEN
    RAISE EXCEPTION 'explicit unpublish must withdraw a legacy course and prevent its legacy value from returning';
  END IF;

  UPDATE public.course_editorial_state
     SET editorial_status = 'archived'
   WHERE course_id = '10000000-0000-0000-0000-000000000014';
  INSERT INTO public.course_editorial_audit (course_id, action)
  VALUES ('10000000-0000-0000-0000-000000000014', 'archive');
  IF EXISTS (SELECT 1 FROM public.courses_public_effective
              WHERE id = '10000000-0000-0000-0000-000000000014') THEN
    RAISE EXCEPTION 'explicit archive must withdraw a legacy course and prevent its legacy value from returning';
  END IF;

  UPDATE public.course_editorial_state
     SET editorial_status = 'published'
   WHERE course_id = '10000000-0000-0000-0000-000000000013';
  SELECT name INTO _value FROM public.courses_public_effective
   WHERE id = '10000000-0000-0000-0000-000000000013';
  IF _value IS DISTINCT FROM 'Approved snapshot before withdrawal' THEN
    RAISE EXCEPTION 'republished course must use its approved snapshot rather than the harvester value';
  END IF;

  IF (SELECT count(*) FROM public.courses) IS DISTINCT FROM _before_courses THEN
    RAISE EXCEPTION 'course rows must be preserved';
  END IF;
  IF (SELECT count(*) FROM private.h2_legacy_public_course_cohort) IS DISTINCT FROM _before_cohort THEN
    RAISE EXCEPTION 'H2 cohort rows must be preserved';
  END IF;
  IF (SELECT count(*) FROM public.course_editorial_state
       WHERE published_editorial_values IS NOT NULL) IS DISTINCT FROM _before_snapshots THEN
    RAISE EXCEPTION 'published editorial snapshots must be preserved';
  END IF;
  IF (SELECT count(*) FROM public.course_editorial_audit) <> 2 THEN
    RAISE EXCEPTION 'append-only audit rows must be preserved';
  END IF;
  IF has_table_privilege('anon', 'private.h3_legacy_public_course_cohort', 'SELECT')
     OR has_table_privilege('authenticated', 'private.h3_legacy_public_course_cohort', 'SELECT')
     OR has_table_privilege('service_role', 'private.h3_legacy_public_course_cohort', 'SELECT') THEN
    RAISE EXCEPTION 'private legacy cohort projection must not expose direct table access';
  END IF;
  IF NOT has_function_privilege('anon', 'private.h2_public_courses_effective()', 'EXECUTE')
     OR NOT has_table_privilege('anon', 'public.courses_public_effective', 'SELECT') THEN
    RAISE EXCEPTION 'anonymous reader must retain only its intended public projection access';
  END IF;
END;
$$;

SET ROLE anon;
SELECT id, name FROM public.courses_public_effective ORDER BY id;
RESET ROLE;
SELECT 'h3_legacy_public_withdrawal_pg17_ok' AS result;
