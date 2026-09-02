-- H3: PR contract delta — effective-value editorial reader and publish completeness gate
-- Scope: Free/Development DDL only. CREATE OR REPLACE deltas are idempotent.
-- No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

CREATE OR REPLACE FUNCTION public.admin_get_course_editorial(
  p_course_id UUID
)
RETURNS TABLE (
  course JSONB,
  field_definitions JSONB,
  error TEXT
)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _course JSONB;
  _field_definitions JSONB;
  _missing_fields TEXT[];
  _is_admin BOOLEAN;
  _allowlist TEXT[] := ARRAY[
    'name', 'price_pen', 'price_status', 'mode', 'duration',
    'description_long', 'syllabus', 'target_audience', 'requirements',
    'certification', 'benefits', 'objectives', 'start_date_text'
  ];
BEGIN
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_editor() THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;

  _is_admin := public.admin_is_active_admin();

  SELECT
    jsonb_build_object(
      'course_id', c.id,
      'course_name', COALESCE(es.manual_overrides ->> 'name', c.name),
      'institution_name', i.name,
      'editorial_status', es.editorial_status,
      'quality_status', es.quality_status,
      'version', es.version,
      'manual_overrides', es.manual_overrides,
      'missing_fields', es.missing_fields,
      'is_sponsored', es.is_sponsored,
      'lead_cta_enabled', es.lead_cta_enabled,
      'published_at', es.published_at,
      'current_values', jsonb_build_object(
        'name', COALESCE(es.manual_overrides -> 'name', to_jsonb(c.name)),
        'price_pen', COALESCE(es.manual_overrides -> 'price_pen', to_jsonb(c.price_pen)),
        'price_status', COALESCE(es.manual_overrides -> 'price_status', to_jsonb(c.price_status)),
        'mode', COALESCE(es.manual_overrides -> 'mode', to_jsonb(c.mode)),
        'duration', COALESCE(es.manual_overrides -> 'duration', to_jsonb(c.duration)),
        'description_long', COALESCE(es.manual_overrides -> 'description_long', to_jsonb(c.description_long)),
        'syllabus', COALESCE(es.manual_overrides -> 'syllabus', to_jsonb(c.syllabus)),
        'target_audience', COALESCE(es.manual_overrides -> 'target_audience', to_jsonb(c.target_audience)),
        'requirements', COALESCE(es.manual_overrides -> 'requirements', to_jsonb(c.requirements)),
        'certification', COALESCE(es.manual_overrides -> 'certification', to_jsonb(c.certification)),
        'benefits', COALESCE(es.manual_overrides -> 'benefits', to_jsonb(c.benefits)),
        'objectives', COALESCE(es.manual_overrides -> 'objectives', to_jsonb(c.objectives)),
        'start_date_text', COALESCE(es.manual_overrides -> 'start_date_text', to_jsonb(c.start_date_text))
      )
    ),
    es.missing_fields
  INTO _course, _missing_fields
  FROM public.courses c
  JOIN public.institutions i ON i.id = c.institution_id
  JOIN public.course_editorial_state es ON es.course_id = c.id
  WHERE c.id = p_course_id;

  IF _course IS NULL THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Course not found'::TEXT;
    RETURN;
  END IF;

  SELECT COALESCE(
    jsonb_agg(
      jsonb_build_object(
        'field_key', efd.field_key,
        'target_column', efd.target_column,
        'description', efd.description,
        'is_required_for_publish', efd.is_required_for_publish,
        'is_editable', (
          _is_admin
          OR (efd.field_key = ANY (_missing_fields))
        ),
        'current_value', _course -> 'current_values' -> efd.field_key
      ) ORDER BY efd.field_key
    ),
    '[]'::JSONB
  )
  INTO _field_definitions
  FROM public.editorial_field_definitions efd
  WHERE efd.field_key = ANY (_allowlist);

  RETURN QUERY SELECT _course, _field_definitions, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_get_course_editorial(UUID) IS
  'H3: Returns the allowlisted private editorial detail and editable field definitions for one course with consistent effective values (manual overrides win).';

REVOKE ALL ON FUNCTION public.admin_get_course_editorial(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_get_course_editorial(UUID) TO authenticated, service_role;

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

  SELECT es.editorial_status, es.quality_status, cardinality(es.missing_fields)
  INTO _old_status, _quality_status, _missing_count
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
    jsonb_build_object('editorial_status', _old_status),
    jsonb_build_object('editorial_status', _new_status, 'published_at', now()),
    p_reason,
    NULL
  );

  RETURN QUERY SELECT true, p_course_id, _new_status, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_publish_course(UUID, TEXT) IS 'H3: Publish a complete course (quality complete and no missing fields) with audit.';
