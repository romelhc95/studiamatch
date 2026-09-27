-- H3/UX: server-side queue facets and institution filtering for Development/Free.
-- Scope: additive Free/Development DDL only.
-- Legacy queue/count RPCs remain intact for compatibility and rollback.
-- No data backfill, operational writes, Pro apply, schedules, writers or canaries.

CREATE OR REPLACE FUNCTION public.admin_get_course_queue_filtered(
  p_first INTEGER DEFAULT 20,
  p_after_cursor TEXT DEFAULT NULL,
  p_editorial_status TEXT DEFAULT NULL,
  p_quality_status TEXT DEFAULT NULL,
  p_institution_slug TEXT DEFAULT NULL
)
RETURNS TABLE (
  courses JSONB,
  page_info JSONB,
  error TEXT
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  _cursor_id UUID;
  _cursor_updated TIMESTAMPTZ;
  _rows JSONB;
  _has_next BOOLEAN;
  _end_cursor JSONB;
BEGIN
  PERFORM public.admin_require_aal2();

  IF NOT public.admin_is_active_editor() THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;

  IF p_first < 1 OR p_first > 100 THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'First must be between 1 and 100'::TEXT;
    RETURN;
  END IF;

  IF p_editorial_status IS NOT NULL
     AND p_editorial_status <> ALL (ARRAY['draft', 'pending_review', 'published', 'archived']) THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Invalid editorial status'::TEXT;
    RETURN;
  END IF;

  IF p_quality_status IS NOT NULL
     AND p_quality_status <> ALL (ARRAY['pending', 'complete', 'blocked']) THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Invalid quality status'::TEXT;
    RETURN;
  END IF;

  IF p_after_cursor IS NOT NULL THEN
    BEGIN
      _cursor_id := (p_after_cursor::JSONB ->> 'id')::UUID;
      _cursor_updated := (p_after_cursor::JSONB ->> 'updated_at')::TIMESTAMPTZ;
      IF _cursor_id IS NULL OR _cursor_updated IS NULL THEN
        RAISE EXCEPTION 'incomplete cursor';
      END IF;
    EXCEPTION WHEN OTHERS THEN
      RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, 'Invalid cursor format'::TEXT;
      RETURN;
    END;
  END IF;

  WITH filtered AS (
    SELECT q.*
    FROM public.admin_course_queue q
    WHERE (p_editorial_status IS NULL OR q.editorial_status = p_editorial_status)
      AND (p_quality_status IS NULL OR q.quality_status = p_quality_status)
      AND (p_institution_slug IS NULL OR q.institution_slug = p_institution_slug)
      AND (
        p_after_cursor IS NULL
        OR (q.updated_at, q.course_id) < (_cursor_updated, _cursor_id)
      )
    ORDER BY q.updated_at DESC, q.course_id DESC
    LIMIT p_first + 1
  ), page_rows AS (
    SELECT *
    FROM filtered
    ORDER BY updated_at DESC, course_id DESC
    LIMIT p_first
  )
  SELECT
    COALESCE(jsonb_agg(to_jsonb(page_rows) ORDER BY updated_at DESC, course_id DESC), '[]'::JSONB),
    EXISTS (SELECT 1 FROM filtered OFFSET p_first),
    (
      SELECT jsonb_build_object('id', course_id, 'updated_at', updated_at)
      FROM page_rows
      ORDER BY updated_at ASC, course_id ASC
      LIMIT 1
    )
  INTO _rows, _has_next, _end_cursor
  FROM page_rows;

  RETURN QUERY SELECT
    _rows,
    jsonb_build_object('hasNextPage', _has_next, 'endCursor', _end_cursor),
    NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_get_course_queue_filtered(INTEGER, TEXT, TEXT, TEXT, TEXT) IS
  'H3 UX: cursor-paginated editorial queue with optional institution slug filter.';

CREATE OR REPLACE FUNCTION public.admin_count_course_queue_filtered(
  p_editorial_status TEXT DEFAULT NULL,
  p_quality_status TEXT DEFAULT NULL,
  p_institution_slug TEXT DEFAULT NULL
)
RETURNS TABLE (
  total INTEGER,
  error TEXT
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  PERFORM public.admin_require_aal2();

  IF NOT public.admin_is_active_editor() THEN
    RETURN QUERY SELECT NULL::INTEGER, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;

  IF p_editorial_status IS NOT NULL
     AND p_editorial_status <> ALL (ARRAY['draft', 'pending_review', 'published', 'archived']) THEN
    RETURN QUERY SELECT NULL::INTEGER, 'Invalid editorial status'::TEXT;
    RETURN;
  END IF;

  IF p_quality_status IS NOT NULL
     AND p_quality_status <> ALL (ARRAY['pending', 'complete', 'blocked']) THEN
    RETURN QUERY SELECT NULL::INTEGER, 'Invalid quality status'::TEXT;
    RETURN;
  END IF;

  RETURN QUERY
  SELECT count(*)::INTEGER, NULL::TEXT
  FROM public.admin_course_queue q
  WHERE (p_editorial_status IS NULL OR q.editorial_status = p_editorial_status)
    AND (p_quality_status IS NULL OR q.quality_status = p_quality_status)
    AND (p_institution_slug IS NULL OR q.institution_slug = p_institution_slug);
END;
$$;

COMMENT ON FUNCTION public.admin_count_course_queue_filtered(TEXT, TEXT, TEXT) IS
  'H3 UX: count editorial queue rows with optional institution slug filter.';

CREATE OR REPLACE FUNCTION public.admin_get_course_queue_facets()
RETURNS TABLE (
  editorial_counts JSONB,
  quality_counts JSONB,
  institutions JSONB,
  error TEXT
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  PERFORM public.admin_require_aal2();

  IF NOT public.admin_is_active_editor() THEN
    RETURN QUERY SELECT NULL::JSONB, NULL::JSONB, NULL::JSONB, 'User is not an active editor'::TEXT;
    RETURN;
  END IF;

  RETURN QUERY
  SELECT
    jsonb_build_object(
      'draft', (SELECT count(*)::INTEGER FROM public.admin_course_queue WHERE editorial_status = 'draft'),
      'pending_review', (SELECT count(*)::INTEGER FROM public.admin_course_queue WHERE editorial_status = 'pending_review'),
      'published', (SELECT count(*)::INTEGER FROM public.admin_course_queue WHERE editorial_status = 'published'),
      'archived', (SELECT count(*)::INTEGER FROM public.admin_course_queue WHERE editorial_status = 'archived')
    ),
    jsonb_build_object(
      'pending', (SELECT count(*)::INTEGER FROM public.admin_course_queue WHERE quality_status = 'pending'),
      'complete', (SELECT count(*)::INTEGER FROM public.admin_course_queue WHERE quality_status = 'complete'),
      'blocked', (SELECT count(*)::INTEGER FROM public.admin_course_queue WHERE quality_status = 'blocked')
    ),
    COALESCE(
      (
        SELECT jsonb_agg(
          jsonb_build_object('slug', catalog.institution_slug, 'name', catalog.institution_name)
          ORDER BY lower(catalog.institution_name), catalog.institution_slug
        )
        FROM (
          SELECT DISTINCT institution_slug, institution_name
          FROM public.admin_course_queue
          WHERE institution_slug IS NOT NULL AND institution_name IS NOT NULL
        ) AS catalog
      ),
      '[]'::JSONB
    ),
    NULL::TEXT;
END;
$$;

COMMENT ON FUNCTION public.admin_get_course_queue_facets() IS
  'H3 UX: grouped editorial/quality counts and institution catalog for the admin queue.';

REVOKE ALL ON FUNCTION public.admin_get_course_queue_filtered(INTEGER, TEXT, TEXT, TEXT, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_count_course_queue_filtered(TEXT, TEXT, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.admin_get_course_queue_facets() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_get_course_queue_filtered(INTEGER, TEXT, TEXT, TEXT, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_count_course_queue_filtered(TEXT, TEXT, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.admin_get_course_queue_facets() TO authenticated, service_role;
