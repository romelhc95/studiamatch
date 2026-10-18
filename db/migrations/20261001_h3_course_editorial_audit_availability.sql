-- H3: Admin-readable audit, evidence-backed availability override, and
-- effective-value preservation for editorial corrections.
-- Local Docker/PG17 validation only; Free DDL/writes and all deployments require
-- separate JIT approval. No backfill, schedule, writer, or legacy cohort removal.

-- H2 Pro retires this cohort after strict parity; Free may still retain it during
-- the compatibility phase. Keep one stable reader contract without recreating
-- retired cohort data in Pro.
DO $$
BEGIN
  IF to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL THEN
    EXECUTE 'CREATE OR REPLACE VIEW private.h3_legacy_public_course_cohort AS
             SELECT course_id FROM private.h2_legacy_public_course_cohort';
  ELSE
    EXECUTE 'CREATE OR REPLACE VIEW private.h3_legacy_public_course_cohort AS
             SELECT NULL::UUID AS course_id WHERE false';
  END IF;
END;
$$;
REVOKE ALL ON TABLE private.h3_legacy_public_course_cohort FROM PUBLIC, anon, authenticated, service_role;

ALTER TABLE public.course_editorial_state
  ADD COLUMN IF NOT EXISTS availability_override_status TEXT,
  ADD COLUMN IF NOT EXISTS availability_evidence_url TEXT,
  ADD COLUMN IF NOT EXISTS availability_observed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS availability_valid_until TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS availability_override_by UUID;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'course_editorial_state_availability_override_valid'
      AND conrelid = 'public.course_editorial_state'::regclass
  ) THEN
    ALTER TABLE public.course_editorial_state
      ADD CONSTRAINT course_editorial_state_availability_override_valid
      CHECK (
        (
          availability_override_status IS NULL
          AND availability_evidence_url IS NULL
          AND availability_observed_at IS NULL
          AND availability_valid_until IS NULL
          AND availability_override_by IS NULL
        )
        OR (
          availability_override_status IN ('available', 'unavailable')
           AND availability_evidence_url IS NOT NULL
           AND availability_evidence_url ~* '^https://'
           AND availability_observed_at IS NOT NULL
           AND availability_valid_until IS NOT NULL
           AND availability_valid_until > availability_observed_at
           AND (availability_valid_until AT TIME ZONE 'UTC')
               <= (availability_observed_at AT TIME ZONE 'UTC') + INTERVAL '90 days'
           AND availability_override_by IS NOT NULL
        )
      );
  END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_course_editorial_state_availability_override_expiry
  ON public.course_editorial_state (availability_valid_until, course_id)
  WHERE availability_override_status IS NOT NULL;

-- An explicit human assessment remains separate from the computed pipeline
-- value. It is effective only until its evidence expires; expiry is fail-closed.
CREATE OR REPLACE FUNCTION public.admin_set_course_availability(
  p_course_id UUID,
  p_availability_status TEXT,
  p_evidence_url TEXT,
  p_observed_at TIMESTAMPTZ,
  p_valid_until TIMESTAMPTZ,
  p_version INTEGER,
  p_reason TEXT
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
  _actor_id UUID;
  _current_version INTEGER;
  _old_status TEXT;
  _old_url TEXT;
  _old_observed_at TIMESTAMPTZ;
  _old_valid_until TIMESTAMPTZ;
  _course_url TEXT;
  _course_host TEXT;
  _evidence_host TEXT;
  _new_version INTEGER;
BEGIN
  PERFORM public.admin_require_aal2();
  _actor_id := (SELECT auth.uid());
  IF _actor_id IS NULL OR NOT public.admin_is_active_admin() THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'User is not an active admin'::TEXT;
    RETURN;
  END IF;

  IF p_version IS NULL THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'Course version is required'::TEXT;
    RETURN;
  END IF;
  IF p_reason IS NULL OR char_length(btrim(p_reason)) < 8 OR char_length(p_reason) > 1000 THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'A reason of 8 to 1000 characters is required'::TEXT;
    RETURN;
  END IF;

  SELECT es.version, es.availability_override_status,
         es.availability_evidence_url, es.availability_observed_at,
         es.availability_valid_until, c.url
    INTO _current_version, _old_status, _old_url, _old_observed_at,
         _old_valid_until, _course_url
    FROM public.course_editorial_state es
    JOIN public.courses c ON c.id = es.course_id
   WHERE es.course_id = p_course_id
   FOR UPDATE OF es;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, NULL::INTEGER, 'Course not found'::TEXT;
    RETURN;
  END IF;
  IF _current_version <> p_version THEN
    RETURN QUERY SELECT false, p_course_id, _current_version, 'Version conflict: record was modified'::TEXT;
    RETURN;
  END IF;

  IF p_availability_status IS NULL THEN
    IF p_evidence_url IS NOT NULL OR p_observed_at IS NOT NULL OR p_valid_until IS NOT NULL THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'Clearing an override cannot include new evidence'::TEXT;
      RETURN;
    END IF;
    IF _old_status IS NULL THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'No manual availability override exists'::TEXT;
      RETURN;
    END IF;
  ELSE
    IF p_availability_status NOT IN ('available', 'unavailable') THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'Availability must be available or unavailable'::TEXT;
      RETURN;
    END IF;
    IF p_evidence_url IS NULL OR char_length(p_evidence_url) > 2000
       OR p_evidence_url !~* '^https://([a-z0-9.-]+)(:[0-9]{1,5})?([/?#]|$)' THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'Evidence must be an HTTPS URL'::TEXT;
      RETURN;
    END IF;
    IF p_observed_at IS NULL OR p_observed_at > now()
       OR p_valid_until IS NULL OR p_valid_until <= now()
       OR p_valid_until <= p_observed_at THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'Evidence observation and future expiry are required'::TEXT;
      RETURN;
    END IF;
    IF (p_valid_until AT TIME ZONE 'UTC')
       > (p_observed_at AT TIME ZONE 'UTC') + INTERVAL '90 days' THEN
      RETURN QUERY SELECT false, p_course_id, _current_version,
        'Evidence validity cannot exceed 90 calendar days from observed_at'::TEXT;
      RETURN;
    END IF;

    _course_host := lower((regexp_match(_course_url, '^https?://([a-z0-9.-]+)(:[0-9]{1,5})?([/?#]|$)', 'i'))[1]);
    _evidence_host := lower((regexp_match(p_evidence_url, '^https://([a-z0-9.-]+)(:[0-9]{1,5})?([/?#]|$)', 'i'))[1]);
    _course_host := regexp_replace(_course_host, '^www\.', '');
    _evidence_host := regexp_replace(_evidence_host, '^www\.', '');
    IF _course_host IS NULL OR _evidence_host IS NULL
       OR (_evidence_host <> _course_host AND right(_evidence_host, length('.' || _course_host)) <> '.' || _course_host) THEN
      RETURN QUERY SELECT false, p_course_id, _current_version, 'Evidence host must match the course source or its subdomain'::TEXT;
      RETURN;
    END IF;
  END IF;

  UPDATE public.course_editorial_state es
     SET availability_override_status = p_availability_status,
         availability_evidence_url = p_evidence_url,
         availability_observed_at = p_observed_at,
         availability_valid_until = p_valid_until,
         availability_override_by = CASE WHEN p_availability_status IS NULL THEN NULL ELSE _actor_id END,
         manual_updated_at = now(),
         manual_updated_by = _actor_id,
         version = es.version + 1,
         updated_at = now()
   WHERE es.course_id = p_course_id AND es.version = _current_version
   RETURNING es.version INTO _new_version;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, p_course_id, _current_version, 'Optimistic lock failed: version mismatch'::TEXT;
    RETURN;
  END IF;

  INSERT INTO public.course_editorial_audit (
    course_id, actor_user_id, action, old_values, new_values, reason
  ) VALUES (
    p_course_id,
    _actor_id,
    'availability_override',
    jsonb_build_object(
      'availability_override_status', _old_status,
      'availability_evidence_url', _old_url,
      'availability_observed_at', _old_observed_at,
      'availability_valid_until', _old_valid_until
    ),
    jsonb_build_object(
      'availability_override_status', p_availability_status,
      'availability_evidence_url', p_evidence_url,
      'availability_observed_at', p_observed_at,
      'availability_valid_until', p_valid_until,
      'version', _new_version
    ),
    btrim(p_reason)
  );

  RETURN QUERY SELECT true, p_course_id, _new_version, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_set_course_availability(UUID, TEXT, TEXT, TIMESTAMPTZ, TIMESTAMPTZ, INTEGER, TEXT) IS
  'H3: Records an Admin-only, evidence-backed availability override. It expires to the computed status and every change is audited.';
REVOKE ALL ON FUNCTION public.admin_set_course_availability(UUID, TEXT, TEXT, TIMESTAMPTZ, TIMESTAMPTZ, INTEGER, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_set_course_availability(UUID, TEXT, TEXT, TIMESTAMPTZ, TIMESTAMPTZ, INTEGER, TEXT) TO authenticated, service_role;

-- Read-only, bounded audit reader. The table itself remains inaccessible to
-- authenticated clients; actor email is returned only after the Admin check.
CREATE OR REPLACE FUNCTION public.admin_get_course_audit(
  p_course_id UUID,
  p_first INTEGER DEFAULT 20,
  p_after_created_at TIMESTAMPTZ DEFAULT NULL,
  p_after_id UUID DEFAULT NULL
)
RETURNS TABLE (
  events JSONB,
  page_info JSONB,
  error TEXT
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _events JSONB;
  _has_next BOOLEAN;
  _end_cursor JSONB;
BEGIN
  PERFORM public.admin_require_aal2();
  IF NOT public.admin_is_active_admin() THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'User is not an active admin'::TEXT;
    RETURN;
  END IF;
  IF p_course_id IS NULL THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Course id is required'::TEXT;
    RETURN;
  END IF;
  IF p_first IS NULL OR p_first < 1 OR p_first > 100 THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'First must be between 1 and 100'::TEXT;
    RETURN;
  END IF;
  IF (p_after_created_at IS NULL) <> (p_after_id IS NULL) THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Both cursor values are required'::TEXT;
    RETURN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.courses c WHERE c.id = p_course_id) THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Course not found'::TEXT;
    RETURN;
  END IF;

  WITH filtered AS (
    SELECT a.id, a.created_at, a.action, a.actor_user_id,
           CASE WHEN a.actor_user_id IS NULL THEN 'Pipeline/sistema'
                ELSE COALESCE(NULLIF(u.email, ''), 'Usuario no disponible')
           END AS actor_label,
           a.old_values, a.new_values, a.reason
      FROM public.course_editorial_audit a
      LEFT JOIN auth.users u ON u.id = a.actor_user_id
     WHERE a.course_id = p_course_id
       AND (
         p_after_created_at IS NULL
         OR (a.created_at, a.id) < (p_after_created_at, p_after_id)
       )
     ORDER BY a.created_at DESC, a.id DESC
     LIMIT p_first + 1
  ), page_rows AS (
    SELECT * FROM filtered
     ORDER BY created_at DESC, id DESC
     LIMIT p_first
  )
  SELECT
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'id', page_rows.id,
          'created_at', page_rows.created_at,
          'action', page_rows.action,
          'actor_label', page_rows.actor_label,
          'old_values', page_rows.old_values,
          'new_values', page_rows.new_values,
          'reason', page_rows.reason
        ) ORDER BY page_rows.created_at DESC, page_rows.id DESC
      ),
      '[]'::JSONB
    ),
    (SELECT count(*) > p_first FROM filtered),
    (
      SELECT jsonb_build_object('created_at', page_rows.created_at, 'id', page_rows.id)
        FROM page_rows
       ORDER BY page_rows.created_at ASC, page_rows.id ASC
       LIMIT 1
    )
    INTO _events, _has_next, _end_cursor
    FROM page_rows;

  RETURN QUERY SELECT
    _events,
    jsonb_build_object('hasNextPage', COALESCE(_has_next, false), 'endCursor', _end_cursor),
    NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_get_course_audit(UUID, INTEGER, TIMESTAMPTZ, UUID) IS
  'H3: Admin-only cursor-paginated course audit reader; does not grant direct table access.';
REVOKE ALL ON FUNCTION public.admin_get_course_audit(UUID, INTEGER, TIMESTAMPTZ, UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_get_course_audit(UUID, INTEGER, TIMESTAMPTZ, UUID) TO authenticated, service_role;

-- Extend the existing bounded editorial reader with pipeline provenance,
-- effective availability and the evidence needed by the Admin editor.
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
  _current_values := _pipeline_values;
  FOREACH _field_key IN ARRAY _allowlist LOOP
    IF _state.manual_overrides ? _field_key
       AND _state.manual_overrides -> _field_key <> 'null'::JSONB THEN
      _current_values := _current_values || jsonb_build_object(_field_key, _state.manual_overrides -> _field_key);
    END IF;
  END LOOP;

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
        'is_editable', (_is_admin OR efd.field_key = ANY (_missing_fields)),
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

COMMENT ON FUNCTION public.admin_get_course_editorial(UUID) IS
  'H3: Returns allowlisted editorial values, pipeline provenance and evidence-backed availability for active editors.';
REVOKE ALL ON FUNCTION public.admin_get_course_editorial(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_get_course_editorial(UUID) TO authenticated, service_role;

-- A null in an update payload explicitly removes an override and restores the
-- pipeline value. Other omitted keys remain untouched.
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
  _role TEXT;
  _missing_fields TEXT[];
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

  SELECT es.version, es.manual_overrides, es.missing_fields
    INTO _current_version, _old_values, _missing_fields
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
      IF _role = 'admin' OR _allowlist_keys[i] = ANY (_missing_fields) THEN
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
      ELSE
        RETURN QUERY SELECT false, p_course_id, _current_version, 'User is not allowed to edit field: ' || _allowlist_keys[i];
        RETURN;
      END IF;
    END IF;
  END LOOP;

  _current_overrides := COALESCE(_old_values, '{}'::JSONB);
  _filtered_overrides := jsonb_strip_nulls(_current_overrides || _filtered_overrides);

  UPDATE public.course_editorial_state es
     SET manual_overrides = _filtered_overrides,
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
    jsonb_build_object('manual_overrides', _old_values),
    jsonb_build_object('manual_overrides', _new_values, 'version', _new_version),
    p_reason
  );
  RETURN QUERY SELECT true, p_course_id, _new_version, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) IS
  'H3: Updates only supplied allowlisted overrides with role checks, optimistic locking, null-to-pipeline reset and append-only audit.';
REVOKE ALL ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_update_course(UUID, JSONB, INTEGER, TEXT) TO authenticated, service_role;

-- Publication must agree with the public reader and all technical source gates.
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
            AND (c.url IS NULL OR c.url NOT LIKE 'https://canary.invalid/%')
     INTO _old_status, _quality_status, _availability_status, _missing_count,
         _is_active, _is_verified, _production_enabled
    FROM public.course_editorial_state es
    JOIN public.courses c ON c.id = es.course_id
    LEFT JOIN public.institution_site_profiles p ON p.institution_id = c.institution_id
   WHERE es.course_id = p_course_id
   FOR UPDATE OF es;
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
  IF NOT COALESCE(_is_active, false) OR NOT COALESCE(_is_verified, false)
     OR NOT COALESCE(_production_enabled, false) THEN
    RETURN QUERY SELECT false, p_course_id, NULL::TEXT, 'Course is not publishable: source pipeline gates are not satisfied'::TEXT;
    RETURN;
  END IF;

  UPDATE public.course_editorial_state es
     SET editorial_status = _new_status,
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
    jsonb_build_object('editorial_status', _old_status, 'availability_status', _availability_status),
    jsonb_build_object('editorial_status', _new_status, 'published_at', now()),
    p_reason
  );
  RETURN QUERY SELECT true, p_course_id, _new_status, NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_publish_course(UUID, TEXT) IS
  'H3: Publishes only complete, available courses whose sync/profile visibility gates are satisfied; every publication is audited.';
REVOKE ALL ON FUNCTION public.admin_publish_course(UUID, TEXT) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_publish_course(UUID, TEXT) TO authenticated, service_role;

-- Preserve the legacy cohort during expansion while honoring an explicit,
-- currently valid unavailable determination. Overrides apply only when the
-- strict editorial contract is met.
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
    SELECT c.*, es.manual_overrides, es.manual_start_date,
           CASE WHEN es.availability_override_status IS NOT NULL
                      AND es.availability_valid_until > now()
                THEN es.availability_override_status
                ELSE es.availability_status END AS effective_availability_status,
           (
             es.editorial_status = 'published'
             AND es.quality_status = 'complete'
             AND cardinality(es.missing_fields) = 0
             AND CASE WHEN es.availability_override_status IS NOT NULL
                            AND es.availability_valid_until > now()
                      THEN es.availability_override_status
                      ELSE es.availability_status END = 'available'
           ) AS is_strict_public,
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
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'name', c.name) ELSE c.name END,
    c.slug,
    c.url,
    CASE
      WHEN c.is_strict_public AND c.manual_overrides ->> 'price_pen' ~ '^[0-9]+(\.[0-9]+)?$'
        THEN (c.manual_overrides ->> 'price_pen')::NUMERIC
      ELSE c.price_pen
    END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'price_status', c.price_status, 'A consultar') ELSE COALESCE(c.price_status, 'A consultar') END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'mode', c.mode) ELSE c.mode END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'duration', c.duration) ELSE c.duration END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'description_long', c.description_long) ELSE c.description_long END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'syllabus', c.syllabus) ELSE c.syllabus END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'target_audience', c.target_audience) ELSE c.target_audience END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'requirements', c.requirements) ELSE c.requirements END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'certification', c.certification) ELSE c.certification END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'benefits', c.benefits) ELSE c.benefits END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'objectives', c.objectives) ELSE c.objectives END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_start_date, c.start_date) ELSE c.start_date END,
    CASE WHEN c.is_strict_public THEN COALESCE(c.manual_overrides ->> 'start_date_text', c.start_date_text, 'Sin confirmar') ELSE COALESCE(c.start_date_text, 'Sin confirmar') END,
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

REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;
CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS SELECT * FROM private.h2_public_courses_effective();
REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;
COMMENT ON VIEW public.courses_public_effective IS
  'H3 expanded effective reader. Preserves the legacy cohort, applies manual overrides only after strict gates, and excludes legacy courses with a current unavailable determination.';
