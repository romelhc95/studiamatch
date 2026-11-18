-- StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261115234509-h1-fg3-atomic-public-transition
-- Additive FG3 transition: preserve the legacy worker until this function is
-- installed, then let the candidate validate public eligibility and mutate
-- only courses.last_404_at or courses.is_active in one transaction.

CREATE OR REPLACE FUNCTION public.fg3_apply_public_course_transition(
  p_course_id UUID,
  p_institution_id UUID,
  p_url TEXT,
  p_observed_last_404_at TIMESTAMPTZ,
  p_http_status INTEGER,
  p_action TEXT
)
RETURNS TABLE (
  outcome TEXT,
  resulting_last_404_at TIMESTAMPTZ,
  resulting_is_active BOOLEAN
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
DECLARE
  _course public.courses%ROWTYPE;
  _locked_cohort_course_id UUID;
BEGIN
  IF p_action IS NULL OR p_action NOT IN (
    'start_404_grace',
    'clear_404_grace',
    'deactivate_after_grace'
  ) THEN
    RAISE EXCEPTION 'unsupported FG3 transition' USING ERRCODE = '22023';
  END IF;

  IF p_http_status IS NULL
     OR (p_action = 'start_404_grace'
      AND (p_http_status NOT IN (404, 410) OR p_observed_last_404_at IS NOT NULL))
     OR (p_action = 'clear_404_grace'
      AND (p_http_status < 200 OR p_http_status >= 300 OR p_observed_last_404_at IS NULL))
     OR (p_action = 'deactivate_after_grace'
      AND (p_http_status NOT IN (404, 410) OR p_observed_last_404_at IS NULL)) THEN
    RAISE EXCEPTION 'FG3 transition does not match the observed HTTP state'
      USING ERRCODE = '22023';
  END IF;

  -- Lock order follows the publication writers and protects legacy removal:
  -- profile, editorial state, legacy membership, then course. The row locks
  -- make eligibility revalidation serial with publish/unpublish/archive,
  -- profile changes, and course updates without taking a catalog-wide lock.
  PERFORM 1
    FROM public.institution_site_profiles AS profile
   WHERE profile.institution_id = p_institution_id
     AND profile.production_enabled IS TRUE
     AND COALESCE(profile.notes, '') <> 'DB_AS_CODE_RELEASE_CANARY'
   FOR SHARE;
  IF NOT FOUND THEN
    RETURN QUERY SELECT 'stale'::TEXT, NULL::TIMESTAMPTZ, NULL::BOOLEAN;
    RETURN;
  END IF;

  PERFORM 1
    FROM public.course_editorial_state AS editorial
   WHERE editorial.course_id = p_course_id
   FOR UPDATE;

  -- Lock a present legacy membership before the course because a legacy
  -- withdrawal may delete it and then insert an audit row referencing course.
  -- H2 may have contracted and dropped this base table. In that schema the
  -- H3 compatibility view is empty; keep the function usable for strict-public
  -- courses without a static dependency on the optional legacy relation.
  IF pg_catalog.to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL THEN
    EXECUTE
      'SELECT cohort.course_id
         FROM private.h2_legacy_public_course_cohort AS cohort
        WHERE cohort.course_id = $1
        FOR KEY SHARE'
      INTO _locked_cohort_course_id
      USING p_course_id;
  END IF;

  SELECT course.*
    INTO _course
    FROM public.courses AS course
   WHERE course.id = p_course_id
     AND course.institution_id = p_institution_id
   FOR UPDATE;
  IF NOT FOUND
     OR _course.url IS DISTINCT FROM p_url
     OR _course.is_active IS NOT TRUE
     OR _course.is_verified IS NOT TRUE
     OR _course.last_404_at IS DISTINCT FROM p_observed_last_404_at THEN
    RETURN QUERY SELECT 'stale'::TEXT, NULL::TIMESTAMPTZ, NULL::BOOLEAN;
    RETURN;
  END IF;

  -- Re-evaluate the canonical public projection after acquiring every row
  -- lock that can change the selected course's eligibility.
  IF NOT EXISTS (
    SELECT 1
      FROM public.courses_public_effective AS visible
     WHERE visible.id = p_course_id
       AND visible.institution_id = p_institution_id
       AND visible.url IS NOT DISTINCT FROM p_url
  ) THEN
    RETURN QUERY SELECT 'stale'::TEXT, NULL::TIMESTAMPTZ, NULL::BOOLEAN;
    RETURN;
  END IF;

  IF p_action = 'deactivate_after_grace'
     AND p_observed_last_404_at >= pg_catalog.clock_timestamp() - INTERVAL '3 days' THEN
    RETURN QUERY SELECT 'grace_pending'::TEXT, _course.last_404_at, _course.is_active;
    RETURN;
  END IF;

  IF p_action = 'start_404_grace' THEN
    UPDATE public.courses AS course
       SET last_404_at = pg_catalog.clock_timestamp()
     WHERE course.id = p_course_id
       AND course.last_404_at IS NOT DISTINCT FROM p_observed_last_404_at;
  ELSIF p_action = 'clear_404_grace' THEN
    UPDATE public.courses AS course
       SET last_404_at = NULL
     WHERE course.id = p_course_id
       AND course.last_404_at IS NOT DISTINCT FROM p_observed_last_404_at;
  ELSE
    UPDATE public.courses AS course
       SET is_active = FALSE
     WHERE course.id = p_course_id
       AND course.last_404_at IS NOT DISTINCT FROM p_observed_last_404_at;
  END IF;

  IF NOT FOUND THEN
    RETURN QUERY SELECT 'stale'::TEXT, NULL::TIMESTAMPTZ, NULL::BOOLEAN;
    RETURN;
  END IF;

  RETURN QUERY
    SELECT 'applied'::TEXT, course.last_404_at, course.is_active
      FROM public.courses AS course
     WHERE course.id = p_course_id;
END;
$function$;

REVOKE ALL ON FUNCTION public.fg3_apply_public_course_transition(
  UUID, UUID, TEXT, TIMESTAMPTZ, INTEGER, TEXT
) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.fg3_apply_public_course_transition(
  UUID, UUID, TEXT, TIMESTAMPTZ, INTEGER, TEXT
) TO service_role;

COMMENT ON FUNCTION public.fg3_apply_public_course_transition(
  UUID, UUID, TEXT, TIMESTAMPTZ, INTEGER, TEXT
) IS
  'FG3 only: lock and revalidate courses_public_effective eligibility, then atomically change last_404_at or is_active; callable only by service_role.';
