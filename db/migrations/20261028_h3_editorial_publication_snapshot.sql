-- H3REQ1 CA4: separate working editorial values from the last Admin-published
-- snapshot. Forward-only and idempotent; no course backfill or operational write.
-- Validate only in Docker/PG17 here. Any Free/Pro apply requires its own JIT.

ALTER TABLE public.course_editorial_state
  ADD COLUMN IF NOT EXISTS published_manual_overrides JSONB,
  ADD COLUMN IF NOT EXISTS published_manual_start_date DATE,
  ADD COLUMN IF NOT EXISTS published_editorial_values JSONB;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'course_editorial_state_published_overrides_object'
      AND conrelid = 'public.course_editorial_state'::regclass
  ) THEN
    ALTER TABLE public.course_editorial_state
      ADD CONSTRAINT course_editorial_state_published_overrides_object
      CHECK (
        published_manual_overrides IS NULL
        OR jsonb_typeof(published_manual_overrides) = 'object'
      );
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'course_editorial_state_published_values_object'
      AND conrelid = 'public.course_editorial_state'::regclass
  ) THEN
    ALTER TABLE public.course_editorial_state
      ADD CONSTRAINT course_editorial_state_published_values_object
      CHECK (
        published_editorial_values IS NULL
        OR jsonb_typeof(published_editorial_values) = 'object'
      );
  END IF;
END;
$$;

COMMENT ON COLUMN public.course_editorial_state.published_manual_overrides IS
  'Legacy-compatible last Admin-published overrides. NULL preserves legacy published rows until first edit/publication; no mass backfill.';
COMMENT ON COLUMN public.course_editorial_state.published_manual_start_date IS
  'Legacy-compatible last Admin-published structured start date override; independent of enrollment evidence.';
COMMENT ON COLUMN public.course_editorial_state.published_editorial_values IS
  'Complete allowlisted editorial projection and public start date at last Admin publication. NULL preserves prior rows without a mass backfill.';

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
  _pipeline_values JSONB;
  _current_values JSONB;
  _published_values JSONB;
  _published_overrides JSONB;
  _has_unpublished_changes BOOLEAN := false;
  _is_publicly_visible BOOLEAN := false;
  _public_visibility_reason TEXT;
  _missing_fields TEXT[];
  _is_admin BOOLEAN;
  _course_row public.courses;
  _state public.course_editorial_state;
  _institution_name TEXT;
  _production_enabled BOOLEAN := false;
  _profile_canary BOOLEAN := false;
  _publication_source_gates BOOLEAN := false;
  _effective_availability TEXT;
  _allowlist TEXT[] := ARRAY[
    'name', 'price_pen', 'price_status', 'mode', 'duration',
    'description_long', 'syllabus', 'target_audience', 'requirements',
    'certification', 'benefits', 'objectives', 'start_date_text'
  ];
  _field_key TEXT;
BEGIN
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_editor() THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;
  _is_admin := public.admin_is_active_admin();

  SELECT c.* INTO _course_row FROM public.courses c WHERE c.id = p_course_id;
  SELECT es.* INTO _state FROM public.course_editorial_state es WHERE es.course_id = p_course_id;
  IF _course_row.id IS NULL OR _state.course_id IS NULL THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Course not found'::TEXT;
    RETURN;
  END IF;
  SELECT i.name INTO _institution_name
    FROM public.institutions i WHERE i.id = _course_row.institution_id;
  SELECT COALESCE(p.production_enabled, false),
         COALESCE(p.notes, '') = 'DB_AS_CODE_RELEASE_CANARY'
    INTO _production_enabled, _profile_canary
    FROM public.institution_site_profiles p WHERE p.institution_id = _course_row.institution_id;
  IF NOT FOUND THEN
    _production_enabled := false;
    _profile_canary := false;
  END IF;
  _publication_source_gates := _production_enabled
    AND NOT _profile_canary
    AND (_course_row.url IS NULL OR _course_row.url NOT LIKE 'https://canary.invalid/%');

  _pipeline_values := jsonb_build_object(
    'name', _course_row.name,
    'price_pen', _course_row.price_pen,
    'price_status', _course_row.price_status,
    'mode', _course_row.mode,
    'duration', _course_row.duration,
    'description_long', _course_row.description_long,
    'syllabus', _course_row.syllabus,
    'target_audience', _course_row.target_audience,
    'requirements', _course_row.requirements,
    'certification', _course_row.certification,
    'benefits', _course_row.benefits,
    'objectives', _course_row.objectives,
    'start_date_text', _course_row.start_date_text
  );
  _current_values := '{}'::JSONB;
  FOREACH _field_key IN ARRAY _allowlist LOOP
    _current_values := _current_values || jsonb_build_object(
      _field_key,
      CASE WHEN _state.manual_overrides ? _field_key
        THEN _state.manual_overrides -> _field_key
        ELSE _pipeline_values -> _field_key END
    );
  END LOOP;
  _current_values := _current_values || jsonb_build_object(
    'start_date', COALESCE(_state.manual_start_date, _course_row.start_date)
  );

  IF _state.editorial_status = 'published' THEN
    _published_overrides := COALESCE(
      _state.published_manual_overrides,
      _state.manual_overrides,
      '{}'::JSONB
    );
    IF _state.published_editorial_values IS NOT NULL THEN
      _published_values := _state.published_editorial_values;
    ELSE
      _published_values := '{}'::JSONB;
      FOREACH _field_key IN ARRAY _allowlist LOOP
        _published_values := _published_values || jsonb_build_object(
          _field_key,
          CASE WHEN _published_overrides ? _field_key
            THEN _published_overrides -> _field_key
            ELSE _pipeline_values -> _field_key END
        );
      END LOOP;
      _published_values := _published_values || jsonb_build_object(
        'start_date', COALESCE(
          CASE WHEN _state.published_manual_overrides IS NOT NULL
            THEN _state.published_manual_start_date
            ELSE _state.manual_start_date
          END,
          _course_row.start_date
        )
      );
    END IF;
    _has_unpublished_changes := _current_values IS DISTINCT FROM _published_values;
    _is_publicly_visible := COALESCE(_course_row.is_active, false)
      AND COALESCE(_course_row.is_verified, false)
      AND _publication_source_gates;
  END IF;
  _public_visibility_reason := CASE
    WHEN _state.editorial_status <> 'published' THEN 'El curso aún no está publicado.'
    WHEN NOT COALESCE(_course_row.is_active, false) THEN 'FG3 desactivó el curso tras confirmar su retirada del origen.'
    WHEN NOT COALESCE(_course_row.is_verified, false) THEN 'El curso no está verificado para el catálogo.'
    WHEN NOT _publication_source_gates THEN 'La institución o la fuente no está habilitada para el catálogo.'
    ELSE NULL
  END;

  _missing_fields := _state.missing_fields;
  _effective_availability := CASE
    WHEN _state.availability_override_status IS NOT NULL
      AND _state.availability_valid_until > now()
      THEN _state.availability_override_status
    ELSE _state.availability_status
  END;

  _course := jsonb_build_object(
    'course_id', _course_row.id,
    'course_name', _current_values ->> 'name',
    'institution_name', _institution_name,
    'source_url', _course_row.url,
    'editorial_status', _state.editorial_status,
    'quality_status', _state.quality_status,
    'version', _state.version,
    'manual_overrides', _state.manual_overrides,
    'missing_fields', _state.missing_fields,
    'field_sources', _state.field_sources,
    'field_timestamps', _state.field_timestamps,
    'is_sponsored', _state.is_sponsored,
    'lead_cta_enabled', _state.lead_cta_enabled,
    'published_at', _state.published_at,
    'current_values', _current_values,
    'pipeline_values', _pipeline_values,
    'published_values', _published_values,
    'has_unpublished_changes', _has_unpublished_changes,
    'is_publicly_visible', _is_publicly_visible,
    'public_visibility_reason', _public_visibility_reason,
    'availability_status', _effective_availability,
    'computed_availability_status', _state.availability_status,
    'availability_override_status', _state.availability_override_status,
    'availability_evidence_url', _state.availability_evidence_url,
    'availability_observed_at', _state.availability_observed_at,
    'availability_valid_until', _state.availability_valid_until,
    'availability_override_active', (
      _state.availability_override_status IS NOT NULL
      AND _state.availability_valid_until > now()
    ),
    'is_active', _course_row.is_active,
    'is_verified', _course_row.is_verified,
    'production_enabled', _production_enabled,
    'publication_source_gates', _publication_source_gates,
    'category', _course_row.category,
    'course_type', _course_row.course_type,
    'expected_monthly_salary', _course_row.expected_monthly_salary,
    'roi_months', _course_row.roi_months,
    'seniority_level', _course_row.seniority_level
  );

  SELECT COALESCE(
    jsonb_agg(
      jsonb_build_object(
        'field_key', efd.field_key,
        'target_column', efd.target_column,
        'description', efd.description,
        'is_required_for_publish', efd.is_required_for_publish,
        'is_editable', true,
        'current_value', _current_values -> efd.field_key
      ) ORDER BY efd.field_key
    ),
    '[]'::JSONB
  ) INTO _field_definitions
    FROM public.editorial_field_definitions efd
   WHERE efd.field_key = ANY (_allowlist);

  RETURN QUERY SELECT _course, _field_definitions, NULL::TEXT;
END;
$$;
CREATE OR REPLACE FUNCTION public.admin_update_course(
  p_course_id UUID,
  p_manual_overrides JSONB,
  p_version INTEGER,
  p_reason TEXT DEFAULT NULL
)
RETURNS TABLE (
  success BOOLEAN,
  course_id UUID,
  new_version INTEGER,
  error TEXT
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _current_version INTEGER;
  _new_version INTEGER;
  _actor_id UUID;
  _allowlist_keys TEXT[] := ARRAY[
    'name', 'price_pen', 'price_status', 'mode', 'duration',
    'description_long', 'syllabus', 'target_audience', 'requirements',
    'certification', 'benefits', 'objectives', 'start_date_text'
  ];
  _filtered_overrides JSONB := '{}'::JSONB;
  _current_overrides JSONB;
  _old_values JSONB;
  _new_values JSONB;
  _pipeline_values JSONB;
  _before_fields JSONB := '{}'::JSONB;
  _after_fields JSONB := '{}'::JSONB;
  _field_before JSONB;
  _field_after JSONB;
  _role TEXT;
  _editorial_status TEXT;
  _published_overrides JSONB;
  _published_editorial_values JSONB;
  _published_start_date DATE;
  _manual_start_date DATE;
  _input_keys TEXT[];
  _course_row public.courses;
  _expected_missing TEXT[];
  i INTEGER;
BEGIN
  _actor_id := (SELECT auth.uid());
  IF _actor_id IS NULL THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'No authenticated user'::TEXT;
    RETURN;
  END IF;
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_editor() THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;
  SELECT am.role INTO _role FROM public.admin_members am
   WHERE am.user_id = _actor_id
     AND am.role IN ('admin', 'user')
     AND am.is_active = true
     AND am.account_status = 'ready';
  IF _role IS NULL THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;
  IF p_manual_overrides IS NULL OR jsonb_typeof(p_manual_overrides) <> 'object' THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'Manual overrides must be a JSON object'::TEXT;
    RETURN;
  END IF;
  IF p_reason IS NULL OR char_length(btrim(p_reason)) < 8 OR char_length(p_reason) > 1000 THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'A reason of 8 to 1000 characters is required'::TEXT;
    RETURN;
  END IF;
  IF p_manual_overrides = '{}'::JSONB THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'At least one editorial field must be supplied'::TEXT;
    RETURN;
  END IF;

  SELECT es.version, es.manual_overrides, es.editorial_status,
         es.published_manual_overrides, es.published_manual_start_date,
         es.published_editorial_values,
         es.manual_start_date
    INTO _current_version, _old_values, _editorial_status,
         _published_overrides, _published_start_date,
         _published_editorial_values, _manual_start_date
    FROM public.course_editorial_state es
   WHERE es.course_id = p_course_id
   FOR UPDATE;
  IF _current_version IS NULL THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'Course not found'::TEXT;
    RETURN;
  END IF;
  IF p_version IS NULL OR _current_version IS DISTINCT FROM p_version THEN
    RETURN QUERY SELECT false, p_course_id, _current_version, 'Version conflict: record was modified'::TEXT;
    RETURN;
  END IF;

  SELECT array_agg(k) INTO _input_keys FROM jsonb_object_keys(p_manual_overrides) AS k;
  FOR i IN 1..COALESCE(array_length(_input_keys, 1), 0) LOOP
    IF NOT (_input_keys[i] = ANY (_allowlist_keys)) THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'Unknown field not allowed: ' || _input_keys[i];
      RETURN;
    END IF;
  END LOOP;

  FOR i IN 1..13 LOOP
    IF p_manual_overrides ? _allowlist_keys[i] THEN
      IF p_manual_overrides -> _allowlist_keys[i] <> 'null'::JSONB THEN
        IF _allowlist_keys[i] = 'price_pen' THEN
          IF jsonb_typeof(p_manual_overrides -> _allowlist_keys[i]) NOT IN ('string', 'number')
             OR NULLIF(btrim(p_manual_overrides ->> _allowlist_keys[i]), '') IS NOT NULL
                AND btrim(p_manual_overrides ->> _allowlist_keys[i]) !~ '^[0-9]+(\.[0-9]+)?$' THEN
            RETURN QUERY SELECT false, p_course_id, _current_version, 'price_pen must be a non-negative decimal value'::TEXT;
            RETURN;
          END IF;
        ELSIF jsonb_typeof(p_manual_overrides -> _allowlist_keys[i]) <> 'string' THEN
          RETURN QUERY SELECT false, p_course_id, _current_version, 'Editorial fields must be text or null: ' || _allowlist_keys[i];
          RETURN;
        END IF;
      END IF;
      _filtered_overrides := _filtered_overrides || jsonb_build_object(
        _allowlist_keys[i], p_manual_overrides -> _allowlist_keys[i]
      );
    END IF;
  END LOOP;

  _current_overrides := COALESCE(_old_values, '{}'::JSONB);
  _filtered_overrides := jsonb_strip_nulls(_current_overrides || _filtered_overrides);
  SELECT * INTO _course_row FROM public.courses c WHERE c.id = p_course_id FOR UPDATE;
  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, _current_version, 'Course not found'::TEXT;
    RETURN;
  END IF;
  _pipeline_values := to_jsonb(_course_row);
  FOR i IN 1..13 LOOP
    IF p_manual_overrides ? _allowlist_keys[i] THEN
      _field_before := CASE
        WHEN _current_overrides ? _allowlist_keys[i]
          THEN _current_overrides -> _allowlist_keys[i]
        ELSE _pipeline_values -> _allowlist_keys[i]
      END;
      _field_after := CASE
        WHEN p_manual_overrides -> _allowlist_keys[i] = 'null'::JSONB
          THEN _pipeline_values -> _allowlist_keys[i]
        ELSE p_manual_overrides -> _allowlist_keys[i]
      END;
      _before_fields := _before_fields || jsonb_build_object(_allowlist_keys[i], _field_before);
      _after_fields := _after_fields || jsonb_build_object(_allowlist_keys[i], _field_after);
    END IF;
  END LOOP;

  IF _editorial_status = 'published' AND _published_editorial_values IS NULL THEN
    _published_editorial_values := '{}'::JSONB;
    FOR i IN 1..13 LOOP
      _published_editorial_values := _published_editorial_values || jsonb_build_object(
        _allowlist_keys[i], CASE WHEN _current_overrides ? _allowlist_keys[i]
          THEN _current_overrides -> _allowlist_keys[i]
          ELSE _pipeline_values -> _allowlist_keys[i] END
      );
    END LOOP;
    _published_editorial_values := _published_editorial_values || jsonb_build_object(
      'start_date', COALESCE(_manual_start_date, _course_row.start_date)
    );
    _published_overrides := _current_overrides;
    _published_start_date := _manual_start_date;
  END IF;

  UPDATE public.course_editorial_state es
     SET manual_overrides = _filtered_overrides,
         published_manual_overrides = _published_overrides,
         published_manual_start_date = _published_start_date,
         published_editorial_values = _published_editorial_values,
         version = es.version + 1,
         manual_updated_at = now(),
         manual_updated_by = _actor_id,
         updated_at = now()
   WHERE es.course_id = p_course_id AND es.version = _current_version
   RETURNING es.version INTO _new_version;
  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, _current_version, 'Optimistic lock failed: version mismatch'::TEXT;
    RETURN;
  END IF;

  SELECT * INTO _course_row FROM public.courses c WHERE c.id = p_course_id;
  _expected_missing := private.h2_required_missing_fields(_course_row, _filtered_overrides);
  UPDATE public.course_editorial_state es
     SET missing_fields = _expected_missing,
         quality_status = CASE WHEN cardinality(_expected_missing) = 0 THEN 'complete' ELSE 'pending' END,
         updated_at = now()
   WHERE es.course_id = p_course_id;

  SELECT es.manual_overrides INTO _new_values
    FROM public.course_editorial_state es WHERE es.course_id = p_course_id;
  INSERT INTO public.course_editorial_audit (
    course_id, actor_user_id, action, old_values, new_values, reason
  ) VALUES (
    p_course_id,
    _actor_id,
    'update',
    jsonb_build_object('manual_overrides', _old_values, 'editorial_fields', _before_fields),
    jsonb_build_object('manual_overrides', _new_values, 'editorial_fields', _after_fields, 'version', _new_version),
    p_reason
  );
  RETURN QUERY SELECT true, p_course_id, _new_version, NULL::TEXT;
END;
$$;
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
  _is_active BOOLEAN;
  _is_verified BOOLEAN;
  _production_enabled BOOLEAN;
  _current_manual_overrides JSONB;
  _old_published_overrides JSONB;
  _current_manual_start_date DATE;
  _old_published_start_date DATE;
  _effective_published_start_date DATE;
  _old_published_editorial_values JSONB;
  _current_editorial_values JSONB;
  _publication_values JSONB;
  _course_row public.courses;
  _allowlist_keys TEXT[] := ARRAY[
    'name', 'price_pen', 'price_status', 'mode', 'duration',
    'description_long', 'syllabus', 'target_audience', 'requirements',
    'certification', 'benefits', 'objectives', 'start_date_text'
  ];
  _field_key TEXT;
  i INTEGER;
  _new_status TEXT := 'published';
BEGIN
  PERFORM public.admin_require_aal2();
  _actor_id := (SELECT auth.uid());
  IF _actor_id IS NULL OR NOT public.admin_is_active_admin() THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'User is not an active admin'::TEXT;
    RETURN;
  END IF;

  SELECT es.editorial_status, es.quality_status,
         CASE WHEN es.availability_override_status IS NOT NULL
                    AND es.availability_valid_until > now()
              THEN es.availability_override_status
              ELSE es.availability_status END,
         cardinality(es.missing_fields), c.is_active, c.is_verified,
          COALESCE(p.production_enabled, false)
            AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
            AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%'),
         es.manual_overrides, es.published_manual_overrides,
         es.manual_start_date, es.published_manual_start_date,
         es.published_editorial_values
     INTO _old_status, _quality_status, _availability_status, _missing_count,
         _is_active, _is_verified, _production_enabled,
         _current_manual_overrides, _old_published_overrides,
         _current_manual_start_date, _old_published_start_date,
         _old_published_editorial_values
    FROM public.course_editorial_state es
    JOIN public.courses c ON c.id = es.course_id
    LEFT JOIN public.institution_site_profiles p ON p.institution_id = c.institution_id
   WHERE es.course_id = p_course_id
   FOR UPDATE OF es;
  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course not found'::TEXT;
    RETURN;
  END IF;
  _current_manual_overrides := COALESCE(_current_manual_overrides, '{}'::JSONB);
  _effective_published_start_date := CASE
    WHEN _old_published_overrides IS NOT NULL THEN _old_published_start_date
    ELSE _current_manual_start_date
  END;
  SELECT * INTO _course_row FROM public.courses c WHERE c.id = p_course_id FOR UPDATE;
  _current_editorial_values := '{}'::JSONB;
  _publication_values := to_jsonb(_course_row);
  FOR i IN 1..13 LOOP
    _field_key := _allowlist_keys[i];
    _current_editorial_values := _current_editorial_values || jsonb_build_object(
      _field_key, CASE WHEN _current_manual_overrides ? _field_key
        THEN _current_manual_overrides -> _field_key
        ELSE _publication_values -> _field_key END
    );
  END LOOP;
  _current_editorial_values := _current_editorial_values || jsonb_build_object(
    'start_date', COALESCE(_current_manual_start_date, _course_row.start_date)
  );
  IF _old_status = 'published'
     AND (
       _old_published_editorial_values IS NOT NULL
       AND _old_published_editorial_values IS NOT DISTINCT FROM _current_editorial_values
       OR _old_published_editorial_values IS NULL
       AND COALESCE(_old_published_overrides, _current_manual_overrides) IS NOT DISTINCT FROM _current_manual_overrides
       AND _effective_published_start_date IS NOT DISTINCT FROM _current_manual_start_date
     ) THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course already published'::TEXT;
    RETURN;
  END IF;
  IF _quality_status IS DISTINCT FROM 'complete' OR COALESCE(_missing_count, 0) > 0 THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course is not publishable: pending quality or missing fields'::TEXT;
    RETURN;
  END IF;
  IF NOT COALESCE(_is_active, false) OR NOT COALESCE(_is_verified, false)
     OR NOT COALESCE(_production_enabled, false) THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course is not publishable: source pipeline gates are not satisfied'::TEXT;
    RETURN;
  END IF;

  UPDATE public.course_editorial_state es
     SET editorial_status = _new_status,
         published_manual_overrides = _current_manual_overrides,
         published_manual_start_date = _current_manual_start_date,
         published_editorial_values = _current_editorial_values,
         published_at = now(),
         archived_at = NULL,
         manual_updated_at = now(),
         manual_updated_by = _actor_id,
         version = es.version + 1,
         updated_at = now()
   WHERE es.course_id = p_course_id;

  INSERT INTO public.course_editorial_audit (
    course_id, actor_user_id, action, old_values, new_values, reason
  ) VALUES (
    p_course_id,
    _actor_id,
    'publish',
    jsonb_build_object(
      'editorial_status', _old_status,
      'availability_status', _availability_status,
      'published_manual_overrides', _old_published_overrides,
      'published_manual_start_date', _old_published_start_date
    ),
    jsonb_build_object(
      'editorial_status', _new_status,
      'published_at', now(),
      'published_manual_overrides', _current_manual_overrides,
      'published_manual_start_date', _current_manual_start_date,
      'published_editorial_values', _current_editorial_values
    ),
    p_reason
  );
  RETURN QUERY SELECT true, p_course_id, _new_status, NULL::TEXT;
END;
$$;
CREATE OR REPLACE FUNCTION private.h2_public_courses_effective()
RETURNS TABLE (
    id UUID,
    institution_id UUID,
    category_id UUID,
    name TEXT,
    slug VARCHAR,
    url TEXT,
    price_pen NUMERIC,
    price_status TEXT,
    mode TEXT,
    duration TEXT,
    description_long TEXT,
    syllabus TEXT,
    target_audience TEXT,
    requirements TEXT,
    certification TEXT,
    benefits TEXT,
    objectives TEXT,
    start_date DATE,
    start_date_text TEXT,
    course_type TEXT,
    brochure_url TEXT,
    expected_monthly_salary NUMERIC,
    seniority_level VARCHAR,
    roi_months NUMERIC,
    view_count INTEGER,
    comparison_count INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
  WITH eligible_courses AS (
    SELECT c.*,
           es.published_editorial_values,
           CASE WHEN es.editorial_status = 'published'
             THEN COALESCE(es.published_manual_overrides, es.manual_overrides, '{}'::JSONB)
             ELSE es.manual_overrides
           END AS manual_overrides,
           CASE WHEN es.editorial_status = 'published'
                     AND es.published_manual_overrides IS NOT NULL
             THEN es.published_manual_start_date
             ELSE es.manual_start_date
           END AS manual_start_date,
           CASE WHEN es.availability_override_status IS NOT NULL
                      AND es.availability_valid_until > now()
                THEN es.availability_override_status
                ELSE es.availability_status END AS effective_availability_status,
           (es.editorial_status = 'published') AS is_strict_public,
           EXISTS (
              SELECT 1 FROM private.h3_legacy_public_course_cohort cohort
              WHERE cohort.course_id = c.id
           ) AS is_legacy_public
      FROM public.courses c
      LEFT JOIN public.course_editorial_state es ON es.course_id = c.id
     WHERE c.is_active IS TRUE
       AND c.is_verified IS TRUE
       AND EXISTS (
         SELECT 1 FROM public.institution_site_profiles p
         WHERE p.institution_id = c.institution_id
            AND p.production_enabled IS TRUE
            AND COALESCE(p.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
       )
       AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%')
  )
  SELECT
    c.id,
    c.institution_id,
    c.category_id,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'name' THEN c.published_editorial_values ->> 'name'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'name', c.name) ELSE c.name END,
    c.slug,
    c.url,
    CASE
      WHEN c.is_strict_public AND c.published_editorial_values ? 'price_pen' THEN
        CASE WHEN c.published_editorial_values -> 'price_pen' = 'null'::JSONB THEN NULL
             ELSE (c.published_editorial_values ->> 'price_pen')::NUMERIC END
      WHEN c.is_strict_public AND c.manual_overrides ->> 'price_pen' ~ '^[0-9]+(\.[0-9]+)?$'
        THEN (c.manual_overrides ->> 'price_pen')::NUMERIC
      ELSE c.price_pen
    END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'price_status' THEN c.published_editorial_values ->> 'price_status'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'price_status', c.price_status, 'A consultar') ELSE COALESCE(c.price_status, 'A consultar') END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'mode' THEN c.published_editorial_values ->> 'mode'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'mode', c.mode) ELSE c.mode END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'duration' THEN c.published_editorial_values ->> 'duration'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'duration', c.duration) ELSE c.duration END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'description_long' THEN c.published_editorial_values ->> 'description_long'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'description_long', c.description_long) ELSE c.description_long END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'syllabus' THEN c.published_editorial_values ->> 'syllabus'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'syllabus', c.syllabus) ELSE c.syllabus END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'target_audience' THEN c.published_editorial_values ->> 'target_audience'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'target_audience', c.target_audience) ELSE c.target_audience END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'requirements' THEN c.published_editorial_values ->> 'requirements'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'requirements', c.requirements) ELSE c.requirements END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'certification' THEN c.published_editorial_values ->> 'certification'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'certification', c.certification) ELSE c.certification END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'benefits' THEN c.published_editorial_values ->> 'benefits'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'benefits', c.benefits) ELSE c.benefits END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'objectives' THEN c.published_editorial_values ->> 'objectives'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'objectives', c.objectives) ELSE c.objectives END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'start_date' THEN
           CASE WHEN c.published_editorial_values -> 'start_date' = 'null'::JSONB THEN NULL
                ELSE (c.published_editorial_values ->> 'start_date')::DATE END
         WHEN c.is_strict_public THEN COALESCE(c.manual_start_date, c.start_date) ELSE c.start_date END,
    CASE WHEN c.is_strict_public AND c.published_editorial_values ? 'start_date_text' THEN c.published_editorial_values ->> 'start_date_text'
         WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'start_date_text', c.start_date_text, 'Sin confirmar') ELSE COALESCE(c.start_date_text, 'Sin confirmar') END,
    c.course_type,
    c.brochure_url,
    c.expected_monthly_salary,
    c.seniority_level,
    c.roi_months,
    c.view_count,
    c.comparison_count,
    c.created_at,
    c.updated_at
  FROM eligible_courses c
  WHERE c.is_strict_public
     OR (c.is_legacy_public AND c.effective_availability_status IS DISTINCT FROM 'unavailable');
$$;

COMMENT ON FUNCTION public.admin_get_course_editorial(UUID) IS
  'H3 CA4: Returns editable allowlisted draft values and the last public snapshot separately for active editors.';
REVOKE ALL ON FUNCTION public.admin_get_course_editorial(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_get_course_editorial(UUID) TO authenticated, service_role;

COMMENT ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) IS
  'H3 CA4: Active editors update only allowlisted draft values with optimistic locking and an append-only before/after audit; published snapshots remain unchanged.';
REVOKE ALL ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) TO authenticated, service_role;

COMMENT ON FUNCTION public.admin_publish_course(UUID, TEXT) IS
  'H3 CA4: Admin publishes a complete editorial snapshot independently from enrollment evidence; source activity and publication gates still apply.';
REVOKE ALL ON FUNCTION public.admin_publish_course(UUID, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_publish_course(UUID, TEXT) TO authenticated, service_role;

REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;

CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS SELECT * FROM private.h2_public_courses_effective();
REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;
COMMENT ON VIEW public.courses_public_effective IS
  'H3 CA4 public reader: Admin-published editorial snapshots survive harvest changes and enrollment evidence expiry; active source and institution gates still control catalog visibility. Legacy-cohort availability handling remains compatible.';
