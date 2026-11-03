-- H3: publication must satisfy the public availability gate.
-- Scope: Free/Development DDL only. CREATE OR REPLACE is idempotent.
-- No data backfill, Pro apply, writers, schedules, canaries, or deploys.

CREATE OR REPLACE FUNCTION public.admin_publish_course(
  p_course_id UUID,
  p_reason TEXT DEFAULT NULL
)
RETURNS TABLE (
  success BOOLEAN,
  course_id UUID,
  new_status TEXT,
  error TEXT
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _actor_id UUID;
  _old_status TEXT;
  _quality_status TEXT;
  _availability_status TEXT;
  _missing_count INTEGER;
  _new_status TEXT := 'published';
BEGIN
  PERFORM public.admin_require_aal2();
  _actor_id := (SELECT auth.uid());
  IF _actor_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::TEXT, 'No authenticated user'::TEXT;
    RETURN;
  END IF;

  IF NOT public.admin_is_active_admin() THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::TEXT, 'User is not an active admin'::TEXT;
    RETURN;
  END IF;

  SELECT es.editorial_status, es.quality_status, es.availability_status, cardinality(es.missing_fields)
  INTO _old_status, _quality_status, _availability_status, _missing_count
  FROM public.course_editorial_state es
  WHERE es.course_id = p_course_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course not found'::TEXT;
    RETURN;
  END IF;

  IF _old_status = 'published' THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course already published'::TEXT;
    RETURN;
  END IF;

  IF _quality_status IS DISTINCT FROM 'complete' OR COALESCE(_missing_count, 0) > 0 THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course is not publishable: pending quality or missing fields'::TEXT;
    RETURN;
  END IF;

  IF _availability_status IS DISTINCT FROM 'available' THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course is not publishable: availability is not confirmed'::TEXT;
    RETURN;
  END IF;

  UPDATE public.course_editorial_state
  SET editorial_status = _new_status,
      published_at = now(),
      archived_at = NULL,
      manual_updated_at = now(),
      manual_updated_by = _actor_id,
      version = public.course_editorial_state.version + 1,
      updated_at = now()
  WHERE public.course_editorial_state.course_id = p_course_id;

  INSERT INTO public.course_editorial_audit (
    course_id,
    actor_user_id,
    action,
    old_values,
    new_values,
    reason,
    request_id
  )
  VALUES (
    p_course_id,
    _actor_id,
    'publish',
    jsonb_build_object('editorial_status', _old_status, 'availability_status', _availability_status),
    jsonb_build_object('editorial_status', _new_status, 'published_at', now()),
    p_reason,
    NULL
  );

  RETURN QUERY SELECT true, p_course_id, _new_status, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_publish_course(UUID, TEXT) IS
  'H3: Publish only a complete, available course with audit.';
