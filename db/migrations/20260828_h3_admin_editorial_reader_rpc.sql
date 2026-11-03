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
        'name', c.name,
        'price_pen', c.price_pen,
        'price_status', c.price_status,
        'mode', c.mode,
        'duration', c.duration,
        'description_long', c.description_long,
        'syllabus', c.syllabus,
        'target_audience', c.target_audience,
        'requirements', c.requirements,
        'certification', c.certification,
        'benefits', c.benefits,
        'objectives', c.objectives,
        'start_date_text', c.start_date_text
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
        'current_value', (
          CASE efd.field_key
            WHEN 'name' THEN to_jsonb((SELECT c.name FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'price_pen' THEN to_jsonb((SELECT c.price_pen FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'price_status' THEN to_jsonb((SELECT c.price_status FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'mode' THEN to_jsonb((SELECT c.mode FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'duration' THEN to_jsonb((SELECT c.duration FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'description_long' THEN to_jsonb((SELECT c.description_long FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'syllabus' THEN to_jsonb((SELECT c.syllabus FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'target_audience' THEN to_jsonb((SELECT c.target_audience FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'requirements' THEN to_jsonb((SELECT c.requirements FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'certification' THEN to_jsonb((SELECT c.certification FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'benefits' THEN to_jsonb((SELECT c.benefits FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'objectives' THEN to_jsonb((SELECT c.objectives FROM public.courses c WHERE c.id = p_course_id))
            WHEN 'start_date_text' THEN to_jsonb((SELECT c.start_date_text FROM public.courses c WHERE c.id = p_course_id))
            ELSE to_jsonb(NULL::text)
          END
        )
      ) ORDER BY efd.field_key
    ),
    '[]'::JSONB
  )
  INTO _field_definitions
  FROM public.editorial_field_definitions efd
  WHERE efd.field_key = ANY (ARRAY[
    'name', 'price_pen', 'price_status', 'mode', 'duration',
    'description_long', 'syllabus', 'target_audience', 'requirements',
    'certification', 'benefits', 'objectives', 'start_date_text'
  ]::TEXT[]);

  RETURN QUERY SELECT _course, _field_definitions, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_get_course_editorial(UUID) IS
  'H3: Returns the allowlisted private editorial detail and editable field definitions for one course.';

REVOKE ALL ON FUNCTION public.admin_get_course_editorial(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_get_course_editorial(UUID) TO authenticated, service_role;
