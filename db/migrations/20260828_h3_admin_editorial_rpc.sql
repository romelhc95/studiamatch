-- H3: Admin editorial RPCs with optimistic locking and audit
-- Scope: Free/Development DDL only under DDL-H3-ADMIN-RPC-FREE
-- No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

-- RPC: Actualizar curso con allowlist, optimistic locking y auditoría
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
  _actor_id UUID;
  _allowlist_keys TEXT[] := ARRAY[
    'name', 'price_pen', 'price_status', 'mode', 'duration',
    'description_long', 'syllabus', 'target_audience', 'requirements',
    'certification', 'benefits', 'objectives', 'start_date_text'
  ];
  _filtered_overrides JSONB;
  _current_overrides JSONB;
  _old_values JSONB;
  _new_values JSONB;
  _is_admin BOOLEAN;
  _role TEXT;
  _missing_fields TEXT[];
  _input_keys TEXT[];
  _course_row public.courses;
  _expected_missing TEXT[];
BEGIN
  -- Verificar identidad
  _actor_id := (SELECT auth.uid());
  IF _actor_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::INTEGER, 'No authenticated user'::TEXT;
    RETURN;
  END IF;

  PERFORM public.admin_require_aal2();
  -- Verificar membresía activa
  SELECT am.role INTO _role
  FROM public.admin_members am
  WHERE am.user_id = _actor_id AND am.is_active = true;

  IF _role NOT IN ('admin', 'user') THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::INTEGER, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;

  _is_admin := (_role = 'admin');

  -- Obtener estado actual
  SELECT es.version, es.manual_overrides, es.missing_fields
  INTO _current_version, _old_values, _missing_fields
  FROM public.course_editorial_state es
  WHERE es.course_id = p_course_id;

  IF _current_version IS NULL THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::INTEGER, 'Course not found'::TEXT;
    RETURN;
  END IF;

  -- Verificar optimistic locking
  IF _current_version <> p_version THEN
    RETURN QUERY SELECT false, p_course_id, _current_version, 'Version conflict: record was modified'::TEXT;
    RETURN;
  END IF;

  -- Rechazar campos desconocidos explicitamente
  _input_keys := array_agg(k)
  FROM jsonb_object_keys(p_manual_overrides) AS k;
  FOR i IN 1..COALESCE(array_length(_input_keys, 1), 0)
  LOOP
    IF NOT (_input_keys[i] = ANY (_allowlist_keys)) THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'Unknown field not allowed: ' || _input_keys[i]::TEXT;
      RETURN;
    END IF;
  END LOOP;

  -- Filtrar overrides por allowlist; para user, solo campos en missing_fields
  _filtered_overrides := '{}'::JSONB;
  FOR i IN 1..array_length(_allowlist_keys, 1)
  LOOP
    IF p_manual_overrides ? _allowlist_keys[i] THEN
      IF _is_admin OR _allowlist_keys[i] = ANY (_missing_fields) THEN
        _filtered_overrides := _filtered_overrides || jsonb_build_object(
          _allowlist_keys[i], p_manual_overrides -> _allowlist_keys[i]
        );
      ELSE
        RETURN QUERY SELECT false, p_course_id, _current_version, 'User is not allowed to edit field: ' || _allowlist_keys[i]::TEXT;
        RETURN;
      END IF;
    END IF;
  END LOOP;

  -- Preservar overrides existentes y mergear con los nuevos
  _current_overrides := COALESCE(_old_values, '{}'::JSONB);
  _filtered_overrides := _current_overrides || _filtered_overrides;

  -- Actualizar estado editorial
  UPDATE public.course_editorial_state
  SET manual_overrides = _filtered_overrides,
      version = public.course_editorial_state.version + 1,
      manual_updated_at = now(),
      manual_updated_by = _actor_id
  WHERE public.course_editorial_state.course_id = p_course_id
    AND version = _current_version;

  GET DIAGNOSTICS _current_version = ROW_COUNT;

  IF _current_version = 0 THEN
    RETURN QUERY SELECT false, p_course_id, _current_version, 'Optimistic lock failed: version mismatch'::TEXT;
    RETURN;
  END IF;

  -- Obtener valores nuevos para auditoría
  SELECT es.manual_overrides, es.version
  INTO _new_values, _current_version
  FROM public.course_editorial_state es
  WHERE es.course_id = p_course_id;

  SELECT * INTO _course_row FROM public.courses WHERE id = p_course_id;
  _expected_missing := private.h2_required_missing_fields(_course_row, _filtered_overrides);
  UPDATE public.course_editorial_state
  SET missing_fields = _expected_missing,
      quality_status = CASE WHEN cardinality(_expected_missing) = 0 THEN 'complete' ELSE 'pending' END,
      updated_at = now()
  WHERE public.course_editorial_state.course_id = p_course_id;

  -- Crear entrada de auditoría
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
    'update',
    COALESCE(jsonb_build_object('manual_overrides', _old_values), '{}'::JSONB),
    jsonb_build_object('manual_overrides', _new_values, 'version', _current_version),
    p_reason,
    NULL
  );

  RETURN QUERY SELECT true, p_course_id, _current_version, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) IS
  'H3: Update course with allowlist validation, optimistic locking, and audit. Returns success/new_version/error.';

-- RPC: Publicar curso
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

  SELECT es.editorial_status INTO _old_status
  FROM public.course_editorial_state es
  WHERE es.course_id = p_course_id
    AND es.editorial_status <> _new_status
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course already published or not found'::TEXT;
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

COMMENT ON FUNCTION public.admin_publish_course(UUID, TEXT) IS 'H3: Publish a course. Sets editorial_status=published with audit.';

-- RPC: Despublicar curso
CREATE OR REPLACE FUNCTION public.admin_unpublish_course(
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
  _new_status TEXT := 'pending_review';
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

  SELECT es.editorial_status INTO _old_status
  FROM public.course_editorial_state es
  WHERE es.course_id = p_course_id
    AND es.editorial_status = 'published'
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course not published or not found'::TEXT;
    RETURN;
  END IF;

  UPDATE public.course_editorial_state
  SET editorial_status = _new_status,
      published_at = NULL,
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
    'unpublish',
    jsonb_build_object('editorial_status', _old_status, 'published_at', now()),
    jsonb_build_object('editorial_status', _new_status, 'published_at', NULL),
    p_reason,
    NULL
  );

  RETURN QUERY SELECT true, p_course_id, _new_status, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_unpublish_course(UUID, TEXT) IS 'H3: Unpublish a course. Sets editorial_status=pending_review with audit.';

-- RPC: Archivar curso
CREATE OR REPLACE FUNCTION public.admin_archive_course(
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
  _new_status TEXT := 'archived';
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

  SELECT es.editorial_status INTO _old_status
  FROM public.course_editorial_state es
  WHERE es.course_id = p_course_id
    AND es.editorial_status <> _new_status
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course already archived or not found'::TEXT;
    RETURN;
  END IF;

  UPDATE public.course_editorial_state
  SET editorial_status = _new_status,
      archived_at = now(),
      published_at = NULL,
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
    'archive',
    jsonb_build_object('editorial_status', _old_status),
    jsonb_build_object('editorial_status', _new_status, 'archived_at', now()),
    p_reason,
    NULL
  );

  RETURN QUERY SELECT true, p_course_id, _new_status, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_archive_course(UUID, TEXT) IS 'H3: Archive a course. Sets editorial_status=archived with audit.';

-- RPC: Actualizar estado de calidad
CREATE OR REPLACE FUNCTION public.admin_update_quality_status(
  p_course_id UUID,
  p_quality_status TEXT,
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
  _valid_statuses TEXT[] := ARRAY['pending', 'complete', 'blocked'];
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

  IF NOT p_quality_status = ANY(_valid_statuses) THEN
    RETURN QUERY SELECT false, NULL::UUID, NULL::TEXT, 'Invalid quality status'::TEXT;
    RETURN;
  END IF;

  SELECT es.quality_status INTO _old_status
  FROM public.course_editorial_state es
  WHERE es.course_id = p_course_id
    AND es.quality_status <> p_quality_status
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course not found or status unchanged'::TEXT;
    RETURN;
  END IF;

  UPDATE public.course_editorial_state
  SET quality_status = p_quality_status,
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
    'update_quality_status',
    jsonb_build_object('quality_status', _old_status),
    jsonb_build_object('quality_status', p_quality_status),
    p_reason,
    NULL
  );

  RETURN QUERY SELECT true, p_course_id, p_quality_status, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_update_quality_status(UUID, TEXT, TEXT) IS 'H3: Update quality status (pending/complete/blocked) with audit.';

-- La identidad se valida dentro de cada RPC; anon no puede ejecutarlas.
REVOKE ALL ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_publish_course(UUID, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_unpublish_course(UUID, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_archive_course(UUID, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_update_quality_status(UUID, TEXT, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_publish_course(UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_unpublish_course(UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_archive_course(UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_update_quality_status(UUID, TEXT, TEXT) TO authenticated, service_role;
