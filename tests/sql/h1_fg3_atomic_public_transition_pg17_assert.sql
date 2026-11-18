\set ON_ERROR_STOP on

SET ROLE service_role;
SELECT outcome
  FROM public.fg3_apply_public_course_transition(
    '10000000-0000-0000-0000-000000000011',
    '10000000-0000-0000-0000-000000000001',
    NULL,
    NULL,
    410,
    'start_404_grace'
  );
RESET ROLE;

DO $assertions$
DECLARE
  _outcome TEXT;
  _marker TIMESTAMPTZ;
  _active BOOLEAN;
BEGIN
  IF (SELECT last_404_at FROM public.courses WHERE id = '10000000-0000-0000-0000-000000000011') IS NULL THEN
    RAISE EXCEPTION 'service_role must be able to execute the atomic FG3 function';
  END IF;

  IF has_function_privilege('anon', 'public.fg3_apply_public_course_transition(uuid,uuid,text,timestamptz,integer,text)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'public.fg3_apply_public_course_transition(uuid,uuid,text,timestamptz,integer,text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'FG3 atomic transition must not be executable by anon or authenticated';
  END IF;
  IF NOT has_function_privilege('service_role', 'public.fg3_apply_public_course_transition(uuid,uuid,text,timestamptz,integer,text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'service_role must be able to execute the FG3 transition';
  END IF;

  SELECT transition.outcome, transition.resulting_last_404_at
    INTO _outcome, _marker
    FROM public.fg3_apply_public_course_transition(
      '10000000-0000-0000-0000-000000000012',
      '10000000-0000-0000-0000-000000000001',
      NULL,
      NULL,
      404,
      'start_404_grace'
    ) AS transition;
  IF _outcome IS DISTINCT FROM 'applied' OR _marker IS NULL THEN
    RAISE EXCEPTION 'public 404 should atomically start the grace period';
  END IF;
  IF (SELECT name FROM public.courses WHERE id = '10000000-0000-0000-0000-000000000012')
       IS DISTINCT FROM 'Harvester published snapshot'
     OR (SELECT published_editorial_values ->> 'name'
           FROM public.course_editorial_state
          WHERE course_id = '10000000-0000-0000-0000-000000000012')
       IS DISTINCT FROM 'Approved snapshot' THEN
    RAISE EXCEPTION 'FG3 may not overwrite base or published editorial values';
  END IF;

  UPDATE public.courses
     SET last_404_at = pg_catalog.clock_timestamp() - INTERVAL '1 day'
   WHERE id = '10000000-0000-0000-0000-000000000015';
  SELECT transition.outcome, transition.resulting_is_active
    INTO _outcome, _active
    FROM public.fg3_apply_public_course_transition(
      '10000000-0000-0000-0000-000000000015',
      '10000000-0000-0000-0000-000000000001',
      NULL,
      (SELECT last_404_at FROM public.courses WHERE id = '10000000-0000-0000-0000-000000000015'),
      410,
      'deactivate_after_grace'
    ) AS transition;
  IF _outcome IS DISTINCT FROM 'grace_pending' OR _active IS DISTINCT FROM TRUE THEN
    RAISE EXCEPTION 'FG3 must preserve active state before three full days';
  END IF;

  UPDATE public.courses
     SET last_404_at = pg_catalog.clock_timestamp() - INTERVAL '4 days'
   WHERE id = '10000000-0000-0000-0000-000000000016';
  SELECT last_404_at INTO _marker
    FROM public.courses
   WHERE id = '10000000-0000-0000-0000-000000000016';
  SELECT transition.outcome, transition.resulting_is_active
    INTO _outcome, _active
    FROM public.fg3_apply_public_course_transition(
      '10000000-0000-0000-0000-000000000016',
      '10000000-0000-0000-0000-000000000001',
      NULL,
      _marker,
      410,
      'deactivate_after_grace'
    ) AS transition;
  IF _outcome IS DISTINCT FROM 'applied' OR _active IS DISTINCT FROM FALSE THEN
    RAISE EXCEPTION 'confirmed 410 after grace should deactivate only the active flag';
  END IF;
  IF (SELECT last_404_at FROM public.courses WHERE id = '10000000-0000-0000-0000-000000000016')
       IS DISTINCT FROM _marker THEN
    RAISE EXCEPTION 'deactivation must preserve the original 404 marker';
  END IF;

  BEGIN
    PERFORM transition.outcome
      FROM public.fg3_apply_public_course_transition(
        '10000000-0000-0000-0000-000000000012',
        '10000000-0000-0000-0000-000000000001',
        NULL,
        NULL,
        503,
        'start_404_grace'
      ) AS transition;
    RAISE EXCEPTION 'transient status must not start a removal grace period';
  EXCEPTION WHEN SQLSTATE '22023' THEN
    NULL;
  END;

  IF has_table_privilege('anon', 'public.courses', 'UPDATE')
     OR has_table_privilege('authenticated', 'public.courses', 'UPDATE') THEN
    RAISE EXCEPTION 'the fixture must not give public roles direct course writers';
  END IF;
END;
$assertions$;

SET ROLE anon;
DO $anonymous_denial$
BEGIN
  BEGIN
    PERFORM transition.outcome
      FROM public.fg3_apply_public_course_transition(
        '10000000-0000-0000-0000-000000000012',
        '10000000-0000-0000-0000-000000000001',
        NULL,
        NULL,
        404,
        'start_404_grace'
      ) AS transition;
    RAISE EXCEPTION 'anon unexpectedly executed the FG3 transition';
  EXCEPTION WHEN insufficient_privilege THEN
    NULL;
  END;
END;
$anonymous_denial$;
RESET ROLE;

SELECT 'h1_fg3_atomic_public_transition_assertions_ok' AS result;
